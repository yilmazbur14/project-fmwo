"""Synthesizes the player's punch swing into Assets/Audio/SFX/punch_whoosh.wav, 16-bit mono 44.1 kHz.

Pure Python with a fixed seed, on make_voices.py's building blocks, so every run writes the same file.
Nothing is sampled or downloaded.

    python make_whoosh.py                 writes punch_whoosh.wav
    python make_whoosh.py --check         rebuilds it and compares with the project file
    python make_whoosh.py --measure DIR   also prints the loudness of the WAVs in DIR next to it
                                          (dump_audio.gd decodes the game's OGGs into such a folder)

A jab, not a sword: short and bright. Three layers:
  the swish, white noise through a band-pass whose centre rises from 700 Hz to 2.4 kHz over the first
  40 ms and falls back to 1.2 kHz, the air moving past the ear; most of the energy is here;
  the snap, 18 ms of noise above 4 kHz where the swish peaks, the arm locking out;
  the body, a 40 ms sine falling from 170 to 95 Hz, faint, so it lands as a punch rather than a breeze.
It is 125 ms long and is loudness-matched to HIT_REF_DB - HEADROOM_DB: on the same B-weighted scale as the
voices, the hit that follows it (hit_impact.ogg, measured at HIT_REF_DB) is always clearly louder.
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'audio_voices'))

from make_voices import SR, samples, contour, noise, highpass, mix, loudness_db, read_wav, write_wav, envelope

OUT = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Audio', 'SFX', 'punch_whoosh.wav'))
LENGTH_MS = 125.0
SEED = 20260918
# hit_impact.ogg decoded by dump_audio.gd, on make_voices.loudness_db's scale.
HIT_REF_DB = -17.0
HEADROOM_DB = 9.0
TARGET_DB = HIT_REF_DB - HEADROOM_DB


def swept_bandpass(x, centres, q):
    """A state-variable band-pass whose centre follows a per-sample list (Chamberlin SVF, 2x oversampled)."""
    low = band = 0.0
    out = []
    damp = 1.0 / q
    for s, hz in zip(x, centres):
        f = 2.0 * math.sin(math.pi * min(hz, SR / 6.0) / (2.0 * SR))
        for _ in range(2):
            high = s - low - damp * band
            band += f * high
            low += f * band
        out.append(band)
    return out


def build():
    rng = random.Random(SEED)
    n = samples(LENGTH_MS)

    centres = contour(n, [(0, 700.0), (40, 2400.0), (125, 1200.0)])
    swish = swept_bandpass(noise(n, rng), centres, 1.4)
    swish_env = envelope(n, 7, 30, decay_ms=55)
    swish = [s * g for s, g in zip(swish, swish_env)]

    m = samples(18)
    snap = highpass(noise(m, rng), 4000.0)
    snap_env = envelope(m, 1.5, 12)
    snap = [0.0] * samples(34) + [s * g for s, g in zip(snap, snap_env)]

    k = samples(40)
    freqs = contour(k, [(0, 170.0), (40, 95.0)])
    body, angle = [], 0.0
    for f in freqs:
        body.append(math.sin(angle))
        angle += 2.0 * math.pi * f / SR
    body_env = envelope(k, 3, 20, decay_ms=18)
    body = [0.0] * samples(20) + [s * g for s, g in zip(body, body_env)]

    x = mix((1.0, swish), (0.35, snap), (0.25, body))[:n]
    x = highpass(x, 60.0)
    edge = samples(1.5)
    for i in range(edge):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    gain = 10.0 ** ((TARGET_DB - loudness_db(x)) / 20.0)
    x = [s * gain for s in x]
    peak = max(abs(s) for s in x)
    assert peak < 0.9, peak
    return x


def main():
    x = build()
    if '--check' in sys.argv:
        disk = read_wav(OUT)
        same = len(disk) == len(x) and all(abs(a - b) <= 1.0 / 32767.0 + 1e-9 for a, b in zip(disk, x))
        assert same, 'punch_whoosh.wav differs from a rebuild'
        print('checked', OUT)
    else:
        write_wav(OUT, x)
        print('wrote', OUT)
    print('punch_whoosh: %.0f ms, loudness %.1f dB (target %.1f), peak %.1f dBFS'
          % (len(x) * 1000.0 / SR, loudness_db(x), TARGET_DB, 20 * math.log10(max(abs(s) for s in x))))
    if '--measure' in sys.argv:
        folder = sys.argv[sys.argv.index('--measure') + 1]
        for name in sorted(os.listdir(folder)):
            if name.endswith('.wav'):
                y = read_wav(os.path.join(folder, name))
                print('  %-22s %.0f ms, loudness %.1f dB, peak %.1f dBFS'
                      % (name, len(y) * 1000.0 / SR, loudness_db(y), 20 * math.log10(max(abs(s) for s in y) + 1e-12)))


if __name__ == '__main__':
    main()
