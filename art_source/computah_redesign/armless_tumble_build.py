"""computah_armless_tumble: render, prove, lint and (only with --ship) write. The frames live in
armless_tumble.py.

  python -B armless_tumble_build.py                  render, prove, report.  WRITES NOTHING.
  python -B armless_tumble_build.py --preview DIR    also writes a 4x strip into DIR (and only
                                                     DIR; a DIR under Assets is refused)
  python -B armless_tumble_build.py --ship           writes computah_armless_tumble.png and its
                                                     .aseprite into Assets/Characters/Computah,
                                                     and nothing else

It only ever writes that one sheet's two files, never the armless, wrench or prop sheets
(armless_build.py owns those), and never replaces an existing file without --replace. Every
file is built in a temp folder, moved into place in one step, and its .aseprite re-exported by
Aseprite and compared with the PNG pixel for pixel (art_source/imgdiff), in the temp folder and
again where it landed. --ship refuses unless every proof and lint check passes.
"""
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import armless_tumble as TB                                      # noqa: E402
import jrig as J                                                 # noqa: E402
from imgdiff import pixel_diff                                   # noqa: E402
from PIL import Image                                            # noqa: E402

M = TB.M
NAME = 'computah_armless_tumble'
ASSETS = os.path.realpath(os.path.join(HERE, '..', '..', 'Assets'))
SHIP_DIR = os.path.realpath(os.path.join(ASSETS, 'Characters', 'Computah'))
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
KEYLINE = (0x0C, 0x11, 0x1A)
KEY_BAND = (19.0, 28.0)          # his shipped sheets: 19.3-27.5% (#0C111A), zero pure black
MAX_COLOURS = 32
STREAK = TB.STREAK[:3]
FX_COLOURS = {STREAK, (0xFF, 0xF6, 0xC8), (0x8C, 0xD8, 0xFF), (0xF2, 0xF8, 0xFF)}  # streaks, sparks


def _under(path, root):
    path, root = os.path.normcase(os.path.realpath(path)), os.path.normcase(root)
    return path == root or path.startswith(root + os.sep)


def prove_rig():
    """The juggle's transform must still reproduce his approved hit frame exactly at angle 0
    (jrig.check_identity's first result), so every part here is his approved rig's, only turned.

    Its second result compares what lies OUTSIDE the 96 crop: since 2026-09-24 it reports 25
    texels there, armour and keyline 1-2 texels past the crop. That is the hit frame itself
    drawing past its own 96 frame edge (his sheet clips it; the juggle's bigger canvas shows it),
    measured the same with nothing of this folder imported, so it is noted and not a failure."""
    d, stray = J.check_identity()
    msg = d or 'the hit frame, pixel for pixel inside its 96 frame'
    if stray:
        msg += ' (note: %s outside it, the source frame running past its own edge)' % (
            stray.split(',')[0],)
    return d is None, msg


def lint(frames):
    fatal = []
    for name, im, pts in frames:
        im = im.convert('RGBA')
        data = im.get_flattened_data()
        op = [p for p in data if p[3]]
        semi = sum(1 for p in data if 0 < p[3] < 255)
        black = sum(1 for p in op if p[:3] == (0, 0, 0))
        key = 100.0 * sum(1 for p in op if p[:3] == KEYLINE) / len(op)
        cols = len({p[:3] for p in op})
        x0, y0, x1, y1 = im.getbbox()
        px = im.load()
        gaps, lone = [], []
        for y in range(TB.CELL):
            for x in range(TB.CELL):
                p = px[x, y]
                if not p[3] or p[:3] == KEYLINE:
                    continue
                n4 = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                open4 = any(not (0 <= a < TB.CELL and 0 <= b < TB.CELL) or not px[a, b][3]
                            for a, b in n4)
                if open4 and p[:3] not in FX_COLOURS:
                    gaps.append((x, y))
                n8 = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
                if not any(0 <= a < TB.CELL and 0 <= b < TB.CELL and px[a, b][3] for a, b in n8):
                    lone.append((x, y))
        tag = '%s %s' % (NAME, name)
        if black:
            fatal.append('%s: %d pure black px' % (tag, black))
        if semi:
            fatal.append('%s: %d semi-transparent px' % (tag, semi))
        if cols > MAX_COLOURS:
            fatal.append('%s: %d colours (his band tops out at %d)' % (tag, cols, MAX_COLOURS))
        if not KEY_BAND[0] <= key <= KEY_BAND[1]:
            fatal.append('%s: keyline %.1f%% outside %.0f-%.0f%%' % (tag, key, KEY_BAND[0],
                                                                    KEY_BAND[1]))
        if x0 < 1 or y0 < 1 or x1 > TB.CELL - 1 or y1 > TB.CELL - 1:
            fatal.append('%s: touches its cell edge %s (he is airborne: all four edges clear)'
                         % (tag, (x0, y0, x1, y1)))
        if gaps:
            fatal.append('%s: keyline gaps at %s' % (tag, gaps[:5]))
        if lone:
            fatal.append('%s: stray pixels at %s' % (tag, lone[:5]))
        print('  %-10s keyline %4.1f%%  colours %2d  pure black %d  bbox %s' % (
            name, key, cols, black, (x0, y0, x1, y1)))
    return fatal


