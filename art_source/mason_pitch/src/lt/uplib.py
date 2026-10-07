"""Shared helpers for the uppercut finisher art (pure python, no PIL).
Canvas of hex strings (None = transparent), grid stamping, strip assembly,
zoomed previews, palette/alpha validation."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png

DB32_HEX = ['000000', '222034', '45283c', '663931', '8f563b', 'df7126', 'd9a066', 'eec39a',
            'fbf236', '99e550', '6abe30', '37946e', '4b692f', '524b24', '323c39', '3f3f74',
            '306082', '5b6ee1', '639bff', '5fcde4', 'cbdbfc', 'ffffff', '9badb7', '847e87',
            '696a6a', '595652', '76428a', 'ac3232', 'd95763', 'd77bba', '8f974a', '8a6f30']
DB32 = set(DB32_HEX)

# The in-game player sprite's own 7-colour palette (player_4dir_sheet.png).
# Five of these are NOT DB32; they are kept so the uppercut is the same character.
PLAYER = {
    'b': 'd79864',  # skin light
    'd': 'ac714f',  # skin shadow
    'c': '000000',  # hair / shoes
    'e': 'ac3232',  # headband
    'a': '2464bd',  # blue base (gloves, shorts)
    'f': '162fbb',  # blue dark
    'g': '3883c9',  # blue light
}
PLAYER_SET = set(PLAYER.values())

# DB32 effect colours
FX = {
    'W': 'ffffff',  # white core
    'P': 'cbdbfc',  # pale blue
    'C': '5fcde4',  # cyan
    'L': '639bff',  # light blue
    'R': '5b6ee1',  # royal blue
    'I': '3f3f74',  # indigo
    'N': '222034',  # navy
    'Y': 'fbf236',  # yellow
    'E': 'eec39a',  # cream
    'T': 'd9a066',  # tan gold
    'O': 'df7126',  # orange
    'G': '9badb7',  # grey-blue (dust shade)
    'K': '000000',  # black
}
PAL = dict(PLAYER)
PAL.update(FX)


def hex2rgb(h):
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[None] * w for _ in range(h)]

    def copy(self):
        c = Canvas(self.w, self.h)
        c.p = [row[:] for row in self.p]
        return c

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, c):
        if self.inb(x, y):
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x] if self.inb(x, y) else None

    def stamp(self, rows, ox, oy, pal=PAL, skip='.'):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == skip or ch == ' ':
                    continue
                if ch not in pal:
                    raise KeyError('char %r not in palette (row %d col %d)' % (ch, j, i))
                self.set(ox + i, oy + j, pal[ch])

    def blit(self, other, ox, oy, under=False):
        for y in range(other.h):
            for x in range(other.w):
                v = other.p[y][x]
                if v is None:
                    continue
                X, Y = ox + x, oy + y
                if not self.inb(X, Y):
                    continue
                if under and self.p[Y][X] is not None:
                    continue
                self.p[Y][X] = v

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

    def rgba(self):
        return [[(hex2rgb(v) + (255,)) if v else (0, 0, 0, 0) for v in row] for row in self.p]

    def save(self, path):
        write_png(path, self.w, self.h, self.rgba())

    def colours(self):
        return {v for row in self.p for v in row if v}


def from_png(path):
    w, h, px = read_png(path)
    c = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            p = px[y][x]
            if p[3] == 255:
                c.p[y][x] = '%02x%02x%02x' % p[:3]
            elif p[3] != 0:
                raise ValueError('partial alpha in %s at %d,%d' % (path, x, y))
    return c


def strip(frames):
    w, h = frames[0].w, frames[0].h
    s = Canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        assert (f.w, f.h) == (w, h)
        s.blit(f, i * w, 0)
    return s


def zoom_rgba(c, s, bg=(0, 0, 0), grid=None, grid_col=(255, 255, 255)):
    out = []
    for y in range(c.h):
        row = []
        for x in range(c.w):
            v = c.p[y][x]
            px = hex2rgb(v) + (255,) if v else bg + (255,)
            row.extend([px] * s)
        for _ in range(s):
            out.append(list(row))
    if grid:
        gw, gh = grid
        for Y in range(c.h * s):
            for f in range(1, c.w // gw):
                out[Y][f * gw * s] = grid_col + (255,)
    return c.w * s, c.h * s, out


def save_zoom(c, path, s, bg=(0, 0, 0), grid=None):
    W, H, px = zoom_rgba(c, s, bg, grid)
    write_png(path, W, H, px)
