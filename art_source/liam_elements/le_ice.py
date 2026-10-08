"""Attack 2's floor: the flood (liam_flood.png), the ice sheet (liam_ice.png), its melt and shatter, and
the frost rim stamped along the freeze front (liam_freeze_front.png). No keyline.

The flood and ice are 64 x 64 tiles, seamless on all four edges, and semi-transparent: the mat and its
markings stay visible under them. Coverage frames nest (every wet texel of frame k is wet in k + 1).
"""
import math

import numpy as np

import le_rig as R
from le_water import pnoise

T = 64

# semi-transparent floor colours (key: rgba). Water sits at ~45-60 % so the mat shows through; ice at
# ~70-80 %, clearly paler and more solid, still letting the ring's lines read through.
FLOOR = {
    '<': (43, 108, 192, 118),     # water body
    '>': (29, 74, 142, 140),      # water, deeper hollow
    '^': (203, 219, 252, 165),    # water shine
    '"': (159, 220, 247, 150),    # puddle rim
    '(': (214, 241, 251, 152),    # ice body (paler and more solid than water, lines still read)
    ')': (150, 204, 234, 188),    # ice crack / seam
    '[': (236, 250, 255, 170),    # ice frost patch
    ']': (255, 255, 255, 228),    # ice glint / gloss streak
    '{': (190, 228, 245, 160),    # ice, slightly deeper
    '}': (184, 228, 246, 150),    # slush
}
R.PAL.update(FLOOR)


def pnoise2(cell, seed):
    """Seamless in x and y (64 x 64)."""
    rnd = np.random.RandomState(seed)
    g = rnd.rand(T // cell + 1, T // cell + 1)
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]
    ys, xs = np.mgrid[0:T, 0:T]
    fx, fy = xs / cell, ys / cell
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


FIELD = 0.62 * pnoise2(16, 5) + 0.38 * pnoise2(8, 6)       # puddle field: high = wets first
DETAIL = pnoise2(4, 7)
THRESH = (0.66, 0.57, 0.48, 0.38, 0.25, -1.0)             # 6 nested coverage levels; the last = full sheet


def flood(k):
    """Coverage frame k (0 sparse puddles .. 5 a full sheet)."""
    cv = R.blank(T, T)
    wet = FIELD > THRESH[k]
    # rim: wet texels next to a dry one (wrapping, so the tile stays seamless)
    dry = ~wet
    nb = np.zeros_like(wet)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb |= np.roll(np.roll(dry, dx, axis=1), dy, axis=0)
    rim = wet & nb
    deep = wet & (FIELD > THRESH[k] + 0.12) & (DETAIL < 0.3) & (FIELD > 0.55)
    rows_ = (np.arange(T)[:, None] % 4) == 1
    shine = wet & ~rim & (DETAIL > 0.74) & rows_ & ((np.arange(T)[None, :] % 7) < 3)
    cv[wet] = '<'
    cv[deep] = '>'
    cv[shine] = '^'
    cv[rim] = '"'
    return cv


def ice(glint=False):
    """The frozen sheet: pale, near-opaque, crazed with seams, frost patches; optional glint frame."""
    cv = R.blank(T, T)
    cv[:, :] = '('
    fr = pnoise2(32, 21)
    cv[fr > 0.74] = '['
    cv[(fr < 0.2)] = '{'
    # gloss: long diagonal streaks (wrapping) that sell 'slippery'
    for (x0, y0, ln) in ((4, 30, 14), (36, 6, 10), (30, 60, 12), (52, 40, 8)):
        for i in range(ln):
            x, y = (x0 + i) % T, (y0 - i) % T
            cv[y, x] = ']' if i % 5 != 4 else '['
            if i % 3 == 0:
                cv[(y + 1) % T, x] = '['
    # seams: a few wrapping crack lines
    for (x0, y0, x1, y1) in ((0, 12, 64, 20), (0, 44, 64, 38), (50, 0, 44, 64)):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(n):
            x = int(round(x0 + (x1 - x0) * i / n)) % T
            y = int(round(y0 + (y1 - y0) * i / n)) % T
            if (i // 5) % 4 != 3:
                cv[y, x] = ')'
    if glint:
        for (x, y) in ((10, 8), (40, 26), (26, 50), (56, 54)):
            for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0)):
                cv[(y + dy) % T, (x + dx) % T] = ']'
    else:
        for (x, y) in ((10, 8), (40, 26), (26, 50), (56, 54)):
            cv[y, x] = ']'
    return cv


def ice_melt(k):
    """3 frames: 0 the ice turning to slush, 1 slush and pools, 2 = flood frame 5 (open water)."""
    if k == 2:
        return flood(5)
    base = ice()
    n = pnoise2(8, 31 + k)
    cv = base.copy()
    if k == 0:
        cv[n < 0.4] = '}'
        cv[(n < 0.25)] = '<'
    else:
        cv[:, :] = '<'
        cv[n > 0.55] = '}'
        cv[n > 0.75] = '('
        cv[(DETAIL > 0.8)] = '^'
    return cv


def ice_shatter(k):
    """4 frames: 0 cracks race across; 1 the sheet breaks into plates; 2 plates shrink and scatter;
    3 the last glinting shards. Holes show the dry mat (the water drains separately)."""
    base = ice()
    cv = base.copy()
    ys, xs = np.mgrid[0:T, 0:T]
    cells = (np.floor((xs + 3 * np.sin(ys / 7.0)) / 13).astype(int) * 7 + np.floor((ys + 3 * np.sin(xs / 9.0)) / 11).astype(int))
    edge = (cells != np.roll(cells, 1, axis=1)) | (cells != np.roll(cells, 1, axis=0))
    if k == 0:
        cv[edge] = ')'
        return cv
    rnd = np.random.RandomState(51)
    keep = {c: rnd.rand() for c in np.unique(cells)}
    kv = np.vectorize(keep.get)(cells)
    shrink = (0, 1, 2, 3)[k]
    grow = edge.copy()
    for _ in range(shrink - 1):
        g2 = grow.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g2 |= np.roll(np.roll(grow, dx, axis=1), dy, axis=0)
        grow = g2
    alive = kv > (0.0, 0.0, 0.35, 0.75)[k]
    cv[grow | ~alive] = '.'
    if k == 3:
        glints = (cv != '.') & (DETAIL > 0.6)
        cv[glints] = ']'
    return cv


def freeze_front(k):
    """16 x 16, pivot (8, 8): a frost rim piece - spiky crystals with a white core; 3-frame shimmer."""
    cv = R.blank(16, 16)
    X, Y = R.centres(16, 16)
    core = ((X - 8) / 4.2) ** 2 + ((Y - 8) / 3.4) ** 2 <= 1
    cv[core] = '['
    for i, a in enumerate(range(0, 360, 45)):
        ln = (6, 4, 7, 4, 6, 4, 7, 4)[(i + k) % 8]
        for r in range(2, ln + 1):
            x = int(round(8 + math.cos(math.radians(a + k * 8)) * r))
            y = int(round(8 + math.sin(math.radians(a + k * 8)) * r * 0.8))
            if 0 <= x < 16 and 0 <= y < 16:
                cv[y, x] = ']' if r < ln - 1 else ')'
    cv[8, 8] = ']'
    return cv
