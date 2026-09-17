"""Sword sprites cut from Eric's own sheet, plus pixel-exact transforms (flips / transpose)."""
from lib import *
R = [to_chars(f) for f in ref_frames()]


class Spr:
    def __init__(self, rows, ax, ay):
        self.rows = [list(r) for r in rows]  # '.' transparent
        self.ax, self.ay = ax, ay            # anchor inside sprite (e.g. hilt grip centre)

    @property
    def w(self): return len(self.rows[0])
    @property
    def h(self): return len(self.rows)

    def fliph(self):
        return Spr([r[::-1] for r in self.rows], self.w - 1 - self.ax, self.ay)

    def flipv(self):
        return Spr(self.rows[::-1], self.ax, self.h - 1 - self.ay)

    def transpose(self):
        return Spr([[self.rows[y][x] for y in range(self.h)] for x in range(self.w)], self.ay, self.ax)

    def put(self, g, x, y, only=None):
        """Place so that anchor lands on (x, y)."""
        for j, r in enumerate(self.rows):
            for i, c in enumerate(r):
                if c == '.':
                    continue
                X, Y = x - self.ax + i, y - self.ay + j
                if 0 <= X < FS and 0 <= Y < FS and (only is None or only(X, Y)):
                    g[Y][X] = c


def cut(fi, x0, y0, x1, y1, keep=lambda x, y: True):
    rows = []
    for y in range(y0, y1):
        rows.append([R[fi][y][x] if (R[fi][y][x] not in '~?' and keep(x, y)) else '.' for x in range(x0, x1)])
    return rows


def close_outline(rows):
    """Add the 1px black outline where the source art left a gap (transparent cell touching a coloured cell)."""
    h, w = len(rows) + 2, len(rows[0]) + 2
    g = [['.'] * w] + [['.'] + list(r) + ['.'] for r in rows] + [['.'] * w]
    out = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] != '.':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if 0 <= X < w and 0 <= Y < h and g[Y][X] not in '.k':
                    out[y][x] = 'k'
                    break
    return out


# planted sword, frames 27-31 (identical in all five). anchor = centre of grip, row 79
def _plant_keep(x, y):
    return x <= 53 if 82 <= y <= 84 else x <= 52
SW_PLANT = Spr(cut(27, 40, 73, 54, 127, _plant_keep), 47 - 40, 79 - 73)
# frames 27-31 have Eric's arm touching the blade's right edge on rows 93-95; restore the clean edge there
for _r, _s in ((20, '..kMkdddDDkMk.'), (21, '..kMkddddDkMk.'), (22, '..kMkDddddkMk.')):
    SW_PLANT.rows[_r] = list(_s)

# up-right ~60 deg sword from whirlwind frame 19 (blade + guard + start of grip); anchor = guard bottom
SW_UR60 = Spr(close_outline(cut(19, 61, 33, 93, 72, lambda x, y: not (y == 71 and x < 63))), 68 - 61 + 1, 70 - 33 + 1)

if __name__ == '__main__':
    import sys
    g = blank(); SW_PLANT.put(g, 20, 20)
    for name, s in [('plant', SW_PLANT), ('ur60', SW_UR60)]:
        print(name, s.w, s.h, 'anchor', s.ax, s.ay)
        for r in s.rows:
            print(''.join(r))
