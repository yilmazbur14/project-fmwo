"""python view.py <out_dir> [scale] [frame indices...]

A zoomed grid of juggle frames, straight from poses.py, with the feet row and the
frame edges marked.  Writes ONLY into the folder it is given; it has no default.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import jrig as J          # noqa: E402
import poses             # noqa: E402
from PIL import Image    # noqa: E402

GUIDE = (170, 40, 170, 255)
FEET = (60, 220, 230, 255)


def render(frames=None):
    want = frames if frames is not None else range(len(poses.FRAMES))
    return [(i, poses.FRAMES[i][0], poses.FRAMES[i][1]()) for i in want]


def grid_image(cells, f, cols=4, mark_feet=True):
    rows = (len(cells) + cols - 1) // cols
    im = Image.new('RGBA', (cols * J.W * f, rows * J.H * f), (34, 34, 44, 255))
    px = im.load()
    for n, (_, _, g) in enumerate(cells):
        ox, oy = (n % cols) * J.W * f, (n // cols) * J.H * f
        for Y in range(J.H * f):
            for X in range(J.W * f):
                p = g[Y // f][X // f]
                if not p[3]:
                    c = 62 if ((X // f) + (Y // f)) % 2 == 0 else 50
                    p = (c, c, c, 255)
                px[ox + X, oy + Y] = p
        for Y in range(J.H * f):
            px[ox, oy + Y] = GUIDE
        for X in range(J.W * f):
            px[ox + X, oy] = GUIDE
            if mark_feet:
                px[ox + X, oy + J.FEET[1] * f + f - 1] = FEET
    return im


def main():
    out = sys.argv[1]
    f = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    args = sys.argv[3:]
    single = '--each' in args
    want = [int(a) for a in args if a != '--each'] or None
    cells = render(want)
    if single:
        for cell in cells:
            im = grid_image([cell], f, cols=1)
            name = os.path.join(out, 'f%02d_%s_%dx.png' % (cell[0], cell[1], f))
            im.save(name)
            print('wrote', name)
        return
    im = grid_image(cells, f, cols=min(4, len(cells)))
    name = os.path.join(out, 'view_%dx.png' % f)
    im.save(name)
    print('wrote', name, im.size, [n for _, n, _ in cells])


if __name__ == '__main__':
    main()
