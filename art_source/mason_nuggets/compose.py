"""Compositing helpers for previews: nearest-neighbour integer scaling like Godot's
Sprite2D (texture filter nearest, centered=true), a 3x5 label font, GIF writer glue."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png
from gifio import write_gif

OUT = os.path.join(HERE, 'out')
MAT = (136, 180, 99)


class Sheet:
    def __init__(self, path, fw, fh):
        self.w, self.h, self.px = read_png(path)
        self.fw, self.fh = fw, fh
        self.n = self.w // fw

    def frame(self, i, row=0):
        x0, y0 = i * self.fw, row * self.fh
        return [r[x0:x0 + self.fw] for r in self.px[y0:y0 + self.fh]]


class Canvas:
    def __init__(self, w, h, bg=MAT):
        self.w, self.h = w, h
        self.px = [[bg] * w for _ in range(h)]

    @classmethod
    def from_png(cls, path):
        w, h, px = read_png(path)
        c = cls(w, h)
        c.px = [[tuple(p[:3]) for p in row] for row in px]
        return c

    def blit(self, tex, left, top, s):
        """tex top-left at (left, top) in canvas px, scaled s"""
        th, tw = len(tex), len(tex[0])
        for ty in range(th):
            for tx in range(tw):
                p = tex[ty][tx]
                if p[3] == 0:
                    continue
                k = p[3] / 255.0          # (only the OLD elbow sprites have partial alpha)
                for yy in range(s):
                    Y = top + ty * s + yy
                    if not (0 <= Y < self.h):
                        continue
                    row = self.px[Y]
                    for xx in range(s):
                        X = left + tx * s + xx
                        if 0 <= X < self.w:
                            if p[3] == 255:
                                row[X] = p[:3]
                            else:
                                q = row[X]
                                row[X] = tuple(int(round(p[i] * k + q[i] * (1 - k))) for i in range(3))

    def place(self, tex, cx, cy, s, anchor=None):
        """Godot centered sprite: node at (cx, cy); anchor (texel coords) overrides the centre"""
        th, tw = len(tex), len(tex[0])
        ax, ay = anchor if anchor else (tw / 2.0, th / 2.0)
        self.blit(tex, int(round(cx - ax * s)), int(round(cy - ay * s)), s)

    def rect(self, x0, y0, x1, y1, col):
        for y in range(max(0, y0), min(self.h, y1)):
            for x in range(max(0, x0), min(self.w, x1)):
                self.px[y][x] = col

    def dot(self, x, y, col, r=1):
        for yy in range(y - r + 1, y + r):
            for xx in range(x - r + 1, x + r):
                if 0 <= xx < self.w and 0 <= yy < self.h:
                    self.px[yy][xx] = col

    def save(self, path):
        write_png(path, self.w, self.h, [[p + (255,) for p in row] for row in self.px])


FONT = {
    'A': ["010", "101", "111", "101", "101"], 'B': ["110", "101", "110", "101", "110"],
    'C': ["011", "100", "100", "100", "011"], 'D': ["110", "101", "101", "101", "110"],
    'E': ["111", "100", "110", "100", "111"], 'F': ["111", "100", "110", "100", "100"],
    'G': ["011", "100", "101", "101", "011"], 'H': ["101", "101", "111", "101", "101"],
    'I': ["111", "010", "010", "010", "111"], 'J': ["001", "001", "001", "101", "010"],
    'K': ["101", "101", "110", "101", "101"], 'L': ["100", "100", "100", "100", "111"],
    'M': ["101", "111", "111", "101", "101"], 'N': ["110", "101", "101", "101", "101"],
    'O': ["010", "101", "101", "101", "010"], 'P': ["110", "101", "110", "100", "100"],
    'Q': ["010", "101", "101", "110", "011"], 'R': ["110", "101", "110", "101", "101"],
    'S': ["011", "100", "010", "001", "110"], 'T': ["111", "010", "010", "010", "010"],
    'U': ["101", "101", "101", "101", "111"], 'V': ["101", "101", "101", "101", "010"],
    'W': ["101", "101", "111", "111", "101"], 'X': ["101", "101", "010", "101", "101"],
    'Y': ["101", "101", "010", "010", "010"], 'Z': ["111", "001", "010", "100", "111"],
    '0': ["111", "101", "101", "101", "111"], '1': ["010", "110", "010", "010", "111"],
    '2': ["111", "001", "111", "100", "111"], '3': ["111", "001", "111", "001", "111"],
    '4': ["101", "101", "111", "001", "001"], '5': ["111", "100", "111", "001", "111"],
    '6': ["111", "100", "111", "101", "111"], '7': ["111", "001", "001", "001", "001"],
    '8': ["111", "101", "111", "101", "111"], '9': ["111", "101", "111", "001", "111"],
    ' ': ["000"] * 5, '.': ["000", "000", "000", "000", "010"], '-': ["000", "000", "111", "000", "000"],
    '(': ["010", "100", "100", "100", "010"], ')': ["010", "001", "001", "001", "010"],
    '/': ["001", "001", "010", "100", "100"], ':': ["000", "010", "000", "010", "000"],
    '+': ["000", "010", "111", "010", "000"], '=': ["000", "111", "000", "111", "000"],
    '_': ["000", "000", "000", "000", "111"],
}


def text(c, x, y, s, msg, col=(255, 255, 255), shadow=(0, 0, 0)):
    msg = msg.upper()
    for pass_, colour, off in ((0, shadow, 1), (1, col, 0)):
        if colour is None:
            continue
        cx = x
        for ch in msg:
            g = FONT.get(ch, FONT[' '])
            for r in range(5):
                for q in range(3):
                    if g[r][q] == '1':
                        c.rect(cx + q * s + off * s // 2 + off, y + r * s + off * s // 2 + off,
                               cx + (q + 1) * s + off * s // 2 + off, y + (r + 1) * s + off * s // 2 + off, colour)
            cx += 4 * s
    return 4 * s * len(msg)


def capsule_outline(c, cx, cy, radius, height, col, dash=0):
    """horizontal CapsuleShape2D (rotated 90 deg): total length = height"""
    half = height / 2.0 - radius
    n = int(2 * math.pi * radius + 4 * half) * 2
    pts = []
    for k in range(n):
        t = k / n
        per = 2 * math.pi * radius + 4 * half
        d = t * per
        if d < 2 * half:
            x, y = cx - half + d, cy - radius
        elif d < 2 * half + math.pi * radius:
            a = -math.pi / 2 + (d - 2 * half) / radius
            x, y = cx + half + math.cos(a) * radius, cy + math.sin(a) * radius
        elif d < 4 * half + math.pi * radius:
            x, y = cx + half - (d - 2 * half - math.pi * radius), cy + radius
        else:
            a = math.pi / 2 + (d - 4 * half - math.pi * radius) / radius
            x, y = cx - half + math.cos(a) * radius, cy + math.sin(a) * radius
        pts.append((int(round(x)), int(round(y)), d))
    for (x, y, d) in pts:
        if dash and int(d // dash) % 2 == 1:
            continue
        c.dot(x, y, col, 2)


def gif(path, canvases, delays):
    frames = [cv.px for cv in canvases]
    size = write_gif(path, frames, delays)
    print('wrote', path, size, 'bytes,', len(frames), 'frames')
