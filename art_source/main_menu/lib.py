"""Shared helpers for the main-menu art: DB32 canvas, dithering, tiny font, PNG io."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png as _read_png, write_png
import time as _time


def read_png(path, tries=4):
    """pngio.read_png with a retry: a freshly written file occasionally fails to decode on the first read here."""
    for k in range(tries):
        try:
            return _read_png(path)
        except Exception:
            if k == tries - 1:
                raise
            _time.sleep(0.3)

DB32_HEX = ['000000', '222034', '45283c', '663931', '8f563b', 'df7126', 'd9a066', 'eec39a',
            'fbf236', '99e550', '6abe30', '37946e', '4b692f', '524b24', '323c39', '3f3f74',
            '306082', '5b6ee1', '639bff', '5fcde4', 'cbdbfc', 'ffffff', '9badb7', '847e87',
            '696a6a', '595652', '76428a', 'ac3232', 'd95763', 'd77bba', '8f974a', '8a6f30']
DB32 = {h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in DB32_HEX}
DB32_SET = set(DB32.values())

# names
K = '000000'; N0 = '222034'; P0 = '45283c'; BR = '663931'; BR2 = '8f563b'; OR = 'df7126'
TN = 'd9a066'; SK = 'eec39a'; YL = 'fbf236'; LG = '99e550'; GR = '6abe30'; TE = '37946e'
OG = '4b692f'; OL = '524b24'; G1 = '323c39'; IN = '3f3f74'; BL = '306082'; RB = '5b6ee1'
SB = '639bff'; CY = '5fcde4'; WH2 = 'cbdbfc'; WH = 'ffffff'; G5 = '9badb7'; G4 = '847e87'
G3 = '696a6a'; G2 = '595652'; PU = '76428a'; RD = 'ac3232'; PK = 'd95763'; MG = 'd77bba'
KH = '8f974a'; GO = '8a6f30'

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dith(x, y, t):
    """ordered dither: True on a fraction t of pixels"""
    return (BAYER4[y % 4][x % 4] + 0.5) / 16.0 < t


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is not None:
                assert c in DB32, c
            self.p[y][x] = c

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return None

    def rect(self, x0, y0, x1, y1, c):
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
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def grid(self, x0, y0, rows, cmap, skip=' .'):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in skip:
                    continue
                if ch not in cmap:
                    raise KeyError('char %r not in map (row %d)' % (ch, j))
                self.set(x0 + i, y0 + j, cmap[ch])

    def blit(self, other, x0, y0):
        for y in range(other.h):
            for x in range(other.w):
                c = other.p[y][x]
                if c is not None:
                    self.set(x0 + x, y0 + y, c)

    def copy(self):
        c = Canvas(self.w, self.h)
        c.p = [row[:] for row in self.p]
        return c

    def to_rgba(self):
        return [[(DB32[c] + (255,)) if c is not None else (0, 0, 0, 0) for c in row] for row in self.p]

    def save(self, path):
        write_png(path, self.w, self.h, self.to_rgba())
        validate_png(path, self.w, self.h)
        return path

    @staticmethod
    def load(path):
        w, h, px = read_png(path)
        rev = {v: k for k, v in DB32.items()}
        c = Canvas(w, h)
        for y in range(h):
            for x in range(w):
                p = px[y][x]
                c.p[y][x] = None if p[3] == 0 else rev[p[:3]]
        return c


def validate_png(path, w=None, h=None):
    W, H, px = read_png(path)
    if w is not None:
        assert (W, H) == (w, h), 'size %dx%d expected %dx%d' % (W, H, w, h)
    bad = set()
    for row in px:
        for p in row:
            if p[3] == 0:
                continue
            assert p[3] == 255, 'partial alpha %r in %s' % (p, path)
            if p[:3] not in DB32_SET:
                bad.add(p[:3])
    assert not bad, 'non-DB32 colours in %s: %r' % (path, sorted(bad)[:10])
    return W, H


def crop_zoom(src, out, x0, y0, w, h, s):
    W, H, px = read_png(src)
    o = []
    for j in range(h * s):
        r = []
        for i in range(w * s):
            yy, xx = y0 + j // s, x0 + i // s
            p = px[yy][xx] if (0 <= yy < H and 0 <= xx < W) else (255, 0, 255, 255)
            if p[3] == 0:
                c = 200 if ((i // (s * 2) + j // (s * 2)) % 2 == 0) else 170
                p = (c, c, c, 255)
            r.append(p)
        o.append(r)
    write_png(out, w * s, h * s, o)


# ------------------------------------------------------------------ tiny 3x5 font
F35 = {
    'A': ['.#.', '#.#', '###', '#.#', '#.#'], 'B': ['##.', '#.#', '##.', '#.#', '##.'],
    'C': ['.##', '#..', '#..', '#..', '.##'], 'D': ['##.', '#.#', '#.#', '#.#', '##.'],
    'E': ['###', '#..', '##.', '#..', '###'], 'F': ['###', '#..', '##.', '#..', '#..'],
    'G': ['.##', '#..', '#.#', '#.#', '.##'], 'H': ['#.#', '#.#', '###', '#.#', '#.#'],
    'I': ['###', '.#.', '.#.', '.#.', '###'], 'J': ['..#', '..#', '..#', '#.#', '.#.'],
    'K': ['#.#', '#.#', '##.', '#.#', '#.#'], 'L': ['#..', '#..', '#..', '#..', '###'],
    'M': ['#.#', '###', '###', '#.#', '#.#'], 'N': ['##.', '#.#', '#.#', '#.#', '#.#'],
    'O': ['.#.', '#.#', '#.#', '#.#', '.#.'], 'P': ['##.', '#.#', '##.', '#..', '#..'],
    'Q': ['.#.', '#.#', '#.#', '##.', '.##'], 'R': ['##.', '#.#', '##.', '#.#', '#.#'],
    'S': ['.##', '#..', '.#.', '..#', '##.'], 'T': ['###', '.#.', '.#.', '.#.', '.#.'],
    'U': ['#.#', '#.#', '#.#', '#.#', '###'], 'V': ['#.#', '#.#', '#.#', '#.#', '.#.'],
    'W': ['#.#', '#.#', '###', '###', '#.#'], 'X': ['#.#', '#.#', '.#.', '#.#', '#.#'],
    'Y': ['#.#', '#.#', '.#.', '.#.', '.#.'], 'Z': ['###', '..#', '.#.', '#..', '###'],
    '0': ['###', '#.#', '#.#', '#.#', '###'], '1': ['.#.', '##.', '.#.', '.#.', '###'],
    '2': ['##.', '..#', '.#.', '#..', '###'], '3': ['##.', '..#', '.#.', '..#', '##.'],
    '4': ['#.#', '#.#', '###', '..#', '..#'], '5': ['###', '#..', '##.', '..#', '##.'],
    '6': ['.##', '#..', '###', '#.#', '###'], '7': ['###', '..#', '.#.', '.#.', '.#.'],
    '8': ['###', '#.#', '###', '#.#', '###'], '9': ['###', '#.#', '###', '..#', '##.'],
    '#': ['#.#', '###', '#.#', '###', '#.#'], '-': ['...', '...', '###', '...', '...'],
    ' ': ['.', '.', '.', '.', '.'], '@': ['###', '#.#', '#.#', '#..', '###'],
    '!': ['#', '#', '#', '.', '#'], '.': ['.', '.', '.', '.', '#'],
}


def text35(c, x, y, s, col, spacing=1):
    for ch in s:
        g = F35[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == '#':
                    c.set(x + i, y + j, col)
        x += len(g[0]) + spacing
    return x


def text35_width(s, spacing=1):
    return sum(len(F35[ch][0]) + spacing for ch in s) - spacing
