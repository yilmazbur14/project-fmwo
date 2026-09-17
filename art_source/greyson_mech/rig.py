"""Pose-driven renderer for the Greyson Mech sheet. Default pose == approved sprite."""
import copy, math
import build as B
from build import (W, H, BLACK, hexc, poly_mask, ell_mask, rot_ell_mask, rot_rect, mirror_mask,
                   sym_poly, render_part, recolor_region, bottom_band, ring_mask, stamp, TH_METAL, TH_SOFT)

for k, v in {'1': 'fff0a0', '2': 'ffb040', '3': 'e06020', '4': '902010',
             '5': 'f6f7f9', '6': 'd4d8de', '7': '9a9ea8', '8': '6a6e78', '9': '44474f',
             '0': 'ffffff'}.items():
    B.PALC[k] = hexc(v)
PALC = B.PALC
canvas = B.canvas

# ------------------------------------------------------------------ grids
FACE_BASE = [
    "......kkkkkkkkkk......",
    "....kkZZZZZZZZZZkk....",
    "...kZYyyyyyyyyyyYZk...",
    "..kZylHHllyyyyyyyYZk..",
    ".kZylHllyyyyyyyyyyYZk.",
    "kZyllyyyyykkyyyyyyyYZk",
    "kZylyyyyykSSkyyyyyYYZk",
    "kZyyyyyykSTTskyyyYYZZk",
    "kZyyyyYkSTTTTckYyYYZZk",
    "kZyYkZZSsssscccZZkYZZk",   # 9 brows
    "kZYkskkZZssccZZkkckZZk",   # 10 brows/lids
    ".ksssWBBksscckBBWcbbk.",   # 11 eyes
    ".ksssckksssccckkccbbk.",   # 12 lower lids
    ".kSssssssscbccccccbbk.",
    ".kssssssskcbkccccbbbk.",
    ".ksscYllyyyyyyYYYcbbk.",   # 15 mustache
    ".kscYlykkkkkkkkyYZbbk.",   # 16 mouth top
    ".kccYlkWWWWiiijkYZbak.",   # 17 teeth
    ".kcbYykMMMXXMMMkZZbak.",   # 18 mouth
    "..kcYZZkkkkkkkkZZZak..",   # 19
    "...kZbccccccbbbbbZk...",   # 20 chin
]

def face_rows(variant):
    f = list(FACE_BASE)
    if variant in ('grit', 'grimace'):
        f[18] = ".kcbYy" + "k" + "iWiWjijj" + "k" + "ZZbak."
    if variant == 'grimace':
        f[9] = "kZyYk" + "sssssssccccc" + "kYZZk"
        f[10] = "kZYk" + "sZZZZsccZZZZcc" + "kZZk"
        f[11] = ".ksss" + "kkkk" + "sscc" + "kkkk" + "cbbk."
        f[12] = ".ksssksssssccccckcbbk."
    if variant in ('winded', 'winded2', 'dazed'):
        f[9] = "kZyYk" + "ZZZssscccZZZ" + "kYZZk"
        f[10] = "kZYk" + "s" + "kkkk" + "sccc" + "kkkk" + "c" + "kZZk"
        f[11] = ".ksss" + "iAAi" + "sscc" + "iAAi" + "cbbk."
    if variant in ('winded', 'dazed'):
        f[16] = ".kscYly" + "y" + "kkkkkk" + "y" + "yYZbbk."
        f[17] = ".kccYl" + "y" + "k" + "MMMMMM" + "k" + "y" + "YZbak."
        f[18] = ".kcbYy" + "y" + "k" + "MMXXMM" + "k" + "y" + "ZZbak."
        f[19] = "..kcYZZ" + "Z" + "kkkkkk" + "Z" + "ZZZak.."
    if variant == 'winded2':
        f[16] = ".kscYly" + "y" + "kkkkkk" + "y" + "yYZbbk."
        f[17] = ".kccYl" + "y" + "k" + "MMMMMM" + "k" + "y" + "YZbak."
        f[18] = ".kcbYy" + "y" + "k" + "MXXXXM" + "k" + "y" + "ZZbak."
        f[19] = "..kcYZZ" + "Z" + "kkXXkk" + "Z" + "ZZZak.."
        f[20] = "...kZbccc" + "kXXk" + "bbbbZk..."
    if variant == 'ko':
        f[9] = "kZyYk" + "sssssssccccc" + "kYZZk"
        f[10] = "kZYk" + "s" + "ksk" + "sscccc" + "kck" + "c" + "kZZk"
        f[11] = ".ksss" + "sks" + "sscccc" + "ckc" + "cbbk."
        f[12] = ".ksss" + "ksk" + "sscccc" + "kck" + "cbbk."
        f[17] = ".kccYlkMMMMMMMMkYZbak."
        f[18] = ".kcbYykMMMXXMMMkZZbak."
        f[19] = "..kcYZZ" + "kkkXXkkk" + "ZZZak.."
        f[20] = "...kZbccc" + "kXXk" + "bbbbZk..."
    for i, r in enumerate(f):
        assert len(r) == 22, (variant, i, len(r), r)
    return f

