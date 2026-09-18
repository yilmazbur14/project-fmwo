"""Synthesizes Carter's Raging Demon sounds into Assets/Audio/SFX, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, sharing the building blocks of make_voices.py. Nothing is sampled or downloaded.

    python make_carter_sfx.py               writes carter_eye_flash, _warp, _dark, _rush_1..3, _strike,
                                            _parry_break, _fake_punish, _finish and _spent
    python make_carter_sfx.py PREVIEW_DIR   also writes preview copies there, plus preview_carter_round.wav:
                                            a whole round at the fight's timings, three clones parried, one
                                            landing and one bait taken

The round is one attack: his eyes flash, the player is dragged to the middle, the room goes dark and five clones
come through one at a time. So the five rushes carry the sound and everything else frames them: the rushes are the
driest and quietest things here, with three variants that differ in pitch and in how the air moves, and the frame
around them (the flash, the darkness, the release) is where the weight is. The parry reward is built on the parry
tinks' own struck-metal cluster, an octave under parry_tink_1 with the body they don't have, so the two ring as
one sound rather than two when they play together.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audio_voices"))

from make_voices import (SR, PROJECT, samples, contour, oscillator, pulse, envelope, noise, lowpass, highpass,
                         bandpass, mul, mix, delayed, normalized, saturate, loudness_db, read_wav, write_wav)
# The struck metal and the chime are the parry sounds' own, so carter_parry_break is audibly the tinks' bigger
# sibling and carter_finish resolves on the chord they ring.
from make_parry_sfx import CHIME_MODES, TINK_MODES, ring, sparkle, strike, struck
from make_bixby_roar import wander

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")

# Peaks chosen so that the sounds come out in the right order of size when you listen, not on paper: a sustained
# sound at the same peak as a transient one is far louder, so the sustained ones (the punish, the release) are
# peaked lower. The report prints the loudness each one actually lands on.
PEAK_DBFS = {
    "carter_eye_flash": -1.5,
    "carter_warp": -4.0,
    "carter_dark": -3.0,
    "carter_rush_1": -7.0,
    "carter_rush_2": -7.0,
    "carter_rush_3": -7.0,
    "carter_strike": -2.0,
    # Low enough that it and a parry tink landing on the same frame still leave the bus a dB of room.
    "carter_parry_break": -5.0,
    "carter_fake_punish": -8.5,
    "carter_finish": -6.0,
    "carter_spent": -7.0,
    # It lands in silence with the fight already over, so it does not have to shout to be heard.
    "carter_ko_ding": -6.0,
}

# Tritones stacked on tritones: a metal cluster in which no interval resolves.
WRONG_MODES = [(1.00, 1.00), (1.414, 0.85), (2.00, 0.42), (2.83, 0.50), (3.37, 0.22), (4.76, 0.14)]


# ------------------------------------------------------------------------------------------------- building blocks

def shaped(x, points):
    return mul(x, contour(len(x), points))


def placed(x, start_ms, n):
    """x starting start_ms in, padded and cut to exactly n samples."""
    out = [0.0] * n
    start = samples(start_ms)
    for i, s in enumerate(x[:max(0, n - start)]):
        out[start + i] = s
    return out


def swept_noise(n, rng, from_hz, to_hz, sweep_ms, q=0.7):
    """Noise sliding between two bands, by crossfading two fixed ones: how the rest of these generators move
    a filter."""
    source = noise(n, rng)
    a, b = bandpass(source, from_hz, q), bandpass(source, to_hz, q)
    blend = contour(n, [(0.0, 0.0), (sweep_ms, 1.0)])
    return [x * (1.0 - t) + y * t for x, y, t in zip(a, b, blend)]


def swept_lowpass(x, from_hz, to_hz, sweep_ms):
    """The same crossfade with lowpasses: something getting darker, or opening back up."""
    a, b = lowpass(x, from_hz), lowpass(x, to_hz)
    blend = contour(len(x), [(0.0, 0.0), (sweep_ms, 1.0)])
    return [p * (1.0 - t) + q * t for p, q, t in zip(a, b, blend)]


def tone(n, freq_points, partials, env_points=None, decay_ms=None, attack_ms=1.0, release_ms=8.0):
    """A pitched layer following a (ms, Hz) contour, either struck (decay_ms) or shaped by hand (env_points)."""
    body = oscillator(contour(n, freq_points), list(partials))
    if env_points is not None:
        return shaped(body, env_points)
    return mul(body, envelope(n, attack_ms, release_ms, decay_ms=decay_ms))


def finish(x, peak_dbfs, thin_hz, top_hz, edge_ms=2.0):
    """Trims the ends of the band, silences both ends of the sound and normalizes to the wanted peak."""
    x = lowpass(highpass(x, thin_hz), top_hz)
    edge = samples(edge_ms)
    for i in range(edge):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x)
    return [s * 10.0 ** (peak_dbfs / 20.0) / peak for s in x]


# ------------------------------------------------------------------------------------------------- the sounds

def build_eye_flash():
    """He takes hold of the player. The floor drops away under a metal ring tuned so it can't settle, with the
    smallest suck of air in front of the hit so it lands on something."""
    rng = random.Random(101)
    # The lip is kept short on purpose: the hit has to land close enough to the flash frame that a coder can play
    # this on the frame and still have them read as one thing.
    length_ms, onset_ms = 580.0, 40.0
    n = samples(length_ms - onset_ms)

    sub = tone(n, [(0.0, 165.0), (60.0, 74.0), (240.0, 36.0), (length_ms, 29.0)],
               [(1, 1.0), (2, 0.28), (3, 0.08)], attack_ms=1.2, release_ms=60.0, decay_ms=230.0)
    sub = saturate(normalized(sub), 1.6)

    metal = tone(n, [(0.0, 1330.0), (40.0, 1270.0), (length_ms, 1120.0)], WRONG_MODES,
                 attack_ms=0.8, release_ms=90.0, decay_ms=300.0)
    metal = mul(metal, [0.72 + 0.28 * math.cos(2.0 * math.pi * 6.5 * i / SR) for i in range(n)])

    flash = mul(swept_noise(n, rng, 6200.0, 2400.0, 55.0, q=0.9), envelope(n, 0.4, 20.0, decay_ms=38.0))

    lip_n = samples(onset_ms + 12.0)
    lip = shaped(bandpass(noise(lip_n, rng), 2600.0, 0.8),
                 [(0.0, 0.0), (onset_ms * 0.7, 0.3), (onset_ms, 1.0), (onset_ms + 12.0, 0.0)])

    return mix((0.14, lip), (1.0, delayed(mix((1.0, sub), (0.42, metal), (0.20, flash)), onset_ms)))


def build_warp():
    """The yank to the middle: air and pitch dragged upward, getting away from the player, and then stopped dead."""
    rng = random.Random(202)
    length_ms, arrive_ms = 330.0, 195.0
    pull_n = samples(arrive_ms + 8.0)
    rest_n = samples(length_ms) - samples(arrive_ms)

    air = shaped(swept_noise(pull_n, rng, 420.0, 3000.0, arrive_ms, q=0.6),
                 [(0.0, 0.0), (arrive_ms * 0.55, 0.18), (arrive_ms * 0.88, 0.75), (arrive_ms, 1.0),
                  (arrive_ms + 8.0, 0.0)])
    rise = tone(pull_n, [(0.0, 130.0), (arrive_ms * 0.6, 320.0), (arrive_ms, 940.0)],
                [(1, 1.0), (2, 0.30), (3, 0.12)],
                env_points=[(0.0, 0.0), (30.0, 0.12), (arrive_ms * 0.8, 0.5), (arrive_ms, 0.95),
                            (arrive_ms + 8.0, 0.0)])

    thud = tone(rest_n, [(0.0, 150.0), (35.0, 62.0), (length_ms, 48.0)], [(1, 1.0), (2, 0.2)],
                release_ms=40.0, decay_ms=75.0)
    snap = strike(rest_n, rng, 2700.0, 7.0, q=0.7)
    ring_down = mul(swept_noise(rest_n, rng, 1400.0, 500.0, 60.0, q=1.2), envelope(rest_n, 1.0, 30.0, decay_ms=55.0))

    return mix((0.45, air), (0.50, rise), (1.0, delayed(thud, arrive_ms)), (0.35, delayed(snap, arrive_ms)),
               (0.22, delayed(ring_down, arrive_ms)))


def build_dark():
    """The lights go and the spotlight comes on. The crowd is there for a moment and then it is behind a door:
    it ducks and darkens at the same time, which is what makes the room feel smaller."""
    rng = random.Random(303)
    length_ms = 560.0
    n = samples(length_ms)

    thud = lowpass(tone(n, [(0.0, 118.0), (50.0, 66.0), (length_ms, 54.0)], [(1, 1.0), (2, 0.30), (3, 0.09)],
                        attack_ms=2.0, release_ms=80.0, decay_ms=170.0), 260.0)
    wumph = mul(lowpass(noise(n, rng), 420.0), envelope(n, 3.0, 40.0, decay_ms=70.0))

    babble = mix((1.0, bandpass(noise(n, rng), 850.0, 0.5)), (0.45, bandpass(noise(n, rng), 2400.0, 0.4)))
    crowd = swept_lowpass(mul(babble, [1.0 + 0.5 * w for w in wander(n, 13.0, rng)]), 5200.0, 330.0, 230.0)
    crowd = shaped(crowd, [(0.0, 0.9), (40.0, 1.0), (190.0, 0.35), (300.0, 0.09), (length_ms, 0.04)])

    clack = mix((1.0, strike(n, rng, 2900.0, 5.0, q=0.9)),
                (0.5, tone(n, [(0.0, 3400.0), (length_ms, 3400.0)], [(1, 1.0), (2.4, 0.4)],
                           attack_ms=0.5, release_ms=20.0, decay_ms=45.0)))
    hum = tone(n, [(0.0, 120.0), (length_ms, 120.0)], [(1, 1.0), (2, 0.5), (3, 0.18)],
               env_points=[(0.0, 0.0), (60.0, 0.0), (240.0, 1.0), (length_ms, 0.9)])

    return mix((1.0, thud), (0.5, wumph), (0.95, crowd), (0.30, placed(clack, 38.0, n)), (0.07, hum))


# One clone closing in. Five of these a round, so they stay short, dry and low in the band that tires the ear:
# the variants differ in weight and in how fast the air moves past, not in loudness.
RUSHES = [
    dict(seed=411, length_ms=200.0, body=168.0, air=(2500.0, 780.0), sweep=95.0, scuff=1700.0),
    dict(seed=412, length_ms=175.0, body=192.0, air=(2000.0, 640.0), sweep=80.0, scuff=2100.0),
    dict(seed=413, length_ms=160.0, body=150.0, air=(3000.0, 960.0), sweep=70.0, scuff=1450.0),
]


def build_rush(spec):
    rng = random.Random(spec["seed"])
    length_ms = spec["length_ms"]
    n = samples(length_ms)
    from_hz, to_hz = spec["air"]

    cloth = mul(swept_noise(n, rng, from_hz, to_hz, spec["sweep"], q=0.55),
                envelope(n, 1.5, 25.0, decay_ms=length_ms * 0.32))
    body = tone(n, [(0.0, spec["body"] * 1.7), (18.0, spec["body"]), (length_ms, spec["body"] * 0.8)],
                [(1, 1.0), (2, 0.45), (3, 0.18)], release_ms=25.0, decay_ms=34.0)
    scuff = strike(n, rng, spec["scuff"], 9.0, q=0.6)

    return mix((1.0, cloth), (0.60, saturate(body, 1.3)), (0.85, scuff))


def build_strike():
    """A clone gets through. Weight first, crack second, and a dull ring under it so it keeps hurting for a moment."""
    rng = random.Random(505)
    length_ms = 440.0
    n = samples(length_ms)

    thump = saturate(tone(n, [(0.0, 190.0), (28.0, 78.0), (160.0, 50.0), (length_ms, 44.0)],
                          [(1, 1.0), (2, 0.35), (3, 0.12)], release_ms=90.0, decay_ms=180.0), 1.8)
    meat = mul(bandpass(noise(n, rng), 420.0, 0.8), envelope(n, 1.2, 60.0, decay_ms=95.0))
    crack = mix((1.0, strike(n, rng, 2300.0, 14.0, q=0.6)), (0.6, strike(n, rng, 4200.0, 7.0, q=0.8)))
    splat = mul(bandpass(noise(n, rng), 1500.0, 0.5), envelope(n, 0.8, 40.0, decay_ms=48.0))
    dull = mul(lowpass(struck(n, 205.0, TINK_MODES, 260.0, 0.85, rng, shimmer=1), 1100.0),
               envelope(n, 2.0, 120.0, decay_ms=260.0))

    # Glued rather than layered, so the crack doesn't own the peak and leave the weight quiet.
    return saturate(normalized(mix((1.0, thump), (1.6, meat), (2.0, crack), (1.2, splat), (0.35, dull))), 1.3)


def build_parry_break():
    """A clone caught and shattered. The parry tinks' cluster an octave under parry_tink_1, with a low anchor for
    the mass they don't have and the shards up above the band they ring in, so this and a tink can play together."""
    rng = random.Random(606)
    length_ms = 700.0
    n = samples(length_ms)

    metal = struck(n, 700.0, TINK_MODES, 560.0, 1.08, rng)
    anchor = struck(n, 175.0, TINK_MODES[:3], 230.0, 0.9, rng, shimmer=1)
    click = strike(n, rng, 3600.0, 5.0, q=0.7)

    shards = []
    for _ in range(11):
        hz = rng.uniform(3600.0, 9500.0)
        start_ms = rng.uniform(0.0, 85.0)
        piece = ring(n - samples(start_ms), hz, 0.30 - 0.16 * (hz - 3600.0) / 5900.0,
                     rng.uniform(45.0, 170.0), attack_ms=0.4, phase=rng.uniform(0.0, math.pi))
        shards.append((1.0, delayed(piece, start_ms)))

    shine = sparkle(n, [(35.0, 2600.0, 6800.0, 200.0, 0.22), (90.0, 1500.0, 2450.0, 150.0, 0.10)])

    return mix((1.0, metal), (0.34, anchor), (0.55, click), (0.80, mix(*shards)), (0.16, shine))


