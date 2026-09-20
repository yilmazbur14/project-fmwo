"""Synthesizes the Eric V2 finisher sounds into Assets/Audio/SFX, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, on make_voices.py's building blocks plus dsp.py. Nothing is sampled or downloaded,
and every run writes byte-identical files.

    python make_eric_v2_sfx.py            writes the seven WAVs
    python make_eric_v2_sfx.py --check    rebuilds them in memory and compares byte for byte; writes nothing

preview.py mixes them into one listen-through of a tier-3 finisher, measure.py prints the level table and the loop
seam check, and verify_eric_v2_sfx.gd loads them in Godot and plays the loop across its seam.

The sounds, and where the plan (scratchpad eric_pacing_plan.md, sections 3 and 7) plays them:

  finisher_charge_loop   the tiered mash, from the prompt until the mash resolves. Loops by itself: the loop
                         points are in the file's smpl chunk, which Godot reads with the import default
                         (edit/loop_mode = Detect From WAV), so code must not set loop_begin/loop_end. It is
                         110250 frames of loop plus one guard frame (see build_all). Code pitches it
                         1.0 + 0.2 * m_s, so 1.0 to 1.6.
  finisher_bar_1..3      a bar banking during the mash: a latch, a heavy clunk and (bars 2-3) the bolt seating.
                         Each is pitched to the loop's drone at the pitch the loop plays when that bar banks, so
                         they climb 6:7:8 with it; each is bigger than the last, bar 3 a full lock-in.
  break_sting            the Break frame: an armour-and-glass crack over a low boom.
  eric_crash_thud        Eric landing after the juggle's last uppercut: an armoured body into the mat.
  knight_breaker_sting   the tier-3 special's contact: a heroic brass stab and a blade shing, laid on top of
                         the existing super-uppercut impact. It carries no impact of its own.

Every level is set on make_voices.loudness_db's scale (B-weighted, loudest 80 ms), the one the other synthesized
SFX were matched on, relative to hit_impact.ogg measured through Godot at -17.0 dB. measure.py prints the table.
"""

import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from dsp import (SR, samples, loudness_db, lp, hp, resonator, swept_band, periodic, periodic_biquad, tone,  # noqa
                 decay, place, fade_edges, soft_limit, wav_bytes, peak_db)
sys.path.insert(0, os.path.join(HERE, "..", "audio_voices"))
from make_voices import PROJECT, contour, noise, mix, normalized, saturate  # noqa: E402

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")

# hit_impact.ogg decoded through Godot (punch_fx/dump_audio.gd), on loudness_db's scale.
HIT_REF_DB = -17.0

# (loudness target, peak ceiling in dBFS), with measure.py's table behind each choice:
#   the loop is a bed: 6 dB under a hit, and its 400 ms level about 2.5 dB under the music's median, so the
#     riser reads over the music without covering the clunks;
#   the clunks climb 1.5-2 dB a bar, from 2 dB under a hit (4 over the loop) to 1.5 over one, since they play
#     alone over the loop while the fight is frozen;
#   the Break and the crash are the biggest moments of the fight: 3.5-4 dB over a hit, over the slam, under
#     whirlwind_whoosh (-11.9) and player_hurt (-9.1); reaching that costs their first boom cycle 2-2.5 dB of
#     soft limiting;
#   the Knight Breaker sting rides on the super impact, which already peaks at -1 dBFS: a dB under a hit, a
#     low peak, and its body after the impact's first 30 ms, so the impact stays the hit.
LEVELS = {
    "finisher_charge_loop": (HIT_REF_DB - 6.0, -6.0),
    "finisher_bar_1": (HIT_REF_DB - 2.0, -2.0),
    "finisher_bar_2": (HIT_REF_DB - 0.5, -1.5),
    "finisher_bar_3": (HIT_REF_DB + 1.5, -1.0),
    "break_sting": (HIT_REF_DB + 4.0, -1.0),
    "eric_crash_thud": (HIT_REF_DB + 3.5, -1.0),
    "knight_breaker_sting": (HIT_REF_DB - 1.0, -4.0),
}


