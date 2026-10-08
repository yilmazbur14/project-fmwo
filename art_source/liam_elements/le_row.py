"""The pillar row (ADDENDUM3 A.1, E.4): his 16 shorter neighbour pillars, wall to wall across the top of
the ring, so nobody gets behind or beside him.

liam_row_pillar_rise / _stand / _crumble: 64x80 cells, rows = 3 variants, pivot (32, 72) on the floor
line (his own pillar's cell and anchor). ROW_STAND_TEXELS 34: the slab top's stand point sits 34 texels
above the floor line (his own is 50), so the neighbours read as a lower wall with him on the tall one.
No runes (only his pillar is hittable and counts hits); the same slate, strata, fissures, moss and
boulders as his, three seeds so a row never reads as one stamp.
"""
import numpy as np

import le_rig as R
import le_pillar as PL

STAND_TEXELS = 34
TOP = PL.ANCHOR[1] - STAND_TEXELS - (PL.STAND[1] - PL.TOP_Y0)      # the slab's first row: 30
SHIFT = TOP - PL.TOP_Y0                                              # 16 rows lower than his
VARIANTS = 3
SEEDS = (21, 34, 55)


def _boulders(L, v, drop=0, spread=1.0):
    """A different ring of rubble per variant (same blocks as his)."""
    sets = [
        [(8, 67, 'L', True), (47, 68, 'M', True), (16, 71, 'M', False), (29, 73, 'S', False), (38, 72, 'M', False)],
        [(9, 68, 'M', False), (46, 67, 'L', True), (20, 72, 'S', True), (33, 73, 'M', False), (42, 74, 'S', False)],
        [(10, 67, 'L', False), (48, 67, 'L', True), (24, 73, 'M', True), (37, 74, 'S', False)],
    ]
    for (x, y, size, mossy) in sets[v]:
        w = len(PL.ROCKS[size][0])
        cx = x + w / 2
        nx = PL.ANCHOR[0] + (cx - PL.ANCHOR[0]) * spread - w / 2
        nx = min(max(nx, PL.DRAW_X0), PL.DRAW_X1 + 1 - w)
        PL.rock_block(L, nx, y + drop, size, mossy)
    return L


def _details(L, m, v):
    """Per-variant character: a chipped corner, an extra ledge crack, a clump of moss down the face."""
    if v == 0:
        for (x, y) in ((PL.COL_X1, TOP + 22), (PL.COL_X1, TOP + 23), (PL.COL_X1 - 1, TOP + 22)):
            if m[y, x]:
                L[y, x] = '.'
                m[y, x] = False
        L[TOP + 22, PL.COL_X1 - 2] = '#'
        L[TOP + 23, PL.COL_X1 - 1] = '#'
    elif v == 1:
        R.arc(L, [(19, TOP + 20), (22, TOP + 24), (21, TOP + 29), (23, TOP + 33)], '#')
    else:
        for (x, y) in ((40, TOP + 18), (41, TOP + 19), (40, TOP + 20), (42, TOP + 21), (41, TOP + 22)):
            if m[y, x] and L[y, x] != '#':
                L[y, x] = '8' if (x + y) % 2 else 'Y'
    return L


def stand(v=0):
    """The neighbour at full height (1 frame per variant)."""
    seed = SEEDS[v]
    m = PL.silhouette(top=TOP)
    L = PL.paint_rock(m, top=TOP, seed=seed)
    PL.fissures(L, m, top_shift=SHIFT)
    PL.moss(L, m, top=TOP, seed=seed)
    PL.keyline(L, m, top=TOP)
    _details(L, m, v)
    _boulders(L, v)
    return PL.clip(L)


RISE_HEIGHTS = (3, 10, 18, 26, 32)


