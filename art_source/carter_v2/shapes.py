"""Part-based silhouette builder: polygons + row spans, z-ordered, auto 1px black outline."""
from lib import *


def bres(x0, y0, x1, y1):
    pts = []
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy
    return pts


def poly_pixels(pts):
    """Filled polygon incl. its Bresenham boundary. pts are pixel coords."""
    out = set()
    n = len(pts)
    for i in range(n):
        out.update(bres(*pts[i], *pts[(i + 1) % n]))
    ys = [p[1] for p in pts]
    for y in range(min(ys), max(ys) + 1):
        yc = y + 0.0
        xs = []
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
            if y0 == y1:
                continue
            if (yc >= min(y0, y1)) and (yc < max(y0, y1)):
                t = (yc - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            a, b = xs[j], xs[j + 1]
            for x in range(int(round(a)), int(round(b)) + 1):
                out.add((x, y))
    return out


def span_pixels(spans):
    out = set()
    for y, segs in spans.items():
        if isinstance(segs, tuple):
            segs = [segs]
        for a, b in segs:
            for x in range(a, b + 1):
                out.add((x, y))
    return out


def rng(a, b, seg):
    return {y: seg for y in range(a, b + 1)}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out.setdefault(k, [])
            out[k] += v if isinstance(v, list) else [v]
    return out


def mirror_pts(pts):
    return [(63 - x, y) for x, y in pts]


def mirror_set(s):
    return {(63 - x, y) for x, y in s}


class Canvas:
    def __init__(self, w=64, h=64):
        self.w, self.h = w, h
        self.parts = []  # (name, z, fill, pixelset, outline_against)

    def add(self, name, z, fill, pix, outline=True):
        self.parts.append((name, z, fill, set(pix), outline))

    def render(self, ground=63):
        w, h = self.w, self.h
        label = [[None] * w for _ in range(h)]
        zmap = [[-1] * w for _ in range(h)]
        g = blank(w, h)
        outl = {}
        for name, z, fill, pix, ol in sorted(self.parts, key=lambda p: p[1]):
            outl[name] = ol
            for (x, y) in pix:
                if 0 <= x < w and 0 <= y < h and z >= zmap[y][x]:
                    label[y][x] = name; zmap[y][x] = z; g[y][x] = fill
        out = [row[:] for row in g]
        for y in range(h):
            for x in range(w):
                L = label[y][x]
                if L is None or not outl[L]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h):
                        if ny >= h:
                            out[y][x] = '#'
                        continue
                    M = label[ny][nx]
                    if M is None or (M != L and zmap[ny][nx] < zmap[y][x]):
                        out[y][x] = '#'
                        break
        self.label = label
        return out
