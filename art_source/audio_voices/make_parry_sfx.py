"""Synthesizes the parry sounds into Assets/Audio/SFX, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, sharing the building blocks of make_voices.py. Nothing is sampled or downloaded.

    python make_parry_sfx.py               writes parry_tink_1..3.wav and parry_streak.wav
    python make_parry_sfx.py PREVIEW_DIR   also writes preview copies there, plus preview_parry_sequence.wav:
                                           three parries 1.2 s apart, tiers 1, 2 and 3, with the sting on the third

The tinks are struck metal rather than tones: a cluster of partials at ratios that aren't whole numbers, each
ringing for a different length, with the high ones dying fastest, which is what a small bell or a blade edge does.
The three tiers climb a major triad (root, third, fifth) and get brighter and longer as the streak grows, and the
sting arpeggiates that same chord an octave down, so it lifts over the tink instead of fighting it.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_voices import (SR, PROJECT, samples, contour, noise, lowpass, highpass, bandpass, mul, mix, delayed,
                         write_wav)

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")
TINK_PEAK_DBFS = -6.0
STING_PEAK_DBFS = -8.0

# A struck-metal cluster: (ratio above the base note, amplitude, how long it rings compared to the tail).
# The ratios are deliberately not whole numbers, and the loudest partial is the second, not the base.
TINK_MODES = [
    (1.00, 0.55, 1.00),
    (1.48, 1.00, 0.95),
    (2.11, 0.80, 0.80),
    (2.74, 0.55, 0.62),
    (3.42, 0.40, 0.48),
    (4.15, 0.28, 0.36),
    (5.06, 0.20, 0.27),
    (6.13, 0.13, 0.20),
    (7.42, 0.08, 0.14),
]

# A chime for the sting: nearly a harmonic series, stretched a little so it stays metallic.
CHIME_MODES = [(1.00, 1.0, 1.0), (2.01, 0.5, 0.7), (3.04, 0.28, 0.5), (4.10, 0.15, 0.36), (5.22, 0.08, 0.26)]


# ------------------------------------------------------------------------------------------------- building blocks

def ring(n, freq, amplitude, decay_ms, attack_ms=1.0, phase=0.0):
    """One struck partial: it appears almost instantly and dies away exponentially."""
    attack = max(1, samples(attack_ms))
    decay = 6.908 / max(1.0, samples(decay_ms))
    step = 2.0 * math.pi * freq / SR
    out = []
    for i in range(n):
        gain = amplitude * math.exp(-decay * i)
        if i < attack:
            gain *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        out.append(gain * math.sin(step * i + phase))
    return out


def struck(n, base, modes, tail_ms, brightness, rng, shimmer=3):
    """The whole cluster. The first few partials get a twin a few cents away, so the tail shimmers
    the way real metal does instead of sitting still."""
    layers = []
    for index, (ratio, amplitude, decay_scale) in enumerate(modes):
        freq = base * ratio
        if freq > 15000.0:
            continue
        lift = amplitude * (1.0 + (brightness - 1.0) * index * 0.5)
        layers.append((1.0, ring(n, freq, lift, tail_ms * decay_scale, phase=rng.uniform(0.0, math.pi))))
        if index < shimmer:
            beat = freq * (1.0 + rng.uniform(0.0012, 0.0035))
            layers.append((0.5, ring(n, beat, lift, tail_ms * decay_scale, phase=rng.uniform(0.0, math.pi))))
    return mix(*layers)


def strike(n, rng, centre, length_ms, q=0.8):
    """The contact itself: a very short burst of high noise, the click before the ring."""
    burst = bandpass(noise(n, rng), centre, q)
    decay = 6.908 / samples(length_ms)
    attack = max(1, samples(0.2))
    out = []
    for i, s in enumerate(burst):
        gain = math.exp(-decay * i)
        if i < attack:
            gain *= i / attack
        out.append(s * gain)
    return out


def whoosh(n, rng, from_hz, to_hz, length_ms):
    """The tiny bit of air the parry moves: noise sweeping downward under the metal."""
    source = noise(n, rng)
    high = bandpass(source, from_hz, 0.7)
    low = bandpass(source, to_hz, 0.7)
    blend = contour(n, [(0.0, 0.0), (length_ms, 1.0)])
    decay = 6.908 / samples(length_ms)
    attack = max(1, samples(6.0))
    out = []
    for i in range(n):
        gain = math.exp(-decay * i)
        if i < attack:
            gain *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        out.append(gain * (high[i] * (1.0 - blend[i]) + low[i] * blend[i]))
    return out


def sparkle(n, sweeps):
    """Quiet high partials sliding upward a moment after the hit: the shine on the best parry."""
    layers = []
    for start_ms, from_hz, to_hz, length_ms, amplitude in sweeps:
        start = samples(start_ms)
        length = min(n - start, samples(length_ms))
        if length <= 0:
            continue
        freqs = contour(length, [(0.0, from_hz), (length_ms, to_hz)])
        decay = 6.908 / length
        attack = max(1, samples(12.0))
        phase = 0.0
        tone = []
        for i, f in enumerate(freqs):
            gain = amplitude * math.exp(-decay * i)
            if i < attack:
                gain *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
            tone.append(gain * math.sin(phase))
            phase += 2.0 * math.pi * f / SR
        layers.append((1.0, [0.0] * start + tone))
    return mix(*layers) if layers else [0.0] * n


def finish(x, peak_dbfs, thin_hz=320.0, top_hz=11000.0):
    """Keeps the low end out (these have to stay thin), takes the hardest edge off the top,
    silences both ends and normalizes to the wanted peak."""
    x = lowpass(highpass(x, thin_hz), top_hz)
    edge = samples(1.5)
    for i in range(edge):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x)
    return [s * 10.0 ** (peak_dbfs / 20.0) / peak for s in x]


# ------------------------------------------------------------------------------------------------- the sounds

# Root, major third, fifth: the tier a parry lands on is audible as a step up the chord.
TIERS = [
    dict(base=1400.0, tail_ms=430.0, brightness=1.00, length_ms=480.0, air=0.13, seed=11, sparkles=[]),
    dict(base=1764.0, tail_ms=540.0, brightness=1.16, length_ms=600.0, air=0.11, seed=12, sparkles=[]),
    dict(base=2097.0, tail_ms=680.0, brightness=1.32, length_ms=740.0, air=0.09, seed=13,
         sparkles=[(45.0, 3300.0, 5400.0, 170.0, 0.10), (95.0, 4300.0, 6800.0, 150.0, 0.07)]),
]


def build_tink(tier):
    rng = random.Random(tier["seed"])
    n = samples(tier["length_ms"])
    metal = struck(n, tier["base"], TINK_MODES, tier["tail_ms"], tier["brightness"], rng)
    click = strike(n, rng, tier["base"] * 2.4, 5.0)
    air = whoosh(n, rng, tier["base"] * 1.6, tier["base"] * 0.8, 70.0)
    return mix((1.0, metal), (0.35, click), (tier["air"], air), (1.0, sparkle(n, tier["sparkles"])))


def build_streak():
    """The reward at three in a row: the tinks' chord arpeggiated an octave down, under a shimmer that
    swells in behind it, so the third tink still cuts through on top."""
    rng = random.Random(21)
    n = samples(860.0)
    notes = [(0.0, 700.0, 520.0, 0.75, 8.0), (95.0, 882.0, 560.0, 0.85, 4.0),
             (190.0, 1048.0, 620.0, 0.95, 3.0), (285.0, 1400.0, 700.0, 1.0, 3.0)]
    layers = []
    for start_ms, freq, decay_ms, amplitude, attack_ms in notes:
        start = samples(start_ms)
        chime = struck(n - start, freq, CHIME_MODES, decay_ms, 1.0, rng, shimmer=1)
        onset = max(1, samples(attack_ms))
        for i in range(onset):
            chime[i] *= 0.5 - 0.5 * math.cos(math.pi * i / onset)
        layers.append((amplitude, [0.0] * start + chime))

    # A quiet line sliding up into the last note, and a shimmer that arrives with it.
    rise = sparkle(n, [(20.0, 420.0, 1400.0, 300.0, 0.18)])
    shine = mul(bandpass(noise(n, rng), 5200, 0.6),
                contour(n, [(0.0, 0.0), (300.0, 1.0), (430.0, 0.75), (860.0, 0.0)]))
    return mix(*layers, (1.0, rise), (0.13, shine))


# ------------------------------------------------------------------------------------------------- output

def report(name, x):
    frame = samples(10.0)
    levels = [20.0 * math.log10(math.sqrt(sum(s * s for s in x[i:i + frame]) / frame) + 1e-12)
              for i in range(0, len(x) - frame, frame)]
    top = max(levels)
    ring_out = max((i for i, level in enumerate(levels) if level > top - 30), default=0)
    print("%-20s %4.0f ms  peak %.1f dBFS  hit within %.0f ms  30 dB down by %.0f ms" % (
        name, len(x) * 1000.0 / SR, 20.0 * math.log10(max(abs(s) for s in x)),
        (levels.index(top) + 1) * 10.0, (ring_out + 1) * 10.0))


def main():
    os.makedirs(SFX_DIR, exist_ok=True)
    sounds = {}
    for number, tier in enumerate(TIERS, 1):
        sounds["parry_tink_%d" % number] = finish(build_tink(tier), TINK_PEAK_DBFS)
    sounds["parry_streak"] = finish(build_streak(), STING_PEAK_DBFS, thin_hz=220.0)

    for name, sound in sounds.items():
        write_wav(os.path.join(SFX_DIR, "%s.wav" % name), sound)
        report("%s.wav" % name, sound)

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        os.makedirs(folder, exist_ok=True)
        for name, sound in sounds.items():
            write_wav(os.path.join(folder, "preview_%s.wav" % name), sound)

        # Three parries 1.2 s apart, the sting a beat behind the third tink so that hit still lands first.
        sequence = [0.0] * samples(4000.0)
        plan = [(400.0, sounds["parry_tink_1"]), (1600.0, sounds["parry_tink_2"]),
                (2800.0, sounds["parry_tink_3"]), (2840.0, sounds["parry_streak"])]
        for start_ms, sound in plan:
            start = samples(start_ms)
            for i, s in enumerate(sound):
                if start + i < len(sequence):
                    sequence[start + i] += s
        write_wav(os.path.join(folder, "preview_parry_sequence.wav"), sequence)
        report("preview_parry_sequence.wav", sequence)


if __name__ == "__main__":
    main()