def leveled(x, name, loop=False):
    """Matches loudness to the target, rounding off any peak over the ceiling. A loop is measured on two turns
    of itself, so its loudest 80 ms may straddle the seam like it does when it plays."""
    target, ceiling = LEVELS[name]
    limit = 10.0 ** (ceiling / 20.0)
    for _ in range(4):
        level = loudness_db(x + x) if loop else loudness_db(x)
        x = [s * 10.0 ** ((target - level) / 20.0) for s in x]
        if max(abs(s) for s in x) <= limit:
            break
        x = soft_limit(x, limit)
    assert max(abs(s) for s in x) <= limit + 1e-9, name
    return x


# ------------------------------------------------------------------------------------------------- the charge loop

LOOP_MS = 2500.0
# Every tone in the loop has a whole number of cycles in it, which at 2.5 s means a multiple of 0.4 Hz.
LOOP_HZ_STEP = 1000.0 / LOOP_MS
# The drone: E2 and two voices beating against it, once and twice per loop.
DRONE_HZ = [(82.4, 1.0), (82.8, 0.8), (81.6, 0.7)]
# The throb: 20 pulses per loop, 8 Hz at pitch 1.0 and 12.8 Hz at 1.6.
PULSE_HZ = 8.0
# The riser: sine partials an octave apart, each climbing an octave per loop under a bell that fades it in at
# the bottom and out at the top (a Shepard-Risset glissando), with a second stack a fifth up.
RISER_BASE_HZ = 110.0
RISER_OCTAVES = 6
LOOP_SEED = 3101


def band_limited_cycle(harmonics, size=4096):
    """One cycle of a sum of harmonics [(k, amplitude)] as a table."""
    return [sum(a * math.sin(2.0 * math.pi * k * i / size) for k, a in harmonics) for i in range(size)]


def table_tone(table, hz, n):
    """Reads a one-cycle table at hz. The phase is computed from the sample index rather than accumulated, so a
    tone with a whole number of cycles in n samples loops exactly."""
    size = len(table)
    out = []
    for i in range(n):
        p = (hz * i / SR) % 1.0 * size
        j = int(p)
        f = p - j
        a, b = table[j], table[(j + 1) % size]
        out.append(a + (b - a) * f)
    return out


def pulse_shape(n, hz, sharpness):
    """0..1 pulses, peaky rather than sinusoidal, a whole number per loop."""
    return [(0.5 + 0.5 * math.cos(2.0 * math.pi * hz * i / SR)) ** sharpness for i in range(n)]


def shepard(n, base_hz, octaves, loop_ms):
    """Partials an octave apart, all rising an octave over the loop. Partial k's phase is analytic, and each
    starting phase is where the partial below it ends, so partial k at the loop's end is partial k+1 at its
    start: frequency, level and phase all meet, and the bell is zero at both ends where one leaves and none
    arrives."""
    t_len = loop_ms / 1000.0
    ln2 = math.log(2.0)
    starts = [0.0]
    for k in range(octaves - 1):
        starts.append(starts[-1] + 2.0 * math.pi * base_hz * 2 ** k * t_len / ln2)
    out = []
    for i in range(n):
        u = i / SR / t_len
        rise = 2.0 ** u - 1.0
        s = 0.0
        for k in range(octaves):
            position = k + u
            level = math.sin(math.pi * position / octaves) ** 4
            s += level * math.sin(starts[k] + 2.0 * math.pi * base_hz * 2 ** k * t_len / ln2 * rise)
        out.append(s)
    return out


def periodic_noise(n, rng):
    return noise(n, rng)


def crackle(n, rng, per_second, length_ms):
    """Sparse electric ticks at fixed random spots, wrapped around the loop so the pattern repeats cleanly."""
    out = [0.0] * n
    count = int(per_second * n / SR)
    length = samples(length_ms)
    for _ in range(count):
        at = rng.randrange(n)
        amp = rng.uniform(0.25, 1.0)
        for j in range(length):
            out[(at + j) % n] += amp * rng.uniform(-1.0, 1.0) * math.exp(-5.0 * j / length)
    return out


