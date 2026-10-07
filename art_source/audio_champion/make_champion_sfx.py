"""Synthesizes the champion ending's crowd sounds (ChampionEndingLayout.SOUNDS), as 16-bit mono 44.1 kHz WAVs.

Pure Python with fixed seeds, on Greyson's crowd (make_greyson_sfx.py: its voices, applause, whistles and crowd bed)
and the project's own building blocks under it, so every run writes identical files. Nothing is sampled or downloaded.

    python make_champion_sfx.py PREVIEW_DIR   writes preview_<name>.wav for every sound into PREVIEW_DIR and prints the
                                              level table and each loop's seam check
    python make_champion_sfx.py --ship        writes <name>.wav into Assets/Audio/SFX - never over a file already there -
                                              and records each new file's sha256 in shipped.json beside this script

Run with no argument, it only says how to use it: it never writes into the shipped folder unless asked to.

THE LEVELS ARE THE STAND-INS'. Each sound replaces a stand-in the ending plays until it is imported (the layout's
SOUNDS: crowd_cheer.wav pitched and layered, burak_blast.wav pitched up), and the layout's later levels - the hush, the
gather, the name - are set against the sound's own volume_db. So each file is scaled to play, at its volume_db, exactly
as loud as its stand-in plays at its own level: B-weighted mean square over a whole cycle for the loops, over the
loudest second for the roar, and over the loudest 80 ms for the pop (make_voices.loudness_db). A peak that would pass
PEAK_CAP is held there, and the table says by how much it falls short. The two loops are seamless: everything in them
is laid round the cycle, wrapping past its end, and filtered over two cycles with the second one kept; each file gets
one guard frame and a smpl loop over the rest (dsp.godot_native).
"""

import hashlib
import json
import math
import os
import random
import struct
import sys
import wave

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
sys.path.insert(0, os.path.join(ART, "audio_greyson"))

import make_greyson_sfx as G  # noqa: E402
from make_greyson_sfx import (SR, samples, contour, noise, mix, normalized, lp, hp, resonator, bandpass, tone,  # noqa
                              decay, place, apply, shape, echoes, wav_bytes, godot_resample, loudness_db,
                              crowd_voice, crowd_bed, whistle, CHEER_VOWELS, AH, EH, OH, OO, NN, EE)
from make_voices import b_weighted  # noqa: E402

SFX_DIR = os.path.join(PROJECT_DIR, "Assets", "Audio", "SFX")
SHIPPED = os.path.join(HERE, "shipped.json")
PEAK_CAP = -1.0
LOOP_MS = 6000.0
ROAR_MS = 5500.0
POP_MS = 1100.0
# The arena thrown back at the crowd: (delay ms, gain, low-pass Hz).
ARENA = [(83.0, 0.24, 3000.0), (167.0, 0.17, 2400.0), (263.0, 0.11, 1800.0), (397.0, 0.07, 1300.0),
         (577.0, 0.04, 900.0)]


# ------------------------------------------------------------------------------------------------- loops

def wrap(n, x):
    """A sound laid round a cycle of n samples: what runs past the end comes in again at the start."""
    out = [0.0] * n
    for i, s in enumerate(x):
        out[i % n] += s
    return out


def place_round(out, x, at_ms, gain=1.0):
    n = len(out)
    start = samples(at_ms)
    for i, s in enumerate(x):
        out[(start + i) % n] += gain * s


def cyclic(n, process):
    """`process` run over two cycles and the second kept, so its filters and echoes carry round the seam."""
    def run(x):
        return process(x + x)[n:]
    return run


def loop_bed(n, rng, low_hz, high_hz):
    """Greyson's crowd bed, held level, made into a loop by crossfading what runs past the end into the start."""
    fade = samples(400.0)
    bed = crowd_bed(n + fade, rng, low_hz, high_hz, [(0, 1.0), ((n + fade) * 1000.0 / SR, 1.0)])
    out = bed[:n]
    for i in range(fade):
        w = i / fade
        out[i] = out[i] * math.sqrt(w) + bed[n + i] * math.sqrt(1.0 - w)
    return out


def loop_claps(n, rng, clappers, level_points):
    """Applause all round the cycle, each clapper at a steady rate of their own."""
    out = [0.0] * n
    for _ in range(clappers):
        rate = rng.uniform(4.0, 7.0)
        hz = rng.uniform(900.0, 2600.0)
        level = rng.uniform(0.4, 1.0)
        start = rng.uniform(0.0, LOOP_MS)
        t = start
        while t < start + LOOP_MS:
            k = samples(18.0)
            clap = resonator(apply(noise(k, rng), decay(k, 12.0, 0.2)), hz, 2.0)
            place_round(out, clap, t, level * rng.uniform(0.7, 1.0))
            t += 1000.0 / rate * rng.uniform(0.9, 1.1)
    return apply(out, shape(n, level_points))


