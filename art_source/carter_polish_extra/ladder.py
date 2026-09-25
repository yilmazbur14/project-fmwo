"""Splice Carter's re-framed ladder icon into Assets/UI/Screens/rank_icons.png - his frame ONLY.

The cell comes from art_source/victory_screen/icons.py carter_cell() (the polish, hand-checked
REMAP['carter'], no nearest() fallbacks). Every other frame of the strip is copied from the live file
untouched and proved byte-identical (raw RGBA bytes and a sha256 per frame). rank_icons.aseprite is
updated the same way: ladder_splice.lua swaps the one cel inside the existing file, so its layer, its
11 frames and their durations stay as they are, and every other frame is proved pixel-identical.

    python ladder.py            # build and prove everything in the scratchpad; Assets untouched
    python ladder.py --ship     # ...then write the PNG and the .aseprite into Assets, one copy each
"""
import hashlib
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlib                                                      # noqa: E402
sys.path.insert(0, os.path.join(xlib.ROOT, 'art_source', 'victory_screen'))
import icons                                                     # noqa: E402
from cv import DB                                                # noqa: E402
from PIL import Image                                            # noqa: E402
from imgdiff import pixel_diff                                   # noqa: E402

SCREENS = os.path.join(xlib.ROOT, 'Assets', 'UI', 'Screens')
PNG = os.path.join(SCREENS, 'rank_icons.png')
ASE = os.path.join(SCREENS, 'rank_icons.aseprite')
S = icons.S
FRAME = icons.ORDER.index('carter')                              # 7
OUT = os.path.join(xlib.SCRATCH, 'ladder')


def cell_image():
    c = icons.carter_cell()
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    for y in range(S):
        for x in range(S):
            h = c.get(x, y)
            if h is not None:
                assert h in DB, h
                im.putpixel((x, y), (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255))
    return im


def frames(im):
    return [im.crop((i * S, 0, i * S + S, S)) for i in range(im.width // S)]


def sha(im):
    return hashlib.sha256(im.tobytes()).hexdigest()


def run(args):
    subprocess.run([xlib.ASEPRITE, '-b'] + args, check=True, capture_output=True)


def main(ship=False):
    os.makedirs(OUT, exist_ok=True)
    old = Image.open(PNG).convert('RGBA')
    n = old.width // S
    assert (old.width, old.height) == (S * 11, S) and n == 11, old.size
    cell = cell_image()

    new = old.copy()
    new.paste(cell, (FRAME * S, 0))                              # replaces all 1600 px of the frame

    # ---- proofs on the PNG
    fo, fn = frames(old), frames(new)
    print('rank_icons.png: %d frames of %dx%d, splicing frame %d (carter) only' % (n, S, S, FRAME))
    bad = 0
    for i in range(n):
        same = fo[i].tobytes() == fn[i].tobytes()
        mark = 'CHANGED (carter)' if i == FRAME else ('byte-identical' if same else 'DIFFERS')
        print('  frame %2d %-10s  before %s  after %s  %s' % (i, icons.ORDER[i], sha(fo[i])[:16], sha(fn[i])[:16], mark))
        if i != FRAME and not same:
            bad += 1
    assert fn[FRAME].tobytes() == cell.tobytes()
    if bad:
        raise SystemExit('%d other frames differ - refusing' % bad)
    print('  carter frame vs before:', pixel_diff(fo[FRAME], fn[FRAME]))
    cols = {c[:3] for c in xlib.lib.flat(cell) if c[3]}
    stray = {'%02x%02x%02x' % c for c in cols} - DB
    print('  carter cell: %d colours, all DB32: %s, alpha %s' % (
        len(cols), not stray, sorted({c[3] for c in xlib.lib.flat(cell)})))

    png = os.path.join(OUT, 'rank_icons.png')
    new.save(png)
    back = Image.open(png).convert('RGBA')
    assert back.tobytes() == new.tobytes(), 'saved PNG does not read back byte-identical'
    cell_png = os.path.join(OUT, 'carter_cell.png')
    cell.save(cell_png)

    # ---- the .aseprite: swap the one cel inside the existing file
    ase = os.path.join(OUT, 'rank_icons.aseprite')
    run(['--script-param', 'in=' + ASE, '--script-param', 'cell=' + cell_png,
         '--script-param', 'frame=%d' % (FRAME + 1), '--script-param', 'out=' + ase,
         '--script', os.path.join(HERE, 'ladder_splice.lua')])
    old_sheet = os.path.join(OUT, 'aseprite_before_sheet.png')
    new_sheet = os.path.join(OUT, 'aseprite_after_sheet.png')
    run([ASE, '--sheet', old_sheet, '--sheet-type', 'horizontal'])
    run([ase, '--sheet', new_sheet, '--sheet-type', 'horizontal', '--data',
         os.path.join(OUT, 'aseprite_after.json'), '--format', 'json-array', '--list-layers'])
    ao, an = Image.open(old_sheet).convert('RGBA'), Image.open(new_sheet).convert('RGBA')
    print('rank_icons.aseprite (cel swapped in place):')
    print('  sheet export vs the new PNG (imgdiff.pixel_diff):', pixel_diff(an, new) or 'identical')
    abad = 0
    for i, (a, b) in enumerate(zip(frames(ao), frames(an))):
        d = pixel_diff(a, b)
        if i != FRAME and d:
            abad += 1
        print('  frame %2d  before vs after: %s' % (i, ('changed (carter)' if d else 'identical') if i == FRAME else (d or 'identical')))
    import json
    meta = json.load(open(os.path.join(OUT, 'aseprite_after.json')))
    print('  frames %d, durations %s, layers %s' % (len(meta['frames']), sorted({f['duration'] for f in meta['frames']}),
                                                  [l['name'] for l in meta['meta'].get('layers', [])]))
    rt = subprocess.run([sys.executable, os.path.join(xlib.ROOT, 'art_source', 'victory_screen', 'rtcheck.py'),
                         png, new_sheet], capture_output=True, text=True,
                        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    print('  rtcheck.py:', rt.stdout.strip())
    if abad or pixel_diff(an, new):
        raise SystemExit('.aseprite check failed - refusing')

    if ship:
        for src, dst in ((png, PNG), (ase, ASE)):
            shutil.copyfile(src, dst)
            with open(src, 'rb') as a, open(dst, 'rb') as b:
                assert a.read() == b.read(), dst
            print('shipped', dst)
        landed = Image.open(PNG).convert('RGBA')
        assert landed.tobytes() == new.tobytes()
        print('landed PNG re-read: byte-identical to the build')
    return 0


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    sys.exit(main('--ship' in sys.argv))
