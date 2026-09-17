"""Synthesizes beast Bixby's transformation roar into Assets/Audio/SFX, as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, sharing the building blocks of make_voices.py. Nothing is sampled or downloaded.

    python make_bixby_roar.py               writes bixby_roar.wav and bixby_roar_short.wav
    python make_bixby_roar.py PREVIEW_DIR   also copies them there as preview_bixby_roar<_short>.wav

Three heads roar at once. Each is a voice source of sharp glottal pulses through its own throat resonances, rather
than a plain tone: pulses let each head be rough the way an animal is, through the length of every single period
(jitter), through dropping every other pulse (the subharmonic, which puts a growl an octave below the pitch) and
through breath noise that pulses along with the voice. The heads are detuned against each other and come in one
after another, so it reads as three throats instead of one big one.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from make_voices import (SR, PROJECT, samples, contour, noise, lowpass, highpass, bandpass, mul, mix, delayed,
                         normalized, saturate, write_wav)

SFX_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX")
PEAK_DBFS = -3.0


# ------------------------------------------------------------------------------------------------- building blocks

def at(length_ms, points):
    """Turns (fraction of the roar, value) points into the (ms, value) points contour() takes."""
    return [(fraction * length_ms, value) for fraction, value in points]


def wander(n, hz, rng):
    """A smooth random walk between -1 and 1, for the unsteadiness of a real animal's voice."""
    steps = max(2, int(n * hz / SR) + 2)
    points = [rng.uniform(-1.0, 1.0) for _ in range(steps)]
    out = []
    for i in range(n):
        p = i * (steps - 1) / max(1, n - 1)
        j = int(p)
        u = p - j
        a, b = points[j], points[min(steps - 1, j + 1)]
        out.append(a + (b - a) * (0.5 - 0.5 * math.cos(math.pi * u)))
    return out


def pulse_train(freqs, pulse_ms, jitter, subharmonic, rng):
    """The voice source: one sharp glottal pulse per period, rising faster than it falls.
    jitter varies each period's length and subharmonic quietens every other pulse."""
    n = len(freqs)
    width = max(4, samples(pulse_ms))
    shape = [0.5 - 0.5 * math.cos(2.0 * math.pi * (i / width) ** 0.62) for i in range(width)]
    out = [0.0] * n
    position = 0.0
    index = 0
    while position < n:
        start = int(position)
        gain = 1.0 - (subharmonic[start] if index % 2 else 0.0)
        for i in range(min(width, n - start)):
            out[start + i] += gain * shape[i]
        period = SR / freqs[start] * (1.0 + jitter[start] * rng.uniform(-1.0, 1.0))
        position += max(width, period)
        index += 1
    return out


def throat(x, resonances):
    """The head's vocal tract: a resonance per formant, mixed by weight."""
    return mix(*[(gain, bandpass(x, hz, q)) for hz, q, gain in resonances])


def growl(n, rate_points, depth_points):
    """The amplitude wobble that makes a growl sound like a growl, in the 25-45 Hz range."""
    rates = contour(n, rate_points)
    depths = contour(n, depth_points)
    out = []
    phase = 0.0
    for i in range(n):
        out.append(1.0 - depths[i] * 0.5 * (1.0 - math.cos(phase)))
        phase += 2.0 * math.pi * rates[i] / SR
    return out


def head(n, body_ms, entry, f0, pulse_ms, resonances, am_rate, am_depth, jitter, sub, breath, seed, vibrato=(0.0, 0.0)):
    """One head, silent until it joins in at `entry` (a fraction of the roar)."""
    rng = random.Random(seed)
    start = samples(entry * body_ms)
    length = n - start
    span = body_ms - entry * body_ms
    freqs = contour(length, at(span, f0))
    vibrato_hz, vibrato_depth = vibrato
    if vibrato_depth:
        swell = samples(0.25 * span)
        freqs = [f * (1.0 + vibrato_depth * min(1.0, i / swell) * math.sin(2.0 * math.pi * vibrato_hz * i / SR))
                 for i, f in enumerate(freqs)]

    source = pulse_train(freqs, pulse_ms, contour(length, at(span, jitter)), contour(length, at(span, sub)), rng)
    voice = throat(source, resonances)
    if breath:
        # Noise that pulses with the voice, which is what makes a throat sound torn rather than hissy.
        pulsing = lowpass([abs(s) for s in source], 400.0)
        voice = mix((1.0, voice), (breath, mul(bandpass(noise(length, rng), 1500, 0.7), [0.3 + 2.2 * p for p in pulsing])))
    return [0.0] * start + mul(voice, growl(length, at(span, am_rate), at(span, am_depth)))


def finish_roar(x, tail_taps):
    """Adds the cave tail, blocks DC, silences both ends and normalizes to PEAK_DBFS."""
    x = mix((1.0, x), *[(gain, lowpass(delayed(x, ms), hz)) for ms, gain, hz in tail_taps])
    x = highpass(x, 25.0)
    edge = samples(5.0)
    for i in range(edge):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    peak = max(abs(s) for s in x)
    return [s * 10.0 ** (PEAK_DBFS / 20.0) / peak for s in x]


# ------------------------------------------------------------------------------------------------- the roar