def crowd_loop():
    """The crowd up and staying up, for the hold after the drop and under the name: four dozen voices yelling "yeah",
    "woo" and "hey" at their own pitches and moments all round the cycle, steady applause, a few whistles, the roar of
    the rest behind, and the arena throwing it back."""
    rng = random.Random(4100)
    n = samples(LOOP_MS)
    voices = [0.0] * n
    for v in range(54):
        female = rng.random() < 0.35
        f0 = rng.uniform(185.0, 290.0) if female else rng.uniform(105.0, 175.0)
        scale = rng.uniform(1.1, 1.22) if female else rng.uniform(0.92, 1.05)
        length = rng.uniform(900.0, 2200.0)
        rise = rng.uniform(1.05, 1.2)
        one = [0.0] * samples(length + 20.0)
        crowd_voice(one, rng, 0.0, length, f0, [(0.0, 0.94), (0.3, rise), (0.8, rise * 0.97), (1.0, rise * 0.9)],
                    CHEER_VOWELS[v % len(CHEER_VOWELS)], scale, rng.uniform(0.5, 1.0))
        place_round(voices, one, rng.uniform(0.0, LOOP_MS))
    applause = loop_claps(n, rng, 30, [(0, 1.0), (LOOP_MS, 1.0)])
    whistles = [0.0] * n
    for at, length, hz, glide, level in ((800.0, 600.0, 2700.0, 1.1, 0.6), (2900.0, 520.0, 3000.0, 1.08, 0.5),
                                         (4700.0, 580.0, 2450.0, 1.14, 0.55)):
        place_round(whistles, whistle(samples(length + 20.0), rng, 0.0, length, hz, glide, level), at)
    bed = loop_bed(n, rng, 350.0, 2600.0)
    x = mix((1.0, normalized(voices)), (0.32, normalized(applause)), (0.14, whistles), (0.55, normalized(bed)))
    return cyclic(n, lambda y: hp(lp(echoes(y, ARENA), 10000.0), 90.0))(x)


MURMUR_VOWELS = [[(0.0, NN), (0.3, AH), (1.0, AH)], [(0.0, EH), (1.0, EE)], [(0.0, OH), (1.0, OO)],
                 [(0.0, AH), (0.6, EH), (1.0, NN)], [(0.0, NN), (1.0, OH)]]


def murmur_loop():
    """The crowd waiting, before the drop: talk rather than shouting - short syllables at speaking pitch from three
    dozen people all round the arena, under a low, steady roar of the rest, and the arena's reverb."""
    rng = random.Random(4200)
    n = samples(LOOP_MS)
    voices = [0.0] * n
    for v in range(120):
        female = rng.random() < 0.4
        f0 = rng.uniform(175.0, 240.0) if female else rng.uniform(95.0, 145.0)
        scale = rng.uniform(1.08, 1.2) if female else rng.uniform(0.92, 1.04)
        length = rng.uniform(180.0, 520.0)
        lilt = rng.uniform(0.92, 1.08)
        one = [0.0] * samples(length + 20.0)
        crowd_voice(one, rng, 0.0, length, f0, [(0.0, 1.0), (0.5, lilt), (1.0, 0.95)],
                    MURMUR_VOWELS[v % len(MURMUR_VOWELS)], scale, rng.uniform(0.3, 1.0), jitter=0.02)
        place_round(voices, one, rng.uniform(0.0, LOOP_MS))
    bed = loop_bed(n, rng, 160.0, 1200.0)
    x = mix((1.0, normalized(voices)), (0.7, normalized(bed)))
    return cyclic(n, lambda y: hp(lp(echoes(y, ARENA), 6500.0), 80.0))(x)


# ------------------------------------------------------------------------------------------------- one-shots

