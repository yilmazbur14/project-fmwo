"""Procedural first draft of the poo bomb. Emits an ASCII grid per frame that is then
frozen and hand-refined in bomb_grid.py."""
import math
import sys
import fxpng

W = H = 32

# char -> colour
PAL = {
    '.': None,
    'K': '#000000',
    # poo ramp (DB32 browns + two in-betweens), light from upper left
    'a': '#45283C',  # deepest shadow / crease tone
    'b': '#663931',  # shadow
    'c': '#8F563B',  # base
    'd': '#B0703F',  # light
    'e': '#D9A066',  # highlight
    'f': '#F2D1A4',  # wet glint
    # fuse cord
    'g': '#E6E0D0',
    'h': '#A8A08C',
    'i': '#5A4A42',  # charred end
    # spark
    'W': '#FFFFFF',
    'Y': '#FBF236',
    'O': '#DF7126',
    'R': '#AC3232',
}

LX, LY, LZ = -0.55, -0.65, 0.52
n = math.sqrt(LX * LX + LY * LY + LZ * LZ)
LX, LY, LZ = LX / n, LY / n, LZ / n


def superell(x, y, cx, cy, a, b, p=2.3):
    return abs((x + 0.5 - cx) / a) ** p + abs((y + 0.5 - cy) / b) ** p


def lum(x, y, cx, cy, a, b):
    nx = (x + 0.5 - cx) / a
    ny = (y + 0.5 - cy) / b
    d2 = nx * nx + ny * ny
    if d2 > 1:
        s = math.sqrt(d2)
        nx, ny, nz = nx / s, ny / s, 0.0
    else:
        nz = math.sqrt(1 - d2)
    return nx * LX + ny * LY + nz * LZ


def quant(vals, fracs):
    s = sorted(vals)
    out, acc = [], 0.0
    for f in fracs:
        acc += f
        out.append(s[min(len(s) - 1, int(len(s) * (1 - acc)))])
    return out


def make(swell):
    s = swell
    ground = 28.5  # bottom edge of the pile (fixed; the pile grows upward)
    t1b, t2b, t3b = 5.0 + 0.3 * s, 4.1 + 0.3 * s, 3.4 + 0.25 * s
    t1 = (15.5, ground - t1b, 12.3 + 0.8 * s, t1b)
    t2 = (16.1, t1[1] - t1b * 0.95, 9.2 + 0.7 * s, t2b)
    t3 = (15.3, t2[1] - t2b * 0.95, 6.2 + 0.6 * s, t3b)
    tiers = [t1, t2, t3]
    owner = {}
    for y in range(H):
        for x in range(W):
            for k, (cx, cy, a, b) in enumerate(tiers):
                if superell(x, y, cx, cy, a, b) <= 1.0:
                    owner[(x, y)] = k  # later (upper) tier wins -> it sits in front
    # tip: tapered horn leaning right out of the top tier
    tip_base_y = t3[1] - t3b * 0.55
    tip_top = (18.6, t3[1] - t3b - 4.2)
    for i in range(0, 41):
        t = i / 40.0
        # quadratic bezier from base centre to tip, bending right
        p0 = (15.0, tip_base_y)
        p1 = (15.2, tip_top[1] + 1.0)
        p2 = tip_top
        px_ = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        py_ = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        rad = 3.3 * (1 - t) + 0.55 * t
        for y in range(H):
            for x in range(W):
                if (x + 0.5 - px_) ** 2 + ((y + 0.5 - py_) * 1.15) ** 2 <= rad * rad:
                    if (x, y) not in owner:
                        owner[(x, y)] = 3
    grid = [['.'] * W for _ in range(H)]
    # shade each tier with its own quantile bands so every tier gets the full ramp
    groups = {}
    for (x, y), k in owner.items():
        if k < 3:
            cx, cy, a, b = tiers[k]
            v = lum(x, y, cx, cy, a, b)
        else:
            v = lum(x, y, 16.0, tip_base_y - 1.0, 3.5, 4.5)
        groups.setdefault(k, []).append(((x, y), v))
    for k, items in groups.items():
        th = quant([v for _, v in items], (0.14, 0.36, 0.30))
        for (x, y), v in items:
            grid[y][x] = 'e' if v > th[0] else 'd' if v > th[1] else 'c' if v > th[2] else 'b'
    # creases: bottom edge of an upper tier drawn over the tier below
    for (x, y), k in owner.items():
        below = owner.get((x, y + 1))
        if below is not None and below < k and k < 3:
            grid[y][x] = 'K'
            if grid[y + 1][x] not in 'K':
                grid[y + 1][x] = 'a'
    # silhouette outline
    for (x, y) in owner:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in owner:
                grid[y][x] = 'K'
                break
    return grid, tip_top


def to_px(grids):
    fw = W
    out = [[(0, 0, 0, 0)] * (fw * len(grids)) for _ in range(H)]
    for f, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                c = PAL[g[y][x]]
                if c:
                    out[y][f * fw + x] = fxpng.hexc(c)
    return out


if __name__ == '__main__':
    grids = []
    for s in (0.0, 1.0):
        g, tip = make(s)
        grids.append(g)
        print('frame swell', s, 'tip', tip)
        for row in g:
            print(''.join(row))
    px = to_px(grids)
    fxpng.write_png('draft_bomb.png', 64, 32, px)
    W8, H8, o = fxpng.view(64, 32, px, 8, grid=(32, 32))
    fxpng.write_png('draft_bomb_8x.png', W8, H8, o)
