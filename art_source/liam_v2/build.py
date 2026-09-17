"""Liam v2 base sprite, layered.  Run: python build.py"""
import math
from lib import *
from lib import _norm

# ------------------------------------------------------------------ helpers
def seg_t(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return t, ax + t * dx, ay + t * dy

def tcapsule_mask(ax, ay, bx, by, r0, r1):
    m = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            t, qx, qy = seg_t(px, py, ax, ay, bx, by)
            if math.hypot(px - qx, py - qy) <= r0 + (r1 - r0) * t:
                m[y][x] = True
    return m

def tcapsule_normal(x, y, ax, ay, bx, by, r0, r1):
    px, py = x + 0.5, y + 0.5
    t, qx, qy = seg_t(px, py, ax, ay, bx, by)
    r = r0 + (r1 - r0) * t
    nx, ny = (px - qx) / r, (py - qy) / r
    d2 = nx * nx + ny * ny
    if d2 >= 1:
        l = math.sqrt(d2)
        return (nx / l, ny / l, 0.0)
    return (nx, ny, math.sqrt(1 - d2))

def shade_fn(normal_fn, ramp, th, light=LIGHT, amb=0.0, wrap=0.0):
    def f(x, y):
        v = lambert(normal_fn(x, y), light, amb)
        if wrap:
            n = normal_fn(x, y)
            Lv = _norm(light)
            raw = n[0] * Lv[0] + n[1] * Lv[1] + n[2] * Lv[2]
            v = max(0.0, (raw + wrap) / (1 + wrap))
        return quant(v, ramp, th)
    return f

def layer():
    return blank_chars()

def block(L, x0, y0, rows):
    wd = len(rows[0])
    for i, r in enumerate(rows):
        assert len(r) == wd, 'row %d (y=%d) len %d != %d: %r' % (i, y0 + i, len(r), wd, r)
    overlay(L, x0, y0, '\n'.join(rows))

def polyline_mask(pts, r):
    m = [[False] * W for _ in range(H)]
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        mm = tcapsule_mask(ax, ay, bx, by, r, r)
        for y in range(H):
            for x in range(W):
                if mm[y][x]:
                    m[y][x] = True
    return m

def compose(layers):
    cv = blank_chars()
    for l in layers:
        composite(cv, l)
    return cv

# ------------------------------------------------------------------ ramps
JACKET = 'NnJji'
JTH = [0.307, 0.577, 0.81, 0.961]
SKIN = 'fdsa'
STH = [0.32, 0.62, 0.9]
TROU = 'zQqp'
TTH = [0.28, 0.58, 0.88]
SHOE = 'xOo'
SHTH = [0.42, 0.86]
WRAP = 'vwW'
WTH = [0.3, 0.62]
HAIR = 'khhH'
HTH = [0.3, 0.62, 0.9]

# ------------------------------------------------------------------ geometry (base pose)
G = dict(
    torso=[(22, 23), (18, 24), (15, 26), (13, 29), (11, 33), (11, 38), (11, 42), (13, 45), (15, 47),
           (45, 47), (47, 45), (49, 41), (49, 36), (48, 32), (46, 28), (43, 25), (39, 23)],
    torso_light=(27, 37, 23, 19),
    far_arm=dict(delt=(11.0, 31.5, 5.3), up=(10, 33, 7, 41, 4.8, 4.2), fore=(7, 41, 6, 48, 3.9, 3.5),
                 sleeve_end=2.6, fist=(6.0, 50.5, 3.9, 3.6)),
    near_arm=dict(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 58, 38, 4.7, 4.1), fore=(58, 38, 51, 45, 3.8, 3.4),
                  sleeve_end=2.6, fist=(49.8, 46.3, 3.8, 3.5)),
    far_leg=[(15, 46), (30, 46), (30, 50), (27, 53), (24, 56), (23, 58), (9, 58), (10, 54), (12, 50)],
    near_leg=[(31, 46), (47, 46), (48, 50), (49, 54), (49, 58), (36, 58), (35, 54), (33, 50)],
    far_shoe=[(8, 57), (23, 57), (24, 59), (24, 63), (2, 63), (2, 61), (4, 59)],
    near_shoe=[(35, 57), (49, 57), (52, 59), (55, 61), (55, 63), (35, 63)],
    far_collar=[(22, 24), (25, 28), (22, 31), (15, 32), (14, 29), (17, 26)],
    near_collar=[(35, 25), (39, 24), (44, 27), (47, 31), (43, 32), (38, 30), (35, 28)],
)