def roar():
    """The crowd erupting on the drop, and bigger on the name: seventy voices all going up at once, a second wave
    joining them, applause and whistles, the whole arena's roar under it swelling in a beat and slowly falling away,
    thrown back off the roof."""
    rng = random.Random(4300)
    n = samples(ROAR_MS)
    voices = [0.0] * n
    for v in range(70):
        female = rng.random() < 0.35
        f0 = rng.uniform(190.0, 300.0) if female else rng.uniform(110.0, 180.0)
        scale = rng.uniform(1.1, 1.22) if female else rng.uniform(0.92, 1.05)
        length = rng.uniform(1600.0, 3400.0)
        rise = rng.uniform(1.1, 1.25)
        crowd_voice(voices, rng, rng.uniform(0.0, 300.0), length, f0,
                    [(0.0, 0.95), (0.15, rise), (0.7, rise * 0.97), (1.0, rise * 0.85)],
                    CHEER_VOWELS[v % len(CHEER_VOWELS)], scale, rng.uniform(0.55, 1.0))
    for v in range(22):
        female = rng.random() < 0.35
        f0 = rng.uniform(190.0, 300.0) if female else rng.uniform(110.0, 180.0)
        scale = rng.uniform(1.1, 1.22) if female else rng.uniform(0.92, 1.05)
        crowd_voice(voices, rng, rng.uniform(1100.0, 2300.0), rng.uniform(1200.0, 2200.0), f0,
                    [(0.0, 0.95), (0.3, 1.15), (1.0, 1.0)], CHEER_VOWELS[(v + 1) % len(CHEER_VOWELS)], scale,
                    rng.uniform(0.4, 0.8))
    applause = G.claps(n, rng, 40, 150.0, ROAR_MS - 300.0,
                       [(0, 0.0), (300, 0.7), (1200, 1.0), (3200, 0.8), (ROAR_MS, 0.0)])
    whistles = mix(*[(1.0, whistle(n, rng, at, length, hz, glide, level)) for at, length, hz, glide, level in
                     ((260.0, 700.0, 2700.0, 1.12, 0.7), (900.0, 520.0, 3100.0, 1.08, 0.55),
                      (1700.0, 600.0, 2450.0, 1.15, 0.6), (2800.0, 640.0, 2850.0, 1.1, 0.5))])
    bed = crowd_bed(n, rng, 300.0, 2800.0, [(0, 0.0), (220, 0.9), (700, 1.0), (2800, 0.85), (4300, 0.45),
                                            (ROAR_MS, 0.0)])
    swell = shape(n, [(0, 0.0), (180, 0.85), (450, 1.0), (2600, 0.9), (4200, 0.5), (ROAR_MS, 0.0)])
    x = mix((1.0, apply(normalized(voices), swell)), (0.34, normalized(applause)), (0.15, whistles),
            (0.6, normalized(bed)))
    x = echoes(x, ARENA)
    return hp(lp(x, 10500.0), 70.0)


def confetti_pop():
    """A confetti cannon: a deep pneumatic thump and a puff of air out of the barrel, then the paper - a shower of
    tiny crisp flutters thinning out as it drifts."""
    rng = random.Random(4400)
    n = samples(POP_MS)
    from make_eric_v2_sfx import thump
    body = thump(samples(400.0), [(0.0, 150.0), (50.0, 72.0), (300.0, 46.0)], 110.0, attack_ms=1.5)
    puff_k = samples(160.0)
    puff = apply(hp(lp(noise(puff_k, rng), 6500.0), 700.0), decay(puff_k, 45.0, 0.8))
    paper = [0.0] * n
    t = 40.0
    while t < POP_MS - 60.0:
        k = samples(rng.uniform(3.0, 7.0))
        flick = resonator(apply(noise(k, rng), decay(k, 2.0, 0.2)), rng.uniform(2800.0, 6500.0), 3.0)
        place(paper, flick, t, rng.uniform(0.3, 1.0) * math.exp(-(t - 40.0) / 420.0))
        t += rng.expovariate(1.0 / (4.0 + (t - 40.0) / 30.0))
    x = [0.0] * n
    place(x, normalized(body), 0.0, 0.9)
    place(x, normalized(puff), 0.0, 0.6)
    place(x, normalized(paper), 0.0, 0.35)
    x = echoes(x, [(61.0, 0.16, 2600.0), (127.0, 0.09, 1800.0)])
    return hp(x, 35.0)


# ------------------------------------------------------------------------------------------------- the levels

