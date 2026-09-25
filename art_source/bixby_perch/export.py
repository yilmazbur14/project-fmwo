"""Build beast Bixby's perch set for the Inferno: 16 frames of 192x160 in one horizontal strip.

    python export.py            # SAFE: the strip, the numbers and the tables into the scratchpad only
    python export.py --write    # ALSO writes Assets/Characters/Bixby/bixby_perch.png (one save) and the
                                # .aseprite beside it, then round-trips the .aseprite back to PNG and
                                # checks it pixel for pixel (art_source/imgdiff.py)

Frame order (sheet.NAMES): perch_land 0-1, perch 2-3, volley 4-6, inhale 7-9, rear_back 10,
perch_breath 11-12, spent 13, release 14-15.
"""
import hashlib
import os
import subprocess
import sys
from collections import Counter

from PIL import Image

import common
from common import SCRATCH, ROOT, ROPE, TOP_ROW, FW, FH, RIG
import mouths
import perch_lint
import sheet
from imgdiff import pixel_diff

BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
OUT_PNG = os.path.join(BIXBY, 'bixby_perch.png')
OUT_ASE = os.path.join(BIXBY, 'bixby_perch.aseprite')
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'
APPROVED = os.path.join(BIXBY, 'bixby_beast_redesign.png')


def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    cnt = Counter(px)
    return dict(opaque=len(px), colours=len(cnt), black=100.0 * cnt.get((0, 0, 0, 255), 0) / max(1, len(px)),
                semi=sum(1 for c in px if c[3] < 255), most=cnt.most_common(1)[0][0])


def rig_hashes():
    out = {}
    for name in sorted(os.listdir(RIG)):
        if name.endswith('.py'):
            with open(os.path.join(RIG, name), 'rb') as fh:
                out[name] = hashlib.md5(fh.read()).hexdigest()[:10]
    return out


def aseprite(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True)
    back = os.path.join(SCRATCH, 'perch_roundtrip.png')
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', back], check=True)
    return pixel_diff(Image.open(png), Image.open(back))


def main(write=False):
    if perch_lint.run(verbose=False):
        perch_lint.run(verbose=True)
        raise SystemExit('lint failed: nothing written')
    ims = sheet.frames()
    strip = sheet.strip(ims)
    assert strip.size == (FW * 16, FH)
    os.makedirs(SCRATCH, exist_ok=True)
    strip.save(os.path.join(SCRATCH, 'bixby_perch.png'))

    s = stats(strip)
    a = stats(Image.open(APPROVED).convert('RGBA'))
    print('sheet     %dx%d, %d frames of %dx%d' % (strip.width, strip.height, len(ims), FW, FH))
    print('measured  colours %d  black %.2f%%  semi-alpha %d  most common #%02X%02X%02X' %
          (s['colours'], s['black'], s['semi'], s['most'][0], s['most'][1], s['most'][2]))
    print('approved  colours %d  black %.2f%%' % (a['colours'], a['black']))
    print('PERCH_ROPE_ROW %d (headroom: nothing above row %d)' % (ROPE, TOP_ROW))
    print('frames:', ', '.join('%s %s' % (k, v) for k, v in sheet.index_table().items()))
    rows, apex = mouths.table()
    for i, r in enumerate(rows):
        print('  %2d  middle %-10s left %-10s right %-10s%s' % (i, r[0], r[1], r[2],
              ('  apex %s (%d texels under the rope)' % (apex[i], apex[i][1] - ROPE)) if i in apex else ''))
    print('rig modules used (md5):', ' '.join('%s=%s' % kv for kv in rig_hashes().items()))

    if write:
        os.makedirs(BIXBY, exist_ok=True)
        strip.save(OUT_PNG)                   # the PNG in one save
        print('wrote', OUT_PNG)
        diff = aseprite(OUT_PNG, OUT_ASE)
        print('wrote', OUT_ASE)
        print('round trip png -> aseprite -> png:', diff or 'pixel-exact match')
        if diff:
            raise SystemExit('round trip differs')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
