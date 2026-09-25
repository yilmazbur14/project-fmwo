"""Shared fire-drawing pieces for the Inferno effects: periodic noise, flame bodies, sparks.

Everything is deterministic (seeded), so a rebuild gives the same pixels.

A flame is a silhouette (a root blob plus tapering tongues) coloured by eroding it: the outer ring is
the cool edge, each ring in is hotter, and the deepest part of the root is white-hot. Thin tips therefore
come out cool and wide roots hot, which is how bixby_fire_trail.png and the redesign's throat fire read.
"""
import math
import random


def periodic_noise(w, h, terms, seed):
    """A smooth w x h field in 0..1, periodic both ways, from random integer-frequency waves (kx, ky, amp)."""
    rnd = random.Random(seed)
    waves = [(kx, ky, amp, rnd.uniform(0, 2 * math.pi)) for kx, ky, amp in terms]
    field = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            s = 0.0
            for kx, ky, amp, ph in waves:
                s += amp * math.sin(2 * math.pi * (kx * x / w + ky * y / h) + ph)
            field[y][x] = s
    lo = min(min(r) for r in field)
    hi = max(max(r) for r in field)
    return [[(v - lo) / (hi - lo) for v in r] for r in field]


def quantise(v, steps):
    """steps: (threshold, key) ascending; the key of the highest threshold <= v."""
    key = steps[0][1]
    for th, k in steps:
        if v >= th:
            key = k
    return key


def put(grid, x, y, k):
    if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
        grid[y][x] = k


def ellipse_set(cx, cy, rx, ry):
    out = set()
    for y in range(int(math.floor(cy - ry)) - 1, int(math.ceil(cy + ry)) + 2):
        for x in range(int(math.floor(cx - rx)) - 1, int(math.ceil(cx + rx)) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def tongue_set(x0, y0, height, width, lean=0.0, sway=0.0, bulge=0.14, phase=0.0):
    """A tapering tongue rising from (x0, y0) (its root centre, bottom row) for `height` rows. Its sides
    bulge and pinch (bulge, phase) so it reads as licking flame rather than a spike."""
    out = set()
    for i in range(height + 1):
        s = i / max(1, height)
        half = width / 2.0 * (1.0 - s) ** 0.6 * (1.0 + bulge * math.sin(2 * math.pi * (1.4 * s + phase)))
        c = x0 + lean * s * s + sway * math.sin(math.pi * s)
        if half < 0.5:
            out.add((int(math.floor(c)), y0 - i))
            continue
        for x in range(int(math.floor(c - half + 0.5)), int(math.floor(c + half - 0.5)) + 1):
            out.add((x, y0 - i))
    return out


def flame_set(cx, base_y, width, height, tongues, phase=0.0):
    """A flame: a root blob `width` wide at base_y plus tongues [(dx, root_dy, height, width, lean, sway)]
    measured from the blob's centre. A tongue with a negative root_dy branches off higher up."""
    blob_h = max(3.0, width * 0.55)
    s = ellipse_set(cx, base_y - blob_h / 2.0 + 0.5, width / 2.0, blob_h / 2.0)
    for j, (dx, dy, th, tw, lean, sway) in enumerate(tongues):
        s |= tongue_set(cx + dx, base_y - int(blob_h * 0.5) + dy, th, tw, lean, sway, phase=phase + 0.37 * j)
    return close_holes(close_holes(s))


def wisp(shape, x, y, size):
    """A detached flame bit: 1x1, 1x2 or 2x2 (+ a tip) at (x, y) (its bottom)."""
    out = {(x, y)}
    if size >= 2:
        out.add((x, y - 1))
    if size >= 3:
        out |= {(x + 1, y), (x + 1, y - 1), (x, y - 2)}
    return out


def close_holes(shape):
    """Fill 1-texel pinholes and notches: a texel with 3 or 4 of its 4 neighbours in the shape joins it."""
    out = set(shape)
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in out:
                continue
            n = sum(q in shape for q in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
            if n >= 3:
                out.add((x, y))
    return out


def rings(shape):
    """Erosion depth of every texel of a shape: 0 on its edge, 1 next in, and so on (4-neighbour)."""
    depth = {}
    cur = set(shape)
    d = 0
    while cur:
        edge = {p for p in cur if any(n not in cur for n in ((p[0] - 1, p[1]), (p[0] + 1, p[1]), (p[0], p[1] - 1), (p[0], p[1] + 1)))}
        for p in edge:
            depth[p] = d
        cur -= edge
        d += 1
    return depth


def paint_flame(grid, shape, base_y, height, bands=('N', 'p', 'P', 'Y'), white='W', white_depth=4,
                cool_top='N', cool_from=0.78, clip=None):
    """Colour a flame shape by erosion rings. Rings past the band list use the last band; texels at
    white_depth or deeper in the lower half are white-hot. The top of the flame (above cool_from of its
    height) never goes hotter than bands[1]."""
    depth = rings(shape)
    for (x, y), d in depth.items():
        if clip and not clip(x, y):
            continue
        s = (base_y - y) / max(1, height)
        k = bands[min(d, len(bands) - 1)]
        if white and d >= white_depth and s < 0.45:
            k = white
        if s > cool_from and d >= 1:
            k = bands[min(d, 1)]
        put(grid, x, y, k)
    return depth


def halo(grid, shape, key, over=('q', 'r'), clip=None):
    """A one-texel glow just outside a shape, only where it lies on darker background keys."""
    for (x, y) in shape:
        for n in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if n in shape:
                continue
            if clip and not clip(*n):
                continue
            if 0 <= n[1] < len(grid) and 0 <= n[0] < len(grid[0]) and grid[n[1]][n[0]] in over:
                grid[n[1]][n[0]] = key


def bounds(shape):
    xs = [p[0] for p in shape]
    ys = [p[1] for p in shape]
    return min(xs), max(xs), min(ys), max(ys)


# Small flames drawn by hand, like bixby_fire_trail.png's little tongues: at these sizes an eroded flame
# is all rim. Bottom row is the root. Hot variants swap one step up the ramp.
FLAME_S = ["..N..",
           ".NpN.",
           ".pPp.",
           "..p.."]
FLAME_M = ["..r..",
           ".rNr.",
           ".NpN.",
           "rpPpr",
           "rPYPr",
           ".rpr."]
FLAME_L = ["...r...",
           "..rNr..",
           "..NpN..",
           ".rpPpr.",
           ".NPYPN.",
           "rpPYPpr",
           "rpYWYpr",
           ".rPYPr.",
           "..rrr.."]
COOLER = {'W': 'Y', 'Y': 'P', 'P': 'p', 'p': 'N', 'N': 'n', 'n': 'r', 'r': 'r'}


def stamp(grid, template, x, y, cool=0, mirror=False):
    """Stamp a flame template with its root's centre at (x, y). cool: steps cooler down the ramp."""
    h = len(template)
    w = len(template[0])
    for j, row in enumerate(template):
        for i, k in enumerate(row[::-1] if mirror else row):
            if k == '.':
                continue
            for _ in range(cool):
                k = COOLER[k]
            put(grid, x - w // 2 + i, y - (h - 1) + j, k)
