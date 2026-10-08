"""Take B, SOUL TORRENT: the beam as a torrent of screaming souls in bone-white ghost fire, wrapped in
black smoke, led by a howling skull. Every colour but white is off the puppets' own sheets: their
cool ash ramp (#17111D #2C2434 #4A4356 #6E6A80 #9893A5), their warm bone (#CFC6B2 #F1EAD4) and their
red for the eyes (#D2403A #9F1C2E #661127).

The sheets have the same sizes, frame counts and pivots as take A's (see mb_body, mb_head,
mb_bursts, mb_diss, mb_charge), so either take drops into the same code.
"""
import math

import numpy as np

import mb_core as C
import mb_body as B
import mb_head as HD
import mb_bursts as X
import mb_diss as D
import mb_charge as Q

W, H, CY, FLOW, FRAMES = B.W, B.H, B.CY, B.FLOW, B.FRAMES


# ----------------------------------------------------------------------------------------------- faces

# A screaming soul, 11 x 11, facing the viewer: '#' skull, 'k' holes (eyes, nose, mouth), '.' clear.
# Two mouths: shut-ish and wide open; the eyes hold a red pinpoint on some frames.
SOUL_SHUT = [
    "...#####...",
    "..#######..",
    ".#########.",
    ".##kk#kk##.",
    ".##kk#kk##.",
    ".####k####.",
    "..##kkk##..",
    "..##kkk##..",
    "...#####...",
    "....###....",
    "...........",
]
SOUL_OPEN = [
    "...#####...",
    "..#######..",
    ".#########.",
    ".##kk#kk##.",
    ".##kk#kk##.",
    "..###k###..",
    "..#kkkkk#..",
    "..#kkkkk#..",
    "..#kkkkk#..",
    "...#kkk#...",
    "....###....",
]

SOUL_BIG_SHUT = [
    "....#####....",
    "..#########..",
    ".###########.",
    "#############",
    "##kkk###kkk##",
    "##kkk###kkk##",
    "##kk##k##kk##",
    ".#####k#####.",
    "..###kkk###..",
    "..##kkkkk##..",
    "...##kkk##...",
    "....#####....",
]
SOUL_BIG_OPEN = [
    "....#####....",
    "..#########..",
    ".###########.",
    "#############",
    "##kkk###kkk##",
    "##kkk###kkk##",
    "##kk##k##kk##",
    ".#####k#####.",
    "..##kkkkk##..",
    "..#kkkkkkk#..",
    "..#kkkkkkk#..",
    "...#kkkkk#...",
    "....##k##....",
    ".....###.....",
]
SOUL_SMALL_SHUT = [
    "..#####..",
    ".#######.",
    "#kk###kk#",
    "#kk###kk#",
    "####k####",
    ".##kkk##.",
    ".##kkk##.",
    "..#####..",
]
SOUL_SMALL_OPEN = [
    "..#####..",
    ".#######.",
    "#kk###kk#",
    "#kk###kk#",
    ".###k###.",
    ".##kkk##.",
    ".#kkkkk#.",
    ".#kkkkk#.",
    "..#kkk#..",
    "...###...",
]
SOULS = {'mid': (SOUL_SHUT, SOUL_OPEN, (3, 6), 4), 'big': (SOUL_BIG_SHUT, SOUL_BIG_OPEN, (3, 9), 5),
         'small': (SOUL_SMALL_SHUT, SOUL_SMALL_OPEN, (1, 7), 2)}