def build_fake_punish():
    """A yellow parried. Two voices a bad interval apart sagging downward while the filter shuts on them and the
    wobble gets slower and deeper: nothing bright in it anywhere, and it ends limp instead of stopping."""
    rng = random.Random(707)
    length_ms = 560.0
    n = samples(length_ms)

    freqs = [(0.0, 452.0), (40.0, 430.0), (300.0, 262.0), (length_ms, 228.0)]
    detuned = [(0.0, 452.0 * 1.024), (40.0, 430.0 * 1.024), (300.0, 262.0 * 1.024), (length_ms, 228.0 * 1.024)]
    sour = swept_lowpass(mix((0.60, oscillator(contour(n, freqs), pulse(0.32, 16))),
                             (0.55, oscillator(contour(n, detuned), pulse(0.28, 16), phase=1.1))),
                         2600.0, 520.0, 300.0)
    sour = shaped(sour, [(0.0, 0.0), (12.0, 1.0), (90.0, 0.8), (300.0, 0.55), (460.0, 0.2), (length_ms, 0.0)])

    rates = contour(n, [(0.0, 7.5), (length_ms, 3.0)])
    depths = contour(n, [(0.0, 0.05), (160.0, 0.30), (length_ms, 0.60)])
    phase = 0.0
    sag = []
    for rate, depth in zip(rates, depths):
        sag.append(1.0 - depth * 0.5 * (1.0 - math.cos(phase)))
        phase += 2.0 * math.pi * rate / SR
    sour = mul(sour, sag)

    hiss = shaped(swept_noise(n, rng, 2600.0, 380.0, 260.0, q=0.5),
                  [(0.0, 0.0), (8.0, 0.9), (120.0, 0.3), (330.0, 0.1), (length_ms, 0.0)])
    tick = strike(n, rng, 1700.0, 8.0, q=1.0)
    dud = tone(n, [(0.0, 120.0), (40.0, 76.0), (length_ms, 66.0)], [(1, 1.0), (2, 0.2)],
               attack_ms=2.0, release_ms=60.0, decay_ms=110.0)

    return mix((1.0, sour), (0.30, hiss), (0.35, tick), (0.50, dud))


