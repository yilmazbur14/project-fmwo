"""python view.py [scale] [frame indices...]  - sheet frames as a grid, with the
feet row and the frame centre marked."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

import jlib as J          # noqa: E402
import poses              # noqa: E402
from zoom import write_png  # noqa: E402

GUIDE = (170, 40, 170, 255)
FEET = (60, 220, 230, 255)


def main():
    f = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    want = [int(a) for a in sys.argv[2:]] or list(range(len(poses.FRAMES)))
    cells = [(poses.FRAMES[i][0], poses.FRAMES[i][1]()) for i in want]
    cols = min(3, len(cells))
    rows = (len(cells) + cols - 1) // cols
    W2, H2 = cols * J.W * f, rows * J.H * f
    out = [[(34, 34, 44, 255)] * W2 for _ in range(H2)]
    for i, (name, g) in enumerate(cells):
        ox, oy = (i % cols) * J.W * f, (i // cols) * J.H * f
        for Y in range(J.H * f):
            for X in range(J.W * f):
                p = g[Y // f][X // f]
                if p[3] == 0:
                    c = 62 if ((X // f) + (Y // f)) % 2 == 0 else 50
                    p = (c, c, c, 255)
                out[oy + Y][ox + X] = p
        for Y in range(J.H * f):
            out[oy + Y][ox] = GUIDE
            out[oy + Y][ox + J.W * f - 1] = GUIDE
        for X in range(J.W * f):
            out[oy][ox + X] = GUIDE
            out[oy + J.H * f - 1][ox + X] = GUIDE
            out[oy + 95 * f][ox + X] = FEET
    name = 'view_%dx.png' % f
    write_png(os.path.join(HERE, name), W2, H2, out)
    print('wrote', name, W2, 'x', H2, [n for n, _ in cells])


if __name__ == '__main__':
    main()
