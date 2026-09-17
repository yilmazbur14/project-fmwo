"""Liam-entrance sprite toolkit (generalised from the approved Bixby-beast / Eric v2 libs).
Canvas pixels are RGBA tuples or None.  Masks are sets of (x, y) (unclipped; the canvas clips on write).
Parts = masks shaded with a volume model then outlined in black, painted back-to-front;
ASCII stamps add hand-placed detail with a per-stamp char->colour map."""
import math
from pngio import write_png, read_png, scale
from pal import BLACK, ALL_RAMPS

# ------------------------------------------------------------------ masks


def poly(pts):
    m = set()
    if not pts:
        return m
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        cy = y + 0.5
        xs = []
        for i in range(n):
            xa, ya = pts[i]
            xb, yb = pts[(i + 1) % n]
            if (ya <= cy < yb) or (yb <= cy < ya):
                xs.append(xa + (cy - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            a, b = xs[i], xs[i + 1]
            for x in range(int(math.ceil(a - 0.5)), int(math.floor(b - 0.5)) + 1):
                m.add((x, y))
    return m


def ell(cx, cy, rx, ry, ang=0.0):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    R = max(rx, ry) + 1
    m = set()
    for y in range(int(cy - R) - 1, int(cy + R) + 2):
        for x in range(int(cx - R) - 1, int(cx + R) + 2):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * ca + dy * sa
            v = -dx * sa + dy * ca
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                m.add((x, y))
    return m


def capsule(p0, p1, r0, r1=None):
    if r1 is None:
        r1 = r0
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    R = max(r0, r1) + 1
    m = set()
    for y in range(int(min(y0, y1) - R) - 1, int(max(y0, y1) + R) + 2):
        for x in range(int(min(x0, x1) - R) - 1, int(max(x0, x1) + R) + 2):
            px, py = x + 0.5, y + 0.5
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
            qx, qy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (px - qx) ** 2 + (py - qy) ** 2 <= r * r:
                m.add((x, y))
    return m


def catmull(pts, n=8):
    if len(pts) < 3:
        return list(pts)
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(n):
            t = s / n
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def tube(path, radii, smooth=True):
    if len(radii) == 2 and len(path) != 2:
        r0, r1 = radii
        Ls = [0.0]
        for a, b in zip(path, path[1:]):
            Ls.append(Ls[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        radii = [r0 + (r1 - r0) * (l / Ls[-1]) for l in Ls]
    if smooth and len(path) >= 3:
        n = 8
        sp = catmull(path, n)
        sr = []
        for i in range(len(path) - 1):
            for s in range(n):
                sr.append(radii[i] + (radii[i + 1] - radii[i]) * s / n)
        sr.append(radii[-1])
        path, radii = sp, sr
    m = set()
    for i in range(len(path) - 1):
        m |= capsule(path[i], path[i + 1], radii[i], radii[i + 1])
    return m


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def mirror(m, axis):
    """axis = x0 + x1 of the mirror pair (e.g. 63 for a 64-wide frame)"""
    return {(axis - x, y) for (x, y) in m}


def mirror_pts(pts, axis):
    return [(axis - x, y) for x, y in pts]


def edge(m):
    out = set()
    for (x, y) in m:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in m:
                out.add((x, y))
                break
    return out


def outer_edge(m, diag=False):
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ())
    out = set()
    for (x, y) in m:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in m:
                out.add(q)
    return out


def dilate(m, n=1, diag=False):
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, 1), (1, -1), (-1, -1)) if diag else ())
    for _ in range(n):
        m = m | {(x + dx, y + dy) for (x, y) in m for dx, dy in nb}
    return m


def erode(m, n=1):
    for _ in range(n):
        m = m - edge(m)
    return m


def shift(m, dx, dy):
    return {(x + dx, y + dy) for (x, y) in m}


def bbox(m):
    xs = [p[0] for p in m]
    ys = [p[1] for p in m]
    return min(xs), min(ys), max(xs), max(ys)


def halfplane_clip(m, p0, p1, side=1):
    (x0, y0), (x1, y1) = p0, p1
    return {(x, y) for (x, y) in m if ((x1 - x0) * (y + 0.5 - y0) - (y1 - y0) * (x + 0.5 - x0)) * side > 0}

# ------------------------------------------------------------------ shading


LIGHT = (-0.45, -0.6, 1.1)       # top-left key light, same as the beast / Eric v2 toolkit
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)


