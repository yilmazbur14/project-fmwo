"""Synthesizes Greyson's fight sounds (FIGHT 03, after Computah falls), as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, on the project's own building blocks (make_voices.py, make_bixby_roar.py,
make_matt_sfx.py, audio_eric_v2/dsp.py and make_eric_v2_sfx.py), so every run writes identical files. Nothing is
sampled or downloaded.

    python make_greyson_sfx.py PREVIEW_DIR   writes preview_<name>.wav for every sound, the six scene previews
                                             (scene_*.wav, every sound at its proposed volume_db) and the voice's
                                             preview line into PREVIEW_DIR, then prints the level table
    python make_greyson_sfx.py --ship        writes <name>.wav into Assets/Audio/SFX (the voice into Voices/)
    ... --only plate_bounce_1,crowd_boo      either of those, for only the sounds named

Run with no argument, it only says how to use it: it never writes into the shipped folder unless asked to.

Like the Matt, Danny and Burak sets, every sound effect is normalized to a -3 dBFS peak and the fight's layout
sets how loud each one plays; PROPOSED_DB below is the volume_db that puts each at its intended loudness on
make_voices.loudness_db's scale, against hit_impact.ogg at -17.0 dB. The two loops (the spinning plate, the
pending eruption) carry their loop points in a smpl chunk plus one guard frame, which is what Godot 4.6 needs for
a seamless loop (see audio_eric_v2/dsp.godot_native). The voice blips are loudness-matched the way
make_voices.finish does it, and DialogueVoices.gd sets their level.
"""

import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))


def _find_project():
    folder = HERE
    for _ in range(6):
        if os.path.exists(os.path.join(folder, "project.godot")):
            return folder
        folder = os.path.dirname(folder)
    return r"C:\Users\theyi\OneDrive\Documents\new-game-project"


PROJECT_DIR = _find_project()
ART = os.path.join(PROJECT_DIR, "art_source")
for sub in ("audio_voices", "audio_matt", "audio_eric_v2"):
    sys.path.insert(0, os.path.join(ART, sub))

import dsp  # noqa: E402
from dsp import (lp, hp, resonator, swept_band, periodic, periodic_biquad, tone, decay, place, fade_edges,  # noqa
                 soft_limit, wav_bytes, godot_resample, godot_native)
from make_voices import (SR, samples, contour, oscillator, pulse, envelope, noise, lowpass, highpass, bandpass,  # noqa
                         mul, mix, delayed, normalized, saturate, loudness_db)
import make_voices  # noqa: E402
from make_bixby_roar import pulse_train, wander  # noqa: E402
from make_eric_v2_sfx import (metal, thump, crack, burst, glints, echoes, ping, band_limited_cycle,  # noqa: E402
                              table_tone, pulse_shape, crackle)

SFX_DIR = os.path.join(PROJECT_DIR, "Assets", "Audio", "SFX")
VOICE_DIR = os.path.join(SFX_DIR, "Voices")
PEAK_DBFS = -3.0
HIT_REF_DB = -17.0


# ------------------------------------------------------------------------------------------------- building blocks

def tv_resonator(x, hz_track, q_track, step=16):
    """A constant-peak band-pass whose centre and Q follow per-sample tracks, its coefficients refreshed every
    `step` samples and its state carried through, so a moving formant glides with no seams."""
    out = []
    x1 = x2 = y1 = y2 = 0.0
    b0 = b2 = a1 = a2 = 0.0
    for i, s in enumerate(x):
        if i % step == 0:
            w = 2.0 * math.pi * min(hz_track[i], 0.45 * SR) / SR
            alpha = math.sin(w) / (2.0 * q_track[i])
            a0 = 1.0 + alpha
            b0, b2, a1, a2 = alpha / a0, -alpha / a0, -2.0 * math.cos(w) / a0, (1.0 - alpha) / a0
        y = b0 * s + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y)
    return out


def tract(x, keys):
    """A vocal tract moving through keyframes [(ms, [(Hz, Q, gain), ...]), ...]: every frame the same number of
    formants, each formant gliding from frame to frame."""
    n = len(x)
    layers = []
    for k in range(len(keys[0][1])):
        hz = contour(n, [(ms, f[k][0]) for ms, f in keys])
        q = contour(n, [(ms, f[k][1]) for ms, f in keys])
        gain = contour(n, [(ms, f[k][2]) for ms, f in keys])
        layers.append([g * s for g, s in zip(gain, tv_resonator(x, hz, q))])
    return mix(*[(1.0, layer) for layer in layers])


def glottal(n, pitch_points, rng, jitter=0.03, sub=0.1, pulse_ms=0.8):
    """A voice source: sharp glottal pulses along (ms, Hz) points, rough by `jitter` (a float or (ms, value)
    points), every other pulse quietened by `sub` for a growl an octave down."""
    jit = contour(n, jitter) if isinstance(jitter, list) else [jitter] * n
    subs = contour(n, sub) if isinstance(sub, list) else [sub] * n
    return pulse_train(contour(n, pitch_points), pulse_ms, jit, subs, rng)


def shape(n, points):
    return contour(n, points)


def apply(x, env):
    return [s * g for s, g in zip(x, env)]


def rattle(n, rng, rate_points, low_hz, high_hz, tick_ms=6.0):
    """Loose metal chattering: tiny inharmonic pings at a rate (per second) following (ms, rate) points."""
    rates = contour(n, rate_points)
    out = [0.0] * n
    i = 0
    while i < n:
        rate = max(rates[i], 0.5)
        i += max(1, int(rng.expovariate(rate) * SR))
        if i >= n:
            break
        hz = rng.uniform(low_hz, high_hz)
        length = samples(tick_ms * rng.uniform(0.6, 1.6))
        amp = rng.uniform(0.3, 1.0)
        env = decay(length, tick_ms * 1.5, 0.2)
        wave = tone(length, [hz] * length, amp, rng.uniform(0.0, 6.283))
        wave2 = tone(length, [hz * 1.47] * length, amp * 0.5, rng.uniform(0.0, 6.283))
        for j in range(length):
            if i + j < n:
                out[i + j] += (wave[j] + wave2[j]) * env[j]
    return out


def debris(n, rng, count, start_ms, end_ms, sizes=(0.3, 1.0), low=(140.0, 420.0), bias=1.0):
    """Rocks landing: `count` knocks between start_ms and end_ms (bunched toward the start by `bias` > 1), each a
    burst of noise through a low resonance with a scrap of gravel on top, bigger ones lower and louder."""
    out = [0.0] * n
    for _ in range(count):
        u = rng.random() ** bias
        at = start_ms + (end_ms - start_ms) * u
        size = rng.uniform(*sizes)
        hz = low[1] - (low[1] - low[0]) * size
        length = samples(40.0 + 120.0 * size)
        knock = burst(length, rng, hz, 2.0, 25.0 + 70.0 * size, 0.5)
        grit = crack(length, rng, 2000.0, 9000.0, 3.0 + 4.0 * size, 2.0)
        piece = [0.8 * k + 0.25 * g for k, g in zip(knock, grit)]
        place(out, piece, at, size * rng.uniform(0.6, 1.0))
    return out


def rumble(n, rng, points, cutoff=110.0, beat=(37.0, 41.5)):
    """Earth rumble: low-passed noise under two low tones beating, shaped by (ms, level) points."""
    low = lp(lp(noise(n, rng), cutoff), cutoff)
    tones = mix((1.0, tone(n, [beat[0]] * n)), (0.8, tone(n, [beat[1]] * n, 1.0, 1.3)))
    body = mix((1.0, normalized(low)), (0.5, tones))
    return apply(body, shape(n, points))


def swish(n, rng, points, q=1.4, env_points=None):
    """Air: noise through a band-pass whose centre follows (ms, Hz) points."""
    band = swept_band(noise(n, rng), contour(n, points), q)
    if env_points:
        band = apply(band, shape(n, env_points))
    return band


def sparks(n, rng, start_ms, end_ms, per_second, bias=1.5):
    """Electric sparks: short bright crackles, thinning out after start_ms."""
    out = [0.0] * n
    t = start_ms
    while t < end_ms:
        span = (t - start_ms) / max(1.0, end_ms - start_ms)
        t += rng.expovariate(per_second * (1.0 - span) ** bias + 2.0) * 1000.0
        length = samples(rng.uniform(1.0, 4.0))
        tick = crack(length, rng, 3000.0, 12000.0, rng.uniform(0.4, 1.4), 3.0)
        place(out, tick, t, rng.uniform(0.3, 1.0) * (1.0 - 0.7 * span))
    return out


def buzz(n, hz, rng, gate_rate=35.0, duty=0.55):
    """An electric arc: a harmonic-rich buzz gated on and off at random, through the band arcs live in."""
    wave = oscillator([hz] * n, [(k, 1.0 / k) for k in range(1, 60) if k * hz < 12000.0])
    gate = []
    on = True
    left = 0
    for _ in range(n):
        if left <= 0:
            on = rng.random() < duty
            left = int(SR / gate_rate * rng.uniform(0.3, 1.7))
        left -= 1
        gate.append(1.0 if on else 0.0)
    gate = lowpass(gate, 400.0)
    return bandpass(apply(wave, gate), 2200.0, 0.8)


def chord_pad(n, notes, rng, cutoff_points, voices=3, spread_cents=8.0, harmonics=24):
    """Detuned saw voices on `notes` (Hz, gain) through a low-pass following (ms, Hz) points."""
    out = [0.0] * n
    for hz, gain in notes:
        table = band_limited_cycle([(k, 1.0 / k) for k in range(1, harmonics + 1) if k * hz * 1.02 < 11000.0])
        for v in range(voices):
            cents = spread_cents * (2.0 * v / (voices - 1) - 1.0) if voices > 1 else 0.0
            f = hz * 2.0 ** (cents / 1200.0)
            size = len(table)
            phase = rng.random()
            for i in range(n):
                phase = (phase + f / SR) % 1.0
                p = phase * size
                j = int(p)
                a, b = table[j], table[(j + 1) % size]
                out[i] += gain * (a + (b - a) * (p - j))
    cut = contour(n, cutoff_points)
    y1 = y2 = 0.0
    filtered = []
    for s, fc in zip(out, cut):
        a = 1.0 - math.exp(-2.0 * math.pi * fc / SR)
        y1 += a * (s - y1)
        y2 += a * (y1 - y2)
        filtered.append(y2)
    return filtered