def build_charge_loop():
    n = samples(LOOP_MS)
    assert all(abs(hz / LOOP_HZ_STEP - round(hz / LOOP_HZ_STEP)) < 1e-9 for hz, _ in DRONE_HZ)
    rng = random.Random(LOOP_SEED)

    # The engine: three detuned saws up to 3 kHz, gently driven so small speakers hear its harmonics.
    drone = [0.0] * n
    for hz, gain in DRONE_HZ:
        table = band_limited_cycle([(k, (1.0 / k) * math.exp(-k / 22.0)) for k in range(1, int(3000 / hz) + 1)])
        drone = mix((1.0, drone), (gain, table_tone(table, hz, n)))
    drone = saturate(normalized(drone), 1.6)
    drone = periodic(lambda x, state: resonator(x, 420.0, 0.9, state=state), drone)
    drone = mix((0.6, drone), (0.4, periodic_biquad(normalized(drone), "lp", 900.0)))

    # The aura: noise through two throat-like bands, the roar of the charge.
    air = periodic_noise(n, rng)
    roar = mix((1.0, periodic(lambda x, state: resonator(x, 650.0, 0.9, state=state), air)),
               (0.35, periodic(lambda x, state: resonator(x, 1400.0, 2.0, state=state), air)),
               (0.6, periodic_biquad(periodic_biquad(air, "lp", 220.0), "lp", 220.0)))
    roar = periodic_biquad(periodic_biquad(roar, "lp", 2600.0), "lp", 2600.0)

    riser = mix((1.0, shepard(n, RISER_BASE_HZ, RISER_OCTAVES, LOOP_MS)),
                (0.5, shepard(n, RISER_BASE_HZ * 1.5, RISER_OCTAVES, LOOP_MS)))

    sparks = crackle(n, rng, 14.0, 1.2)
    sparks = periodic(lambda x, state: resonator(x, 4200.0, 1.4, state=state), sparks)

    throb = pulse_shape(n, PULSE_HZ, 2.0)
    body = [(0.5 + 0.5 * p) for p in throb]
    aura = [(0.35 + 0.65 * p) for p in throb]
    shimmer = [(0.8 + 0.2 * p) for p in throb]
    x = mix((0.9, [s * g for s, g in zip(normalized(drone), body)]),
            (0.5, [s * g for s, g in zip(normalized(roar), aura)]),
            (0.6, [s * g for s, g in zip(normalized(riser), shimmer)]),
            (0.06, normalized(sparks)))
    x = saturate(normalized(x), 1.2)
    # Nothing under 40 Hz, and nothing near the top: pitched up 1.6x, 9 kHz lands at 14.4 kHz, under where
    # Godot's resampler would fold it back.
    for kind, hz in (("hp", 40.0), ("lp", 8500.0), ("lp", 8500.0)):
        x = periodic_biquad(x, kind, hz)

    # Start on a throb trough at the quietest sample near it, so the first play fades in on its own and the
    # seam lands where the loop is softest. Rotating a periodic signal keeps it periodic.
    per = SR / PULSE_HZ
    best = None
    for k in range(int(PULSE_HZ * LOOP_MS / 1000.0)):
        trough = int(round((k + 0.5) * per))
        for i in range(trough - samples(1.5), trough + samples(1.5)):
            score = abs(x[i % n]) + abs(x[i % n] - x[(i - 1) % n])
            if best is None or score < best[0]:
                best = (score, i % n)
    start = best[1]
    return x[start:] + x[:start]


# ------------------------------------------------------------------------------------------------- one-shot parts

def metal(n, base, modes, tail_ms, rng, bend=1.0, glide_ms=1.0, twins=2, twin_cents=6.0, attack_ms=0.4):
    """A struck metal cluster: partials (ratio, amplitude, how long it rings against the tail) at ratios that are
    not whole numbers. It lands a shade sharp and settles over glide_ms, the way a struck object falls into its
    note, and the lowest `twins` partials get a detuned twin so the tail beats like real metal."""
    bend_curve = contour(n, [(0.0, bend), (glide_ms, 1.0), (glide_ms + 1.0, 1.0)])
    layers = []
    for index, (ratio, amplitude, scale) in enumerate(modes):
        pairs = [(1.0, 0.0)] + ([(0.6, twin_cents * rng.uniform(0.6, 1.0))] if index < twins else [])
        for gain, cents in pairs:
            hz = base * ratio * 2.0 ** (cents / 1200.0)
            if hz >= 14000.0:
                continue
            env = decay(n, tail_ms * scale, attack_ms)
            wave = tone(n, [hz * b for b in bend_curve], 1.0, rng.uniform(0.0, 2.0 * math.pi))
            layers.append((gain * amplitude, [w * e for w, e in zip(wave, env)]))
    return mix(*layers)


