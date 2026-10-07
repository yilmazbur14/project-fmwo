"""Cut a theme's one-shot intro out of the same take its loop comes from.

Some themes open with an intro that plays once, followed by a body that loops, and both come out
of one take (jordan_final_theme.rb: 8 intro bars, then 64 looping bars). cut_loop.py already cuts
the loop: give it --offset <intro seconds> and it skips the intro, then takes the body's second
pass as usual. This cuts the intro to match it, so that intro.wav followed by loop.wav joins as
cleanly as the loop joins itself:

  - the intro starts on the same downbeat cut_loop.py finds (it uses cut_loop's own detector)
    and is exactly --intro-bars long;
  - its last --seam milliseconds are crossfaded onto the frames just before the loop file's first
    frame, so the join intro -> loop is two adjacent samples of the original take. That makes it
    continuous by construction, the same trick cut_loop.py uses on the loop's own seam.

The loop file's first frame is the take's frame at downbeat + intro + cycle x (bars of the body).
Pass the same --bars/--beats/--cycle you gave cut_loop.py.

    python cut_intro.py take.wav 185 --intro-bars 8 --bars 64 --out intro.wav [--loop loop.wav]

With --loop it also reads the loop file back and reports the actual join, sample for sample.
"""

import argparse
import struct
import wave

from cut_loop import find_onset, read_frames, sample_at, to_mono_16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("bpm", type=float)
    ap.add_argument("--out", required=True)
    ap.add_argument("--intro-bars", type=int, default=8)
    ap.add_argument("--bars", type=int, default=64, help="bars in the looping body")
    ap.add_argument("--beats", type=int, default=4)
    ap.add_argument("--cycle", type=int, default=1,
                    help="which pass of the body cut_loop.py took (its --cycle; default 1)")
    ap.add_argument("--search", type=float, default=20.0)
    ap.add_argument("--offset", type=float, default=0.0,
                    help="nudge the downbeat, in seconds, exactly as cut_loop.py's --offset would "
                         "WITHOUT the intro length in it")
    ap.add_argument("--seam", type=float, default=12.0,
                    help="milliseconds of crossfade onto the frames before the loop's first frame")
    ap.add_argument("--loop", help="the loop file cut_loop.py wrote, to check the join against")
    args = ap.parse_args()

    channels, width, rate, raw = read_frames(args.source)
    step = width * channels
    total = len(raw) // step
    beat = 60.0 / args.bpm
    intro_seconds = args.intro_bars * args.beats * beat
    # cut_loop.py rounds its --offset to whole frames the same way, so passing it the intro length
    # (printed below) lands its loop exactly where this expects it.
    intro_frames = int(round(intro_seconds * rate))
    cycle_frames = int(round(args.bars * args.beats * beat * rate))

    mono = to_mono_16(raw, channels, width)
    onset = max(0, find_onset(mono, rate, args.search) + int(round(args.offset * rate)))
    loop_start = onset + intro_frames + args.cycle * cycle_frames
    if loop_start >= total:
        raise SystemExit("the take ends before the loop would start; record longer")

    seam_frames = max(0, min(int(round(args.seam / 1000.0 * rate)), intro_frames - 1))
    values = []
    for f in range(intro_frames):
        for c in range(channels):
            values.append(sample_at(raw, width, (onset + f) * step + c * width))

    def frame(i):
        return [sample_at(raw, width, i * step + c * width) for c in range(channels)]

    first_of_loop = frame(loop_start)
    before = max(abs(values[(intro_frames - 1) * channels + c] - first_of_loop[c])
                 for c in range(channels))
    if seam_frames:
        first = intro_frames - seam_frames
        for f in range(first, intro_frames):
            weight = (f - first) / float(seam_frames - 1) if seam_frames > 1 else 1.0
            src = loop_start - intro_frames + f  # the frames just before the loop's first
            for c in range(channels):
                i = f * channels + c
                prev = sample_at(raw, width, src * step + c * width)
                values[i] = int(round(values[i] * (1.0 - weight) + prev * weight))
    after = max(abs(values[(intro_frames - 1) * channels + c] - first_of_loop[c])
                for c in range(channels))

    out = bytearray()
    for v in values:
        out += struct.pack("<h", max(-32768, min(32767, v)))
    with wave.open(args.out, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(out))

    print(f"source   {args.source}  {channels}ch {width * 8}-bit {rate} Hz  {total / rate:.3f} s")
    print(f"downbeat {onset / rate:.3f} s (cut_loop.py's detector)")
    print(f"intro    {args.intro_bars} bars = {intro_seconds:.6f} s ({intro_frames} frames) "
          f"-> pass cut_loop.py --offset {intro_seconds:.6f}")
    print(f"loop     starts at {loop_start / rate:.3f} s in the take (body pass {args.cycle})")
    print(f"wrote    {args.out}")
    print(f"join     intro's last frame -> loop's first frame: {before} -> {after} "
          f"over {args.seam:g} ms (an adjacent pair of the take after the fade)")

    if args.loop:
        with wave.open(args.loop, "rb") as w:
            lf = w.readframes(1)
            loop_first = [struct.unpack_from("<h", lf, c * 2)[0] for c in range(w.getnchannels())]
        real = max(abs(values[(intro_frames - 1) * channels + c] - loop_first[c])
                   for c in range(channels))
        match = "matches" if loop_first == first_of_loop else "DOES NOT MATCH"
        print(f"check    {args.loop}: its first frame {match} the take at the loop start; "
              f"the real join steps {real}")


if __name__ == "__main__":
    main()
