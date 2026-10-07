"""Write the player's combo sheet, the PNG with its .aseprite beside it, after checking every cell.
The output folder is required; a bare run prints this and writes nothing:

    python combo_export.py <out_dir>                # write both files into that folder
    python combo_export.py <out_dir> --overwrite    # the same, replacing files already there

It only ever writes these two names:
    player_combo_sheet.png, player_combo_sheet.aseprite
        8 columns x 4 rows of 32x32 (256x128). Rows DOWN, UP, LEFT, RIGHT (PlayerScript.Facing order);
        columns 0-3 hit 2 (guard, chamber, travel, extension), columns 4-7 hit 3 (guard, chamber,
        drive, extension). The .aseprite is the same single image with a 32x32 grid set on it.

Nothing is written unless every cell passes combo_frames' checks: only his seven colours, alpha 0 or
255, one piece, no lone texels, no pinholes but his own neck notches, the head texel for texel his own,
the shoes on exactly hit 1's pixels, soles on row 28, and LEFT the exact mirror of RIGHT. Both files
are built in a temp folder and moved in only after the .aseprite re-exports to exactly the PNG's pixels
(imgdiff.pixel_diff); the round trip is checked again where they land.

Prints each cell's bounding box and colour count, and the fist tip of every extension frame (hits 1, 2
and 3) in cell texels and in game pixels from the player's origin (the Sprite2D is centred on the
CharacterBody2D, which is scaled 3x).
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
import combo_frames as F  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
NAME = 'player_combo_sheet'
SCALE = 3                                           # the player's CharacterBody2D scale
LUA = '''local spr = app.open(app.params["png"])
spr.gridBounds = Rectangle(0, 0, 32, 32)
spr:saveAs(app.params["out"])
spr:close()
'''


def flat(im):
    get = getattr(im, 'get_flattened_data', None)   # Pillow 12 renamed getdata
    return list(get() if get else im.getdata())


def check(sheet):
    problems = F.syntax_problems()
    if problems:
        return problems
    for facing in F.FACINGS:
        for c in range(8):
            problems += F.cell_problems(facing, c)
    data = flat(sheet)
    if {d for d in data if d[3]} - set(F.PAL.values()):
        problems.append('colours outside his seven')
    if any(0 < d[3] < 255 for d in data):
        problems.append('semi-transparent texels')
    if sheet.size != (F.W * 8, F.H * 4):
        problems.append('sheet is %dx%d, not 256x128' % sheet.size)
    left = sheet.crop((0, F.H * 2, sheet.width, F.H * 3))
    right = sheet.crop((0, F.H * 3, sheet.width, F.H * 4))
    for c in range(8):
        a = left.crop((c * F.W, 0, c * F.W + F.W, F.H))
        b = right.crop((c * F.W, 0, c * F.W + F.W, F.H)).transpose(Image.FLIP_LEFT_RIGHT)
        d = pixel_diff(a, b)
        if d:
            problems.append('LEFT col %d is not RIGHT col %d mirrored: %s' % (c, c, d))
    return problems


def aseprite(*args):
    subprocess.run([ASEPRITE, '-b'] + list(args), check=True, capture_output=True)


def write_sheet(im, out_dir, overwrite):
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    if not overwrite:
        there = [p for p in (png, ase) if os.path.exists(p)]
        if there:
            raise SystemExit('refused: %s already there (pass --overwrite to replace)' % ', '.join(there))
    tmp = tempfile.mkdtemp(prefix='player_combo_')
    try:
        tmp_png = os.path.join(tmp, NAME + '.png')
        tmp_ase = os.path.join(tmp, NAME + '.aseprite')
        lua = os.path.join(tmp, 'grid.lua')
        with open(lua, 'w') as f:
            f.write(LUA)
        im.save(tmp_png)
        aseprite('--script-param', 'png=' + tmp_png, '--script-param', 'out=' + tmp_ase, '--script', lua)
        back = os.path.join(tmp, 'rt.png')
        aseprite(tmp_ase, '--save-as', back)
        with Image.open(tmp_png) as a, Image.open(back) as b:
            d = pixel_diff(a, b)
        if d:
            raise SystemExit('%s: the .aseprite does not round-trip: %s' % (NAME, d))
        os.makedirs(out_dir, exist_ok=True)
        os.replace(tmp_png, png)
        os.replace(tmp_ase, ase)
        back2 = os.path.join(tmp, 'rt2.png')
        aseprite(ase, '--save-as', back2)
        with Image.open(png) as a, Image.open(back2) as b:
            rt = pixel_diff(a, b)
        return png, ase, rt
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def game_px(p):
    """A cell texel's centre in game pixels from the player's origin."""
    return ((p[0] + 0.5 - F.W / 2) * SCALE, (p[1] + 0.5 - F.H / 2) * SCALE)


def report(sheet):
    print('%s  %dx%d: 8 columns x 4 rows of 32x32; colours %d' % (
        NAME, sheet.width, sheet.height, len({d for d in flat(sheet) if d[3]})))
    for facing in F.FACINGS:
        print('  %s' % facing)
        for c in range(8):
            px = F.px_of(F.FRAMES[facing][c])
            xs = [x for x, y in px]
            ys = [y for x, y in px]
            print('    col %d  %-20s bbox (%2d,%2d)-(%2d,%2d)  colours %d' % (
                c, F.COLUMNS[c], min(xs), min(ys), max(xs), max(ys), len(set(px.values()))))
    print('  fist tips on the extension frames (cell texel; game px from the player origin at scale 3):')
    for r, facing in enumerate(F.FACINGS):
        tips = [('hit 1 (4-dir col 8)', F.tip_of(F.image_px(F.base_cell(r, 8)), facing)),
                ('hit 2 (col 3)', F.fist_tip(facing, 3)),
                ('hit 3 (col 7)', F.fist_tip(facing, 7))]
        for name, ((x, y), (e0, e1)) in tips:
            gx, gy = game_px((x, y))
            axis = 'x' if facing in ('DOWN', 'UP') else 'y'
            print('    %-5s %-20s (%2d,%2d)  leading edge %s %d-%d   %+6.1f,%+6.1f px' % (
                facing, name, x, y, axis, e0, e1, gx, gy))


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    if len(args) != 1 or set(argv) - set(args) - {'--overwrite'}:
        print(__doc__)
        return 2
    out_dir = os.path.abspath(args[0])
    sheet = F.sheet_image()
    problems = check(sheet)
    if problems:
        print('NOT WRITTEN, problems:')
        for p in problems:
            print('  ' + p)
        return 1
    png, ase, rt = write_sheet(sheet, out_dir, '--overwrite' in argv)
    print('%s\n%s\n  .aseprite round trip: %s' % (png, ase, rt or 'identical'))
    report(sheet)
    return 1 if rt else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
