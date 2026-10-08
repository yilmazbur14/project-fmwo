"""The earth pillar (new, invented for this phase): liam_pillar.png, liam_pillar_shield.png,
liam_pillar_dust.png.

A slab-topped slate column raised by earthbending: layered rock with lit ledges and long fissures, a mossy
lip, a domed top slab, boulders round its foot, and a stack of six rune notches down its face that glow
earth-green. Each accepted hit darkens one rune (top first) and spreads the cracks up from the base, so
the pillar is its own 6-hit meter. While it is invincible a spiral of wind (his air bending) wraps it.

Cell: 64 x 80 texels. ANCHOR (32, 72) is the floor line's centre = screen (960, 348) at 3x.
Column face x 14..49 (36 texels = the solid footprint x -18..+18); top slab rows 14..30 (16 deep = the
footprint's y -16..0); STAND (32, 22) - his soles - is exactly 50 texels above the floor line. Everything
drawn stays inside x 8..55 (48 texels, the contract's cap).
Colours: his own slate greys (t T y Y), E for crevices, the keyline, the earth greens 8 and Y-shadowed
moss, and W/w/v/l for dust and wind.
"""
import math
import random

import numpy as np

import le_rig as R

PW, PH = 64, 80
ANCHOR = (32, 72)
STAND = (32, 22)
COL_X0, COL_X1 = 14, 49
TOP_Y0, TOP_Y1 = 14, 30
BASE_Y = 72
DRAW_X0, DRAW_X1 = 8, 55
RUNE_ROWS = (35, 41, 47, 53, 59, 65)
RUNE_X = 30                      # block's left column (5 wide): centred on x 32


def blank():
    return R.blank(PW, PH)


def value_noise(seed, cell=3, w=PW, h=PH):
    rnd = np.random.RandomState(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = rnd.rand(gh, gw)
    ys, xs = np.mgrid[0:h, 0:w]
    fx, fy = xs / cell, ys / cell
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


# the rock's edge wobble: a few big bumps, not a zipper
EDGE_L = {18: 1, 19: 1, 26: -1, 27: -1, 38: 1, 39: 1, 40: 1, 51: -1, 52: -1, 60: 1, 61: 1, 68: -1}
EDGE_R = {21: -1, 22: -1, 33: 1, 34: 1, 44: -1, 45: -1, 46: -1, 55: 1, 56: 1, 64: -1, 65: -1}


def silhouette(top=TOP_Y0, height=None):
    """Top slab + front face mask. top = the slab's first row (the rise frames move it)."""
    m = np.zeros((PH, PW), dtype=bool)
    t0 = top
    t1 = top + (TOP_Y1 - TOP_Y0)
    bottom = BASE_Y
    for y in range(max(0, t0), bottom + 1):
        rel = y - t0 + TOP_Y0          # the row in stand-frame terms, for the edge bumps
        x0 = COL_X0 - EDGE_L.get(rel, 0) if y > t1 + 1 else COL_X0
        x1 = COL_X1 + EDGE_R.get(rel, 0) if y > t1 + 1 else COL_X1
        if y == t0:
            x0, x1 = x0 + 4, x1 - 4
        elif y == t0 + 1:
            x0, x1 = x0 + 2, x1 - 2
        elif y == t0 + 2:
            x0, x1 = x0 + 1, x1 - 1
        m[y, x0:x1 + 1] = True
    # bumps and dips along the slab's back edge (it is rock, not a table top)
    if 0 <= t0 - 1 < PH:
        for (a, b) in ((21, 25), (33, 36), (41, 44)):
            m[t0 - 1, a:b + 1] = True
    if 0 <= t0 < PH:
        for x in (27, 28, 38):
            m[t0, x] = False
    return m


STRATA = (0, 8, 15, 23, 31, 36)     # ledge rows below the slab (rel to TOP_Y1)


def paint_rock(m, top=TOP_Y0, seed=7):
    L = blank()
    t1 = top + (TOP_Y1 - TOP_Y0)
    n = value_noise(seed, 3)
    n2 = value_noise(seed + 1, 2)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys.tolist(), xs.tolist()):
        row = np.nonzero(m[y])[0]
        xl, xr = row.min(), row.max()
        u = (x - xl) / max(1, xr - xl)          # 0 left .. 1 right
        if y < t1:                               # top slab: domed, lit, noisy
            cy = (top + t1) / 2
            dv = ((y - cy) / ((t1 - top) / 2 + 0.01)) ** 2 + ((u - 0.45) / 0.62) ** 2
            v = 1.0 - 0.32 * dv + (n[y, x] - 0.5) * 0.3
            if y >= t1 - 3:
                v -= 0.3 * (y - (t1 - 4)) / 3     # the slab's front band turns away from the light
            ch = 't' if v > 0.6 else ('T' if v > 0.3 else 'y')
        else:                                    # front face
            v = 0.80 - 0.60 * u ** 1.2 + (n[y, x] - 0.5) * 0.30 + (n2[y, x] - 0.5) * 0.10
            if u < 0.06:
                v += 0.25                        # the lit left corner of the column
            rel = y - t1
            for k_, s_ in enumerate(STRATA):
                broken = n2[y, x] > (0.62 if k_ % 2 else 0.5)
                if rel == s_ + 1 and not broken:
                    v -= 0.42                    # shadow under each ledge (broken, not ruled)
                elif rel == s_ + 2 and not broken:
                    v += 0.30                    # the lip below catches light
            if y > BASE_Y - 5:
                v -= 0.2 * (y - (BASE_Y - 5)) / 5
            ch = 't' if v > 0.9 else ('T' if v > 0.5 else ('y' if v > 0.2 else 'Y'))
        L[y, x] = ch
    return L