def finish(x, edge_ms=3.0, dc_hz=25.0):
    """Blocks DC, silences both ends and normalizes to PEAK_DBFS (make_matt_sfx.finish)."""
    x = hp(x, dc_hz)
    edge = samples(edge_ms)
    for i in range(min(edge, len(x) // 2)):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x) or 1.0
    return [s * 10.0 ** (PEAK_DBFS / 20.0) / peak for s in x]


def finish_loop(x):
    """A loop to a -3 dBFS peak. Nothing touches its ends: it has none."""
    peak = max(abs(s) for s in x) or 1.0
    return [s * 10.0 ** (PEAK_DBFS / 20.0) / peak for s in x]


# (Hz, Q, gain) per formant. The vowels are a big man's: a shade lower than Matt's.
NN = [(260.0, 4.0, 1.0), (1100.0, 6.0, 0.15), (2300.0, 7.0, 0.10)]
OH = [(480.0, 4.0, 1.0), (880.0, 5.0, 0.55), (2450.0, 6.0, 0.18)]
OO = [(350.0, 4.0, 1.0), (760.0, 5.0, 0.40), (2300.0, 6.0, 0.12)]
AH = [(720.0, 3.5, 1.0), (1120.0, 4.5, 0.65), (2450.0, 5.5, 0.30)]
RR = [(480.0, 3.0, 1.0), (1350.0, 4.0, 0.55), (1700.0, 6.0, 0.30)]
EH = [(560.0, 4.0, 1.0), (1750.0, 5.0, 0.55), (2500.0, 6.0, 0.25)]
EE = [(300.0, 4.5, 1.0), (2150.0, 6.0, 0.45), (2900.0, 7.0, 0.25)]


def vibrato(freqs, rate, depth, start_ms=0.0, swell_ms=200.0):
    return [f * (1.0 + depth * min(1.0, max(0.0, (i / SR * 1000.0 - start_ms) / swell_ms))
                 * math.sin(2.0 * math.pi * rate * i / SR)) for i, f in enumerate(freqs)]


def breath(source, rng, hz=1400.0, q=0.8):
    """Noise that pulses with the voice, which is what makes a throat sound strained rather than hissy."""
    pulsing = lowpass([abs(s) for s in source], 400.0)
    return [b * (0.3 + 2.2 * p) for b, p in zip(bandpass(noise(len(source), rng), hz, q), pulsing)]


# ------------------------------------------------------------------------------------------------- the cutscene

def shout():
    """The shout, heard from off in the arena: a man's "NOOOO", the nasal onset opening into an anguished "oh"
    that climbs to 300 Hz, shakes, and cracks as it falls into "oo", thinned by distance and thrown back by the far
    walls, over a dark D minor swell and a low boom that land on the top of the cry."""
    rng = random.Random(3301)
    n = samples(2500)
    voice_n = samples(1950)
    freqs = contour(voice_n, [(0, 200), (120, 236), (380, 300), (900, 292), (1400, 270), (1750, 236), (1950, 186)])
    freqs = vibrato(freqs, 5.6, 0.02, 420.0, 300.0)
    source = pulse_train(freqs, 0.8, contour(voice_n, [(0, 0.015), (1300, 0.025), (1950, 0.06)]),
                         contour(voice_n, [(0, 0.1), (1400, 0.15), (1950, 0.35)]), rng)
    cry = tract(source, [(0, NN), (100, NN), (175, OH), (750, OH), (1350, OO), (1950, OO)])
    cry = mix((1.0, normalized(cry)), (0.22, normalized(breath(source, rng))))
    cry = saturate(normalized(cry), 1.7)
    cry = apply(cry, shape(voice_n, [(0, 0.0), (15, 0.35), (100, 0.4), (190, 1.0), (1450, 0.9), (1950, 0.0)]))
    cry = lp(lp(hp(cry, 280.0), 3400.0), 3400.0)
    far = echoes(cry + [0.0] * (n - voice_n), [(95.0, 0.36, 2600.0), (182.0, 0.28, 2200.0), (291.0, 0.22, 1800.0),
                                               (433.0, 0.16, 1400.0), (607.0, 0.10, 1100.0), (815.0, 0.06, 900.0)])

    sting_n = n - samples(360)
    pad = chord_pad(sting_n, [(73.42, 0.9), (146.83, 1.0), (174.61, 0.8), (220.0, 0.7)], rng,
                    [(0, 180.0), (140, 1500.0), (700, 900.0), (2140, 350.0)])
    pad = apply(normalized(pad), shape(sting_n, [(0, 0.0), (90, 1.0), (800, 0.6), (2140, 0.0)]))
    boom = normalized(thump(sting_n, [(0, 80.0), (60, 52.0), (700, 40.0)], 1500.0, 3.0,
                            harmonics=((1, 1.0), (2, 0.3), (3, 0.08))))
    sting = [0.0] * n
    place(sting, mix((0.55, pad), (0.7, boom)), 360.0)
    return mix((1.0, normalized(far)), (0.5, sting))


def cannon_rip():
    """The cannon torn off: the joint groaning under the strain, a stick-slip creak speeding up, then a long
    shriek of tearing metal falling in pitch, three cables snapping, an arc buzzing and sparks spraying and thinning
    out, and a couple of bolts dropping."""
    rng = random.Random(3302)
    n = samples(1700)

    groan_n = samples(700)
    impulses = [0.0] * groan_n
    rates = contour(groan_n, [(0, 22.0), (450, 55.0), (700, 110.0)])
    i = 0
    while i < groan_n:
        impulses[i] = rng.uniform(0.5, 1.0)
        i += max(1, int(SR / rates[i] * rng.uniform(0.7, 1.3)))
    groan = mix((1.0, resonator(impulses, 190.0, 9.0)), (0.8, resonator(impulses, 430.0, 10.0)),
                (0.55, resonator(impulses, 960.0, 12.0)), (0.3, resonator(impulses, 1720.0, 12.0)))
    whine = tone(groan_n, contour(groan_n, [(0, 320.0), (700, 880.0)]), 0.12)
    groan = apply(mix((1.0, normalized(groan)), (1.0, whine)), shape(groan_n, [(0, 0.0), (120, 0.5), (700, 1.0)]))

    tear_n = samples(700)
    grit = [0.0] * tear_n
    i = 0
    while i < tear_n:
        grit[i] = rng.uniform(-1.0, 1.0)
        i += max(1, int(SR / rng.uniform(300.0, 900.0)))
    shriek = swept_band(mix((1.0, grit), (0.35, noise(tear_n, rng))), contour(tear_n, [(0, 4200.0), (700, 850.0)]), 5.0)
    rasp = swept_band(noise(tear_n, rng), contour(tear_n, [(0, 2600.0), (700, 600.0)]), 1.2)
    tear = mix((1.0, normalized(shriek)), (0.5, normalized(rasp)))
    tear = apply(saturate(normalized(tear), 1.8), [(0.55 + 0.45 * w) * e for w, e in zip(
        wander(tear_n, 40.0, rng), shape(tear_n, [(0, 0.0), (20, 1.0), (480, 0.8), (700, 0.0)]))])

    snaps = [0.0] * n
    for at, hz in ((640.0, 520.0), (705.0, 380.0), (790.0, 610.0)):
        k = samples(260.0)
        twang = tone(k, contour(k, [(0, hz * 1.25), (40, hz), (260, hz * 0.94)]))
        twang = [t * e for t, e in zip(mix((1.0, twang), (0.4, tone(k, [hz * 2.76] * k))), decay(k, 240.0, 0.3))]
        place(snaps, mix((1.0, twang), (0.6, crack(k, rng, 1500.0, 9000.0, 2.0, 3.0))), at, 0.7)

    arc = apply(buzz(samples(900), 60.0, rng), shape(samples(900), [(0, 0.0), (30, 1.0), (500, 0.6), (900, 0.0)]))
    spray = sparks(n, rng, 620.0, 1650.0, 70.0)
    bolts = [0.0] * n
    for at, hz in ((1080.0, 2300.0), (1260.0, 2850.0), (1330.0, 2600.0)):
        place(bolts, ping(90.0, hz, rng, 80.0), at, 0.5)

    x = [0.0] * n
    place(x, groan, 0.0, 0.8)
    place(x, tear, 560.0, 1.0)
    place(x, snaps, 0.0, 0.8)
    place(x, arc, 700.0, 0.35)
    place(x, spray, 0.0, 0.5)
    place(x, bolts, 0.0, 0.6)
    return hp(lp(x, 12000.0), 60.0)


# Computah's own beep pitches (make_voices.voice_computah): the cannon is his, and it still talks like him.
COMPUTAH_BEEPS = (988.0, 1175.0, 1319.0, 1760.0)


def computah_beep(ms, hz):
    n = samples(ms)
    wave = make_voices.crush(normalized(oscillator([hz] * n, make_voices.square(15, rolloff=1.15))), bits=5, hold=3)
    return mul(lowpass(wave, 7000), envelope(n, 2, 5))


def cannon_clamp():
    """The cannon going on: a servo winding up under a ratchet, the collar slamming shut, two bolts shooting
    home, a hydraulic hiss, and the cannon powering up and saying so in Computah's own beeps."""
    rng = random.Random(3303)
    n = samples(1450)

    whir_n = samples(380)
    motor = oscillator(contour(whir_n, [(0, 170.0), (380, 520.0)]), [(k, 1.0 / k) for k in range(1, 18)])
    gear = tone(whir_n, contour(whir_n, [(0, 850.0), (380, 2600.0)]), 0.2)
    wobble = [0.7 + 0.3 * math.sin(2 * math.pi * 30.0 * i / SR) for i in range(whir_n)]
    motor = apply(mix((0.5, lp(motor, 2500.0)), (1.0, gear)), wobble)
    ticks = [0.0] * whir_n
    for t in range(0, whir_n, samples(1000.0 / 28.0)):
        ticks[t] = 1.0
    ratchet = resonator(ticks, 2600.0, 6.0)
    whir = apply(mix((0.7, normalized(motor)), (0.5, normalized(ratchet))),
                 shape(whir_n, [(0, 0.0), (40, 0.6), (380, 1.0)]))

    clamp_n = samples(700)
    collar = [(1.0, 1.0, 1.0), (1.51, 0.7, 0.7), (2.23, 0.5, 0.5), (2.79, 0.4, 0.4), (3.63, 0.25, 0.3)]
    clunk = mix((1.0, normalized(metal(clamp_n, 185.0, collar, 220.0, rng, bend=1.04, glide_ms=6.0))),
                (1.1, normalized(thump(clamp_n, [(0, 200.0), (12, 130.0), (60, 85.0)], 260.0, 0.6,
                                       harmonics=((1, 1.0), (2, 0.35))))),
                (0.8, crack(clamp_n, rng, 900.0, 7000.0, 3.0, 5.0)))
    bolts = [0.0] * samples(300)
    for at in (0.0, 70.0):
        k = samples(120)
        latch = [(1.0, 1.0, 1.0), (1.37, 0.8, 0.7), (1.82, 0.5, 0.5)]
        place(bolts, mix((0.6, crack(k, rng, 2500.0, 10000.0, 1.5, 4.0)),
                         (0.5, normalized(metal(k, 1450.0, latch, 45.0, rng)))), at)
    hiss_n = samples(420)
    hiss = apply(bandpass(highpass(noise(hiss_n, rng), 2500.0), 5200.0, 0.7),
                 shape(hiss_n, [(0, 0.0), (12, 1.0), (120, 0.6), (420, 0.0)]))
    rise_n = samples(520)
    rise = oscillator(contour(rise_n, [(0, 380.0), (520, 1650.0)]), [(1, 1.0), (2, 0.3), (3, 0.15)])
    rise = apply(rise, shape(rise_n, [(0, 0.0), (80, 0.5), (500, 1.0), (520, 0.0)]))

    x = [0.0] * n
    place(x, whir, 0.0, 0.6)
    place(x, clunk, 360.0, 1.0)
    place(x, bolts, 470.0, 0.55)
    place(x, hiss, 520.0, 0.35)
    place(x, rise, 700.0, 0.22)
    place(x, computah_beep(70, COMPUTAH_BEEPS[2]), 1230.0, 0.3)
    place(x, computah_beep(110, COMPUTAH_BEEPS[3]), 1320.0, 0.3)
    return hp(lp(x, 12000.0), 40.0)


def roar():
    """The gigantic roar that shakes the arena: a big man's "RRAAAAAHH" climbing from 104 to 172 Hz, rough and
    growling an octave down, a chest an octave under that, and the arena answering: a rumble that swells with him,
    the lighting rig and the bleachers rattling, dust sifting down, and the far walls throwing it back."""
    rng = random.Random(3304)
    n = samples(3400)
    voice_n = samples(2900)
    freqs = contour(voice_n, [(0, 104), (250, 150), (520, 172), (1400, 168), (2200, 150), (2600, 136), (2900, 118)])
    freqs = vibrato(freqs, 6.2, 0.012, 500.0, 400.0)
    source = pulse_train(freqs, 1.0, contour(voice_n, [(0, 0.04), (1600, 0.05), (2900, 0.09)]),
                         contour(voice_n, [(0, 0.45), (700, 0.3), (2000, 0.35), (2900, 0.55)]), rng)
    throat = tract(source, [(0, RR), (200, RR), (420, AH), (2300, AH), (2900, OH)])
    throat = mix((1.0, normalized(throat)), (0.3, normalized(breath(source, rng, 1200.0, 0.7))))
    growl = [1.0 - 0.3 * (0.5 - 0.5 * math.cos(2 * math.pi * 31.0 * i / SR)) for i in range(voice_n)]
    body = saturate(normalized(apply(throat, growl)), 3.0)
    chest = tone(voice_n, [f * 0.5 for f in freqs])
    ragged = wander(voice_n, 9.0, rng)
    env = shape(voice_n, [(0, 0.0), (60, 0.7), (450, 1.0), (2200, 0.95), (2650, 0.6), (2900, 0.0)])
    voice_ = apply(mix((1.0, body), (0.35, chest)), [e * (1.0 - 0.18 * r) for e, r in zip(env, ragged)])

    quake = rumble(n, rng, [(0, 0.0), (300, 0.3), (1400, 1.0), (2600, 0.8), (3400, 0.0)], 100.0, (34.0, 38.5))
    shake = rattle(n, rng, [(0, 0.5), (400, 8.0), (1300, 60.0), (2400, 45.0), (3200, 4.0)], 1400.0, 4200.0)
    dust = apply(lp(noise(n, rng), 1800.0), shape(n, [(0, 0.0), (900, 0.3), (2400, 0.5), (3400, 0.0)]))

    x = mix((1.0, voice_ + [0.0] * (n - voice_n)), (0.6, normalized(quake)), (0.22, normalized(shake)),
            (0.12, normalized(dust)))
    x = echoes(x, [(118.0, 0.24, 2400.0), (236.0, 0.17, 1800.0), (372.0, 0.11, 1300.0), (541.0, 0.07, 900.0)])
    return densify(hp(lp(x, 11000.0), 28.0), 4.0)


def densify(x, drive_db):
    """Drives the sound into a soft ceiling so its peaks are rounded off by about drive_db: a big sound gets
    louder at the same -3 dBFS peak, and the few peaks that set its level stop setting it."""
    g = 10.0 ** (drive_db / 20.0)
    return soft_limit([s * g for s in normalized(x)], 1.0)


# ------------------------------------------------------------------------------------------------- attack 1: plates

# A thick iron disc: its modes are far apart and irregular, the base the loudest, the top dying first.
IRON = [(1.00, 1.00, 1.00), (1.72, 0.80, 0.80), (2.31, 0.60, 0.65), (3.02, 0.45, 0.50), (3.91, 0.30, 0.40),
        (4.63, 0.20, 0.30), (5.80, 0.12, 0.22)]


def plate_throw():
    """A 20 kg plate flung like a discus: air torn open around it, fluttering at the spin, and the weight of it
    going past low down."""
    rng = random.Random(3310)
    n = samples(460)
    air = swish(n, rng, [(0, 350.0), (150, 1600.0), (460, 800.0)], 1.3)
    spin_rate = contour(n, [(0, 14.0), (460, 20.0)])
    phase, flutter = 0.0, []
    for r in spin_rate:
        flutter.append(0.5 + 0.5 * math.cos(phase))
        phase += 2.0 * math.pi * r / SR
    air = apply(air, [0.5 + 0.5 * f for f in flutter])
    mass = tone(n, contour(n, [(0, 85.0), (200, 120.0), (460, 95.0)]))
    x = mix((1.0, normalized(air)), (0.3, apply(mass, shape(n, [(0, 0.0), (40, 1.0), (180, 0.2), (400, 0.0)]))))
    return apply(x, shape(n, [(0, 0.0), (60, 0.8), (150, 1.0), (460, 0.0)]))


PLATE_SPIN_MS = 1000.0
PLATE_SPIN_HZ = 12.0


def plate_spin():
    """The plate in flight, as a loop: a whistle off its rim and the air it chops, pulsing twelve times a turn of
    the loop, over a low hum. Every tone is a whole number of cycles in the loop and every filter runs periodic,
    so it loops without a seam. Plates in flight together sound best started at different offsets."""
    rng = random.Random(3311)
    n = samples(PLATE_SPIN_MS)
    turn = pulse_shape(n, PLATE_SPIN_HZ, 1.5)
    whistle = mix((1.0, tone(n, [660.0] * n)), (0.35, tone(n, [1320.0] * n, 1.0, 0.7)),
                  (0.25, tone(n, [1587.0] * n, 1.0, 2.1)))
    chop = periodic(lambda s, state: resonator(s, 900.0, 1.2, state=state), noise(n, rng))
    hum = mix((1.0, tone(n, [110.0] * n)), (0.4, tone(n, [220.0] * n, 1.0, 0.4)))
    x = mix((0.35, apply(whistle, [0.6 + 0.4 * t for t in turn])),
            (1.0, apply(normalized(chop), [0.35 + 0.65 * t for t in turn])),
            (0.3, apply(hum, [0.8 + 0.2 * t for t in turn])))
    for kind, hz in (("hp", 60.0), ("lp", 7000.0), ("lp", 7000.0)):
        x = periodic_biquad(x, kind, hz)
    return x


def plate_bounce(variant=1):
    """A plate glancing off the edge of the ring: a hard knock, the disc ringing out, a thud from the post, and a
    chatter or two as it wobbles away. Three variants, so a string of bounces never repeats itself."""
    base, seed, chatter = {1: (318.0, 3312, (46.0, 97.0)), 2: (339.0, 3313, (38.0, 84.0)),
                           3: (298.0, 3314, (55.0, 118.0))}[variant]
    rng = random.Random(seed)
    n = samples(560)
    ring = normalized(metal(n, base, IRON, 460.0, rng, bend=1.03, glide_ms=5.0, twins=2, twin_cents=7.0))
    knock = crack(n, rng, 800.0, 7000.0, 3.0, 5.0)
    post = normalized(thump(n, [(0, 170.0), (20, 110.0), (150, 90.0)], 160.0, 0.5, harmonics=((1, 1.0), (2, 0.3))))
    x = mix((1.0, ring), (0.7, knock), (0.7, post))
    for at, level in zip(chatter, (0.35, 0.18)):
        k = n - samples(at)
        place(x, normalized(metal(k, base * 1.02, IRON[:4], 90.0, rng, bend=1.02, glide_ms=3.0)), at, level)
    return x


def plate_bounce_1():
    return plate_bounce(1)


def plate_bounce_2():
    return plate_bounce(2)


def plate_bounce_3():
    return plate_bounce(3)


def plate_parry():
    """A plate parried, laid over the shared parry sound: the plate struck square and ringing bright and long, a
    zing as it is knocked spinning away, and the air behind it."""
    rng = random.Random(3315)
    n = samples(820)
    bright = [(r, a * (1.0 + 0.25 * k), d) for k, (r, a, d) in enumerate(IRON)]
    ring = normalized(metal(n, 425.0, bright, 720.0, rng, bend=1.05, glide_ms=8.0, twins=3, twin_cents=6.0))
    knock = crack(n, rng, 1200.0, 10000.0, 3.5, 6.0)
    zing_n = samples(260)
    zing = apply(tone(zing_n, contour(zing_n, [(0, 2100.0), (260, 5200.0)])), decay(zing_n, 260.0, 4.0))
    away = swish(samples(300), rng, [(0, 1800.0), (300, 500.0)], 1.5, [(0, 0.0), (30, 1.0), (300, 0.0)])
    x = mix((1.0, ring), (0.8, knock))
    place(x, zing, 20.0, 0.25)
    place(x, normalized(away), 40.0, 0.3)
    return x


# ------------------------------------------------------------------------------------------------- attack 1: the slams

def barbell_slam():
    """The one-plate barbell brought down like a hammer: the plate clanging into the floor, the floor taking it
    with a deep drop, the steel bar ringing on, the canvas cracking and grit skittering, and a puff of dust."""
    rng = random.Random(3320)
    n = samples(1400)
    plate = normalized(metal(n, 152.0, IRON, 460.0, rng, bend=1.05, glide_ms=8.0, twins=2, twin_cents=9.0))
    floor = normalized(thump(n, [(0, 96.0), (30, 58.0), (260, 40.0), (1400, 36.0)], 950.0, 1.0,
                             harmonics=((1, 1.0), (2, 0.45), (3, 0.18))))
    front = crack(n, rng, 500.0, 9000.0, 5.0, 6.0)
    bar = mix((1.0, tone(n, [884.0] * n)), (0.6, tone(n, [889.0] * n, 1.0, 1.0)), (0.35, tone(n, [2436.0] * n)))
    bar = apply(bar, decay(n, 760.0, 2.0))
    grit = debris(n, rng, 16, 25.0, 520.0, (0.1, 0.5), (300.0, 900.0), 1.6)
    dust = apply(lp(noise(n, rng), 900.0), decay(n, 500.0, 25.0))
    low = saturate(normalized(mix((1.0, floor), (0.6, plate))), 1.6)
    x = mix((1.1, low), (0.55, plate), (0.7, front), (0.12, bar), (0.35, normalized(grit)), (0.2, normalized(dust)))
    return densify(hp(lp(x, 12000.0), 28.0), 3.5)


def teleport_out():
    """He blinks out: the air sucked up after him in a rising zip, a crackle of the cannon's energy, and the pop
    of the space he left closing."""
    rng = random.Random(3321)
    n = samples(330)
    zip_ = swish(n, rng, [(0, 300.0), (260, 4200.0), (330, 4200.0)], 2.0, [(0, 0.0), (40, 0.7), (250, 1.0), (285, 0.0)])
    whine = apply(oscillator(contour(n, [(0, 140.0), (270, 900.0)]), [(1, 1.0), (2, 0.35), (3, 0.15)]),
                  shape(n, [(0, 0.0), (30, 0.6), (250, 1.0), (280, 0.0)]))
    zap = sparks(n, rng, 0.0, 200.0, 180.0)
    pop = [0.0] * n
    place(pop, apply(tone(samples(45), [95.0] * samples(45)), decay(samples(45), 45.0, 1.0)), 278.0)
    return mix((1.0, normalized(zip_)), (0.45, whine), (0.35, normalized(zap)), (0.6, pop))


def teleport_in():
    """He blinks in: the zip falling, the crackle, and 120 kg of bodybuilder landing on the canvas."""
    rng = random.Random(3322)
    n = samples(420)
    zip_ = swish(n, rng, [(0, 3800.0), (220, 300.0), (420, 250.0)], 2.0, [(0, 0.0), (25, 1.0), (200, 0.6), (240, 0.0)])
    whine = apply(oscillator(contour(n, [(0, 900.0), (220, 130.0)]), [(1, 1.0), (2, 0.35), (3, 0.15)]),
                  shape(n, [(0, 0.0), (20, 1.0), (200, 0.5), (230, 0.0)]))
    zap = sparks(n, rng, 0.0, 180.0, 180.0)
    land_n = n - samples(215)
    land = mix((1.0, normalized(thump(land_n, [(0, 130.0), (25, 70.0), (205, 55.0)], 220.0, 0.8,
                                      harmonics=((1, 1.0), (2, 0.4))))),
               (0.35, burst(land_n, rng, 260.0, 1.2, 40.0)))
    x = mix((0.9, normalized(zip_)), (0.4, whine), (0.3, normalized(zap)))
    place(x, land, 215.0, 1.0)
    return x


ERUPTION_MS = 2000.0


def eruption_rumble():
    """The ground about to go, as a loop to run from the slam to the eruption: a deep churning rumble swelling
    three times a turn, two low tones beating against it, grit grinding and knocking under the canvas, and a hiss
    of pressure. The fight rides its volume and pitch up as the eruption nears (the scene preview ramps it from
    -12 dB to 0 and from pitch 0.9 to 1.15). Loops seamlessly, like the plate's hum."""
    rng = random.Random(3323)
    n = samples(ERUPTION_MS)
    low = periodic_biquad(periodic_biquad(noise(n, rng), "lp", 90.0), "lp", 90.0)
    swell = [0.7 + 0.3 * math.cos(2.0 * math.pi * 1.5 * i / SR) for i in range(n)]
    tones = mix((1.0, tone(n, [36.0] * n)), (0.8, tone(n, [41.5] * n, 1.0, 1.3)))
    grind = periodic(lambda s, state: resonator(s, 700.0, 1.5, state=state), crackle(n, rng, 90.0, 2.5))
    knock = periodic(lambda s, state: resonator(s, 180.0, 3.0, state=state), crackle(n, rng, 9.0, 6.0))
    hiss = apply(periodic(lambda s, state: resonator(s, 1200.0, 0.8, state=state), noise(n, rng)),
                 [0.6 + 0.4 * math.cos(2.0 * math.pi * 4.0 * i / SR) for i in range(n)])
    # The churn a small speaker can play: the same rumble an octave and a half up.
    churn = apply(periodic(lambda s, state: resonator(s, 240.0, 1.1, state=state), noise(n, rng)), swell)
    x = mix((0.7, apply(normalized(low), swell)), (0.3, tones), (0.45, normalized(churn)), (0.55, normalized(grind)),
            (0.6, normalized(knock)), (0.15, normalized(hiss)))
    for kind, hz in (("hp", 25.0), ("lp", 5000.0)):
        x = periodic_biquad(x, kind, hz)
    return x


def eruption_blast():
    """The ground erupting under the marked area: a deep boom with a hard crack at its front, the earth tearing
    open, dirt flung up, rocks raining back down and thinning out, and the dirt settling."""
    rng = random.Random(3324)
    n = samples(1550)
    boom = normalized(thump(n, [(0, 115.0), (35, 62.0), (300, 42.0), (1550, 35.0)], 1150.0, 1.0,
                            harmonics=((1, 1.0), (2, 0.4), (3, 0.15))))
    front = crack(n, rng, 400.0, 10000.0, 6.0, 7.0)
    tear = apply(lp(noise(n, rng), 1500.0), shape(n, [(0, 0.0), (8, 1.0), (200, 0.3), (400, 0.0)]))
    fling = swish(n, rng, [(0, 200.0), (260, 1300.0), (500, 700.0)], 1.2, [(0, 0.0), (20, 1.0), (500, 0.0)])
    rocks = debris(n, rng, 40, 60.0, 1350.0, (0.15, 1.0), (140.0, 520.0), 1.7)
    shower = apply(lp(noise(n, rng), 3000.0), shape(n, [(0, 0.0), (250, 0.0), (400, 0.5), (1550, 0.0)]))
    low = saturate(normalized(mix((1.0, boom), (0.4, normalized(tear)))), 1.8)
    x = mix((1.2, low), (0.7, front), (0.35, normalized(fling)), (0.55, normalized(rocks)), (0.12, normalized(shower)))
    return densify(hp(lp(x, 12000.0), 28.0), 4.5)


# ------------------------------------------------------------------------------------------------- the poses

def flex():
    """A pose struck: the muscles creaking tight like leather under strain, a grunt as he locks it, and the
    competition flash going off on it, a camera pop and a glint over a short brassy hit. The fight can pitch it up
    a little per pose as the hype climbs."""
    rng = random.Random(3330)
    n = samples(700)

    creak_n = samples(340)
    impulses = [0.0] * creak_n
    rates = contour(creak_n, [(0, 35.0), (340, 95.0)])
    i = 0
    while i < creak_n:
        impulses[i] = rng.uniform(0.4, 1.0)
        i += max(1, int(SR / rates[i] * rng.uniform(0.75, 1.25)))
    creak = mix((1.0, resonator(impulses, 320.0, 5.0)), (0.7, resonator(impulses, 740.0, 6.0)),
                (0.35, resonator(impulses, 1500.0, 7.0)))
    creak = apply(normalized(creak), shape(creak_n, [(0, 0.0), (60, 0.35), (320, 1.0), (340, 0.0)]))

    grunt_n = samples(230)
    source = glottal(grunt_n, [(0, 150), (60, 138), (230, 118)], rng, 0.05, 0.4, 1.0)
    grunt = tract(source, [(0, EH), (80, AH), (230, AH)])
    grunt = apply(saturate(normalized(grunt), 2.5), shape(grunt_n, [(0, 0.0), (15, 1.0), (120, 0.6), (230, 0.0)]))

    stab_n = samples(360)
    stab = chord_pad(stab_n, [(164.81, 1.0), (246.94, 0.8), (329.63, 0.7), (415.30, 0.45)], rng,
                     [(0, 900.0), (20, 5000.0), (120, 2200.0), (360, 900.0)], harmonics=30)
    stab = apply(normalized(stab), shape(stab_n, [(0, 0.0), (8, 1.0), (90, 0.7), (360, 0.0)]))
    flash = crack(samples(40), rng, 2500.0, 11000.0, 2.5, 4.0)
    glint = glints(samples(380), [(10.0, 3800.0, 7200.0, 300.0, 1.0)])

    x = [0.0] * n
    place(x, creak, 0.0, 0.55)
    place(x, grunt, 250.0, 0.45)
    place(x, stab, 300.0, 0.6)
    place(x, flash, 300.0, 0.5)
    place(x, glint, 300.0, 0.18)
    return hp(lp(x, 12000.0), 50.0)


# ------------------------------------------------------------------------------------------------- the crowd

def crowd_voice(out, rng, at_ms, length_ms, f0, pitch_shape, vowels, scale, level, jitter=0.03):
    """One voice in the crowd: glottal pulses along pitch_shape (fractions of f0 at fractions of the length)
    through `vowels` (fractions of the length, formant sets), its formants scaled for a smaller or bigger head."""
    k = samples(length_ms)
    freqs = contour(k, [(u * length_ms, f0 * m) for u, m in pitch_shape])
    freqs = vibrato(freqs, rng.uniform(4.5, 6.5), rng.uniform(0.005, 0.02), 0.25 * length_ms, 0.3 * length_ms)
    source = pulse_train(freqs, 0.7, [jitter] * k, [0.05] * k, rng)
    keys = [(u * length_ms, [(hz * scale, q, g) for hz, q, g in v]) for u, v in vowels]
    # Breath pulsing with the voice: a crowd shouts rather than sings.
    voice_ = mix((1.0, normalized(tract(source, keys))), (0.35, normalized(breath(source, rng, 1600.0, 0.7))))
    attack = rng.uniform(40.0, 160.0)
    env = shape(k, [(0, 0.0), (attack, 1.0), (0.65 * length_ms, 0.85), (length_ms, 0.0)])
    place(out, apply(normalized(voice_), env), at_ms, level)


def claps(n, rng, clappers, start_ms, end_ms, env_points):
    """Applause: each clapper at a steady rate of their own, every clap a short burst through their hands' own
    resonance."""
    out = [0.0] * n
    for _ in range(clappers):
        rate = rng.uniform(4.2, 7.0)
        hz = rng.uniform(900.0, 2600.0)
        level = rng.uniform(0.4, 1.0)
        t = start_ms + rng.uniform(0.0, 350.0)
        stop = end_ms - rng.uniform(0.0, 500.0)
        while t < stop:
            k = samples(18.0)
            clap = resonator(apply(noise(k, rng), decay(k, 12.0, 0.2)), hz, 2.0)
            place(out, clap, t, level * rng.uniform(0.7, 1.0))
            t += 1000.0 / rate * rng.uniform(0.9, 1.1)
    return apply(out, shape(n, env_points))


def whistle(n, rng, at_ms, length_ms, hz, glide, level):
    """A two-finger whistle: a pure tone sliding by `glide` and warbling, breathy at the edges."""
    k = samples(length_ms)
    freqs = vibrato(contour(k, [(0, hz), (0.3 * length_ms, hz * glide), (length_ms, hz * glide)]), 6.5, 0.012, 0.0,
                    60.0)
    wave = tone(k, freqs)
    air = bandpass(noise(k, rng), hz, 4.0)
    env = shape(k, [(0, 0.0), (35, 1.0), (length_ms - 60, 0.9), (length_ms, 0.0)])
    out = [0.0] * n
    place(out, apply(mix((1.0, wave), (0.25, normalized(air))), env), at_ms, level)
    return out


def crowd_bed(n, rng, low_hz, high_hz, points):
    """The body of the crowd: a wide band of noise wandering in level, the thousand voices too far to tell apart."""
    band = lp(lp(hp(noise(n, rng), low_hz), high_hz), high_hz)
    moving = wander(n, 3.0, rng)
    return apply(band, [e * (0.75 + 0.25 * m) for e, m in zip(shape(n, points), moving)])


CHEER_VOWELS = [
    [(0.0, EE), (0.25, EH), (1.0, AH)],   # "yeah"
    [(0.0, OO), (1.0, OO)],               # "woo"
    [(0.0, AH), (1.0, AH)],               # "ahh"
    [(0.0, EH), (0.5, EH), (1.0, EE)],    # "hey"
]


def crowd_cheer():
    """The crowd going up as the hype climbs: three dozen voices yelling "yeah", "woo" and "hey" at their own
    pitches and moments, rising as they go, applause coming in under them, a few whistles, and the roar of the
    rest behind, swelling for a second and falling away, thrown back by the arena."""
    rng = random.Random(3340)
    n = samples(2900)
    voices = [0.0] * n
    for v in range(36):
        female = rng.random() < 0.35
        f0 = rng.uniform(185.0, 290.0) if female else rng.uniform(105.0, 175.0)
        scale = rng.uniform(1.1, 1.22) if female else rng.uniform(0.92, 1.05)
        length = rng.uniform(900.0, 1900.0)
        at = rng.uniform(0.0, 700.0)
        rise = rng.uniform(1.08, 1.22)
        crowd_voice(voices, rng, at, length, f0, [(0.0, 0.92), (0.3, rise), (0.8, rise * 0.97), (1.0, rise * 0.9)],
                    CHEER_VOWELS[v % len(CHEER_VOWELS)], scale, rng.uniform(0.5, 1.0))
    applause = claps(n, rng, 28, 250.0, 2700.0, [(0, 0.0), (500, 0.6), (1300, 1.0), (2300, 0.6), (2900, 0.0)])
    whistles = mix(*[(1.0, whistle(n, rng, at, length, hz, glide, level)) for at, length, hz, glide, level in
                     ((420.0, 620.0, 2650.0, 1.12, 0.7), (980.0, 480.0, 3050.0, 1.08, 0.5),
                      (1500.0, 560.0, 2400.0, 1.15, 0.55))])
    bed = crowd_bed(n, rng, 350.0, 2600.0, [(0, 0.0), (500, 0.7), (1200, 1.0), (2200, 0.6), (2900, 0.0)])
    swell = shape(n, [(0, 0.0), (650, 0.9), (1200, 1.0), (2000, 0.75), (2900, 0.0)])
    x = mix((1.0, apply(normalized(voices), swell)), (0.35, normalized(applause)), (0.16, whistles),
            (0.5, normalized(bed)))
    x = echoes(x, [(71.0, 0.2, 3000.0), (143.0, 0.14, 2200.0), (229.0, 0.09, 1600.0), (347.0, 0.05, 1100.0)])
    return hp(lp(x, 10000.0), 90.0)


BOO_VOWELS = [[(0.0, [(300.0, 4.0, 1.0), (700.0, 5.0, 0.3), (2200.0, 6.0, 0.08)]), (0.12, OO), (1.0, OO)]]


def crowd_boo():
    """The crowd turning on him as the hype drains: thirty low "boooo"s sagging as they go, a couple of falling
    whistles, and a darker, duller roar under them."""
    rng = random.Random(3341)
    n = samples(2600)
    voices = [0.0] * n
    for _ in range(30):
        female = rng.random() < 0.2
        f0 = rng.uniform(170.0, 235.0) if female else rng.uniform(92.0, 150.0)
        scale = rng.uniform(1.08, 1.18) if female else rng.uniform(0.92, 1.04)
        length = rng.uniform(1000.0, 2000.0)
        at = rng.uniform(0.0, 550.0)
        sag = rng.uniform(0.86, 0.95)
        crowd_voice(voices, rng, at, length, f0, [(0.0, 1.0), (0.2, 1.02), (1.0, sag)], BOO_VOWELS[0], scale,
                    rng.uniform(0.55, 1.0), jitter=0.035)
    whistles = mix((1.0, whistle(n, rng, 700.0, 700.0, 2900.0, 0.78, 0.6)),
                   (1.0, whistle(n, rng, 1350.0, 600.0, 2600.0, 0.8, 0.45)))
    bed = crowd_bed(n, rng, 180.0, 1300.0, [(0, 0.0), (400, 0.8), (1600, 1.0), (2600, 0.0)])
    swell = shape(n, [(0, 0.0), (450, 1.0), (1700, 0.9), (2600, 0.0)])
    x = mix((1.0, apply(normalized(voices), swell)), (0.12, whistles), (0.45, normalized(bed)))
    x = echoes(x, [(71.0, 0.2, 2400.0), (143.0, 0.14, 1800.0), (229.0, 0.09, 1300.0), (347.0, 0.05, 900.0)])
    return hp(lp(x, 8000.0), 80.0)


# ------------------------------------------------------------------------------------------------- the spirit bomb

SPIRIT_CHARGE_MS = 3600.0


def spirit_charge():
    """The crowd's energy gathering over the cannon: a hum winding up under it, the crowd itself as a choir on an
    A major chord rising three semitones, glowing orbs whistling up into the bomb faster and faster, a shimmer
    thickening on top and a riser pulling the whole thing up to the launch. It ends at full tilt: the launch
    takes over from it."""
    rng = random.Random(3350)
    n = samples(SPIRIT_CHARGE_MS)
    lift = contour(n, [(0, 1.0), (SPIRIT_CHARGE_MS, 2.0 ** (3.0 / 12.0))])

    hum = oscillator([55.0 * f for f in contour(n, [(0, 1.0), (SPIRIT_CHARGE_MS, 1.5)])],
                     [(k, 1.0 / k) for k in range(1, 14)])
    hum = apply(lp(hum, 800.0), shape(n, [(0, 0.2), (SPIRIT_CHARGE_MS, 1.0)]))

    choir = [0.0] * n
    for hz, gain in ((110.0, 0.8), (164.81, 0.9), (220.0, 1.0), (277.18, 0.8), (329.63, 0.7)):
        for detune in (0.997, 1.004):
            freqs = vibrato([hz * detune * f for f in lift], rng.uniform(4.8, 5.8), 0.008, 300.0, 600.0)
            source = pulse_train(freqs, 0.7, [0.01] * n, [0.0] * n, rng)
            choir = mix((1.0, choir), (gain, tract(source, [(0, OH), (1200, AH), (SPIRIT_CHARGE_MS, AH)])))
    choir = apply(normalized(choir), shape(n, [(0, 0.0), (600, 0.35), (SPIRIT_CHARGE_MS, 1.0)]))

    orbs = [0.0] * n
    t = 150.0
    while t < SPIRIT_CHARGE_MS - 250.0:
        u = t / SPIRIT_CHARGE_MS
        length = rng.uniform(180.0, 320.0)
        k = samples(length)
        start = rng.uniform(450.0, 800.0) * (1.0 + 0.6 * u)
        glide = tone(k, contour(k, [(0, start), (length, start * rng.uniform(2.2, 3.0))]))
        env = shape(k, [(0, 0.0), (0.4 * length, 1.0), (length, 0.0)])
        place(orbs, apply(glide, env), t, rng.uniform(0.4, 1.0))
        t += rng.expovariate(1.0 / (220.0 - 150.0 * u))
    air = apply(bandpass(highpass(noise(n, rng), 4500.0), 7000.0, 0.8),
                [(0.6 + 0.4 * math.sin(2.0 * math.pi * r * i / SR)) for i, r in
                 enumerate(contour(n, [(0, 18.0), (SPIRIT_CHARGE_MS, 38.0)]))])
    air = apply(air, shape(n, [(0, 0.0), (SPIRIT_CHARGE_MS, 1.0)]))
    riser = tone(n, [300.0 * 4.0 ** (i / n) for i in range(n)])
    riser = apply(riser, shape(n, [(0, 0.0), (1000, 0.2), (SPIRIT_CHARGE_MS, 1.0)]))

    x = mix((0.45, normalized(hum)), (1.0, choir), (0.22, normalized(orbs)), (0.1, normalized(air)), (0.12, riser))
    x = echoes(x, [(83.0, 0.18, 4000.0), (167.0, 0.12, 3000.0), (251.0, 0.07, 2000.0)])
    return hp(lp(x, 12000.0), 35.0)


def spirit_launch():
    """The bomb thrown: a vast rushing "VWOOOM" as it leaves the cannon, a drop to the floor of hearing under it,
    a harmonic roar sweeping down as it closes, and the whine of it coming at the player."""
    rng = random.Random(3351)
    n = samples(1500)
    rush = swish(n, rng, [(0, 150.0), (350, 900.0), (1500, 260.0)], 1.0, [(0, 0.0), (80, 1.0), (900, 0.7), (1500, 0.0)])
    drop = apply(tone(n, contour(n, [(0, 90.0), (1200, 34.0)])), shape(n, [(0, 0.0), (60, 1.0), (1500, 0.0)]))
    roar_ = chord_pad(n, [(600.0, 1.0), (606.0, 0.8), (900.0, 0.5)], rng, [(0, 3000.0), (1500, 600.0)], voices=2,
                      harmonics=12)
    sweep_down = contour(n, [(0, 1.0), (1500, 0.25)])
    roar_ = apply(normalized(roar_), shape(n, [(0, 0.0), (100, 1.0), (1500, 0.0)]))
    whine = apply(tone(n, [2100.0 * s for s in sweep_down]), shape(n, [(0, 0.0), (300, 0.6), (1400, 0.0)]))
    x = mix((1.0, normalized(rush)), (0.8, drop), (0.3, roar_), (0.12, whine))
    return densify(hp(lp(x, 12000.0), 25.0), 2.0)


def spirit_explosion():
    """The bomb landing, the biggest sound in the fight: a crack and a boom that falls to the bottom of hearing,
    a white-hot wash of noise darkening as it spreads, the energy crackling through it, a pale blue shimmer ringing
    over the whiteout, and the ground rumbling on. The flashes it plays under are the fight's; at most three a
    second."""
    rng = random.Random(3352)
    n = samples(3300)
    front = crack(n, rng, 300.0, 12000.0, 9.0, 8.0)
    boom = normalized(thump(n, [(0, 95.0), (40, 55.0), (500, 32.0), (3300, 28.0)], 3000.0, 1.0,
                            harmonics=((1, 1.0), (2, 0.5), (3, 0.2), (4, 0.08))))
    cut = contour(n, [(0, 9000.0), (500, 4500.0), (1600, 1800.0), (3300, 500.0)])
    y1 = y2 = 0.0
    wash = []
    for s, fc in zip(noise(n, rng), cut):
        a = 1.0 - math.exp(-2.0 * math.pi * fc / SR)
        y1 += a * (s - y1)
        y2 += a * (y1 - y2)
        wash.append(y2)
    wash = apply(normalized(wash), shape(n, [(0, 0.0), (15, 1.0), (900, 0.55), (3300, 0.0)]))
    energy = sparks(n, rng, 0.0, 1800.0, 260.0, 1.2)
    shimmer = mix(*[(a, tone(n, [hz] * n, 1.0, rng.uniform(0, 6.28))) for hz, a in
                    ((2200.0, 1.0), (2213.0, 0.8), (3100.0, 0.6), (3121.0, 0.5), (4400.0, 0.3))])
    shimmer = apply(shimmer, shape(n, [(0, 0.0), (120, 1.0), (1400, 0.5), (3000, 0.0)]))
    ground = rumble(n, rng, [(0, 0.0), (200, 1.0), (2000, 0.6), (3300, 0.0)], 90.0, (31.0, 34.5))
    low = saturate(normalized(mix((1.0, boom), (0.6, normalized(ground)))), 2.0)
    x = mix((0.6, low), (1.0, front), (1.3, wash), (0.5, normalized(energy)), (0.09, normalized(shimmer)))
    x = echoes(x, [(97.0, 0.2, 2500.0), (211.0, 0.13, 1600.0), (353.0, 0.08, 1000.0)])
    return densify(hp(lp(x, 12500.0), 22.0), 8.0)


def disintegrate():
    """The player coming apart: thousands of tiny bright grains fizzing up out of the sprite, thickest a moment
    in and climbing in pitch as they scatter, carried off on a soft rush of air, the last few glittering out."""
    rng = random.Random(3353)
    n = samples(2100)
    fizz = [0.0] * n
    density = contour(n, [(0, 200.0), (450, 1400.0), (1200, 700.0), (1900, 80.0), (2100, 0.0)])
    t = 0
    while t < n:
        rate = max(density[t], 20.0)
        t += max(1, int(rng.expovariate(rate) * SR))
        if t >= n:
            break
        u = t / n
        hz = rng.uniform(2000.0, 5500.0) * (1.0 + 0.9 * u)
        length = samples(rng.uniform(1.5, 4.0))
        grain = [math.sin(2.0 * math.pi * hz * j / SR) * (0.5 - 0.5 * math.cos(2.0 * math.pi * j / length))
                 for j in range(length)]
        place(fizz, grain, t * 1000.0 / SR, rng.uniform(0.3, 1.0))
    drift = swish(n, rng, [(0, 700.0), (1400, 3200.0), (2100, 4000.0)], 1.0,
                  [(0, 0.0), (300, 0.8), (1200, 0.6), (2100, 0.0)])
    glitter = glints(n, [(1500.0, 5200.0, 8800.0, 400.0, 1.0), (1650.0, 6000.0, 9500.0, 350.0, 0.7)])
    x = mix((1.0, normalized(fizz)), (0.3, normalized(drift)), (0.1, glitter))
    return hp(lp(x, 12500.0), 200.0)


# ------------------------------------------------------------------------------------------------- the final brawl

def brawl_debris():
    """The roof giving way under his slams: a crack and a groan overhead, the arena rumbling, rocks and chunks of
    roof coming down all over the ring, three big ones landing hard, and dust hissing down after them."""
    rng = random.Random(3360)
    n = samples(3500)
    groan_n = samples(900)
    impulses = [0.0] * groan_n
    i = 0
    while i < groan_n:
        impulses[i] = rng.uniform(0.3, 1.0)
        i += max(1, int(SR / rng.uniform(18.0, 40.0)))
    groan = mix((1.0, resonator(impulses, 150.0, 8.0)), (0.6, resonator(impulses, 330.0, 9.0)))
    groan = apply(normalized(groan), shape(groan_n, [(0, 0.0), (80, 1.0), (900, 0.0)]))
    split = crack(samples(300), rng, 400.0, 9000.0, 25.0, 5.0)
    shake = rumble(n, rng, [(0, 0.0), (300, 0.8), (1800, 1.0), (3500, 0.0)], 100.0, (39.0, 44.5))
    rocks = debris(n, rng, 70, 250.0, 3300.0, (0.15, 0.9), (150.0, 560.0), 1.15)
    chunks = [0.0] * n
    for at in (700.0, 1480.0, 2260.0):
        k = samples(600)
        chunk = mix((1.0, normalized(thump(k, [(0, 110.0), (30, 60.0), (600, 45.0)], 500.0, 0.5,
                                           harmonics=((1, 1.0), (2, 0.4))))),
                    (0.9, crack(k, rng, 300.0, 6000.0, 12.0, 4.0)))
        place(chunks, chunk, at, 1.0)
    dust = apply(bandpass(noise(n, rng), 2200.0, 0.6), shape(n, [(0, 0.0), (1000, 0.4), (3500, 0.0)]))
    x = mix((0.5, groan + [0.0] * (n - groan_n)), (0.6, split + [0.0] * (n - len(split))), (0.45, normalized(shake)),
            (1.0, normalized(rocks)), (0.7, normalized(chunks)), (0.08, normalized(dust)))
    return densify(hp(lp(x, 12000.0), 28.0), 6.0)


def brawl_hook():
    """His hook: a wide, heavy swing, the air rising and falling across the arc, the weight of the arm under it
    and a flick of his shirt as it starts."""
    rng = random.Random(3361)
    n = samples(300)
    air = swish(n, rng, [(0, 350.0), (130, 1400.0), (300, 600.0)], 1.2, [(0, 0.0), (40, 0.6), (130, 1.0), (300, 0.0)])
    arm = apply(tone(n, contour(n, [(0, 110.0), (300, 88.0)])), shape(n, [(0, 0.0), (50, 1.0), (220, 0.0)]))
    flick = apply(bandpass(noise(n, rng), 4000.0, 1.0), shape(n, [(0, 0.0), (5, 1.0), (40, 0.0)]))
    return mix((1.0, normalized(air)), (0.35, arm), (0.12, normalized(flick)))


def brawl_straight():
    """His straight: quick and direct, a short bright tear of air with a snap at full extension."""
    rng = random.Random(3362)
    n = samples(200)
    air = swish(n, rng, [(0, 700.0), (60, 2600.0), (200, 1500.0)], 1.6, [(0, 0.0), (12, 0.8), (60, 1.0), (200, 0.0)])
    snap = [0.0] * n
    place(snap, crack(samples(20), rng, 3000.0, 10000.0, 3.0, 3.0), 68.0)
    return mix((1.0, normalized(air)), (0.3, snap))


def brawl_punch_hit():
    """A glove landing on the player: a meaty thud, the body taking it, the leather slapping and a crunch in it."""
    rng = random.Random(3363)
    n = samples(380)
    thud = burst(n, rng, 260.0, 1.4, 160.0, 0.4)
    body = normalized(thump(n, [(0, 125.0), (20, 78.0), (180, 68.0)], 260.0, 0.5, harmonics=((1, 1.0), (2, 0.35))))
    smack = burst(n, rng, 720.0, 1.2, 70.0, 0.3)
    slap = crack(n, rng, 900.0, 6000.0, 6.0, 4.0)
    crunch = burst(n, rng, 1500.0, 2.0, 20.0, 0.3)
    x = mix((1.0, thud), (0.6, body), (1.0, slap), (0.45, crunch), (0.5, smack))
    return densify(hp(lp(x, 11000.0), 40.0), 5.0)


def brawl_dodge():
    """The player slipping the punch: a quick light swish and a rustle of clothes."""
    rng = random.Random(3364)
    n = samples(170)
    air = swish(n, rng, [(0, 900.0), (60, 3200.0), (170, 2000.0)], 1.8, [(0, 0.0), (20, 1.0), (170, 0.0)])
    rustle = apply(bandpass(noise(n, rng), 3500.0, 0.9), shape(n, [(0, 0.0), (8, 1.0), (90, 0.0)]))
    return mix((1.0, normalized(air)), (0.25, normalized(rustle)))


def blip_note(hz, ms, attack_ms=2.0):
    n = samples(ms)
    wave = oscillator([hz] * n, [(1, 1.0), (2, 0.3), (3, 0.1)])
    return apply(wave, envelope(n, attack_ms, ms * 0.5, decay_ms=ms * 0.9))


def brawl_tell():
    """The arrow over his head: a crisp rising two-note blip, E6 then B6, so it reads as "go" in the time the
    telegraph gives."""
    rng = random.Random(3365)
    n = samples(150)
    x = [0.0] * n
    place(x, crack(samples(10), rng, 4000.0, 11000.0, 1.0, 2.0), 0.0, 0.15)
    place(x, blip_note(1318.5, 45.0), 0.0, 0.8)
    place(x, blip_note(1975.5, 80.0), 55.0, 1.0)
    return x


def brawl_tell_parry():
    """The red "parry this" indicator: unlike the arrow, a low, gritty double pulse falling a step, A4 then G4,
    so the ear tells the two apart before the eye does."""
    n = samples(190)
    x = [0.0] * n
    for at, hz in ((0.0, 440.0), (85.0, 392.0)):
        k = samples(70)
        wave = oscillator([hz] * k, [(1, 1.0), (3, 0.45), (5, 0.25), (7, 0.12)])
        wave = saturate(normalized(wave), 1.8)
        place(x, apply(wave, envelope(k, 2, 25, decay_ms=65)), at)
    return lp(x, 6000.0)


# ------------------------------------------------------------------------------------------------- his voice

def gym_bro_blips():
    """His dialogue blip, loud and hyped: a chesty ~205 Hz bark that jumps up into its note like he can't wait to
    say it, through a "yeah", a "bro" or a "huh!", with a breathy "h" in front and the grit of a man who talks at
    gym volume. Deeper and pushier than Matt's friendly "bwah", brighter and more excited than the Captain's
    swaggering "hah". Loudness-matched like every other voice (make_voices.finish)."""
    return [make_voices.finish(x) for x in gym_bro_raw()]


def gym_bro_raw():
    """gym_bro_blips' variants before make_voices.finish, which make_voices.voice_greyson hands on as they are, so
    its own finish writes the same files as the ship here."""
    variants = []
    shapes = [
        (205.0, [(0, 0.97), (22, 1.08), (66, 1.05)], [(0, EE), (18, EH), (66, AH)], 3371),   # "yeah"
        (196.0, [(0, 1.0), (20, 1.07), (66, 1.02)], [(0, RR), (22, OH), (66, OH)], 3372),    # "bro"
        (214.0, [(0, 0.98), (18, 1.1), (62, 1.04)], [(0, AH), (62, AH)], 3373),              # "huh!"
    ]
    for f0, pitch_points, vowels, seed in shapes:
        rng = random.Random(seed)
        n = samples(pitch_points[-1][0])
        buzz = oscillator(contour(n, [(ms, f0 * m) for ms, m in pitch_points]), pulse(0.3, 40))
        voice_ = tract(buzz, vowels)
        voice_ = mix((1.0, normalized(voice_)), (0.3, normalized(bandpass(buzz, 2600.0, 2.2))))
        h = apply(bandpass(noise(n, rng), 1800.0, 1.0), envelope(n, 0.5, 5.0, decay_ms=10.0))
        x = mix((1.0, saturate(normalized(voice_), 2.2)), (0.25, normalized(h)))
        variants.append(mul(lowpass(x, 6500.0), envelope(n, 2.0, 16.0, decay_ms=85.0)))
    return variants


# The DialogueVoices.gd entry proposed for him: the widest pitch spread of anyone and a melody that keeps
# bumping up, because he is always hyping; blips every third letter; the loudest voice in the game.
GREYSON_VOICE = {
    "pitch_min": 0.96,
    "pitch_max": 1.08,
    "melody": [1.0, 1.08, 1.0, 1.15],
    "every": 3,
    "volume_db": 3.0,
}
VOICE_LINES = [
    "That was my gym partner. I hit my first 225 on bench with this little guy. That was a long time ago. Now "
    "you've really messed up.",
    "What Computah didn't know was that this cannon is fueled by the crowd's energy... but I know how to get them "
    "going.",
    "Pal, you won't like what comes next.",
]


def voice_lines(blips):
    """His three cutscene lines typed and voiced the way the game does it (make_voices.typed_letters,
    voiced_blips and render) with GREYSON_VOICE, then the first line again in his current voice to compare."""
    sounds = {"new_%d" % (k + 1): x for k, x in enumerate(blips)}
    new = dict(GREYSON_VOICE, streams=sorted(sounds))
    gap_ms, _, table = make_voices.read_table()
    out = []
    for k, text in enumerate(VOICE_LINES):
        line, _ = make_voices.render(make_voices.voiced_blips(make_voices.typed_letters(text), new, gap_ms,
                                                             random.Random("greyson%d" % k)), new["volume_db"], sounds)
        out += line + [0.0] * samples(600)
    old = table.get("greyson")
    if old:
        for path in old["streams"]:
            sounds[path] = make_voices.read_wav(path)
        line, _ = make_voices.render(make_voices.voiced_blips(make_voices.typed_letters(VOICE_LINES[0]), old, gap_ms,
                                                             random.Random("greyson0")), old["volume_db"], sounds)
        out += [0.0] * samples(600) + line
    return out


# ------------------------------------------------------------------------------------------------- the plan's extra keys

def stomp(variant=1):
    """One heavy bodybuilder step onto the ring: the weight going into the mat in a deep drop, the canvas taking
    the boot, the boards under it booming for a moment and the sole scuffing. Two variants, left foot and right,
    since the walk steps every 0.30 s (GreysonTakeover STEP_FRAMES) and one sound would machine-gun."""
    f, seed, scuff_at = {1: (1.0, 3380, 6.0), 2: (0.93, 3381, 11.0)}[variant]
    rng = random.Random(seed)
    n = samples(420)
    heel = normalized(thump(n, [(0, 95.0 * f), (18, 62.0 * f), (160, 50.0 * f)], 240.0, 0.6,
                            harmonics=((1, 1.0), (2, 0.4), (3, 0.12))))
    canvas = burst(n, rng, 380.0 * f, 1.1, 45.0, 0.4)
    hit = apply(noise(n, rng), decay(n, 25.0, 0.3))
    boards = normalized(mix((1.0, resonator(hit, 108.0 * f, 6.0)), (0.7, resonator(hit, 171.0 * f, 5.0))))
    scuff = [0.0] * n
    place(scuff, apply(bandpass(noise(samples(70), rng), 3200.0, 1.0), shape(samples(70), [(0, 0.0), (4, 1.0),
                                                                                           (70, 0.0)])), scuff_at)
    # The heel's knock, so a small speaker hears the step as well as a big one feels it.
    knock = burst(n, rng, 900.0 * f, 1.5, 15.0, 0.2)
    x = mix((1.0, heel), (0.9, canvas), (0.45, boards), (0.35, knock), (0.12, normalized(scuff)))
    return densify(hp(lp(x, 11000.0), 30.0), 2.0)


def stomp_1():
    return stomp(1)


def stomp_2():
    return stomp(2)


def spark():
    """The torn wires on Computah's empty socket arcing: five zaps of buzzing current, each struck with a crack,
    spitting sparks that thin out, a hiss under them. One-shot, and fine retriggered at random for a longer spell."""
    rng = random.Random(3382)
    n = samples(900)
    x = [0.0] * n
    for at, level in ((0.0, 1.0), (140.0, 0.7), (310.0, 0.85), (520.0, 0.5), (700.0, 0.35)):
        k = samples(rng.uniform(45.0, 110.0))
        zap = apply(buzz(k, rng.choice((100.0, 120.0)), rng, 60.0, 0.7), shape(k, [(0, 1.0), (k * 1000.0 / SR, 0.0)]))
        place(x, normalized(zap), at, 0.55 * level)
        place(x, crack(samples(12), rng, 2000.0, 12000.0, 1.2, 4.0), at, 0.6 * level)
    spit = sparks(n, rng, 0.0, 900.0, 140.0, 1.3)
    hiss = apply(highpass(noise(n, rng), 5000.0), shape(n, [(0, 0.0), (10, 1.0), (500, 0.4), (900, 0.0)]))
    x = mix((1.0, x), (0.45, normalized(spit)), (0.06, normalized(hiss)))
    return hp(lp(x, 12500.0), 150.0)


SLAM_WINDUP_MS = 400.0


def slam_windup():
    """The barbell hauled overhead in the 0.40 s before each slam (GreysonSlams.windup_time): a rising effort
    growl, the plate clinking on the bar as it comes up, the bar creaking and the air rushing up after it,
    everything peaking at the top and let go at 0.40 s so the slam lands clean."""
    rng = random.Random(3383)
    n = samples(470)
    top = SLAM_WINDUP_MS
    source = glottal(samples(top), [(0, 118), (250, 148), (top, 166)], rng, 0.05, 0.4, 1.0)
    growl = tract(source, [(0, RR), (160, RR), (top, AH)])
    growl = apply(saturate(normalized(growl), 2.8), shape(samples(top), [(0, 0.0), (40, 0.45), (320, 1.0),
                                                                          (top, 0.7)]))
    lift = swish(n, rng, [(0, 250.0), (380, 1500.0), (470, 1700.0)], 1.2,
                 [(0, 0.0), (80, 0.3), (380, 1.0), (430, 0.3), (470, 0.0)])
    clinks = [0.0] * n
    for at, level in ((60.0, 0.6), (150.0, 0.8), (250.0, 1.0)):
        k = samples(90)
        place(clinks, normalized(metal(k, rng.uniform(480.0, 520.0), IRON[:4], 70.0, rng, bend=1.02, glide_ms=3.0)),
              at, level)
    impulses = [0.0] * n
    i = samples(50)
    while i < samples(380):
        impulses[i] = rng.uniform(0.4, 1.0)
        i += max(1, int(SR / rng.uniform(40.0, 70.0)))
    creak = resonator(impulses, 880.0, 12.0)
    x = mix((0.65, growl + [0.0] * (n - samples(top))), (0.5, normalized(lift)), (0.3, clinks),
            (0.12, normalized(creak)))
    return fade_edges(hp(lp(x, 11000.0), 60.0), 0.5, 30.0)


PLATE_DROP_MS = 300.0


def plate_drop():
    """A plate that hit the player knocked back off them: a dull glancing tonk as it goes, a flutter as it tumbles
    back, and a clang onto the mat 0.30 s later, when its drop ends (the plate's drop_time in GreysonArtLayout),
    chattering once or twice as it settles flat."""
    rng = random.Random(3384)
    n = samples(680)
    tonk = normalized(metal(samples(160), 330.0, IRON[:5], 110.0, rng, bend=1.02, glide_ms=4.0))
    flutter = swish(samples(PLATE_DROP_MS), rng, [(0, 600.0), (150, 1100.0), (PLATE_DROP_MS, 700.0)], 1.4,
                    [(0, 0.0), (40, 1.0), (PLATE_DROP_MS, 0.2)])
    land_n = n - samples(PLATE_DROP_MS)
    ring = normalized(metal(land_n, 302.0, IRON, 360.0, rng, bend=1.03, glide_ms=5.0, twins=2, twin_cents=7.0))
    canvas = normalized(thump(land_n, [(0, 140.0), (20, 95.0), (120, 85.0)], 130.0, 0.4, harmonics=((1, 1.0), (2, 0.3))))
    land = mix((1.0, ring), (0.7, canvas), (0.6, crack(land_n, rng, 700.0, 7000.0, 2.5, 4.0)))
    for at, level in ((42.0, 0.3), (78.0, 0.16), (101.0, 0.08)):
        place(land, normalized(metal(land_n - samples(at), 306.0, IRON[:4], 60.0, rng, bend=1.01, glide_ms=2.0)),
              at, level)
    x = [0.0] * n
    place(x, tonk, 0.0, 0.3)
    place(x, normalized(flutter), 0.0, 0.12)
    place(x, land, PLATE_DROP_MS, 1.0)
    return hp(lp(x, 11000.0), 60.0)


def bell(n, hz, decay_ms, rng):
    """A clean struck chime, nearly harmonic, for the cannon's battery."""
    modes = [(1.0, 1.0, 1.0), (2.01, 0.45, 0.7), (3.04, 0.22, 0.5), (4.1, 0.1, 0.35)]
    return metal(n, hz, modes, decay_ms, rng, bend=1.0, glide_ms=1.0, twins=1, twin_cents=3.0, attack_ms=1.5)


def pose_bank():
    """A pose landed clean: the crowd's energy streaming up into the cannon, a rising glide and a swell of air,
    a little spark as it connects, and the battery taking a cell in a bright two-note chime on Computah's own beep
    notes (E6 then A6), shining off. It sits over the crowd cheer rather than in it."""
    rng = random.Random(3385)
    n = samples(880)
    rise_n = samples(210)
    glide = apply(tone(rise_n, contour(rise_n, [(0, 480.0), (210, 1650.0)])), shape(rise_n, [(0, 0.0), (150, 1.0),
                                                                                             (210, 0.3)]))
    air = apply(swept_band(noise(rise_n, rng), contour(rise_n, [(0, 1500.0), (210, 5000.0)]), 1.5),
                shape(rise_n, [(0, 0.0), (180, 1.0), (210, 0.0)]))
    chime = [0.0] * n
    place(chime, normalized(bell(n - samples(200), COMPUTAH_BEEPS[2], 560.0, rng)), 200.0, 1.0)
    place(chime, normalized(bell(n - samples(270), COMPUTAH_BEEPS[3], 620.0, rng)), 270.0, 0.9)
    x = [0.0] * n
    place(x, glide, 0.0, 0.35)
    place(x, normalized(air), 0.0, 0.15)
    place(x, crack(samples(15), rng, 3000.0, 12000.0, 1.0, 3.0), 195.0, 0.25)
    x = mix((1.0, x), (0.8, chime), (0.12, glints(n, [(230.0, 3500.0, 7000.0, 350.0, 1.0)])))
    return hp(lp(x, 12500.0), 200.0)


def pose_spoiled():
    """A pose knocked out of: the battery losing half a cell, a tone sagging and wobbling down like power going
    out of it, a hiss of it escaping, the cannon grumbling in Computah's falling crushed beeps, and a sputter of
    sparks dying away. It sits under the boo, not on it."""
    rng = random.Random(3386)
    n = samples(680)
    fall_n = samples(470)
    sag = vibrato(contour(fall_n, [(0, 880.0), (470, 210.0)]), 9.0, 0.03, 60.0, 120.0)
    power = apply(oscillator(sag, [(1, 1.0), (2, 0.35), (3, 0.18)]), shape(fall_n, [(0, 0.0), (15, 1.0), (300, 0.7),
                                                                                   (470, 0.0)]))
    vent = apply(bandpass(noise(samples(180), rng), 4000.0, 0.8), shape(samples(180), [(0, 0.0), (8, 1.0), (180, 0.0)]))
    sputter = sparks(n, rng, 100.0, 620.0, 40.0, 1.0)
    x = [0.0] * n
    place(x, power, 0.0, 0.7)
    place(x, normalized(vent), 0.0, 0.2)
    place(x, computah_beep(60, COMPUTAH_BEEPS[3]), 120.0, 0.28)
    place(x, computah_beep(95, COMPUTAH_BEEPS[1]), 200.0, 0.28)
    x = mix((1.0, x), (0.3, normalized(sputter)))
    return hp(lp(x, 11000.0), 120.0)


CANNON_HUM_MS = 2000.0


def cannon_hum():
    """The cannon humming on his arm, as a loop the fight rides with his hype: a low 73.5 Hz transformer hum and a
    voice beating once a loop against it, a band of charge in the middle breathing twice a second, and a faint
    capacitor whine on top. Every tone is a whole number of cycles in the 2.0 s loop and every filter runs
    periodic, so it loops without a seam; it holds up from pitch 0.85 to 1.3."""
    rng = random.Random(3387)
    n = samples(CANNON_HUM_MS)
    hum = [0.0] * n
    for hz, gain in ((73.5, 1.0), (74.0, 0.6)):
        cycle = band_limited_cycle([(k, (1.0 / k ** 1.2) * (1.3 if k % 2 else 1.0)) for k in range(1, 31)])
        hum = mix((1.0, hum), (gain, table_tone(cycle, hz, n)))
    hum = periodic_biquad(normalized(hum), "lp", 1400.0)
    charge = periodic(lambda s, state: resonator(s, 620.0, 4.0, state=state), noise(n, rng))
    breathe = [0.6 + 0.4 * math.cos(2.0 * math.pi * 2.0 * i / SR) for i in range(n)]
    whine = apply(tone(n, [2940.0] * n), [0.5 + 0.5 * math.cos(2.0 * math.pi * 0.5 * i / SR) for i in range(n)])
    x = mix((1.0, hum), (0.28, apply(normalized(charge), breathe)), (0.03, whine))
    for kind, hz in (("hp", 35.0), ("lp", 5000.0)):
        x = periodic_biquad(x, kind, hz)
    # Start 0.75 s in, on a breath trough with the two voices apart and the whine low, so the seam and the first
    # play both sit on the loop's quietest stretch. Turning a looped signal keeps it looped.
    start = samples(750.0)
    return x[start:] + x[:start]


def brawl_toss():
    """The barbell landing in the rubble, crash first, so it stays on the frame the existing call plays it on
    (GreysonFinalBrawl._on_barbell_landed): the plate clanging into the heap with a deep thud, the bar ringing,
    the rubble crunching and sliding under it, a smaller second bounce, and loose pieces trickling down after."""
    rng = random.Random(3388)
    n = samples(1400)
    plate = normalized(metal(n, 165.0, IRON, 520.0, rng, bend=1.05, glide_ms=8.0, twins=2, twin_cents=9.0))
    thud = normalized(thump(n, [(0, 110.0), (30, 64.0), (400, 52.0)], 420.0, 0.6, harmonics=((1, 1.0), (2, 0.4))))
    bar = apply(mix((1.0, tone(n, [884.0] * n)), (0.6, tone(n, [889.0] * n, 1.0, 1.0)), (0.35, tone(n, [2436.0] * n))),
                decay(n, 700.0, 2.0))
    front = crack(n, rng, 500.0, 9000.0, 6.0, 6.0)
    crunch = debris(n, rng, 34, 0.0, 700.0, (0.1, 0.7), (200.0, 700.0), 2.0)
    slide = apply(lp(noise(n, rng), 1200.0), shape(n, [(0, 0.0), (15, 1.0), (500, 0.25), (800, 0.0)]))
    trickle = debris(n, rng, 14, 450.0, 1250.0, (0.05, 0.3), (400.0, 1000.0), 1.0)
    x = mix((1.0, plate), (1.0, thud), (0.15, bar), (0.7, front), (0.55, normalized(crunch)),
            (0.22, normalized(slide)), (0.2, normalized(trickle)))
    place(x, normalized(metal(n - samples(160), 171.0, IRON[:5], 200.0, rng, bend=1.03, glide_ms=5.0)), 160.0, 0.35)
    return densify(hp(lp(x, 12000.0), 28.0), 3.0)


BRAWL_TOSS_FLIGHT_MS = 220.0


def brawl_toss_whoosh():
    """The barbell's flight, to play on the toss's fling frame (GreysonFinalBrawl._fling): 0.22 s in the air
    (cut_at - toss_at - TOSS_FLING - TOSS_LANDS), turning once, so each end of it chops the air twice across a
    heavy, rising rush; it hands over to brawl_toss as that lands."""
    rng = random.Random(3389)
    n = samples(BRAWL_TOSS_FLIGHT_MS + 80.0)
    air = swish(n, rng, [(0, 300.0), (BRAWL_TOSS_FLIGHT_MS, 950.0), (n * 1000.0 / SR, 900.0)], 1.2)
    chop = [0.55 + 0.45 * math.cos(2.0 * math.pi * 9.0 * i / SR) for i in range(n)]
    weight = apply(tone(n, contour(n, [(0, 95.0), (BRAWL_TOSS_FLIGHT_MS, 125.0)])),
                   shape(n, [(0, 0.0), (40, 1.0), (BRAWL_TOSS_FLIGHT_MS, 0.6), (n * 1000.0 / SR, 0.0)]))
    x = mix((1.0, apply(normalized(air), chop)), (0.3, weight))
    return apply(x, shape(n, [(0, 0.0), (35, 0.7), (BRAWL_TOSS_FLIGHT_MS - 20.0, 1.0), (n * 1000.0 / SR, 0.0)]))


# ------------------------------------------------------------------------------------------------- the hurl

# GreysonTakeover's hurl beats: the grab, the heave, Computah's flight off the screen.
HURL_GRAB_MS = 250.0
HURL_HEAVE_MS = 200.0
HURL_FLIGHT_MS = 550.0
# The hurled body turns a quarter every 0.08 s (GreysonArtLayout.HURL_TUMBLE), so a broad side comes round
# twice a turn: 6.25 times a second.
HURL_TUMBLE_HZ = 2.0 / (4 * 0.08)


def hurl_grab():
    """His effort as he hoists the armless robot, in the voice his dialogue blips use (~205 Hz, the same presence
    bump and grit): a pressed "hnnn" climbing through the 0.25 s grab, bursting into a "HAH!" on the 0.20 s heave.
    Made to play at pitch 1.0 (the stand-in's HURL_GRUNT_PITCH of 0.9 was for the flex)."""
    rng = random.Random(3390)
    n = samples(HURL_GRAB_MS + HURL_HEAVE_MS + 70.0)

    hn_n = samples(HURL_GRAB_MS)
    strain = glottal(hn_n, [(0, 178), (HURL_GRAB_MS, 198)], rng, 0.04, 0.35, 0.9)
    hn = tract(strain, [(0, NN), (HURL_GRAB_MS, NN)])
    hn = apply(saturate(normalized(hn), 2.0), shape(hn_n, [(0, 0.0), (40, 0.4), (200, 0.75), (HURL_GRAB_MS, 0.6)]))

    hah_ms = HURL_HEAVE_MS + 70.0
    hah_n = samples(hah_ms)
    heave = glottal(hah_n, [(0, 212), (30, 228), (hah_ms, 186)], rng, 0.03, 0.25, 0.8)
    hah = tract(heave, [(0, EH), (40, AH), (hah_ms, AH)])
    hah = mix((1.0, normalized(hah)), (0.3, normalized(bandpass(heave, 2600.0, 2.2))),
              (0.3, normalized(breath(heave, rng))))
    hah = apply(saturate(normalized(hah), 2.4), shape(hah_n, [(0, 0.0), (12, 1.0), (150, 0.8), (hah_ms, 0.0)]))
    h = apply(bandpass(noise(samples(30), rng), 1800.0, 1.0), shape(samples(30), [(0, 0.0), (3, 1.0), (30, 0.0)]))

    x = [0.0] * n
    place(x, hn, 0.0, 0.55)
    place(x, normalized(h), HURL_GRAB_MS - 10.0, 0.3)
    place(x, hah, HURL_GRAB_MS - 5.0, 1.0)
    return hp(lp(x, 7000.0), 70.0)


def hurl_whoosh():
    """Computah's body thrown: a heavy rush of air rising as he leaves the hand, fluttering each time his broad
    side comes round in the tumble, the weight of him low under it and his loose bits rattling, then duller and
    quieter as he goes off the screen at 0.55 s, where the crash takes over."""
    rng = random.Random(3391)
    end = HURL_FLIGHT_MS + 70.0
    n = samples(end)
    air = swish(n, rng, [(0, 260.0), (180, 820.0), (HURL_FLIGHT_MS, 420.0), (end, 380.0)], 1.1)
    tumble = [0.45 + 0.55 * (0.5 + 0.5 * math.cos(2.0 * math.pi * HURL_TUMBLE_HZ * i / SR)) for i in range(n)]
    mass = apply(tone(n, contour(n, [(0, 75.0), (180, 105.0), (HURL_FLIGHT_MS, 80.0)])),
                 shape(n, [(0, 0.0), (60, 1.0), (300, 0.5), (HURL_FLIGHT_MS, 0.0)]))
    bits = rattle(n, rng, [(0, 25.0), (HURL_FLIGHT_MS, 10.0)], 1500.0, 4200.0, 5.0)
    x = mix((1.0, apply(normalized(air), tumble)), (0.35, mass), (0.06, normalized(bits)))
    # Going away: the top closing down over the second half of the flight.
    cut = contour(n, [(0, 7000.0), (250, 7000.0), (HURL_FLIGHT_MS, 1800.0), (end, 1500.0)])
    y1 = y2 = 0.0
    away = []
    for s, fc in zip(x, cut):
        a = 1.0 - math.exp(-2.0 * math.pi * fc / SR)
        y1 += a * (s - y1)
        y2 += a * (y1 - y2)
        away.append(y2)
    return apply(away, shape(n, [(0, 0.0), (50, 0.8), (200, 1.0), (420, 0.65), (HURL_FLIGHT_MS, 0.35), (end, 0.0)]))


def room(x, wet, feedback=0.74, damp_hz=2400.0):
    """A small diffuse arena reverb (four damped parallel combs into two allpasses), mixed in at `wet`: distance
    without the flam that a few discrete echoes give. Keeps the input's length."""
    n = len(x)
    a = 1.0 - math.exp(-2.0 * math.pi * damp_hz / SR)
    tail = [0.0] * n
    for ms in (29.7, 37.1, 41.1, 43.7):
        d = samples(ms)
        buf = [0.0] * n
        low = 0.0
        for i in range(n):
            back = buf[i - d] if i >= d else 0.0
            low += a * (back - low)
            buf[i] = x[i] + feedback * low
            tail[i] += 0.25 * back
    for ms, g in ((5.0, 0.7), (1.7, 0.7)):
        d = samples(ms)
        out = [0.0] * n
        for i in range(n):
            back = out[i - d] if i >= d else 0.0
            fwd = tail[i - d] if i >= d else 0.0
            out[i] = -g * tail[i] + fwd + g * back
        tail = out
    return [(1.0 - wet) * s + wet * t for s, t in zip(x, tail)]


# A hollow robot chassis: modes closer together and boomier than a solid plate's.
HOLLOW = [(1.00, 1.00, 1.00), (1.38, 0.85, 0.80), (1.93, 0.70, 0.65), (2.61, 0.50, 0.50), (3.40, 0.35, 0.38),
          (4.37, 0.22, 0.28)]


def hurl_crash():
    """Computah landing beyond the ropes, out of sight: his hollow chassis clanging into the floor with a boom
    inside it, the metal crunching as it dents, a deep thud, a short skid, a panel and bolts rattling loose. All
    of it heard from past the ropes: the top dulled and the arena's reverb well up against the hit. No crowd: the
    cheer is its own sound."""
    rng = random.Random(3392)
    n = samples(1500)
    chassis = normalized(metal(n, 132.0, HOLLOW, 620.0, rng, bend=1.06, glide_ms=10.0, twins=3, twin_cents=12.0))
    cavity = normalized(resonator(apply(noise(n, rng), decay(n, 40.0, 0.5)), 95.0, 6.0))
    thud = normalized(thump(n, [(0, 100.0), (30, 58.0), (380, 52.0)], 380.0, 0.6, harmonics=((1, 1.0), (2, 0.4))))

    crunch_n = samples(110)
    impulses = [0.0] * crunch_n
    i = 0
    while i < crunch_n:
        impulses[i] = rng.uniform(-1.0, 1.0)
        i += max(1, int(SR / rng.uniform(250.0, 700.0)))
    crunch = mix((1.0, resonator(impulses, 700.0, 4.0)), (0.8, resonator(impulses, 1400.0, 5.0)),
                 (0.5, resonator(impulses, 2600.0, 6.0)))
    crunch = apply(normalized(crunch), shape(crunch_n, [(0, 1.0), (110, 0.0)]))

    skid_n = samples(320)
    skid = apply(bandpass(noise(skid_n, rng), 1200.0, 1.2),
                 [e * (0.6 + 0.4 * w) for e, w in zip(shape(skid_n, [(0, 0.0), (40, 1.0), (320, 0.0)]),
                                                      wander(skid_n, 30.0, rng))])
    loose = [0.0] * n
    for at, hz, level in ((190.0, 410.0, 0.6), (430.0, 455.0, 0.35)):
        place(loose, normalized(metal(n - samples(at), hz, IRON[:5], 180.0, rng, bend=1.03, glide_ms=4.0)), at, level)
    t = 120.0
    while t < 1000.0:
        place(loose, ping(60.0, rng.uniform(1400.0, 3800.0), rng, rng.uniform(30.0, 60.0)), t,
              rng.uniform(0.2, 0.6) * math.exp(-(t - 120.0) / 450.0))
        t += rng.expovariate(1.0 / (35.0 + 0.12 * t))

    x = mix((1.0, chassis), (0.55, cavity), (1.0, thud))
    place(x, crunch, 0.0, 0.6)
    place(x, normalized(skid), 60.0, 0.22)
    x = mix((1.0, x), (0.45, loose))
    # Out of sight past the ropes: dulled, and set back in the room.
    x = lp(lp(x, 3200.0), 3200.0)
    x = room(x, 0.4)
    return densify(hp(x, 30.0), 2.5)


# ------------------------------------------------------------------------------------------------- the list

# name: (builder, loops, loudness it should play at against hit_impact, where it plays)
SOUNDS = {
    "greyson_shout": (shout, False, 1.0, "cutscene: the \"COMPUTAH NOOO!\" that opens it"),
    "greyson_cannon_rip": (cannon_rip, False, 2.0, "cutscene: tearing the cannon arm off Computah"),
    "greyson_cannon_clamp": (cannon_clamp, False, 0.0, "cutscene: the cannon locking onto his arm"),
    "greyson_roar": (roar, False, 5.0, "cutscene: the roar that shakes the arena (with the screen shake)"),
    "greyson_plate_throw": (plate_throw, False, -2.0, "attack 1: each plate thrown"),
    "greyson_plate_spin": (plate_spin, True, -9.0, "attack 1: loop under each plate in flight"),
    "greyson_plate_bounce_1": (plate_bounce_1, False, -1.0, "attack 1: a plate bouncing off the edge (3 variants)"),
    "greyson_plate_bounce_2": (plate_bounce_2, False, -1.0, "attack 1: bounce variant 2"),
    "greyson_plate_bounce_3": (plate_bounce_3, False, -1.0, "attack 1: bounce variant 3"),
    "greyson_plate_parry": (plate_parry, False, 0.5, "attack 1: a plate parried, over the shared parry sound"),
    "greyson_barbell_slam": (barbell_slam, False, 2.0, "attack 1: each ground slam (and the brawl's debris slams)"),
    "greyson_teleport_out": (teleport_out, False, -1.0, "attack 1: blinking out"),
    "greyson_teleport_in": (teleport_in, False, -0.5, "attack 1: blinking in and landing"),
    "greyson_eruption_rumble": (eruption_rumble, True, -6.0, "attack 1: loop under a pending eruption, ramped up"),
    "greyson_eruption_blast": (eruption_blast, False, 3.0, "attack 1: an eruption going off"),
    "greyson_flex": (flex, False, -1.0, "poses: each pose struck (pitch it up as the hype climbs)"),
    "crowd_cheer": (crowd_cheer, False, 1.0, "poses: the crowd as the hype rises"),
    "crowd_boo": (crowd_boo, False, 0.0, "poses: the crowd as the hype drains"),
    "greyson_spirit_charge": (spirit_charge, False, 1.0, "spirit bomb: the bomb gathering over the cannon"),
    "greyson_spirit_launch": (spirit_launch, False, 3.0, "spirit bomb: the launch"),
    "greyson_spirit_explosion": (spirit_explosion, False, 6.0, "spirit bomb: the explosion, the loudest sound"),
    "greyson_disintegrate": (disintegrate, False, -1.0, "spirit bomb: the player disintegrating"),
    "greyson_brawl_debris": (brawl_debris, False, 1.0, "brawl cutscene: roof debris coming down"),
    "greyson_brawl_hook": (brawl_hook, False, -4.0, "brawl: his hook (left or right)"),
    "greyson_brawl_straight": (brawl_straight, False, -4.0, "brawl: his straight"),
    "greyson_brawl_hit": (brawl_punch_hit, False, -1.0, "brawl: his punch landing (player_hurt plays too)"),
    "greyson_brawl_dodge": (brawl_dodge, False, -6.0, "brawl: the player slipping a hook"),
    "greyson_brawl_tell": (brawl_tell, False, -2.0, "brawl: the arrow over his head"),
    "greyson_brawl_tell_parry": (brawl_tell_parry, False, -1.5, "brawl: the red parry indicator"),
    # The plan's extra keys, which had stand-ins only. stomp plays its two files in turn; brawl_toss_whoosh is a
    # new key for the fling frame, so brawl_toss can stay on the landing.
    "greyson_stomp_1": (stomp_1, False, -4.0, "takeover walk-in: a step (key stomp, with _2 in turn)"),
    "greyson_stomp_2": (stomp_2, False, -4.0, "takeover walk-in: the other foot"),
    "greyson_spark": (spark, False, -8.0, "takeover: the torn wires on Computah's socket (key spark)"),
    "greyson_slam_windup": (slam_windup, False, -3.0, "the barbell hauled overhead before a slam (key slam_windup)"),
    "greyson_plate_drop": (plate_drop, False, -3.0, "a plate that hit, clanging on the mat 0.30 s on (key plate_drop)"),
    "greyson_pose_bank": (pose_bank, False, -2.0, "a pose banked, the battery gaining a cell (key pose_bank)"),
    "greyson_pose_spoiled": (pose_spoiled, False, -2.0, "a pose spoiled, half a cell lost (key pose_spoiled)"),
    "greyson_cannon_hum": (cannon_hum, True, -12.0, "loop: the cannon's hum, at full hype (key cannon_hum)"),
    "greyson_brawl_toss": (brawl_toss, False, 1.0, "the barbell landing in the rubble (key brawl_toss)"),
    "greyson_brawl_toss_whoosh": (brawl_toss_whoosh, False, -4.0, "the barbell's flight, on the fling frame"),
    # The takeover's hurl (GreysonTakeover._hurl): the grab and heave, the flight, the crash out of sight.
    "greyson_hurl_grab": (hurl_grab, False, -2.0, "takeover hurl: his grunt grabbing and heaving Computah (key hurl_grab)"),
    "greyson_hurl_whoosh": (hurl_whoosh, False, -4.0, "takeover hurl: Computah's 0.55 s flight (key hurl_whoosh)"),
    "greyson_hurl_crash": (hurl_crash, False, -1.0, "takeover hurl: the crash beyond the ropes (key hurl_crash)"),
}
VOICE_NAMES = ["voice_greyson_1", "voice_greyson_2", "voice_greyson_3"]


def build(name):
    builder, loops, _, _ = SOUNDS[name]
    return finish_loop(builder()) if loops else finish(builder())


def file_bytes(name, x):
    """A loop gets one guard frame and its smpl loop over everything before it (dsp.godot_native)."""
    if SOUNDS[name][1]:
        return wav_bytes(x + x[:1], loop=(0, len(x)))
    return wav_bytes(x)


def level_of(name, x):
    return loudness_db(x + x) if SOUNDS[name][1] else loudness_db(x)


def proposed_db(name, x):
    """The volume_db that puts the sound at its target loudness, to the nearest half dB."""
    return round(2.0 * (HIT_REF_DB + SOUNDS[name][2] - level_of(name, x))) / 2.0


# ------------------------------------------------------------------------------------------------- scene previews

def play(x, pitch=1.0, db=0.0):
    """A one-shot through Godot's playback at a pitch, at a volume."""
    y = x if pitch == 1.0 else godot_resample(x, pitch, int(len(x) / pitch))
    g = 10.0 ** (db / 20.0)
    return [s * g for s in y]


def play_loop(x, ms, pitch_points=((0.0, 1.0),), db_points=((0.0, 0.0),), start=0.0):
    """A loop through Godot's playback for `ms`, its pitch and volume following (ms, value) points a frame at a
    time, then Godot's stop fade."""
    n = len(x)
    one = 1 << 16
    count = samples(ms)
    pitches = contour(count, list(pitch_points) + [(ms, pitch_points[-1][1])])
    gains = contour(count, list(db_points) + [(ms, db_points[-1][1])])
    q = [max(-32768, min(32767, int(round(s * 32767.0)))) / 32767.0 for s in x]
    offset = int(start * n) % n
    native = godot_native(q[offset:] + q[:offset] + q[offset:offset + 1], int(sum(pitches)) + 16, (0, n))
    buf = [0.0] * 4 + native
    out = []
    pos = 0
    step = int(pitches[0] * one)
    for i in range(count):
        if i % 735 == 0:
            step = int(pitches[i] * one)
        idx = 4 + (pos >> 16)
        mu = (pos & (one - 1)) / one
        y0, y1, y2, y3 = buf[idx - 3], buf[idx - 2], buf[idx - 1], buf[idx]
        mu2 = mu * mu
        h11 = mu2 * (mu - 1.0)
        z = mu2 - h11
        out.append((y1 + (y2 - y1) * (z - h11) + ((y2 - y0) * (mu - z) + (y3 - y1) * h11) * 0.5)
                   * 10.0 ** (gains[i] / 20.0))
        pos += step
    fade = min(512, len(out))
    for k in range(fade):
        out[-fade + k] *= 1.0 - k / fade
    return out


def shared(name):
    """A shared, public sound the fight already plays (never anything in SFX/local)."""
    return dsp.read_wav_file(os.path.join(SFX_DIR, name))[0]


def scene(events, ms):
    out = [0.0] * samples(ms)
    for at, x in events:
        place(out, x, at)
    peak = max(abs(s) for s in out)
    if peak > 10.0 ** (-1.0 / 20.0):
        out = [s * 10.0 ** (-1.0 / 20.0) / peak for s in out]
    return out, 20.0 * math.log10(peak)


def scenes(files, db):
    """Four listen-throughs at the proposed levels, with the waits cut short."""
    def s(name, pitch=1.0, extra=0.0):
        return play(files[name], pitch, db[name] + extra)

    def loop(name, ms, **kw):
        return play_loop(files[name], ms, db_points=kw.pop("db_points", ((0.0, db[name]),)), **kw)

    cut = [(300.0, s("greyson_shout")), (3300.0, s("greyson_cannon_rip")), (5300.0, s("greyson_cannon_clamp")),
           (7300.0, s("greyson_roar"))]

    rumble_db = db["greyson_eruption_rumble"]
    ramp = dict(pitch_points=((0.0, 0.9), (2400.0, 1.15)), db_points=((0.0, rumble_db - 12.0), (2400.0, rumble_db)))
    attack = [(200.0, s("greyson_plate_throw")), (350.0, loop("greyson_plate_spin", 3250.0)),
              (900.0, s("greyson_plate_throw")), (1050.0, loop("greyson_plate_spin", 950.0, start=0.37)),
              (1200.0, s("greyson_plate_bounce_1")), (2000.0, s("greyson_plate_parry")),
              (2000.0, play(shared("parry_hit_1.wav"))), (2200.0, s("greyson_plate_bounce_2")),
              (3300.0, s("greyson_plate_bounce_3"))]
    for k, at in enumerate((2600.0, 3900.0, 5200.0)):
        attack += [(at, s("greyson_teleport_out")), (at + 300.0, s("greyson_teleport_in")),
                   (at + 450.0, s("greyson_barbell_slam", (1.0, 0.97, 1.03)[k]))]
    blasts = (5500.0, 7000.0, 7800.0)
    for k, at in enumerate((3100.0, 4400.0, 5700.0)):
        attack.append((at, loop("greyson_eruption_rumble", blasts[k] - at, **ramp)))
        attack.append((blasts[k], s("greyson_eruption_blast", (1.0, 0.96, 1.04)[k])))
    attack += [(6400.0, s("greyson_teleport_out")), (6700.0, s("greyson_teleport_in")),
               (8600.0, s("greyson_flex")), (8800.0, s("crowd_cheer")),
               (10100.0, s("greyson_flex", 1.06)), (10300.0, s("crowd_cheer")),
               (11600.0, s("crowd_boo"))]

    bomb = [(300.0, s("greyson_spirit_charge")), (3900.0, s("greyson_spirit_launch")),
            (4900.0, s("greyson_spirit_explosion")), (5500.0, s("greyson_disintegrate"))]

    brawl = [(200.0 + 700.0 * k, s("greyson_barbell_slam", p)) for k, p in enumerate((1.0, 0.97, 1.03, 0.95))]
    brawl.append((500.0, s("greyson_brawl_debris")))
    t = 4400.0
    for kind in ("hook", "hook", "straight", "hit", "hook", "straight"):
        if kind == "straight":
            brawl += [(t, s("greyson_brawl_tell_parry")), (t + 300.0, s("greyson_brawl_straight")),
                      (t + 330.0, play(shared("parry_hit_1.wav")))]
        else:
            brawl += [(t, s("greyson_brawl_tell")), (t + 300.0, s("greyson_brawl_hook"))]
            brawl.append((t + 340.0, s("greyson_brawl_hit") if kind == "hit" else s("greyson_brawl_dodge")))
        t += 750.0
    brawl.append((t + 200.0, play(shared("break_sting.wav"))))

    new = [(200.0 + 300.0 * k, s("greyson_stomp_%d" % (k % 2 + 1))) for k in range(5)]
    new += [(2000.0, s("greyson_spark")),
            (3200.0, s("greyson_slam_windup")), (3200.0 + SLAM_WINDUP_MS, s("greyson_barbell_slam")),
            (5000.0, s("greyson_plate_drop")),
            (6200.0, s("greyson_pose_bank")), (6200.0, s("crowd_cheer")),
            (9000.0, s("greyson_pose_spoiled")), (9000.0, s("crowd_boo")),
            (11800.0, loop("greyson_cannon_hum", 4200.0, pitch_points=((0.0, 0.85), (4000.0, 1.3)),
                           db_points=((0.0, db["greyson_cannon_hum"] - 14.0), (4000.0, db["greyson_cannon_hum"])))),
            (16400.0, s("greyson_brawl_toss_whoosh")),
            (16400.0 + BRAWL_TOSS_FLIGHT_MS, s("greyson_brawl_toss"))]

    # The hurl at the takeover's timing, bare and then with the cheer the fight plays on the crash.
    hurl = []
    for at, cheer in ((200.0, False), (2900.0, True)):
        hurl += [(at, s("greyson_hurl_grab")), (at + HURL_GRAB_MS + HURL_HEAVE_MS, s("greyson_hurl_whoosh")),
                 (at + HURL_GRAB_MS + HURL_HEAVE_MS + HURL_FLIGHT_MS, s("greyson_hurl_crash"))]
        if cheer:
            hurl.append((at + HURL_GRAB_MS + HURL_HEAVE_MS + HURL_FLIGHT_MS, s("crowd_cheer")))

    return {"scene_1_cutscene": scene(cut, 11000.0), "scene_2_attack_and_poses": scene(attack, 14800.0),
            "scene_3_spirit_bomb": scene(bomb, 8600.0), "scene_4_brawl": scene(brawl, t + 1900.0),
            "scene_5_new_keys": scene(new, 18400.0), "scene_6_hurl": scene(hurl, 7300.0)}


# ------------------------------------------------------------------------------------------------- output

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    ship = sys.argv[1] == "--ship"
    folder = SFX_DIR if ship else sys.argv[1]
    names = list(SOUNDS) + VOICE_NAMES
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        unknown = [name for name in only if name not in names]
        if unknown:
            print("no such sound: %s" % ", ".join(unknown))
            return
    os.makedirs(folder, exist_ok=True)

    files, db = {}, {}
    print("%-26s %6s %8s %8s %9s %9s  %s" % ("sound", "ms", "file dB", "target", "volume_db", "peak dBFS", "plays"))
    for name in SOUNDS:
        if only is not None and name not in only and ship:
            continue
        x = build(name)
        files[name], db[name] = x, proposed_db(name, x)
        if only is None or name in only:
            path = os.path.join(folder, ("%s.wav" if ship else "preview_%s.wav") % name)
            with open(path, "wb") as f:
                f.write(file_bytes(name, x))
        print("%-26s %6.0f %8.1f %+8.1f %+9.1f %9.1f  %s%s" % (
            name, len(x) * 1000.0 / SR, level_of(name, x), SOUNDS[name][2], db[name], PEAK_DBFS + db[name],
            SOUNDS[name][3], "  (loop)" if SOUNDS[name][1] else ""))

    blips = gym_bro_blips()
    for name, x in zip(VOICE_NAMES, blips):
        if only is None or name in only:
            path = os.path.join(VOICE_DIR if ship else folder, ("%s.wav" if ship else "preview_%s.wav") % name)
            make_voices.write_wav(path, x)
    print("voice_greyson_1..3          %s ms, loudness %s (every voice sits at %.1f)" % (
        "/".join("%.0f" % (len(x) * 1000.0 / SR) for x in blips), "/".join("%.1f" % loudness_db(x) for x in blips),
        make_voices.TARGET_DB))
    if ship or only is not None:
        return

    make_voices.write_wav(os.path.join(folder, "preview_voice_greyson_lines.wav"), voice_lines(blips))
    for name, (x, peak) in scenes(files, db).items():
        with open(os.path.join(folder, "%s.wav" % name), "wb") as f:
            f.write(wav_bytes(x))
        print("%-26s %6.1f s  summed peak %+.1f dBFS%s" % (name, len(x) / SR, peak,
                                                            ", turned down to -1.0" if peak > -1.0 else ""))


if __name__ == "__main__":
    main()
