"""Write the player's 2x brawl sheets (PLAN_BRAWL.md section 7), each PNG with its .aseprite beside it,
after checking every cell. A bare run writes nothing:

    python gb_export2x.py placeholder <scratch_dir>       # into that folder, for checking
    python gb_export2x.py placeholder --ship              # into Assets/Characters/MainPlayer/
    python gb_export2x.py placeholder --ship --replace    # the same, over an existing sheet
    python gb_export2x.py native <scratch_dir>            # the native 2x redraw, same file name
    python gb_export2x.py native --ship --replace         # ...over the shipped placeholder
    python gb_export2x.py uppercut <scratch_dir>          # the back-view uppercut and its _super
    python gb_export2x.py uppercut --ship [--replace]

A <scratch_dir> inside the project's Assets/ is refused (realpath, so 8.3 names too); --ship never
overwrites an existing file without --replace.

Targets and the only names each writes (.png and .aseprite):
    placeholder   player_final_brawl_2x: 10 x 4 cells of 64x96 (640x384), the approved 1x
                  player_final_brawl poses as an EXACT nearest-neighbour x2 about the ground line
                  (gb_player2x), every row the same back view. Checked texel for texel against the 1x.

Every cell: only his seven colours, pure black, no semi-alpha, the soles' bottom edge on y 61
(sole texels on rows 59-60), rows 0, 2 and 3 copies of row 1.

    native        player_final_brawl_2x again, from the native 2x redraw (gb_native2x): the same
                  contract, checked cell by cell (his seven colours, no semi-alpha, a clean audit, soles
                  on rows 59-60 with their bottom edge on y 61, rows 0/2/3 copies of row 1) and against
                  the contract's anchors: each column's head centre, the guard's head top on row 12,
                  the parry contacts (31,9) and (31,11).

    uppercut      player_final_brawl_uppercut and player_final_brawl_uppercut_super: 10 frames of
                  64x128 in a row (640x128), Sprite2D offset (0,-16), ground line y 93 (gb_uppercut2x).
                  Checked: his seven colours plus player_uppercut.png's six effect colours only, no
                  semi-alpha, every body one clean piece (the energy may float), each frame's feet at
                  its planned height, the contact glove's top-centre at (32, 43) (0,-111 px) and the
                  apex glove's at (32, 23); the _super sheet the same pixels with the energy recoloured
                  exactly as player_uppercut_super.png recolours player_uppercut.png.
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
import gb_player2x as G2  # noqa: E402
import gb_uppercut2x as U  # noqa: E402
import gb_native2x as N  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
ASSETS = os.path.join(G.ROOT, 'Assets')
SHIP_DIR = G.PLAYER_DIR
TARGETS = {'placeholder': ['player_final_brawl_2x'],
           'native': ['player_final_brawl_2x'],
           'uppercut': ['player_final_brawl_uppercut', 'player_final_brawl_uppercut_super']}


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return path == root or path.startswith(root + os.sep)


def common_problems(tag, im):
    problems = []
    data = flat(im)
    cols = {d for d in data if d[3]}
    if cols - set(G.PAL.values()):
        problems.append('%s: colours outside his seven' % tag)
    if any(0 < d[3] < 255 for d in data):
        problems.append('%s: semi-transparent pixels' % tag)
    return problems


def build_placeholder():
    problems = []
    sheet = Image.new('RGBA', (G2.W2 * len(G.FRAMES), G2.H2 * 4), (0, 0, 0, 0))
    cells = G2.placeholder_cells()
    for i, (name, px) in enumerate(cells):
        tag = 'player_final_brawl_2x col %d (%s)' % (i, name)
        # exact x2 of the approved 1x cell, and nothing else
        one = G.g(G.FRAMES[i][1])
        want = G2.x2(one)
        if px != want:
            problems.append('%s: not the exact x2 of the 1x cell' % tag)
        for (x, y), k in one.items():
            bx, by = G2.to2x(x, y)
            if {px.get((bx + dx, by + dy)) for dx in (0, 1) for dy in (0, 1)} != {k}:
                problems.append('%s: block at 1x (%d,%d) is not uniform %s' % (tag, x, y, k))
                break
        im = G2.image2x(px)
        problems += common_problems(tag, im)
        low = max(y for x, y in px)
        if low != G2.GROUND - 1:
            problems.append('%s: lowest texel on row %d, not %d' % (tag, low, G2.GROUND - 1))
        for r in range(4):
            sheet.alpha_composite(im, (G2.W2 * i, G2.H2 * r))
    up_row = sheet.crop((0, G2.H2 * G.UP, sheet.width, G2.H2 * G.UP + G2.H2))
    for r in (G.DOWN, G.LEFT, G.RIGHT):
        d = pixel_diff(up_row, sheet.crop((0, G2.H2 * r, sheet.width, G2.H2 * r + G2.H2)))
        if d:
            problems.append('player_final_brawl_2x: row %d is not a copy of row 1: %s' % (r, d))
    # and the whole sheet, downsampled back, must be the approved 1x sheet's cells re-registered
    return {'player_final_brawl_2x': sheet}, cells, problems


def build_native():
    problems = []
    sheet = Image.new('RGBA', (G2.W2 * len(N.CELLS), G2.H2 * 4), (0, 0, 0, 0))
    cells = []
    for i, (name, fn) in enumerate(N.CELLS):
        px = fn()
        tag = 'player_final_brawl_2x (native) col %d (%s)' % (i, name)
        im = G2.image2x(px)
        problems += common_problems(tag, im)
        a = {k: v for k, v in N.audit2x(px).items() if v}
        if a:
            problems.append('%s: %s' % (tag, a))
        low = max(y for x, y in px)
        if low != G2.GROUND - 1:
            problems.append('%s: lowest texel on row %d, not %d' % (tag, low, G2.GROUND - 1))
        if name == 'parry':
            blue = [(x, y) for (x, y), k in px.items() if k in 'BLD' and y < 23]
            got = ((min(x for x, y in blue) + max(x for x, y in blue) + 1) / 2.0, min(y for x, y in blue))
            if got != N.PARRY_CONTACTS[i]:
                problems.append('%s: parry contact %s, not %s' % (tag, got, N.PARRY_CONTACTS[i]))
        for r in range(4):
            sheet.alpha_composite(im, (G2.W2 * i, G2.H2 * r))
        cells.append((name, px))
    g = N.guard_px()
    core = [(x, y) for (x, y), k in g.items() if 26 <= x <= 35 and 13 <= y <= 24]
    centre = ((min(x for x, y in core) + max(x for x, y in core) + 1) / 2.0,
              (min(y for x, y in core) + max(y for x, y in core) + 1) / 2.0)
    if centre != (31.0, 19.0):
        problems.append('the guard head core centre is %s, not (31, 19)' % (centre,))
    if min(y for x, y in g) != 12:
        problems.append('the guard head top is row %d, not 12' % min(y for x, y in g))
    up_row = sheet.crop((0, G2.H2 * G.UP, sheet.width, G2.H2 * G.UP + G2.H2))
    for r in (G.DOWN, G.LEFT, G.RIGHT):
        d = pixel_diff(up_row, sheet.crop((0, G2.H2 * r, sheet.width, G2.H2 * r + G2.H2)))
        if d:
            problems.append('player_final_brawl_2x: row %d is not a copy of row 1: %s' % (r, d))
    return {'player_final_brawl_2x': sheet}, cells, problems


def report_native(sheets, cells):
    sheet = sheets['player_final_brawl_2x']
    d = [p for p in flat(sheet) if p[3]]
    print('player_final_brawl_2x (native)  %dx%d: 10 x 4 cells of 64x96; every row the back view; colours %d, '
          'black %.1f%%' % (sheet.width, sheet.height, len(set(d)),
                            100.0 * sum(1 for p in d if p[:3] == (0, 0, 0)) / len(d)))
    for i, (name, px) in enumerate(cells):
        hx, hy = N.HEAD_CENTRES[i]
        line = '   col %d  %-10s head centre (%d,%d) = %+.0f,%+.0f px   top row %d   soles rows 59-60 (ground 61)' % (
            i, name, hx, hy, *G2.px_from_origin(hx, hy), min(y for x, y in px))
        if i in N.PARRY_CONTACTS:
            cx, cy = N.PARRY_CONTACTS[i]
            line += '   parry contact (%d,%d) = %+.0f,%+.0f px' % (cx, cy, *G2.px_from_origin(cx, cy))
        print(line)


def build_uppercut():
    problems = []
    sheet = Image.new('RGBA', (U.W * 10, U.H), (0, 0, 0, 0))
    sup = Image.new('RGBA', (U.W * 10, U.H), (0, 0, 0, 0))
    allowed = set(U.PAL.values())
    frames = U.frames()
    bodies = U.bodies()
    for i, (role, px) in enumerate(frames):
        tag = 'player_final_brawl_uppercut f%d (%s)' % (i, role)
        im = U.image(px)
        data = flat(im)
        if {d for d in data if d[3]} - allowed:
            problems.append('%s: colours outside his seven and the six effect colours' % tag)
        if any(0 < d[3] < 255 for d in data):
            problems.append('%s: semi-transparent pixels' % tag)
        a = {k: v for k, v in N.audit2x(bodies[i][1]).items() if k != 'outside' and v}
        if a:
            problems.append('%s: body %s' % (tag, a))
        h = U.POSES[i][1]
        low = max(y for (x, y), k in bodies[i][1].items())
        if low != U.GROUND - 1 - h:
            problems.append('%s: feet on row %d, not %d (%d off the mat)' % (tag, low, U.GROUND - 1 - h, h))
        sheet.alpha_composite(im, (U.W * i, 0))
        sup.alpha_composite(U.image(px, U.PAL_SUPER), (U.W * i, 0))
    box5, (cx5, top5) = U.glove_box(5)
    if (cx5, top5) != (32.0, 43):
        problems.append('contact glove top-centre is (%.1f,%d), not (32,43)' % (cx5, top5))
    box7, (cx7, top7) = U.glove_box(7)
    if (cx7, top7) != (32.0, 23):
        problems.append('apex glove top-centre is (%.1f,%d), not (32,23)' % (cx7, top7))
    # the _super sheet is the normal one with exactly the energy recoloured
    recolour = {U.FX[k]: U.SUPER[k] for k in U.FX}
    for pa, pb in zip(flat(sheet), flat(sup)):
        if pa[3] != pb[3] or (pa[3] and recolour.get(pa, pa) != pb):
            problems.append('the _super sheet is not the energy recolour of the normal sheet')
            break
    return {'player_final_brawl_uppercut': sheet, 'player_final_brawl_uppercut_super': sup}, frames, problems


def report_uppercut(sheets, frames):
    for name, im in sheets.items():
        d = [p for p in flat(im) if p[3]]
        print('%s  %dx%d: 10 frames of 64x128, offset (0,-16), ground y 93; colours %d, black %.1f%%' % (
            name, im.width, im.height, len(set(d)), 100.0 * sum(1 for p in d if p[:3] == (0, 0, 0)) / len(d)))
    for i, (role, px) in enumerate(frames):
        box, (cx, top) = U.glove_box(i)
        h = U.POSES[i][1]
        print('   f%d %-8s glove texels x %d-%d rows %d-%d, top-centre (%.0f,%d) = %+.0f,%+.0f px, %d up; feet %d off the mat' % (
            i, role, box[0], box[2], box[1], box[3], cx, top, *U.px_from_origin(cx, top), U.GROUND - top, h))


def write_sheet(name, im, out_dir):
    tmp = tempfile.mkdtemp(prefix='greyson_player2x_')
    try:
        tmp_png = os.path.join(tmp, name + '.png')
        tmp_ase = os.path.join(tmp, name + '.aseprite')
        im.save(tmp_png)
        subprocess.run([ASEPRITE, '-b', tmp_png, '--save-as', tmp_ase], check=True, capture_output=True)
        back = os.path.join(tmp, 'rt.png')
        subprocess.run([ASEPRITE, '-b', tmp_ase, '--save-as', back], check=True, capture_output=True)
        with Image.open(tmp_png) as a, Image.open(back) as b:
            d = pixel_diff(a, b)
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
        os.makedirs(out_dir, exist_ok=True)
        png = os.path.join(out_dir, name + '.png')
        ase = os.path.join(out_dir, name + '.aseprite')
        os.replace(tmp_png, png)
        os.replace(tmp_ase, ase)
        back2 = os.path.join(tmp, 'rt2.png')
        subprocess.run([ASEPRITE, '-b', ase, '--save-as', back2], check=True, capture_output=True)
        with Image.open(png) as a, Image.open(back2) as b:
            rt = pixel_diff(a, b)
        return png, ase, rt
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def report_placeholder(sheets, cells):
    sheet = sheets['player_final_brawl_2x']
    d = [p for p in flat(sheet) if p[3]]
    print('player_final_brawl_2x  %dx%d: 10 x 4 cells of 64x96; every row the back view; colours %d, '
          'black %.1f%%' % (sheet.width, sheet.height, len(set(d)),
                            100.0 * sum(1 for p in d if p[:3] == (0, 0, 0)) / len(d)))
    for i, (name, px) in enumerate(cells):
        path, col, row, x0, y0, x1, y1, dx, dy = G.HEADS[i]
        # the 1x head core box (continuous) mapped to 2x
        hx = (x0 + dx + x1 + dx + 1) / 2.0 * 2 + G2.X0
        hy = (y0 + dy + y1 + dy + 1) / 2.0 * 2 + G2.Y0
        top = min(y for x, y in px)
        line = '   col %d  %-10s head centre (%.0f,%.0f) = %+.0f,%+.0f px   top row %d   soles rows 59-60 (ground 61)' % (
            i, name, hx, hy, *G2.px_from_origin(hx, hy), top)
        if name == 'parry':
            blue = [(x, y) for (x, y), k in px.items() if k in 'BLD' and y < 23]
            gt = min(y for x, y in blue)
            gx = (min(x for x, y in blue) + max(x for x, y in blue) + 1) / 2.0
            line += '   parry contact (%.0f,%d) = %+.0f,%+.0f px' % (gx, gt, *G2.px_from_origin(gx, gt))
        print(line)


def main(argv):
    if not argv or argv[0] not in TARGETS or len(argv) < 2:
        print(__doc__)
        return 2
    target = argv[0]
    replace = '--replace' in argv
    args = [a for a in argv[1:] if a != '--replace']
    if args[0] == '--ship':
        out_dir = SHIP_DIR
        existing = [n + ext for n in TARGETS[target] for ext in ('.png', '.aseprite')
                    if os.path.exists(os.path.join(out_dir, n + ext))]
        if existing and not replace:
            print('refused: %s already in %s; pass --replace to overwrite' % (existing, out_dir))
            return 2
    else:
        out_dir = os.path.abspath(args[0])
        if _under(out_dir, ASSETS):
            print('refused: %s is inside Assets/. Only --ship writes there.' % out_dir)
            return 2
    if target == 'placeholder':
        sheets, cells, problems = build_placeholder()
    elif target == 'native':
        sheets, cells, problems = build_native()
    else:
        sheets, cells, problems = build_uppercut()
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    status = 0
    for name, im in sheets.items():
        png, ase, rt = write_sheet(name, im, out_dir)
        print('%s -> %s (+ .aseprite), round trip: %s' % (name, png, rt or 'identical'))
        status |= 1 if rt else 0
    if target == 'placeholder':
        report_placeholder(sheets, cells)
    elif target == 'native':
        report_native(sheets, cells)
    else:
        report_uppercut(sheets, cells)
    return status


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