def chamfer(mask):
    INF = 1e9
    d = {p: INF for p in mask}
    for p in mask:
        x, y = p
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in mask:
                d[p] = 0.5
                break
    if not mask:
        return d
    x0, y0, x1, y1 = bbox(mask)
    a, b = 1.0, 1.4142
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p = (x, y)
            if p not in d:
                continue
            v = d[p]
            for (dx, dy, c) in ((-1, 0, a), (0, -1, a), (-1, -1, b), (1, -1, b)):
                q = (x + dx, y + dy)
                if q in d and d[q] + c < v:
                    v = d[q] + c
            d[p] = v
    for y in range(y1, y0 - 1, -1):
        for x in range(x1, x0 - 1, -1):
            p = (x, y)
            if p not in d:
                continue
            v = d[p]
            for (dx, dy, c) in ((1, 0, a), (0, 1, a), (1, 1, b), (-1, 1, b)):
                q = (x + dx, y + dy)
                if q in d and d[q] + c < v:
                    v = d[q] + c
            d[p] = v
    return d


def normals(mask, model):
    kind = model[0]
    out = {}
    if kind == 'sphere':
        _, cx, cy, rx, ry = model[:5]
        flat = model[5] if len(model) > 5 else 0.0
        for (x, y) in mask:
            u = (x + 0.5 - cx) / rx
            v = (y + 0.5 - cy) / ry
            dd = u * u + v * v
            if dd > 0.97:
                s = math.sqrt(0.97 / dd)
                u, v, dd = u * s, v * s, 0.97
            out[(x, y)] = (u, v, math.sqrt(1 - dd) + flat)
    elif kind == 'cyl':
        _, (x0, y0), (x1, y1), r = model[:4]
        flat = model[4] if len(model) > 4 else 0.0
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        for (x, y) in mask:
            s = ((x + 0.5 - x0) * px + (y + 0.5 - y0) * py) / r
            s = max(-0.985, min(0.985, s))
            out[(x, y)] = (s * px, s * py, math.sqrt(1 - s * s) + flat)
    elif kind == 'dist':
        R = model[1]
        flat = model[2] if len(model) > 2 else 0.0
        d = chamfer(mask)
        hgt = {}
        for p, v in d.items():
            t = min(v, R) / R
            hgt[p] = R * math.sqrt(max(0.0, 1 - (1 - t) ** 2))

        def g(q):
            return hgt.get(q, 0.0)
        for (x, y) in mask:
            gx = (g((x + 1, y)) - g((x - 1, y))) / 2
            gy = (g((x, y + 1)) - g((x, y - 1))) / 2
            out[(x, y)] = (-gx, -gy, 1.0 + flat)
    elif kind == 'flat':
        nx, ny = model[1], model[2]
        for p in mask:
            out[p] = (nx, ny, 1.0)
    elif kind == 'func':
        f = model[1]
        for (x, y) in mask:
            out[(x, y)] = f(x + 0.5, y + 0.5)
    return out


def intensity(n, light=None):
    L = light or LIGHT
    nx, ny, nz = n
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx * L[0] + ny * L[1] + nz * L[2]) / l


TH_METAL = [0.97, 0.87, 0.63, 0.38, 0.12]
TH_SOFT = [9.0, 0.88, 0.64, 0.38, 0.12]
TH_CLOTH = [9.0, 0.93, 0.72, 0.46, 0.18]
TH_4 = [9.0, 0.80, 0.50, 0.15]
TH_B = [0.93, 0.62, 0.30, 0.02]


