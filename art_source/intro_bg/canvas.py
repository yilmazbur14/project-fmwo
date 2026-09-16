"""Palette-keyed pixel canvas for authoring the intro background (DB32 only)."""
import math
from pngio import write_png, scale

# DawnBringer 32, one key per colour.
DB32 = {
    'K': '#000000',  # black
    'N': '#222034',  # navy (darkest)
    'M': '#45283c',  # maroon
    'B': '#663931',  # dark brown
    'w': '#8f563b',  # wood brown
    'O': '#df7126',  # orange
    'd': '#d9a066',  # tan / skin shadow
    's': '#eec39a',  # skin light
    'Y': '#fbf236',  # yellow
    '1': '#99e550',
    '2': '#6abe30',
    '3': '#37946e',
    '4': '#4b692f',
    '5': '#524b24',
    '6': '#323c39',
    'I': '#3f3f74',  # indigo
    '7': '#306082',
    'U': '#5b6ee1',  # blue
    'u': '#639bff',  # light blue
    'c': '#5fcde4',
    'P': '#cbdbfc',  # pale blue-white
    'W': '#ffffff',  # white
    'g': '#9badb7',  # light grey
    'F': '#847e87',  # floor grey
    'D': '#696a6a',  # dark grey
    'E': '#595652',  # darker grey
    'V': '#76428a',  # violet
    'R': '#ac3232',  # red
    'r': '#d95763',  # pink red
    '8': '#d77bba',
    '9': '#8f974a',
    'A': '#8a6f30',  # dark gold
}


def hex2rgb(h):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


RGB = {k: hex2rgb(v) for k, v in DB32.items()}
RGB2KEY = {v: k for k, v in RGB.items()}


class Canvas:
    def __init__(self, w, h, fill='F'):
        self.w = w
        self.h = h
        self.px = [[fill] * w for _ in range(h)]

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, k):
        if k is None or k == '.':
            return
        if self.inb(x, y):
            self.px[y][x] = k

    def get(self, x, y):
        if self.inb(x, y):
            return self.px[y][x]
        return None

    def to_rgba(self):
        return [[RGB[k] + (255,) for k in row] for row in self.px]

    def save(self, path, k=1):
        rows = self.to_rgba()
        if k > 1:
            rows = scale(rows, k)
        write_png(path, rows)

    def stamp(self, lines, x0, y0, remap=None):
        """Blit an ASCII grid; '.' and ' ' are transparent."""
        for j, line in enumerate(lines):
            for i, ch in enumerate(line):
                if ch in '. ':
                    continue
                if remap and ch in remap:
                    ch = remap[ch]
                self.set(x0 + i, y0 + j, ch)

    def paint_mask(self, mask, k):
        for (x, y) in mask:
            self.set(x, y, k)


# ---------------------------------------------------------------- geometry

def poly_mask(pts, w=640, h=360):
    """Pixels whose centres fall inside the polygon (even-odd rule)."""
    out = set()
    n = len(pts)
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))) - 1)
    y1 = min(h - 1, int(math.ceil(max(ys))) + 1)
    for y in range(y0, y1 + 1):
        cy = y + 0.5
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= cy < by) or (by <= cy < ay):
                xs.append(ax + (cy - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            xa = int(math.ceil(a - 0.5))
            xb = int(math.floor(b - 0.5))
            for x in range(max(0, xa), min(w - 1, xb) + 1):
                out.add((x, y))
    return out


def func_mask(fn, x0, y0, x1, y1):
    out = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if fn(x + 0.5, y + 0.5):
                out.add((x, y))
    return out


def boundary(mask, out_of_canvas_is_outside=False, w=640, h=360):
    """Inner 4-neighbour boundary -> a clean 8-connected 1px contour."""
    b = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if (nx, ny) not in mask:
                if not out_of_canvas_is_outside and not (0 <= nx < w and 0 <= ny < h):
                    continue
                b.add((x, y))
                break
    return b


def line_pts(x0, y0, x1, y1):
    """Bresenham, inclusive."""
    pts = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
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


def polyline_pts(pts, closed=False):
    out = []
    seq = list(pts) + ([pts[0]] if closed else [])
    for (a, b) in zip(seq, seq[1:]):
        out.extend(line_pts(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1]))))
    return out


def pixel_perfect(path):
    """Aseprite-style: drop the middle pixel of L-shaped triples."""
    if len(path) < 3:
        return path
    out = [path[0]]
    i = 1
    while i < len(path) - 1:
        a = out[-1]
        b = path[i]
        c = path[i + 1]
        if (a[0] == b[0] or a[1] == b[1]) and (c[0] == b[0] or c[1] == b[1]) and a[0] != c[0] and a[1] != c[1]:
            i += 1
            continue
        out.append(b)
        i += 1
    out.append(path[-1])
    return out


def dedupe(pts):
    seen = set()
    out = []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    return (BAYER4[y % 4][x % 4] + 0.5) / 16.0
