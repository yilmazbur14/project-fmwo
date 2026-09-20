"""Synthesizes the dash's whoosh into Assets/Audio/SFX/dash_whoosh.wav, as a 16-bit mono 44.1 kHz WAV.

Pure Python with a fixed seed, sharing the building blocks of make_voices.py. Nothing is sampled or downloaded.

    python make_dash_whoosh.py               writes dash_whoosh.wav
    python make_dash_whoosh.py PREVIEW_DIR   also writes a copy there, plus preview_dash_spam.wav (five dashes at the
                                             fastest the dash can repeat)

Noise through a band-pass that sweeps up and falls back, which is what air rushing past sounds like: the rise is the
body going by, the fall is it leaving. A thin layer of hiss rides the first few milliseconds so the start has an edge
without a click. It is short because the dash is, and quiet because it plays on every dash: it sits under the hit
sounds and under the perfect dodge's whoosh, so the dash reads without competing with what the dash was for.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_voices import SR, PROJECT, samples, contour, noise, highpass, lowpass, mix, normalized, loudness_db, write_wav

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")

LENGTH_MS = 160.0
SEED = 41
# Loudness in make_voices' measure, taken off Godot's mixer at 0 dB: hit_impact is -17.0, player_hurt -9.1 and the
# perfect dodge's whoosh -12.6. Eight under the quietest hit keeps it a texture rather than an event.
TARGET_DB = -25.0
# The dash repeats at best every 0.45 s (PlayerDefense.dash_cooldown_v2).
SPAM_GAP_MS = 450.0

# (ms, Hz) of the band's centre: up while the body passes, back down as it leaves.
SWEEP = [(0.0, 700.0), (70.0, 2600.0), (LENGTH_MS, 1400.0)]
BAND_Q = 1.3
HISS_HZ = 4500.0
HISS_GAIN = 0.35


def swept_band(x, centres, q):
    """Chamberlin state-variable band-pass following a per-sample centre frequency. Every centre used here is far under
    SR / 6, where this filter stays stable."""
    low = band = 0.0
    damping = 1.0 / q
    out = []
    for s, hz in zip(x, centres):
        f = 2.0 * math.sin(math.pi * hz / SR)
        low += f * band
        high = s - low - damping * band
        band += f * high
        out.append(band)
    return out


def shape(n):
    """A soft rise to a peak at 30 ms, then an exponential fall that is faded to exactly 0 at the end."""
    attack, peak_ms, tau = samples(18.0), samples(30.0), samples(42.0)
    release = samples(35.0)
    out = []
    for i in range(n):
        if i < attack:
            g = 0.5 - 0.5 * math.cos(math.pi * i / attack)
        elif i < peak_ms:
            g = 1.0
        else:
            g = math.exp(-(i - peak_ms) / tau)
        if n - 1 - i < release:
            g *= 0.5 - 0.5 * math.cos(math.pi * (n - 1 - i) / release)
        out.append(g)
    return out


def hiss_shape(n):
    fast = samples(4.0)
    return [(0.5 - 0.5 * math.cos(math.pi * min(i, fast) / fast)) * math.exp(-i / samples(20.0)) for i in range(n)]


def build():
    rng = random.Random(SEED)
    n = samples(LENGTH_MS)
    body = normalized(swept_band(noise(n, rng), contour(n, SWEEP), BAND_Q))
    body = [s * g for s, g in zip(body, shape(n))]
    hiss = normalized(highpass(noise(n, random.Random(SEED + 1)), HISS_HZ))
    hiss = [s * g for s, g in zip(hiss, hiss_shape(n))]
    x = lowpass(highpass(mix((1.0, body), (HISS_GAIN, hiss)), 250.0), 11000.0)
    x[0] = 0.0
    x[-1] = 0.0
    gain = 10.0 ** ((TARGET_DB - loudness_db(x)) / 20.0)
    return [s * gain for s in x]


def report(name, x):
    peak = max(abs(s) for s in x)
    print("%-22s %4.0f ms  peak %5.1f dBFS  loudness %5.1f dB" % (
        name, len(x) * 1000.0 / SR, 20.0 * math.log10(peak), loudness_db(x)))


def main():
    os.makedirs(SFX_DIR, exist_ok=True)
    whoosh = build()
    write_wav(os.path.join(SFX_DIR, "dash_whoosh.wav"), whoosh)
    report("dash_whoosh.wav", whoosh)

    if len(sys.argv) > 1:
        folder = sys.argv[1]
        os.makedirs(folder, exist_ok=True)
        write_wav(os.path.join(folder, "dash_whoosh.wav"), whoosh)
        spam = [0.0] * samples(SPAM_GAP_MS * 5 + LENGTH_MS)
        for k in range(5):
            start = samples(SPAM_GAP_MS * k)
            for i, s in enumerate(whoosh):
                spam[start + i] += s
        write_wav(os.path.join(folder, "preview_dash_spam.wav"), spam)


if __name__ == "__main__":
    main()