# ------------------------------------------------------------------ legs
def build_legs():
    L = layer()
    far = poly_mask(G['far_leg'])
    near = poly_mask(G['near_leg'])
    paint_part(L, far, shade_fn(lambda x, y: tcapsule_normal(x, y, 24, 46, 16, 58, 7.5, 6.5), TROU, TTH))
    paint_part(L, near, shade_fn(lambda x, y: tcapsule_normal(x, y, 40, 46, 42, 58, 8.0, 6.8), TROU, TTH))
    fs = poly_mask(G['far_shoe'])
    ns = poly_mask(G['near_shoe'])
    paint_part(L, fs, shade_fn(lambda x, y: sphere_normal(x, y, 11, 60, 11, 5), SHOE, SHTH))
    paint_part(L, ns, shade_fn(lambda x, y: sphere_normal(x, y, 43, 60, 11, 5), SHOE, SHTH))
    return L

# ------------------------------------------------------------------ torso
def build_torso(details=True):
    L = layer()
    t = poly_mask(G['torso'])
    paint_part(L, t, shade_fn(lambda x, y: sphere_normal(x, y, *G['torso_light']), JACKET, JTH, wrap=0.35))
    if not details:
        return L
    # belt
    belt = m_and(t, poly_mask([(0, 43), (63, 42), (63, 46), (0, 47)]))
    paint_mask(L, belt, lambda x, y: 'N' if y > 43 else 'n')
    bo = outline_pixels(belt, prune=True)
    for y in range(H):
        for x in range(W):
            if bo[y][x]:
                L[y][x] = '#'
    plate = poly_mask([(25, 42), (32, 42), (32, 47), (25, 47)])
    paint_part(L, plate, shade_fn(lambda x, y: sphere_normal(x, y, 26, 43, 7, 5), 'eMm', [0.45, 0.85]))
    # collar
    fc = poly_mask(G['far_collar'])
    nc = poly_mask(G['near_collar'])
    for m, c in ((fc, (15, 27, 9, 7)), (nc, (39, 26, 10, 8))):
        paint_part(L, m, shade_fn(lambda x, y, c=c: sphere_normal(x, y, *c), 'vwW', [0.3, 0.66]))
    # tie
    tie = poly_mask([(26, 28), (31, 28), (30, 31), (32, 35), (31, 39), (28, 41), (26, 38), (26, 34), (27, 31)])
    paint_part(L, tie, shade_fn(lambda x, y: capsule_normal(x, y, 28.5, 28, 28.5, 41, 3.6), 'YyTt', [0.3, 0.6, 0.9]))
    put(L, 27, 31, '###')
    return L

