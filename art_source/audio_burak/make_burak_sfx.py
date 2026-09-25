"""Synthesizes Captain Burak's sound effects, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, built from make_voices.py's blocks and make_bixby_roar.py's voice source (pulse_train),
so every run writes identical files. Nothing is sampled or downloaded.

    python make_burak_sfx.py PREVIEW_DIR   writes preview_burak_<name>.wav for every sound into PREVIEW_DIR
    python make_burak_sfx.py --ship        writes burak_<name>.wav into Assets/Audio/SFX
    ... --only gunshot,blast               either of those, for only the sounds named

Run with no argument, it only says how to use it: it never writes into the shipped folder unless asked to.
Ship a new sound with --only, so the approved ones are never rewritten.

Every sound is normalized to a -3 dBFS peak; BurakBossArtLayout.SFX sets how loud each one plays. The fuse's hiss
loops, so its end is cross-faded into its start and its edges are left open.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_voices"))

from make_voices import (SR, PROJECT, samples, contour, oscillator, envelope, noise, lowpass, highpass, bandpass, mul,
                         mix, delayed, normalized, saturate, write_wav)
from make_bixby_roar import pulse_train

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")
PEAK_DBFS = -3.0
# Sounds that loop end to start: no fade at their edges.
LOOPED = ("fuse_hiss",)


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


def voice(n, pitch_points, jitter, sub, rng, pulse_ms=0.8):
    """His voice's source: sharp glottal pulses along (ms, Hz) points, rough by `jitter`, with every other pulse
    quietened by `sub` for a growl an octave down."""
    return pulse_train(contour(n, pitch_points), pulse_ms, [jitter] * n, [sub] * n, rng)


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


AH = [(820, 3.0, 1.0), (1250, 4.0, 0.7), (2600, 5.0, 0.35)]
UH = [(640, 3.0, 1.0), (1190, 4.0, 0.6), (2390, 5.0, 0.3)]


# ------------------------------------------------------------------------------------------------- the kegs

def throw():
    """The heave: a "HUP" grunt on 150 Hz pulses and a whoosh climbing 300 Hz to 2 kHz as the keg leaves his hands."""
    rng = random.Random(801)
    n = samples(460)
    grunt_n = samples(160)
    grunt = formants(voice(grunt_n, [(0, 155), (160, 132)], 0.04, 0.3, rng), UH)
    grunt = mul(saturate(normalized(grunt), 1.8), envelope(grunt_n, 3, 60, decay_ms=110))
    whoosh_n = samples(380)
    whoosh = mul(sliding_bandpass(noise(whoosh_n, rng), 300.0, 2000.0, 1.5), envelope(whoosh_n, 40, 200, decay_ms=240))
    out = [0.0] * n
    place(out, grunt, 0, 0.8)
    place(out, whoosh, samples(80), 0.7)
    return out


def barrel_land():
    """A keg dropping onto the canvas: a thump falling 110 to 55 Hz, the hollow "tok" of its staves at 380 Hz and a
    puff off the mat."""
    rng = random.Random(802)
    n = samples(380)
    thump = mul(sweep(n, [(0, 110), (380, 55)]), envelope(n, 2, 120, decay_ms=120))
    tok = mul(oscillator([380.0] * n, [(1, 1.0), (2.3, 0.4), (3.9, 0.2)]), envelope(n, 1, 60, decay_ms=45))
    puff = mul(bandpass(noise(n, rng), 900, 0.9), envelope(n, 2, 100, decay_ms=60))
    return mix((1.0, thump), (0.45, tok), (0.35, puff))


def barrel_hit():
    """A punch cracking a stave: a sharp crack of noise around 2.2 kHz over a knock at 260 Hz, with wood's inharmonic
    partials. The code pitches it up as the keg splits."""
    rng = random.Random(803)
    n = samples(240)
    crack = mul(bandpass(highpass(noise(n, rng), 800.0), 2200, 1.2), envelope(n, 1, 40, decay_ms=25))
    knock = mul(oscillator([260.0] * n, [(1, 1.0), (2.4, 0.5), (4.1, 0.25)]), envelope(n, 1, 80, decay_ms=55))
    return mix((1.0, crack), (0.8, knock))


def barrel_break():
    """A keg bursting: a spray of splinter cracks over 0.3 s, the staves' last knock falling away, and a dull poof of
    powder."""
    rng = random.Random(804)
    n = samples(700)
    splinters = [0.0] * n
    for _ in range(18):
        start = samples(rng.uniform(0.0, 300.0))
        length = samples(rng.uniform(8.0, 30.0))
        crack = mul(bandpass(noise(length, rng), rng.uniform(1500.0, 4500.0), 2.0), envelope(length, 1, 6, decay_ms=10))
        place(splinters, crack, start, rng.uniform(0.4, 1.0))
    knock = mul(sweep(n, [(0, 180), (400, 90)]), envelope(n, 2, 120, decay_ms=90))
    poof = mul(lowpass(noise(n, rng), 600.0), envelope(n, 15, 300, decay_ms=260))
    return mix((1.0, splinters), (0.7, knock), (0.9, poof))


def barrel_tonk():
    """A punch on an armed keg: a dull, damped thunk at 150 Hz that goes nowhere."""
    n = samples(200)
    return mul(lowpass(oscillator([150.0] * n, [(1, 1.0), (2.2, 0.3)]), 900.0), envelope(n, 2, 60, decay_ms=45))


def fuse_hiss():
    """The lit fuses: a bright hiss fluttering at 13 Hz with sparse crackle, 2 s, looping without a seam."""
    rng = random.Random(805)
    fade = samples(200)
    n = samples(2000) + fade
    hiss = bandpass(highpass(noise(n, rng), 2500.0), 5000, 0.9)
    crackle = bandpass([rng.uniform(-1.0, 1.0) if rng.random() < 0.012 else 0.0 for _ in range(n)], 3000, 1.0)
    flutter = [0.8 + 0.2 * math.sin(2.0 * math.pi * 13.0 * i / SR) for i in range(n)]
    return loop_seam(mix((1.0, mul(hiss, flutter)), (1.6, crackle)), fade)


def blast():
    """A keg going up: a boom falling 55 to 30 Hz, a burst of noise, crackle and a long low rumble, 1.6 s."""
    rng = random.Random(808)
    n = samples(1600)
    boom = mul(sweep(n, [(0, 55), (400, 38), (1600, 30)]), envelope(n, 2, 500, decay_ms=420))
    burst = mul(lowpass(noise(n, rng), 3000.0), envelope(n, 1, 300, decay_ms=120))
    crackle = [rng.uniform(-1.0, 1.0) if rng.random() < 0.02 else 0.0 for _ in range(n)]
    crackle = mul(bandpass(crackle, 2500, 1.0), envelope(n, 50, 600, decay_ms=500))
    rumble = mul(lowpass(noise(n, rng), 250.0), envelope(n, 30, 800, decay_ms=700))
    return mix((1.0, boom), (0.6, burst), (0.5, crackle), (1.2, rumble))


# ------------------------------------------------------------------------------------------------- the pistol

def load_click():
    """A bullet going in: the tamp's wooden clack, then the hammer cocking, a small metal click."""
    rng = random.Random(806)
    n = samples(260)
    clack_n = samples(40)
    clack = mul(bandpass(noise(clack_n, rng), 1400, 1.5), envelope(clack_n, 1, 20, decay_ms=15))
    click_n = samples(60)
    click = mix((1.0, mul(bandpass(noise(click_n, rng), 4200, 3.0), envelope(click_n, 0.5, 20, decay_ms=8))),
                (0.5, mul(oscillator([3100.0] * click_n, [(1, 1.0)]), envelope(click_n, 0.5, 30, decay_ms=12))))
    out = [0.0] * n
    place(out, clack, 0, 0.9)
    place(out, click, samples(140))
    return out