def thump(n, points, decay_ms, attack_ms=1.0, harmonics=((1, 1.0),)):
    """A body blow: a low tone whose pitch falls through `points` (ms, Hz) while it dies away."""
    freqs = contour(n, points)
    env = decay(n, decay_ms, attack_ms)
    out = [0.0] * n
    for k, amp in harmonics:
        wave = tone(n, [f * k for f in freqs], amp)
        out = [o + w for o, w in zip(out, wave)]
    return [o * e for o, e in zip(out, env)]


def crack(n, rng, low_hz, high_hz, decay_ms, drive):
    """A hard broadband front, clipped once it is at full scale so it rides the ceiling for its short life
    (make_parry_hit.click)."""
    source = hp(lp(noise(n, rng), high_hz), low_hz)
    env = decay(n, decay_ms)
    return normalized(saturate(normalized([s * e for s, e in zip(source, env)]), drive))


def burst(n, rng, centre, q, decay_ms, attack_ms=0.3):
    """Noise through a resonance, dying away: the thick part of a knock."""
    band = resonator(noise(n, rng), centre, q)
    env = decay(n, decay_ms, attack_ms)
    return normalized([s * e for s, e in zip(band, env)])


def glints(n, sweeps):
    """Quiet sine glints sliding upward, the shine on top: (start ms, from Hz, to Hz, length ms, amplitude)."""
    out = [0.0] * n
    for start_ms, from_hz, to_hz, length_ms, amplitude in sweeps:
        length = min(n - samples(start_ms), samples(length_ms))
        freqs = contour(length, [(0.0, from_hz), (length_ms, to_hz)])
        env = decay(length, length_ms, 10.0)
        place(out, [w * e * amplitude for w, e in zip(tone(length, freqs), env)], start_ms)
    return out


# ------------------------------------------------------------------------------------------------- the bars

# A heavy latch: the base partial is the loudest, so the clunk has a pitch to climb with.
MECH_MODES = [(1.00, 1.00, 1.00), (1.51, 0.70, 0.72), (2.23, 0.50, 0.52), (2.79, 0.40, 0.42),
              (3.63, 0.28, 0.30), (4.41, 0.18, 0.22), (5.37, 0.11, 0.16)]
LATCH_MODES = [(1.00, 1.00, 1.00), (1.37, 0.80, 0.70), (1.82, 0.60, 0.50), (2.66, 0.35, 0.30)]
RING_MODES = [(1.00, 1.00, 1.00), (2.01, 0.55, 0.75), (2.98, 0.30, 0.55), (4.07, 0.16, 0.40), (5.19, 0.08, 0.28)]

# Each bar locks in on the charge loop's own drone at the pitch the loop is playing when that bar banks: the
# meter snaps to k on banking, so the loop is at exactly 1.0 + 0.2 k. Bars 1..3 therefore sit at 6:7:8, a
# septimal third and then a fourth over the first, climbing with the loop instead of against it.
DRONE_ROOT = DRONE_HZ[0][0]
BARS = [
    dict(pitch=1.2, seed=711, latch_gap=26.0, length_ms=420.0, metal_tail=150.0, thump_ms=190.0, drive=1.0,
         bright=0.0, lock=None, sub=0.0, ring=0.0, glint=[]),
    dict(pitch=1.4, seed=722, latch_gap=30.0, length_ms=560.0, metal_tail=190.0, thump_ms=240.0, drive=1.3,
         bright=0.35, lock=(92.0, 0.30), sub=0.0, ring=0.0, glint=[]),
    dict(pitch=1.6, seed=733, latch_gap=34.0, length_ms=1050.0, metal_tail=260.0, thump_ms=320.0, drive=1.6,
         bright=0.7, lock=(104.0, 0.42), sub=0.85, ring=0.42,
         glint=[(120.0, 2600.0, 5200.0, 420.0, 0.11), (190.0, 3300.0, 6800.0, 380.0, 0.08)]),
]