FISSURES = [   # texture fissures (not damage): long, thin, in the rock's own dark
    [(22, 36), (21, 42), (22, 47), (21, 51)],
    [(42, 38), (43, 44), (42, 49)],
    [(26, 55), (27, 60), (26, 66)],
    [(39, 58), (38, 63), (39, 69)],
]


def fissures(L, m, top_shift=0):
    for pts in FISSURES:
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = max(abs(x1 - x0), abs(y1 - y0))
            for k in range(n + 1):
                x = round(x0 + (x1 - x0) * k / n)
                y = round(y0 + (y1 - y0) * k / n) + top_shift
                if 0 <= y < PH and m[y, x] and L[y, x] != '#':
                    L[y, x] = 'Y' if L[y, x] in 'yY' else 'y'
                    if 0 <= x - 1 and m[y, x - 1] and L[y, x - 1] in 'Ty':
                        L[y, x - 1] = 't' if L[y, x - 1] == 'T' else 'T'
    return L


def moss(L, m, top=TOP_Y0, seed=7):
    rnd = random.Random(seed + 9)
    t1 = top + (TOP_Y1 - TOP_Y0)
    # tufts hanging over the slab's front lip
    x = COL_X0 + 1
    while x < COL_X1:
        run = rnd.randint(2, 6)
        if rnd.random() < 0.6:
            for k in range(run):
                xx = x + k
                if xx < COL_X1 and 0 <= t1 < PH and m[t1, xx]:
                    L[t1 - 1, xx] = '8'
                    if rnd.random() < 0.7 and m[t1 + 1, xx]:
                        L[t1 + 1, xx] = '8' if k % 2 else 'Y'
                    if k == run // 2 and rnd.random() < 0.6 and m[t1 + 2, xx]:
                        L[t1 + 2, xx] = '8'
        x += run + rnd.randint(1, 4)
    # a few tufts on the slab top
    for (xx, yy) in ((20, 3), (41, 4), (28, 9), (45, 10), (18, 11)):
        yy += top
        if 0 <= yy < PH and m[yy, xx] and L[yy, xx] != '#':
            L[yy, xx] = '8'
            if m[yy, xx + 1]:
                L[yy, xx + 1] = 'Y'
    return L


def keyline(L, m, top=TOP_Y0):
    R.paint_outline(L, m, prune=True, under=None)
    t1 = top + (TOP_Y1 - TOP_Y0)
    if 0 <= t1 < PH:
        for x in range(PW):
            if m[t1, x] and L[t1, x] not in '#8':
                L[t1, x] = '#'
    return L


RUNE_LIT = ["..#..", ".#8#.", "#8W8#", ".#8#.", "..#.."]
RUNE_DARK = ["..#..", ".#E#.", "#EYE#", ".#E#.", "..#.."]


def runes(L, lit, dy=0):
    for i, ry in enumerate(RUNE_ROWS):
        rows = RUNE_DARK if i < 6 - lit else RUNE_LIT
        R.blk(L, RUNE_X, ry + dy, rows)
    return L


