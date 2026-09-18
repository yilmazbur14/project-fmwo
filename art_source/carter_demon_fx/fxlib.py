"""Effects toolkit for Carter's RAGING DEMON sequence.

carter_akuma/lib.py is built around a fixed 96x96 body canvas with a volume
shading model - the wrong tool for effects, which come in seven different sizes
from 24x24 up to 640x360 and are made of gradients rather than anatomy.  So this
is a small arbitrary-size mask/canvas engine instead.  The PALETTE is imported
from carter_akuma/lib.py rather than copied, so the effects cannot drift away
from the cast's colours.

Gradients are the whole game here, and 8-bit gradients band.  Everything soft in
this file goes through `quant`, which ordered-dithers a continuous field into a
handful of palette steps, so a falloff is a dither pattern rather than a set of
visible contour rings.
"""
import os
import sys
import math

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'carter_akuma'))

from lib import RAMPS, hexc                      # noqa: E402  (shared palette)
from pngio import write_png, read_png, blank, paste, crop, scale  # noqa: E402

BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# Extra ramps this sequence needs, built to sit inside the existing cast
# palette.  'gold' is RAMPS['hair'] (Carter's beard orange) pushed to a hot
# yellow, so the fake light is a warm cousin of his own colour rather than a
# foreign hue.  'ink' is the darkness: RAMPS['gi'] violet end, pushed black.
RAMPS = dict(RAMPS)
RAMPS['gold'] = ['fffce0', 'ffe45c', 'ffc21e', 'd68a12', '8a5208', '4a2a04']
RAMPS['ink'] = ['2a1450', '1a0c34', '120826', '0c0518', '070310', '000000']


def ramp(name):
    return [hexc(c) for c in RAMPS[name]]


def rgba(c, a):
    """re-alpha a colour"""
    return (c[0], c[1], c[2], max(0, min(255, int(round(a)))))


# --------------------------------------------------------------------- masks

class Mask:
    """boolean grid; supports | & - ~ and morphology"""

    __slots__ = ('w', 'h', 'g')

    def __init__(self, w, h, g=None):
        self.w, self.h = w, h
        self.g = g if g is not None else [[False] * w for _ in range(h)]

    def __getitem__(self, y):
        return self.g[y]

    def _zip(self, o, f):
        return Mask(self.w, self.h,
                    [[f(self.g[y][x], o.g[y][x]) for x in range(self.w)]
                     for y in range(self.h)])

    def __or__(self, o):
        return self._zip(o, lambda a, b: a or b)

    def __and__(self, o):
        return self._zip(o, lambda a, b: a and b)

    def __sub__(self, o):
        return self._zip(o, lambda a, b: a and not b)

    def __invert__(self):
        return Mask(self.w, self.h,
                    [[not v for v in row] for row in self.g])

    def copy(self):
        return Mask(self.w, self.h, [row[:] for row in self.g])

    def count(self):
        return sum(sum(r) for r in self.g)

    def bbox(self):
        xs = [x for y in range(self.h) for x in range(self.w) if self.g[y][x]]
        ys = [y for y in range(self.h) for x in range(self.w) if self.g[y][x]]
        return (min(xs), min(ys), max(xs), max(ys)) if xs else None

    def grow(self, n=1, diag=False):
        m = self.copy()
        nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if diag:
            nb = nb + ((1, 1), (1, -1), (-1, 1), (-1, -1))
        for _ in range(n):
            nx = m.copy()
            for y in range(self.h):
                for x in range(self.w):
                    if m.g[y][x]:
                        for dx, dy in nb:
                            xx, yy = x + dx, y + dy
                            if 0 <= xx < self.w and 0 <= yy < self.h:
                                nx.g[yy][xx] = True
            m = nx
        return m

    def erode(self, n=1, diag=False):
        return ~((~self).grow(n, diag))

    def ring(self, n=1, diag=False):
        return self.grow(n, diag) - self

    def shift(self, dx, dy):
        m = Mask(self.w, self.h)
        for y in range(self.h):
            yy = y + dy
            if not (0 <= yy < self.h):
                continue
            for x in range(self.w):
                xx = x + dx
                if 0 <= xx < self.w and self.g[y][x]:
                    m.g[yy][xx] = True
        return m

    def mirror(self):
        return Mask(self.w, self.h, [row[::-1] for row in self.g])

    def flipv(self):
        return Mask(self.w, self.h, [row[:] for row in self.g[::-1]])

    def sym(self):
        return self | self.mirror()

    def sym4(self):
        m = self.sym()
        return m | m.flipv()

    def dither(self, level, off=0):
        """ordered-thin a mask; level 0..16, higher keeps more"""
        m = Mask(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] and _BAYER[(y + off) % 4][(x + off) % 4] < level:
                    m.g[y][x] = True
        return m


_BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
_B8 = [[(_BAYER[y % 4][x % 4] * 4 + _BAYER[(y // 4) % 4][(x // 4) % 4]) / 64.0
        for x in range(8)] for y in range(8)]


def bayer01(x, y):
    """ordered-dither threshold in [0,1) - 8x8, fine enough that a falloff
    reads as texture rather than as a checkerboard"""
    return _B8[y % 8][x % 8]


def poly(w, h, pts):
    """even-odd scanline fill, sampling pixel centres"""
    m = Mask(w, h)
    n = len(pts)
    for y in range(h):
        cy = y + 0.5
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= cy < y1) or (y1 <= cy < y0):
                xs.append(x0 + (cy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(w):
                if xs[i] <= x + 0.5 < xs[i + 1]:
                    m.g[y][x] = True
    return m


def ell(w, h, cx, cy, rx, ry):
    m = Mask(w, h)
    for y in range(h):
        dy = (y + 0.5 - cy) / max(1e-6, ry)
        for x in range(w):
            dx = (x + 0.5 - cx) / max(1e-6, rx)
            if dx * dx + dy * dy <= 1.0:
                m.g[y][x] = True
    return m


def rect(w, h, x0, y0, x1, y1):
    return poly(w, h, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def diamond(w, h, cx, cy, rx, ry):
    m = Mask(w, h)
    for y in range(h):
        dy = abs(y + 0.5 - cy) / max(1e-6, ry)
        for x in range(w):
            dx = abs(x + 0.5 - cx) / max(1e-6, rx)
            if dx + dy <= 1.0:
                m.g[y][x] = True
    return m


def ray(w, h, cx, cy, ang, r0, r1, wid0, wid1):
    """a tapered spike from radius r0 to r1 along `ang` (degrees, 0 = +x)"""
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    px, py = -uy, ux
    ax, ay = cx + ux * r0, cy + uy * r0
    bx, by = cx + ux * r1, cy + uy * r1
    return poly(w, h, [(ax + px * wid0, ay + py * wid0),
                       (bx + px * wid1, by + py * wid1),
                       (bx - px * wid1, by - py * wid1),
                       (ax - px * wid0, ay - py * wid0)])


def stamp_mask(w, h, grid, x0, y0):
    """mask from an ASCII block: any char but '.' and ' ' is set"""
    m = Mask(w, h)
    for dy, row in enumerate(grid.strip('\n').split('\n')):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x, y = x0 + dx, y0 + dy
            if 0 <= x < w and 0 <= y < h:
                m.g[y][x] = True
    return m


# ------------------------------------------------------------------- fields

def field(w, h, fn):
    return [[fn(x + 0.5, y + 0.5) for x in range(w)] for y in range(h)]


def radial_field(w, h, cx, cy, rx, ry, power=1.0):
    """1.0 at the centre falling to 0.0 on the ellipse rim"""
    def fn(x, y):
        dx, dy = (x - cx) / max(1e-6, rx), (y - cy) / max(1e-6, ry)
        d = math.sqrt(dx * dx + dy * dy)
        return max(0.0, 1.0 - d) ** power
    return field(w, h, fn)


def quant(fld, n):
    """ordered-dither a [0,1] field into integer steps 0..n-1.

    This is the anti-banding workhorse: instead of thresholding at fixed
    values (which draws contour rings), the fractional part is compared with an
    8x8 Bayer threshold, so the boundary between two steps becomes a gradient
    of dots."""
    h, w = len(fld), len(fld[0])
    out = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            t = max(0.0, min(1.0, fld[y][x])) * (n - 1)
            i = int(t)
            if i < n - 1 and (t - i) > bayer01(x, y):
                i += 1
            out[y][x] = i
    return out


# ------------------------------------------------------------------- canvas

class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def paint(self, mask, color):
        for y in range(self.h):
            for x in range(self.w):
                if mask.g[y][x]:
                    self.px[y][x] = color

    def paint_over(self, mask, color):
        """only where something is already drawn"""
        for y in range(self.h):
            for x in range(self.w):
                if mask.g[y][x] and self.px[y][x] is not None:
                    self.px[y][x] = color

    def erase(self, mask):
        for y in range(self.h):
            for x in range(self.w):
                if mask.g[y][x]:
                    self.px[y][x] = None

    def outline(self, mask, color=BLACK):
        self.paint(mask.ring(1, diag=True), color)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def mask_of(self):
        return Mask(self.w, self.h,
                    [[p is not None and p[3] > 0 for p in row] for row in self.px])

    def steps(self, fld, colors, mask=None, floor=0):
        """dither a field through a colour ramp (colors[0] = outermost).
        steps below `floor` stay transparent."""
        idx = quant(fld, len(colors))
        for y in range(self.h):
            for x in range(self.w):
                if mask is not None and not mask.g[y][x]:
                    continue
                i = idx[y][x]
                if i < floor:
                    continue
                self.px[y][x] = colors[i]

    def stamp(self, grid, x0, y0, pal):
        for dy, row in enumerate(grid.strip('\n').split('\n')):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                x, y = x0 + dx, y0 + dy
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                self.px[y][x] = None if ch == '_' else pal[ch]

    def rgba(self):
        return [[(p if p is not None else CLEAR) for p in row] for row in self.px]

    def save(self, path):
        write_png(path, self.w, self.h, self.rgba())
        return path


def sheet(frames, path):
    """lay canvases out as a horizontal strip and write it"""
    w, h = frames[0].w, frames[0].h
    out = blank(w * len(frames), h, CLEAR)
    for i, cv in enumerate(frames):
        paste(out, cv.rgba(), i * w, 0)
    write_png(path, w * len(frames), h, out)
    return path
