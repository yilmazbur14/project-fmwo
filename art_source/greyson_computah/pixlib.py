"""Tiny pixel-art shading library used for the Greyson & Computah redesign pass.

The point of this file is to avoid the "stacked primitives" look: shapes are
unioned into ONE silhouette first, then shaded from a real surface normal and a
single global light, then given contact shadows where parts overlap, then
outlined once around the whole union.  Nothing is ever drawn as a flat fill.

Pure Python (no numpy on this machine).  Canvases are <= 128x128 so it is fast
enough.
"""

import math

# --------------------------------------------------------------------------
# light
# --------------------------------------------------------------------------
_L = (-0.46, -0.60, 0.66)
_ln = math.sqrt(sum(c * c for c in _L))
LIGHT = tuple(c / _ln for c in _L)


def _clamp(v, a=0.0, b=1.0):
    return a if v < a else (b if v > b else v)


# --------------------------------------------------------------------------
# shapes.  every shape answers:  sdf(x,y) -> negative inside
#                                normal(x,y) -> (nx,ny,nz) unit-ish
# --------------------------------------------------------------------------
class Shape(object):
    round_r = 5.0            # how many px the form rolls over at the edge

    def bbox(self):
        raise NotImplementedError

    def sdf(self, x, y):
        raise NotImplementedError

    def normal(self, x, y):
        """Generic: finite-difference the sdf for the in-plane direction and
        lift out of the screen by how deep inside the shape we are."""
        d = self.sdf(x, y)
        e = 0.35
        gx = (self.sdf(x + e, y) - self.sdf(x - e, y)) / (2 * e)
        gy = (self.sdf(x, y + e) - self.sdf(x, y - e)) / (2 * e)
        g = math.hypot(gx, gy)
        if g < 1e-6:
            return (0.0, 0.0, 1.0)
        gx /= g
        gy /= g
        depth = _clamp(-d / self.round_r)          # 0 at the rim, 1 deep in
        theta = (1.0 - depth) * (math.pi / 2.0)
        s = math.sin(theta)
        return (gx * s, gy * s, math.cos(theta))


class Ellipse(Shape):
    def __init__(self, cx, cy, rx, ry, round_r=None):
        self.cx, self.cy, self.rx, self.ry = cx, cy, float(rx), float(ry)
        self.round_r = round_r if round_r is not None else min(rx, ry) * 0.95

    def bbox(self):
        return (self.cx - self.rx - 2, self.cy - self.ry - 2,
                self.cx + self.rx + 2, self.cy + self.ry + 2)

    def sdf(self, x, y):
        dx = (x - self.cx) / self.rx
        dy = (y - self.cy) / self.ry
        r = math.hypot(dx, dy)
        return (r - 1.0) * min(self.rx, self.ry)

    def normal(self, x, y):
        dx = (x - self.cx) / self.rx
        dy = (y - self.cy) / self.ry
        r2 = dx * dx + dy * dy
        if r2 >= 1.0:
            r = math.sqrt(r2) or 1.0
            return (dx / r, dy / r, 0.0)
        return (dx, dy, math.sqrt(1.0 - r2))


class Capsule(Shape):
    """Tapered capsule = a limb.  Shaded as a cylinder, which is what gives the
    arms and legs real roundness instead of a flat tube."""

    def __init__(self, p0, p1, r0, r1=None, round_r=None):
        self.p0, self.p1 = (float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1]))
        self.r0 = float(r0)
        self.r1 = float(r1 if r1 is not None else r0)
        self.round_r = round_r if round_r is not None else max(self.r0, self.r1) * 0.95

    def bbox(self):
        r = max(self.r0, self.r1) + 2
        return (min(self.p0[0], self.p1[0]) - r, min(self.p0[1], self.p1[1]) - r,
                max(self.p0[0], self.p1[0]) + r, max(self.p0[1], self.p1[1]) + r)

    def _proj(self, x, y):
        ax, ay = self.p0
        bx, by = self.p1
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = 0.0 if L2 < 1e-9 else _clamp(((x - ax) * vx + (y - ay) * vy) / L2)
        px, py = ax + vx * t, ay + vy * t
        r = self.r0 + (self.r1 - self.r0) * t
        return t, px, py, r

    def sdf(self, x, y):
        t, px, py, r = self._proj(x, y)
        return math.hypot(x - px, y - py) - r

    def normal(self, x, y):
        t, px, py, r = self._proj(x, y)
        dx, dy = x - px, y - py
        d = math.hypot(dx, dy)
        s = _clamp(d / r) if r > 0 else 1.0
        if d < 1e-6:
            # on the axis: point straight out of the screen
            return (0.0, 0.0, 1.0)
        return (dx / d * s, dy / d * s, math.sqrt(_clamp(1.0 - s * s)))