# ------------------------------------------------------------------ arms
def build_arm(A, bandage=True):
    L = layer()
    dx_, dy_, dr = A['delt']
    up, fore = A['up'], A['fore']
    m_delt = ellipse_mask(dx_, dy_, dr, dr)
    m_up = tcapsule_mask(*up)
    m_fore = tcapsule_mask(*fore)
    ax, ay, bx, by = fore[0], fore[1], fore[2], fore[3]
    flen = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / flen, (by - ay) / flen
    se = A['sleeve_end']
    def along_perp(x, y):
        px, py = x + .5 - ax, y + .5 - ay
        return px * ux + py * uy, -px * uy + py * ux
    m_sleeve_fore = [[m_fore[y][x] and along_perp(x, y)[0] < se for x in range(W)] for y in range(H)]
    m_sleeve = m_or(m_delt, m_up, m_sleeve_fore)
    arm_mask = m_or(m_delt, m_up, m_fore)
    def jn(x, y):
        du = seg_dist(x + .5, y + .5, up[0], up[1], up[2], up[3])[0] / up[4]
        dd = math.hypot(x + .5 - dx_, y + .5 - dy_) / dr
        if dd < du:
            return sphere_normal(x, y, dx_, dy_, dr, dr)
        return tcapsule_normal(x, y, *up)
    paint_mask(L, m_or(m_delt, m_up), shade_fn(jn, JACKET, JTH, wrap=0.3))
    # rolled cuff: lighter band
    cuff = m_sub(m_sleeve_fore, m_or(m_delt, m_up))
    paint_mask(L, m_sleeve_fore, lambda x, y: 'j' if lambert(tcapsule_normal(x, y, *fore)) > 0.45 else 'J')
    def fn(x, y):
        al, pe = along_perp(x, y)
        v = lambert(tcapsule_normal(x, y, *fore))
        if bandage and int(math.floor(al + pe * 0.8 + 100)) % 3 == 0:
            return 'v' if v < 0.6 else 'w'
        return quant(v, WRAP, WTH)
    m_wrap = m_sub(m_fore, m_sleeve)
    paint_mask(L, m_wrap, fn)
    paint_outline(L, arm_mask)
    # line where the sleeve ends
    for y in range(H):
        for x in range(W):
            if m_wrap[y][x]:
                for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    X, Y = x + ddx, y + ddy
                    if 0 <= X < W and 0 <= Y < H and m_sleeve_fore[Y][X] and not m_or(m_delt, m_up)[Y][X]:
                        L[y][x] = '#'
                        break
    fx, fy, frx, fry = A['fist']
    mf = ellipse_mask(fx, fy, frx, fry)
    paint_part(L, mf, shade_fn(lambda x, y: sphere_normal(x, y, fx, fy, frx, fry), SKIN, STH))
    return L

