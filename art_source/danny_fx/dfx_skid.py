"""danny_sumo_dust.png: dust kicked up by a skidding foot in the sumo push. 5 frames x 2 rows of 72x32, looping
at 0.06 s: row 0 sized for Danny's feet, row 1 for the player's. Drawn for a foot sliding to the LEFT: the
dust piles up low at its leading edge and billows back over it; flip_h for a foot sliding right. Never rotated.
THE PIVOT IS (52, 28) on both rows: the foot's contact point on the floor. Put one on each skidding foot.
His cool dust (W Q P g N), low and rolling, the oldest puff thinning out in stepped alpha (168), with a scuff
line left on the mat behind the foot (k m). No keyline.
"""
import math
import random

import dfx_pal as pal
import dfx_floor as fl

W, H = 72, 32
PX, PY = 52.0, 28.0
FRAME_SIZE = (W, H)
ROWS = 2
FRAMES = 5
NOTE = ("5 frames x 2 rows of 72x32 looping at 0.06 s (row 0 Danny's feet, row 1 the player's), foot sliding left "
        "(flip_h for right); pivot (52,28) = the foot on the floor")


def frame(f, big=True):
    g = pal.blank(W, H)
    k = 1.6 if big else 1.0
    # the scuff the foot leaves on the mat, behind it (to the right)
    for x in range(int(PX) + 2, min(W - 3, int(PX + 2 + 14 * k))):
        if (x + f * 3) % 7 < 5:
            g[int(PY)][x] = 'm'
            if (x + f) % 5 == 0:
                g[int(PY)][x] = 'k'
    rnd = random.Random(f * 5 + 2)
    # dust piling up at the leading edge (left of the foot), low, rolling up and back over it
    puffs = []
    for j in range(3):
        u = (j / 3.0 + f * 0.2) % 1.0                       # each puff's age through the loop
        x = PX - 5 * k - 20 * k * u
        y = PY - 2.2 * k - 7.5 * k * u
        r = (2.4 + 4.0 * u) * k
        shade = 0 if u < 0.45 else (1 if u < 0.75 else 2)
        puffs.append((u, x, y, r, shade))
    local = {}
    for (u, x, y, r, shade) in sorted(puffs, reverse=True):
        if u > 0.7:
            # the oldest puff thins out: drawn apart, in stepped alpha, under the fresher ones
            h = pal.blank(W, H)
            fl.puff(h, x, y, r, shade, squash=0.7)
            local = fl.dust_alpha(h, 168)
            for yy in range(H):
                for xx in range(W):
                    if h[yy][xx] != '.' and g[yy][xx] == '.':
                        g[yy][xx] = h[yy][xx]
        else:
            fl.puff(g, x, y, r, shade, squash=0.7)
    # a spray of grit off the front
    for j in range(4):
        x = int(PX - (6 + 5 * j) * k - 2 * math.sin(f + j))
        y = int(PY - 2 - ((j * 3 + f) % 6) * k)
        pal.put(g, x, y, 'g')
    return pal.Frame(pal.rows(g), local)


def frames():
    """Row by row: frames[row * 5 + f]."""
    return [frame(f, big) for big in (True, False) for f in range(5)]


def rows_of_frames():
    return [[frame(f, big) for f in range(5)] for big in (True, False)]