def build_bar(spec):
    rng = random.Random(spec["seed"])
    n = samples(spec["length_ms"])
    hz = DRONE_ROOT * spec["pitch"]
    gap = spec["latch_gap"]

    # The latch: a small bright click and tick, the mechanism moving before it seats.
    latch = mix((0.55, crack(n, rng, 2500.0, 9000.0, 2.0, 4.0)),
                (0.45, normalized(metal(n, hz * 16.0, LATCH_MODES, 28.0, rng, bend=1.03, glide_ms=4.0))))

    # The clunk: a hard front, the heavy latch ringing two octaves over the drone, and the body under it
    # dropping onto the drone's own note.
    clunk_n = n - samples(gap)
    front = crack(clunk_n, rng, 900.0, 6500.0, 3.5, 5.0)
    block = normalized(metal(clunk_n, hz * 4.0, MECH_MODES, spec["metal_tail"], rng, bend=1.04, glide_ms=6.0))
    body = normalized(thump(clunk_n, [(0.0, hz * 2.4), (10.0, hz * 1.6), (45.0, hz), (400.0, hz * 0.97)],
                            spec["thump_ms"], 0.8, harmonics=((1, 1.0), (2, 0.35), (3, 0.12))))
    chunk = burst(clunk_n, rng, 320.0 * spec["pitch"], 1.1, 40.0)
    clunk = mix((0.8, front), (1.0, block), (1.15, body), (0.5, chunk))
    if spec["bright"]:
        clunk = mix((1.0, clunk), (spec["bright"], normalized(hp(block, 1800.0))))
    clunk = saturate(normalized(clunk), spec["drive"])

    x = [0.0] * n
    place(x, latch, 0.0, 0.42)
    place(x, clunk, gap, 1.0)
    if spec["lock"]:
        # The bolt seating a beat after the clunk: the "lock" in clunk-and-lock.
        at, gain = spec["lock"]
        lock_n = n - samples(at)
        lock = mix((0.5, crack(lock_n, rng, 3000.0, 10000.0, 1.6, 4.0)),
                   (0.5, normalized(metal(lock_n, hz * 12.0, LATCH_MODES, 40.0, rng, bend=1.02, glide_ms=3.0))))
        place(x, lock, at, gain)
    if spec["sub"]:
        sub = thump(n - samples(gap), [(0.0, hz * 0.75), (60.0, hz * 0.5), (600.0, hz * 0.47)], 620.0, 2.0,
                    harmonics=((1, 1.0), (2, 0.3)))
        place(x, normalized(sub), gap, spec["sub"])
    if spec["ring"]:
        # Bar 3's lock-in: the whole mechanism rings on, an octave up, fading over most of a second.
        ring = metal(n - samples(gap), hz * 8.0, RING_MODES, 820.0, rng, bend=1.01, glide_ms=8.0, twins=3,
                     twin_cents=4.0, attack_ms=3.0)
        place(x, normalized(ring), gap, spec["ring"])
    if spec["glint"]:
        place(x, glints(n, spec["glint"]), 0.0, 1.0)
    x = hp(lp(x, 12000.0), 38.0)
    return fade_edges(x, 0.3, 4.0)


def echoes(x, taps):
    """A small room: darkened copies (delay ms, gain, low-pass Hz), trimmed back to the dry length."""
    n = len(x)
    layers = [(1.0, x)]
    for ms, gain, hz in taps:
        layers.append((gain, lp([0.0] * samples(ms) + x[:n - samples(ms)], hz)))
    return mix(*layers)


def ping(n_ms, hz, rng, decay_ms, attack_ms=0.2):
    """One tiny glassy ping: a sine and a scrap of its own click."""
    n = samples(n_ms)
    wave = tone(n, [hz] * n, 1.0, rng.uniform(0.0, 2.0 * math.pi))
    env = decay(n, decay_ms, attack_ms)
    tick = crack(n, rng, 3000.0, 12000.0, 0.5, 2.0)
    return [w * e + 0.25 * t for w, e, t in zip(wave, env, tick)]


# ------------------------------------------------------------------------------------------------- the Break

# A thick armour plate: irregular ratios, the second partial the loudest, a long-ish ring.
PLATE_MODES = [(1.00, 0.85, 1.00), (1.47, 1.00, 0.82), (2.09, 0.78, 0.64), (2.56, 0.60, 0.52), (3.18, 0.46, 0.42),
               (3.97, 0.33, 0.32), (4.66, 0.22, 0.25), (5.83, 0.14, 0.18)]
BREAK_SEED = 811