def rise(k, v=0):
    """5 frames (the ripple's per-pillar clip): 0 the floor bursts; 1-4 it punches up through its own
    rubble (10, 18, 26, 32 texels) with chips flying and dust at its foot; stand follows."""
    full = stand(v)
    h = RISE_HEIGHTS[k]
    body_ = full.copy()
    body_[PL.BASE_Y - 1:, :] = '.'
    sunk = R.shift(body_, 0, STAND_TEXELS - h)
    sunk[PL.BASE_Y:, :] = '.'
    out = PL.blank()
    R.composite(out, sunk)
    for x in range(PL.COL_X0 - 1, PL.COL_X1 + 2):
        if out[PL.BASE_Y - 1, x] != '.':
            out[PL.BASE_Y, x] = '#'
    _boulders(out, v, spread=1.0 + 0.05 * (4 - k))
    fly = [[(20, 62, 1), (44, 60, 2), (31, 58, 1)],
           [(17, 54, 2), (47, 50, 1), (27, 48, 1), (40, 46, 1)],
           [(15, 44, 1), (49, 40, 2), (24, 38, 1)],
           [(18, 34, 1), (46, 32, 1)],
           [(47, 26, 1)]][k]
    for (x, y, s) in fly:
        PL.rock_block(out, x - 2, y - 2, 'S' if s == 1 else 'M')
    PL.dust(out, [[(12, 72, 4.5), (52, 72, 4.5), (32, 76, 4)], [(12, 71, 5), (52, 71, 5), (32, 76, 3)],
                  [(12, 72, 4.5), (52, 72, 4.5)], [(12, 73, 3.8), (52, 73, 3.8)], [(13, 73, 3), (51, 73, 3)]][k])
    return PL.clip(out)


def crumble(k, v=0):
    """6 frames: 0 it splits along its strata; 1 the slab slides off; 2 blocks falling apart; 3 the crash
    (dust); 4 a heap in the dust; 5 settled rubble, the dust thinning (the row goes down with him)."""
    base = stand(v)
    base_nr = base.copy()
    base_nr[PL.BASE_Y - 1:, :] = '.'
    rub = PL.blank()
    _boulders(rub, v)
    out = PL.blank()
    cut1, cut2 = TOP + 18, TOP + 30

    def band(y0, y1):
        b = PL.blank()
        b[y0:y1, :] = base_nr[y0:y1, :]
        return b
    top, mid, low = band(0, cut1), band(cut1, cut2), band(cut2, PL.BASE_Y)
    if k == 0:
        R.composite(out, rub)
        R.composite(out, low)
        R.composite(out, mid, 1, 0)
        R.composite(out, top, 2, 1)
        for y in (cut1, cut2):
            for x in range(PL.COL_X0, PL.COL_X1 + 3):
                if out[y, x] != '.':
                    out[y, x] = '#'
        PL.dust(out, [(12, 73, 3), (52, 73, 3)])
    elif k == 1:
        R.composite(out, rub)
        R.composite(out, low)
        R.composite(out, mid, -2, 2)
        R.composite(out, top, 5, 4)
        PL.dust(out, [(10, 72, 4), (54, 72, 4), (32, 77, 3)])
        for (x, y, sz) in ((10, 50, 'S'), (50, 44, 'M')):
            PL.rock_block(out, x, y, sz)
    elif k == 2:
        R.composite(out, rub)
        R.composite(out, low, 0, 2)
        R.composite(out, mid, -4, 6)
        R.composite(out, top, 5, 11)
        for (x, y, sz) in ((9, 52, 'M'), (49, 48, 'M'), (18, 42, 'S'), (45, 38, 'S')):
            PL.rock_block(out, x, y, sz)
        PL.dust(out, [(10, 70, 5), (54, 70, 5), (32, 76, 4)])
    else:
        heap = PL.blank()
        _boulders(heap, v, spread=1.1)
        lift = {3: 0, 4: 1, 5: 2}[k]
        for (x, y, r) in ((23, 66, 3.4), (33, 64, 3.8), (42, 66, 3.2), (28, 70, 2.8), (38, 70, 3.0)):
            PL.boulder(heap, x, y + lift, r, moss_top=(v != 1))
        R.composite(out, heap)
        puffs = {3: [(10, 66, 6.5), (54, 66, 6.5), (32, 58, 6.5), (21, 61, 4.5), (43, 61, 4.5)],
                 4: [(9, 64, 5), (55, 64, 5), (32, 56, 4.5), (20, 59, 3)],
                 5: [(8, 66, 3), (56, 66, 3)]}[k]
        PL.dust(out, puffs)
    return PL.clip(out)


def sheets():
    """(rise, stand, crumble): lists of rows (variants) of frames."""
    return ([[rise(k, v) for k in range(len(RISE_HEIGHTS))] for v in range(VARIANTS)],
            [[stand(v)] for v in range(VARIANTS)],
            [[crumble(k, v) for k in range(6)] for v in range(VARIANTS)])
