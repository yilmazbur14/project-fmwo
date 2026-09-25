"""Synthesizes Danny's sound effects, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, built from make_voices.py's blocks and make_bixby_roar.py's voice source (pulse_train),
so every run writes identical files. Nothing is sampled or downloaded.

    python make_danny_sfx.py PREVIEW_DIR   writes preview_danny_<name>.wav for every sound into PREVIEW_DIR
    python make_danny_sfx.py --ship        writes danny_<name>.wav into Assets/Audio/SFX
    ... --only gulp,spit                   either of those, for only the sounds named

Run with no argument, it only says how to use it: it never writes into the shipped folder unless asked to.
Ship a new sound with --only, so the approved ones are never rewritten.

Every sound is normalized to a -3 dBFS peak; DannyBossArtLayout.SFX sets how loud each one plays. The snore and the
push's strain loop, so their ends are cross-faded into their starts and their edges are left open. His voice here
is the evolved sumo's, a big low one: the training room's little Danny talks in make_voices.py's triangle bop.
The gate's clang, the record scratch, the sumo's stomp and clash and the Break's sting stay on the shared set.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_voices"))

from make_voices import (SR, PROJECT, samples, contour, oscillator, envelope, noise, lowpass, highpass, bandpass, mul,
                         mix, normalized, saturate, write_wav)
from make_bixby_roar import pulse_train

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")
PEAK_DBFS = -3.0
# Sounds that loop end to start: no fade at their edges.
LOOPED = ("snore", "push_strain")


# ------------------------------------------------------------------------------------------------- building blocks

def finish(x, edge_ms=3.0):
    """Blocks DC, silences both ends (unless edge_ms is 0) and normalizes to PEAK_DBFS."""
    x = highpass(x, 25.0)
    edge = samples(edge_ms)
    for i in range(min(edge, len(x) // 2)):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x) or 1.0
    return [s * 10.0 ** (PEAK_DBFS / 20.0) / peak for s in x]


def ms_of(n):
    return n * 1000.0 / SR


def sweep(n, points):
    """A sine following (ms, Hz) points."""
    return oscillator(contour(n, points), [(1, 1.0)])


def formants(x, resonances):
    """A vocal tract: a band-pass per formant, mixed by weight. resonances: (Hz, Q, gain)."""
    return mix(*[(gain, bandpass(x, hz, q)) for hz, q, gain in resonances])


def sliding_bandpass(x, from_hz, to_hz, q, chunk_ms=15.0):
    """A band-pass whose centre walks from from_hz to to_hz, a chunk at a time and cross-faded."""
    n = len(x)
    size = samples(chunk_ms)
    pieces = max(1, n // size)
    out = [0.0] * n
    for p in range(pieces + 1):
        u = min(1.0, p / max(1, pieces))
        hz = from_hz * (to_hz / from_hz) ** u
        lo = max(0, (p - 1) * size)
        hi = min(n, (p + 1) * size)
        if lo >= hi:
            continue
        piece = bandpass(x[lo:hi], hz, q)
        for i, s in enumerate(piece):
            t = lo + i
            w = 1.0 - abs(t - p * size) / size
            if w > 0.0:
                out[t] += w * s
    return out


def voice(n, pitch_points, jitter, sub, rng, pulse_ms=1.0):
    """His voice's source: glottal pulses along (ms, Hz) points, rough by `jitter`, with every other pulse quietened
    by `sub` for a growl an octave down."""
    return pulse_train(contour(n, pitch_points), pulse_ms, [jitter] * n, [sub] * n, rng)


def syllable(ms, pitch_points, shape, rng, jitter=0.03, sub=0.35, drive=1.8, attack_ms=4.0, release_ms=40.0):
    """One voiced syllable of his: pulses through a vowel's formants, saturated, in an envelope."""
    n = samples(ms)
    sound = formants(voice(n, pitch_points, jitter, sub, rng), shape)
    return mul(saturate(normalized(sound), drive), envelope(n, attack_ms, release_ms))


