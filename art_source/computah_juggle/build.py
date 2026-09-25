"""Computah's juggle sheet and his mat shadow.

  python build.py                  render, check and report.  WRITES NOTHING.
  python build.py --preview DIR    also writes the 4x strip and a 3x contact sheet
                                   into DIR (and only DIR).
  python build.py --ship           writes computah_juggle.png + .aseprite and
                                   computah_leap_shadow.png + .aseprite into
                                   Assets/Characters/Computah, then re-exports each
                                   .aseprite and pixel-diffs it against its PNG.

Without --ship this script has no path into Assets at all: art_source exporters
that default to the live folder have clobbered shipped art before.  --ship also
refuses to write unless the identity proof and the lint both pass.

Output: 12 frames of 192x144 in one horizontal strip, feet on (96, 143).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

import jrig as J          # noqa: E402
import poses              # noqa: E402
import shadow             # noqa: E402
from imgdiff import pixel_diff   # noqa: E402
from PIL import Image     # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters',
                                       'Computah'))
SHEET = 'computah_juggle'
SHADOW = 'computah_leap_shadow'
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
CHECK = [(60, 60, 60, 255), (48, 48, 48, 255)]


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.putdata([p for row in rows for p in row])
    return im


def strip(grids):
    out = [[(0, 0, 0, 0)] * (len(grids) * J.W) for _ in range(J.H)]
    for i, g in enumerate(grids):
        for y in range(J.H):
            out[y][i * J.W:(i + 1) * J.W] = g[y]
    return to_image(out)


def upscale(im, f, cell=None):
    """A checkerboard-backed, nearest-neighbour enlargement with frame dividers."""
    w, h = im.size
    big = im.resize((w * f, h * f), Image.NEAREST)
    bg = Image.new('RGBA', big.size)
    bp = bg.load()
    for y in range(big.size[1]):
        for x in range(big.size[0]):
            bp[x, y] = CHECK[((x // f) + (y // f)) % 2]
    bg.alpha_composite(big)
    if cell:
        bp = bg.load()
        for i in range(1, w // cell):
            for y in range(bg.size[1]):
                bp[i * cell * f, y] = (170, 40, 170, 255)
    return bg


def measure(grids):
    """The numbers the coder needs, measured off the drawn frames."""
    tops, cxs, cys, n = [], 0.0, 0.0, 0
    for i, g in enumerate(grids[:7]):          # every frame that can show lifted
        ys = [y for y in range(J.H) if any(p[3] for p in g[y])]
        tops.append((min(ys), i))
    for g in grids[2:7]:                       # the tumble loop
        for y in range(J.H):
            for x in range(J.W):
                if g[y][x][3]:
                    cxs += x
                    cys += y
                    n += 1
    ground = []
    for i in (0, 7, 8, 9, 10, 11):
        g = grids[i]
        ys = [y for y in range(J.H) if any(p[3] for p in g[y])]
        ground.append((i, max(ys)))
    spans = []
    for i, g in enumerate(grids):
        xs = [x for y in range(J.H) for x in range(J.W) if g[y][x][3]]
        ys = [y for y in range(J.H) for x in range(J.W) if g[y][x][3]]
        spans.append((i, min(xs), min(ys), max(xs), max(ys)))
    return {'top_row': min(tops), 'tops': tops,
            'tumble_centre': (round(cxs / n), round(cys / n)),
            'ground_rows': ground, 'spans': spans}


def aseprite_roundtrip(png, ase):
    """Save the PNG as an .aseprite with Aseprite itself, re-export that, and
    pixel-diff the re-export against the PNG (imgdiff, never a bare getbbox)."""
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True,
                   capture_output=True)
    tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(png))
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', tmp], check=True,
                   capture_output=True)
    return pixel_diff(Image.open(png), Image.open(tmp))


def main(argv):
    ship = '--ship' in argv
    preview = argv[argv.index('--preview') + 1] if '--preview' in argv else None

    same, stray = J.check_identity()
    print('identity: build_hit frame 0 through the juggle machinery at angle 0 is '
          + ('the rig\'s own frame, pixel for pixel' if same is None else 'OFF: ' + same))
    if stray:
        print('          (outside the 96x96 crop: %s -- the rig\'s own frame clips '
              'these at its edge)' % stray)

    import lint
    print()
    fatal = lint.main()
    print()

    grids = [fn() for _, fn, _ in poses.FRAMES]
    sheet = strip(grids)
    shadow_rows, sizes = shadow.sheet()
    shadow_im = to_image(shadow_rows)
    m = measure(grids)

    print('%s: %d frames of %dx%d in one strip (%dx%d), hframes %d, vframes 1'
          % (SHEET, len(grids), J.W, J.H, sheet.width, sheet.height, len(grids)))
    print('feet texel      (%d, %d)   ground frames 0, 7-11; lowest drawn rows %s'
          % (J.FEET[0], J.FEET[1], ', '.join('f%d:%d' % r for r in m['ground_rows'])))
    print('tumble_centre   (%d, %d)   centroid of everything drawn on the loop 2-6'
          % m['tumble_centre'])
    print('top_row         %d        (frame %d; highest row on any frame that can '
          'show lifted, 0-6)' % m['top_row'])
    print('                per frame: %s'
          % ', '.join('f%d:%d' % (i, t) for t, i in m['tops']))
    print('drawn extents   ' + ', '.join('f%d:%d,%d-%d,%d' % s for s in m['spans']))
    print('timings         ' + ', '.join('%d %s %.2f' % (i, n, t)
                                         for i, (n, _, t) in enumerate(poses.FRAMES)))
    print('clips           ' + ', '.join('%s %d-%d%s' % (k, a, b, ' loop' if lp else '')
                                         for k, (a, b, lp) in poses.TAGS.items()))
    print('%s: %d frames of %dx%d, ellipses %s, ink #0C111A'
          % (SHADOW, shadow.FRAMES, shadow.W, shadow.H,
             ' '.join('%dx%d' % s for s in sizes)))

    if preview:
        os.makedirs(preview, exist_ok=True)
        upscale(sheet, 4, J.W).save(os.path.join(preview, SHEET + '_4x.png'))
        upscale(shadow_im, 6, shadow.W).save(os.path.join(preview, SHADOW + '_6x.png'))
        print('\npreviews written to', preview)

    if not ship:
        print('\n(no --ship: nothing written to Assets)')
        return 1 if (fatal or same) else 0
    if fatal or same:
        print('\nREFUSING TO SHIP: the lint or the identity proof failed')
        return 1
    bad = 0
    for name, im in ((SHEET, sheet), (SHADOW, shadow_im)):
        png = os.path.join(ASSETS, name + '.png')
        ase = os.path.join(ASSETS, name + '.aseprite')
        im.save(png)
        d = aseprite_roundtrip(png, ase)
        print('shipped %-22s round trip: %s'
              % (name, d or 'identical (alpha and colour, every pixel)'))
        bad += d is not None
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
