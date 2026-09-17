"""Armoured limb rasterizer matching Eric's arm rendering: 1px black outline around the union,
light grey fill (L), mid-blue shade (M) on the side away from the light, white glint (w) on the lit edge."""
import math
from lib import FS

LIGHT = (0.8, -0.6)   # from the right and slightly above (idle arm is lit on its right edge)


def _seg_info(px, py, a):
    x0, y0, x1, y1, r = a[:5]
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-9
    t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
    cx, cy = x0 + t * dx, y0 + t * dy
    d = math.hypot(px - cx, py - cy)
    L = math.sqrt(L2)
    nx, ny = -dy / L, dx / L
    if nx * LIGHT[0] + ny * LIGHT[1] < 0:
        nx, ny = -nx, -ny
    v = ((px - cx) * nx + (py - cy) * ny) / r
    return d, v, t


def limb(g, parts, glint=True, outline=True, lines=()):
    """parts: list of (x0,y0,x1,y1,r[, 'noglint']) capsules in pixel-centre coords.
    lines: list of ((x,y),(x,y)) interior black lines (e.g. an elbow or knuckle crease), drawn after fill."""
    inside = {}
    xs = [p[0] for p in parts] + [p[2] for p in parts]
    ys = [p[1] for p in parts] + [p[3] for p in parts]
    R = max(p[4] for p in parts) + 2
    for y in range(max(0, int(min(ys) - R)), min(FS, int(max(ys) + R) + 1)):
        for x in range(max(0, int(min(xs) - R)), min(FS, int(max(xs) + R) + 1)):
            best = None
            for a in parts:
                d, v, t = _seg_info(x + 0.5, y + 0.5, a)
                if d <= a[4] and (best is None or d - a[4] < best[0]):
                    best = (d - a[4], v, t, a)
            if best is not None:
                inside[(x, y)] = best
    if outline:
        for (x, y) in list(inside):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in inside and 0 <= q[0] < FS and 0 <= q[1] < FS:
                    g[q[1]][q[0]] = 'k'
    for (x, y), (_, v, t, a) in inside.items():
        # distance to the outline in pixels decides the edge treatment
        edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if (edge and v < -0.2) or v < -0.8:
            c = 'M'
        else:
            c = 'L'
        if glint and edge and v > 0.55 and 0.25 < t < 0.75 and (len(a) < 6 or a[5] != 'noglint'):
            c = 'w'
        g[y][x] = c
    for (p0, p1) in lines:
        n = int(max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))) + 1
        for i in range(n):
            tt = i / max(1, n - 1)
            X = int(round(p0[0] + (p1[0] - p0[0]) * tt))
            Y = int(round(p0[1] + (p1[1] - p0[1]) * tt))
            if (X, Y) in inside:
                g[Y][X] = 'k'
    return inside