class Poly(Shape):
    def __init__(self, pts, round_r=5.0):
        self.pts = [(float(a), float(b)) for a, b in pts]
        self.round_r = round_r

    def bbox(self):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        return (min(xs) - 2, min(ys) - 2, max(xs) + 2, max(ys) + 2)

    def sdf(self, x, y):
        pts = self.pts
        n = len(pts)
        inside = False
        best = 1e9
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay > y) != (by > y):
                xin = (bx - ax) * (y - ay) / (by - ay) + ax
                if x < xin:
                    inside = not inside
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy
            t = 0.0 if L2 < 1e-9 else _clamp(((x - ax) * vx + (y - ay) * vy) / L2)
            best = min(best, math.hypot(x - (ax + vx * t), y - (ay + vy * t)))
        return -best if inside else best


class RoundRect(Poly):
    def __init__(self, x0, y0, x1, y1, r=3.0, round_r=4.0):
        self.x0, self.y0, self.x1, self.y1, self.r = x0, y0, x1, y1, float(r)
        self.round_r = round_r

    def bbox(self):
        return (self.x0 - 2, self.y0 - 2, self.x1 + 2, self.y1 + 2)

    def sdf(self, x, y):
        hx = (self.x1 - self.x0) / 2.0
        hy = (self.y1 - self.y0) / 2.0
        cx = (self.x1 + self.x0) / 2.0
        cy = (self.y1 + self.y0) / 2.0
        r = min(self.r, hx, hy)
        qx = abs(x - cx) - (hx - r)
        qy = abs(y - cy) - (hy - r)
        return (math.hypot(max(qx, 0.0), max(qy, 0.0)) +
                min(max(qx, qy), 0.0) - r)


class Union(Shape):
    """Smooth union - welds parts so the seam reads as one body."""

    def __init__(self, shapes, k=1.6, round_r=5.0):
        self.shapes = shapes
        self.k = k
        self.round_r = round_r

    def bbox(self):
        bs = [s.bbox() for s in self.shapes]
        return (min(b[0] for b in bs), min(b[1] for b in bs),
                max(b[2] for b in bs), max(b[3] for b in bs))

    def sdf(self, x, y):
        k = self.k
        d = self.shapes[0].sdf(x, y)
        for s in self.shapes[1:]:
            b = s.sdf(x, y)
            h = _clamp(0.5 + 0.5 * (d - b) / k)
            d = b * h + d * (1 - h) - k * h * (1 - h)
        return d

    def normal(self, x, y):
        # blend the member normals by how close each one is, so the seam
        # between two masses rolls over instead of creasing
        ds = [s.sdf(x, y) for s in self.shapes]
        lo = min(ds)
        nx = ny = nz = 0.0
        tot = 0.0
        for s, d in zip(self.shapes, ds):
            w = math.exp(-(d - lo) / max(self.k * 1.6, 0.4))
            if w < 1e-3:
                continue
            a, b, c = s.normal(x, y)
            nx += a * w
            ny += b * w
            nz += c * w
            tot += w
        if tot < 1e-6:
            return (0.0, 0.0, 1.0)
        nx, ny, nz = nx / tot, ny / tot, nz / tot
        m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return (nx / m, ny / m, nz / m)


class Clip(Shape):
    """`shape` limited to where `clipper` also covers, but keeping `shape`'s
    surface normal - used for hair on a skull, trunks on hips, panels on a
    chest, so the clothing rolls over the body volume underneath."""

    def __init__(self, shape, clipper, soft=0.0):
        self.shape = shape
        self.clipper = clipper
        self.soft = soft
        self.round_r = shape.round_r

    def bbox(self):
        a, b = self.shape.bbox(), self.clipper.bbox()
        return (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))

    def sdf(self, x, y):
        return max(self.shape.sdf(x, y), self.clipper.sdf(x, y) - self.soft)

    def normal(self, x, y):
        return self.shape.normal(x, y)