def place(out, sound, at, gain=1.0):
    """Mixes `sound` into `out` from sample `at`, cut off at the end of `out`."""
    for i, s in enumerate(sound):
        if at + i >= len(out):
            break
        out[at + i] += gain * s


def loop_seam(x, fade):
    """The last `fade` samples cross-faded into the first and dropped, so the sound loops end to start with no seam."""
    out = x[:len(x) - fade]
    for i in range(fade):
        w = i / fade
        out[i] = out[i] * w + x[len(x) - fade + i] * (1.0 - w)
    return out


def droplets(n, count, rng, lo_hz=1500.0, hi_hz=4000.0, spread_ms=250.0):
    """Little wet ticks scattered over the first spread_ms: each a quick falling blip."""
    out = [0.0] * n
    for _ in range(count):
        m = samples(rng.uniform(12.0, 28.0))
        f0 = rng.uniform(lo_hz, hi_hz)
        blip = mul(sweep(m, [(0, f0), (ms_of(m), f0 * 0.6)]), envelope(m, 0.5, 8, decay_ms=8))
        place(out, blip, samples(rng.uniform(0.0, spread_ms)), rng.uniform(0.3, 0.8))
    return out


UH = [(640, 3.0, 1.0), (1190, 4.0, 0.6), (2390, 5.0, 0.3)]
AH = [(820, 3.0, 1.0), (1250, 4.0, 0.7), (2600, 5.0, 0.35)]
OO = [(300, 3.0, 1.0), (870, 4.0, 0.45), (2240, 5.0, 0.2)]
OH = [(500, 3.0, 1.0), (880, 4.0, 0.6), (2400, 5.0, 0.25)]
OI = [(420, 3.0, 1.0), (1600, 4.0, 0.55), (2500, 5.0, 0.3)]
# A nose full of snore.
NASAL = [(250, 3.0, 1.0), (1000, 4.0, 0.3), (2100, 5.0, 0.12)]


# ------------------------------------------------------------------------------------------------- the worm spit

def gulp():
    """A wet belly gurgle: a throat "glk" on 120 Hz pulses, then bubbles rising through a low stomach rumble, 0.45 s."""
    rng = random.Random(901)
    n = samples(450)
    rumble = mul(lowpass(noise(n, rng), 180.0), envelope(n, 30, 150, decay_ms=300))
    glk = syllable(90, [(0, 125), (90, 104)], UH, rng, jitter=0.05, sub=0.4, drive=1.5, attack_ms=2, release_ms=40)
    out = [0.0] * n
    place(out, glk, 0, 0.8)
    for i in range(7):
        m = samples(rng.uniform(30.0, 55.0))
        f0 = rng.uniform(140.0, 220.0)
        blip = mul(sweep(m, [(0, f0), (ms_of(m), f0 * 2.1)]), envelope(m, 2, 15, decay_ms=20))
        place(out, blip, samples(90 + i * 45 + rng.uniform(-10.0, 10.0)), rng.uniform(0.35, 0.7))
    return mix((1.0, out), (0.9, rumble))


def spit():
    """A wet "PTOO": a lip pop, a tongue tick, a voiced "oo" falling from 150 Hz, and a spray of wet ticks off the
    front of it, 0.4 s."""
    rng = random.Random(902)
    n = samples(400)
    pop_n = samples(30)
    pop = mul(lowpass(noise(pop_n, rng), 900.0), envelope(pop_n, 0.5, 20, decay_ms=10))
    tick_n = samples(20)
    tick = mul(highpass(noise(tick_n, rng), 3000.0), envelope(tick_n, 0.5, 12, decay_ms=6))
    oo = syllable(240, [(0, 150), (240, 118)], OO, rng, jitter=0.03, sub=0.25, drive=1.6, attack_ms=6, release_ms=120)
    spray = mul(bandpass(noise(n, rng), 3200, 1.1), envelope(n, 5, 200, decay_ms=110))
    out = [0.0] * n
    place(out, pop, 0, 0.9)
    place(out, tick, samples(45), 0.7)
    place(out, oo, samples(60), 0.9)
    return mix((1.0, out), (0.35, spray), (0.6, droplets(n, 6, rng, spread_ms=220.0)))


