"""Fuse warning: 2 frames. A = normal colours + glowing cracks + small spark, jitter left.
B = white-hot red flash + white cracks + big spark, swelled 1px, jitter right."""
from figures import *
from rig import STAND

SPARK_W = hx('ffffff')
SPARK_Y = hx('fbf236')
SPARK_O = hx('ff9b3b')
SPARK_R = hx('e8452c')
WICK = hx('4a3c36')
WICK_L = hx('8a7a6e')
GLOW_CORE = hx('fff6a0')
GLOW_EDGE = hx('ffa43a')
ORANGE_CORE = hx('e8621a')
ORANGE_EDGE = hx('ffb040')

# crack pixels in HEAD-grid coords: (x, y, 'c' core | 'e' edge glow)
CRACKS = {
    'plumber': [(9, 1, 'c'), (10, 2, 'c'), (9, 3, 'c'), (10, 4, 'e'), (3, 2, 'c'), (2, 3, 'e'), (3, 3, 'c')],
    'hedgehog': [(9, 1, 'e'), (9, 2, 'c'), (10, 3, 'c'), (11, 3, 'e'), (4, 3, 'c'), (5, 4, 'c'), (4, 4, 'e')],
    'mascot': [(4, 1, 'c'), (3, 2, 'c'), (3, 3, 'c'), (2, 4, 'c'), (2, 5, 'e')],
    'gamer': [(8, 1, 'e'), (9, 1, 'c'), (10, 2, 'c'), (11, 3, 'c'), (12, 4, 'e'), (3, 2, 'c'), (2, 3, 'e')],
}
CRACK_COLS = {'mascot': (ORANGE_CORE, ORANGE_EDGE)}
WICK_X = {'plumber': 6, 'hedgehog': 7, 'mascot': 6, 'gamer': 7}

FLASH_RAMP = [hx('5e0f1c'), hx('b3202a'), hx('ff5a3c'), hx('ffb4a0'), hx('ffffff')]


def lum(p):
    return 0.3 * p[0] + 0.59 * p[1] + 0.11 * p[2]


def flash(px, keep):
    out = copy(px)
    for y, r in enumerate(out):
        for x, p in enumerate(r):
            if p[3] == 0 or p[:3] == (0, 0, 0) or (x, y) in keep:
                continue
            L = lum(p)
            idx = 0 if L < 60 else 1 if L < 110 else 2 if L < 165 else 3 if L < 225 else 4
            out[y][x] = FLASH_RAMP[idx]
    return out


def spark_pts(cx, tipy, big):
    pts = [(cx, tipy + 2, WICK), (cx, tipy + 1, WICK_L)]
    if not big:
        pts += [(cx, tipy, SPARK_W), (cx - 1, tipy, SPARK_Y), (cx + 1, tipy, SPARK_Y), (cx, tipy - 1, SPARK_Y),
                (cx + 1, tipy - 2, SPARK_O), (cx - 2, tipy - 1, SPARK_R)]
    else:
        pts += [(cx, tipy, SPARK_W), (cx - 1, tipy, SPARK_W), (cx + 1, tipy, SPARK_Y), (cx, tipy - 1, SPARK_W),
                (cx - 2, tipy, SPARK_Y), (cx + 2, tipy, SPARK_O), (cx, tipy - 2, SPARK_Y), (cx, tipy - 3, SPARK_O),
                (cx - 2, tipy - 2, SPARK_O), (cx + 2, tipy - 2, SPARK_Y), (cx + 3, tipy - 3, SPARK_R),
                (cx - 3, tipy + 1, SPARK_R), (cx + 2, tipy + 1, SPARK_O)]
    return pts


def fuse_frames(fig):
    out = []
    for i in range(2):
        big = i == 1
        jx = -1 if i == 0 else 1
        head_dy = 0 if i == 0 else -1
        f = fig.frame(STAND, head_off=(jx, head_dy), body_off=(jx, 0))
        close_outline(f)
        # cracks
        hx0 = FX0 + fig.head_dx + jx
        hy0 = FY0 + fig.head_dy + head_dy
        core, edge = CRACK_COLS.get(fig.name, (GLOW_CORE, GLOW_EDGE))
        if big:
            core, edge = SPARK_W, SPARK_Y
        keep = set()
        for (x, y, k) in CRACKS[fig.name]:
            X, Y = hx0 + x, hy0 + y
            if f[Y][X][3] and f[Y][X][:3] != (0, 0, 0):
                f[Y][X] = core if k == 'c' else edge
                keep.add((X, Y))
        if big:
            f = flash(f, keep)
        for (x, y, c) in spark_pts(hx0 + WICK_X[fig.name], hy0 - 3, big):
            if 0 <= x < 24 and 0 <= y < 24:
                f[y][x] = c
        out.append(f)
    return out


if __name__ == '__main__':
    rows = []
    for fig in FIGURES:
        fr = fuse_frames(fig)
        rows.append(hstack([zoom([r[0:24] for r in f[0:22]], 10, ARENA_GREEN, True) for f in fr], gap=10))
    save(vstack([hstack(rows[:2], gap=20), hstack(rows[2:], gap=20)], gap=20), WIP + 'fuse_sheet.png')
    print('ok')
