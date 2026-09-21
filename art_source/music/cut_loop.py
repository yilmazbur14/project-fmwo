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


def sample_at(raw, width, offset):
    """One sample, as a signed 16-bit value, from a source of any supported width."""
    if width == 3:
        b = raw[offset:offset + 3]
        v = b[0] | (b[1] << 8) | (b[2] << 16)
        if v & 0x800000:
            v -= 1 << 24
        return v >> 8
    if width == 2:
        return struct.unpack_from("<h", raw, offset)[0]
    return (raw[offset] - 128) << 8


def body_step(values, channels, percentile=0.99):
    """How far the signal normally moves between adjacent samples, inside the piece.

    The yardstick for the seam. A fixed threshold cannot tell a cut artifact from a downbeat kick:
    Carter's seam measures 3342 either way, because his piece IS periodic there and both the cut and
    the crossfade land on the same real transient. Compared against his own 1908, that reads as what
    it is - the music moving - rather than as a click.
    """
    steps = sorted(abs(values[i] - values[i - channels])
                   for i in range(channels, len(values), channels))
    return steps[int(len(steps) * percentile)] if steps else 0, steps[-1] if steps else 0


def seam_jump(values, channels):
    """How far the signal has to leap when the loop wraps, in 16-bit units."""
    frames = len(values) // channels
    if frames < 2:
        return 0
    return max(abs(values[(frames - 1) * channels + c] - values[c]) for c in range(channels))


def write_16bit(path, raw, channels, width, rate, start_frame, frame_count, seam_frames=0):
    """One cycle, with the loop seam made continuous.

    Taking exactly one arithmetic cycle lands the cut wherever the waveform happens to be, which is
    almost never where it was at the downbeat. Measured on real takes, Eric's seam leapt 31741 of a
    possible 32768 while the busiest moment inside the piece moved 1745 - a loud click, once every
    27.8 seconds, forever.

    The piece is periodic, so the frames just BEFORE the loop start are near-copies of the frames at
    its end, and the last one of them is by definition continuous with the first frame of the loop.
    Crossfading the tail onto them over a few milliseconds therefore forces the seam shut while
    leaving the cycle exactly one cycle long - which nudging the cut point to a zero crossing would
    not, and which matters because a drifting loop length walks off the beat a little more each pass.
    """
    step = width * channels
    end = (start_frame + frame_count) * step
    if end > len(raw):
        raise SystemExit(
            f"the take is too short: need {frame_count} frames from {start_frame}, "
            f"only {len(raw) // step - start_frame} left")
    # The fade reads from the cycle before this one, so there has to be one.
    seam_frames = max(0, min(seam_frames, start_frame, frame_count - 1))

    plain = []
    for f in range(frame_count):
        for c in range(channels):
            plain.append(sample_at(raw, width, (start_frame + f) * step + c * width))
    before = seam_jump(plain, channels)

    values = list(plain)
    if seam_frames:
        first = frame_count - seam_frames
        for f in range(first, frame_count):
            weight = (f - first) / float(seam_frames - 1) if seam_frames > 1 else 1.0
            for c in range(channels):
                prev = sample_at(raw, width, (start_frame - frame_count + f) * step + c * width)
                i = f * channels + c
                values[i] = int(round(values[i] * (1.0 - weight) + prev * weight))
    after = seam_jump(values, channels)
    motion, biggest = body_step(values, channels)

    out = bytearray()
    for v in values:
        out += struct.pack("<h", max(-32768, min(32767, v)))
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(out))
    return before, after, motion, biggest


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
    ap.add_argument("--seam", type=float, default=12.0,
                    help="milliseconds of crossfade onto the previous cycle, closing the loop seam. "
                         "0 disables it.")
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

    seam_frames = int(round(args.seam / 1000.0 * rate))
    before, after, motion, biggest = write_16bit(
        args.out, raw, channels, width, rate, start, cycle_frames, seam_frames)
    print(f"wrote    {args.out}  {cycle_seconds:.3f} s, 16-bit {channels}ch {rate} Hz")
    # With a crossfade applied the last frame IS the frame before the loop start, so the wrap is two
    # adjacent samples of the original take and is continuous by construction. What is worth printing
    # is how big that natural step is next to the rest of the piece - a downbeat kick is allowed to be
    # large. Only a seam beyond anything the piece does means the fade did not take.
    verdict = ("the fade did not take" if seam_frames and after > biggest
               else "continuous by construction")
    print(f"seam     {before} -> {after} over {args.seam:g} ms; the piece's own steps reach "
          f"{motion} (99th) and {biggest} (max) -> {verdict}")


if __name__ == "__main__":
    main()