def build_roar(body_ms, shape_points, seed):
    """Growl into a rising howl, then a long ragged decay.

    The three heads bend up together through the howl and sag at the end. The low head carries the growl, the
    middle one the torn throat, and the high one the howl itself."""
    n = samples(body_ms)
    rng = random.Random(seed)

    low = head(n, body_ms, 0.0,
               f0=[(0.0, 62), (0.10, 72), (0.30, 88), (0.50, 92), (0.72, 78), (1.0, 58)],
               pulse_ms=1.1,
               resonances=[(88, 1.2, 0.9), (420, 4.0, 1.0), (950, 5.0, 0.5), (2300, 6.0, 0.18)],
               am_rate=[(0.0, 30), (0.5, 26), (1.0, 24)],
               am_depth=[(0.0, 0.75), (0.35, 0.4), (0.62, 0.5), (1.0, 0.8)],
               jitter=[(0.0, 0.02), (0.5, 0.025), (1.0, 0.06)],
               sub=[(0.0, 0.3), (0.4, 0.15), (1.0, 0.35)],
               breath=0.25, seed=seed + 1)

    middle = head(n, body_ms, 0.035,
                  f0=[(0.0, 165), (0.12, 190), (0.34, 240), (0.55, 252), (0.75, 205), (1.0, 150)],
                  pulse_ms=0.7,
                  resonances=[(225, 1.5, 0.55), (600, 4.0, 1.0), (1400, 5.0, 0.6), (2900, 6.0, 0.25)],
                  am_rate=[(0.0, 34), (0.6, 29), (1.0, 26)],
                  am_depth=[(0.0, 0.65), (0.4, 0.35), (1.0, 0.7)],
                  jitter=[(0.0, 0.035), (0.5, 0.04), (1.0, 0.075)],
                  sub=[(0.0, 0.2), (0.45, 0.1), (1.0, 0.3)],
                  breath=0.45, seed=seed + 2)

    high = head(n, body_ms, 0.08,
                f0=[(0.0, 700), (0.15, 840), (0.38, 1150), (0.58, 1210), (0.78, 980), (1.0, 720)],
                pulse_ms=0.35,
                resonances=[(1100, 6.0, 1.0), (2400, 7.0, 0.5), (3600, 8.0, 0.2)],
                am_rate=[(0.0, 38), (0.6, 31), (1.0, 28)],
                am_depth=[(0.0, 0.45), (0.45, 0.2), (1.0, 0.55)],
                jitter=[(0.0, 0.02), (0.5, 0.025), (1.0, 0.06)],
                sub=[(0.0, 0.1), (1.0, 0.25)],
                breath=0.3, seed=seed + 3, vibrato=(5.5, 0.015))

    # Chest rumble an octave under the low head, and the air being shifted: loudest at the first hit.
    rumble = contour(n, at(body_ms, [(0.0, 31), (0.30, 44), (0.50, 46), (0.72, 39), (1.0, 29)]))
    phase = 0.0
    chest = []
    for f in rumble:
        chest.append(math.sin(phase))
        phase += 2.0 * math.pi * f / SR
    air_env = contour(n, at(body_ms, [(0.0, 0.0), (0.012, 1.0), (0.12, 0.4), (0.45, 0.3), (0.78, 0.45), (1.0, 0.0)]))
    air = mul(highpass(bandpass(noise(n, rng), 1100, 0.45), 300.0), air_env)

    roar = mix((1.0, low), (0.85, middle), (0.55, high), (0.1, chest), (0.5, air))
    roar = saturate(normalized(roar), 1.5)

    # The howl's shape, roughened more and more as it falls apart at the end.
    shape = contour(n, at(body_ms, shape_points))
    ragged = wander(n, 9.0, rng)
    creeping = contour(n, at(body_ms, [(0.0, 0.0), (0.55, 0.0), (1.0, 1.0)]))
    return mul(roar, [s * (1.0 - 0.32 * grow * r) for s, grow, r in zip(shape, creeping, ragged)])


LONG = dict(
    body_ms=2050.0,
    shape_points=[(0.0, 0.0), (0.015, 0.82), (0.07, 0.72), (0.25, 0.88), (0.45, 1.0), (0.62, 0.94), (0.75, 0.74),
                  (0.88, 0.36), (1.0, 0.0)],
    tail_taps=[(150, 0.12, 2500), (270, 0.07, 1700), (430, 0.04, 1100), (620, 0.02, 700)],
    seed=70,
)
SHORT = dict(
    body_ms=880.0,
    shape_points=[(0.0, 0.0), (0.03, 0.95), (0.12, 0.85), (0.32, 1.0), (0.55, 0.85), (0.78, 0.45), (1.0, 0.0)],
    tail_taps=[(110, 0.1, 2200), (200, 0.05, 1400)],
    seed=91,
)


def envelope_report(name, x):
    frame = samples(25.0)
    levels = []
    for start in range(0, len(x) - frame, frame):
        window = x[start:start + frame]
        levels.append(20.0 * math.log10(math.sqrt(sum(s * s for s in window) / frame) + 1e-12))
    loudest = max(range(len(levels)), key=lambda i: levels[i])
    print("%-22s %.2f s  peak %.1f dBFS  loudest at %.2f s (%.1f dB)  per 100 ms: %s" % (
        name, len(x) / SR, 20.0 * math.log10(max(abs(s) for s in x)), loudest * frame / SR, levels[loudest],
        " ".join("%.0f" % level for level in levels[::4])))


def main():
    os.makedirs(SFX_DIR, exist_ok=True)
    for name, settings in (("bixby_roar", LONG), ("bixby_roar_short", SHORT)):
        body = build_roar(settings["body_ms"], settings["shape_points"], settings["seed"])
        sound = finish_roar(body, settings["tail_taps"])
        write_wav(os.path.join(SFX_DIR, "%s.wav" % name), sound)
        envelope_report("%s.wav" % name, sound)
        if len(sys.argv) > 1:
            os.makedirs(sys.argv[1], exist_ok=True)
            write_wav(os.path.join(sys.argv[1], "preview_%s.wav" % name), sound)


if __name__ == "__main__":
    main()