def _stamp_soul(g, pal, x0, y0, open_mouth, red_eyes, flip_v=False, kind='mid'):
    shut, opened, eyes_x, eye_y = SOULS[kind]
    art = opened if open_mouth else shut
    if flip_v:
        art = art[::-1]
    hh, ww = len(art), len(art[0])
    for j in range(hh):
        for i in range(ww):
            ch = art[j][i]
            if ch == '.':
                continue
            x = (x0 + i) % W
            y = y0 + j
            if not 0 <= y < H:
                continue
            if ch == '#':
                # bone, lit from its top-left, shadowed low and at the edges
                edge = (j == 0 or i in (0, ww - 1) or art[j - 1][i] == '.' or art[j][i - 1] == '.'
                        or (i + 1 < ww and art[j][i + 1] == '.') or (j + 1 < hh and art[j + 1][i] == '.'))
                if edge:
                    g[y, x] = pal['l']
                elif j <= 2:
                    g[y, x] = pal['w']
                elif j <= 5:
                    g[y, x] = pal['e']
                else:
                    g[y, x] = pal['b']
            else:
                g[y, x] = pal['k']
    if red_eyes:
        for ex in eyes_x:
            ey = eye_y if not flip_v else hh - 1 - eye_y
            if 0 <= y0 + ey < H:
                g[y0 + ey, (x0 + ex) % W] = pal['r']


# ----------------------------------------------------------------------------------------------- body

def _profile_b(pal, f, variant):
    s = FLOW * f
    v = variant * 100

    def flow(seed, harmonics, amp):
        return np.roll(B._smooth(seed + 500 + v, harmonics, amp), s)

    fl = C.rng('bodyB-flicker-%d-%d' % (variant, f))
    sides = {}
    for side, o in (('t', 0), ('b', 10)):
        core = 2.4 + flow(1 + o, (2, 3, 5), 0.7)
        bone = core + 2.6 + flow(2 + o, (3, 4, 7), 1.5)
        tongue = np.roll(B._sawtooth('B%s%d' % (side, variant), 6, 15, 2.5, 7.0), s)
        tongue = tongue + fl.integers(-1, 2, W) * 0.6 * (tongue > 1.5)
        pale = bone + 1.2 + 0.55 * tongue
        tips = pale + 0.9 + 0.35 * tongue
        sides[side] = (core, bone, pale, tips)
    g = C.blank(W, H)
    for x in range(W):
        for y in range(H):
            d = CY - (y + 0.5)
            core, bone, pale, tips = sides['t' if d > 0 else 'b']
            ad = abs(d)
            if ad <= core[x]:
                k = 'w'
            elif ad <= core[x] + 1.0:
                k = 'e'
            elif ad <= bone[x]:
                k = 'b'
            elif ad <= pale[x]:
                k = 'l'
            elif ad <= tips[x]:
                k = 'g'
            else:
                continue
            g[y, x] = pal[k]
    return g