CRACKS = [   # (hit that opens it, polyline): from the base where he is punched, climbing
    (1, [(29, 72), (28, 68), (30, 65), (29, 62)]),
    (1, [(35, 72), (37, 69), (36, 66)]),
    (2, [(29, 62), (26, 58), (27, 54), (24, 50)]),
    (2, [(19, 72), (21, 68), (20, 64), (22, 61)]),
    (3, [(36, 66), (39, 62), (38, 57), (41, 53), (40, 49)]),
    (3, [(24, 50), (22, 46), (23, 42)]),
    (4, [(44, 72), (42, 68), (44, 63), (43, 58)]),
    (4, [(40, 49), (37, 45), (39, 40), (36, 36), (37, 32)]),
    (4, [(23, 42), (20, 38), (22, 33)]),
    (5, [(22, 61), (18, 57), (19, 52), (16, 48)]),
    (5, [(43, 58), (46, 54), (45, 50)]),
    (5, [(22, 33), (25, 31)]),
]
CHIPS = [(2, (COL_X1, 66)), (3, (COL_X0, 57)), (4, (COL_X1, 43)), (5, (COL_X0, 37)), (5, (COL_X1 - 1, 32))]


def cracks(L, m, hits):
    for h, pts in CRACKS:
        if hits >= h:
            R.arc(L, pts, '#')
            for (x, y) in pts[1:]:
                if 0 <= y + 1 < PH and m[y + 1, x] and L[y + 1, x] in 'Ty':
                    L[y + 1, x] = 't'
    return L


def chips(L, m, hits):
    for h, (x, y) in CHIPS:
        if hits >= h:
            side = 1 if x > 32 else -1
            for (dx, dy) in ((0, 0), (0, 1), (0, -1), (-side, 0)):
                L[y + dy, x + dx] = '.'
                m[y + dy, x + dx] = False
            inner = x - side
            for yy in (y - 1, y, y + 1):
                L[yy, inner - (side if L[yy, inner] == '.' else 0)] = '#'
            L[y, inner - side] = 'E'
    return L


ROCKS = {
    'S': [".##.", "#tT#", "#Ty#", ".##."],
    'M': [".####.", "#ttTT#", "#tTTy#", "#TTyY#", ".####."],
    'L': ["..####..", ".#ttTT#.", "#ttTTTy#", "#tTTTyY#", "#TTyyYY#", ".######."],
}
BOULDERS = [  # (top-left x, y, size, moss) round the foot, all inside x 8..55
    (8, 67, 'L', True), (48, 67, 'L', True), (15, 71, 'M', False), (43, 71, 'M', True),
    (27, 73, 'M', False), (35, 74, 'S', False), (21, 75, 'S', False),
]


def boulder(L, cx, cy, r, moss_top=False):
    """A shaded boulder (lit top-left) with a keyline."""
    X, Y = R.centres(PW, PH)
    m = ((X - cx - 0.5) / r) ** 2 + ((Y - cy - 0.5) / (r * 0.8)) ** 2 <= 1
    v = R.lambert(R.sphere_normal(X, Y, cx + 0.5, cy + 0.5, r, r * 0.8))
    ch = np.where(v > 0.8, 't', np.where(v > 0.5, 'T', np.where(v > 0.25, 'y', 'Y')))
    R.paint_part(L, m, ch)
    if moss_top:
        ys, xs = np.nonzero(m & (L != '#'))
        if len(ys):
            top = ys.min()
            for x in xs[ys == top][:3].tolist():
                L[top, x] = '8'
    return m


def rock_block(L, x, y, size, mossy=False):
    rows = ROCKS[size]
    if mossy:
        rows = [rows[0], rows[1].replace('tt', '88', 1)] + rows[2:]
    R.blk(L, int(x), int(y), rows)


def rubble(L, seed=7, spread=1.0, drop=0):
    for (x, y, size, mossy) in BOULDERS:
        w = len(ROCKS[size][0])
        cx = x + w / 2
        nx = ANCHOR[0] + (cx - ANCHOR[0]) * spread - w / 2
        nx = min(max(nx, DRAW_X0), DRAW_X1 + 1 - w)
        rock_block(L, nx, y + drop, size, mossy)
    return L


def clip(L):
    L[:, :DRAW_X0] = '.'
    L[:, DRAW_X1 + 1:] = '.'
    return L


