"""TRUESHOT_HIT_POLY: the 0-degree Trueshot crescent as drawn, inset 2 texels, traced into a polygon.

  1. the drawn crescent: every texel of mfx_wave.mask(0) (the body, fade included; the streak tails that
     trail behind it are not part of it)
  2. inset 2 texels: keep a texel only if every texel within 2.0 of it (a radius-2 disc) is in the body
  3. trace the kept region's outline along texel edges, clockwise on screen, then simplify it with
     Ramer-Douglas-Peucker at 0.6 texels, and check the polygon against the eroded mask
Coordinates are relative to the pivot (the frame centre, texel corner (48, 48)), x forward along the
travel direction, y across (down on screen at 0 degrees). Multiply by 3 for pixels at the game's scale.
The polygon is concave (a crescent): CollisionPolygon2D decomposes it on its own; for Geometry2D tests use
Geometry2D.is_point_in_polygon, which handles concave polygons.
"""
import math

import mfx_wave as wave

DISC = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 4]


def body_mask():
    return set(wave.mask(0.0).keys())


def inset(m):
    return {(x, y) for (x, y) in m if all((x + dx, y + dy) in m for dx, dy in DISC)}


def components(m):
    """4-connected components of a texel set, largest first."""
    left = set(m)
    out = []
    while left:
        seed = left.pop()
        comp = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in left:
                    left.discard(q)
                    comp.add(q)
                    stack.append(q)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def trace(m, keep_collinear=False):
    """The outline of a 4-connected texel region as one closed loop of texel-corner points, clockwise on
    screen (interior on the right of travel)."""
    edges = {}
    for (x, y) in m:
        if (x, y - 1) not in m:
            edges[(x, y)] = (x + 1, y)
        if (x + 1, y) not in m:
            edges[(x + 1, y)] = (x + 1, y + 1)
        if (x, y + 1) not in m:
            edges[(x + 1, y + 1)] = (x, y + 1)
        if (x - 1, y) not in m:
            edges[(x, y + 1)] = (x, y)
    start = min(edges)
    loop = [start]
    p = edges[start]
    guard = 0
    while p != start:
        loop.append(p)
        p = edges[p]
        guard += 1
        assert guard < 100000, 'outline did not close'
    assert len(loop) == len(edges), 'the region is not one simple outline (%d of %d edges)' % (len(loop), len(edges))
    if keep_collinear:
        return loop
    # Drop points in the middle of straight runs.
    out = []
    n = len(loop)
    for i in range(n):
        a, b, c = loop[i - 1], loop[i], loop[(i + 1) % n]
        if (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) != 0:
            out.append(b)
    return out


def rdp(points, eps):
    """Ramer-Douglas-Peucker on an open polyline."""
    if len(points) < 3:
        return list(points)
    (ax, ay), (bx, by) = points[0], points[-1]
    L = math.hypot(bx - ax, by - ay) or 1e-9
    best, idx = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        d = abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / L
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [points[0], points[-1]]
    return rdp(points[:idx + 1], eps)[:-1] + rdp(points[idx:], eps)


