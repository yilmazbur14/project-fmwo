"""Form shading: tones picked from a pseudo-3D surface normal lit from the upper left, so the big
masses come out rounded (highlight, base, mid, shadow) instead of flat fills with an edge line."""
import math

LIGHT3 = (-0.55, -0.62, 0.56)       # toward the light: left, up, and out of the screen
_l = math.sqrt(sum(c * c for c in LIGHT3))
LIGHT3 = tuple(c / _l for c in LIGHT3)


def tone(i, ramp, cuts):
    """ramp: keys light -> dark; cuts: descending intensity thresholds, one fewer than the ramp."""
    for k, c in zip(ramp, cuts):
        if i >= c:
            return k
    return ramp[-1]


def ellipsoid(part, cx, cy, rx, ry, ramp, cuts, only=None, bulge=1.0):
    """Shade the pixels of `part` as the front of an ellipsoid centred (cx, cy)."""
    for (x, y) in list(part):
        if only is not None and part[(x, y)] not in only:
            continue
        u = (x - cx) / rx
        v = (y - cy) / ry
        r2 = u * u + v * v
        z = math.sqrt(max(0.0, 1.0 - min(1.0, r2))) * bulge
        n = (u, v, z)
        ln = math.sqrt(u * u + v * v + z * z) or 1.0
        i = (n[0] * LIGHT3[0] + n[1] * LIGHT3[1] + n[2] * LIGHT3[2]) / ln
        part[(x, y)] = tone(i, ramp, cuts)


def cylinder(part, p0, p1, r, ramp, cuts, only=None, tilt=0.0):
    """Shade the pixels of `part` as a cylinder of radius r along p0 -> p1. `tilt` leans the
    surface toward the light along the axis (positive: the p0 end faces up more)."""
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    al = math.hypot(ax, ay) or 1.0
    ax, ay = ax / al, ay / al
    nx, ny = -ay, ax
    for (x, y) in list(part):
        if only is not None and part[(x, y)] not in only:
            continue
        dx, dy = x - x0, y - y0
        s = (dx * nx + dy * ny) / r
        s = max(-1.0, min(1.0, s))
        z = math.sqrt(max(0.0, 1.0 - s * s))
        n = (s * nx - tilt * ax, s * ny - tilt * ay, z)
        ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        i = (n[0] * LIGHT3[0] + n[1] * LIGHT3[1] + n[2] * LIGHT3[2]) / ln
        part[(x, y)] = tone(i, ramp, cuts)


def near(part, pixels, key, dist=1, only=None):
    """Recolour pixels of `part` within `dist` (Chebyshev) of any pixel in `pixels`."""
    ps = set(pixels)
    for (x, y) in list(part):
        if only is not None and part[(x, y)] not in only:
            continue
        for dx in range(-dist, dist + 1):
            for dy in range(-dist, dist + 1):
                if (x + dx, y + dy) in ps:
                    part[(x, y)] = key
                    break
            else:
                continue
            break