class Sub(Shape):
    """`shape` minus `cutter`."""

    def __init__(self, shape, cutter):
        self.shape = shape
        self.cutter = cutter
        self.round_r = shape.round_r

    def bbox(self):
        return self.shape.bbox()

    def sdf(self, x, y):
        return max(self.shape.sdf(x, y), -self.cutter.sdf(x, y))

    def normal(self, x, y):
        return self.shape.normal(x, y)


class Translate(Shape):
    """`shape` moved by (dx, dy).  Subtracting a translated copy of a mass from
    itself yields the crescent used for flat cartoon shading."""

    def __init__(self, shape, dx, dy):
        self.shape = shape
        self.dx = float(dx)
        self.dy = float(dy)
        self.round_r = shape.round_r

    def bbox(self):
        a = self.shape.bbox()
        return (a[0] + self.dx, a[1] + self.dy, a[2] + self.dx, a[3] + self.dy)

    def sdf(self, x, y):
        return self.shape.sdf(x - self.dx, y - self.dy)

    def normal(self, x, y):
        return self.shape.normal(x - self.dx, y - self.dy)


class HalfPlane(Shape):
    """ax+by+c <= 0 is inside."""

    def __init__(self, a, b, c, box=(-200, -200, 400, 400)):
        n = math.hypot(a, b) or 1.0
        self.a, self.b, self.c = a / n, b / n, c / n
        self.box = box

    def bbox(self):
        return self.box

    def sdf(self, x, y):
        return self.a * x + self.b * y + self.c

    def normal(self, x, y):
        return (self.a, self.b, 0.0)