def gunshot():
    """His flintlock: a bright crack, a thump sliding 80 to 60 Hz under it, and a tail rolling off the back of the
    arena."""
    rng = random.Random(807)
    n = samples(700)
    crack_n = samples(90)
    crack = mul(highpass(noise(crack_n, rng), 1200.0), envelope(crack_n, 0.5, 60, decay_ms=22))
    thump_n = samples(220)
    thump = mul(sweep(thump_n, [(0, 80), (220, 60)]), envelope(thump_n, 1, 90, decay_ms=70))
    dry = mix((1.0, crack), (0.9, thump))
    out = mul(lowpass(noise(n, rng), 1200.0), envelope(n, 10, 400, decay_ms=260))
    out = [0.3 * s for s in out]
    place(out, dry, 0)
    place(out, lowpass(dry, 1600), samples(90), 0.2)
    return out


def misfire():
    """Nothing left to shoot: the hammer's dry click, then a sad little fizzle sagging away."""
    rng = random.Random(809)
    n = samples(700)
    click_n = samples(50)
    click = mul(bandpass(noise(click_n, rng), 3600, 2.5), envelope(click_n, 0.5, 20, decay_ms=8))
    fizz_n = samples(520)
    fizz = mul(sliding_bandpass(noise(fizz_n, rng), 3000.0, 600.0, 2.2), envelope(fizz_n, 20, 200, decay_ms=300))
    sag = mul(sweep(fizz_n, [(0, 520), (520, 330)]), envelope(fizz_n, 30, 200, decay_ms=280))
    out = [0.0] * n
    place(out, click, 0)
    place(out, fizz, samples(120), 0.5)
    place(out, sag, samples(120), 0.25)
    return out


