"""Write the player's sumo push sheet for Danny's fight, the PNG with its .aseprite beside it, after
checking every cell. A bare run writes nothing:

    python dp_export.py <scratch_dir>    # write it into that one folder, for checking
                                         # (refused if the folder is inside the project's Assets/)
    python dp_export.py --ship           # write it into Assets/Characters/MainPlayer/

It only ever writes these two names:
    player_sumo_push.png, player_sumo_push.aseprite
        8 columns x 4 rows of 32x32 (256x128), rows in player_4dir_sheet.png's order (DOWN, UP, LEFT,
        RIGHT). Row 1 (UP, the back view) is drawn; rows 0, 2 and 3 are copies of it, as
        player_glass_row.png does: the sumo is staged vertically (Danny at the top gate, the player
        below him facing up), so only the back view is ever wanted and no facing can show a wrong row.

Every cell, in the player's own style (measured off his shipped sheets, see dp_player): only his seven
colours, pure black, no semi-alpha, one piece, no pinholes but the idle's own neck notches, no lone
texels, the lowest texel on row 28 (the airborne launch: 26), and the head texel for texel his own
(the UP idle's, moved; on the last frame the DOWN idle's, flipped).

Prints every cell's black share, colour count, bounding box and lowest row, and every push frame's
glove contact points (the top edge of each glove, where it meets Danny's hands), in cell texels and in
game pixels from the player's origin (the Sprite2D is centred on the CharacterBody2D, scaled 3x).
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # art_source, for imgdiff
import dp_player as P  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.join(P.ROOT, 'Assets')
SHIP_DIR = P.PLAYER_DIR
W = H = 32
SCALE = 3                                           # the player's CharacterBody2D scale
NAME = 'player_sumo_push'

TIMING = ['0.20, then the strain loop', 'loop 1,2 @ 0.10', 'loop 1,2 @ 0.10', 'one-shot, hold',
          'loop 4,5 @ 0.08', 'loop 4,5 @ 0.08', 'one-shot 0.30', 'hold']
LOWEST = {6: 26}                                    # the launch is airborne; the rest reach row 28
# What the gloves are doing per column; a contact is reported only where they are on Danny's hands.
CONTACT = ['pre-contact: his guard, gloves either side of his head', 'ON DANNY', 'ON DANNY',
           'ON DANNY, driven through', 'ON DANNY, driven back a row', 'ON DANNY, driven back a row',
           'contact broken: flung off', None]

# Where each column's head came from. The UP idle's head is x 13-17, rows 4-9 (its two flying tail
# texels at x 11-12 are left out: an arm crosses them, or they whip elsewhere). The last frame's head is
# the DOWN idle's (x 13-17, rows 4-9) turned upside down by dp_player.ON_BACK_SOURCE_ROWS.
UP_HEAD_BOX = (13, 4, 17, 9)


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def head_problems(i, px):
    x0, y0, x1, y1 = UP_HEAD_BOX
    if P.PUSH_HEAD_ROW[i] is not None:
        ref = P.from_sheet(P.SHEET_4DIR, 0, P.UP)
        dy = P.PUSH_HEAD_ROW[i] - 4
        return [(x, y) for (x, y), k in ref.items()
                if x0 <= x <= x1 and y0 <= y <= y1 and px.get((x, y + dy)) != k]
    ref = P.from_sheet(P.SHEET_4DIR, 0, P.DOWN)
    to_row = {sy: y for y, sy in P.ON_BACK_SOURCE_ROWS.items()}
    return [(x, y) for (x, y), k in ref.items()
            if x0 <= x <= x1 and y0 <= y <= y1 and px.get((x, to_row[y])) != k]


def gloves(px):
    """The two gloves: the glove blue above the shorts' waistband (the row with L between two B's)."""
    waist = min(y for (x, y), k in px.items() if k == 'L' and y > 12 and
                px.get((x - 1, y)) == 'B' and px.get((x + 1, y)) == 'B')
    blue = [(x, y) for (x, y), k in px.items() if k in 'BLD' and y < waist]
    mid = sum(x for x, y in blue) / len(blue)
    return [p for p in blue if p[0] < mid], [p for p in blue if p[0] >= mid]


def contact(texels):
    """A glove's texel box, and the centre of its top edge in game px from the player's origin."""
    xs = [x for x, y in texels]
    ys = [y for x, y in texels]
    cx = (min(xs) + max(xs) + 1) / 2.0
    return (min(xs), min(ys), max(xs), max(ys)), ((cx - W / 2) * SCALE, (min(ys) - H / 2) * SCALE)


def check_cell(i, name, px):
    tag = '%s col %d (%s)' % (NAME, i, name)
    problems = []
    im = P.image(px)
    data = flat(im)
    cols = {d for d in data if d[3]}
    if cols - set(P.PAL.values()):
        problems.append('%s: colours outside his seven' % tag)
    if any(0 < d[3] < 255 for d in data):
        problems.append('%s: semi-transparent pixels' % tag)
    if {c for c in cols if c[:3] == (0, 0, 0)} - {(0, 0, 0, 255)}:
        problems.append('%s: impure black' % tag)
    a = P.audit(px)
    if any(a.values()):
        problems.append('%s: %s' % (tag, {k: v for k, v in a.items() if v}))
    if P.sole_row(px) != LOWEST.get(i, 28):
        problems.append('%s: lowest texel on row %d, not %d' % (tag, P.sole_row(px), LOWEST.get(i, 28)))
    bad = head_problems(i, px)
    if bad:
        problems.append('%s: head differs from his own at %s' % (tag, bad[:6]))
    return im, problems


def build():
    problems = []
    sheet = Image.new('RGBA', (W * len(P.PUSH), H * 4), (0, 0, 0, 0))
    cells = []
    for i, (name, grid) in enumerate(P.PUSH):
        px = P.g(grid)
        im, probs = check_cell(i, name, px)
        problems += probs
        for r in range(4):
            sheet.alpha_composite(im, (W * i, H * r))
        cells.append((i, name, px))
    up_row = sheet.crop((0, H * P.UP, sheet.width, H * P.UP + H))
    for r in (P.DOWN, P.LEFT, P.RIGHT):
        d = pixel_diff(up_row, sheet.crop((0, H * r, sheet.width, H * r + H)))
        if d:
            problems.append('%s: row %d is not a copy of row 1: %s' % (NAME, r, d))
    return sheet, cells, problems


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root + os.sep)


def write_sheet(im, out_dir):
    """<out_dir>/player_sumo_push.png and .aseprite, built in a temp folder and moved in with os.replace;
    the .aseprite must re-export to exactly the PNG's pixels (imgdiff.pixel_diff) before anything moves,
    and again where it landed."""
    tmp = tempfile.mkdtemp(prefix='danny_player_')
    try:
        tmp_png = os.path.join(tmp, NAME + '.png')
        tmp_ase = os.path.join(tmp, NAME + '.aseprite')
        im.save(tmp_png)
        subprocess.run([ASEPRITE, '-b', tmp_png, '--save-as', tmp_ase], check=True, capture_output=True)
        back = os.path.join(tmp, 'rt.png')
        subprocess.run([ASEPRITE, '-b', tmp_ase, '--save-as', back], check=True, capture_output=True)
        with Image.open(tmp_png) as a, Image.open(back) as b:
            d = pixel_diff(a, b)
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (NAME, d))
        os.makedirs(out_dir, exist_ok=True)
        png = os.path.join(out_dir, NAME + '.png')
        ase = os.path.join(out_dir, NAME + '.aseprite')
        os.replace(tmp_png, png)
        os.replace(tmp_ase, ase)
        back2 = os.path.join(tmp, 'rt2.png')
        subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
        with Image.open(png) as a, Image.open(back2) as b:
            rt = pixel_diff(a, b)
        return png, ase, rt
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def report(sheet, cells):
    d = [p for p in flat(sheet) if p[3]]
    print('%s  %dx%d: 8 columns x 4 rows of 32x32; row 1 (UP) drawn, rows 0/2/3 copies; sheet colours %d, '
          'black %.1f%%' % (NAME, sheet.width, sheet.height, len(set(d)),
                            100.0 * sum(1 for p in d if p[:3] == (0, 0, 0)) / len(d)))
    for i, name, px in cells:
        xs = [x for x, y in px]
        ys = [y for x, y in px]
        low = P.sole_row(px)
        lx = sorted(x for (x, y) in px if y == low)
        print('   col %d  %-9s %-28s black %4.1f%%  colours %d  bbox (%d,%d)-(%d,%d)  lowest row %d x %d-%d' % (
            i, name, TIMING[i], 100 * P.black(px), len(set(px.values())),
            min(xs), min(ys), max(xs), max(ys), low, lx[0], lx[-1]))
        if CONTACT[i] is None:
            print('            gloves: flung out flat on the canvas, no contact')
            continue
        lg, rg = gloves(px)
        (lb, lp), (rb, rp) = contact(lg), contact(rg)
        print('            gloves %s: L %s top-centre %+.1f,%+.1f px | R %s top-centre %+.1f,%+.1f px | '
              'mid %+.1f,%+.1f px' % (CONTACT[i], lb, lp[0], lp[1], rb, rp[0], rp[1],
                                      (lp[0] + rp[0]) / 2, (lp[1] + rp[1]) / 2))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == '--ship':
        out_dir = SHIP_DIR
    else:
        out_dir = os.path.abspath(argv[0])
        if _under(out_dir, ASSETS):
            print('refused: %s is inside Assets/. Only --ship writes there.' % out_dir)
            return 2
    sheet, cells, problems = build()
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    png, ase, rt = write_sheet(sheet, out_dir)
    print('%s -> %s (+ .aseprite), round trip: %s' % (NAME, png, rt or 'identical'))
    report(sheet, cells)
    return 1 if rt else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