def glob_splat():
    """A glob of worms landing: a wet slap, a soft thud falling 180 to 70 Hz, a squelch sliding down through the mat
    and a few drops, 0.42 s."""
    rng = random.Random(903)
    n = samples(420)
    slap = mul(bandpass(noise(n, rng), 1200, 1.4), envelope(n, 0.5, 60, decay_ms=35))
    thud = mul(sweep(n, [(0, 180), (420, 70)]), envelope(n, 2, 120, decay_ms=90))
    squelch_n = samples(300)
    wobble = [0.6 + 0.4 * math.sin(2.0 * math.pi * 22.0 * i / SR) for i in range(squelch_n)]
    squelch = mul(mul(sliding_bandpass(noise(squelch_n, rng), 800.0, 280.0, 3.0), wobble), envelope(squelch_n, 15, 150))
    out = [0.0] * n
    place(out, squelch, samples(40), 1.0)
    return mix((1.0, slap), (0.7, thud), (0.9, out), (0.5, droplets(n, 4, rng, 1200.0, 3000.0, 200.0)))


def puddle_dry():
    """A puddle drying up as the next spit comes: a 0.4 s fizzle, a hiss sliding down from 4 kHz with sparse crackle,
    thinning to nothing."""
    rng = random.Random(904)
    n = samples(400)
    hiss = mul(sliding_bandpass(highpass(noise(n, rng), 1500.0), 4000.0, 1500.0, 1.5), envelope(n, 10, 250, decay_ms=220))
    crackle = bandpass([rng.uniform(-1.0, 1.0) if rng.random() < 0.01 else 0.0 for _ in range(n)], 2800, 1.2)
    return mix((1.0, hiss), (1.3, mul(crackle, envelope(n, 5, 200, decay_ms=200))))


def root_clamp():
    """The worms taking the player's feet: a squelch and a creak tightening like a rope, pulses rising 45 to 110 Hz
    through a woody band, 0.55 s."""
    rng = random.Random(905)
    n = samples(550)
    squelch = mul(sliding_bandpass(noise(n, rng), 450.0, 950.0, 3.0), envelope(n, 5, 180, decay_ms=160))
    creak_n = samples(420)
    creak = pulse_train(contour(creak_n, [(0, 45), (420, 110)]), 0.6, [0.18] * creak_n, [0.2] * creak_n, rng)
    creak = mul(bandpass(creak, 750, 2.5), envelope(creak_n, 20, 80))
    out = [0.0] * n
    place(out, creak, samples(90), 1.0)
    return mix((0.9, squelch), (1.0, out))


def root_burst():
    """The root bursting as the headbutt is parried: a wet pop falling 900 to 300 Hz and the worms scattering in
    ticks, 0.36 s."""
    rng = random.Random(906)
    n = samples(360)
    pop = mul(sweep(n, [(0, 900), (60, 300)]), envelope(n, 0.5, 60, decay_ms=40))
    burst = mul(bandpass(noise(n, rng), 1600, 1.0), envelope(n, 0.5, 40, decay_ms=25))
    return mix((1.0, pop), (0.6, burst), (0.8, droplets(n, 10, rng, 1500.0, 4200.0, 260.0)))


# ------------------------------------------------------------------------------------------------- the Sumo Smash

def jump():
    """The launch: a heavy "HUP!" on 130 Hz pulses and a whoosh climbing 200 Hz to 1.5 kHz as he leaves the mat,
    0.52 s."""
    rng = random.Random(907)
    n = samples(520)
    hup = syllable(170, [(0, 138), (170, 118)], UH, rng, jitter=0.04, sub=0.4, drive=2.2, attack_ms=3, release_ms=70)
    whoosh_n = samples(420)
    whoosh = mul(sliding_bandpass(noise(whoosh_n, rng), 200.0, 1500.0, 1.4), envelope(whoosh_n, 60, 220, decay_ms=260))
    out = [0.0] * n
    place(out, hup, 0, 0.9)
    place(out, whoosh, samples(70), 0.8)
    return out