# --------------------------------------------------------------------------
# canvas
# --------------------------------------------------------------------------
class Canvas(object):
    def __init__(self, w, h, palette, outline="#100a0e"):
        self.w, self.h = w, h
        self.pal = {k: [_hex(c) for c in v] for k, v in palette.items()}
        self.outline = _hex(outline)
        self.mat = [[None] * w for _ in range(h)]
        self.lvl = [[0] * w for _ in range(h)]
        self.prio = [[-1] * w for _ in range(h)]
        self.raw = [[None] * w for _ in range(h)]   # direct rgba overrides
        self.locked = [[False] * w for _ in range(h)]

    # ---- geometry -------------------------------------------------------
    def add(self, shape, mat, prio=0, bias=0.0, flat=None, amb=0.06,
            wrap=0.5, grow=0.0):
        """Paint a shape's pixels with a shaded material.

        bias   shifts the whole part lighter (-) or darker (+) in ramp steps
        flat   if given, force this ramp index (used for cloth panels)
        grow   dilate the shape by this many px before testing
        """
        ramp = self.pal[mat]
        n = len(ramp)
        x0, y0, x1, y1 = shape.bbox()
        x0 = max(0, int(math.floor(x0)))
        y0 = max(0, int(math.floor(y0)))
        x1 = min(self.w - 1, int(math.ceil(x1)))
        y1 = min(self.h - 1, int(math.ceil(y1)))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if shape.sdf(x + 0.5, y + 0.5) > grow:
                    continue
                if self.prio[y][x] > prio:
                    continue
                if flat is not None:
                    lv = flat
                else:
                    nx, ny, nz = shape.normal(x + 0.5, y + 0.5)
                    d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
                    # wrapped diffuse: keeps a lit rim and a soft terminator,
                    # which is what makes a 6-tone ramp read as a round volume
                    d = _clamp((1.0 - wrap) + wrap * d)
                    d = d * (1.0 - amb) + amb
                    lv = _ramp_index(d, n)
                    # reflected light on the far rim keeps limbs round
                    if lv >= n - 1 and shape.sdf(x + 0.5, y + 0.5) > -1.35:
                        lv = n - 2
                    lv += bias
                lv = int(_clampi(lv, 0, n - 1))
                self.mat[y][x] = mat
                self.lvl[y][x] = lv
                self.prio[y][x] = prio

    def carve(self, shape, grow=0.0):
        """Cut pixels back out of the silhouette."""
        x0, y0, x1, y1 = shape.bbox()
        for y in range(max(0, int(y0)), min(self.h, int(y1) + 2)):
            for x in range(max(0, int(x0)), min(self.w, int(x1) + 2)):
                if shape.sdf(x + 0.5, y + 0.5) <= grow:
                    self.mat[y][x] = None
                    self.raw[y][x] = None
                    self.prio[y][x] = -1

    # ---- shading detail -------------------------------------------------
    def occlude(self, strength=2, reach=2):
        """Darken a pixel that sits under a higher-priority part.  This is what
        separates arm from torso without drawing a hard black line."""
        out = [row[:] for row in self.lvl]
        for y in range(self.h):
            for x in range(self.w):
                if self.mat[y][x] is None or self.locked[y][x]:
                    continue
                p = self.prio[y][x]
                add = 0
                for r in range(1, reach + 1):
                    hit = False
                    for dy in range(-r, r + 1):
                        for dx in range(-r, r + 1):
                            if max(abs(dx), abs(dy)) != r:
                                continue
                            xx, yy = x + dx, y + dy
                            if 0 <= xx < self.w and 0 <= yy < self.h:
                                if self.locked[yy][xx]:
                                    continue
                                if self.mat[yy][xx] is not None and self.prio[yy][xx] > p:
                                    hit = True
                                    break
                        if hit:
                            break
                    if hit:
                        add = max(add, strength - (r - 1))
                if add:
                    n = len(self.pal[self.mat[y][x]])
                    out[y][x] = int(_clampi(self.lvl[y][x] + add, 0, n - 1))
        self.lvl = out

    def rim(self, lift=1, mats=None, dirs=((-1, 0), (0, -1), (-1, -1))):
        """One step lighter along the silhouette edge that faces the light.
        This is the pass that makes a sprite look finished rather than merely
        shaded - it separates the form from the black outline."""
        out = [row[:] for row in self.lvl]
        for y in range(self.h):
            for x in range(self.w):
                m = self.mat[y][x]
                if m is None or self.locked[y][x] or self.raw[y][x] is not None:
                    continue
                if mats and m not in mats:
                    continue
                for dx, dy in dirs:
                    xx, yy = x + dx, y + dy
                    if (xx < 0 or yy < 0 or xx >= self.w or yy >= self.h
                            or (self.mat[yy][xx] is None and self.raw[yy][xx] is None)):
                        out[y][x] = max(0, self.lvl[y][x] - lift)
                        break
        self.lvl = out

    def shade_px(self, pts, d=2, mat=None):
        """Darken specific pixels by d ramp steps (anatomy creases, folds)."""
        for (x, y) in pts:
            x, y = int(round(x)), int(round(y))
            if not (0 <= x < self.w and 0 <= y < self.h):
                continue
            m = self.mat[y][x]
            if m is None or (mat and m != mat):
                continue
            n = len(self.pal[m])
            self.lvl[y][x] = int(_clampi(self.lvl[y][x] + d, 0, n - 1))

    def contour(self, shape, width=1.3, delta=3, color=None, mats=None,
                below_prio=None):
        """Darken (or ink) the body pixels immediately OUTSIDE a shape.  This
        is how an overlapping limb reads as in-front without the sprite's own
        exterior outline being involved."""
        x0, y0, x1, y1 = shape.bbox()
        for y in range(max(0, int(y0) - 2), min(self.h, int(y1) + 3)):
            for x in range(max(0, int(x0) - 2), min(self.w, int(x1) + 3)):
                m = self.mat[y][x]
                if m is None or self.locked[y][x]:
                    continue
                if mats and m not in mats:
                    continue
                if below_prio is not None and self.prio[y][x] >= below_prio:
                    continue
                d = shape.sdf(x + 0.5, y + 0.5)
                if 0.0 < d <= width:
                    if color:
                        self.raw[y][x] = _hex(color)
                    else:
                        n = len(self.pal[m])
                        self.lvl[y][x] = int(_clampi(self.lvl[y][x] + delta, 0, n - 1))

    def set_px(self, pts, mat, lvl):
        for (x, y) in pts:
            x, y = int(round(x)), int(round(y))
            if 0 <= x < self.w and 0 <= y < self.h:
                self.mat[y][x] = mat
                self.lvl[y][x] = lvl
                self.prio[y][x] = 99

    def raw_px(self, pts, color):
        c = _hex(color)
        for (x, y) in pts:
            x, y = int(round(x)), int(round(y))
            if 0 <= x < self.w and 0 <= y < self.h:
                self.raw[y][x] = c
                if self.mat[y][x] is None:
                    self.prio[y][x] = 99

    # ---- ascii stamp ----------------------------------------------------
    def stamp(self, grid, ox, oy, chars):
        """grid: list of equal-length strings.  chars: char -> (mat,lvl) or
        '#rrggbb' or None (leave alone) / '.' means transparent-skip."""
        for j, row in enumerate(grid):
            for i, ch in enumerate(row):
                if ch == ' ':
                    continue
                v = chars.get(ch)
                if v is None:
                    continue
                x, y = ox + i, oy + j
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                if isinstance(v, str):
                    self.raw[y][x] = _hex(v)
                    self.prio[y][x] = 99
                else:
                    self.mat[y][x] = v[0]
                    self.lvl[y][x] = v[1]
                    self.prio[y][x] = 99
                self.locked[y][x] = True

    # ---- output ---------------------------------------------------------
    def despeckle(self):
        """Kill lone shade pixels so the ramps read as smooth form."""
        for _ in range(1):
            snap = [r[:] for r in self.lvl]
            msnap = [r[:] for r in self.mat]
            for y in range(1, self.h - 1):
                for x in range(1, self.w - 1):
                    if self.locked[y][x] or msnap[y][x] is None or self.raw[y][x]:
                        continue
                    m = msnap[y][x]
                    same = []
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if msnap[y + dy][x + dx] == m:
                            same.append(snap[y + dy][x + dx])
                    if len(same) >= 4 and snap[y][x] not in same:
                        if same.count(same[0]) == 4:
                            self.lvl[y][x] = same[0]

    def pixels(self):
        """-> dict (x,y) -> (r,g,b,a) including the black outline."""
        out = {}
        for y in range(self.h):
            for x in range(self.w):
                if self.raw[y][x] is not None:
                    out[(x, y)] = self.raw[y][x]
                elif self.mat[y][x] is not None:
                    out[(x, y)] = self.pal[self.mat[y][x]][self.lvl[y][x]]
        # outline: any empty pixel touching a filled one (8-neighbour)
        edge = {}
        for (x, y) in list(out.keys()):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h and (xx, yy) not in out:
                        edge[(xx, yy)] = self.outline
        out.update(edge)
        return out

    def to_image(self):
        from PIL import Image
        im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = im.load()
        for (x, y), c in self.pixels().items():
            px[x, y] = c
        return im


