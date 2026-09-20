"""Cut one seamless loop out of a Sonic Pi recording.

A Sonic Pi take starts whenever Rec was pressed, runs a few times round the piece, and ends
whenever Rec was pressed again, so the raw file has silence in front, a ragged tail, and no
particular relationship to the bar grid. The game wants exactly one cycle, starting on the
downbeat, so `AudioStreamWAV.LOOP_FORWARD` can run it end to end forever.

It finds the first downbeat by looking for the first real transient, then takes exactly one
cycle's worth of frames - the cycle length is arithmetic, not guesswork:
bars * beats_per_bar * 60 / bpm. Output is 16-bit stereo at the source rate.

**It takes the SECOND cycle by default, not the first, and that matters.** Sonic Pi's `sync:`
means every voice except the one driving the clock waits for that loop to come round before it
starts, so cycle 1 is missing whatever had not joined yet. Measured on real takes: Jordan's
cycle-1 bar 1 is **25.1 dB quieter** than his cycle-2 bar 1, Carter's 1.8 dB, Eric's 0.1 dB. An
early cut therefore ships a near-empty opening bar - and with `edit/loop_mode=2` that bar now
repeats for the whole fight. `--cycle 0` restores the old behaviour if a take only has one.

    python cut_loop.py greyson_theme_raw.wav 160 --out ../../Assets/Audio/Music/greyson_theme.wav

Pass --bars/--beats if a piece is not the usual 16 bars of 4.
"""

import argparse
import struct
import wave


def read_frames(path):
    with wave.open(path, "rb") as w:
        return (w.getnchannels(), w.getsampwidth(), w.getframerate(),
                w.readframes(w.getnframes()))


def to_mono_16(raw, channels, width):
    """A coarse mono signal for onset detection only - not what gets written out."""
    step = width * channels
    out = []
    for i in range(0, len(raw) - step + 1, step):
        total = 0
        for c in range(channels):
            off = i + c * width
            if width == 3:
                b = raw[off:off + 3]
                v = b[0] | (b[1] << 8) | (b[2] << 16)
                if v & 0x800000:
                    v -= 1 << 24
                v >>= 8
            elif width == 2:
                v = struct.unpack_from("<h", raw, off)[0]
            else:
                v = (raw[off] - 128) << 8
            total += v
        out.append(total // channels)
    return out


def find_onset(mono, rate, search_seconds, floor_ratio=0.12):
    """The first window that is clearly louder than the room tone in front of it."""
    win = max(1, rate // 100)          # 10 ms
    limit = min(len(mono), int(rate * search_seconds))
    peaks = []
    for start in range(0, limit - win, win):
        peak = 0
        for i in range(start, start + win):
            a = mono[i]
            if a < 0:
                a = -a
            if a > peak:
                peak = a
        peaks.append((start, peak))
    if not peaks:
        return 0
    loudest = max(p for _, p in peaks)
    threshold = loudest * floor_ratio
    for start, peak in peaks:
        if peak >= threshold:
            return start
    return 0


def write_16bit(path, raw, channels, width, rate, start_frame, frame_count):
    step = width * channels
    begin = start_frame * step
    end = begin + frame_count * step
    if end > len(raw):
        raise SystemExit(
            f"the take is too short: need {frame_count} frames from {start_frame}, "
            f"only {len(raw) // step - start_frame} left")
    chunk = raw[begin:end]
    out = bytearray()
    for i in range(0, len(chunk), width):
        if width == 3:
            b = chunk[i:i + 3]
            v = b[0] | (b[1] << 8) | (b[2] << 16)
            if v & 0x800000:
                v -= 1 << 24
            v >>= 8
        elif width == 2:
            v = struct.unpack_from("<h", chunk, i)[0]
        else:
            v = (chunk[i] - 128) << 8
        out += struct.pack("<h", max(-32768, min(32767, v)))
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("bpm", type=float)
    ap.add_argument("--out", required=True)
    ap.add_argument("--bars", type=int, default=16)
    ap.add_argument("--beats", type=int, default=4)
    ap.add_argument("--search", type=float, default=20.0,
                    help="seconds of the head to look in for the downbeat")
    ap.add_argument("--offset", type=float, default=0.0,
                    help="nudge the cut point, in seconds, when the transient is not the downbeat")
    ap.add_argument("--cycle", type=int, default=1,
                    help="which cycle after the downbeat to take (default 1, the second). "
                         "Cycle 0 is missing any voice that had not synced in yet.")
    args = ap.parse_args()

    channels, width, rate, raw = read_frames(args.source)
    total = len(raw) // (width * channels)
    cycle_seconds = args.bars * args.beats * 60.0 / args.bpm
    cycle_frames = int(round(cycle_seconds * rate))

    mono = to_mono_16(raw, channels, width)
    onset = find_onset(mono, rate, args.search) + int(round(args.offset * rate))
    onset = max(0, onset)
    available = (total - onset) / cycle_frames
    start = onset + args.cycle * cycle_frames

    print(f"source   {args.source}  {channels}ch {width * 8}-bit {rate} Hz  "
          f"{total / rate:.3f} s")
    print(f"cycle    {args.bars} bars x {args.beats} at {args.bpm:g} bpm = "
          f"{cycle_seconds:.4f} s  ({cycle_frames} frames)")
    print(f"downbeat {onset / rate:.3f} s")
    print(f"cycles available after the downbeat: {available:.2f}")
    print(f"taking   cycle {args.cycle} -> from {start / rate:.3f} s"
          + ("  (cycle 0 may be missing voices that had not synced in)"
             if args.cycle == 0 else ""))
    if available < args.cycle + 1:
        raise SystemExit(
            f"the take only has {available:.2f} cycles after the downbeat; "
            f"cycle {args.cycle} needs {args.cycle + 1}. Record longer, or pass a lower --cycle.")

    write_16bit(args.out, raw, channels, width, rate, start, cycle_frames)
    print(f"wrote    {args.out}  {cycle_seconds:.3f} s, 16-bit {channels}ch {rate} Hz")


if __name__ == "__main__":
    main()