def butt_slam():
    """His whole weight coming down: a 60 Hz thud and boom falling to 42 Hz, the mat's slap, a burst of air and a
    rumble rolling on, 1.1 s."""
    rng = random.Random(908)
    n = samples(1100)
    boom = mul(sweep(n, [(0, 72), (120, 60), (1100, 42)]), envelope(n, 2, 450, decay_ms=380))
    slap = mul(bandpass(noise(n, rng), 620, 1.2), envelope(n, 0.5, 60, decay_ms=40))
    burst = mul(lowpass(noise(n, rng), 1000.0), envelope(n, 1, 250, decay_ms=110))
    rumble = mul(lowpass(noise(n, rng), 160.0), envelope(n, 40, 600, decay_ms=520))
    return mix((1.0, boom), (0.7, slap), (0.5, burst), (1.3, rumble))


def slam_bonk():
    """A landing parried: a short thump bouncing off the guard, 160 falling to 90 Hz, and a springy "boing" at
    300 Hz wobbling as it fades, 0.42 s."""
    rng = random.Random(909)
    n = samples(420)
    thump = mul(sweep(n, [(0, 160), (120, 90)]), envelope(n, 1, 120, decay_ms=70))
    wobble = [300.0 * (1.0 + 0.06 * math.sin(2.0 * math.pi * 11.0 * i / SR)) for i in range(n)]
    boing = mul(oscillator(wobble, [(1, 1.0), (2, 0.3)]), envelope(n, 3, 200, decay_ms=150))
    knock = mul(bandpass(noise(n, rng), 1800, 2.0), envelope(n, 0.5, 20, decay_ms=10))
    return mix((1.0, thump), (0.55, boing), (0.5, knock))


# ------------------------------------------------------------------------------------------------- the nap

def snore():
    """His nap, 1.6 s round: a rattling in-breath on 58 Hz pulses through his nose, swelling and dying away, then a
    breathy "pwoo" out, looping without a seam."""
    rng = random.Random(910)
    fade = samples(160)
    n = samples(1600) + fade
    in_n = samples(820)
    rattle = pulse_train(contour(in_n, [(0, 54), (400, 60), (820, 56)]), 1.4, [0.22] * in_n, [0.35] * in_n, rng)
    rattle = mul(formants(rattle, NASAL), contour(in_n, [(0, 0.0), (420, 1.0), (820, 0.0)]))
    out_n = samples(760)
    breath = mul(sliding_bandpass(noise(out_n, rng), 1300.0, 700.0, 1.6), contour(out_n, [(0, 0.0), (160, 0.55), (760, 0.0)]))
    out = [0.0] * n
    place(out, rattle, 0, 1.0)
    place(out, breath, in_n, 1.0)
    place(out, rattle, samples(1600), 1.0)
    return loop_seam(out, fade)


def sleep_hit():
    """A punch waking him for a moment: a snort, rough pulses at 90 Hz through his nose with a puff of air, 0.3 s."""
    rng = random.Random(911)
    n = samples(300)
    snort = pulse_train(contour(n, [(0, 95), (300, 80)]), 1.0, [0.3] * n, [0.3] * n, rng)
    snort = mul(saturate(normalized(formants(snort, NASAL)), 2.0), envelope(n, 2, 120, decay_ms=90))
    puff = mul(bandpass(noise(n, rng), 1400, 1.0), envelope(n, 1, 80, decay_ms=50))
    return mix((1.0, snort), (0.4, puff))


def regen_tick():
    """One HP back: a soft chime rising a fifth, 880 then 1320 Hz, each with a little bell shimmer, 0.36 s."""
    n = samples(360)
    low_n = samples(200)
    low = mul(oscillator([880.0] * low_n, [(1, 1.0), (2.76, 0.12), (5.4, 0.05)]), envelope(low_n, 6, 120, decay_ms=110))
    high_n = samples(260)
    high = mul(oscillator([1320.0] * high_n, [(1, 1.0), (2.76, 0.12), (5.4, 0.05)]), envelope(high_n, 6, 160, decay_ms=140))
    out = [0.0] * n
    place(out, low, 0, 0.8)
    place(out, high, samples(90), 0.9)
    return out


