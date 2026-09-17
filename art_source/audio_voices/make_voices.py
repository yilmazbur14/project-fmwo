"""Synthesizes every character's dialogue talk blip into Assets/Audio/SFX/Voices, as 16-bit mono 44.1 kHz WAVs.

Pure Python (wave, struct, math, random) with fixed seeds, so every run writes identical files. Nothing is sampled
or downloaded.

    python make_voices.py               writes voice_<name>_<n>.wav for every voice
    python make_voices.py PREVIEW_DIR   also writes preview_<name>.wav per voice and all_voices_preview.wav

A preview is a couple of seconds of one of the character's real lines, typed the way DialogueLabel types it and
voiced the way Scripts/balloon.gd voices it, with the table in Scripts/DialogueVoices.gd, so it sounds like the game.

Every variant is loudness-matched to TARGET_DB (B-weighted, over its loudest 80 ms), so a voice's volume_db in the
table is the only thing setting how loud it plays.
"""

import math
import os
import random
import re
import struct
import sys
import wave

SR = 44100
TARGET_DB = -22.0
LOUDNESS_WINDOW_MS = 80

PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
VOICE_DIR = os.path.join(PROJECT, "Assets", "Audio", "SFX", "Voices")
TABLE = os.path.join(PROJECT, "Scripts", "DialogueVoices.gd")


# ------------------------------------------------------------------------------------------------- building blocks

def samples(ms):
    return int(round(ms * SR / 1000.0))


def contour(n, points):
    """n values easing (cosine) through (ms, value) points, holding the last value."""
    out = []
    seg = 0
    for i in range(n):
        t = i * 1000.0 / SR
        while seg < len(points) - 2 and t > points[seg + 1][0]:
            seg += 1
        (t0, v0), (t1, v1) = points[seg], points[seg + 1]
        u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
        out.append(v0 + (v1 - v0) * (0.5 - 0.5 * math.cos(math.pi * u)))
    return out


def oscillator(freqs, partials, phase=0.0):
    """Additive oscillator following a per-sample frequency. partials: (harmonic, amplitude[, phase offset]).
    Partials above 15 kHz are left out, so nothing aliases."""
    parts = [(p[0], p[1], p[2] if len(p) > 2 else 0.0) for p in partials]
    out = []
    for f in freqs:
        s = 0.0
        for k, amp, offset in parts:
            if k * f < 15000.0:
                s += amp * math.sin(k * phase + offset)
        out.append(s)
        phase += 2.0 * math.pi * f / SR
    return out


