"""Volume shading for the Flyby's body parts: light from the top-front (up and to the right, as he flies
right), the approved ramps (art_source/bixby_redesign/pal.py) stepped by how deep a texel sits between
the lit edge and the shadowed edge of its part, so forms turn rather than sit flat.

  RAMPS[material] = (highlight, light, base, shade, deep)
"""
import math

import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)

RAMPS = {
    'fur': ('u', 't', 't', 's', 'r'),
    'fur_dark': ('t', 's', 's', 'r', 'q'),
    'black': ('d', 'c', 'c', 'b', 'a'),
    'bone': ('w', 'x', 'x', 'y', 'z'),
    'wine': ('M', 'm', 'L', 'L', 'l'),
}
LIGHT = (0.55, -0.83)        # toward the light: up and a little to the right


def _steps(part, x, y, dx, dy, cap=24):
    n = 0
    fx, fy = float(x), float(y)
    while n < cap:
        fx += dx
        fy += dy
        if (int(round(fx)), int(round(fy))) not in part:
            return n
        n += 1
    return cap


def shade(pixels, material, light=LIGHT, bands=(0.14, 0.34, 0.68, 0.88), rim=None, rim_side=(-1, 0.3)):
    """{pixel: key} for a set of pixels, shaded as one rounded form lit from `light`.

    bands split t = lit_depth / (lit_depth + dark_depth) into highlight, light, base, shade and deep.
    rim: a key painted on the edge facing rim_side (Hades' violet rim on black, say)."""
    part = set(pixels)
    ramp = RAMPS[material]
    lx, ly = light
    n = math.hypot(lx, ly)
    lx, ly = lx / n, ly / n
    out = {}
    for (x, y) in part:
        a = _steps(part, x, y, lx, ly)
        b = _steps(part, x, y, -lx, -ly)
        t = a / max(1, a + b)
        if a == 0:
            k = ramp[0]
        elif t < bands[0]:
            k = ramp[0]
        elif t < bands[1]:
            k = ramp[1]
        elif t < bands[2]:
            k = ramp[2]
        elif t < bands[3]:
            k = ramp[3]
        else:
            k = ramp[4]
        if b == 0:
            k = ramp[4]
        out[(x, y)] = k
    if rim:
        rx, ry = rim_side
        rn = math.hypot(rx, ry)
        rx, ry = rx / rn, ry / rn
        for (x, y) in part:
            if (int(round(x + rx)), int(round(y + ry))) not in part:
                out[(x, y)] = rim
    return out