def build_break_sting():
    """The guard giving way: a crack that runs through the plate in a burst of ticks, the plate clanging, glass
    shards scattering and thinning out, all over a deep boom with a thud of air in it."""
    rng = random.Random(BREAK_SEED)
    n = samples(1400.0)

    front = crack(n, rng, 600.0, 11500.0, 4.5, 6.0)
    split = [0.0] * n
    t = 0.0
    for _ in range(16):
        t += rng.uniform(1.2, 4.5)
        tick = crack(samples(3.0), rng, 1800.0, 12000.0, rng.uniform(0.4, 1.1), 3.0)
        place(split, tick, t, rng.uniform(0.45, 1.0) * math.exp(-t / 38.0))

    plate = normalized(metal(n, 330.0, PLATE_MODES, 560.0, rng, bend=1.05, glide_ms=14.0, twins=3, twin_cents=9.0))

    shards = [0.0] * n
    t = 6.0
    while True:
        t += rng.expovariate(1.0 / (5.0 + 0.1 * t))
        if t > 760.0:
            break
        length = rng.uniform(25.0, 85.0)
        place(shards, ping(length, rng.uniform(3200.0, 9200.0), rng, length), t,
              rng.uniform(0.35, 1.0) * math.exp(-t / 280.0))

    boom = thump(n, [(0.0, 98.0), (35.0, 64.0), (240.0, 42.0), (1400.0, 38.0)], 1200.0, 2.5,
                 harmonics=((1, 1.0), (2, 0.3), (3, 0.1)))
    air = [s * e for s, e in zip(noise(n, rng), decay(n, 260.0, 3.0))]
    whump = normalized(lp(lp(air, 240.0), 240.0))
    low = saturate(normalized(mix((1.0, normalized(boom)), (0.5, whump))), 1.7)

    x = mix((0.95, front), (0.6, normalized(split)), (0.82, plate), (0.5, normalized(shards)), (1.35, low))
    x = echoes(x, [(61.0, 0.16, 3200.0), (127.0, 0.10, 2200.0), (203.0, 0.06, 1400.0), (311.0, 0.035, 900.0)])
    x = hp(lp(x, 13000.0), 28.0)
    return fade_edges(x, 0.3, 30.0)


# ------------------------------------------------------------------------------------------------- the crash

ARMOUR_MODES = [(1.00, 1.00, 1.00), (1.41, 0.85, 0.75), (1.93, 0.62, 0.55), (2.57, 0.45, 0.42), (3.31, 0.30, 0.30),
                (4.22, 0.18, 0.22)]
CRASH_SEED = 911
# (ms after the landing, level, base Hz, ring ms): the plates and gauntlets settling after the body.
CLATTER = [(0.0, 1.00, 610.0, 150.0), (41.0, 0.72, 790.0, 120.0), (93.0, 0.52, 540.0, 130.0),
           (162.0, 0.36, 930.0, 95.0), (251.0, 0.22, 700.0, 90.0), (344.0, 0.12, 860.0, 70.0)]


def build_crash_thud():
    """A knight in full armour landing flat on a ring mat: the body's deep drop and the ring's boards booming under
    the canvas, a slap of canvas and dust, and the armour clattering to rest a piece at a time."""
    rng = random.Random(CRASH_SEED)
    n = samples(1350.0)

    body = thump(n, [(0.0, 90.0), (22.0, 60.0), (110.0, 37.0), (1350.0, 33.0)], 950.0, 1.2,
                 harmonics=((1, 1.0), (2, 0.5), (3, 0.22), (4, 0.09)))
    hit = [s * e for s, e in zip(noise(n, rng), decay(n, 70.0, 0.5))]
    boards = mix((1.0, resonator(hit, 104.0, 5.0)), (0.7, resonator(hit, 167.0, 4.0)), (0.35, resonator(hit, 243.0, 3.5)))
    low = saturate(normalized(mix((1.0, normalized(body)), (0.8, normalized(boards)))), 2.2)

    slap = burst(n, rng, 480.0, 0.8, 26.0)
    thud = burst(n, rng, 210.0, 1.4, 60.0)

    clatter = [0.0] * n
    for at, level, base, ring_ms in CLATTER:
        piece_n = n - samples(at)
        piece = mix((1.0, normalized(metal(piece_n, base, ARMOUR_MODES, ring_ms, rng, bend=1.035, glide_ms=5.0))),
                    (0.5, crack(piece_n, rng, 1500.0, 9000.0, 1.8, 3.0)))
        place(clatter, piece, at, level)

    mail = [0.0] * n
    t = 4.0
    while t < 220.0:
        t += rng.expovariate(1.0 / 3.5)
        place(mail, crack(samples(2.0), rng, 4000.0, 11000.0, 0.6, 2.0), t, rng.uniform(0.2, 1.0) * math.exp(-t / 90.0))

    dust = normalized(lp(lp([s * e for s, e in zip(noise(n, rng), decay(n, 480.0, 28.0))], 650.0), 650.0))
    shake_env = decay(n, 1150.0, 12.0)
    shake = [e * (math.sin(2.0 * math.pi * 55.0 * i / SR) + 0.8 * math.sin(2.0 * math.pi * 58.5 * i / SR + 1.1))
             for i, e in enumerate(shake_env)]

    x = mix((1.3, low), (0.55, slap), (0.45, thud), (0.42, normalized(clatter)), (0.10, normalized(mail)),
            (0.22, dust), (0.16, normalized(shake)))
    x = echoes(x, [(53.0, 0.12, 1800.0), (109.0, 0.07, 1200.0), (181.0, 0.04, 800.0)])
    x = hp(lp(x, 12000.0), 26.0)
    return fade_edges(x, 0.3, 30.0)


