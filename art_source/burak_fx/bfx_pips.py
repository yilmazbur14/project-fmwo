"""burak_pips.png: one pip of the bullet-loading timer (the code draws 5 in a row, left to right). 4 frames
of 16x24, one strip:
  frame 0   EMPTY: a hollow slot on its plate
  frame 1   LOADING: the flash as a bullet goes in (show it for about 0.1 s, then frame 2)
  frame 2   LOADED: a brass cartridge with a lead tip
  frame 3   SPENT: the slot empty again, a wisp of smoke off it (for emptying them as he fires)
THE PIVOT IS THE FRAME CENTRE (8, 12). Suggested spacing: 18 texels (54 px at 3x) between pip centres.

Built to read at a glance as a timer: a dark plate (#23232F, rimmed #15151D) behind every pip so it holds
up over anything, a gold rim (Burak's trim), and the loaded state bright brass (#FFF3B0 #F5D94E #E0AB35
#B07D22 #7A5216) against it, so empty and loaded differ in brightness, not just colour. No keyline.
"""
import math

import bfx_pal as pal

W, H = 16, 24
FRAME_SIZE = (16, 24)
NOTE = '4 frames: f0 empty, f1 loading flash, f2 loaded, f3 spent; pivot = centre (8,12); space 18 texels'

# The cartridge, 6 wide, in the plate: round-nosed lead tip over a brass case with a rim at its base.
BULLET = [
    '..##..',
    '.####.',
    '.####.',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
    '######',
]
BX, BY = 5, 4


def plate(g, rim_key='G'):
    """A rounded plate: dark, with a gold rim lit on its top-left edges."""
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            cx, cy = x + 0.5, y + 0.5
            dx = max(0.0, abs(cx - 8.0) - 3.5)
            dy = max(0.0, abs(cy - 12.0) - 7.5)
            d = math.hypot(dx, dy)
            if d > 3.5:
                continue
            if d > 2.6:
                g[y][x] = rim_key if (cx + cy) < 20 else 'g'
            elif d > 1.8:
                g[y][x] = 'x'
            else:
                g[y][x] = 'K'


def bullet_cells():
    return [(BX + x, BY + y) for y, r in enumerate(BULLET) for x, k in enumerate(r) if k == '#']


def frame(f):
    g = pal.blank(W, H)
    plate(g)
    cells = bullet_cells()
    if f in (0, 3):
        # a hollow slot: the bullet's outline in dim iron
        cs = set(cells)
        for (x, y) in cells:
            if any((x + dx, y + dy) not in cs for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = 'k'
        if f == 3:
            for (x, y, k) in ((8, 3, 'c'), (9, 2, 'w'), (8, 1, 'c'), (7, 0, 'c')):
                g[y][x] = k
    elif f == 1:
        for (x, y) in cells:
            g[y][x] = 'Q' if y < BY + 3 or x in (BX + 1, BX + 2) else 'Y'
        for (x, y) in ((1, 1), (14, 1), (1, 22), (14, 22), (0, 12), (15, 12), (8, 0)):
            g[y][x] = 'Q'
    else:
        for (x, y) in cells:
            col = x - BX
            row = y - BY
            if row < 3:
                k = 'S' if col <= 2 and row >= 1 else ('s' if col <= 3 else 'i')     # the lead tip
                if row == 0:
                    k = 's'
            elif row == 14:
                k = 'h'                                                          # the case's rim
            elif row == 3:
                k = 'g'                                                          # where the lead meets it
            else:
                k = 'Q' if col == 1 else ('Y' if col <= 2 else ('G' if col <= 4 else 'g'))
            g[y][x] = k
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