def report(frames):
    print('\nanchors (texels in each 96x96 cell; (0, 0) its top-left corner)')
    for name, _im, pts in frames:
        extra = ''
        if 'grip' in pts:
            extra = '  grip %s (Greyson\'s fist goes here in the press)' % (
                tuple(round(v, 1) for v in pts['grip']),)
        print('  %-10s middle %s  torn socket %s%s' % (
            name, tuple(round(v, 1) for v in pts['com']),
            tuple(round(v, 1) for v in pts['socket']), extra))


def aseprite(src, dst):
    subprocess.run([ASEPRITE, '-b', src, '--save-as', dst], check=True, capture_output=True)


def write(sheet, out_dir, replace):
    png = os.path.join(out_dir, NAME + '.png')
    ase = os.path.join(out_dir, NAME + '.aseprite')
    for p in (png, ase):
        if os.path.exists(p) and not replace:
            raise SystemExit('%s exists; pass --replace to overwrite it' % p)
    tmp = tempfile.mkdtemp(prefix='computah_tumble_')
    try:
        t_png, t_ase = os.path.join(tmp, NAME + '.png'), os.path.join(tmp, NAME + '.aseprite')
        sheet.save(t_png)
        aseprite(t_png, t_ase)
        back = os.path.join(tmp, 'roundtrip.png')
        aseprite(t_ase, back)
        d = pixel_diff(Image.open(t_png), Image.open(back)) or pixel_diff(sheet, Image.open(t_png))
        if d:
            raise SystemExit('the .aseprite does not round-trip: %s' % d)
        os.makedirs(out_dir, exist_ok=True)
        os.replace(t_png, png)
        os.replace(t_ase, ase)
        back2 = os.path.join(tmp, 'roundtrip_landed.png')
        aseprite(ase, back2)
        landed = pixel_diff(Image.open(png), Image.open(back2)) or pixel_diff(sheet, Image.open(png))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return png, ase, landed


def preview(sheet, out):
    out = os.path.realpath(out)
    if _under(out, ASSETS):
        raise SystemExit('refusing %s: it is under Assets. Only --ship writes there.' % out)
    os.makedirs(out, exist_ok=True)
    bg = Image.new('RGBA', sheet.size, (60, 64, 78, 255))
    bg.alpha_composite(sheet)
    bg.resize((sheet.width * 4, sheet.height * 4), Image.NEAREST).save(
        os.path.join(out, NAME + '_4x.png'))
    print('\npreview written to', out)


def main(argv):
    do_ship = '--ship' in argv
    replace = '--replace' in argv
    out = argv[argv.index('--preview') + 1] if '--preview' in argv else None
    sheet, frames = TB.render()
    fatal = []
    print('proofs')
    ok, msg = prove_rig()
    print('  %-44s %s  %s' % ('the juggle transform is exact at angle 0', 'ok  ' if ok else 'FAIL',
                              msg))
    if not ok:
        fatal.append('rig proof: %s' % msg)
    print('\nlint')
    fatal += lint(frames)
    report(frames)
    if out:
        preview(sheet, out)
    if fatal:
        print('\nFAILED:\n  ' + '\n  '.join(fatal))
    if not do_ship:
        print('\n(no --ship: nothing written)')
        return 1 if fatal else 0
    if fatal:
        print('\nREFUSING TO SHIP')
        return 1
    if not (os.path.isdir(SHIP_DIR) and SHIP_DIR.replace('\\', '/').lower().endswith(
            'assets/characters/computah')):
        raise SystemExit('refusing: %s is not the live Computah folder' % SHIP_DIR)
    png, ase, landed = write(sheet, SHIP_DIR, replace)
    print('\nshipped %s (%dx%d, %d cells of %dx%d)' % (png, sheet.width, sheet.height, len(frames),
                                                      TB.CELL, TB.CELL))
    print('shipped %s' % ase)
    print('.aseprite round trip where it landed:', landed or 'identical (alpha and colour)')
    return 1 if landed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
