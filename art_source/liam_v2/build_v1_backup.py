"""Liam v2 base sprite, layered.  Run: python build.py"""
import math
from lib import *

# ------------------------------------------------------------------ helpers
def tcapsule_mask(ax, ay, bx, by, r0, r1):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
            qx, qy = ax + t * dx, ay + t * dy
            if math.hypot(px - qx, py - qy) <= r0 + (r1 - r0) * t:
                m[y][x] = True
    return m

def tcapsule_normal(x, y, ax, ay, bx, by, r0, r1):
    px, py = x + 0.5, y + 0.5
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    r = r0 + (r1 - r0) * t
    nx, ny = (px - qx) / r, (py - qy) / r
    d2 = nx * nx + ny * ny
    if d2 >= 1:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))

def shade_fn(normal_fn, ramp, th, light=LIGHT, amb=0.0):
    def f(x, y):
        return quant(lambert(normal_fn(x, y), light, amb), ramp, th)
    return f

def layer():
    return blank_chars()

# ------------------------------------------------------------------ geometry (base pose)
G = dict(
    torso=[(22, 24), (18, 26), (15, 29), (13, 33), (12, 38), (12, 42), (13, 45), (16, 48),
           (46, 48), (48, 45), (49, 41), (49, 36), (47, 31), (44, 27), (40, 25), (36, 24)],
    near_up=(45, 31, 57, 37, 4.6, 3.9),
    near_fore=(57, 37, 50, 44, 3.7, 3.2),
    near_fist=(48.5, 45.5, 3.7, 3.4),
    far_up=(17, 31, 11, 39, 4.6, 3.9),
    far_fore=(11, 39, 9, 46, 3.7, 3.3),
    far_fist=(8.5, 48.5, 3.6, 3.4),
    far_leg=[(16, 47), (31, 47), (30, 51), (27, 54), (24, 57), (23, 59), (10, 59), (11, 55), (13, 51)],
    near_leg=[(32, 47), (48, 46), (49, 50), (49, 55), (49, 59), (36, 59), (35, 55), (33, 51)],
    far_shoe=[(9, 58), (24, 58), (25, 63), (3, 63), (3, 61), (5, 59)],
    near_shoe=[(36, 58), (50, 58), (53, 60), (54, 63), (35, 63)],
)

JACKET = 'NnJj'      # dark -> light
JTH = [0.30, 0.58, 0.86]
SKIN = 'fdsa'
STH = [0.32, 0.62, 0.9]
TROU = 'zQqp'
TTH = [0.30, 0.60, 0.88]
SHOE = 'xOo'
SHTH = [0.45, 0.85]

def build_legs():
    L = layer()
    far = poly_mask(G['far_leg'])
    near = poly_mask(G['near_leg'])
    paint_mask(L, far, shade_fn(lambda x, y: tcapsule_normal(x, y, 24, 47, 17, 58, 7.5, 6.0), TROU, TTH))
    paint_outline(L, far)
    paint_mask(L, near, shade_fn(lambda x, y: tcapsule_normal(x, y, 40, 46, 42, 58, 8.0, 6.5), TROU, TTH))
    paint_outline(L, near)
    fs = poly_mask(G['far_shoe'])
    ns = poly_mask(G['near_shoe'])
    paint_mask(L, fs, shade_fn(lambda x, y: sphere_normal(x, y, 14, 62, 11, 5), SHOE, SHTH))
    paint_outline(L, fs)
    paint_mask(L, ns, shade_fn(lambda x, y: sphere_normal(x, y, 44, 62, 10, 5), SHOE, SHTH))
    paint_outline(L, ns)
    return L

def build_torso():
    L = layer()
    t = poly_mask(G['torso'])
    paint_mask(L, t, shade_fn(lambda x, y: sphere_normal(x, y, 30, 39, 21, 17), JACKET, JTH))
    paint_outline(L, t)
    build_collar_tie(L)
    return L

