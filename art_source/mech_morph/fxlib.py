"""Generic mask / shading helpers for arbitrary canvas sizes (effects sprites)."""
import math

def hexc(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)

BLACK = (0, 0, 0, 255)

PAL = {
    'k': '000000',
    # energy (mech laser family)
    'W': 'ffffff', 'P': 'ffe8ec', 'r': 'ff9aa8', 'R': 'e8566a', 'X': 'ac3232', 'V': '6e1e22',
    # dust (warm neutrals), light -> deep
    '1': 'f6ecd6', '2': 'dcc8a4', '3': 'b49c7a', '4': '86725a', '5': '5c4e40',
    # rock
    'a': 'd6d2c8', 'b': 'a09a8e', 'c': '716b62', 'd': '48433c',
    # torn soil
    'e': '7a5a3a', 'f': '543c26', 'g': '36261a',
}
PALC = {k: hexc(v) for k, v in PAL.items()}
DUST = [PALC[c] for c in '12345']
ROCK = [PALC[c] for c in 'abcd']
SOIL = [PALC[c] for c in 'efg']


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = [[None] * w for _ in range(h)]

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = [row[:] for row in self.px]
        return c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def put(self, x, y, c, only_empty=False):
        if 0 <= x < self.w and 0 <= y < self.h:
            if only_empty and self.px[y][x] is not None:
                return
            self.px[y][x] = c

    def stamp(self, grid, x0, y0, only_empty=False, wrap=False):
        rows = grid.strip('\n').split('\n')
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in '. ':
                    continue
                x = x0 + dx
                if wrap:
                    x %= self.w
                self.put(x, y0 + dy, PALC[ch], only_empty)

    def paste(self, other, ox=0, oy=0):
        for y in range(other.h):
            for x in range(other.w):
                p = other.px[y][x]
                if p is not None:
                    self.put(x + ox, y + oy, p)

    def rgba(self):
        return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in self.px]


def empty_mask(w, h):
    return [[False] * w for _ in range(h)]

def ell_mask(w, h, cx, cy, rx, ry, wrap=False):
    m = empty_mask(w, h)
    for y in range(h):
        for x in range(w):
            dxs = [x + 0.5 - cx]
            if wrap:
                dxs += [x + 0.5 - cx - w, x + 0.5 - cx + w]
            for dx in dxs:
                if (dx / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    m[y][x] = True
                    break
    return m

def poly_mask(w, h, pts):
    m = empty_mask(w, h)
    n = len(pts)
    for y in range(h):
        cy = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= cy < y2) or (y2 <= cy < y1):
                xs.append(x1 + (cy - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(w):
                if xs[i] <= x + 0.5 <= xs[i + 1]:
                    m[y][x] = True
    return m

def union(*ms):
    h, w = len(ms[0]), len(ms[0][0])
    return [[any(m[y][x] for m in ms) for x in range(w)] for y in range(h)]

def sub(a, b):
    return [[a[y][x] and not b[y][x] for x in range(len(a[0]))] for y in range(len(a))]

def count(m):
    return sum(sum(1 for v in row if v) for row in m)

LIGHT = (-0.55, -0.75, 0.9)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)

def shade(mask, R, thresholds, vbias=0.15, wrap=False):
    h, w = len(mask), len(mask[0])
    ys = [y for y in range(h) for x in range(w) if mask[y][x]]
    if not ys:
        return [[None] * w for _ in range(h)]
    y0, y1 = min(ys), max(ys)
    Rr = int(R) + 2

    def inside(xx, yy):
        if wrap:
            xx %= w
        return 0 <= yy < h and 0 <= xx < w and mask[yy][xx]

    hgt = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            best = Rr
            for dy in range(-Rr, Rr + 1):
                for dx in range(-Rr, Rr + 1):
                    if not inside(x + dx, y + dy):
                        d = math.sqrt(dx * dx + dy * dy) - 0.5
                        best = min(best, d)
            t = min(best, R) / R
            hgt[y][x] = R * math.sqrt(max(0.0, 1 - (1 - t) ** 2))
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            def g(xx, yy):
                if inside(xx, yy):
                    return hgt[yy][xx % w if wrap else xx]
                return 0.0
            gx = (g(x + 1, y) - g(x - 1, y)) / 2
            gy = (g(x, y + 1) - g(x, y - 1)) / 2
            nx, ny, nz = -gx, -gy, 1.0
            nl = math.sqrt(nx * nx + ny * ny + nz * nz)
            I = (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / nl
            if y1 > y0:
                I += vbias * (0.5 - (y - y0) / (y1 - y0))
            idx = len(thresholds)
            for i, th in enumerate(thresholds):
                if I >= th:
                    idx = i
                    break
            out[y][x] = idx
    # remove isolated tones
    for _ in range(2):
        chg = []
        for y in range(h):
            for x in range(w):
                if out[y][x] is None:
                    continue
                nb = []
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if wrap:
                        xx %= w
                    if 0 <= xx < w and 0 <= yy < h and out[yy][xx] is not None:
                        nb.append(out[yy][xx])
                if len(nb) >= 3 and out[y][x] not in nb:
                    chg.append((x, y, max(set(nb), key=nb.count)))
        for x, y, v in chg:
            out[y][x] = v
    return out

TH4 = [0.93, 0.72, 0.5]          # 4 tones
TH5 = [0.95, 0.8, 0.62, 0.42]    # 5 tones

def render(cv, mask, ramp, R=4, th=TH4, outline=True, vbias=0.15, wrap=False, outline_col=BLACK):
    idx = shade(mask, R, th, vbias, wrap)
    h, w = len(mask), len(mask[0])
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                cv.px[y][x] = ramp[min(idx[y][x], len(ramp) - 1)]
    if outline:
        for y in range(h):
            for x in range(w):
                if not mask[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if wrap:
                        xx %= w
                    if not (0 <= xx < w and 0 <= yy < h) or not mask[yy][xx]:
                        cv.px[y][x] = outline_col
                        break

def line(cv, x0, y0, x1, y1, col, only_empty=False):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / n
        cv.put(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), col, only_empty)

class RNG:
    def __init__(self, seed):
        self.s = seed & 0x7fffffff
    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7fffffff
        return self.s
    def uniform(self, a, b):
        return a + (b - a) * ((self.next() >> 8) % 10000) / 10000.0
    def choice(self, seq):
        return seq[(self.next() >> 8) % len(seq)]