CHEST_EYE = "kk....\nkkkk..\n.kPRk.\n.kRXk.\n.kXVk.\n.kkkk."
GRIN = """kkkkkkkkkkkkkkkkkkkk
kqkqqkqqkqqkqqkqqkqk
kVXRrrPPPPPPPPrrRXVk
.kVXRrrrrrrrrrrRXVk.
..kVXRRrrrrrrRRXVk..
...kkVXXRRRRXXVkk...
.....kkkkkkkkkk....."""
ANT = {
    0: ".....kkkk\n....kkPRk\n...kdkXXk\n..kdk.kk.\n.kdk.....\n.kek.....",
    -1: "...kkkk..\n..kkPRk..\n..kdXXk..\n..kdkk...\n.kdk.....\n.kek.....",
    1: "......kkkk\n.....kkPRk\n....kdkXXk\n..kkdk.kk.\n.kddk.....\n.kek......",
}
ROCKET = "..k..\n.kRk.\nkPRXk\nkRRXk\nkWWik\nkWWik\nkWiik\nkXXVk\nkWijk"
Y_EMB = "kkk....kkk\nkGFk..kFyk\n.kGFkkFyk.\n..kGFFyk..\n...kFyk...\n...kFyk...\n...kFyk...\n...kkkk..."
EMIT = """.kkkkkkkk
kRRXkfdek
krRRkddek
kPrRkdDek
kPrRkkkkk
kPrRkdDek
kPrRkkkkk
kPrRkdDek
krRRkdeek
kRRXkeffk
.kkkkkkkk"""
FIST = """..kkkkkkkkkk..
.kDdkDdkDdkdk.
kDddkdddkddkek
kdddkdddkdekek
kdddkddekeekfk
kkkkkkkkkkkkfk
kDDdddddeeekfk
kdddddddeeefgk
kkkkkkkkkkfggk
.kdddeeeeffggk
.keeeeefffgghk
..kfffffggghk.
...kkkkkkkkk.."""

def rot90_down(grid):
    """rotate a left-pointing grid so its left column ends up at the bottom."""
    rows = grid.split('\n')
    nr, nc = len(rows), len(rows[0])
    return '\n'.join(''.join(rows[nr - 1 - j][nc - 1 - i] for j in range(nr)) for i in range(nc))

def vflip(grid):
    return '\n'.join(reversed(grid.split('\n')))

EMIT_D = rot90_down(EMIT)