def wake():
    """His nap cut short: a snort, then a startled "huh?!" rising 120 to 230 Hz after a breathy "h", 0.62 s."""
    rng = random.Random(912)
    n = samples(620)
    snort_n = samples(180)
    snort = pulse_train(contour(snort_n, [(0, 90), (180, 78)]), 1.0, [0.3] * snort_n, [0.3] * snort_n, rng)
    snort = mul(saturate(normalized(formants(snort, NASAL)), 2.0), envelope(snort_n, 2, 80, decay_ms=70))
    h_n = samples(50)
    h = mul(bandpass(noise(h_n, rng), 1600, 1.0), envelope(h_n, 3, 30))
    huh = syllable(300, [(0, 120), (300, 230)], UH, rng, jitter=0.03, sub=0.2, drive=1.7, attack_ms=10, release_ms=90)
    out = [0.0] * n
    place(out, snort, 0, 0.8)
    place(out, h, samples(250), 0.35)
    place(out, huh, samples(290), 1.0)
    return out


# ------------------------------------------------------------------------------------------------- the headbutt

def headbutt_charge():
    """Winding up the torpedo: a strained grunt through clenched teeth, rough pulses rising 108 to 172 Hz and
    swelling, 0.8 s."""
    rng = random.Random(913)
    n = samples(800)
    grunt = formants(voice(n, [(0, 108), (800, 172)], 0.09, 0.45, rng), UH)
    grunt = mul(saturate(normalized(grunt), 2.6), contour(n, [(0, 0.0), (120, 0.45), (760, 1.0), (800, 0.0)]))
    strain = mul(bandpass(noise(n, rng), 2400, 2.0), contour(n, [(0, 0.0), (600, 0.3), (800, 0.0)]))
    return mix((1.0, grunt), (0.3, strain))


def headbutt_launch():
    """The torpedo leaving: a "DOSUKOI!" yell, three syllables climbing 150, 165 then 200 Hz, and a whoosh under it,
    0.72 s."""
    rng = random.Random(914)
    n = samples(720)
    out = [0.0] * n
    d_n = samples(12)
    place(out, mul(lowpass(noise(d_n, rng), 1200.0), envelope(d_n, 0.5, 8)), 0, 0.6)
    place(out, syllable(150, [(0, 150), (150, 152)], OH, rng, drive=2.2, release_ms=30), samples(10))
    s_n = samples(45)
    place(out, mul(highpass(noise(s_n, rng), 3500.0), envelope(s_n, 5, 20)), samples(165), 0.35)
    place(out, syllable(110, [(0, 165), (110, 168)], OO, rng, drive=2.2, release_ms=30), samples(205))
    k_n = samples(15)
    place(out, mul(highpass(noise(k_n, rng), 2000.0), envelope(k_n, 0.5, 10)), samples(320), 0.45)
    place(out, syllable(330, [(0, 200), (180, 212), (330, 185)], OI, rng, drive=2.4, release_ms=140), samples(335))
    whoosh = mul(sliding_bandpass(noise(n, rng), 400.0, 2500.0, 1.3), envelope(n, 200, 220, decay_ms=330))
    return mix((1.0, out), (0.55, whoosh))


def headbutt_bonk():
    """The torpedo parried: a hollow head bonk, a wooden knock at 520 Hz with inharmonic partials ringing short,
    0.42 s."""
    rng = random.Random(915)
    n = samples(420)
    click_n = samples(10)
    click = mul(highpass(noise(click_n, rng), 2500.0), envelope(click_n, 0.3, 6))
    knock = mul(oscillator([520.0] * n, [(1, 1.0), (1.52, 0.5), (2.83, 0.28), (4.1, 0.12)]), envelope(n, 0.5, 200, decay_ms=110))
    body = mul(sweep(n, [(0, 190), (200, 140)]), envelope(n, 1, 150, decay_ms=70))
    out = [0.0] * n
    place(out, click, 0, 0.7)
    return mix((1.0, out), (1.0, knock), (0.45, body))