def body_b(pal, f, variant=0):
    """Take B, Soul Torrent: bone-white ghost fire streaming towards the player, its tongues torn
    back, wrapped in black smoke, and screaming souls bulging up through it, eyes flaring red."""
    s = FLOW * f
    g = _profile_b(pal, f, variant)
    # flowing wisps: pale streaks through the bone, ash ones through the grey
    sr = C.rng('bodyB-streaks-%d' % variant)
    for k in range(28):
        x0 = int(sr.integers(0, W))
        up = k % 2 == 0
        off = float(sr.uniform(2.5, 10.5))
        y = int(math.floor(CY - off)) if up else int(math.floor(CY + off))
        length = int(sr.integers(4, 14))
        for i in range(length):
            x = (x0 + s + i) % W
            here = g[y, x]
            if here == pal['b']:
                g[y, x] = pal['e'] if k % 3 else pal['l']
            elif here == pal['l']:
                g[y, x] = pal['b'] if k % 3 == 1 else pal['g']
            elif here == pal['g']:
                g[y, x] = pal['a']
    # black smoke coiling round the outside, rimmed ash-grey so it reads on the dark
    smoke = np.roll(C.fbm_periodic(W, H, [(16, 4, 1.0), (8, 2, 0.5)], 1501 + variant), s // 2, axis=1)
    ys = np.arange(H)[:, None] + 0.5
    ady = np.abs(ys - CY)
    body = g > 0
    puff = (~body) & (ady < 15.5) & (smoke > 0.15)
    g[puff] = pal['k']
    rim = puff & ~C.dilate_wrap(~(puff | body), 1)
    edge = puff & C.dilate_wrap(~(puff | body), 1)
    g[edge] = pal['u']
    # the souls: three a tile, big, small and middling, riding the flow at different heights, each
    # trailing a ghost tail; they scream and their eyes flare out of step
    yy, xx = np.mgrid[0:H, 0:W]
    for k, (x_at, y_top, kind) in enumerate(((4, 9, 'big'), (40, 15, 'small'), (66, 10, 'mid'))):
        shut, opened, _, _ = SOULS[kind]
        hh, ww = len(shut), len(shut[0])
        x0 = (x_at + s) % W
        cx, cy = x0 + ww / 2.0, y_top + hh / 2.0
        dxw = ((xx + 0.5 - cx) + W / 2) % W - W / 2
        tail = (dxw < -1) & (dxw > -(14 + ww)) & (np.abs(yy + 0.5 - cy) < (hh / 2.0) * (1 + dxw / (14.0 + ww)) + 0.5)
        tail_core = tail & (np.abs(yy + 0.5 - cy) < (hh / 4.0) * (1 + dxw / (14.0 + ww)) + 0.5)
        g[tail & ~np.isin(g, [pal['w'], pal['e']])] = pal['l']
        g[tail_core & ~np.isin(g, [pal['w']])] = pal['e']
        _stamp_soul(g, pal, x0, y_top, open_mouth=(f + k) % 2 == 0, red_eyes=(f + 3 * k) % 4 < 2, kind=kind)
    # embers of bone-fire flying off and dying
    er = C.rng('bodyB-embers-%d' % variant)
    for e in range(12):
        born = int(er.integers(0, FRAMES))
        life = int(er.integers(3, 5))
        age = (f - born) % FRAMES
        if age >= life:
            continue
        up = e % 2 == 0
        x = (int(er.integers(0, W)) + FLOW * born + (FLOW - 5) * age) % W
        y = int(round((CY - 12 if up else CY + 12) + (-1 if up else 1) * (0.5 + 1.2 * age)))
        if 0 <= y < H and g[y, x] == 0:
            g[y, x] = pal[['w', 'e', 'b', 'l'][min(age, 3)]]
    return g


def glow_b(gpal, f, variant=0):
    s = FLOW * f
    n = np.roll(C.fbm_periodic(W, B.GH, [(24, 6, 1.0), (12, 3, 0.5)], 1591 + variant), s, axis=1)
    ys = np.arange(B.GH)[:, None] + 0.5
    ady = np.abs(ys - B.GH / 2.0)
    I = 1.0 - ady / 23.0 + 0.10 * n + 0.03 * math.sin(f * math.pi / 2)
    g = C.blank(W, B.GH)
    g[I > 0.18] = gpal['1']
    g[I > 0.38] = gpal['2']
    g[I > 0.55] = gpal['3']
    return g


# ----------------------------------------------------------------------------------------------- head

HW, HH, HCY = HD.HW, HD.HH, HD.HCY

# The skull in profile, facing right, in its own texels (origin top-left of a 31 x 31 box).
CRANIUM = [(3, 12), (2.2, 8), (4, 4.2), (8, 1.6), (14, 0.6), (20, 1.3), (24.2, 3.6), (26.8, 7.0),
           (28.0, 10.0), (27.2, 12.2), (28.8, 15.0), (30.0, 18.2), (30.0, 20.8), (21, 21.2), (16.5, 20.4),
           (12.5, 19.8), (7.5, 17.4), (4.2, 15.2)]
MANDIBLE = [(12.8, 18.8), (12.6, 24.2), (15.5, 26.2), (28.5, 26.4), (29.2, 22.8), (18.5, 22.6),
            (15.8, 20.2)]
HINGE = (13.2, 19.2)
EYE = (21.6, 12.4, 4.4, 3.8)
NOSE = [(26.8, 15.2), (28.6, 17.6), (26.2, 18.4)]


def _rot(pts, about, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    ax, ay = about
    return [(ax + (x - ax) * ca - (y - ay) * sa, ay + (x - ax) * sa + (y - ay) * ca) for x, y in pts]


def _shade_bone(g, pal, mask, lx, ly):
    """Bone shading on a mask: by distance to its edge and by a light from (lx, ly) (unit)."""
    inner1 = mask & ~C.dilate(~mask, 1)
    inner2 = mask & ~C.dilate(~mask, 2)
    inner3 = mask & ~C.dilate(~mask, 3)
    ys, xs = np.nonzero(mask)
    cy, cx = ys.mean(), xs.mean()
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    lit = ((xx - cx) * lx + (yy - cy) * ly) / max(1.0, (mask.sum() ** 0.5))
    g[mask] = pal['b']
    g[inner2 & (lit > -0.05)] = pal['e']
    g[inner3 & (lit > 0.18)] = pal['w']
    g[mask & (lit < -0.28)] = pal['l']
    g[mask & (lit < -0.55)] = pal['g']
    g[mask & ~inner1] = pal['u']


def head_b(pal, f, variant=0):
    """Take B, Soul Torrent: a howling skull, jaw flung open, a red ember in its socket, pale ghost
    fire pouring back off its crown into the torrent, black smoke curling off the fire."""
    g = C.blank(HW, HH)
    r = C.rng('headB-%d-%d' % (variant, f))
    ys, xs = np.mgrid[0:HH, 0:HW]
    px, py = xs + 0.5, ys + 0.5
    ox, oy = 31.0, 7.0                              # the skull box's top-left in the frame
    # ghost fire behind and above the skull, trailing back into the line
    fire_c = (ox + 12.0, oy + 12.0)
    streak = np.roll(C.fbm_periodic(HW, HH, [(16, 3, 1.0), (8, 2, 0.5)], 1701 + variant, period_x=HW), 6 * f, axis=1)
    back = np.clip((fire_c[0] - px) / fire_c[0], 0, 1)
    half = 15.0 * (1 - back) ** 0.8 + 1.0
    I = (1.0 - np.abs(py - (HCY - 2.0 * (1 - back))) / half) * (1 - back) ** 0.45 + 0.18 * streak
    blob = 1.0 - np.hypot((px - fire_c[0]) / 17.0, (py - fire_c[1]) / 15.0)
    I = np.maximum(I, blob + 0.15 * streak)
    I[px > ox + 30] = -1
    for t, k in ((0.0, 'u'), (0.1, 'a'), (0.22, 'g'), (0.38, 'l'), (0.55, 'b'), (0.72, 'e')):
        g[I > t] = pal[k]
    # black smoke curling off the fire's edge
    sm = np.roll(C.fbm_periodic(HW, HH, [(16, 6, 1.0), (8, 3, 0.5)], 1733 + variant, period_x=HW), 4 * f, axis=1)
    puff = (g == 0) & (sm > 0.2) & (np.hypot((px - 26) / 26.0, (py - HCY) / 17.0) < 1.0)
    g[puff] = pal['k']
    g[puff & C.dilate(~puff & (g == 0), 1)] = pal['u']
    # the skull
    jaw = [0.42, 0.52, 0.62, 0.55, 0.45, 0.36][f % 6]
    cran = C.polygon_mask(HW, HH, [(ox + x, oy + y) for x, y in CRANIUM])
    mand_pts = _rot(MANDIBLE, HINGE, jaw)
    mand = C.polygon_mask(HW, HH, [(ox + x, oy + y) for x, y in mand_pts])
    # the dark of the mouth between the jaws
    tip_up = (ox + 30.0, oy + 21.0)
    tip_dn = (ox + mand_pts[4][0], oy + mand_pts[4][1])
    mouth = C.polygon_mask(HW, HH, [(ox + 16.0, oy + 20.6), tip_up, (tip_up[0] + 1.0, tip_up[1] + 2.0),
                                    (tip_dn[0] + 1.0, tip_dn[1]), (ox + mand_pts[5][0], oy + mand_pts[5][1])])
    g[mouth] = pal['k']
    g[mouth & C.dilate(~mouth, 1) & (px < ox + 22)] = pal['d']
    _shade_bone(g, pal, mand, 0.5, -0.85)
    _shade_bone(g, pal, cran, 0.55, -0.83)
    # the socket, burning red from deep inside
    ex, ey, erx, ery = EYE
    sock = C.disc_mask(HW, HH, ox + ex, oy + ey, erx, ery)
    g[sock] = pal['k']
    g[sock & ~C.dilate(~sock, 1) & (py > oy + ey)] = pal['u']
    # the brow ridge overhanging it
    for x in range(int(ox + ex - erx), int(ox + ex + erx + 1)):
        y = int(oy + ey - ery - 0.6)
        if cran[y, x] and not sock[y, x]:
            g[y, x] = pal['l']
    glint = [(0, 0), (0, 0), (1, 0), (0, 0), (0, 0), (-1, 0)][f % 6]
    gx, gy = int(ox + ex + 1.0 + glint[0]), int(oy + ey)
    for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
        if sock[gy + ddy, gx + ddx]:
            g[gy + ddy, gx + ddx] = pal['c']
    g[gy, gx] = pal['r']
    g[gy, gx + 1] = pal['r']
    if f % 3 != 2:
        g[gy - 1, gx] = pal['r']
    # a crack across the crown: undead bone
    crack = [(ox + 10, oy + 2), (ox + 12, oy + 5), (ox + 11, oy + 7), (ox + 14, oy + 9), (ox + 13, oy + 11)]
    for (xa, ya), (xb, yb) in zip(crack, crack[1:]):
        for cx_, cy_ in C.line_points(xa, ya, xb, yb):
            if 0 <= cy_ < HH and cran[cy_, cx_]:
                g[cy_, cx_] = pal['g']
    # the nose, the cheekbone's shadow and the temple
    g[C.polygon_mask(HW, HH, [(ox + x, oy + y) for x, y in NOSE])] = pal['k']
    for x in range(int(ox + 14), int(ox + 21)):
        y = int(oy + 17.2 + (x - ox - 14) * 0.08)
        if cran[y, x]:
            g[y, x] = pal['l']
    # teeth: the upper row hanging off the jaw, the lower row standing on the mandible
    for tx in range(int(ox + 21), int(ox + 30), 2):
        for ty in (int(oy + 21.2), int(oy + 22.2)):
            if mouth[ty, tx] or cran[ty, tx]:
                g[ty, tx] = pal['e'] if ty == int(oy + 21.2) else pal['b']
    lo = _rot([(x, 22.6) for x in range(19, 29, 2)], HINGE, jaw)
    for tx, ty in lo:
        X_, Y_ = int(ox + tx), int(oy + ty) - 1
        if 0 <= Y_ < HH and 0 <= X_ < HW:
            g[Y_, X_] = pal['e']
            if Y_ - 1 >= 0 and mouth[Y_ - 1, X_]:
                g[Y_ - 1, X_] = pal['b']
    # speed wisps streaming off the back of the skull
    for k in range(10):
        y = int(HCY + r.normal(-2, 7))
        if not 0 <= y < HH:
            continue
        x1 = int(r.integers(18, 34))
        for i in range(int(r.integers(6, 18))):
            x = x1 - i
            if x < 0:
                break
            if g[y, x] in (0, pal['u'], pal['a'], pal['k']):
                g[y, x] = pal['g'] if i > 8 else pal['l']
    return g


def head_glow_b(gpal, f):
    g = C.blank(HW, HH)
    ys, xs = np.mgrid[0:HH, 0:HW]
    d = np.sqrt(((xs + 0.5 - 45) / 23.0) ** 2 + ((ys + 0.5 - HCY + 2) / 21.0) ** 2)
    tail = (xs + 0.5 < 45) & (np.abs(ys + 0.5 - HCY) < 14 * (xs + 0.5) / 45.0)
    pulse = 0.05 * math.sin(f * math.pi / 3)
    g[(d < 1.0 + pulse) | tail] = gpal['1']
    g[(d < 0.72 + pulse)] = gpal['2']
    g[(d < 0.45 + pulse)] = gpal['3']
    return g
