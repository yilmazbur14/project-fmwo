"""Shared helpers for the controls-screen art: DB32 palette, a simple canvas,
PNG save with strict palette validation, and preview helpers."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, upscale

DB32_HEX = ['000000', '222034', '45283c', '663931', '8f563b', 'df7126', 'd9a066', 'eec39a',
            'fbf236', '99e550', '6abe30', '37946e', '4b692f', '524b24', '323c39', '3f3f74',
            '306082', '5b6ee1', '639bff', '5fcde4', 'cbdbfc', 'ffffff', '9badb7', '847e87',
            '696a6a', '595652', '76428a', 'ac3232', 'd95763', 'd77bba', '8f974a', '8a6f30']
DB32 = {h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) for h in DB32_HEX}
DB32_SET = set(DB32.values())


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]  # hex string or None (transparent)

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
        """inclusive"""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
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

    def grid(self, x0, y0, rows, cmap, skip=' '):
        """Stamp an ASCII grid. chars in cmap -> colour, `skip` char leaves pixel as is."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == skip:
                    continue
                if ch not in cmap:
                    raise KeyError('char %r not in map (row %d)' % (ch, j))
                self.set(x0 + i, y0 + j, cmap[ch])

    def replace(self, x0, y0, x1, y1, src, dst):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.get(x, y) == src:
                    self.set(x, y, dst)

    def blit(self, other, x0, y0):
        for y in range(other.h):
            for x in range(other.w):
                c = other.p[y][x]
                if c is not None:
                    self.set(x0 + x, y0 + y, c)

    def to_rgba(self):
        out = []
        for row in self.p:
            out.append([(DB32[c] + (255,)) if c is not None else (0, 0, 0, 0) for c in row])
        return out

    def save(self, path):
        write_png(path, self.w, self.h, self.to_rgba())
        validate_png(path, self.w, self.h)
        return path


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


def zoom(src_png, out_png, s, bg='checker'):
    w, h, p = read_png(src_png)
    W, H, up = upscale(w, h, p, s, bg=bg)
    write_png(out_png, W, H, up)
    return out_png
