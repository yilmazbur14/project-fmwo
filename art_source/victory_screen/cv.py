"""Tiny DB32 pixel canvas for the victory screen art. Pure python."""
from pngio import read_png, write_png

DB32 = """000000 222034 45283c 663931 8f563b df7126 d9a066 eec39a fbf236 99e550
6abe30 37946e 4b692f 524b24 323c39 3f3f74 306082 5b6ee1 639bff 5fcde4 cbdbfc
ffffff 9badb7 847e87 696a6a 595652 76428a ac3232 d95763 d77bba 8f974a 8a6f30""".split()
DB = set(DB32)

# named colours
K = '000000'; NAVY = '222034'; PLUM = '45283c'; BROWN = '663931'; RUST = '8f563b'
ORANGE = 'df7126'; TAN = 'd9a066'; SKIN = 'eec39a'; YEL = 'fbf236'; LIME = '99e550'
GREEN = '6abe30'; TEAL = '37946e'; OLIVE = '4b692f'; MUD = '524b24'; SLATE = '323c39'
INDIGO = '3f3f74'; STEEL = '306082'; BLURPLE = '5b6ee1'; SKY = '639bff'; CYAN = '5fcde4'
PALE = 'cbdbfc'; WHITE = 'ffffff'; GREY = '9badb7'; DGREY = '847e87'; ASH = '696a6a'
DASH = '595652'; PURPLE = '76428a'; RED = 'ac3232'; PINK = 'd95763'; ROSE = 'd77bba'
KHAKI = '8f974a'; BRASS = '8a6f30'


def rgba(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, c):
        if self.inb(x, y):
            if c is not None:
                assert c in DB, c
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x] if self.inb(x, y) else None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def paint(self, mask, c):
        for (x, y) in mask:
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        for (x, y) in line_pts(x0, y0, x1, y1):
            self.set(x, y, c)

    def grid(self, rows, pal, ox, oy, flipx=False):
        for j, r in enumerate(rows):
            if flipx:
                r = r[::-1]
            for i, ch in enumerate(r):
                if ch in ('.', ' '):
                    continue
                self.set(ox + i, oy + j, pal[ch])

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                c = other.p[y][x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def to_pix(self):
        T = (0, 0, 0, 0)
        return [[rgba(c) if c else T for c in row] for row in self.p]

    def save(self, path):
        write_png(path, self.w, self.h, self.to_pix())

    def crop(self, x, y, w, h):
        o = Canvas(w, h)
        for j in range(h):
            for i in range(w):
                o.p[j][i] = self.get(x + i, y + j)
        return o


def load(path):
    w, h, px = read_png(path)
    c = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            q = px[y][x]
            if q[3] == 0:
                continue
            c.p[y][x] = '%02x%02x%02x' % q[:3]
    return c


def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
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


def poly_mask(pts):
    """Even-odd scanline fill sampled at pixel centres."""
    m = set()
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        yc = y + 0.5
        xs = []
        for i in range(n):
            (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
            if (ya <= yc < yb) or (yb <= yc < ya):
                xs.append(xa + (yc - ya) * (xb - xa) / (yb - ya))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = xs[k], xs[k + 1]
            x = int(xa - 0.5) - 1
            while x + 0.5 < xb:
                if x + 0.5 >= xa:
                    m.add((x, y))
                x += 1
    return m


def ellipse_mask(cx, cy, rx, ry):
    """cx,cy may be .5 values; pixel centre inside test."""
    m = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                m.add((x, y))
    return m


N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))


def outer_ring(mask, nb=N4):
    out = set()
    for (x, y) in mask:
        for dx, dy in nb:
            q = (x + dx, y + dy)
            if q not in mask:
                out.add(q)
    return out


def inner_edge(mask, nb=N4):
    return {(x, y) for (x, y) in mask if any((x + dx, y + dy) not in mask for dx, dy in nb)}


def mirror(mask, axis2):
    """mirror about x = axis2/2 - 0.5... i.e. x' = axis2 - x (axis2 = 2*centre-1)."""
    return {(axis2 - x, y) for (x, y) in mask}


# 3x5 pixel font (caps, digits, a few symbols)
FONT = {
    'A': ["###", "#.#", "###", "#.#", "#.#"], 'B': ["##.", "#.#", "##.", "#.#", "##."],
    'C': ["###", "#..", "#..", "#..", "###"], 'D': ["##.", "#.#", "#.#", "#.#", "##."],
    'E': ["###", "#..", "##.", "#..", "###"], 'F': ["###", "#..", "##.", "#..", "#.."],
    'G': ["###", "#..", "#.#", "#.#", "###"], 'H': ["#.#", "#.#", "###", "#.#", "#.#"],
    'I': ["###", ".#.", ".#.", ".#.", "###"], 'J': ["..#", "..#", "..#", "#.#", "###"],
    'K': ["#.#", "#.#", "##.", "#.#", "#.#"], 'L': ["#..", "#..", "#..", "#..", "###"],
    'M': ["#.#", "###", "###", "#.#", "#.#"], 'N': ["##.", "#.#", "#.#", "#.#", "#.#"],
    'O': ["###", "#.#", "#.#", "#.#", "###"], 'P': ["###", "#.#", "###", "#..", "#.."],
    'R': ["##.", "#.#", "##.", "#.#", "#.#"], 'S': ["###", "#..", "###", "..#", "###"],
    'T': ["###", ".#.", ".#.", ".#.", ".#."], 'U': ["#.#", "#.#", "#.#", "#.#", "###"],
    'V': ["#.#", "#.#", "#.#", "#.#", ".#."], 'W': ["#.#", "#.#", "###", "###", "#.#"],
    'Y': ["#.#", "#.#", ".#.", ".#.", ".#."], 'Z': ["###", "..#", ".#.", "#..", "###"],
    '0': ["###", "#.#", "#.#", "#.#", "###"], '1': [".#.", "##.", ".#.", ".#.", "###"],
    '2': ["##.", "..#", ".#.", "#..", "###"], '3': ["##.", "..#", ".#.", "..#", "##."],
    '4': ["#.#", "#.#", "###", "..#", "..#"], '5': ["###", "#..", "##.", "..#", "##."],
    '6': [".##", "#..", "###", "#.#", "###"], '7': ["###", "..#", ".#.", ".#.", ".#."],
    '8': ["###", "#.#", "###", "#.#", "###"], '9': ["###", "#.#", "###", "..#", "##."],
    '#': [".#.#.", "#####", ".#.#.", "#####", ".#.#."], '@': [".####.", "#....#", "#.##.#", "#.####", "#.....", ".####."],
    '+': ["...", ".#.", "###", ".#.", "..."], '-': ["...", "...", "###", "...", "..."],
    '!': [".#.", ".#.", ".#.", "...", ".#."], ' ': ["...", "...", "...", "...", "..."],
    '<': ["..#", ".#.", "#..", ".#.", "..#"], '3s': ["##.", "..#", ".#.", "..#", "##."],
}


def text_w(s):
    return sum(len(FONT[ch][0]) + 1 for ch in s) - 1


def text(cv, s, x, y, c):
    for ch in s:
        g = FONT[ch]
        for j, r in enumerate(g):
            for i, t in enumerate(r):
                if t == '#':
                    cv.set(x + i, y + j, c)
        x += len(g[0]) + 1