def build_finish():
    """The fifth clone is gone and the darkness lifts: the room opening back up under the same F major the parry
    tinks ring on, two octaves down, swelling in instead of being struck and letting go at the end."""
    rng = random.Random(808)
    length_ms = 950.0
    n = samples(length_ms)

    layers = []
    for hz, amplitude, start_ms in ((349.2, 1.0, 0.0), (440.0, 0.80, 35.0), (523.3, 0.62, 70.0)):
        voice = struck(n - samples(start_ms), hz, CHIME_MODES, 620.0, 1.0, rng, shimmer=1)
        onset = samples(90.0)
        for i in range(onset):
            voice[i] *= 0.5 - 0.5 * math.cos(math.pi * i / onset)
        layers.append((amplitude, delayed(voice, start_ms)))

    room = mix((1.0, bandpass(noise(n, rng), 1100.0, 0.4)), (0.5, bandpass(noise(n, rng), 3200.0, 0.35)))
    room = swept_lowpass(mul(room, [1.0 + 0.4 * w for w in wander(n, 11.0, rng)]), 420.0, 5800.0, 520.0)
    room = shaped(room, [(0.0, 0.03), (120.0, 0.12), (520.0, 0.55), (760.0, 0.42), (length_ms, 0.0)])

    lift = sparkle(n, [(60.0, 320.0, 1450.0, 420.0, 0.30), (230.0, 2600.0, 5200.0, 340.0, 0.10)])
    hold = tone(n, [(0.0, 87.3), (300.0, 87.3), (length_ms, 82.0)], [(1, 1.0), (2, 0.35), (3, 0.14), (4, 0.05)],
                env_points=[(0.0, 0.0), (110.0, 1.0), (520.0, 0.8), (length_ms, 0.0)])

    return mix(*layers, (0.45, room), (1.0, lift), (0.40, hold))