def stand_frame(hits, seed=7):
    """Hits 0..5: runes lit = 6 - hits; cracks and chips accumulate."""
    m = silhouette()
    L = paint_rock(m, seed=seed)
    fissures(L, m)
    moss(L, m, seed=seed)
    keyline(L, m)
    runes(L, 6 - hits)
    cracks(L, m, hits)
    chips(L, m, hits)
    rubble(L, seed)
    return clip(L)


# ------------------------------------------------------------------ dust (no keyline)
def dust(L, puffs):
    X, Y = R.centres(PW, PH)
    for (cx, cy, r) in puffs:
        mm = ((X - cx) / r) ** 2 + ((Y - cy) / (r * 0.72)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, cx, cy, r, r * 0.72))
        ch = np.where(v > 0.72, 'w', np.where(v > 0.38, 'v', 'T'))
        L[mm] = ch[mm]
    return L


def dust_frame(k):
    """liam_pillar_dust.png: 3 frames at the base (the ride and the rise)."""
    L = blank()
    sets = [
        [(11, 73, 4.5), (53, 73, 4.5), (22, 77, 3), (42, 77, 3)],
        [(10, 71, 5.5), (54, 71, 5.5), (18, 76, 3.5), (46, 76, 3.5), (32, 78, 2.5)],
        [(11, 69, 4.5), (53, 69, 4.5), (20, 74, 2.5), (44, 74, 2.5)],
    ]
    dust(L, sets[k])
    return L


# ------------------------------------------------------------------ rise, crumble
def column_at(height, seed=7, hits=0):
    """The whole stand frame with its top slab raised `height` texels above the floor line (0..50),
    the part below the floor hidden: the rise's middle frames."""
    full = stand_frame(hits, seed)
    shift = 50 - height                  # how far down the column is sunk
    out = blank()
    body_ = full.copy()
    body_[BASE_Y - 1:, :] = '.'          # the rubble is redrawn per frame
    sunk = R.shift(body_, 0, shift)
    sunk[BASE_Y:, :] = '.'
    R.composite(out, sunk)
    return out


def rise_frame(k, seed=7):
    """5 frames: 0 the floor bursts; 1-3 the column climbs (12, 27, 42 texels); 4 = stand frame 0."""
    if k == 4:
        return stand_frame(0, seed)
    heights = [3, 14, 29, 44]
    out = column_at(heights[k], seed)
    # the floor line gets a hard lip where the rock punches through
    for x in range(COL_X0 - 1, COL_X1 + 2):
        if out[BASE_Y - 1, x] != '.':
            out[BASE_Y, x] = '#'
    rubble(out, seed + k, spread=1.0 + 0.05 * (3 - k))
    fly = [[(20, 60, 2), (44, 58, 2), (30, 54, 1), (38, 50, 1)],
           [(16, 46, 2), (48, 42, 2), (24, 36, 1), (41, 34, 1)],
           [(14, 32, 1), (50, 28, 2), (22, 24, 1)],
           [(18, 16, 1), (46, 14, 1)]][k]
    for (x, y, s) in fly:
        rock_block(out, x - 2, y - 2, 'S' if s == 1 else 'M')
    dust(out, [[(12, 72, 4.5), (52, 72, 4.5), (32, 76, 4)], [(12, 71, 5), (52, 71, 5)],
               [(12, 72, 4.5), (52, 72, 4.5)], [(12, 73, 3.5), (52, 73, 3.5)]][k])
    return clip(out)