UP = {'V': 'X', 'X': 'R', 'R': 'r', 'r': 'P'}
DOWN = {'P': 'r', 'r': 'R', 'R': 'X', 'X': 'V'}
def gmap(level):
    if level == 1:
        return None
    if level == 0:
        return DOWN
    if level == 2:
        return UP
    if level == 3:
        return {'V': 'X', 'X': 'R', 'R': 'r', 'r': 'P', 'P': '0'}
    if level == 'off':
        return {'P': 'e', 'r': 'e', 'R': 'f', 'X': 'g', 'V': 'h'}
    if level == 'heat':
        return {'P': '1', 'r': '2', 'R': '3', 'X': '4', 'V': '4'}
    if level == 'heat2':
        return {'P': '1', 'r': '1', 'R': '2', 'X': '3', 'V': '4'}
    raise ValueError(level)

def st(grid, x, y, mirror=False, level=1):
    m = gmap(level)
    if m:
        grid = ''.join(m.get(c, c) for c in grid)
    stamp(grid, int(x), int(y), mirror)

def shiftm(m, dx, dy):
    dx, dy = int(dx), int(dy)
    out = [[False] * W for _ in range(H)]
    for y in range(H):
        yy = y - dy
        if 0 <= yy < H:
            row = m[yy]
            for x in range(W):
                xx = x - dx
                if 0 <= xx < W and row[xx]:
                    out[y][x] = True
    return out

def clear():
    for y in range(H):
        for x in range(W):
            canvas[y][x] = None
            B.owner[y][x] = None

def part(name, mL, ramp, R, th, sh, mirror=True, mR=None):
    """render left mask and its mirror (or explicit right mask)."""
    if mR is None and mirror:
        mR = mirror_mask(mL)
    if mR is not None:
        U = [[mL[y][x] or mR[y][x] for x in range(W)] for y in range(H)]
        render_part(name, U, ramp, R=R, th=th, shadow_below=sh)
    else:
        render_part(name, mL, ramp, R=R, th=th, shadow_below=sh)

def off_poly(pts, dx, dy):
    return [(x + dx, y + dy) for x, y in pts]

# ------------------------------------------------------------------ default pose
ARM0 = dict(uarm=(15, 43, 16, 11, 132), elbow=(9, 50, 5.5),
            barrel=('H', 9, 50), farm=(19, 55, 22, 14, 24), fist=(31, 61.5),
            fist_grid=FIST, muzzle=1, cuff=True)

def arm_from_joints(S, E, F, barrel_ang=0, muzzle=1, fist_grid=FIST, uw=11, fw=14):
    sx, sy = S; ex, ey = E; fx, fy = F
    ul = math.hypot(ex - sx, ey - sy)
    uang = math.degrees(math.atan2(ey - sy, ex - sx))
    ebx, eby = ex - 0.6, ey + 1.0
    dx, dy = fx - ebx, fy - eby
    dl = math.hypot(dx, dy)
    ux, uy = dx / dl, dy / dl
    wx, wy = fx - 2.4 * ux, fy - 2.4 * uy
    fl = math.hypot(wx - ebx, wy - eby)
    fang = math.degrees(math.atan2(wy - eby, wx - ebx))
    if barrel_ang is None:
        barrel = None
    elif barrel_ang == 0:
        barrel = ('H', round(ebx), round(eby))
    elif barrel_ang == 90:
        barrel = ('D', round(ebx), round(eby))
    else:
        barrel = ('P', ebx, eby, barrel_ang)
    return dict(uarm=((sx + ex) / 2, (sy + ey) / 2, ul, uw, uang), elbow=(ebx, eby, 5.5),
                barrel=barrel, farm=((ebx + wx) / 2, (eby + wy) / 2, fl, fw, fang),
                fist=(fx, fy), fist_grid=fist_grid, muzzle=muzzle, cuff=True)

