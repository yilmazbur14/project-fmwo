"""White motion smears, dust puffs, sparks (128-space)."""
import math
import lib
from lib import PALC, BLACK

WHITE = PALC['W']
PALE = PALC['A']
SOFT = PALC['B']


def _ang_in(t, a0, a1):
    """t, a0, a1 in radians; span from a0 going positive to a1 (a1 may be > a0 + 2pi? no)"""
    span = (a1 - a0) % (2 * math.pi)
    d = (t - a0) % (2 * math.pi)
    return d <= span, (d / span if span else 0)


def crescent(cv, cx, cy, rx, ry, a0, a1, thick0, thick1, rot=0.0, inner_rim=True, dash_tail=0.0,
             color=WHITE, rim=SOFT, clip=None, over_only_empty=False):
    """Smear band on the ellipse (cx,cy,rx,ry) rotated by rot (deg), from angle a0 to a1 (deg, increasing),
    thickness (px, measured inward from the outer ellipse) growing thick0 -> thick1.
    dash_tail: fraction of the span at the thin end broken into dashes."""
    W, H = lib.W, lib.H
    a0r, a1r = math.radians(a0), math.radians(a1)
    ro = math.radians(rot)
    cr, sr = math.cos(ro), math.sin(ro)
    band = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * cr + dy * sr
            v = -dx * sr + dy * cr
            rho = math.hypot(u / rx, v / ry)
            if rho > 1.0 or rho < 0.2:
                continue
            t = math.atan2(v / ry, u / rx)
            inside, f = _ang_in(t, a0r, a1r)
            if not inside:
                continue
            th = thick0 + (thick1 - thick0) * f
            # local radius in px along this direction
            rloc = math.hypot(math.cos(t) * rx, math.sin(t) * ry)
            depth = (1.0 - rho) * rloc
            if depth <= th:
                if dash_tail and f < dash_tail:
                    seg = int(f / dash_tail * 5)
                    if seg % 2 == 1:
                        continue
                band[y][x] = (depth, th)
    for y in range(H):
        for x in range(W):
            if band[y][x]:
                if clip is not None and not clip[y][x]:
                    continue
                if over_only_empty and cv.px[y][x] is not None:
                    continue
                depth, th = band[y][x]
                col = color
                if inner_rim and th >= 3 and depth > th - 1.0:
                    col = rim
                cv.px[y][x] = col
    return band


def spark(cv, cx, cy, r=6, rays=8, core=2):
    """impact spark: white star with pale-yellow core and black-free tips"""
    Y1 = PALC['g']
    Y2 = PALC['G']
    pts = {}
    for k in range(rays):
        ang = math.radians(k * 360 / rays + 22.5 * (k % 2))
        L = r if k % 2 == 0 else r * 0.6
        for s in range(0, int(L * 2) + 1):
            d = s / 2
            x = int(math.floor(cx + math.cos(ang) * d))
            y = int(math.floor(cy + math.sin(ang) * d))
            pts[(x, y)] = min(pts.get((x, y), 99), d)
    for (x, y), d in pts.items():
        if 0 <= x < lib.W and 0 <= y < lib.H:
            cv.px[y][x] = Y1 if d <= core else WHITE
    for dx in range(-core, core + 1):
        for dy in range(-core, core + 1):
            if abs(dx) + abs(dy) <= core:
                x, y = int(cx) + dx, int(cy) + dy
                if 0 <= x < lib.W and 0 <= y < lib.H:
                    cv.px[y][x] = Y1 if abs(dx) + abs(dy) < core else Y2


DUST = """
..kkkk...
.kAAWAk..
kBAAAABkk
kBBBAABAk
.kCBBBBCk
..kkkkkk.
"""


def stamp(cv, grid, x0, y0, flip=False):
    rows = grid.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            X = x0 + (w - 1 - c if flip else c)
            Y = y0 + r
            if 0 <= X < lib.W and 0 <= Y < lib.H:
                cv.px[Y][X] = PALC[ch]