def arm(L, up, fore, fist, jacket_th=JTH):
    mu = tcapsule_mask(*up)
    mf = tcapsule_mask(*fore)
    ma = m_or(mu, mf)
    def nfn(x, y):
        a = tcapsule_normal(x, y, *up)
        b = tcapsule_normal(x, y, *fore)
        # choose the closer segment
        du = seg_dist(x + .5, y + .5, up[0], up[1], up[2], up[3])[0]
        dfo = seg_dist(x + .5, y + .5, fore[0], fore[1], fore[2], fore[3])[0]
        return a if du < dfo else b
    paint_mask(L, ma, shade_fn(nfn, JACKET, jacket_th))
    paint_outline(L, ma)
    mfist = ellipse_mask(*fist)
    paint_mask(L, mfist, shade_fn(lambda x, y: sphere_normal(x, y, fist[0], fist[1], fist[2], fist[3]), SKIN, STH))
    paint_outline(L, mfist)
    return L

def build_near_arm():
    return arm(layer(), G['near_up'], G['near_fore'], G['near_fist'])

def build_far_arm():
    return arm(layer(), G['far_up'], G['far_fore'], G['far_fist'])

# ------------------------------------------------------------------ compose
def compose(layers):
    cv = blank_chars()
    for l in layers:
        composite(cv, l)
    return cv

# ------------------------------------------------------------------ head
HAIR = 'khHr'
HTH = [0.25, 0.55, 0.86]

def curls_layer(curls, L=None, ramp=HAIR, th=HTH, crease='k', outline=True, light=LIGHT):
    L = L or layer()
    ids = [[-1] * W for _ in range(H)]
    for i, (cx, cy, r) in enumerate(curls):
        m = ellipse_mask(cx, cy, r, r)
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    ids[y][x] = i
                    L[y][x] = quant(lambert(sphere_normal(x, y, cx, cy, r, r), light), ramp, th)
    union = [[ids[y][x] >= 0 for x in range(W)] for y in range(H)]
    # creases where a later curl overlaps an earlier one
    for y in range(H):
        for x in range(W):
            i = ids[y][x]
            if i < 0:
                continue
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                X, Y = x + dx, y + dy
                if 0 <= X < W and 0 <= Y < H and ids[Y][X] >= 0 and ids[Y][X] < i:
                    # pixel on edge of curl i bordering earlier curl: crease on the earlier curl side
                    L[Y][X] = crease
    if outline:
        paint_outline(L, union)
    return L, union


def block(L, x0, y0, rows, width=None):
    rows = [r for r in rows]
    wd = width or len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, 'row %d (y=%d) len %d != %d: %r' % (i, y0 + i, len(r), wd, r)
    overlay(L, x0, y0, '\n'.join(rows))

def build_hair():
    curls = [
        (40.6, 18.2, 2.2), (41.8, 14.8, 2.4),
        (21.5, 6.2, 2.4), (25.6, 4.9, 2.5), (30.0, 4.6, 2.5), (34.4, 5.0, 2.5), (38.4, 6.8, 2.4),
        (18.4, 9.2, 2.3), (22.4, 8.4, 2.5), (26.6, 7.6, 2.6), (31.0, 7.3, 2.6), (35.4, 8.0, 2.6),
        (39.6, 10.0, 2.5), (42.4, 11.8, 2.2),
        (17.2, 12.4, 2.0),
    ]
    L, union = curls_layer(curls, ramp='khhH', th=[0.3, 0.62, 0.9])
    return L, union

