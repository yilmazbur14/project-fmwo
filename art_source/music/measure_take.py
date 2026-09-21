"""Report a take's level, cycle by cycle, so a missing layer is visible before it ships.

This pipeline has shipped silence twice, and neither time did anything fail loudly:

  - a fractional `noise:` on :hollow killed a live_loop at runtime while every other voice played;
  - `look(:bar)` reads 0 forever from a non-ticking thread, so Carter's demon sequence, Mason's
    comedy moments and Jordan's bass, lead and fuses never sounded in any shipped recording.

Both would have shown here as a cycle that is quieter than it should be, or as a take whose cycles
never fill out. Sonic Pi's `sync:` also means cycle 1 is legitimately thinner than cycle 2 - every
voice waiting on the driving loop has not joined yet - which is why cut_loop takes the second one.
A take where cycle 2 is NOT fuller than cycle 1 is the suspicious one.

    python measure_take.py raw/eric_theme_v3_raw.wav 138
"""

import argparse
import math
import pathlib
import struct
import wave


def samples(raw, width, channels):
    """Signed sample values, correct for 16- and 24-bit."""
    step = width * channels
    for i in range(0, len(raw) - step + 1, step):
        for c in range(channels):
            off = i + c * width
            if width == 2:
                yield struct.unpack("<h", raw[off:off + 2])[0]
            elif width == 3:
                b = raw[off:off + 3]
                v = b[0] | (b[1] << 8) | (b[2] << 16)
                yield v - 0x1000000 if v & 0x800000 else v
            else:
                yield struct.unpack("<i", raw[off:off + 4])[0]


def db(value, full):
    return 20 * math.log10(value / full) if value > 0 else -99.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("take")
    ap.add_argument("bpm", type=int)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--beats", type=int, default=4)
    args = ap.parse_args()

    with wave.open(args.take, "rb") as w:
        ch, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(w.getnframes())

    full = float(1 << (width * 8 - 1))
    vals = list(samples(raw, width, ch))
    per_frame = ch
    frames = len(vals) // per_frame
    cycle_frames = int(args.bars * args.beats * 60.0 / args.bpm * rate)

    peak = max((abs(v) for v in vals), default=0)
    rms = math.sqrt(sum(v * v for v in vals) / len(vals)) if vals else 0.0
    print("%s  %d Hz %d-bit x%d  %.2f s" % (
        pathlib.Path(args.take).name, rate, width * 8, ch, frames / rate))
    print("  overall peak %6.1f dBFS   rms %6.1f dBFS" % (db(peak, full), db(rms, full)))

    prev = None
    for c in range(max(1, frames // cycle_frames)):
        seg = vals[c * cycle_frames * per_frame:(c + 1) * cycle_frames * per_frame]
        if not seg:
            break
        c_rms = math.sqrt(sum(v * v for v in seg) / len(seg))
        c_peak = max(abs(v) for v in seg)
        note = ""
        if prev is not None:
            delta = db(c_rms, full) - prev
            note = "  (%+.1f dB vs previous)" % delta
            if c == 1 and delta < -0.5:
                note += "  <-- SUSPICIOUS: cycle 2 should not be quieter than cycle 1"
        print("  cycle %d: peak %6.1f  rms %6.1f dBFS%s" % (
            c + 1, db(c_peak, full), db(c_rms, full), note))
        prev = db(c_rms, full)

    silent = sum(1 for i in range(0, len(vals), rate * per_frame)
                 if max((abs(v) for v in vals[i:i + rate * per_frame]), default=0) < full * 0.001)
    if silent:
        print("  WARNING: %d second-long stretches are effectively silent" % silent)


if __name__ == "__main__":
    main()