DEFAULT = dict(
    body=(0, 0), head=(0, 0), pelvis=(0, 0), thigh=(0, 0), legs=(0, 0),
    face='shout', antenna=0, glow_chest=1, glow_ant=1,
    pod=(16, 18.5, -14), pod_off=(0, 0), rockets=[(8, 7), (13, 6), (18, 5)], pods_on=True,
    paul=(22, 32, -12), paul_off=(0, 0),
    armL=ARM0, armR=None,
    thigh_poly=[(33, 59), (46, 60), (46, 67), (43, 76), (29, 77), (27, 69), (29, 63)],
    knee=(35, 77, 7, 5), shin_poly=[(27, 79), (43, 79), (45, 84), (46, 90), (24, 90), (23, 84)],
    foot_poly=[(21, 89), (44, 88), (47, 90), (47, 96), (18, 96), (18, 92)],
    boot_seam=(28, 82), foot_seam=(26, 90),
    helmet_on=True, fx_back=[], fx=[], fx_mid=[], debris=[], hide=set(),
)

def pose(**kw):
    P = copy.deepcopy(DEFAULT)
    P.update(copy.deepcopy(kw))
    return P

# ------------------------------------------------------------------ arm rendering
def barrel_proc_mask(ox, oy, a, L=10.0, Wd=9.0):
    ar = math.radians(a)
    d = (-math.cos(ar), math.sin(ar))
    cx, cy = ox + d[0] * L / 2, oy + d[1] * L / 2
    return poly_mask(rot_rect(cx, cy, L, Wd, 180 - a, ch=1)), (cx, cy), d

def draw_barrel_proc(ox, oy, a, level, mirror):
    L, Wd = 10.0, 9.0
    m, (cx, cy), d = barrel_proc_mask(ox, oy, a, L, Wd)
    if mirror:
        m = mirror_mask(m)
    render_part('emit', m, 'dark', R=3, th=TH_METAL, shadow_below=0)
    n = (-d[1], d[0])
    gm = gmap(level) or {}
    for y in range(H):
        for x in range(W):
            if not m[y][x] or canvas[y][x] == BLACK:
                continue
            px = (95 - x) if mirror else x
            rx, ry = px + 0.5 - cx, y + 0.5 - cy
            u = rx * d[0] + ry * d[1]
            v = abs(rx * n[0] + ry * n[1])
            t = v / (Wd / 2)
            ch = None
            if u > L / 2 - 3.6:
                ch = 'P' if t < 0.34 else ('r' if t < 0.66 else 'R')
                ch = gm.get(ch, ch)
            elif u > L / 2 - 4.6:
                ch = 'k'
            elif -2.0 < u <= -0.9 and t < 0.6:
                ch = 'D'
            if ch:
                canvas[y][x] = PALC[ch]

def arm_masks(A, bx, by):
    ucx, ucy, ul, uw, ua = A['uarm']
    um = poly_mask(rot_rect(ucx + bx, ucy + by, ul, uw, ua))
    ex, ey, er = A['elbow']
    em = ell_mask(ex + bx, ey + by, er, er)
    fcx, fcy, fl, fw, fa = A['farm']
    fm = poly_mask(rot_rect(fcx + bx, fcy + by, fl, fw, fa, ch=3))
    return um, em, fm

