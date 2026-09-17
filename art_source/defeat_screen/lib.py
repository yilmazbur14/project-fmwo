"""Tiny raster library for the defeat screen art. Pixels are hex strings
('rrggbb') or None (transparent). Pure python, no PIL."""
import math
from pngio import read_png, write_png

DB32 = """000000 222034 45283c 663931 8f563b df7126 d9a066 eec39a fbf236 99e550
6abe30 37946e 4b692f 524b24 323c39 3f3f74 306082 5b6ee1 639bff 5fcde4 cbdbfc
ffffff 9badb7 847e87 696a6a 595652 76428a ac3232 d95763 d77bba 8f974a 8a6f30""".split()
DB32_SET = set(DB32)

# named colours (all DB32)
K = '000000'      # outline
NAVY = '222034'
PLUM = '45283c'
BROWN_D = '663931'
BROWN = '8f563b'
ORANGE = 'df7126'
TAN = 'd9a066'
SKIN_L = 'eec39a'
YELLOW = 'fbf236'
LIME = '99e550'
GREEN = '6abe30'
TEAL = '37946e'
GREEN_D = '4b692f'
OLIVE_D = '524b24'
SLATE = '323c39'
INDIGO = '3f3f74'
BLUE_D = '306082'
BLURPLE = '5b6ee1'
BLUE_L = '639bff'
CYAN = '5fcde4'
ICE = 'cbdbfc'
WHITE = 'ffffff'
GREY_L = '9badb7'
GREY = '847e87'
GREY_M = '696a6a'
GREY_D = '595652'
PURPLE = '76428a'
RED = 'ac3232'
RED_L = 'd95763'
PINK = 'd77bba'
OLIVE = '8f974a'
BRASS = '8a6f30'

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    """threshold in (0,1)"""
    return (BAYER4[y % 4][x % 4] + 0.5) / 16.0


def mix(x, y, a, b, t):
    """ordered dither between a (t=0) and b (t=1)"""
    return b if t > bayer(x, y) else a


def checker(x, y, a, b):
    return a if (x + y) % 2 == 0 else b


class Img:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def copy(self):
        o = Img(self.w, self.h)
        o.p = [row[:] for row in self.p]
        return o

    def blit(self, src, ox, oy):
        for y in range(src.h):
            for x in range(src.w):
                c = src.p[y][x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def rect(self, x0, y0, x1, y1, c):
        """inclusive"""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        for x, y in line_pts(x0, y0, x1, y1):
            self.set(x, y, c)

    def stamp(self, rows, ox, oy, pal):
        """rows: strings; '.' / ' ' skip; other chars via pal"""
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in '. ':
                    continue
                self.set(ox + x, oy + y, pal[ch])

    def save(self, path, bg=None):
        rows = []
        for y in range(self.h):
            r = []
            for x in range(self.w):
                c = self.p[y][x]
                if c is None:
                    r.append(bg if bg is not None else (0, 0, 0, 0))
                else:
                    r.append((int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255))
            rows.append(r)
        write_png(path, self.w, self.h, rows)

    def scaled(self, s):
        o = Img(self.w * s, self.h * s)
        for y in range(o.h):
            row = self.p[y // s]
            o.p[y] = [row[x // s] for x in range(o.w)]
        return o

    def crop(self, x, y, w, h):
        o = Img(w, h)
        for yy in range(h):
            for xx in range(w):
                o.p[yy][xx] = self.get(x + xx, y + yy)
        return o

    def check_db32(self):
        bad = set()
        for row in self.p:
            for c in row:
                if c is not None and c not in DB32_SET:
                    bad.add(c)
        return bad


def load(path):
    w, h, px = read_png(path)
    im = Img(w, h)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[y][x]
            im.p[y][x] = '%02x%02x%02x' % (r, g, b) if a else None
    return im


def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def in_poly(px, py, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > py) != (yj > py):
            xc = (xj - xi) * (py - yi) / (yj - yi) + xi
            if px < xc:
                inside = not inside
        j = i
    return inside


def poly_mask(poly, w, h):
    """set of (x,y) whose pixel centre is inside poly"""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    m = set()
    for y in range(max(0, int(min(ys)) - 1), min(h, int(max(ys)) + 2)):
        for x in range(max(0, int(min(xs)) - 1), min(w, int(max(xs)) + 2)):
            if in_poly(x + 0.5, y + 0.5, poly):
                m.add((x, y))
    return m


def ellipse_mask(cx, cy, rx, ry):
    m = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m.add((x, y))
    return m


def outline_of(mask, diag=False):
    """pixels outside mask touching it"""
    o = set()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for (x, y) in mask:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in mask:
                o.add(q)
    return o


def inner_edge(mask):
    """mask pixels touching outside (4-neighbour)"""
    e = set()
    for (x, y) in mask:
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if (x + dx, y + dy) not in mask:
                e.add((x, y))
                break
    return e


def dist_to_seg(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L2))
    cx, cy = ax + t * vx, ay + t * vy
    return math.hypot(px - cx, py - cy), cx, cy, t


def capsule_mask(ax, ay, bx, by, ra, rb):
    """tapered capsule: radius ra at a, rb at b"""
    m = set()
    r = max(ra, rb)
    for y in range(int(min(ay, by) - r) - 1, int(max(ay, by) + r) + 2):
        for x in range(int(min(ax, bx) - r) - 1, int(max(ax, bx) + r) + 2):
            d, cx, cy, t = dist_to_seg(x + 0.5, y + 0.5, ax, ay, bx, by)
            if d <= ra + (rb - ra) * t:
                m.add((x, y))
    return m


def norm3(x, y, z):
    L = math.sqrt(x * x + y * y + z * z) or 1.0
    return x / L, y / L, z / L


def zoom_save(img, path, s, bg='303030'):
    o = img.scaled(s)
    rows = []
    for y in range(o.h):
        r = []
        for x in range(o.w):
            c = o.p[y][x]
            if c is None:
                v = 200 if ((x // (s * 2) + y // (s * 2)) % 2 == 0) else 170
                r.append((v, v, v, 255))
            else:
                r.append((int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), 255))
        rows.append(r)
    write_png(path, o.w, o.h, rows)