def build_spent():
    """He has nothing left. One breath out through a throat that closes as it empties, half-voiced, with his weight
    settling under it: short, so it reads as an opening and not as a moment."""
    rng = random.Random(909)
    length_ms = 460.0
    n = samples(length_ms)

    source = noise(n, rng)
    throat = mix((1.0, bandpass(source, 620.0, 1.1)), (0.55, bandpass(source, 1180.0, 1.3)),
                 (0.30, bandpass(source, 2600.0, 0.8)))
    breath = shaped(swept_lowpass(throat, 3200.0, 900.0, 320.0),
                    [(0.0, 0.0), (22.0, 1.0), (150.0, 0.62), (320.0, 0.22), (length_ms, 0.0)])

    voiced = lowpass(tone(n, [(0.0, 104.0), (120.0, 86.0), (length_ms, 74.0)],
                          [(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.08)],
                          env_points=[(0.0, 0.0), (30.0, 0.9), (200.0, 0.45), (length_ms, 0.0)]), 700.0)
    settle = tone(n, [(0.0, 84.0), (60.0, 54.0), (length_ms, 46.0)], [(1, 1.0), (2, 0.18)],
                  attack_ms=3.0, release_ms=70.0, decay_ms=120.0)
    rustle = shaped(mul(bandpass(noise(n, rng), 3400.0, 0.5), [max(0.0, w) for w in wander(n, 28.0, rng)]),
                    [(0.0, 0.5), (90.0, 0.25), (length_ms, 0.0)])

    return mix((1.0, breath), (0.34, voiced), (0.16, settle), (0.12, rustle))


