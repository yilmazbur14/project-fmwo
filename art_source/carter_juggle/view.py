"""python view.py <out_dir> [scale] [frame indices...] [--each]

Zoomed juggle frames straight from poses.py, the feet row marked.  Writes ONLY into the folder it is
given; it has no default.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kjrig as K         # noqa: E402
import poses              # noqa: E402
from PIL import Image     # noqa: E402

GUIDE = (170, 40, 170, 255)
FEET = (60, 220, 230, 255)


def render(want=None):
    idx = want if want is not None else range(len(poses.FRAMES))
    out = []
    for i in idx:
        name, fn, _ = poses.FRAMES[i]
        r = fn()
        im = r if isinstance(r, Image.Image) else r.image()
        out.append((i, name, im))
    return out


def grid_image(cells, f, cols=4):
    rows = (len(cells) + cols - 1) // cols
    out = Image.new('RGBA', (cols * K.W * f, rows * K.H * f), (34, 34, 44, 255))
    px = out.load()
    for n, (_, _, im) in enumerate(cells):
        ox, oy = (n % cols) * K.W * f, (n // cols) * K.H * f
        src = im.load()
        for Y in range(K.H * f):
            for X in range(K.W * f):
                p = src[X // f, Y // f]
                if not p[3]:
                    c = 62 if ((X // f) + (Y // f)) % 2 == 0 else 50
                    p = (c, c, c, 255)
                px[ox + X, oy + Y] = p
        for Y in range(K.H * f):
            px[ox, oy + Y] = GUIDE
        for X in range(K.W * f):
            px[ox + X, oy] = GUIDE
            px[ox + X, oy + K.FEET[1] * f + f - 1] = FEET
    return out


def main():
    out = sys.argv[1]
    f = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    args = sys.argv[3:]
    each = '--each' in args
    want = [int(a) for a in args if a != '--each'] or None
    cells = render(want)
    if each:
        for c in cells:
            path = os.path.join(out, 'k%02d_%s_%dx.png' % (c[0], c[1], f))
            grid_image([c], f, cols=1).save(path)
            print('wrote', path)
        return
    im = grid_image(cells, f, cols=min(4, len(cells)))
    path = os.path.join(out, 'kview_%dx.png' % f)
    im.save(path)
    print('wrote', path, im.size, [c[1] for c in cells])


if __name__ == '__main__':
    main()