# ------------------------------------------------------------------ head
def curls_layer(curls, ramp=HAIR, th=HTH, crease='k', light=LIGHT):
    L = layer()
    ids = [[-1] * W for _ in range(H)]
    for i, (cx, cy, r) in enumerate(curls):
        m = ellipse_mask(cx, cy, r, r)
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    ids[y][x] = i
                    L[y][x] = quant(lambert(sphere_normal(x, y, cx, cy, r, r), light), ramp, th)
    union = [[ids[y][x] >= 0 for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            i = ids[y][x]
            if i < 0:
                continue
            for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                X, Y = x + ddx, y + ddy
                if 0 <= X < W and 0 <= Y < H and 0 <= ids[Y][X] < i:
                    L[Y][X] = crease
    paint_outline(L, union)
    return L, union

HAIR_CURLS = [
    # back / top row (drawn first so front curls overlap and crease them)
    (19.2, 6.2, 2.6), (23.4, 4.0, 2.8), (28.2, 4.1, 3.0), (33.2, 4.2, 3.0), (37.8, 4.6, 2.8), (41.4, 7.2, 2.6),
    (42.6, 14.4, 2.5), (41.4, 18.0, 2.3),
    # front row
    (16.4, 9.2, 2.5), (21.0, 7.2, 2.8), (25.8, 6.3, 2.9), (30.6, 6.0, 3.0), (35.4, 6.6, 2.9), (39.8, 8.6, 2.8),
    (43.0, 11.0, 2.4), (15.2, 12.2, 2.1),
]

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

def build_head():
    L = layer()
    skull = ellipse_mask(29, 17, 10.5, 11)
    paint_part(L, skull, shade_fn(lambda x, y: sphere_normal(x, y, 26, 15, 12, 12), SKIN, STH))
    hairL, _ = curls_layer(HAIR_CURLS, ramp='khhHr', th=[0.3, 0.6, 0.86, 0.975])
    composite(L, hairL)
    block(L, 16, 12, FACE)
    block(L, 16, 7, BAND)
    return L

# ------------------------------------------------------------------ headband tails
def ribbon(L, pts, r=1.6, ramp='yT'):
    m = polyline_mask(pts, r)
    def f(x, y):
        best = None
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            d, (vx, vy) = seg_dist(x + .5, y + .5, ax, ay, bx, by)
            if best is None or d < best[0]:
                best = (d, vx, vy)
        d, vx, vy = best
        return ramp[1] if (vy < 0.2 and vx < 0.8) else ramp[0]
    paint_part(L, m, f)
    return m

def build_tails():
    L = layer()
    ribbon(L, [(41, 12), (43.5, 16), (45, 20), (46.5, 24)], r=1.7, ramp='Yy')
    ribbon(L, [(42, 10), (46, 12.5), (49.5, 15.5), (52, 19), (55, 21.5), (58, 21.5)], r=1.8, ramp='yT')
    return L

def build_base_layers():
    return dict(tails=build_tails(), far=build_arm(G['far_arm']), legs=build_legs(), torso=build_torso(),
                near=build_arm(G['near_arm']), head=build_head())

ORDER = ('tails', 'legs', 'torso', 'far', 'near', 'head')

if __name__ == '__main__':
    Ls = build_base_layers()
    cv = compose([Ls[k] for k in ORDER])
    open('out/base.txt', 'w').write(to_text(cv))
    write_png('out/base_wip.png', 64, 64, to_rgba(cv))
    preview(cv, 'out/base_8x.png')
    print('ok')

# ------------------------------------------------------------------ polygon-traced arms (v2)
def arm_poly(poly, delt, up, E, Wr, a0, cuff_w=2.0, wrap_r=3.6, jacket_th=None):
    """poly: hand-traced silhouette (sleeve+forearm, no fist).  delt=(cx,cy,r) up=(ax,ay,bx,by,r0,r1)
    E/Wr: forearm axis (elbow -> wrist).  a0: along-axis distance where the sleeve ends."""
    L = layer()
    m = poly_mask(poly)
    ex, ey = E; wx, wy = Wr
    flen = math.hypot(wx - ex, wy - ey)
    ux, uy = (wx - ex) / flen, (wy - ey) / flen
    def ap(x, y):
        px, py = x + .5 - ex, y + .5 - ey
        return px * ux + py * uy, -px * uy + py * ux
    dcx, dcy, dr = delt
    def jn(x, y):
        du = seg_dist(x + .5, y + .5, up[0], up[1], up[2], up[3])[0] / up[4]
        dd = math.hypot(x + .5 - dcx, y + .5 - dcy) / dr
        if dd < du:
            return sphere_normal(x, y, dcx, dcy, dr, dr)
        return tcapsule_normal(x, y, *up)
    jshade = shade_fn(jn, JACKET, jacket_th or [0.25, 0.5, 0.78, 0.94], wrap=0.3)
    def is_fore(x, y):
        al, pe = ap(x, y)
        d_up = seg_dist(x + .5, y + .5, up[0], up[1], up[2], up[3])[0]
        d_fo = seg_dist(x + .5, y + .5, ex, ey, wx, wy)[0]
        return al >= a0 and d_fo <= d_up + 0.6
    def f(x, y):
        al, pe = ap(x, y)
        if not is_fore(x, y):
            return jshade(x, y)
        n = capsule_normal(x, y, ex, ey, wx, wy, wrap_r)
        v = lambert(n)
        if al < a0 + cuff_w:
            return 'i' if v > 0.75 else ('j' if v > 0.45 else 'J')
        if int(math.floor(al - a0 - cuff_w + pe * 0.9 + 100)) % 3 == 2:
            return 'w' if v > 0.55 else 'v'
        return 'W' if v > 0.62 else ('w' if v > 0.3 else 'v')
    paint_part(L, m, f)
    # seam lines at both cuff edges (only inside the silhouette, not on the outline)
    for y in range(H):
        for x in range(W):
            if m[y][x] and L[y][x] != '#':
                al, pe = ap(x, y)
                if is_fore(x, y) and a0 + cuff_w - 0.5 <= al < a0 + cuff_w + 0.5:
                    L[y][x] = '#'
    return L, m

NEAR_ARM_POLY = [(45, 26), (50, 26), (54, 28), (58, 32), (61, 36), (61, 39), (58, 42), (55, 45), (53, 46),
                 (50, 43), (53, 40), (53, 39), (50, 37), (47, 35), (44, 33), (43, 30)]
FAR_ARM_POLY = [(9, 27), (13, 27), (15, 30), (15, 34), (13, 38), (11, 41), (10, 45), (10, 48), (5, 48),
                (4, 45), (4, 41), (5, 37), (5, 33), (6, 29)]
