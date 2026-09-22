"""python compare.py [scale] [frame indices...]  - juggle frames beside Mason's own,
both at the same pixel scale on the arena's mat colour, which is the only honest
way to tell whether the new art belongs next to the approved art."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

import jlib as J          # noqa: E402
import poses              # noqa: E402
from png import read_png  # noqa: E402
from zoom import write_png  # noqa: E402

SHEET = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason_sheet.png'
MAT = (92, 78, 70, 255)          # a mid canvas tone, not black and not white


def main():
    f = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    _, _, sheet = read_png(SHEET)
    refs = [0, 12, 14]            # idle, hit, KO
    want = [int(a) for a in sys.argv[2:]] or sorted(poses.APPROVED_AT.values())
    keys = [(poses.FRAMES[i][0], poses.FRAMES[i][1]()) for i in want]

    cw, ch = J.W, J.H
    pad = 10
    cols = len(refs) + len(keys)
    W2, H2 = cols * cw * f, ch * f + pad * 2
    out = [[MAT] * W2 for _ in range(H2)]

    def blit(g, gw, gh, col, foot_row):
        ox = col * cw * f
        # bottom-align on the frame's feet row so the scale comparison is fair
        oy = (95 - foot_row) * f + pad
        for Y in range(gh * f):
            for X in range(gw * f):
                p = g[Y // f][X // f]
                if p[3]:
                    dy, dx = oy + Y, ox + (cw - gw) // 2 * f + X
                    if 0 <= dy < H2 and 0 <= dx < W2:
                        out[dy][dx] = p

    for i, fi in enumerate(refs):
        g = [[sheet[y][fi * 64 + x] for x in range(64)] for y in range(64)]
        blit(g, 64, 64, i, 63)
    for i, (n, g) in enumerate(keys):
        blit(g, cw, ch, len(refs) + i, 95)

    for X in range(W2):
        out[95 * f + pad][X] = (140, 120, 108, 255)
    for c in range(1, cols):
        for Y in range(H2):
            out[Y][c * cw * f] = (150, 40, 150, 255)
    name = 'compare_%dx.png' % f
    write_png(os.path.join(HERE, name), W2, H2, out)
    print('wrote', name, W2, 'x', H2)


if __name__ == '__main__':
    main()
