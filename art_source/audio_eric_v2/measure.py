"""Prints the level table for the Eric V2 finisher sounds against the game's own, and checks the charge loop's seam.

    python measure.py DECODED_DIR

DECODED_DIR holds the game's OGGs decoded through Godot's playback, so they are measured the way they play:
    Godot.exe --headless --path . --script res://art_source/punch_fx/dump_audio.gd -- out=DECODED_DIR ^
        res://Assets/Audio/SFX/hit_impact.ogg res://Assets/Audio/SFX/earthquake_slam.ogg ^
        res://Assets/Audio/SFX/player_hurt.ogg res://Assets/Audio/SFX/whirlwind_whoosh.ogg ^
        res://Assets/Audio/Music/boss_theme.ogg
The synthesized WAVs are read straight from Assets/Audio/SFX. Nothing in Assets/Audio/SFX/local is read.

Columns: sample peak and 4x true peak in dBFS; RMS over the whole file and over its loudest 80 ms; loudness on
make_voices.loudness_db's scale (B-weighted, loudest 80 ms), which every synthesized SFX here is matched on; that
loudness against hit_impact; and how long until the sound is 40 dB down.
"""

import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dsp  # noqa: E402
from dsp import SR, samples, loudness_db  # noqa: E402
from make_eric_v2_sfx import SFX_DIR, SOUNDS, LEVELS, HIT_REF_DB  # noqa: E402

REFERENCES = [
    ("hit_impact.ogg", "decoded", "every punch and uppercut contact, 0 dB"),
    ("dash_whoosh.wav", "sfx", "the dash, 0 dB"),
    ("punch_whoosh.wav", "sfx", "the punch swing, 0 dB"),
    ("parry_hit_1.wav", "sfx", "the parry (public fallback), 0 dB"),
    ("parry_hit_2.wav", "sfx", "the parry, variant"),
    ("parry_hit_3.wav", "sfx", "the parry, variant"),
    ("earthquake_slam.ogg", "decoded", "Eric's slam; the crash's stand-in at pitch 0.6"),
    ("player_hurt.ogg", "decoded", "the player hit, loudest cue"),
    ("whirlwind_whoosh.ogg", "decoded", "whirlwind / perfect dodge"),
]

# The loop's pitch at no bars, each bar banked (1.0 + 0.2 k), and on a 48 kHz output device, where Godot
# resamples every stream by 44.1/48 on top of its pitch.
LOOP_RATES = [1.0, 1.2, 1.4, 1.6, 44100.0 / 48000.0, 1.6 * 44100.0 / 48000.0]


def load(name, where, decoded_dir):
    if where == "decoded":
        path = os.path.join(decoded_dir, os.path.splitext(name)[0] + ".wav")
    else:
        path = os.path.join(SFX_DIR, name)
    x, loop = dsp.read_wav_file(path)
    return x, loop


def row(name, x, note=""):
    level = loudness_db(x)
    print("%-26s %6.0f %7.1f %7.1f %7.1f %7.1f %7.1f %+7.1f %6.0f  %s" % (
        name, len(x) * 1000.0 / SR, dsp.peak_db(x), dsp.true_peak_db(x), dsp.rms_db(x), dsp.short_rms_db(x), level,
        level - HIT_REF_DB, dsp.ring_out_ms(x), note))


def header(title):
    print()
    print(title)
    print("%-26s %6s %7s %7s %7s %7s %7s %7s %6s" % ("file", "ms", "peak", "tpeak", "RMS", "RMS80", "loud", "vs hit",
                                                     "-40dB"))


