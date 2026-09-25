"""Build every MESSATSU effect into Assets/Characters/Carter/Messatsu/.

    python build_messatsu.py [out_dir]

With no argument it writes the shipped sheets; with one it writes the same
sheets somewhere else (a scratch folder, for review).  Nothing here touches
Carter's body sheets, the Demon's effects, the scenes or the scripts.

Each sheet is a horizontal strip, frame 0 leftmost.  The .aseprite beside each
PNG is written by Aseprite from the PNG afterwards (see the report / README in
the hand-off), never by hand.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.chdir(_HERE)

import beam        # noqa: E402
import charge      # noqa: E402
from mpal import colours   # noqa: E402

OUT = os.path.abspath(os.path.join('..', '..', 'Assets', 'Characters',
                                   'Carter', 'Messatsu'))

# name: (builder, frame builder, frame count, frame w, frame h, blend)
SHEETS = [
    ('messatsu_ball', charge.ball_frame, 6, charge.BS, charge.BS, 'add'),
    ('messatsu_eyes', charge.eyes_frame, 2, charge.EW, charge.EH, 'add'),
    ('messatsu_lock', charge.lock_frame, 6, charge.LS, charge.LS, 'add'),
    ('messatsu_beam', beam.beam_frame, 4, beam.BW, beam.BH, 'paint'),
    ('messatsu_flare', beam.flare_frame, 4, beam.FW, beam.FH, 'paint'),
    ('messatsu_head', beam.head_frame, 3, beam.HW, beam.HH, 'paint'),
    ('messatsu_pulse', beam.pulse_frame, 3, beam.UW, beam.UH, 'paint'),
]


def main(out=OUT):
    from mpal import sheet
    if not os.path.isdir(out):
        os.makedirs(out)
    made = []
    for name, fn, n, fw, fh, blend in SHEETS:
        frames = [fn(i) for i in range(n)]
        path = os.path.join(out, name + '.png').replace('\\', '/')
        sheet(frames, path)
        made.append(path)
        print('%-16s %3d x %-3d x %d  %-5s  %d colours' % (
            name, fw, fh, n, blend, len(colours(frames))))
    return made


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else OUT)