# ------------------------------------------------------------------------------------------------- Knight Breaker

# A heroic stab in D: a quick pickup on A, then D major voiced D4 A4 D5 F#5, as a synth brass section.
PICKUP = [(440.0, 1.0), (220.0, 0.55)]
CHORD = [(293.66, 1.0), (440.0, 0.85), (587.33, 0.7), (739.99, 0.55)]
PICKUP_AT_MS = 28.0
PICKUP_MS = 80.0
CHORD_AT_MS = 104.0
# A long blade ringing: sparse, slightly stretched partials, the top of a sword being flashed.
BLADE_MODES = [(1.00, 1.00, 1.00), (1.34, 0.75, 0.85), (1.79, 0.55, 0.70), (2.41, 0.35, 0.55), (3.05, 0.22, 0.42)]
KNIGHT_SEED = 1011


def saw_table(hz, size=2048):
    return band_limited_cycle([(k, 1.0 / k) for k in range(1, int(11000.0 / (hz * 1.04)) + 1)], size)


def brass(n, hz, rng, length_ms, cutoff_points, scoop=0.965, scoop_ms=38.0, voices=3, spread_cents=9.0,
          hold_ms=150.0, fall_ms=900.0):
    """A synth brass voice: detuned saws scooping up into the note, through a low-pass that blats open on the
    attack and settles, with a slow vibrato arriving late."""
    table = saw_table(hz)
    size = len(table)
    cutoff = contour(n, cutoff_points)
    out = [0.0] * n
    for v in range(voices):
        cents = spread_cents * (2.0 * v / (voices - 1) - 1.0) if voices > 1 else 0.0
        f0 = hz * 2.0 ** (cents / 1200.0)
        bend = contour(n, [(0.0, scoop), (scoop_ms, 1.0), (length_ms, 1.0)])
        phase = rng.uniform(0.0, 1.0)
        for i in range(n):
            t = i / SR
            wobble = 1.0 + 0.004 * min(1.0, max(0.0, (t - 0.18) / 0.15)) * math.sin(2.0 * math.pi * 5.5 * t + v)
            phase = (phase + f0 * bend[i] * wobble / SR) % 1.0
            p = phase * size
            j = int(p)
            a, b = table[j], table[(j + 1) % size]
            out[i] += a + (b - a) * (p - j)
    y1 = y2 = 0.0
    filtered = []
    for s, fc in zip(out, cutoff):
        a = 1.0 - math.exp(-2.0 * math.pi * fc / SR)
        y1 += a * (s - y1)
        y2 += a * (y1 - y2)
        filtered.append(y2)
    attack = samples(9.0)
    hold = samples(hold_ms)
    k = 6.908 / samples(fall_ms)
    env = []
    for i in range(n):
        g = 1.0 if i < hold else math.exp(-k * (i - hold))
        if i < attack:
            g *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        env.append(g)
    return [f * e for f, e in zip(filtered, env)]