def seam_report(x, loop):
    """The loop's seam three ways. The file: the step Godot plays from the loop's last frame into the guard frame
    at loop_end, and from the guard on to frame 1, against every other step in the loop. Then the loop played
    through dsp.godot_resample (Godot 4.6's playback, checked against Godot's own output) at several rates, with
    a click measure (energy of the second difference over 1.5 ms) around every pass through the seam against
    the same measure everywhere else in the loop."""
    begin, end = loop
    n = end - begin
    print()
    print("LOOP SEAM (finisher_charge_loop.wav: %d loop frames = %.3f s, plus %d guard frame; smpl loop %s)" % (
        n, n / SR, len(x) - n, loop))
    assert begin == 0 and len(x) == n + 1 and x[n] == x[0], "expected the loop then one guard frame copying its first"
    steps = sorted(abs(x[i] - x[i - 1]) for i in range(1, n))
    into_guard = abs(x[n] - x[n - 1])
    out_of_guard = abs(x[1] - x[n])
    worst = max(into_guard, out_of_guard)
    rank = 100.0 * sum(1 for s in steps if s < worst) / len(steps)
    print("  file: frames %+.5f -> guard %+.5f -> %+.5f; largest seam step %.5f (%.1f dBFS) against a median step"
          " of %.5f and a largest of %.5f: bigger than %.1f%% of the steps inside the loop" % (
              x[n - 1], x[n], x[1], worst, dsp.db(worst), steps[len(steps) // 2], steps[-1], rank))
    window = samples(1.5)
    for rate in LOOP_RATES:
        count = int(n * 3.2 / rate)
        y = dsp.godot_resample(x, rate, count, loop=loop)
        wraps = [2 + int(round(k * n / rate)) for k in (1, 2, 3) if 2 + k * n / rate < count - window]
        d2 = [0.0, 0.0] + [y[i] - 2.0 * y[i - 1] + y[i - 2] for i in range(2, count)]

        def energy(centre):
            lo = max(2, centre - window // 2)
            return sum(v * v for v in d2[lo:lo + window]) / window

        others = sorted(energy(c) for c in range(window, count - window, window // 2)
                        if all(abs(c - w) > 2 * window for w in wraps))
        worst = max(energy(w) for w in wraps)
        rank = 100.0 * sum(1 for e in others if e < worst) / len(others)
        print("  played at %.4f: %d passes through the seam; worst seam click measure %+.1f dB against the loop's"
              " median, at the %.1f percentile of the rest of the loop (max elsewhere %+.1f dB)" % (
                  rate, len(wraps), 10.0 * math.log10(worst / others[len(others) // 2]), rank,
                  10.0 * math.log10(others[-1] / others[len(others) // 2])))


def main():
    decoded_dir = sys.argv[1]
    header("REFERENCES (as the game plays them)")
    for name, where, note in REFERENCES:
        x, _ = load(name, where, decoded_dir)
        row(name, x, note)
    music, _ = load("boss_theme.ogg", "decoded", decoded_dir)
    music = [s * 10.0 ** (-4.0 / 20.0) for s in music]
    print("%-26s %6.0f   median 400 ms loudness %.1f (MusicPlayer at -4 dB, first %.1f s)" % (
        "boss_theme.ogg", len(music) * 1000.0 / SR, dsp.long_loudness_db(music), len(music) / SR))

    header("NEW (targets: %s)" % ", ".join("%s %.1f" % (k, v[0]) for k, v in LEVELS.items()))
    loop_x = loop_info = None
    for name, _, loops in SOUNDS:
        x, loop = load(name + ".wav", "sfx", decoded_dir)
        if loops:
            loop_x, loop_info = x, loop
            turn = x[:loop[1]]
            row(name + ".wav", turn + turn, "two turns (%.0f ms each)" % (len(turn) * 1000.0 / SR))
            for rate in (1.0, 1.6):
                y = dsp.godot_resample(x, rate, int(len(turn) * 2 / rate), loop=loop)
                print("%-26s        at pitch %.1f: loudness %.1f (%+.1f vs hit), 400 ms median %.1f, peak %.1f" % (
                    "", rate, loudness_db(y), loudness_db(y) - HIT_REF_DB, dsp.long_loudness_db(y), dsp.peak_db(y)))
        else:
            row(name + ".wav", x)

    crash, _ = load("eric_crash_thud.wav", "sfx", decoded_dir)
    slam, _ = load("earthquake_slam.ogg", "decoded", decoded_dir)
    print()
    print("crash vs slam: centroid %.0f vs %.0f Hz; share under 150 Hz %.0f%% vs %.0f%%; loudness %.1f vs %.1f;"
          " 40 dB down at %.0f vs %.0f ms" % (
              dsp.centroid_hz(crash), dsp.centroid_hz(slam), 100 * dsp.band_share(crash, 150.0),
              100 * dsp.band_share(slam, 150.0), loudness_db(crash), loudness_db(slam), dsp.ring_out_ms(crash),
              dsp.ring_out_ms(slam)))
    seam_report(loop_x, loop_info)


if __name__ == "__main__":
    main()
