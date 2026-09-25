"""Write Matt's fight body set, each PNG with its .aseprite beside it, after checking every frame.
A bare run writes nothing:

    python mf_export.py <scratch_dir>     # write all twenty files there, for checking
    python mf_export.py --ship            # write them into Assets/Characters/Matt/

It only ever writes these names (.png and .aseprite): matt_recover, matt_hit, matt_yell_tell,
matt_mystic_cast, matt_trueshot_charge, matt_trueshot_fire, matt_teleport, matt_idle, matt_spent,
matt_defeat. Each file is built in a temp folder and moved into place in one step, and each .aseprite
is re-exported and compared with its PNG pixel for pixel (art_source/imgdiff.pixel_diff).

Checked before anything is written, per frame: 96x96, lowest drawn row 95, highest row 1 or lower
(the approved headroom), only the approved sheet's 41 colours, pure black, no semi-alpha, no keyline
gaps / stray pixels / pinholes, black ratio 22-28% (not for the teleport's streak frames, which are
a thin keylined spindle, not his body), and matt_idle f0 is matt.png f0 pixel for pixel.

Also prints every frame's anchors (crest top, crown, mouth) and BODY_BOX, traced off the recover
pose with the crest's spikes excluded.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mf_base as M  # noqa: E402
from mf_base import B, F, PZ  # noqa: E402
import mi_anchors  # noqa: E402
import mf_recover  # noqa: E402
import mf_shout  # noqa: E402
import mf_trueshot  # noqa: E402
import mf_teleport  # noqa: E402
import mf_idle  # noqa: E402
import mf_defeat  # noqa: E402

SHEETS = [
    (mf_recover.Recover, '4 x 0.18 s, looping'),
    (mf_recover.Hit, '0.07, 0.12'),
    (mf_shout.YellTell, '2 x 0.20 s, then matt_roar f1-3 is the yell'),
    (mf_shout.MysticCast, '0.225, 0.225, 0.075, 0.075; the bolt leaves the mouth on f2'),
    (mf_trueshot.Charge, '4 x 0.12 s, looping'),
    (mf_trueshot.Fire, '0.06, 0.08, hold; the wave leaves the mouth on f0'),
    (mf_teleport.Teleport, '6 x 0.05 s: out 0-2, in 3-5'),
    (mf_idle.Idle, '4 x 0.16 s, looping; f0 = matt.png f0'),
    (mf_idle.Spent, '4 x 0.15 s, looping'),
    (mf_defeat.Defeat, '0.13, 0.11, 0.11, 0.13, 0.18, hold'),
]
BLACK_RANGE = (0.22, 0.28)
STREAK_FRAMES = {('matt_teleport', i) for i in (1, 2, 3, 4)}


def px_of(f):
    return mf_teleport.px_of(f)


def is_fig(f):
    return isinstance(f, F.Fig)


def anchors(f, px):
    if not is_fig(f):
        top = min(y for (x, y) in px)
        xs = sorted(x for (x, y) in px if y == top)
        return {'crest_top': (xs[len(xs) // 2], top)}
    return mi_anchors.anchors(f, px)


def body_box(f):
    """The frame's bounding box with the crest's spikes shrunk into the dome: BODY_BOX's source."""
    import copy
    g = copy.copy(f)
    g.spikes = [(0, 8, 8.5, 0.1, 0.1, 0.0)] * 3
    return B.bbox(F.px_of(g))


def check(cls, allowed):
    figs = cls.figs()
    problems, rows, frames, anc = [], [], [], []
    for i, f in enumerate(figs):
        px = px_of(f)
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
        if (cls.NAME, i) not in STREAK_FRAMES and not (BLACK_RANGE[0] <= st['black'] <= BLACK_RANGE[1]):
            problems.append('%s: black %.1f%% outside range' % (tag, 100 * st['black']))
        rows.append((i, st, len(cols), (x0, y0, x1, y1)))
        anc.append(anchors(f, px))
    if cls is mf_idle.Idle:
        d = B.pixel_diff(B.image(frames[0]), B.approved_sheet().crop((0, 0, 96, 96)))
        if d:
            problems.append('matt_idle f0 is not matt.png f0: %s' % d)
    return B.strip(frames), rows, problems, anc


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    out_dir = B.ASSETS if argv[0] == '--ship' else os.path.abspath(argv[0])
    allowed = {c for c in B.flat(B.approved_sheet()) if c[3]}
    built, problems = [], []
    for cls, times in SHEETS:
        im, rows, probs, anc = check(cls, allowed)
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
            print('   f%d  black %.1f%%  colours %2d  rows %d..%d  %s' % (
                i, 100 * st['black'], ncol, bb[1], bb[3], '  '.join('%s %s' % kv for kv in a.items())))
        print('   sheet: colours %d, black %.1f%%' % (sheet['colours'], 100 * sheet['black']))
        status |= 1 if rt else 0
    boxes = [body_box(f) for f in mf_recover.Recover.figs()]
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes)
    y1 = max(b[3] for b in boxes)
    print('BODY_BOX (recover, spikes excluded, all 4 frames): Rect2(%d, %d, %d, %d)' % (x0, y0, x1 - x0 + 1, y1 - y0 + 1))
    print('written to', out_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