def triangle(top):
    return [(k, (-1) ** ((k - 1) // 2) / (k * k)) for k in range(1, top + 1, 2)]


def square(top, rolloff=1.0):
    """Odd harmonics. A rolloff above 1 softens the square toward a hollow, clarinet-like tone."""
    return [(k, 1.0 / k ** rolloff) for k in range(1, top + 1, 2)]


def pulse(duty, top):
    return [(k, 2.0 * math.sin(math.pi * k * duty) / k, math.pi / 2 - math.pi * k * duty) for k in range(1, top + 1)]


def envelope(n, attack_ms, release_ms, decay_ms=None):
    """Raised-cosine attack and release around an optional exponential decay. Starts and ends at exactly 0."""
    attack, release = max(1, samples(attack_ms)), max(1, samples(release_ms))
    tau = samples(decay_ms) if decay_ms else None
    out = []
    for i in range(n):
        g = math.exp(-i / tau) if tau else 1.0
        if i < attack:
            g *= 0.5 - 0.5 * math.cos(math.pi * i / attack)
        if n - 1 - i < release:
            g *= 0.5 - 0.5 * math.cos(math.pi * (n - 1 - i) / release)
        out.append(g)
    return out


def noise(n, rng):
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def lowpass(x, hz):
    a = 1.0 - math.exp(-2.0 * math.pi * hz / SR)
    y, out = 0.0, []
    for s in x:
        y += a * (s - y)
        out.append(y)
    return out


def highpass(x, hz):
    return [s - low for s, low in zip(x, lowpass(x, hz))]


def bandpass(x, hz, q):
    w = 2.0 * math.pi * hz / SR
    alpha = math.sin(w) / (2.0 * q)
    a0 = 1.0 + alpha
    b0, b2, a1, a2 = alpha / a0, -alpha / a0, -2.0 * math.cos(w) / a0, (1.0 - alpha) / a0
    x1 = x2 = y1 = y2 = 0.0
    out = []
    for s in x:
        y = b0 * s + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y)
    return out


def mul(a, b):
    return [x * y for x, y in zip(a, b)]


def mix(*layers):
    """Sums (gain, signal) layers into a signal as long as the longest."""
    out = [0.0] * max(len(signal) for _, signal in layers)
    for gain, signal in layers:
        for i, s in enumerate(signal):
            out[i] += gain * s
    return out


def delayed(x, ms):
    return [0.0] * samples(ms) + x


def normalized(x):
    peak = max(abs(s) for s in x) or 1.0
    return [s / peak for s in x]


def saturate(x, drive):
    k = math.tanh(drive)
    return [math.tanh(drive * s) / k for s in x]


def crush(x, bits, hold):
    """Rounds to 2**bits levels and holds each value for `hold` samples."""
    step = 2.0 / 2 ** bits
    out, held = [], 0.0
    for i, s in enumerate(x):
        if i % hold == 0:
            held = round(s / step) * step
        out.append(held)
    return out


def b_weighted(x):
    """B-weighting (0 dB at 1 kHz, -4 dB at 125 Hz): how loud a moderate-level sound seems across pitches, so the deep
    voices aren't matched as if their lows were as audible as the beeps' mids."""
    for hz, kind in ((20.6, "hp"), (20.6, "hp"), (158.5, "hp"), (12194.0, "lp"), (12194.0, "lp")):
        k = math.tan(math.pi * hz / SR)
        a1 = (k - 1.0) / (k + 1.0)
        b0, b1 = (1.0 / (1.0 + k), -1.0 / (1.0 + k)) if kind == "hp" else (k / (1.0 + k), k / (1.0 + k))
        out, x1, y1 = [], 0.0, 0.0
        for s in x:
            y1 = b0 * s + b1 * x1 - a1 * y1
            x1 = s
            out.append(y1)
        x = out
    return x


def loudness_db(x, window_ms=LOUDNESS_WINDOW_MS):
    """Mean square of the loudest window, B-weighted, in dB. A blip shorter than the window counts all its energy,
    which is roughly how the ear sums very short sounds."""
    n = samples(window_ms)
    w = b_weighted(x + [0.0] * n)
    total = sum(s * s for s in w[:n])
    best = total
    for i in range(n, len(w)):
        total += w[i] * w[i] - w[i - n] * w[i - n]
        best = max(best, total)
    return 10.0 * math.log10(best / n + 1e-20)


def finish(x):
    """DC-blocks, makes sure both ends are silent, and matches the loudness to TARGET_DB."""
    x = highpass(x, 30.0)
    edge = samples(1.5)
    for i in range(edge):
        g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
        x[i] *= g
        x[-1 - i] *= g
    gain = 10.0 ** ((TARGET_DB - loudness_db(x)) / 20.0)
    return [s * gain for s in x]


def write_wav(path, x):
    ints = [max(-32768, min(32767, int(round(s * 32767.0)))) for s in x]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(struct.pack("<%dh" % len(ints), *ints))


def read_wav(path):
    with wave.open(path, "rb") as w:
        raw = w.readframes(w.getnframes())
    return [v / 32767.0 for v in struct.unpack("<%dh" % (len(raw) // 2), raw)]


# ------------------------------------------------------------------------------------------------- voices
# Each returns its variants. Scripts/DialogueVoices.gd adds each blip's random pitch, the melody, how often a voice
# blips and how loud it plays.

def voice_burak():
    """The main character: a clean, friendly sine-triangle "bup" at ~490 Hz. A soft attack, few overtones and a small
    fall in pitch like the end of a spoken syllable, so it's the least tiring voice to hear over and over."""
    variants = []
    for f0, shape in ((488, [(0, 1.01), (46, 0.975)]),
                      (500, [(0, 0.99), (14, 1.005), (46, 0.985)]),
                      (476, [(0, 1.0), (22, 1.012), (46, 0.98)])):
        n = samples(46)
        tone = oscillator([f0 * m for m in contour(n, shape)], [(1, 1.0), (2, 0.07), (3, -0.05), (5, 0.012)])
        variants.append(mul(lowpass(tone, 4000), envelope(n, 5, 16, decay_ms=38)))
    return variants


def voice_eric():
    """Deep and warm with a little grit: a triangle with a touch of saw overtones at ~170 Hz, gently saturated, with
    an "uh" resonance around 620 Hz and rolled off above 3 kHz. It starts a shade sharp and settles downward, like a
    heavy, self-important voice. The resonance carries it on small speakers that can't play 170 Hz."""
    variants = []
    partials = [(k, 0.85 * a) for k, a in triangle(31)] + [(k, 0.4 / k, math.pi / 2) for k in range(2, 41)]
    for f0, fall in ((170, 0.975), (163, 0.97), (177, 0.98)):
        n = samples(66)
        tone = oscillator([f0 * m for m in contour(n, [(0, 1.035), (12, 1.0), (66, fall)])], partials)
        tone = saturate(normalized(tone), 2.2)
        tone = lowpass(lowpass(mix((1.0, tone), (1.5, bandpass(tone, 620, 1.3))), 2800), 5500)
        variants.append(mul(tone, envelope(n, 6, 22, decay_ms=70)))
    return variants


def voice_computah():
    """Robotic terminal beeps: flat-gated square waves on a fixed set of pitches (B5, D6, E6, A6), lightly
    bitcrushed. Variants 1-4 are single beeps and 5 is a two-tone chirp, so about one blip in five chirps. The table
    gives Computah no random pitch, so every beep stays on that set."""
    def beep(freqs):
        tone = crush(normalized(oscillator(freqs, square(15, rolloff=1.15))), bits=5, hold=3)
        return mul(lowpass(tone, 7000), envelope(len(freqs), 2, 5))
    half = samples(18)
    return [beep([f] * samples(34)) for f in (988, 1175, 1319, 1760)] + [beep([1760] * half + [1319] * half)]


def voice_carter():
    """Deadpan and unimpressed: a soft, round, low-mid "bup" at 220 Hz that never moves in pitch."""
    variants = []
    for second, third in ((0.45, 0.16), (0.4, 0.2)):
        n = samples(48)
        tone = oscillator([220.0] * n, [(1, 1.0), (2, second), (3, third), (4, 0.03)])
        variants.append(mul(lowpass(tone, 1800), envelope(n, 6, 18, decay_ms=55)))
    return variants


def voice_josh():
    """Flashy show-off: a bright, bouncy chirp at ~720 Hz that flicks up past its note and bounces back."""
    variants = []
    for f0, start in ((720, 0.86), (690, 0.9), (760, 0.84)):
        n = samples(40)
        freqs = [f0 * m for m in contour(n, [(0, start), (14, 1.06), (24, 1.015), (40, 1.03)])]
        tone = oscillator(freqs, [(1, 1.0), (2, 0.38), (3, 0.2), (4, 0.12), (5, 0.06), (6, 0.03)])
        variants.append(mul(lowpass(tone, 6000), envelope(n, 3, 12, decay_ms=45)))
    return variants


def voice_liam():
    """Smug and anime-like, a sing-song "hm~": a soft hum at ~620 Hz behind a breathy "h", scooping upward and
    wobbling as it ends. The table's melody walks it between this note and a minor third below, the interval of a
    playground "nyah-nyah"."""
    variants = []
    for f0, rise, wobble, seed in ((620, 1.05, 0.0, 31), (610, 1.04, 2.1, 32), (632, 1.06, 4.2, 33)):
        rng = random.Random(seed)
        n = samples(76)
        freqs = []
        for i, m in enumerate(contour(n, [(0, 0.965), (42, rise), (76, rise)])):
            t = i / SR
            depth = 0.018 * min(1.0, max(0.0, (t - 0.025) / 0.02))
            freqs.append(f0 * m * (1.0 + depth * math.sin(2.0 * math.pi * 11.0 * t + wobble)))
        hum = mul(oscillator(freqs, [(1, 1.0), (2, 0.16), (3, 0.08), (4, 0.02)]), envelope(n, 10, 24, decay_ms=150))
        breath = mul(bandpass(noise(n, rng), 1800, 1.2), envelope(n, 2, 30, decay_ms=9))
        variants.append(mix((1.0, hum), (0.35, breath)))
    return variants


def voice_jordan():
    """The final boss, slightly scary: two tones ~120 Hz and 35-40 cents apart, so they waver sourly, through a dark
    "oh" resonance, with a raspy breath pulsing along with them. A slow swell, a long decay drifting flat, and a
    faint, darker echo."""
    variants = []
    partials = [(k, 0.8 * a) for k, a in triangle(25)] + [(k, 0.42 / k, math.pi / 2) for k in range(2, 30)]
    for f0, cents, seed in ((120, 38, 41), (116, 42, 42), (125, 34, 43)):
        rng = random.Random(seed)
        n = samples(150)
        drift = contour(n, [(0, 1.0), (150, 0.965)])
        low = oscillator([f0 * d for d in drift], partials)
        high = oscillator([f0 * 2.0 ** (cents / 1200.0) * d for d in drift], partials, phase=1.3)
        tones = lowpass(lowpass(mix((0.5, low), (0.5, high)), 2000), 3500)
        tones = normalized(mix((1.0, tones), (1.0, bandpass(tones, 480, 1.2))))
        rasp = [b * (0.65 + 0.35 * t) for b, t in zip(bandpass(noise(n, rng), 800, 0.8), tones)]
        body = mul(mix((1.0, tones), (0.75, rasp)), envelope(n, 20, 45, decay_ms=110))

        def echo(ms, hz):
            return lowpass(delayed(body, ms) + [0.0] * samples(10), hz)

        variants.append(mix((1.0, body), (0.3, echo(85, 1200)), (0.12, echo(170, 800))))
    return variants


def voice_mason():
    """Goofy guy in a chicken suit: a bouncy "bawk", a round tone at ~400 Hz that drops fast into its note from well
    above, ending in a soft "k"."""
    variants = []
    for f0, start, seed in ((400, 1.55, 51), (380, 1.45, 52), (430, 1.6, 53)):
        rng = random.Random(seed)
        n = samples(52)
        freqs = [f0 * m for m in contour(n, [(0, start), (13, 1.0), (52, 0.93)])]
        tone = oscillator(freqs, [(1, 1.0), (2, 0.42), (3, 0.22), (4, 0.08)])
        tone = mul(lowpass(tone, 3500), envelope(n, 2.5, 14, decay_ms=42))
        k = mul(bandpass(noise(samples(6), rng), 2800, 1.5), envelope(samples(6), 1, 4))
        variants.append(mix((1.0, tone), (0.35, delayed(k, 42))))
    return variants


def voice_greyson():
    """The pilot and gamer: a short, slightly nasal pulse at ~470 Hz with a boosted 1.4 kHz "nose" resonance."""
    variants = []
    for f0, shape in ((470, [(0, 0.98), (10, 1.01), (38, 0.985)]),
                      (488, [(0, 1.0), (38, 0.97)]),
                      (455, [(0, 0.99), (20, 1.015), (38, 1.0)])):
        n = samples(38)
        buzz = oscillator([f0 * m for m in contour(n, shape)], pulse(0.22, 24))
        nasal = mix((0.5, buzz), (1.0, bandpass(buzz, 1400, 2.0)))
        variants.append(mul(lowpass(nasal, 4200), envelope(n, 3, 10, decay_ms=40)))
    return variants


def voice_danny():
    """The intro guide: a warm, mid-range triangle "bop" at ~330 Hz that falls a little."""
    variants = []
    for f0, fall in ((330, 0.965), (318, 0.97), (345, 0.96)):
        n = samples(52)
        tone = oscillator([f0 * m for m in contour(n, [(0, 1.01), (52, fall)])], triangle(15) + [(2, 0.09, math.pi / 2)])
        variants.append(mul(lowpass(tone, 3000), envelope(n, 5, 16, decay_ms=50)))
    return variants


def voice_bixby():
    """The dog: a short "arf", a tiny noise burst into a round tone that bumps up and drops low (~450 to ~250 Hz)."""
    variants = []
    for f_hi, f_lo, seed in ((440, 250, 61), (480, 272, 62), (410, 236, 63)):
        rng = random.Random(seed)
        n = samples(64)
        freqs = contour(n, [(0, f_hi), (10, f_hi * 1.06), (64, f_lo)])
        tone = mul(lowpass(oscillator(freqs, [(1, 1.0), (2, 0.35), (3, 0.12)]), 2500), envelope(n, 4, 16, decay_ms=38))
        burst = mul(bandpass(noise(n, rng), 1600, 1.1), envelope(n, 1.5, 40, decay_ms=6))
        variants.append(mix((1.0, tone), (0.6, burst)))
    return variants


def voice_neutral():
    """Nathan (Dialogue Manager's example speaker) and anyone else without a voice of their own: a plain, hollow,
    level "doo" at ~390 Hz, unlike Burak's rounder, moving blip."""
    variants = []
    for f0 in (392, 381, 403):
        n = samples(44)
        tone = oscillator([f0] * n, square(11, rolloff=1.6))
        variants.append(mul(lowpass(tone, 2200), envelope(n, 4, 14, decay_ms=60)))
    return variants


VOICES = {
    "burak": voice_burak,
    "eric": voice_eric,
    "computah": voice_computah,
    "carter": voice_carter,
    "josh": voice_josh,
    "liam": voice_liam,
    "jordan": voice_jordan,
    "mason": voice_mason,
    "greyson": voice_greyson,
    "danny": voice_danny,
    "bixby": voice_bixby,
    "neutral": voice_neutral,
}


# ------------------------------------------------------------------------------------------------- previews

PREVIEW_LINES = [
    ("burak", "Burak", "(Another server ghosted me... nobody wants a newcomer.)"),
    ("eric", "Eric", "Ha! The server stays pure for another day. Log off, and don't come back."),
    ("computah", "Computah", "Target neutralised. Bzzzt. Shall I remove another heart, sir?"),
    ("carter", "Carter", "Just don't run into me like Tulsa again. Born ready. Let's dance."),
    ("josh", "Josh", "Alright Carter, this one's got fresh legs. Let's give him the full show."),
    ("liam", "Liam", "Well, well! Welcome to my arena, newcomer. Nobody gets this far by accident."),
    ("jordan", "Jordan", "So you're the newcomer everyone keeps pinging me about. I run this server."),
    ("mason", "Mason", "Hold on, my Uber Eats is almost here. Now if you'll excuse me, my food's getting cold."),
    ("greyson", "Greyson", "Get UP, Computah! I skipped the gym for this! Look at his face, Computah!"),
    ("danny", "Danny", "I'm only gonna explain this once, I need to get back to my Tarky raid."),
    ("bixby", "Bixby", "Grrrrrrr... *GULP*"),
    ("nathan", "Nathan", "Hi, this is some dialogue. For more information see the online documentation."),
]
PREVIEW_GAP_MS = 600

# DialogueLabel's defaults, which the balloon doesn't change, typed at a 60 fps frame rate.
SECONDS_PER_STEP = 0.02
SECONDS_PER_PAUSE = 0.3
FPS = 60
# Godot starts a sound at its next mix step, and fades out a sound that's cut off over one step.
MIX_STEP = 512


def read_table():
    """MIN_BLIP_GAP_MS, NEUTRAL_VOICE and VOICES from Scripts/DialogueVoices.gd, with each stream as a file path."""
    with open(TABLE, encoding="utf-8") as f:
        text = f.read()
    gap = int(re.search(r"const MIN_BLIP_GAP_MS := (\d+)", text).group(1))
    neutral = re.search(r'const NEUTRAL_VOICE := "(\w+)"', text).group(1)
    voices = {}
    for name, body in re.findall(r'^\t"(\w+)": \{\n(.*?)^\t\},?$', text, re.M | re.S):
        def number(key):
            return float(re.search(r'"%s": (-?[\d.]+)' % key, body).group(1))
        voices[name] = {
            "streams": [os.path.join(PROJECT, *p[len("res://"):].split("/"))
                        for p in re.findall(r'preload\("(res://[^"]+)"\)', body)],
            "pitch_min": number("pitch_min"),
            "pitch_max": number("pitch_max"),
            "melody": [float(v) for v in re.search(r'"melody": \[([^\]]*)\]', body).group(1).split(",")],
            "every": int(number("every")),
            "volume_db": number("volume_db"),
        }
    return gap, neutral, voices


def typed_letters(text):
    """(seconds, letter) for each letter as DialogueLabel types it at 60 fps, pausing after . ? and !"""
    delta = 1.0 / FPS
    letters = []
    visible, waiting, last_wait_index = 0, 0.0, -1

    def should_pause():
        if visible == 0 or visible >= len(text) or text[visible] in ')"':
            return False
        if visible > 3 and text[visible - 1] == "." and re.fullmatch(r"\d\.\d", text[visible - 2:visible + 1]):
            return False
        if text[visible - 1] == ".":
            for abbreviation in ("Mr", "Mrs", "Ms", "Dr", "etc", "eg", "ex"):
                start = visible - len(abbreviation) - 1
                if start >= 0 and text[start:visible - 1] == abbreviation:
                    return False
        if visible > 1 and text[visible - 1] in "?!" and text[visible] in "?!":
            return False
        return text[visible - 1] in ".?!"

    # type_out() waits a frame before the first letter.
    frame = 1
    while visible < len(text):
        frame += 1
        if waiting > 0:
            waiting -= delta
        if waiting <= 0:
            needed = waiting
            while visible < len(text):
                if last_wait_index != visible and should_pause():
                    last_wait_index = visible
                    waiting += SECONDS_PER_PAUSE
                    break
                visible += 1
                letters.append((frame * delta, text[visible - 1]))
                needed += SECONDS_PER_STEP
                if needed > delta:
                    waiting += needed
                    break
    return letters


def voiced_blips(letters, voice, gap_ms, rng):
    """(seconds, stream, pitch_scale) for each blip, picked the way balloon.gd picks them."""
    blips = []
    letters_since_blip, last_blip_ms, step, last_stream = voice["every"], None, 0, None
    for seconds, letter in letters:
        if not re.match(r"[^\W_]", letter):
            continue
        ms = int(seconds * 1000)
        if letters_since_blip >= voice["every"] and (last_blip_ms is None or ms - last_blip_ms >= gap_ms):
            fresh = [s for s in voice["streams"] if s != last_stream]
            last_stream = rng.choice(fresh or voice["streams"])
            melody = voice["melody"]
            pitch = rng.uniform(voice["pitch_min"], voice["pitch_max"]) * melody[step % len(melody)]
            blips.append((seconds, last_stream, pitch))
            step += 1
            letters_since_blip, last_blip_ms = 0, ms
        letters_since_blip += 1
    return blips


def resampled(x, pitch):
    out = []
    for i in range(int(len(x) / pitch)):
        p = i * pitch
        j = int(p)
        nxt = x[j + 1] if j + 1 < len(x) else 0.0
        out.append(x[j] + (nxt - x[j]) * (p - j))
    return out


def render(blips, volume_db, sounds):
    """Mixes the blips through two players like balloon.gd: a free one if there is one, otherwise the one that started
    first, which gets cut off. Returns the audio and how many blips were cut off."""
    gain = 10.0 ** (volume_db / 20.0)
    players = [{"playback": None}, {"playback": None}]
    playbacks, cut_offs = [], 0
    for seconds, stream, pitch in blips:
        start = int(math.ceil(seconds * SR / MIX_STEP)) * MIX_STEP
        player = players[0]
        for candidate in players:
            playback = candidate["playback"]
            if playback is None or playback["start"] + len(playback["data"]) <= start:
                player = candidate
                break
        playback = player["playback"]
        if playback is not None and playback["start"] + len(playback["data"]) > start:
            playback["cut"] = start
            cut_offs += 1
        players.remove(player)
        players.append(player)
        player["playback"] = {"start": start, "data": resampled(sounds[stream], pitch), "cut": None}
        playbacks.append(player["playback"])

    out = [0.0] * (max(p["start"] + len(p["data"]) for p in playbacks) + samples(200))
    for playback in playbacks:
        for i, s in enumerate(playback["data"]):
            pos = playback["start"] + i
            if playback["cut"] is not None and pos >= playback["cut"]:
                fade = 1.0 - (pos - playback["cut"]) / MIX_STEP
                if fade <= 0.0:
                    break
                s *= fade
            out[pos] += gain * s
    return out, cut_offs


def write_previews(folder):
    os.makedirs(folder, exist_ok=True)
    gap_ms, neutral, table = read_table()
    sounds = {}
    everything = []
    for key, speaker, text in PREVIEW_LINES:
        voice = table.get(speaker.lower(), table[neutral])
        for path in voice["streams"]:
            if path not in sounds:
                sounds[path] = read_wav(path)
        letters = typed_letters(text)
        blips = voiced_blips(letters, voice, gap_ms, random.Random(key))
        audio, cut_offs = render(blips, voice["volume_db"], sounds)
        write_wav(os.path.join(folder, "preview_%s.wav" % key), audio)
        everything += audio + [0.0] * samples(PREVIEW_GAP_MS)

        gaps = sorted(round((b[0] - a[0]) * 1000) for a, b in zip(blips, blips[1:]) if b[0] - a[0] < 0.25)
        weighted = b_weighted(audio)
        window, hop = samples(400), samples(50)
        levels = sorted(10.0 * math.log10(sum(s * s for s in weighted[i:i + window]) / window + 1e-20)
                        for i in range(0, len(weighted) - window, hop))
        print("preview_%-9s %4.2fs  %2d blips  %3s ms between blips while typing  %d cut off  %5.1f dB talking"
              "  peak %5.1f dBFS" % (key, len(audio) / SR, len(blips), gaps[len(gaps) // 2] if gaps else "-", cut_offs,
                                    levels[len(levels) * 3 // 4], 20.0 * math.log10(max(abs(s) for s in audio))))
    write_wav(os.path.join(folder, "all_voices_preview.wav"), everything)


def main():
    os.makedirs(VOICE_DIR, exist_ok=True)
    for name, make in VOICES.items():
        for number, variant in enumerate(make(), 1):
            sound = finish(variant)
            write_wav(os.path.join(VOICE_DIR, "voice_%s_%d.wav" % (name, number)), sound)
            print("voice_%s_%d.wav  %3d ms  peak %5.1f dBFS  loudness %5.1f dB" % (
                name, number, round(len(sound) * 1000 / SR), 20.0 * math.log10(max(abs(s) for s in sound)),
                loudness_db(sound)))
    if len(sys.argv) > 1:
        write_previews(sys.argv[1])


if __name__ == "__main__":
    main()
