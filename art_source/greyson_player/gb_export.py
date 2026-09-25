"""Write the player's Greyson final-phase brawl sheet, the PNG with its .aseprite beside it, after
checking every cell. A bare run writes nothing:

    python gb_export.py <scratch_dir>          # write it into that one folder, for checking
                                               # (refused if the folder is inside the project's Assets/)
    python gb_export.py --ship                 # write it into Assets/Characters/MainPlayer/ (only when
                                               # neither file exists yet)
    python gb_export.py --ship --replace       # the same, over an existing sheet

It only ever writes these two names:
    player_final_brawl.png, player_final_brawl.aseprite
        10 columns x 4 rows of 32x32 (320x128), rows in player_4dir_sheet.png's order (DOWN, UP,
        LEFT, RIGHT). Row 1 (UP, the back view) is drawn; rows 0, 2 and 3 are copies of it, as
        player_glass_row.png and player_sumo_push.png do.

Every cell, in the player's own style (see art_source/danny_player/dp_player.py): only his seven
colours, pure black, no semi-alpha, one piece, no pinholes but the idle's own neck notches, no lone
texels, the head texel for texel his own (gb_player.HEADS), and BOTH FEET ON THE SAME TEXELS IN
EVERY CELL (he is walled in: left shoe x 11-12 rows 26-27, right shoe x 18-21 rows 27-28).

Prints every cell's black share, colour count, bounding box, its head centre (where a punch lands)
and, on the parry, the gloves' top edge (where the straight meets them), in cell texels and in game
pixels from the player's origin (the Sprite2D is centred on the CharacterBody2D, which is scaled 3x).
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
import gb_player as G  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.join(G.ROOT, 'Assets')
SHIP_DIR = G.PLAYER_DIR
NAME = 'player_final_brawl'
W = H = 32
SCALE = 3
TIMING = ['loop 0,1 @ 0.16', 'loop 0,1 @ 0.16', 'slip L: 2,3,2 @ 0.04, hold, 0.06', 'held while the hook passes',
          'slip R: 4,5,4 @ 0.04, hold, 0.06', 'held while the hook passes', 'parry: 6,7 @ 0.05, 0.12',
          'then back to 0', 'hit: 8,9 @ 0.10, 0.25', 'then back to 0']
FEET = {(11, 26), (12, 26), (11, 27), (12, 27), (18, 27), (19, 27), (20, 27),
        (18, 28), (19, 28), (20, 28), (21, 28)}


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def head_problems(px, src):
    path, col, row, x0, y0, x1, y1, dx, dy = src
    ref = G.from_sheet(path, col, row)
    return [(x, y) for (x, y), k in ref.items()
            if x0 <= x <= x1 and y0 <= y <= y1 and px.get((x + dx, y + dy)) != k]


def head_centre(src):
    """The centre of the head's core box where this cell puts it: texel coords and px from origin."""
    path, col, row, x0, y0, x1, y1, dx, dy = src
    cx = (x0 + x1 + 1) / 2.0 + dx
    cy = (y0 + y1 + 1) / 2.0 + dy
    return (cx, cy), ((cx - W / 2) * SCALE, (cy - H / 2) * SCALE)


def check_cell(i, name, px):
    tag = '%s col %d (%s)' % (NAME, i, name)
    problems = []
    im = G.image(px)
    data = flat(im)
    cols = {d for d in data if d[3]}
    if cols - set(G.PAL.values()):
        problems.append('%s: colours outside his seven' % tag)
    if any(0 < d[3] < 255 for d in data):
        problems.append('%s: semi-transparent pixels' % tag)
    if {c for c in cols if c[:3] == (0, 0, 0)} - {(0, 0, 0, 255)}:
        problems.append('%s: impure black' % tag)
    a = G.audit(px)
    if any(a.values()):
        problems.append('%s: %s' % (tag, {k: v for k, v in a.items() if v}))
    feet = {p for p, k in px.items() if k == 'k' and p[1] >= 26}
    if feet != FEET:
        problems.append('%s: the feet are not where every other cell has them: %s' % (
            tag, sorted(feet ^ FEET)[:6]))
    bad = head_problems(px, G.HEADS[i])
    if bad:
        problems.append('%s: head differs from his own at %s' % (tag, bad[:6]))
    return im, problems


def build():
    problems = []
    sheet = Image.new('RGBA', (W * len(G.FRAMES), H * 4), (0, 0, 0, 0))
    cells = []
    for i, (name, grid) in enumerate(G.FRAMES):
        px = G.g(grid)
        im, probs = check_cell(i, name, px)
        problems += probs
        for r in range(4):
            sheet.alpha_composite(im, (W * i, H * r))
        cells.append((i, name, px))
    up_row = sheet.crop((0, H * G.UP, sheet.width, H * G.UP + H))
    for r in (G.DOWN, G.LEFT, G.RIGHT):
        d = pixel_diff(up_row, sheet.crop((0, H * r, sheet.width, H * r + H)))
        if d:
            problems.append('%s: row %d is not a copy of row 1: %s' % (NAME, r, d))
    return sheet, cells, problems


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root + os.sep)


def write_sheet(im, out_dir):
    """<out_dir>/<NAME>.png and .aseprite, built in a temp folder and moved in with os.replace; the
    .aseprite must re-export to exactly the PNG's pixels (imgdiff.pixel_diff) before anything moves,
    and again where it landed."""
    tmp = tempfile.mkdtemp(prefix='greyson_player_')
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
    print('%s  %dx%d: 10 columns x 4 rows of 32x32; row 1 (UP) drawn, rows 0/2/3 copies; sheet colours %d, '
          'black %.1f%%' % (NAME, sheet.width, sheet.height, len(set(d)),
                            100.0 * sum(1 for p in d if p[:3] == (0, 0, 0)) / len(d)))
    for i, name, px in cells:
        xs = [x for x, y in px]
        ys = [y for x, y in px]
        (hx, hy), (hpx, hpy) = head_centre(G.HEADS[i])
        print('   col %d  %-10s %-34s black %4.1f%%  colours %d  bbox (%d,%d)-(%d,%d)  head centre (%.1f,%.1f) '
              '= %+.1f,%+.1f px' % (i, name, TIMING[i], 100 * G.black(px), len(set(px.values())),
                                    min(xs), min(ys), max(xs), max(ys), hx, hy, hpx, hpy))
        if name == 'parry':
            blue = [(x, y) for (x, y), k in px.items() if k in 'BLD' and y < 10]
            top = min(y for x, y in blue)
            gx0, gx1 = min(x for x, y in blue), max(x for x, y in blue)
            cx = (gx0 + gx1 + 1) / 2.0
            print('            gloves x %d-%d, top edge row %d: the straight meets them at %+.1f,%+.1f px' % (
                gx0, gx1, top, (cx - W / 2) * SCALE, (top - H / 2) * SCALE))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    replace = '--replace' in argv
    args = [a for a in argv if a != '--replace']
    if args[0] == '--ship':
        out_dir = SHIP_DIR
        existing = [f for f in (NAME + '.png', NAME + '.aseprite') if os.path.exists(os.path.join(out_dir, f))]
        if existing and not replace:
            print('refused: %s already in %s; pass --replace to overwrite' % (existing, out_dir))
            return 2
    else:
        out_dir = os.path.abspath(args[0])
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