def headbutt_hit():
    """The torpedo landing on the player: a heavy thud falling 120 to 58 Hz, a burst of air and a crunch at 2 kHz,
    0.52 s."""
    rng = random.Random(916)
    n = samples(520)
    thud = mul(sweep(n, [(0, 120), (300, 58)]), envelope(n, 1, 250, decay_ms=150))
    burst = mul(lowpass(noise(n, rng), 1400.0), envelope(n, 0.5, 150, decay_ms=70))
    crunch = mul(bandpass(noise(n, rng), 2000, 1.6), envelope(n, 0.5, 60, decay_ms=30))
    return mix((1.0, thud), (0.6, burst), (0.5, crunch))


# ------------------------------------------------------------------------------------------------- the sumo

def push_strain():
    """The tug: his long strained grunt, rough 102 Hz pulses with a slow waver, 1.2 s round, looping without a seam."""
    rng = random.Random(917)
    fade = samples(200)
    n = samples(1200) + fade
    pitch = [102.0 * (1.0 + 0.035 * math.sin(2.0 * math.pi * 1.7 * i / SR)) for i in range(n)]
    grunt = formants(pulse_train(pitch, 1.1, [0.08] * n, [0.45] * n, rng), UH)
    swell = [0.8 + 0.2 * math.sin(2.0 * math.pi * (i / (n - fade))) for i in range(n)]
    grunt = mul(saturate(normalized(grunt), 2.2), swell)
    return loop_seam(grunt, fade)


def pushed_out():
    """Out of the ring: three tumbling thumps rolling away, then a crash, a boom and a burst of noise, 1.0 s."""
    rng = random.Random(918)
    n = samples(1000)
    out = [0.0] * n
    for k, (at, hz) in enumerate(((0, 140), (140, 125), (270, 110))):
        m = samples(160)
        thump = mul(sweep(m, [(0, hz), (160, hz * 0.6)]), envelope(m, 1, 80, decay_ms=50))
        place(out, thump, samples(at), 0.8 - 0.15 * k)
    crash_n = samples(600)
    boom = mul(sweep(crash_n, [(0, 90), (600, 45)]), envelope(crash_n, 2, 300, decay_ms=220))
    burst = mul(lowpass(noise(crash_n, rng), 2200.0), envelope(crash_n, 0.5, 200, decay_ms=90))
    place(out, mix((1.0, boom), (0.7, burst)), samples(400), 1.0)
    return out


SOUNDS = {
    "gulp": gulp,
    "spit": spit,
    "glob_splat": glob_splat,
    "puddle_dry": puddle_dry,
    "root_clamp": root_clamp,
    "root_burst": root_burst,
    "jump": jump,
    "butt_slam": butt_slam,
    "slam_bonk": slam_bonk,
    "snore": snore,
    "sleep_hit": sleep_hit,
    "regen_tick": regen_tick,
    "wake": wake,
    "headbutt_charge": headbutt_charge,
    "headbutt_launch": headbutt_launch,
    "headbutt_bonk": headbutt_bonk,
    "headbutt_hit": headbutt_hit,
    "push_strain": push_strain,
    "pushed_out": pushed_out,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    ship = sys.argv[1] == "--ship"
    folder = SFX_DIR if ship else sys.argv[1]
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
        unknown = [name for name in only if name not in SOUNDS]
        if unknown:
            print("no such sound: %s" % ", ".join(unknown))
            return
    os.makedirs(folder, exist_ok=True)
    for name, make in SOUNDS.items():
        if only is not None and name not in only:
            continue
        sound = finish(make(), 0.0 if name in LOOPED else 3.0)
        path = os.path.join(folder, ("danny_%s.wav" if ship else "preview_danny_%s.wav") % name)
        write_wav(path, sound)
        print("%-40s %5d ms  peak %5.1f dBFS" % (os.path.basename(path), round(len(sound) * 1000 / SR),
                                                20.0 * math.log10(max(abs(s) for s in sound))))


if __name__ == "__main__":
    main()