# A real tuned bell, which is the only pitched thing in this set that is allowed to ring. The partial that decides
# how it feels is the tierce at 1.2, a minor third over the prime: with the quint at 1.5 the bell spells a minor
# triad, which is why church bells sound like a verdict and why there is no 1.25 major third anywhere in here.
# The hum an octave under the prime rings longest, so the sound sinks as it dies rather than thinning out.
BELL_MODES = [
    # The hum sits five cents under a true octave and the tierce a shade over a tempered minor third, so the bell
    # is very slightly sour against itself. Tuned exactly it comes out sad; tuned like this it comes out wrong.
    (0.4985, 0.42, 1.30),
    (1.00, 1.00, 1.00),
    (1.193, 0.88, 0.86),
    (1.50, 0.38, 0.64),
    (2.00, 0.60, 0.55),
    (2.50, 0.26, 0.40),
    (3.01, 0.32, 0.33),
    (4.02, 0.20, 0.23),
    (5.43, 0.12, 0.16),
    (6.79, 0.07, 0.11),
]

# Three to choose between, since nobody here can hear the reference. None of them is in the key of the parry
# sounds: the outer two are B, a tritone from their F, and the middle one is E, a semitone under it. The note the
# player dies to is one that will not resolve against the note they win to, whichever gets picked.
# KO_DING is the index that ships as carter_ko_ding.wav; the preview writes all three to choose from.
KO_DING_CANDIDATES = [
    dict(name="low_long", prime=1975.5, tail_ms=1550.0, length_ms=1750.0, seed=1301),
    dict(name="mid", prime=2637.0, tail_ms=1250.0, length_ms=1430.0, seed=1302),
    dict(name="very_high", prime=3951.1, tail_ms=950.0, length_ms=1120.0, seed=1303),
]
KO_DING = 1