def build_knight_breaker_sting():
    """The flare on the tier-3 special, over the super impact rather than instead of it: a blade flashing on
    contact, then a brass stab "da-DAAN" and glints, with nothing under 260 Hz and little in the impact's first
    30 ms, so the impact stays the hit and this is the shine on it."""
    rng = random.Random(KNIGHT_SEED)
    n = samples(1250.0)

    blade_n = n - samples(8.0)
    blade = normalized(metal(blade_n, 2150.0, BLADE_MODES, 820.0, rng, bend=1.012, glide_ms=10.0, twins=3,
                             twin_cents=5.0, attack_ms=1.8))
    centres = contour(blade_n, [(0.0, 2400.0), (140.0, 9000.0), (400.0, 9000.0)])
    swish = swept_band(noise(blade_n, rng), centres, 1.6)
    swish = normalized([s * e for s, e in zip(swish, decay(blade_n, 260.0, 6.0))])

    pickup_n = samples(PICKUP_MS + 60.0)
    pickup = [0.0] * pickup_n
    for hz, gain in PICKUP:
        voice = brass(pickup_n, hz, rng, PICKUP_MS, [(0.0, 900.0), (18.0, 4200.0), (PICKUP_MS, 2400.0)],
                      scoop=0.98, scoop_ms=14.0, hold_ms=PICKUP_MS - 20.0, fall_ms=90.0)
        pickup = mix((1.0, pickup), (gain, voice))

    chord_n = n - samples(CHORD_AT_MS)
    chord = [0.0] * chord_n
    for hz, gain in CHORD:
        voice = brass(chord_n, hz, rng, 1150.0,
                      [(0.0, 800.0), (26.0, 6200.0), (180.0, 3600.0), (700.0, 1800.0), (1150.0, 1200.0)])
        chord = mix((1.0, chord), (gain, voice))

    x = [0.0] * n
    place(x, blade, 8.0, 0.55)
    place(x, swish, 8.0, 0.22)
    place(x, normalized(pickup), PICKUP_AT_MS, 0.55)
    place(x, saturate(normalized(chord), 1.3), CHORD_AT_MS, 1.0)
    place(x, glints(n, [(150.0, 3600.0, 7200.0, 380.0, 1.0), (225.0, 4500.0, 8400.0, 330.0, 0.7)]), 0.0, 0.10)
    x = echoes(x, [(71.0, 0.14, 5000.0), (149.0, 0.09, 3500.0), (233.0, 0.05, 2400.0)])
    x = hp(hp(lp(x, 12000.0), 260.0), 260.0)
    return fade_edges(x, 0.5, 40.0)


# ------------------------------------------------------------------------------------------------- output

# (file name, builder, loops)
SOUNDS = [
    ("finisher_charge_loop", build_charge_loop, True),
    ("finisher_bar_1", lambda: build_bar(BARS[0]), False),
    ("finisher_bar_2", lambda: build_bar(BARS[1]), False),
    ("finisher_bar_3", lambda: build_bar(BARS[2]), False),
    ("break_sting", build_break_sting, False),
    ("eric_crash_thud", build_crash_thud, False),
    ("knight_breaker_sting", build_knight_breaker_sting, False),
]


def build_all():
    """{name: WAV bytes}, every sound leveled. The loop's N frames are followed by one guard frame, a copy of its
    first: Godot 4.6 plays the frame at loop_end and then resumes at loop_begin + 1 (dsp.godot_native), so with
    loop (0, N) it plays frames 0..N-1, the guard, 1.., which is the loop repeating exactly every N frames."""
    out = {}
    for name, builder, loops in SOUNDS:
        x = leveled(builder(), name, loop=loops)
        if loops:
            out[name] = wav_bytes(x + x[:1], loop=(0, len(x)))
        else:
            out[name] = wav_bytes(x)
    return out


def main():
    check = "--check" in sys.argv
    built = build_all()
    same = True
    for name, data in built.items():
        path = os.path.join(SFX_DIR, name + ".wav")
        if check:
            with open(path, "rb") as f:
                on_disk = f.read()
            match = on_disk == data
            same = same and match
            print("%-26s %s" % (name + ".wav", "identical" if match else "DIFFERS (%d vs %d bytes)" % (len(on_disk), len(data))))
        else:
            with open(path, "wb") as f:
                f.write(data)
            print("wrote %-26s %7d bytes" % (name + ".wav", len(data)))
    if check and not same:
        sys.exit(1)


if __name__ == "__main__":
    main()
