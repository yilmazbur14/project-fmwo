"""v2 elliptical crescent smear (white rim, pale middle, soft inner) on a rig2.Frame."""
import math
from lib import PALC


def crescent(fr, cx, cy, rx, ry, a0, a1, thick0, thick1, rot=0.0):
    """band on the ellipse (cx, cy, rx, ry) from angle a0 to a1 (deg, increasing); thickness thick0 -> thick1 px"""
    a0r, a1r = math.radians(a0), math.radians(a1)
    span = (a1r - a0r) % (2 * math.pi) or 2 * math.pi
    ro = math.radians(rot)
    cr, sr = math.cos(ro), math.sin(ro)
    for y in range(fr.H):
        for x in range(fr.W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * cr + dy * sr
            v = -dx * sr + dy * cr
            rho = math.hypot(u / rx, v / ry)
            if rho > 1.0 or rho < 0.3:
                continue
            t = math.atan2(v / ry, u / rx)
            d = (t - a0r) % (2 * math.pi)
            if d > span:
                continue
            f = d / span
            th = thick0 + (thick1 - thick0) * f
            rloc = math.hypot(math.cos(t) * rx, math.sin(t) * ry)
            depth = (1.0 - rho) * rloc
            if depth > th:
                continue
            q = depth / max(th, 1e-6)
            col = 'W' if (th < 2.2 or q < 0.34) else ('A' if q < 0.7 else 'B')
            fr.px[y][x] = PALC[col]