def build_ko_ding(spec):
    """The emblem on his back lights. One struck bell, nothing else: no noise crack, no cluster, no room. It has
    to land on a single frame, so it starts at full level with only enough of an edge on it not to click."""
    rng = random.Random(spec["seed"])
    n = samples(spec["length_ms"])

    bell = struck(n, spec["prime"], BELL_MODES, spec["tail_ms"], 1.0, rng, shimmer=5)
    # The mallet, kept narrow and high so it reads as part of the bell rather than as a separate tick.
    contact = strike(n, rng, spec["prime"] * 3.2, 4.0, q=1.6)

    return mix((1.0, bell), (0.09, contact))


# (build, how far to thin the bottom, where to stop the top). The rushes lose everything above 6.8 kHz because
# they play five times in a round; the reward keeps its shards.
SOUNDS = [
    ("carter_eye_flash", build_eye_flash, 20.0, 12000.0),
    ("carter_warp", build_warp, 45.0, 12000.0),
    ("carter_dark", build_dark, 25.0, 11000.0),
    ("carter_rush_1", lambda: build_rush(RUSHES[0]), 115.0, 6800.0),
    ("carter_rush_2", lambda: build_rush(RUSHES[1]), 115.0, 6800.0),
    ("carter_rush_3", lambda: build_rush(RUSHES[2]), 115.0, 6800.0),
    ("carter_strike", build_strike, 28.0, 9000.0),
    ("carter_parry_break", build_parry_break, 110.0, 14500.0),
    ("carter_fake_punish", build_fake_punish, 70.0, 7000.0),
    ("carter_finish", build_finish, 55.0, 13000.0),
    ("carter_spent", build_spent, 90.0, 9000.0),
    ("carter_ko_ding", lambda: build_ko_ding(KO_DING_CANDIDATES[KO_DING]), 200.0, 15000.0),
]

