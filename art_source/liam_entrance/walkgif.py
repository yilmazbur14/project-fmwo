"""Carrier march GIF: C1's 4-frame walk on the arena floor colour, a length of pole in his fists, floor shadow, 6x."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Canvas, ell
from pal import BLACK, WOOD, GOLD_A
from gifio import write_gif
import carriers
import throne_parts

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'liam_entrance', 'liam_carrier_walk_6x.gif'))
FLOOR = (136, 180, 99, 255)
SHADOW = tuple(int(c * 0.62) for c in FLOOR[:3]) + (255,)
S = 6


def frame(cv_carrier):
    W, H = 56, 40
    bg = [[FLOOR] * W for _ in range(H)]
    for (x, y) in ell(28, 36.5, 9, 2.2):
        if 0 <= x < W and 0 <= y < H:
            bg[y][x] = SHADOW
    pole = Canvas(W, H)
    throne_parts.pole(pole, carriers.POLE_Y0 + 4, 5, 50)
    for y in range(H):
        for x in range(W):
            c = pole.px[y][x]
            if c is not None:
                bg[y][x] = c
    for y in range(cv_carrier.h):
        for x in range(cv_carrier.w):
            c = cv_carrier.px[y][x]
            if c is not None:
                bg[y + 4][x + 12] = c
    out = []
    for row in bg:
        r = []
        for p in row:
            r.extend([p] * S)
        for _ in range(S):
            out.append(list(r))
    return out


if __name__ == '__main__':
    frames = [frame(f) for f in carriers.c1_walk()]
    size = write_gif(OUT, frames, [12, 12, 12, 12])
    print(OUT, size)