# --------------------------------------------------------------------------
def _ramp_index(d, n):
    """map diffuse 0..1 to a ramp index, weighted so mid-tones dominate"""
    stops = {
        4: (0.80, 0.58, 0.34),
        5: (0.84, 0.66, 0.46, 0.26),
        6: (0.86, 0.72, 0.56, 0.40, 0.22),
        7: (0.88, 0.76, 0.63, 0.50, 0.36, 0.20),
    }[n]
    for i, s in enumerate(stops):
        if d >= s:
            return i
    return n - 1


def _clampi(v, a, b):
    return a if v < a else (b if v > b else v)


def _hex(c):
    if isinstance(c, tuple):
        return c
    c = c.lstrip("#")
    if len(c) == 6:
        c += "ff"
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4, 6))


# --------------------------------------------------------------------------
def mirror_x(pts, axis):
    return [(2 * axis - x, y) for (x, y) in pts]


def polyline(pts):
    """integer bresenham chain through pts"""
    out = []
    for i in range(len(pts) - 1):
        x0, y0 = int(pts[i][0]), int(pts[i][1])
        x1, y1 = int(pts[i + 1][0]), int(pts[i + 1][1])
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            out.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
    return out


def save_strip(images, path, pad=0):
    from PIL import Image
    w = sum(i.width for i in images) + pad * (len(images) - 1)
    h = max(i.height for i in images)
    sheet = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for im in images:
        sheet.paste(im, (x, 0), im)
        x += im.width + pad
    sheet.save(path)
    return sheet
