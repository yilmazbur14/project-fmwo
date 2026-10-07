"""Grid painting helpers for authoring Burak's frames as text."""
from common import *


class G:
    def __init__(self, w=48, h=48, base=None):
        self.w, self.h = w, h
        self.c = [['.'] * w for _ in range(h)]
        if base is not None:
            for y in range(h):
                for x in range(w):
                    self.c[y][x] = base.c[y][x]

    def copy(self):
        return G(self.w, self.h, self)

    def put(self, x, y, s):
        for i, ch in enumerate(s):
            if ch == ' ':
                continue  # space = leave as is
            if 0 <= x + i < self.w and 0 <= y < self.h:
                self.c[y][x + i] = ch
        return self

    def block(self, x, y, lines):
        for j, s in enumerate(lines):
            self.put(x, y + j, s)
        return self

    def clear(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.c[y][x] = '.'
        return self

    def shift(self, dx, dy, x0=0, y0=0, x1=None, y1=None):
        """Move the pixels in the box by dx,dy (box cleared first)."""
        x1 = self.w - 1 if x1 is None else x1
        y1 = self.h - 1 if y1 is None else y1
        px = [(x, y, self.c[y][x]) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if self.c[y][x] != '.']
        self.clear(x0, y0, x1, y1)
        for x, y, ch in px:
            if 0 <= x + dx < self.w and 0 <= y + dy < self.h:
                self.c[y + dy][x + dx] = ch
        return self

    def mirror(self):
        g = G(self.w, self.h)
        for y in range(self.h):
            g.c[y] = list(reversed(self.c[y]))
        return g

    def rows(self):
        return [''.join(r) for r in self.c]

    def img(self):
        return grid_to_img(self.rows())


def from_sheet(sheet, col, row, cw=32, ch=32, dx=8, dy=8, w=48, h=48):
    inv = {v[:3]: k for k, v in BURAK.items()}
    g = G(w, h)
    px = sheet.load()
    for y in range(ch):
        for x in range(cw):
            p = px[col * cw + x, row * ch + y]
            if p[3] > 0:
                g.c[y + dy][x + dx] = inv[p[:3]]
    return g
