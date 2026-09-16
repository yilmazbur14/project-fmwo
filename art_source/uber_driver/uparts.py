"""Silhouette masks, auto 1px outline, form shading, layered compositing."""
import math

LIGHT = (-0.55, -0.62, 0.56)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)

RAMP_GREEN = ['X', 'g', 'G', 'L', 'Q']
RAMP_GREEN_FAR = ['X', 'X', 'g', 'G', 'L']
RAMP_CHAR = ['Z', 'b', 'B', 'T', 'E']
RAMP_CHAR_FAR = ['Z', 'Z', 'b', 'B', 'T']
RAMP_SKIN = ['D', 'd', 's', 'S', 'A']
RAMP_SKIN_FAR = ['D', 'D', 'd', 's', 'S']
THRESH = [0.12, 0.40, 0.74, 0.90]


def tone(ramp, i, thresh=THRESH):
    k = 0
    while k < 4 and i >= thresh[k]:
        k += 1
    return ramp[k]


def mask_spans(spans):
    """spans: {y: (xl, xr)} inclusive silhouette incl. outline -> set of (x,y)."""
    m = set()
    for y, (xl, xr) in spans.items():
        for x in range(xl, xr + 1):
            m.add((x, y))
    return m


def mask_stroke(pts, radii):
    """Tapered stroke through joint points with per-point radius."""
    m = set()
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    R = max(radii) + 1
    for y in range(int(min(ys) - R), int(max(ys) + R) + 1):
        for x in range(int(min(xs) - R), int(max(xs) + R) + 1):
            if inside_stroke(x, y, pts, radii):
                m.add((x, y))
    return m


def inside_stroke(x, y, pts, radii):
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx, ay + t * dy
        r = radii[i] + t * (radii[i + 1] - radii[i])
        if (x - px) ** 2 + (y - py) ** 2 <= r * r + 0.25:
            return True
    return False


def stroke_normal(x, y, pts, radii):
    """Cylinder normal for the closest segment."""
    best = None
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0 if L2 == 0 else max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx, ay + t * dy
        r = radii[i] + t * (radii[i + 1] - radii[i])
        d2 = (x - px) ** 2 + (y - py) ** 2
        if best is None or d2 < best[0]:
            best = (d2, px, py, r)
    d2, px, py, r = best
    ux, uy = (x - px) / (r + 0.5), (y - py) / (r + 0.5)
    s = ux * ux + uy * uy
    if s > 1:
        k = 1 / math.sqrt(s); ux *= k; uy *= k; s = 1
    return (ux, uy, math.sqrt(max(0.0, 1 - s)))


def span_normal(spans, y0, y1):
    """Ellipsoid-ish normal for a span-defined blob."""
    yc = (y0 + y1) / 2.0
    hh = (y1 - y0) / 2.0 + 0.5

    def fn(x, y):
        xl, xr = spans[y]
        xc = (xl + xr) / 2.0
        hw = (xr - xl) / 2.0 + 0.5
        u = (x - xc) / hw
        v = (y - yc) / hh * 0.75
        s = u * u + v * v
        if s > 1:
            k = 1 / math.sqrt(s); u *= k; v *= k; s = 1
        return (u, v, math.sqrt(max(0.0, 1 - s)))
    return fn


def render(mask, normal_fn, ramp, bias=0.0, thresh=THRESH):
    """-> layer dict {(x,y): char} with auto outline."""
    layer = {}
    for (x, y) in mask:
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            layer[(x, y)] = 'K'
        else:
            n = normal_fn(x, y)
            i = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2] + bias
            layer[(x, y)] = tone(ramp, i, thresh)
    return layer


def sprite_layer(rows, ox, oy):
    layer = {}
    for j, r in enumerate(rows):
        for i, c in enumerate(r):
            if c not in '. ':
                layer[(ox + i, oy + j)] = c
    return layer


def spans_layer(rows, ox=0, oy=0):
    """{y: [(x0,x1,c) | (x,c)]} detail overrides -> layer."""
    layer = {}
    for y, spec in rows.items():
        for item in spec:
            if len(item) == 3:
                x0, x1, c = item
            else:
                x0, c = item; x1 = x0
            for x in range(x0, x1 + 1):
                layer[(ox + x, oy + y)] = c
    return layer


def compose(layers):
    import ulib
    f = ulib.new_frame()
    for layer in layers:
        for (x, y), c in layer.items():
            if c in '. ':
                continue
            if not (0 <= x < 64 and 0 <= y < 64):
                raise ValueError('pixel out of frame %d,%d' % (x, y))
            f[y][x] = c
    return f
