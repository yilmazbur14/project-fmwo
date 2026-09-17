"""Char-grid authoring: place ASCII runs at (x, y); spaces skip, '.' clears.  Render with a char->RGBA map."""
from lib import Canvas


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [['.'] * w for _ in range(h)]

    def put(self, x, y, s):
        for i, ch in enumerate(s):
            if ch == ' ':
                continue
            if 0 <= x + i < self.w and 0 <= y < self.h:
                self.g[y][x + i] = ch
        return self

    def rows(self, x, y, block):
        lines = block.strip('\n').split('\n')
        for j, ln in enumerate(lines):
            self.put(x, y + j, ln)
        return self

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.g[y][x]
        return '.'

    def copy(self):
        n = Grid(self.w, self.h)
        n.g = [r[:] for r in self.g]
        return n

    def shift(self, dx, dy):
        n = Grid(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] != '.':
                    X, Y = x + dx, y + dy
                    if 0 <= X < self.w and 0 <= Y < self.h:
                        n.g[Y][X] = self.g[y][x]
        return n

    def clear(self, x0, y0, x1, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    self.g[y][x] = '.'
        return self

    def canvas(self, cmap):
        cv = Canvas(self.w, self.h)
        for y in range(self.h):
            for x in range(self.w):
                ch = self.g[y][x]
                if ch != '.':
                    cv.px[y][x] = cmap[ch]
        return cv

    def text(self):
        return '\n'.join(''.join(r) for r in self.g)