def crumble_frame(k, seed=7):
    """6 frames: 0 split along the cracks; 1 the top slab slides; 2 blocks falling apart;
    3 the crash (dust); 4 a heap in dust; 5 settled rubble."""
    base = stand_frame(5, seed)
    base_nr = base.copy()
    base_nr[BASE_Y - 1:, :] = '.'
    rub = blank()
    rubble(rub, seed)
    out = blank()
    cut1, cut2 = 44, 58

    def band(y0, y1):
        b = blank()
        b[y0:y1, :] = base_nr[y0:y1, :]
        return b
    top, mid, low = band(0, cut1), band(cut1, cut2), band(cut2, BASE_Y)
    if k == 0:
        R.composite(out, rub)
        R.composite(out, low)
        R.composite(out, mid, 1, 0)
        R.composite(out, top, 2, 1)
        for y in (cut1, cut2):
            for x in range(COL_X0, COL_X1 + 3):
                if out[y, x] != '.':
                    out[y, x] = '#'
        dust(out, [(12, 73, 3), (52, 73, 3)])
    elif k == 1:
        R.composite(out, rub)
        R.composite(out, low)
        R.composite(out, mid, -2, 2)
        R.composite(out, top, 5, 5)
        dust(out, [(10, 72, 4), (54, 72, 4), (32, 77, 3)])
        for (x, y, sz) in ((10, 42, 'S'), (50, 36, 'M'), (29, 20, 'S')):
            rock_block(out, x, y, sz)
    elif k == 2:
        R.composite(out, rub)
        R.composite(out, low, 0, 2)
        R.composite(out, mid, -4, 8)
        R.composite(out, top, 5, 14)
        for (x, y, sz) in ((9, 48, 'M'), (49, 44, 'M'), (17, 34, 'S'), (46, 28, 'S'), (31, 24, 'S')):
            rock_block(out, x, y, sz)
        dust(out, [(10, 70, 5), (54, 70, 5), (32, 76, 4)])
    elif k == 3:
        heap = blank()
        rubble(heap, seed + 1, spread=1.1)
        for (x, y, r) in ((22, 64, 3.8), (33, 62, 4.2), (43, 64, 3.6), (27, 69, 3.0), (39, 69, 3.2)):
            boulder(heap, x, y, r, moss_top=True)
        R.composite(out, heap)
        dust(out, [(10, 66, 6.5), (54, 66, 6.5), (32, 57, 7), (21, 60, 4.5), (43, 60, 4.5)])
    elif k == 4:
        heap = blank()
        rubble(heap, seed + 1, spread=1.1)
        for (x, y, r) in ((22, 65, 3.8), (33, 63, 4.2), (43, 65, 3.6), (27, 70, 3.0), (39, 70, 3.2)):
            boulder(heap, x, y, r, moss_top=True)
        R.composite(out, heap)
        dust(out, [(9, 64, 5), (55, 64, 5), (32, 55, 5), (20, 58, 3)])
    else:
        heap = blank()
        rubble(heap, seed + 1, spread=1.1)
        for (x, y, r) in ((22, 66, 3.8), (33, 64, 4.2), (43, 66, 3.6), (27, 71, 3.0), (39, 71, 3.2)):
            boulder(heap, x, y, r, moss_top=True)
        R.composite(out, heap)
        dust(out, [(8, 66, 3), (56, 66, 3)])
    out[:, :DRAW_X0] = '.'
    out[:, DRAW_X1 + 1:] = '.'
    return out


# ------------------------------------------------------------------ shield overlay (4-frame loop)
def shield_overlay(phase):
    """Invincible: two bands of wind spiral up the column (phase 0..3 rotates them a quarter turn), with
    a pale rim round the rock and flecks flung off. Only the band's front arcs, and arcs outside the
    rock, are drawn, so the overlay sits on top of any stand frame. No keyline."""
    m = silhouette()
    O = blank()
    grow = m.copy()
    grow[1:, :] |= m[:-1, :]
    grow[:-1, :] |= m[1:, :]
    grow[:, 1:] |= m[:, :-1]
    grow[:, :-1] |= m[:, 1:]
    O[grow & ~m] = 'l'
    cx = (COL_X0 + COL_X1) / 2 + 0.5
    rx, ry = 22.0, 4.5
    top, bot = TOP_Y0 + 2, BASE_Y - 3
    for band in range(2):
        n = 420
        for i in range(n):
            u = i / (n - 1)
            t = 2 * math.pi * (1.6 * u) + phase * math.pi / 2 + band * math.pi
            x = cx + rx * math.cos(t)
            y = bot - (bot - top) * u + ry * math.sin(t)
            s_ = math.sin(t)
            xi, yi = int(round(x)), int(round(y))
            if not (DRAW_X0 <= xi <= DRAW_X1 and 0 <= yi < PH):
                continue
            if s_ < 0 and m[yi, xi]:
                continue
            ch = 'W' if s_ > 0.5 else ('l' if s_ > -0.25 else 'w')
            O[yi, xi] = ch
            if s_ > 0.2 and yi + 1 < PH:
                O[yi + 1, xi] = 'l' if s_ > 0.6 else 'w'
    for (x, y) in [(10, 30), (54, 44), (9, 58), (55, 20), (12, 12), (52, 66)][phase:phase + 3]:
        O[y, x] = 'W'
        O[y, x + 1] = 'l'
    return O
