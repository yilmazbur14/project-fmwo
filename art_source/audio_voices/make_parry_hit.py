"""Synthesizes the primary parry hit into Assets/Audio/SFX, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, sharing the building blocks of make_voices.py. Nothing is sampled or downloaded.

    python make_parry_hit.py               writes parry_hit_1..3.wav
    python make_parry_hit.py PREVIEW_DIR   also writes preview copies there, plus preview_parry_chain.wav
                                           (five hits 90 ms apart, then three 110 ms apart) and
                                           preview_parry_stack.wav (each hit under its streak tink)

An imitation of the Street Fighter III parry, which is a clink and not a chime. Four things make it that:

A hard broadband click at the very front. Three milliseconds of bright noise carrying most of the energy of the
whole sound. This is what "crisp" is, and no stack of partials can produce it however fast they start: an earlier
attempt at this sound was a pitched cluster with a fast attack and it came out pretty rather than sharp.

A clangy cluster rather than a musical one. The ratios are deliberately irregular and avoid fifths and octaves,
and the lowest three each carry a twin about one percent away, so they beat roughly once over the length of the
sound. That is what makes it read as a small piece of struck metal instead of a bell note.

A pitch drop across the first nine milliseconds. Struck metal goes slightly sharp on impact and falls into its
note; without that it sounds plucked.

Almost no sustain. The top of the cluster is gone in under ten milliseconds and the root inside fifty, so the
whole thing is over before the ear files it as a note. It is dry: no room, no tail, nothing that blooms.

It is pitched at F7, one octave over parry_tink_1 and two over carter_parry_break, so the parry family is one note
across three octaves. The three variants are the same clink struck slightly differently, not three sounds.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_voices import (SR, PROJECT, samples, contour, noise, lowpass, highpass, mix, loudness_db, read_wav,
                         write_wav)

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")

# High, because a transient this short cuts through a mix on its peak rather than on its energy, but low enough
# that it and any one of the tinks or carter_parry_break landing on the same frame at 0 dB still stay under the
# ceiling. Three reward layers at once is past what any peak here can save; the tinks have to be ducked for that.
PEAK_DBFS = -3.0
LENGTH_MS = 120.0

# An octave over parry_tink_1's F6 root.
ROOT = 2793.8

# (ratio above the root, amplitude, how long it rings compared to the tail, how far its twin is detuned).
# No ratio here is a fifth, an octave or anything else that would sound like a chord, and the loudest partial is
# the second rather than the root. The twins on the bottom three beat about once over the life of the sound,
# which is the roughness that makes struck metal sound struck.
CLANG_MODES = [
    (1.00, 0.80, 1.00, 0.008),
    (1.37, 1.00, 0.62, 0.011),
    (1.82, 0.86, 0.44, 0.009),
    (2.29, 0.66, 0.30, 0.0),
    (2.66, 0.52, 0.24, 0.0),
    (3.18, 0.40, 0.18, 0.0),
    (3.94, 0.28, 0.13, 0.0),
    (4.61, 0.20, 0.10, 0.0),
    (5.77, 0.13, 0.07, 0.0),
]


# ------------------------------------------------------------------------------------------------- building blocks

def ping(n, freqs, amplitude, decay_ms, phase=0.0):
    """One partial following a per-sample frequency, at full level on the first sample and only ever quieter.
    Cosine rather than sine so it starts at its own peak: there is no attack anywhere in this sound."""
    decay = 6.908 / max(1.0, samples(decay_ms))
    out = []
    angle = phase
    for i in range(n):
        out.append(amplitude * math.exp(-decay * i) * math.cos(angle))
        angle += 2.0 * math.pi * freqs[i] / SR
    return out


def cluster(n, root, modes, tail_ms, fan, bend, glide_ms):
    """The clink. Everything bends down together over glide_ms, the way a struck object settles into its note."""
    shape = contour(n, [(0.0, bend), (glide_ms, 1.0), (LENGTH_MS, 1.0)])
    layers = []
    for index, (ratio, amplitude, scale, detune) in enumerate(modes):
        for gain, offset in ((1.0, 0.0), (0.62, detune)) if detune else ((1.0, 0.0),):
            freq = root * ratio * (1.0 + offset)
            if freq >= 15000.0:
                continue
            layers.append((gain, ping(n, [freq * s for s in shape], amplitude, tail_ms * scale, fan * index)))
    return mix(*layers)


def click(n, rng, low_hz, high_hz, decay_ms):
    """The hard front: broadband noise, already at full level on the first sample and gone in a few milliseconds.
    Broad on purpose rather than a narrow band, because a band is a pitch and this has to be a bang."""
    source = highpass(lowpass(noise(n, rng), high_hz), low_hz)
    decay = 6.908 / samples(decay_ms)
    return [s * math.exp(-decay * i) for i, s in enumerate(source)]


def knock(n, hz, decay_ms):
    """A scrap of body under the metal, short enough to be part of the transient rather than a note of its own."""
    return ping(n, [hz] * n, 1.0, decay_ms)


def finish(x, peak_dbfs):
    """Keeps the bottom out of the way of the fight's impacts, takes the very top off, and silences the end only:
    the front is left exactly as it is, because any window there is an attack and this sound must not have one."""
    x = lowpass(highpass(x, 220.0), 13000.0)
    edge = samples(1.5)
    for i in range(edge):
        x[-1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / edge)
    peak = max(abs(s) for s in x)
    return [s * 10.0 ** (peak_dbfs / 20.0) / peak for s in x]


# ------------------------------------------------------------------------------------------------- the hits

# One clink struck three slightly different ways: the seeds pick the grain of the click, and the rest moves by a
# percent or two. The seeds are also chosen so the very first sample lands on the sound's peak, which a noise
# front will not do on its own.
VARIANTS = [
    dict(seed=41, detune=1.000, tail_ms=48.0, fan=0.35, bend=1.070, glide_ms=9.0, click_hz=(1800.0, 11000.0),
         top_hz=5000.0, knock_hz=520.0, knock=0.12),
    dict(seed=17, detune=1.007, tail_ms=43.0, fan=0.33, bend=1.082, glide_ms=8.0, click_hz=(2000.0, 11500.0),
         top_hz=5400.0, knock_hz=560.0, knock=0.10),
    dict(seed=63, detune=0.993, tail_ms=53.0, fan=0.38, bend=1.060, glide_ms=10.5, click_hz=(1650.0, 10200.0),
         top_hz=4600.0, knock_hz=478.0, knock=0.14),
]

# The click carries the sound and the clink colours it, not the other way round.
CLICK_GAIN = 1.15
TOP_GAIN = 0.55
CLUSTER_GAIN = 0.62


def build_hit(spec):
    rng = random.Random(spec["seed"])
    n = samples(LENGTH_MS)
    low_hz, high_hz = spec["click_hz"]

    front = click(n, rng, low_hz, high_hz, 3.0)
    top = click(n, rng, spec["top_hz"], 13000.0, 1.1)
    metal = cluster(n, ROOT * spec["detune"], CLANG_MODES, spec["tail_ms"], spec["fan"], spec["bend"],
                    spec["glide_ms"])
    body = knock(n, spec["knock_hz"], 14.0)

    return mix((CLICK_GAIN, front), (TOP_GAIN, top), (CLUSTER_GAIN, metal), (spec["knock"], body))


# ------------------------------------------------------------------------------------------------- output

def report(name, x):
    total = sum(s * s for s in x) + 1e-12
    frame = samples(5.0)
    levels = [10.0 * math.log10(sum(s * s for s in x[i:i + frame]) / frame + 1e-12)
              for i in range(0, max(1, len(x) - frame), frame)]
    top = max(levels)
    peak = max(abs(s) for s in x)
    print("%-20s %4.0f ms  peak %5.1f dBFS  loudness %5.1f dB  first sample %+.2f dB of peak  "
          "%2.0f%% in first 10 ms  %2.0f%% over 3 kHz  20 dB down by %3.0f ms" % (
              name, len(x) * 1000.0 / SR, 20.0 * math.log10(peak), loudness_db(x),
              20.0 * math.log10(abs(x[0]) / peak), 100.0 * sum(s * s for s in x[:samples(10.0)]) / total,
              100.0 * sum(s * s for s in highpass(x, 3000.0)) / total,
              (max((i for i, level in enumerate(levels) if level > top - 20), default=0) + 1) * 5.0))


def chain(plan, tail_ms=400.0):
    out = [0.0] * samples(plan[-1][0] + tail_ms)
    for start_ms, sound in plan:
        start = samples(start_ms)
        for i, s in enumerate(sound):
            if start + i < len(out):
                out[start + i] += s
    return out


def main():
    os.makedirs(SFX_DIR, exist_ok=True)
    sounds = {}
    for number, spec in enumerate(VARIANTS, 1):
        name = "parry_hit_%d" % number
        sounds[name] = finish(build_hit(spec), PEAK_DBFS)
        write_wav(os.path.join(SFX_DIR, "%s.wav" % name), sounds[name])
        report("%s.wav" % name, sounds[name])

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        os.makedirs(folder, exist_ok=True)
        for name, sound in sounds.items():
            write_wav(os.path.join(folder, "preview_%s.wav" % name), sound)

        order = [sounds["parry_hit_1"], sounds["parry_hit_2"], sounds["parry_hit_3"]]
        # Carter's five clones, then a pause, then Josh's three cards.
        plan = [(90.0 * i, order[i % 3]) for i in range(5)]
        plan += [(700.0 + 110.0 * i, order[(i + 1) % 3]) for i in range(3)]
        write_wav(os.path.join(folder, "preview_parry_chain.wav"), chain(plan))
        report("preview_parry_chain.wav", chain(plan))

        # Each hit with the streak tink it would play over, 900 ms apart.
        tinks = [read_wav(os.path.join(SFX_DIR, "parry_tink_%d.wav" % n)) for n in (1, 2, 3)]
        stack = []
        for i in range(3):
            stack += [(900.0 * i, order[i]), (900.0 * i, tinks[i])]
        write_wav(os.path.join(folder, "preview_parry_stack.wav"), chain(stack, tail_ms=900.0))
        report("preview_parry_stack.wav", chain(stack, tail_ms=900.0))


if __name__ == "__main__":
    main()