def read_wav(name):
    with wave.open(os.path.join(SFX_DIR, name)) as w:
        assert w.getnchannels() == 1 and w.getsampwidth() == 2 and w.getframerate() == SR, name
        data = w.readframes(w.getnframes())
    return [v / 32768.0 for v in struct.unpack("<%dh" % (len(data) // 2), data)]


def played(x, pitch, db):
    y = x if pitch == 1.0 else godot_resample(x, pitch, int(len(x) / pitch))
    g = 10.0 ** (db / 20.0)
    return [s * g for s in y]


def cycle_level(x):
    w = b_weighted(x + x)[len(x):]
    return 10.0 * math.log10(sum(s * s for s in w) / len(w) + 1e-20)


def loudest_second(x):
    w = b_weighted(x)
    k = samples(1000.0)
    total = sum(s * s for s in w[:k])
    best = total
    for i in range(k, len(w)):
        total += w[i] * w[i] - w[i - k] * w[i - k]
        best = max(best, total)
    return 10.0 * math.log10(best / k + 1e-20)


# The volume_db each file plays at: ChampionEndingLayout.SOUNDS' own, which must stay the same as these.
VOLUME_DB = {"champion_murmur_loop": -16.0, "champion_crowd_loop": -8.0, "champion_roar": 3.0,
             "champion_confetti_pop": -9.0}


def stand_ins():
    """Each stand-in's level as the ending plays it (ChampionEndingLayout.SOUNDS: its pitch, layers and volume_db)."""
    cheer = read_wav("crowd_cheer.wav")
    blast = read_wav("burak_blast.wav")
    layered = [0.0] * samples(3500.0)
    for pitch, at in ((0.94, 0.0), (1.0, 150.0), (1.07, 300.0)):
        place(layered, played(cheer, pitch, 1.0), at)
    return {
        "champion_murmur_loop": cycle_level(played(cheer, 0.7, -22.0)),
        "champion_crowd_loop": cycle_level(played(cheer, 1.0, -8.0)),
        "champion_roar": loudest_second(layered),
        "champion_confetti_pop": loudness_db(played(blast, 1.6, -12.0)),
    }


# name: (builder, loops, measure, where it plays)
SOUNDS = {
    "champion_murmur_loop": (murmur_loop, True, cycle_level, "the crowd waiting through the walk-in, hushed and rising"),
    "champion_crowd_loop": (crowd_loop, True, cycle_level, "the crowd up after the drop, and under the name"),
    "champion_roar": (roar, False, loudest_second, "the drop, and +3 dB on the name"),
    "champion_confetti_pop": (confetti_pop, False, loudness_db, "the confetti burst on the drop and the name"),
}


def finish(name, x, target_db):
    """Ends faded (one-shots), DC out, and scaled to the level its stand-in plays at - held at PEAK_CAP."""
    x = hp(x, 25.0)
    if not SOUNDS[name][1]:
        edge = samples(3.0)
        for i in range(edge):
            g = 0.5 - 0.5 * math.cos(math.pi * i / edge)
            x[i] *= g
            x[-1 - i] *= g
    gain_db = target_db - SOUNDS[name][2](x)
    peak = max(abs(s) for s in x) or 1.0
    room = PEAK_CAP - 20.0 * math.log10(peak)
    short = max(0.0, gain_db - room)
    g = 10.0 ** (min(gain_db, room) / 20.0)
    return [s * g for s in x], short


def seam(x):
    """The jump across the loop's seam against the loop's own sample-to-sample steps, and the level either side."""
    steps = sorted(abs(x[i + 1] - x[i]) for i in range(len(x) - 1))
    jump = abs(x[0] - x[-1])
    k = samples(100.0)
    a = 10.0 * math.log10(sum(s * s for s in x[-k:]) / k + 1e-20)
    b = 10.0 * math.log10(sum(s * s for s in x[:k]) / k + 1e-20)
    return jump, steps[int(0.99 * len(steps))], a - b


def file_bytes(name, x):
    if SOUNDS[name][1]:
        return wav_bytes(x + x[:1], loop=(0, len(x)))
    return wav_bytes(x)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    ship = sys.argv[1] == "--ship"
    folder = SFX_DIR if ship else sys.argv[1]
    os.makedirs(folder, exist_ok=True)
    targets = stand_ins()
    record = {}
    if ship and os.path.exists(SHIPPED):
        with open(SHIPPED) as f:
            record = json.load(f)
    print("%-22s %6s %9s %9s %9s %8s %9s  %s" % ("sound", "ms", "stand-in", "volume_db", "file", "short", "peak", "plays"))
    for name in SOUNDS:
        stand_in_db, volume_db = targets[name], VOLUME_DB[name]
        x, short = finish(name, SOUNDS[name][0](), stand_in_db - volume_db)
        level = SOUNDS[name][2](x)
        peak = 20.0 * math.log10(max(abs(s) for s in x))
        print("%-22s %6.0f %9.1f %+9.1f %9.1f %8.1f %9.1f  %s%s" % (name, len(x) * 1000.0 / SR, stand_in_db, volume_db,
              level, short, peak, SOUNDS[name][3], "  (loop)" if SOUNDS[name][1] else ""))
        if SOUNDS[name][1]:
            jump, step, side = seam(x)
            print("%-22s seam jump %.4f against the loop's 99th-percentile step %.4f; last 100 ms %+.2f dB on the first"
                  % ("", jump, step, side))
        path = os.path.join(folder, ("%s.wav" if ship else "preview_%s.wav") % name)
        data = file_bytes(name, x)
        if ship:
            try:
                with open(path, "xb") as f:
                    f.write(data)
            except FileExistsError:
                print("%-22s already in Assets/Audio/SFX: left as it is" % "")
                continue
            record[name + ".wav"] = {"path": "Assets/Audio/SFX/%s.wav" % name, "sha256": hashlib.sha256(data).hexdigest(),
                                     "bytes": len(data)}
        else:
            with open(path, "wb") as f:
                f.write(data)
    if ship:
        with open(SHIPPED, "w") as f:
            json.dump(record, f, indent=2, sort_keys=True)
            f.write("\n")


if __name__ == "__main__":
    main()
