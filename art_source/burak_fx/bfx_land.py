"""burak_barrel_land.png: dust where a thrown keg lands, sized for the 2x keg (48x56). 5 frames of 96x40
at 0.05 s, one strip.
THE PIVOT IS (48, 32): the keg's floor point. As a centred Sprite2D, offset (0, -12). Never flipped.
A flat burst along the floor, then puffs rolling out left and right and thinning; Burak's smoke whites
and warm browns (#FFFCF4 #E8E1D3 #C3B9A9 #A88068 #7C5438), lit from the top left. No keyline, opaque.
Drawn natively: the first draft's measures (48x20) times S = 2.0.
"""
import math

import bfx_pal as pal

S = 2.0
W, H = int(48 * S + 0.5), int(20 * S + 0.5)
PX, PY = 24.0 * S, 16.0 * S
FRAME_SIZE = (W, H)
NOTE = '5 frames of %dx%d at 0.05 s; pivot (%d,%d) on the floor point, offset (0,%d)' % (W, H, PX, PY, H // 2 - PY)
RAMP = ['W', 'w', 'c', 'd', 'D']

PUFFS = [
    [(0, 0, 3.4), (5, 0.5, 2.6), (9, 1, 1.8)],
    [(3, -1, 3.8), (9, 0, 3.2), (14, 1, 2.2)],
    [(5, -2, 3.8), (12, -1, 3.4), (18, 0, 2.4)],
    [(7, -3, 3.0), (14, -2, 2.8), (20, -1, 1.8)],
    [(9, -4, 2.0), (16, -3, 1.8), (21, -2, 1.2)],
]
FADE = [0, 0, 0, 1, 2]


def puff(g, cx, cy, r, fade):
    for y in range(max(0, int(cy - r) - 1), min(H, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(W, int(cx + r) + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            hl = math.hypot(dx + 0.3 * r, dy + 0.35 * r)
            i = 0 if hl < 0.5 * r else (3 if (d > r - 0.8 * S and dy > 0.2 * r) else (1 if dx + dy < 0.4 * r else 2))
            g[y][x] = RAMP[min(4, i + fade)]


def streak(g):
    """f0's flat burst along the floor: a thin lens, white on top, greying to its ends and underside."""
    up, down = 1.4 * S, 0.8 * S
    half = 11.0 * S
    for y in range(H):
        for x in range(W):
            dx = abs(x + 0.5 - PX) / half
            dy = y + 0.5 - PY
            if dx > 1.0:
                continue
            reach = (1.0 - dx * dx)
            if -up * reach <= dy < 0:
                g[y][x] = 'W' if dx < 0.55 else 'w'
            elif 0 <= dy <= down * reach + 0.5:
                g[y][x] = ('w' if dx < 0.72 else 'c') if dy < 0.5 * down else ('c' if dx < 0.8 else 'd')


def frame(f):
    g = pal.blank(W, H)
    if f == 0:
        streak(g)
    for (ox, oy, r) in PUFFS[f]:
        for sx in (1, -1):
            puff(g, PX + sx * ox * S, PY + oy * S, r * S, FADE[f])
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(5)]