def shade_idx(mask, model, th, cleanup=True, light=None):
    ns = normals(mask, model)
    out = {}
    for p, n in ns.items():
        I = intensity(n, light)
        idx = len(th)
        for i, t in enumerate(th):
            if I >= t:
                idx = i
                break
        out[p] = idx
    if cleanup:
        for _ in range(2):
            chg = []
            for (x, y), v in out.items():
                nb = [out[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in out]
                if len(nb) >= 3 and v not in nb:
                    chg.append(((x, y), max(set(nb), key=nb.count)))
            for p, v in chg:
                out[p] = v
    return out


DARKER, LIGHTER = {}, {}
for _r in ALL_RAMPS:
    for _i, _c in enumerate(_r):
        DARKER.setdefault(_c, _r[min(_i + 1, len(_r) - 1)])
        LIGHTER.setdefault(_c, _r[max(_i - 1, 0)])

# ------------------------------------------------------------------ canvas


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def part(self, mask, rp, model, th=TH_SOFT, outline=True, bias=0, light=None, cleanup=True):
        idx = shade_idx(mask, model, th, cleanup, light)
        for (x, y), i in idx.items():
            self.put(x, y, rp[max(0, min(i + bias, len(rp) - 1))])
        if outline:
            self.outline(mask)
        return idx

    def fill(self, mask, c):
        for (x, y) in mask:
            self.put(x, y, c)

    def outline(self, mask, color=BLACK):
        for (x, y) in edge(mask):
            self.put(x, y, color)

    def recolor(self, mask, rp, model, th=TH_SOFT, bias=0, keep=(BLACK,), light=None, cleanup=True):
        sub = {p for p in mask if self.get(*p) is not None and self.get(*p) not in keep}
        idx = shade_idx(sub, model, th, cleanup, light)
        for (x, y), i in idx.items():
            self.put(x, y, rp[max(0, min(i + bias, len(rp) - 1))])

    def paint(self, mask, color, over_only=False, keep=()):
        for (x, y) in mask:
            cur = self.get(x, y)
            if over_only and cur is None:
                continue
            if cur in keep:
                continue
            self.put(x, y, color)

    def darken(self, mask, steps=1, keep=(BLACK,)):
        for (x, y) in mask:
            c = self.get(x, y)
            if c is None or c in keep:
                continue
            for _ in range(steps):
                c = DARKER.get(c, c)
            self.put(x, y, c)

    def lighten(self, mask, steps=1, keep=(BLACK,)):
        for (x, y) in mask:
            c = self.get(x, y)
            if c is None or c in keep:
                continue
            for _ in range(steps):
                c = LIGHTER.get(c, c)
            self.put(x, y, c)

    def erase(self, mask):
        for (x, y) in mask:
            self.put(x, y, None)

    def stamp(self, grid, x0, y0, cmap, flip=False, over_only=False):
        """'.' and space skip, '_' erase, '-' darken, '+' lighten, anything else cmap[ch]"""
        rows = grid.strip('\n').split('\n')
        wdt = max(len(r) for r in rows)
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                x = x0 + (wdt - 1 - dx if flip else dx)
                y = y0 + dy
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                cur = self.px[y][x]
                if over_only and cur is None:
                    continue
                if ch == '_':
                    self.px[y][x] = None
                elif ch == '-':
                    if cur is not None and cur != BLACK:
                        self.px[y][x] = DARKER.get(cur, cur)
                elif ch == '+':
                    if cur is not None and cur != BLACK:
                        self.px[y][x] = LIGHTER.get(cur, cur)
                else:
                    self.px[y][x] = cmap[ch]

    def blit(self, other, ox=0, oy=0, flip=False):
        for y in range(other.h):
            for x in range(other.w):
                c = other.px[y][x]
                if c is not None:
                    self.put((other.w - 1 - x if flip else x) + ox, y + oy, c)

    def crop(self, x0, y0, w, h):
        c = Canvas(w, h)
        for y in range(h):
            for x in range(w):
                c.px[y][x] = self.get(x0 + x, y0 + y)
        return c

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def mask(self):
        return {(x, y) for y in range(self.h) for x in range(self.w) if self.px[y][x] is not None}

    def rgba(self):
        return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in self.px]

    def save(self, path, s=1, bg=None):
        px = self.rgba()
        if s == 1 and bg is None:
            write_png(path, self.w, self.h, px)
        else:
            write_png(path, self.w * s, self.h * s, scale(px, s, bg))
        return path


def from_png(path):
    w, h, px = read_png(path)
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            p = tuple(px[y][x])
            cv.px[y][x] = p if p[3] > 0 else None
    return cv


def close_outline(cv):
    """any opaque non-black pixel touching transparency (4-nb) becomes black"""
    chg = []
    for y in range(cv.h):
        for x in range(cv.w):
            c = cv.px[y][x]
            if c is None or c == BLACK:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if cv.get(x + dx, y + dy) is None:
                    chg.append((x, y))
                    break
    for x, y in chg:
        cv.px[y][x] = BLACK


def outline_outside(cv, color=BLACK):
    """grow a 1px outline around every opaque non-outline pixel (4-nb) into transparency"""
    add = []
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.px[y][x] is not None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c = cv.get(x + dx, y + dy)
                if c is not None and c != color:
                    add.append((x, y))
                    break
    for x, y in add:
        cv.px[y][x] = color


def shave_corners(cv, passes=1):
    for _ in range(passes):
        kill = []
        for y in range(cv.h):
            for x in range(cv.w):
                if cv.px[y][x] != BLACK:
                    continue

                def em(xx, yy):
                    return cv.get(xx, yy) is None

                def bk(xx, yy):
                    return cv.get(xx, yy) == BLACK
                for (ax, ay), (bx, by) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                    if em(x + ax, y + ay) and em(x + bx, y + by) and bk(x - ax, y - ay) and bk(x - bx, y - by):
                        ip = cv.get(x - ax - bx, y - ay - by)
                        if ip is not None and ip != BLACK:
                            kill.append((x, y))
                            break
        for x, y in kill:
            cv.px[y][x] = None


def lone_black_cleanup(cv):
    kill = []
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.px[y][x] != BLACK:
                continue
            if all(cv.get(x + dx, y + dy) is None for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy)):
                kill.append((x, y))
    for x, y in kill:
        cv.px[y][x] = None
