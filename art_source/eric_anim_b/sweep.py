"""Sweep smear: the area the outer blade passed through between a previous pose and the current pose.
Crescent-shaped: thick next to the current blade, tapering to a thin tail at the old pose; banded radially
like designer A's smear_arc (white rim along the tip path, pale middle, soft inner edge)."""
import math
import lib
from lib import PALC
from sword import Sword

TIP = 91.0


def sweep(fr, pose0, pose1, steps=18, band=30.0, tail=0.12, keep_out=None, a_tip=TIP, ease=0.8, recency=False,
          a_floor=-26.5):
    """pose = (origin, ang, sa, sb). band: radial thickness (in blade units) next to the current blade."""
    lib.W = lib.H = 128
    best = {}
    for k in range(steps + 1):
        t = k / steps
        o = (pose0[0][0] + (pose1[0][0] - pose0[0][0]) * t, pose0[0][1] + (pose1[0][1] - pose0[0][1]) * t)
        ang = pose0[1] + (pose1[1] - pose0[1]) * t
        sa = pose0[2] + (pose1[2] - pose0[2]) * t
        sb = pose0[3] + (pose1[3] - pose0[3]) * t
        S = Sword(o, ang, sa, sb)
        thick = band * (tail + (1 - tail) * (t ** ease))
        a_in = max(a_floor, a_tip - thick)
        pts = [S.P(a, b) for a in (a_in, a_tip) for b in (-11, 11)]
        x0 = max(0, int(min(p[0] for p in pts)) - 1)
        x1 = min(127, int(max(p[0] for p in pts)) + 1)
        y0 = max(0, int(min(p[1] for p in pts)) - 1)
        y1 = min(127, int(max(p[1] for p in pts)) + 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                a, b = S.ab(x, y)
                if a_in <= a <= a_tip and abs(b) <= 10.5:
                    q = t if recency else (a - a_in) / max(1e-6, thick)       # 0 inner .. 1 tip path
                    cur = best.get((x, y))
                    if cur is None or q > cur:
                        best[(x, y)] = q
    for (x, y), q in best.items():
        if keep_out is not None and (x, y) in keep_out:
            continue
        ch = 'W' if q > 0.62 else ('A' if q > 0.3 else 'B')
        fr.px[y][x] = PALC[ch]
    return best
