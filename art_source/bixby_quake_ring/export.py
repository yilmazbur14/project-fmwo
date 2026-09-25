"""Build bixby_quake_ring.png, check it, and (only with --ship) ship it to Assets/Characters/Bixby.

  python export.py                  build into the scratchpad (out/), run every check, touch nothing else
  python export.py --ship           also copy the PNG into Assets in one write, save its .aseprite beside it
                                    with the Aseprite CLI, and round-trip that .aseprite back to a PNG checked
                                    by art_source/imgdiff.py pixel_diff; refuses if either file already exists
  python export.py --ship --replace the same, allowed to replace this sheet's own two files

It never writes any other file in Assets, and a bare run writes only into the scratchpad.

Checks (all runs): the sheet is a whole 4 x 7 grid of FRAME_W x FRAME_H; every colour is in ringpal.PAL;
0% pure black and no semi-transparent texel (the Bixby FX convention); tiletest.py (seams, periodicity,
nothing moving where a neighbour draws); coverage.py (no holes in the band's middle at any radius).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import coverage  # noqa: E402
import mock  # noqa: E402
import ring  # noqa: E402
import ringpal  # noqa: E402
import tiletest  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402

from PIL import Image  # noqa: E402

NAME = 'bixby_quake_ring.png'
ASSETS = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby'
SCRATCH = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_quake_ring/out'
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'


def build():
    rows = ring.layout()
    return ringpal.sheet([cut for cut, _ in rows])


def check(im):
    """Problems with a built sheet, as a list of strings (empty if none)."""
    bad = []
    fw, fh = ring.FRAME_W, ring.FRAME_H
    if im.size != (fw * ring.FRAMES, fh * len(ring.ROWS)):
        bad.append('size %s, want %d x %d frames of %dx%d' % (im.size, ring.FRAMES, len(ring.ROWS), fw, fh))
    allowed = set(ringpal.PAL.values())
    flat = getattr(im, 'get_flattened_data', None)
    px = list(flat() if flat else im.getdata())
    stray = {p for p in px if p[3] and p not in allowed}
    if stray:
        bad.append('%d colours outside the palette, e.g. %s' % (len(stray), sorted(stray)[:3]))
    st = ringpal.stats(im)
    if st['black%'] or st['semi']:
        bad.append('black %s%%, semi-alpha %d' % (st['black%'], st['semi']))
    for r in range(len(ring.ROWS)):
        for c in range(ring.FRAMES):
            if not im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)).getbbox():
                bad.append('frame %d,%d is empty' % (c, r))
    return bad


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError('aseprite %s failed: %s %s' % (args, r.stdout, r.stderr))


def main(argv):
    ship = '--ship' in argv
    replace = '--replace' in argv
    os.makedirs(SCRATCH, exist_ok=True)
    im = build()
    src = os.path.join(SCRATCH, NAME)
    im.save(src)
    st = ringpal.stats(im)
    print('%s %dx%d: %d x %d frames of %dx%d, pivot %s (the frame centre), colours %d, black %.2f%%, semi %d'
          % (NAME, im.width, im.height, ring.FRAMES, len(ring.ROWS), ring.FRAME_W, ring.FRAME_H, ring.PIVOT,
             st['colours'], st['black%'], st['semi']))
    problems = check(im)
    for p in problems:
        print('CHECK FAILED:', p)
    if tiletest.main():
        problems.append('tiletest')
    sheet = mock.Sheet(im, ring.FRAME_W, ring.FRAME_H, [ring.PIVOT[1]] * len(ring.ROWS))
    holes = 0
    for i in range(94):
        for beat in (0, 1):
            bad, _ = coverage.holes(sheet, 187.0 + 13.0 * i, beat)
            holes += len(bad)
    print('coverage: %d uncovered px in the band middle over 94 radii x 2 beats' % holes)
    if holes:
        problems.append('coverage')
    print('built into', SCRATCH)
    if problems:
        print('NOT SHIPPABLE:', problems)
        return 1
    if not ship:
        print('(pass --ship to ship)')
        return 0
    dst = os.path.join(ASSETS, NAME)
    ase = dst[:-4] + '.aseprite'
    for p in (dst, ase):
        if os.path.exists(p) and not replace:
            print('REFUSED: %s exists; pass --replace to overwrite this sheet' % p)
            return 1
    shutil.copyfile(src, dst)                           # one write into Assets
    aseprite(dst, '--save-as', ase)
    rt = os.path.join(SCRATCH, 'roundtrip_' + NAME)
    aseprite(ase, '--save-as', rt)
    d_ase = pixel_diff(Image.open(dst), Image.open(rt))
    d_copy = pixel_diff(Image.open(src), Image.open(dst))
    print('shipped %s and %s; .aseprite round trip: %s; copy check: %s'
          % (dst, os.path.basename(ase), d_ase or 'identical', d_copy or 'identical'))
    return 1 if (d_ase or d_copy) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
