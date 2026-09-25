"""Greyson's weapon: a barbell with a plate on ONE end only, swung like a hammer (the user's
brief). The bar is chrome (the boots' cool whites W X x); the plate is dark iron in the cannon
bore's slate (Z z, Computah's) with a chrome rim light and hub, so the weapon adds no colours.
Keylined in pure black like everything he carries.

  bar(p0, p1)      the bar from the grip end p0 to the plate end p1, lit from the upper left.
  plate(c, ...)    a 45-lb plate: a raised outer lip, the flat face, the inner ring, the hub
                   with the bar's sleeve through it. Drawn as a slightly squashed disc: the bar
                   runs back over his shoulder, so the plate is seen nearly face-on.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
K = B.K


def bar(p0, p1, half=1.35):
    """Chrome bar pixels between p0 and p1 (half-width `half`), a tiny cylinder: lit top edge
    W, body X, shadow edge x. Stamp WITH an outline."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    out = {}
    for y in range(int(min(y0, y1)) - 3, int(max(y0, y1)) + 4):
        for x in range(int(min(x0, x1)) - 3, int(max(x0, x1)) + 4):
            dx, dy = x - x0, y - y0
            a = dx * ux + dy * uy
            s = dx * nx + dy * ny
            if -0.4 <= a <= L + 0.4 and abs(s) <= half:
                lit = -(s * (nx * K.LIGHT3[0] + ny * K.LIGHT3[1]))
                out[(x, y)] = 'W' if lit < -0.5 * half else ('x' if lit > 0.5 * half else 'X')
    # which side is lit depends on the bar's direction; make the lit edge the upper one
    return out


def plate(c, r=10.4, squash=0.88, ang=-45.0):
    """A plate centred at c: radius r across its long axis (at angle `ang`, degrees), r*squash
    across the other. Stamp WITH an outline."""
    cx, cy = c
    t = math.radians(ang)
    ex, ey = math.cos(t), math.sin(t)          # the long axis
    fx, fy = -ey, ex                           # the short axis
    out = {}
    R = int(r) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x - cx, y - cy
            u = (dx * ex + dy * ey) / r
            v = (dx * fx + dy * fy) / (r * squash)
            d = math.sqrt(u * u + v * v)
            if d > 1.0:
                continue
            # a flat disc lit from the upper left: the lip catches the light on that side
            side = (dx * K.LIGHT3[0] + dy * K.LIGHT3[1]) / max(0.5, math.hypot(dx, dy))
            if d > 0.80:                        # the raised outer lip
                k = 'x' if side > 0.35 else ('Z' if side > -0.45 else 'z')
            elif d > 0.72:                      # the groove inside the lip
                k = 'z'
            elif d > 0.38:                      # the face
                k = 'Z' if side > -0.55 else 'z'
            elif d > 0.30:                      # the inner ring
                k = 'x' if side > 0.2 else 'z'
            else:                               # the hub, chrome, with the sleeve's end
                k = 'W' if side > 0.3 else ('X' if side > -0.3 else 'x')
            out[(x, y)] = k
    return out