def taunt():
    """Blowing the smoke off his muzzle: a soft "fwoo", breath through a band sliding down from 1.4 kHz to 500 Hz."""
    rng = random.Random(813)
    n = samples(600)
    breath = sliding_bandpass(noise(n, rng), 1400.0, 500.0, 1.2)
    return mul(breath, mul(contour(n, [(0, 0.0), (150, 1.0), (600, 0.3)]), envelope(n, 20, 120)))


# ------------------------------------------------------------------------------------------------- the cutlass

def slash():
    """The cutlass: a fast whoosh, noise through a band climbing 500 Hz to 3.5 kHz, with a thin edge of 6 kHz air.
    The three swings pitch it three ways."""
    rng = random.Random(811)
    n = samples(300)
    shape = contour(n, [(0, 0.0), (110, 1.0), (300, 0.0)])
    whoosh = mul(sliding_bandpass(noise(n, rng), 500.0, 3500.0, 2.0), shape)
    edge = mul(bandpass(highpass(noise(n, rng), 4000.0), 6000, 2.0), shape)
    return mix((1.0, whoosh), (0.25, edge))


def clang():
    """A swing parried: steel on steel, a bright strike and inharmonic partials ringing out."""
    rng = random.Random(812)
    n = samples(900)
    strike_n = samples(20)
    strike = mul(highpass(noise(strike_n, rng), 2000.0), envelope(strike_n, 0.5, 10))
    ring = mix(*[(a, mul(oscillator([hz] * n, [(1, 1.0)]), envelope(n, 1, 200, decay_ms=d)))
                 for hz, a, d in ((1180.0, 1.0, 420), (2710.0, 0.6, 260), (4390.0, 0.35, 160), (6120.0, 0.2, 90))])
    return mix((0.8, strike), (1.0, ring))


# ------------------------------------------------------------------------------------------------- the laugh

def laugh():
    """His laugh, "HA-HA-HA-HAAA": four bursts of 200-220 Hz pulses through "ah", each after a breathy "h", the last
    long and falling toward 180 Hz, 1.4 s."""
    rng = random.Random(810)
    n = samples(1400)
    out = [0.0] * n
    for start_ms, length_ms, hz in ((0, 150, 215), (230, 150, 220), (460, 150, 210), (700, 620, 205)):
        m = samples(length_ms)
        last = length_ms > 300
        ha = formants(voice(m, [(0, hz * 1.04), (length_ms, hz * (0.88 if last else 0.96))], 0.03, 0.15, rng), AH)
        ha = mul(saturate(normalized(ha), 1.8), envelope(m, 4, 260 if last else 60))
        h_n = samples(40)
        h = mul(bandpass(noise(h_n, rng), 1800, 1.0), envelope(h_n, 2, 30))
        place(out, h, samples(start_ms), 0.3)
        place(out, ha, samples(start_ms + 20))
    return out


SOUNDS = {
    "throw": throw,
    "barrel_land": barrel_land,
    "barrel_hit": barrel_hit,
    "barrel_break": barrel_break,
    "barrel_tonk": barrel_tonk,
    "fuse_hiss": fuse_hiss,
    "blast": blast,
    "load_click": load_click,
    "gunshot": gunshot,
    "misfire": misfire,
    "taunt": taunt,
    "slash": slash,
    "clang": clang,
    "laugh": laugh,
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
        path = os.path.join(folder, ("burak_%s.wav" if ship else "preview_burak_%s.wav") % name)
        write_wav(path, sound)
        print("%-40s %5d ms  peak %5.1f dBFS" % (os.path.basename(path), round(len(sound) * 1000 / SR),
                                                20.0 * math.log10(max(abs(s) for s in sound))))


if __name__ == "__main__":
    main()
