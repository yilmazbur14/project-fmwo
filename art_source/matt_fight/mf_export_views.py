"""Write the trueshot's extra views, each PNG with its .aseprite beside it, after checking every
frame. A bare run writes nothing:

    python mf_export_views.py <scratch_dir>    # write all eight files there, for checking
    python mf_export_views.py --ship           # write them into Assets/Characters/Matt/

It only ever writes these names (.png and .aseprite): matt_trueshot_charge_back,
matt_trueshot_fire_back (the BOTTOM station, facing up the ring), matt_trueshot_charge_side,
matt_trueshot_fire_side (the LEFT/RIGHT stations, drawn facing screen-right; the code mirrors it).

Checked per frame as the rest of the set: 96x96, feet on row 95, top at row 1 or lower, only the
approved 41 colours, pure black, no semi-alpha, a clean audit. Black ratio 22-28% for the side view;
20-28% for the back view, which has no face: the eyes, brows and mouth that carry a front frame's
black are on the far side of his head, and nothing was drawn in to pad the number.

Prints every frame's WAVE SPAWN (where the blast leaves him), crest top and crown.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mf_base as M  # noqa: E402
from mf_base import B, A, F  # noqa: E402
import mf_back  # noqa: E402
import mf_side  # noqa: E402
import mf_hands as MH  # noqa: E402

SHEETS = [
    (mf_back.ChargeBack, '4 x 0.12 s, looping', (0.20, 0.28)),
    (mf_back.FireBack, '0.06, 0.08, hold', (0.20, 0.28)),
    (mf_side.ChargeSide, '4 x 0.12 s, looping', (0.22, 0.28)),
    (mf_side.FireSide, '0.06, 0.08, hold', (0.22, 0.28)),
]


def frame_px(f):
    return f.px() if isinstance(f, mf_back.BackFig) else F.px_of(f)


def anchors(f, px):
    top = min(y for (x, y) in px)
    xs = sorted(x for (x, y) in px if y == top)
    out = {'crest_top': (xs[len(xs) // 2], top)}
    if isinstance(f, mf_back.BackFig):
        cx, cy = f.crown()
        out['crown'] = (cx, cy)
        # facing up the ring: the blast leaves just past the top of his head
        out['wave_spawn'] = (cx, cy - 3)
        return out
    P = f.pose()
    out['crown'] = (48 + f.head[0], 16 + f.head[1] + P.head_dy)
    near = f.arms[1]
    ax, ay = A.attach(near)
    ac, ar = MH.MEGA_CONE[1]
    bx, by = f.body
    tl = (int(round(ax)) - ac + bx, int(round(ay)) - ar + by)
    # one texel past the cone's opening, level with its middle
    out['wave_spawn'] = (tl[0] + len(MH.MEGA_CONE[0][0]), tl[1] + 5)
    return out


def check(cls, allowed, black_range):
    figs = cls.figs()
    problems, rows, frames, anc = [], [], [], []
    for i, f in enumerate(figs):
        px = frame_px(f)
        frames.append(px)
        im = B.image(px)
        st = B.stats(im)
        cols = {c for c in B.flat(im) if c[3]}
        a = B.audit(px, getattr(f, 'fx', set()))
        x0, y0, x1, y1 = B.bbox(px)
        tag = '%s f%d' % (cls.NAME, i)
        if cols - allowed:
            problems.append('%s: colours outside the approved 41' % tag)
        if {c for c in cols if c[:3] == (0, 0, 0)} - {(0, 0, 0, 255)}:
            problems.append('%s: impure black' % tag)
        if st['semi']:
            problems.append('%s: semi-transparent pixels' % tag)
        if any(a.values()):
            problems.append('%s: %s' % (tag, {k: v[:5] for k, v in a.items() if v}))
        if y1 != 95:
            problems.append('%s: lowest drawn row is %d, not 95' % (tag, y1))
        if y0 < 1:
            problems.append('%s: drawn on row %d, above the approved headroom' % (tag, y0))
        if not (black_range[0] <= st['black'] <= black_range[1]):
            problems.append('%s: black %.1f%% outside range' % (tag, 100 * st['black']))
        rows.append((i, st, len(cols), (x0, y0, x1, y1)))
        anc.append(anchors(f, px))
    return B.strip(frames), rows, problems, anc


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = B.ASSETS if argv[0] == '--ship' else os.path.abspath(argv[0])
    allowed = {c for c in B.flat(B.approved_sheet()) if c[3]}
    built, problems = [], []
    for cls, times, rng in SHEETS:
        im, rows, probs, anc = check(cls, allowed, rng)
        built.append((cls, times, im, rows, anc))
        problems += probs
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    status = 0
    for cls, times, im, rows, anc in built:
        png, ase, rt = B.write_sheet(cls.NAME, im, out_dir)
        sheet = B.stats(im)
        print('%s  %dx%d, %d frames, %s' % (os.path.basename(png), im.width, im.height, len(rows), times))
        print('   .aseprite round trip:', rt or 'identical')
        for (i, st, ncol, bb), a in zip(rows, anc):
            print('   f%d  black %.1f%%  colours %2d  %s' % (
                i, 100 * st['black'], ncol, '  '.join('%s %s' % kv for kv in a.items())))
        print('   sheet: colours %d, black %.1f%%' % (sheet['colours'], 100 * sheet['black']))
        status |= 1 if rt else 0
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