def render(P):
    clear()
    bx, by = P['body']
    hx, hy = bx + P['head'][0], by + P['head'][1]
    px_, py_ = P['pelvis']
    tx, ty = P['thigh']
    lx, ly = P['legs']
    armL = P['armL']
    armR = P['armR'] or armL
    hide = P['hide']

    for fx in P['fx_back']:
        fx()

    # rockets + pods
    if P['pods_on'] and P.get('podR') is None and 'podL' not in hide and 'podR' not in hide:
        pcx, pcy, pang = P['pod']
        pox, poy = P['pod_off']
        ox, oy = bx + pox, by + poy
        for rk in P['rockets']:
            x0, y0 = rk[0], rk[1]
            g = rk[2] if len(rk) > 2 else ROCKET
            st(g, x0 + ox, y0 + oy)
            st(g, x0 + ox, y0 + oy, mirror=True)
        podm = poly_mask(rot_rect(pcx + ox, pcy + oy, 18, 11, pang, ch=1))
        part('pod', podm, 'dark', 3, TH_METAL, 0)
        pod_detail(podm, pcx + ox, pcy + oy, pang)
    elif P['pods_on']:
        pcx, pcy, pang = P['pod']
        pox, poy = P['pod_off']
        sides = []
        if 'podL' not in hide:
            sides.append((pcx, pcy, pang, bx + pox, by + poy, False, P['rockets']))
        if 'podR' not in hide:
            rc = P.get('podR') or (pcx, pcy, pang, pox, poy)
            rr = P.get('rocketsR')
            sides.append((rc[0], rc[1], rc[2], bx + rc[3], by + rc[4], True, P['rockets'] if rr is None else rr))
        for cx, cy, ang, ox, oy, mir, rks in sides:
            for rk in rks:
                g = rk[2] if len(rk) > 2 else ROCKET
                st(g, rk[0] + ox, rk[1] + oy, mirror=mir)
            m = poly_mask(rot_rect(cx + ox, cy + oy, 18, 11, ang, ch=1))
            if mir:
                m = mirror_mask(m)
            render_part('pod', m, 'dark', R=3, th=TH_METAL, shadow_below=0)
            pod_detail_one(m, cx + ox, cy + oy, ang, mir)

    if 'thigh' not in hide:
        part('thigh', poly_mask(off_poly(P['thigh_poly'], tx, ty)), 'metal', 6, TH_METAL, 0)
    torso = poly_mask(sym_poly([(48, 29), (40, 29), (34, 31), (30, 35), (28, 41), (29, 47), (33, 54), (38, 59), (48, 61)]))
    render_part('torso', shiftm(torso, bx, by), 'metal', R=8, th=TH_METAL, shadow_below=0)
    if 'chestplate' not in hide:
        render_part('chestplate', ell_mask(48 + bx, 48.5 + by, 13.5, 10.5), 'metal', R=7, th=TH_METAL, shadow_below=0)
    else:
        render_part('cavity', ell_mask(48 + bx, 48.5 + by, 11.5, 8.5), 'shoe', R=6, th=[9, 9, 0.95, 0.8, 0.6], shadow_below=0)
    if P['helmet_on']:
        part('bolt', poly_mask([(29 + hx, 17 + hy), (33 + hx, 16 + hy), (33 + hx, 24 + hy), (29 + hx, 23 + hy)]), 'dark', 2, TH_METAL, 0)
        render_part('helmet', ell_mask(48 + hx, 19.5 + hy, 16, 15), 'metal', R=9, th=TH_METAL, shadow_below=0)
    for fx in P.get('fx_head_back', []):
        fx()
    rows = face_rows(P['face'])
    st('\n'.join(rows[:12]), 37 + hx, 10 + hy)
    st('\n'.join(rows[12:]), 37 + hx, 22 + hy)
    for fx in P.get('fx_face', []):
        fx()
    collar = poly_mask(sym_poly([(48, 30), (39, 30), (35, 33), (36, 37), (41, 39), (48, 40)]))
    if 'collar' not in hide:
        render_part('collar', shiftm(collar, bx, by), 'dark', R=3, th=TH_METAL, shadow_below=2)
    else:
        st("...kkkkkkkkkkkkkkkk...", 37 + hx, 31 + hy)
    gc = P['glow_chest']
    if 'chestplate' not in hide:
        st(CHEST_EYE, 38 + bx, 40 + by, level=gc)
        st(CHEST_EYE, 38 + bx, 40 + by, mirror=True, level=gc)
        st(GRIN, 38 + bx, 47 + by, level=gc)
    if 'collar' not in hide:
        st("kD", 38 + bx, 33 + by); st("kD", 38 + bx, 33 + by, mirror=True)
    for fx in P['fx_mid']:
        fx()

    pel = poly_mask(sym_poly([(48, 56), (37, 56), (35, 60), (38, 66), (43, 70), (48, 71)]))
    render_part('pelvis', shiftm(pel, px_, py_), 'purple', R=5, th=TH_SOFT, shadow_below=2)
    st(Y_EMB, 43 + px_, 58 + py_)

    kx, ky, krx, kry = P['knee']
    part('knee', ell_mask(kx + lx, ky + ly, krx, kry), 'metal', 4, TH_METAL, 0)
    part('shin', poly_mask(off_poly(P['shin_poly'], lx, ly)), 'white', 6, TH_SOFT, 1)
    if P['boot_seam']:
        bsx, bsy = P['boot_seam']
        g = "......o...\n......o...\n......o..."
        st(g, bsx + lx, bsy + ly); st(g, bsx + lx, bsy + ly, mirror=True)
    part('foot', poly_mask(off_poly(P['foot_poly'], lx, ly)), 'shoe', 3, TH_SOFT, 1)
    if P['foot_seam']:
        fsx, fsy = P['foot_seam']
        g = ".......\n..k....\n..k....\n......."
        st(g, fsx + lx, fsy + ly); st(g, fsx + lx, fsy + ly, mirror=True)

    for fx in P.get('fx_legs', []):
        fx()

    # arms: masks (left coords), right mirrored
    mL = arm_masks(armL, bx, by)
    mR = [mirror_mask(m) for m in arm_masks(armR, bx, by)]
    if 'arms' not in hide:
        part('uarm', mL[0], 'dark', 5, TH_METAL, 0, mR=mR[0])
    # pauldrons
    if 'paul' not in hide and P.get('paulR') is None and 'paulL' not in hide and 'paulR' not in hide:
        pcx, pcy, pa = P['paul']
        pox, poy = P['paul_off']
        pm = rot_ell_mask(pcx + bx + pox, pcy + by + poy, 12.5, 9.5, pa)
        pmR = mirror_mask(pm)
        render_part('paul', [[pm[y][x] or pmR[y][x] for x in range(W)] for y in range(H)], 'metal', R=8, th=TH_METAL, shadow_below=2)
        for m in (pm, pmR):
            band, line = bottom_band(m, 3)
            recolor_region(band, 'purple', R=2, line_mask=line)
        for x, y in [(13, 37), (25, 38)]:
            st("Uk", x + bx + pox, y + by + poy); st("Uk", x + bx + pox, y + by + poy, mirror=True)
    elif 'paul' not in hide:
        pcx, pcy, pa = P['paul']
        pox, poy = P['paul_off']
        sides = []
        if 'paulL' not in hide:
            sides.append((pcx, pcy, pa, pox, poy, False))
        if 'paulR' not in hide:
            rc = P.get('paulR') or (pcx, pcy, pa, pox, poy)
            sides.append((rc[0], rc[1], rc[2], rc[3], rc[4], True))
        for cx, cy, ang, ox, oy, mir in sides:
            draw_pauldron(cx + bx + ox, cy + by + oy, ang, mir)
    if 'arms' not in hide:
        # barrel masks (H style needs underlying mask like approved)
        bm = []
        for A in (armL, armR):
            b = A['barrel']
            if b and b[0] == 'H':
                bm.append(poly_mask(rot_rect(b[1] - 4.5 + bx, b[2] - 0.5 + by, 9, 11, 0, ch=1)))
            else:
                bm.append(None)
        if bm[0] is not None or bm[1] is not None:
            e = [[False] * W for _ in range(H)]
            part('emit', bm[0] or e, 'dark', 3, TH_METAL, 0, mR=mirror_mask(bm[1]) if bm[1] else e)
        part('elbow', mL[1], 'dark', 4, TH_METAL, 0, mR=mR[1])
        part('farm', mL[2], 'metal', 7, TH_METAL, 2, mR=mR[2])
        for A, mirror, fm in ((armL, False, mL[2]), (armR, True, mR[2])):
            if A.get('cuff'):
                fx_, fy_ = A['fist']
                cx = fx_ + bx
                if mirror:
                    cx = 96 - cx
                cl = ring_mask(fm, cx, fy_ + by, 9.0, 10.0)
                cu = ring_mask(fm, cx, fy_ + by, 10.0, 13.0)
                recolor_region(cu, 'purple', R=2, line_mask=cl)
        for fx in P.get('fx_prefist', []):
            fx()
        for A, mirror in ((armL, False), (armR, True)):
            fx_, fy_ = A['fist']
            st(A['fist_grid'], round(fx_ - 7 + bx), round(fy_ - 6.5 + by), mirror=mirror)
    for fx in P['debris']:
        fx()
    if P['helmet_on']:
        st(ANT[P['antenna']], 47 + hx, 0 + hy + max(0, -hy), level=P['glow_ant'])
    if 'arms' not in hide:
        for A, mirror in ((armL, False), (armR, True)):
            b = A['barrel']
            if not b:
                continue
            if b[0] == 'H':
                st(EMIT, b[1] - 9 + bx, b[2] - 6 + by, mirror=mirror, level=A['muzzle'])
            elif b[0] == 'D':
                st(EMIT_D, b[1] - 6 + bx, b[2] - 1 + by, mirror=mirror, level=A['muzzle'])
            elif b[0] == 'P':
                draw_barrel_proc(b[1] + bx, b[2] + by, b[3], A['muzzle'], mirror)
    for fx in P['fx']:
        fx()
    return [[(canvas[y][x] if canvas[y][x] is not None else (0, 0, 0, 0)) for x in range(W)] for y in range(H)]