def simplify_loop(loop, eps):
    """RDP on a closed loop, split at its two farthest-apart points so the ends are stable."""
    i0 = min(range(len(loop)), key=lambda i: (loop[i][1], loop[i][0]))       # the topmost point
    i1 = max(range(len(loop)), key=lambda i: (loop[i][1], -loop[i][0]))      # the bottommost point
    if i1 < i0:
        i0, i1 = i1, i0
    a = loop[i0:i1 + 1]
    b = loop[i1:] + loop[:i0 + 1]
    return rdp(a, eps)[:-1] + rdp(b, eps)[:-1]


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def symmetric_resample(loop, spacing):
    """A smooth, exactly symmetric polygon traced on the outline.

    The traced outline is a staircase of texel corners; the midpoints of its unit edges follow the true
    curve far better, so the polygon's points are taken on that midpoint outline. Its upper half (from the
    front point on the travel axis, over the top horn, to the back point on the axis) is resampled evenly
    by arc length, keeping the horn tip, and mirrored for the lower half."""
    axis = int(wave.PY)
    n = len(loop)
    mids = [((loop[i][0] + loop[(i + 1) % n][0]) / 2.0, (loop[i][1] + loop[(i + 1) % n][1]) / 2.0)
            for i in range(n)]
    # Axis crossings: the outline's corner points on the axis line (the midpoint outline passes through
    # them on the vertical runs at the apex and at the trailing curve's middle).
    on_axis = [i for i, p in enumerate(loop) if p[1] == axis]
    front = max(on_axis, key=lambda i: loop[i][0])
    back = min(on_axis, key=lambda i: loop[i][0])
    step = -1 if loop[(front - 1) % n][1] < axis else 1
    chain = [(float(loop[front][0]), float(axis))]
    i = front
    while True:
        j = i if step == 1 else (i - 1) % n          # the edge leaving point i in walking direction
        chain.append(mids[j])
        i = (i + step) % n
        if i == back:
            break
    chain.append((float(loop[back][0]), float(axis)))
    assert all(p[1] <= axis for p in chain), 'the upper chain crosses the axis'
    tip = min(range(len(chain)), key=lambda k: (chain[k][1], chain[k][0]))   # the topmost point
    out = []
    for seg in (chain[:tip + 1], chain[tip:]):
        lens = [0.0]
        for a, b in zip(seg, seg[1:]):
            lens.append(lens[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        total = lens[-1]
        k = max(1, int(round(total / spacing)))
        pts = []
        for q in range(k + 1):
            target = total * q / k
            m = max(0, min(len(seg) - 2, next(i for i in range(len(lens) - 1) if lens[i + 1] >= target - 1e-9)))
            t = 0.0 if lens[m + 1] == lens[m] else (target - lens[m]) / (lens[m + 1] - lens[m])
            (ax, ay), (bx, by) = seg[m], seg[m + 1]
            pts.append((round(ax + (bx - ax) * t, 2), round(ay + (by - ay) * t, 2)))
        out.extend(pts if not out else pts[1:])
    upper = out
    lower = [(x, 2 * axis - y) for (x, y) in reversed(upper[1:-1])]
    poly = upper + lower
    area2 = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                for i in range(len(poly)))
    return poly if area2 > 0 else list(reversed(poly))


def mirror_ok(m):
    return all((x, int(2 * wave.PY) - 1 - y) in m for (x, y) in m)


def polygon(spacing=5.0):
    """(poly in frame texel corners, eroded mask, overlap report)."""
    body = body_mask()
    assert mirror_ok(body), 'the 0 degree crescent is not symmetric about its axis'
    comps = components(inset(body))
    m = comps[0]                       # the crescent; the horns' thin tips erode to stray texels
    dropped = sum(len(c) for c in comps[1:])
    loop = trace(m, keep_collinear=True)
    poly = symmetric_resample(loop, spacing)
    # Check: the polygon should cover the eroded mask's texel centres and little else.
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    inside_poly = {(x, y) for y in range(int(min(ys)) - 1, int(max(ys)) + 2)
                   for x in range(int(min(xs)) - 1, int(max(xs)) + 2)
                   if point_in_poly(x + 0.5, y + 0.5, poly)}
    inter = len(inside_poly & m)
    union = len(inside_poly | m)
    return poly, m, {'mask texels': len(m), 'polygon texels': len(inside_poly), 'iou': round(inter / union, 4),
                     'stray texels dropped': dropped, 'pieces dropped': len(comps) - 1}


def relative(poly):
    """Pivot-relative coordinates, texels."""
    return [(round(x - wave.PX, 2) + 0.0, round(y - wave.PY, 2) + 0.0) for (x, y) in poly]


def gd_literal(poly, scale):
    pts = ', '.join('Vector2(%g, %g)' % (round(x * scale, 2), round(y * scale, 2)) for (x, y) in relative(poly))
    return 'PackedVector2Array([%s])' % pts


if __name__ == '__main__':
    poly, m, rep = polygon()
    print(rep, len(poly), 'points')
    print('texels:', gd_literal(poly, 1))
    print('px:    ', gd_literal(poly, 3))