FACE = [  # x 16..41, y 12..28
    ".#hssaaaasssssssssddhk....",   # 12 forehead
    ".########s#########dhk....",   # 13 glasses top frame
    ".##LLLLL###LLLLLLL######..",   # 14
    ".##LLLLL#d#LLLLLLL#dh#dd#.",   # 15
    ".##LLLLl#d#LLLLLll#dh#fd#.",   # 16
    ".########d#########dh#gf#.",   # 17 bottom frame
    ".#hsass#adsssssssddhhh#f#.",   # 18 cheeks + nose
    ".#hHhs#sdfdssdhHhhHhhhh#..",   # 19 nose tip, beard top
    "#hhHhhHHhkhHHhhk##hHhhh#..",   # 20 mustache + smirk corner
    "#hHh#WWWWWWWWWWWW#hhHhh#..",   # 21 grin top
    "#hhHh#WWwWWwWWwW#hHhhH#...",   # 22
    ".#hhHh#WWWWWWWW#hHhhHh#...",   # 23
    ".#hHhhk########khhHhh#....",   # 24 lip line
    ".#hhHrHhHhhHhhHhkhHh#.....",   # 25
    "..#hhHhHhhHhkhHhhk#.......",   # 26
    "...#hHhhHhhhkhkk##........",   # 27
    "....############..........",   # 28
]

BAND = [  # x 16..43, y 7..12
    "....#########...............",   # 7  plate top
    ".####mmMMMMM###########.###.",   # 8
    "#TTT#mMMMMMe#TTTTTTTTTT##TT#",   # 9
    "#yyy#MeeeeeE#yyyyyyyyyyTTTy#",   # 10
    ".######################yyyy#",   # 11
    ".......................####.",   # 12
]

def build_collar_tie(L):
    fc = poly_mask([(20, 24), (24, 27), (21, 29), (17, 32), (15, 31), (15, 28), (17, 25)])
    nc = poly_mask([(33, 26), (37, 24), (42, 26), (45, 30), (42, 32), (38, 30), (35, 29)])
    for m, c in ((fc, (17, 27, 8, 6)), (nc, (38, 27, 8, 6))):
        paint_mask(L, m, shade_fn(lambda x, y, c=c: sphere_normal(x, y, *c), 'vwW', [0.35, 0.7]))
        paint_outline(L, m)
    tie = poly_mask([(26, 28), (31, 28), (30, 31), (32, 36), (32, 40), (29, 43), (26, 40), (26, 35), (27, 31)])
    paint_mask(L, tie, shade_fn(lambda x, y: capsule_normal(x, y, 28.5, 28, 29, 42, 4.0), 'YyTt', [0.3, 0.6, 0.9]))
    paint_outline(L, tie)
    # knot separation line
    put(L, 27, 31, '###')
    return L

def build_head():
    L = layer()
    skull = ellipse_mask(29, 17, 10.5, 11)
    paint_mask(L, skull, shade_fn(lambda x, y: sphere_normal(x, y, 26, 15, 12, 12), SKIN, STH))
    paint_outline(L, skull)
    hairL, hair_union = build_hair()
    composite(L, hairL)
    block(L, 16, 12, FACE)
    block(L, 16, 7, BAND)
    return L

def build_tails():
    L = layer()
    t1 = poly_mask([(41, 10), (44, 10), (48, 16), (52, 22), (55, 26), (51, 27), (47, 21), (42, 14)])
    t2 = poly_mask([(40, 12), (43, 12), (46, 19), (48, 26), (45, 27), (42, 20), (40, 15)])
    paint_mask(L, t2, lambda x, y: 'y')
    paint_outline(L, t2)
    paint_mask(L, t1, lambda x, y: 'T' if (x - 41) - (y - 10) * 0.62 < 1.6 else 'y')
    paint_outline(L, t1)
    return L

def build_base_layers():
    return dict(tails=build_tails(), far=build_far_arm(), legs=build_legs(), torso=build_torso(),
                near=build_near_arm(), head=build_head())

if __name__ == '__main__':
    Ls = build_base_layers()
    cv = compose([Ls[k] for k in ('tails', 'far', 'legs', 'torso', 'near', 'head')])
    open('out/base.txt', 'w').write(to_text(cv))
    preview(cv, 'out/base_8x.png')
    print('ok')