def pod_detail(msk_left, cx, cy, ang):
    a = math.radians(ang)
    for msk, ccx in ((msk_left, cx), (mirror_mask(msk_left), 96 - cx)):
        sgn = 1 if ccx < 48 else -1
        band = [[False] * W for _ in range(H)]
        seam = [[False] * W for _ in range(H)]
        rim = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                if not msk[y][x]:
                    continue
                dx, dy = (x + 0.5 - ccx) * sgn, y + 0.5 - cy
                v = -dx * math.sin(a) + dy * math.cos(a)
                if v > 0.2:
                    band[y][x] = True
                elif v > -0.8:
                    seam[y][x] = True
                if y >= 2 and msk[y - 1][x] and not msk[y - 2][x]:
                    rim[y][x] = True
        recolor_region(band, 'purple', R=2, line_mask=seam)
        for y in range(H):
            for x in range(W):
                if rim[y][x] and canvas[y][x] != BLACK:
                    canvas[y][x] = PALC['h']


def draw_pauldron(cx, cy, ang, mirror=False, rivets=True):
    pm = rot_ell_mask(cx, cy, 12.5, 9.5, ang)
    if mirror:
        pm = mirror_mask(pm)
    render_part('paul', pm, 'metal', R=8, th=TH_METAL, shadow_below=2)
    band, line = bottom_band(pm, 3)
    recolor_region(band, 'purple', R=2, line_mask=line)

def pod_detail_one(msk, cx, cy, ang, mirror):
    a = math.radians(ang)
    ccx = (96 - cx) if mirror else cx
    sgn = -1 if mirror else 1
    band = [[False] * W for _ in range(H)]
    seam = [[False] * W for _ in range(H)]
    rim = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if not msk[y][x]:
                continue
            dx, dy = (x + 0.5 - ccx) * sgn, y + 0.5 - cy
            v = -dx * math.sin(a) + dy * math.cos(a)
            if v > 0.2:
                band[y][x] = True
            elif v > -0.8:
                seam[y][x] = True
            if y >= 2 and msk[y - 1][x] and not msk[y - 2][x]:
                rim[y][x] = True
    recolor_region(band, 'purple', R=2, line_mask=seam)
    for y in range(H):
        for x in range(W):
            if rim[y][x] and canvas[y][x] != BLACK:
                canvas[y][x] = PALC['h']
