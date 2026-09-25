"""Write Matt's Glass Row / Deafening Yell sheets and the player's Glass Row poses, each PNG with its
.aseprite beside it, after checking every frame. A bare run writes nothing:

    python mg_export.py <scratch_dir>    # write all eight files into that one folder, for checking
    python mg_export.py --ship           # Matt's three into Assets/Characters/Matt/,
                                         # the player's into Assets/Characters/MainPlayer/

It only ever writes these names (.png and .aseprite):
    matt_stomp     4 x 96x96   0.15, 0.30, 0.08, hold
    matt_fury      4 x 96x96   0.08 loop
    matt_yell_up   5 x 96x96   0.25, 0.25, then f2-4 loop at 0.06
    player_glass_row  18 x 4 cells of 32x32 (576x128), rows in player_4dir_sheet.png's order
                   (DOWN, UP, LEFT, RIGHT): row 1 (UP) is drawn, rows 0, 2 and 3 are copies of it

Matt, per frame, as the approved sets: 96x96, feet on row 95, top at row 1 or lower, only the
approved 41 colours, pure black, no semi-alpha, a clean audit (effects exempt: the fury's steam),
black 24.1-26.1%.
The player, per cell, in his own style: only his seven colours, pure black, no semi-alpha, one piece
(no transparent row splitting the body), no pinholes but the idle's own neck notches, no lone
texels, soles on row 28 (the airborne glass frames: 27 for the jolt, 25 for the hop).

Prints every Matt frame's anchors (crest_top, crown, mouth; slam_foot on the slam frames; the
yell_up mouth is the ring centre) and every player column's sole row and head centre.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mg_base as M  # noqa: E402
from mg_base import B, F, G  # noqa: E402
import mg_matt as MM  # noqa: E402
import mg_faces as MF  # noqa: E402
import mg_player as P  # noqa: E402
import mi_anchors as AN  # noqa: E402
from PIL import Image  # noqa: E402

BLACK = (0.241, 0.261)
MATT_SHEETS = [
    ('matt_stomp', MM.stomp_figs, '0.15, 0.30, 0.08, hold', {2: 0}),
    ('matt_fury', MM.fury_figs, '0.08 loop', {1: 0, 3: 1}),
    ('matt_yell_up', MM.yell_up_figs, '0.25, 0.25, then f2-4 loop at 0.06', {}),
]
PLAYER_NAME = 'player_glass_row'
SOLE_ROW = {16: 27, 17: 25}          # the rest stand on row 28, as the 4-dir UP idle


def box_centre(pts):
    xs = [x for x, y in pts]
    ys = [y for x, y in pts]
    return ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)


def mouth(f):
    """The mouth centre. The tipped-back faces keep their mouth lower in the map than the rig's
    faces do, so they are measured on their own rows: the yell's open mouth (map rows 8-19) and the
    shut lips of the breath held (map row 8, the lip line)."""
    rows = f.face[0] if f.face else None
    if rows is MF.YELL_UP or rows is MF.TIP_BACK:
        fp, (dx, dy) = AN.face_pixels(f)
        if rows is MF.YELL_UP:
            pts = [p for p, k in fp.items() if k in AN.MOUTH_KEYS and G.Y0 + 8 + dy <= p[1] <= G.Y0 + 19 + dy]
        else:
            pts = [p for p, k in fp.items() if k == 'k' and p[1] == G.Y0 + 8 + dy and 38 + dx <= p[0] <= 58 + dx]
        return box_centre(pts)
    return AN.mouth(f)


def sole_centre(px, side):
    """The centre of one foot's sole: its run on row 95 (side 0 = screen-left foot)."""
    xs = sorted(x for (x, y) in px if y == 95 and ((x < 48) if side == 0 else (x > 48)))
    return ((xs[0] + xs[-1]) // 2, 95)


def matt_anchors(f, px, slam_side):
    top = min(y for (x, y) in px)
    tx = sorted(x for (x, y) in px if y == top)
    P_ = f.pose()
    out = {'crest_top': (tx[len(tx) // 2], top),
           'crown': (48 + f.head[0], 16 + f.head[1] + P_.head_dy),
           'mouth': mouth(f)}
    if slam_side is not None:
        out['slam_foot'] = sole_centre(px, slam_side)
    return out


def check_matt(name, figs_fn, allowed, slams):
    problems, rows, frames = [], [], []
    for i, f in enumerate(figs_fn()):
        px = F.px_of(f)
        frames.append(px)
        im = B.image(px)
        st = B.stats(im)
        cols = {c for c in B.flat(im) if c[3]}
        a = B.audit(px, f.fx)
        x0, y0, x1, y1 = B.bbox(px)
        tag = '%s f%d' % (name, i)
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
        if not (BLACK[0] <= st['black'] <= BLACK[1]):
            problems.append('%s: black %.1f%% outside 24.1-26.1%%' % (tag, 100 * st['black']))
        rows.append((i, st, len(cols), (x0, y0, x1, y1), matt_anchors(f, px, slams.get(i))))
    return B.strip(frames), rows, problems


def check_player():
    problems, rows = [], []
    sheet = Image.new('RGBA', (32 * 18, 32 * 4), (0, 0, 0, 0))
    allowed = set(P.PAL.values())
    for c, name, px, timing in P.columns():
        im = P.image(px)
        tag = '%s col %d (%s)' % (PLAYER_NAME, c, name)
        data = [d for d in B.flat(im) if d[3]]
        cols = set(data)
        if cols - allowed:
            problems.append('%s: colours outside his seven' % tag)
        if any(0 < d[3] < 255 for d in B.flat(im)):
            problems.append('%s: semi-transparent pixels' % tag)
        a = P.audit(px)
        if any(a.values()):
            problems.append('%s: %s' % (tag, {k: v for k, v in a.items() if v}))
        xs = [x for x, y in px]
        ys = [y for x, y in px]
        sole = max(ys)
        if sole != SOLE_ROW.get(c, 28):
            problems.append('%s: soles on row %d, not %d' % (tag, sole, SOLE_ROW.get(c, 28)))
        if min(ys) < 0 or max(xs) > 31 or min(xs) < 0:
            problems.append('%s: outside its cell' % tag)
        hair = sorted(x for (x, y) in px if px[(x, y)] == 'k' and y == min(yy for (xx, yy), k in px.items() if k == 'k'))
        head_centre = (hair[0] + hair[-1]) / 2
        for r in range(4):
            sheet.alpha_composite(im, (32 * c, 32 * r))
        rows.append((c, name, timing, P.black(px), len(cols), (min(xs), min(ys), max(xs), max(ys)), sole, head_centre))
    # rows 0, 2 and 3 must be exact copies of row 1
    r1 = sheet.crop((0, 32, 576, 64))
    for r in (0, 2, 3):
        d = B.pixel_diff(r1, sheet.crop((0, 32 * r, 576, 32 * r + 32)))
        if d:
            problems.append('%s: row %d is not a copy of row 1: %s' % (PLAYER_NAME, r, d))
    return sheet, rows, problems


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    ship = argv[0] == '--ship'
    matt_dir = B.ASSETS if ship else os.path.abspath(argv[0])
    player_dir = M.PLAYER_DIR if ship else os.path.abspath(argv[0])
    allowed = {c for c in B.flat(B.approved_sheet()) if c[3]}
    assert len(allowed) == 41, len(allowed)
    built, problems = [], []
    for name, fn, times, slams in MATT_SHEETS:
        im, rows, probs = check_matt(name, fn, allowed, slams)
        built.append((name, times, im, rows))
        problems += probs
    psheet, prows, pprobs = check_player()
    problems += pprobs
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    status = 0
    for name, times, im, rows in built:
        png, ase, rt = B.write_sheet(name, im, matt_dir)
        sheet = B.stats(im)
        print('%s  %dx%d, %d frames, %s' % (os.path.basename(png), im.width, im.height, len(rows), times))
        print('   .aseprite round trip:', rt or 'identical')
        for (i, st, ncol, bb, anc) in rows:
            print('   f%d  black %.1f%%  colours %2d  bbox %s  %s' % (
                i, 100 * st['black'], ncol, bb, '  '.join('%s %s' % kv for kv in anc.items())))
        print('   sheet: colours %d, black %.1f%%' % (sheet['colours'], 100 * sheet['black']))
        status |= 1 if rt else 0
    png, ase, rt = B.write_sheet(PLAYER_NAME, psheet, player_dir)
    print('%s  %dx%d, 18 columns x 4 rows of 32x32 (row 1 drawn; rows 0, 2, 3 copies)' % (
        os.path.basename(png), psheet.width, psheet.height))
    print('   .aseprite round trip:', rt or 'identical')
    for (c, name, timing, blk, ncol, bb, sole, hc) in prows:
        print('   col %2d  %-9s %-10s black %.1f%%  colours %d  bbox %s  soles row %d  head centre x %.1f' % (
            c, name, timing, 100 * blk, ncol, bb, sole, hc))
    status |= 1 if rt else 0
    print('written to', matt_dir, 'and', player_dir)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
