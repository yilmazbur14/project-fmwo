"""Carter's juggle sheet and his mat shadow.

  python build.py                  render, check and report.  WRITES NOTHING.
  python build.py --preview DIR    also writes the 4x strip and the shadow preview into DIR (only DIR).
  python build.py --ship           writes carter_juggle.png + .aseprite and carter_leap_shadow.png +
                                   .aseprite into Assets/Characters/Carter, then re-exports each
                                   .aseprite and pixel-diffs it against its PNG.

Without --ship this script has no path into Assets at all: art_source exporters that default to the
live folder have clobbered shipped art before.  --ship also refuses to write unless the identity proof
(every approved three-quarter pose through the juggle rig at angle 0 == rig34.draw), a determinism
check and the lint all pass.

Output: 12 frames of 192x144 in one horizontal strip, feet on (96, 143).
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
try:                                    # the report names the 天; a cp1252 console cannot print it
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, ValueError):
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kjrig as K         # noqa: E402  (sets up the carter_polish imports)
import body               # noqa: E402
import poses              # noqa: E402
import shadow             # noqa: E402
from imgdiff import pixel_diff   # noqa: E402
from PIL import Image     # noqa: E402

ASSETS = os.path.normpath(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Carter'))
SHEET = 'carter_juggle'
SHADOW = 'carter_leap_shadow'
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
CHECK = [(60, 60, 60, 255), (48, 48, 48, 255)]


def render():
    out = []
    for name, fn, _ in poses.FRAMES:
        r = fn()
        out.append(r if isinstance(r, Image.Image) else r.image())
    return out


def strip(frames):
    im = Image.new('RGBA', (K.W * len(frames), K.H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        im.paste(f, (i * K.W, 0))
    return im


def to_image(rows):
    h, w = len(rows), len(rows[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    im.putdata([p for row in rows for p in row])
    return im


def upscale(im, f, cell=None):
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


def measure(frames):
    def span(im):
        box = im.getbbox()
        return box
    spans = [(i,) + span(f) for i, f in enumerate(frames)]
    tops = [(s[2], s[0]) for s in spans[:7]]          # every frame that can show lifted
    cx = cy = n = 0
    for f in frames[2:7]:                              # the tumble loop
        px = f.load()
        for y in range(K.H):
            for x in range(K.W):
                if px[x, y][3]:
                    cx += x
                    cy += y
                    n += 1
    ground = [(i, frames[i].getbbox()[3] - 1) for i in (0, 7, 8, 9, 10, 11)]
    return {'top_row': min(tops), 'tops': tops, 'tumble_centre': (round(cx / n), round(cy / n)),
            'ground_rows': ground, 'spans': spans}


def aseprite_roundtrip(png, ase):
    subprocess.run([ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    tmp = os.path.join(tempfile.mkdtemp(), os.path.basename(png))
    subprocess.run([ASEPRITE, '-b', ase, '--save-as', tmp], check=True, capture_output=True)
    return pixel_diff(Image.open(png), Image.open(tmp))


def main(argv):
    ship = '--ship' in argv
    preview = argv[argv.index('--preview') + 1] if '--preview' in argv else None

    ident = body.check_identity()
    bad_ident = [(n, d) for n, d in ident if d]
    print('identity: %d approved three-quarter poses (rush, pass with the 天, spent, defeat) through '
          'the juggle rig at angle 0: %s'
          % (len(ident), 'all identical to rig34.draw' if not bad_ident else bad_ident))

    frames = render()
    again = render()
    deterministic = all(a.tobytes() == b.tobytes() for a, b in zip(frames, again))
    # ...and across processes: a render in a child with a DIFFERENT string-hash seed.  A tie settled
    # by iterating a set of one-letter keys passes the in-process check and fails this one.
    import hashlib
    mine = hashlib.sha1(strip(frames).tobytes()).hexdigest()
    env = dict(os.environ, PYTHONHASHSEED='4242', PYTHONDONTWRITEBYTECODE='1')
    child = subprocess.run([sys.executable, '-c',
                            'import sys, hashlib; sys.dont_write_bytecode = True; '
                            'sys.path.insert(0, %r); import build; '
                            'print(hashlib.sha1(build.strip(build.render()).tobytes()).hexdigest())'
                            % HERE], capture_output=True, text=True, env=env, cwd=HERE)
    other = child.stdout.strip().splitlines()[-1] if child.stdout.strip() else child.stderr
    deterministic = deterministic and other == mine
    print('determinism: two renders %s; a child process with another hash seed %s'
          % ('identical' if all(a.tobytes() == b.tobytes() for a, b in zip(frames, again))
             else 'DIFFER', 'matches' if other == mine else 'DIFFERS (%s)' % other[:60]))

    import lint
    print()
    fatal = lint.main()
    print()

    sheet = strip(frames)
    rows, sizes = shadow.sheet()
    shadow_im = to_image(rows)
    m = measure(frames)
    print('%s: %d frames of %dx%d in one strip (%dx%d), hframes %d, vframes 1'
          % (SHEET, len(frames), K.W, K.H, sheet.width, sheet.height, len(frames)))
    print('feet texel      (%d, %d)   ground frames 0, 7-11; lowest drawn rows %s'
          % (K.FEET[0], K.FEET[1], ', '.join('f%d:%d' % r for r in m['ground_rows'])))
    print('tumble_centre   (%d, %d)   centroid of everything drawn on the loop 2-6'
          % m['tumble_centre'])
    print('top_row         %d        (frame %d; highest row on any frame that can show lifted, 0-6)'
          % m['top_row'])
    print('drawn extents   ' + ', '.join('f%d:%d,%d-%d,%d' % (s[0], s[1], s[2], s[3] - 1, s[4] - 1)
                                         for s in m['spans']))
    print('timings         ' + ', '.join('%d %s %.2f' % (i, n, t)
                                         for i, (n, _, t) in enumerate(poses.FRAMES)))
    print('clips           ' + ', '.join('%s %d-%d%s' % (k, a, b, ' loop' if lp else '')
                                         for k, (a, b, lp) in poses.TAGS.items()))
    print('%s: %d frames of %dx%d, ellipses %s, ink #000000'
          % (SHADOW, shadow.FRAMES, shadow.W, shadow.H, ' '.join('%dx%d' % s for s in sizes)))

    if preview:
        os.makedirs(preview, exist_ok=True)
        upscale(sheet, 4, K.W).save(os.path.join(preview, SHEET + '_4x.png'))
        upscale(shadow_im, 6, shadow.W).save(os.path.join(preview, SHADOW + '_6x.png'))
        print('\npreviews written to', preview)

    ok = not bad_ident and deterministic and not fatal
    if not ship:
        print('\n(no --ship: nothing written to Assets)')
        return 0 if ok else 1
    if not ok:
        print('\nREFUSING TO SHIP: the identity proof, the determinism check or the lint failed')
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