# The round the preview plays: (when, which sound). Clones 1, 2 and 4 are parried, 3 lands, 5 is the bait. The
# primary parry hit belongs to make_parry_hit.py rather than to this file, and the preview reads it back out of
# the SFX folder, so the round sounds like the fight instead of like this file's own contents.
ROUND = [(0.0, "carter_eye_flash"), (520.0, "carter_warp"), (900.0, "carter_dark"),
         (1500.0, "carter_rush_1"), (1640.0, "parry_hit_1"), (1640.0, "carter_parry_break"),
         (2050.0, "carter_rush_2"), (2190.0, "parry_hit_2"), (2190.0, "carter_parry_break"),
         (2600.0, "carter_rush_3"), (2740.0, "carter_strike"),
         (3150.0, "carter_rush_1"), (3290.0, "parry_hit_3"), (3290.0, "carter_parry_break"),
         (3700.0, "carter_rush_2"), (3840.0, "carter_fake_punish"),
         (4400.0, "carter_finish"), (4780.0, "carter_spent")]


# ------------------------------------------------------------------------------------------------- output

def report(name, x):
    """Length, peak, how loud it actually sounds, where its weight sits and how fast it gets out of the way."""
    low = sum(s * s for s in lowpass(x, 250.0))
    high = sum(s * s for s in highpass(x, 2000.0))
    total = sum(s * s for s in x) + 1e-12
    frame = samples(10.0)
    levels = [10.0 * math.log10(sum(s * s for s in x[i:i + frame]) / frame + 1e-12)
              for i in range(0, max(1, len(x) - frame), frame)]
    top = max(levels)
    print("%-20s %4.0f ms  peak %5.1f dBFS  loudness %5.1f dB  low %2.0f%% high %2.0f%%  "
          "loudest at %3.0f ms  30 dB down by %3.0f ms" % (
              name, len(x) * 1000.0 / SR, 20.0 * math.log10(max(abs(s) for s in x)), loudness_db(x),
              100.0 * low / total, 100.0 * high / total, (levels.index(top) + 1) * 10.0,
              (max((i for i, level in enumerate(levels) if level > top - 30), default=0) + 1) * 10.0))


def main():
    os.makedirs(SFX_DIR, exist_ok=True)
    sounds = {}
    for name, build, thin_hz, top_hz in SOUNDS:
        sounds[name] = finish(build(), PEAK_DBFS[name], thin_hz, top_hz)
        write_wav(os.path.join(SFX_DIR, "%s.wav" % name), sounds[name])
        report("%s.wav" % name, sounds[name])

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        os.makedirs(folder, exist_ok=True)
        for name, sound in sounds.items():
            write_wav(os.path.join(folder, "preview_%s.wav" % name), sound)

        # All three ko_ding candidates, so the one that ships can be chosen by ear.
        for number, spec in enumerate(KO_DING_CANDIDATES, 1):
            candidate = finish(build_ko_ding(spec), PEAK_DBFS["carter_ko_ding"], 200.0, 15000.0)
            write_wav(os.path.join(folder, "preview_carter_ko_ding_%d_%s.wav" % (number, spec["name"])), candidate)
            report("carter_ko_ding %d %s" % (number, spec["name"]), candidate)

        for _, name in ROUND:
            if name not in sounds:
                sounds[name] = read_wav(os.path.join(SFX_DIR, "%s.wav" % name))

        played = [0.0] * samples(ROUND[-1][0] + 1400.0)
        for start_ms, name in ROUND:
            start = samples(start_ms)
            for i, s in enumerate(sounds[name]):
                if start + i < len(played):
                    played[start + i] += 0.7 * s
        write_wav(os.path.join(folder, "preview_carter_round.wav"), played)
        report("preview_carter_round.wav", played)


if __name__ == "__main__":
    main()
