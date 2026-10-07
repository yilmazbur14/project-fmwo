"""The ten key poses of Liam's elements phase (a-h from the first brief, i-j for attack 2).

Each pose function returns (canvas, meta). meta: name, where ('perch' = shown standing on the pillar,
so it keeps inside le_poses.PERCH_BOX; 'ground' = the cutscene and the downed window), and anchors in
frame coordinates (orb centre, impact point, mouth) for FX placement.
"""
import math

import numpy as np

import le_rig as R
import le_staff as S
from le_poses import (FW, FH, BODY, P, layer, place, body, arm, blkb, staff_line, legs_narrow,
                      head_variant, fist_at, FIST)

# ------------------------------------------------------------------ extra hands
OPEN_PALM = [  # palm out to the viewer, fingers up, thumb on the left (9 x 10)
    "..#.#.#..",
    ".#a#s#s#.",
    ".#a#s#s##",
    "#as#s#sd#",
    "#asssssd#",
    "#asssssd#",
    "#sssssdf#",
    ".#sssdf#.",
    ".#ddfff#.",
    "..#####..",
]
BACKHAND = [  # back of the hand raised to the mouth, fingers together pointing right (9 x 8)
    "...#####.",
    "..#aasss#",
    ".#assssd#",
    "#assssdd#",
    "#asssdf#.",
    "#sssdff#.",
    ".#dff##..",
    "..###....",
]

# headband tails in 64-space (liam_v2 frames.TAILS plus 'droop')
TAILS = {
    'down': ([(41, 12), (43, 16), (44, 21), (45, 26)],
             [(42, 10), (45.5, 13), (48.5, 17), (50.5, 21), (52.5, 25), (55.5, 27)]),
    'up': ([(41, 12), (45, 12.5), (49, 13.5), (53, 13)],
           [(42, 10), (46, 9), (50, 9.5), (54, 8.5), (58, 6.5)]),
    'flick': ([(41, 12), (45, 11), (49, 11.5), (53, 10.5), (56, 9)],
              [(42, 10), (46, 8), (50, 7), (54, 7.5), (58, 6), (61, 4)]),
    'mid': ([(41, 12), (44.5, 14.5), (48, 17), (51, 19)],
            [(42, 10), (46, 11), (50, 12.5), (54, 14), (57, 14), (60, 12.5)]),
    'droop': ([(41, 12), (42, 17), (42.5, 22), (42, 27)],
              [(42, 10), (44, 15), (45, 20), (45.5, 25), (45, 30)]),
    'hold': ([(41, 12), (44, 15.5), (46.5, 19.5), (48.5, 23)],
             [(42, 10), (46, 12), (50, 14.5), (53.5, 17), (57, 18), (60, 17)]),
}


def tails(dy=0, kind=None, dx=0):
    if kind is None:
        return body('tails', dx=dx, dy=dy)
    lo, up = TAILS[kind]
    return R.tails_layer(FW, FH, lo, up, BODY[0] + dx, BODY[1] + dy)


# ------------------------------------------------------------------ small FX helpers (no keyline)
def dots(L, pts, ch):
    for (x, y) in pts:
        x, y = int(round(x)), int(round(y))
        if 0 <= x < FW and 0 <= y < FH:
            L[y, x] = ch


def ring_arc(L, cx, cy, rx, ry, a0, a1, ch, step=2.0):
    n = max(4, int(abs(a1 - a0) / step))
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = int(round(cx + rx * math.cos(a))), int(round(cy + ry * math.sin(a)))
        if 0 <= x < FW and 0 <= y < FH:
            L[y, x] = ch


def sweat_drop(L, x, y):
    R.blk(L, x, y, [
        "..#..",
        ".#l#.",
        "#llb#",
        "#lbb#",
        ".###.",
    ])
    return L


def little_star(L, x, y):
    R.blk(L, x - 2, y - 2, [
        "..#..",
        ".#c#.",
        "#cWc#",
        ".#c#.",
        "..#..",
    ])
    return L


# ------------------------------------------------------------------ poses
def pose_a_idle():
    """a) on the pillar, idle and smug: staff held upright at his side, chin up, smirk, lenses glinting."""
    legs = place(legs_narrow())
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 5, 33, 3.6, 3.2))
    st = staff_line((4.5, 61.5), (4.5, 8.5), orb='neutral')
    H = place(head_variant(mouth='smirk', lens='dim'), dy=-1)
    cv = R.compose([tails(-1), legs, body('torso'), body('near'), H, st, A], FW, FH)
    fist_at(cv, *P(4.5, 30))
    return cv, dict(name='a_idle', where='perch', orb=P(5.0, 9.0))


def stroke(L, pts, ch, r=0.8):
    """A filled polyline (no keyline) for FX strokes."""
    m = R.polyline_mask(pts, r, FW, FH)
    L[m] = ch
    return m


def vortex(cx, cy, rx, ry, turns=(0, 360), thick=1.4, cols=('5', 'b', 'l', 'W')):
    """A flattened water ring round (cx, cy): returns (back, front) layers. Colour runs dark at the back
    to foam at the front; the back half goes behind the staff head, the front half over it."""
    back, front = layer(), layer()
    a0, a1 = turns
    n = int(abs(a1 - a0) / 2)
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        s_ = math.sin(a)            # +1 = front (toward the viewer, lower on screen)
        k = int(max(0, min(len(cols) - 1, round((s_ + 1) / 2 * (len(cols) - 1)))))
        tgt = front if s_ > -0.05 else back
        m = R.ellipse_mask(x, y, thick, thick * 0.8, FW, FH)
        tgt[m] = cols[k]
    return back, front


def ribbon_fx(pts, radii, front_fn, ramp=('q', 'b', 'l', 'W'), light=(-0.3, -1.0)):
    """A shaded FX ribbon (no keyline) along a point list with a radius per point.
    Shading runs across the ribbon: the edge facing `light` is lit (highlight, then a foam fleck), the
    other edge falls to the dark. front_fn(i) says whether segment i passes in front of the staff.
    Returns (back, front) layers."""
    back, front = layer(), layer()
    X, Y = R.centres(FW, FH)
    lx, ly = light
    ln = math.hypot(lx, ly)
    lx, ly = lx / ln, ly / ln
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        r0, r1 = radii[i], radii[i + 1]
        m = R.tcapsule_mask(ax, ay, bx, by, r0, r1, FW, FH)
        if not m.any():
            continue
        t, qx, qy = R.seg_t_arr(X, Y, ax, ay, bx, by)
        r = r0 + (r1 - r0) * t
        ox_, oy_ = (X - qx) / np.maximum(r, 1e-6), (Y - qy) / np.maximum(r, 1e-6)
        v = ox_ * lx + oy_ * ly          # +1 on the lit edge, -1 on the shadow edge
        ch = np.where(v > 0.55, ramp[3], np.where(v > 0.05, ramp[2], np.where(v > -0.5, ramp[1], ramp[0])))
        tgt = front if front_fn(i) else back
        tgt[m] = ch[m]
    return back, front


def coil(cx, cy, rx, ry, t0, t1, rise, n=90, r_mid=1.9, r_end=0.5):
    """A rising elliptical coil: points and a tapered radius profile, plus a front/back test."""
    pts, radii, fronts = [], [], []
    for i in range(n + 1):
        u = i / n
        t = t0 + (t1 - t0) * u
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t) - rise * u))
        taper = math.sin(math.pi * min(1, u * 1.15)) if u < 0.87 else max(0.25, (1 - u) / 0.13 * 0.8)
        radii.append(r_end + (r_mid - r_end) * max(0.0, taper))
        fronts.append(math.sin(t) > 0)
    return pts, radii, (lambda i: fronts[i])


def pose_b_cast():
    """b) casting the tsunami: staff hoisted high at his side, orb blazing blue, a rope of water coiling
    up round the shaft and the head; huge grin, lenses flashing, tails lifting."""
    legs = place(legs_narrow())
    A = arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 6.5, 22, 4.6, 3.6), fore=(6.5, 22, 6, 15, 3.4, 3.1))
    head_c = (6.0, 8.5)
    st = staff_line((6.0, 61.5), head_c, orb='water')
    H = place(head_variant(mouth='big', lens='flash'), dy=-1)
    ox, oy = P(6.0 + 0.5, 8.5 + 0.5)
    # a spinning ring of water round the head, tilted, thick at the front, thinning at the back
    pts, radii, fr = [], [], []
    tilt = math.radians(-16)
    for i in range(121):
        t = math.radians(-60 + 380 * i / 120)
        ex, ey = 9.8 * math.cos(t), 4.2 * math.sin(t)
        pts.append((ox + ex * math.cos(tilt) - ey * math.sin(tilt), oy + 2 + ex * math.sin(tilt) + ey * math.cos(tilt)))
        u = i / 120
        radii.append(0.5 + 1.25 * math.sin(math.pi * u) * (0.55 + 0.45 * max(0, math.sin(t))))
        fr.append(math.sin(t) > -0.1)
    back, front = ribbon_fx(pts, radii, lambda i: fr[i])
    cv = R.compose([tails(-1, 'up'), legs, body('torso'), body('near'), H, back, st, A, front], FW, FH)
    fist_at(cv, *P(6.0, 19.0))
    fx = layer()
    dots(fx, [(ox - 9, oy - 3), (ox + 12, oy - 5), (ox + 10, oy + 4), (ox - 8, oy + 5), (ox + 3, oy - 9),
              (ox - 5, oy - 8), (ox + 13, oy)], 'l')
    dots(fx, [(ox - 9, oy - 2), (ox + 13, oy - 4), (ox - 4, oy - 9)], 'b')
    R.composite(cv, fx)
    return cv, dict(name='b_cast_tsunami', where='perch', orb=(ox, oy))


def motion_arc(L, cx, cy, r, a0, a1, ramp=('v', 'w', 'W'), thick=1.0):
    """A windmill smear: a thick arc that fades from the tail (v) to the head (W), no keyline."""
    n = max(6, int(abs(a1 - a0) / 3))
    for i in range(n + 1):
        u = i / n
        a = math.radians(a0 + (a1 - a0) * u)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        k = min(len(ramp) - 1, int(u * len(ramp)))
        m = R.ellipse_mask(x, y, thick * (0.5 + u), thick * (0.5 + u), FW, FH)
        L[m] = ramp[k]
    return L


def wind_burst(L, cx, cy, reach=18, spread=70, down=True, arcs=4, swirl=True):
    """Air FX (no keyline): a swirl on the source point and crescent arcs fanning out down-screen."""
    ramp = ('W', 'W', 'l', 'w', 'v')
    base = 90 if down else -90
    for k in range(arcs):
        r = 6 + k * (reach - 6) / max(1, arcs - 1)
        ch = ramp[min(len(ramp) - 1, k + 1)]
        a0, a1 = base - spread * (0.55 + 0.1 * k), base + spread * (0.55 + 0.1 * k)
        n = max(8, int((a1 - a0) / 2.5))
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            x, y = cx + r * math.cos(a), cy + r * 0.8 * math.sin(a)
            gap = (i % 7) in (5, 6) and k > 0
            if not gap and 0 <= int(x) < FW and 0 <= int(y) < FH:
                L[int(y), int(x)] = ch
                if k < 2 and 0 <= int(y) + 1 < FH:
                    L[int(y) + 1, int(x)] = ch
    if swirl:
        for i in range(60):
            t = i / 59
            a = math.radians(-40 + 520 * t)
            r = 1.0 + 5.0 * t
            x, y = cx + r * math.cos(a), cy + r * 0.85 * math.sin(a)
            if 0 <= int(x) < FW and 0 <= int(y) < FH:
                L[int(y), int(x)] = 'W' if t < 0.6 else 'l'
    return L


def frost_mist(L, x, y, length=30, width=16):
    """Frost breath (no keyline): three curling wisps fanning down-screen from the lips, each a tapered
    stroke with a pale core, a few small icy puffs where they curl, and snowflakes around."""
    X, Y = R.centres(FW, FH)
    for k, (bend, reach, ch_core) in enumerate(((-1.0, 1.0, 'W'), (0.9, 0.92, 'l'), (-0.2, 0.78, 'W'))):
        pts, radii = [], []
        for i in range(24):
            u = i / 23
            px = x + (k - 1) * width * 0.42 * u + bend * math.sin(u * math.pi * 1.6) * 3.0
            py = y + 2 + u * length * reach
            pts.append((px, py))
            radii.append(0.45 + 1.1 * math.sin(math.pi * min(1.0, u * 1.05)))
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            m = R.tcapsule_mask(ax, ay, bx, by, radii[i], radii[i + 1], FW, FH)
            L[m] = 'l' if ch_core == 'W' and i > 17 else ch_core
            m2 = R.tcapsule_mask(ax + 0.6, ay + 0.4, bx + 0.6, by + 0.4, radii[i] * 0.5, radii[i + 1] * 0.5, FW, FH)
            L[m2 & ~m] = 'b'
        ex, ey = pts[-4]
        r = 2.2
        mm = ((X - ex) / r) ** 2 + ((Y - ey) / (r * 0.8)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, ex, ey, r, r * 0.8))
        L[mm] = np.where(v > 0.6, 'W', np.where(v > 0.3, 'l', 'b'))[mm]
    for (dx, dy) in ((-10, 12), (10, 15), (-13, 24), (13, 26), (-4, 33), (5, 7), (1, 20)):
        cx, cy = int(x + dx), int(y + dy)
        for (a_, b_) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= cx + a_ < FW and 0 <= cy + b_ < FH:
                L[cy + b_, cx + a_] = 'W' if (a_, b_) == (0, 0) else 'l'
    return L
def pose_c_wobble():
    """c) wobbling after a hit: pitched over to his left, near foot kicked up off the stone, near arm
    windmilling, staff jabbed down for balance; gasping, sweat flying, tails whipping."""
    from le_poses import legs_lift_near
    legs = place(legs_lift_near(up=6, out=3))
    lean = -2
    torso = body('torso', dx=lean)
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 5, 39, 4.8, 4.0), fore=(5, 39, 4, 33, 3.6, 3.2), dx=lean)
    N = arm(delt=(49.0, 31.0, 5.3), up=(50, 30, 57, 23, 4.6, 3.8), fore=(57, 23, 60, 14, 3.6, 3.2), dx=lean)
    st = staff_line((9.0, 60.0), (5.5, 8.0), orb='neutral')
    H = place(head_variant(mouth='gasp', lens='flash'), dx=lean - 3, dy=1)
    T = tails(1, 'flick', dx=lean - 3)
    fx = layer()
    hx_, hy_ = P(60 + lean, 12)
    motion_arc(fx, hx_ - 6, hy_ + 10, 11.0, -150, -15, ramp=('v', 'w', 'W'), thick=1.5)
    motion_arc(fx, hx_ - 6, hy_ + 10, 11.0, 15, 95, ramp=('v', 'w'), thick=1.3)
    motion_arc(fx, hx_ - 6, hy_ + 10, 7.5, -140, -40, ramp=('v', 'w'), thick=0.9)
    cv = R.compose([T, fx, legs, torso, N, H, st, A], FW, FH)
    fist_at(cv, *P(4 + lean, 31))
    fist_at(cv, *P(60 + lean, 12))
    sweat_drop(cv, *P(39, 0))
    sweat_drop(cv, *P(6, 7))
    sweat_drop(cv, *P(46, 8))
    wob = layer()
    for (x0, y0, x1, y1) in ((0, 44, -2, 47), (-2, 48, -2, 51), (-2, 52, 0, 55),
                             (63, 42, 65, 45), (65, 46, 65, 50), (65, 51, 63, 54)):
        R.line(wob, *P(x0, y0), *P(x1, y1), 'v')
    cv = R.compose([wob, cv], FW, FH)
    return cv, dict(name='c_wobble', where='perch')

def pose_d_blast():
    """d) air blast: the staff driven forward level across his chest with both fists (a push at the
    player), orb blazing white, a burst of wind rolling off it down the ring."""
    legs = place(legs_narrow())
    A = arm(delt=(11.0, 31.5, 5.3), up=(11, 32, 16, 40, 4.8, 4.2), fore=(16, 40, 18, 38.5, 3.8, 3.5))
    N = arm(delt=(49.0, 31.0, 5.3), up=(49, 32, 45, 40, 4.7, 4.1), fore=(45, 40, 42, 38.5, 3.8, 3.5))
    H = place(head_variant(mouth='shout', lens='flash'), dy=-1)
    head_c = (58.0, 38.0)
    st = staff_line((5.0, 38.0), head_c, orb='air')
    cx, cy = P(*head_c)
    fx = layer()
    wind_burst(fx, cx - 1, cy + 1, reach=8, spread=70, arcs=2)
    mid = P(31, 40)
    wind_burst(fx, mid[0], mid[1] + 2, reach=20, spread=62, arcs=4, swirl=False)
    cv = R.compose([tails(-1, 'up'), legs, body('torso'), A, N, H, st], FW, FH)
    fist_at(cv, *P(18, 38.5))
    fist_at(cv, *P(42, 38.5))
    cv = R.compose([cv, fx], FW, FH)
    # the orb and its crown stay readable on top of the burst
    R.composite(cv, S.head_canvas('air'), int(round(cx - 0.5)) - 8, int(round(cy - 0.5)) - 8)
    return cv, dict(name='d_air_blast', where='perch', orb=(cx, cy))

def pose_e_laugh():
    """e) the anime laugh (ground, before the staff): head back, back of the hand at the mouth, other
    hand on the hip, mouth wide open."""
    A = arm(delt=(11.5, 30.5, 5.2), up=(11, 31, 7, 24, 4.6, 3.5), fore=(7, 24, 15, 21, 3.4, 3.1))
    H = place(head_variant(mouth='laugh', lens='flash'), dy=-2)
    cv = R.compose([tails(-2, 'up'), body('legs'), body('torso'), body('near'), H, A], FW, FH)
    R.blk(cv, *P(13, 16), BACKHAND)
    fx = layer()
    for (x0, y0, x1, y1) in ((45, -2, 48, -5), (48, 3, 52, 1), (49, 9, 53, 9), (14, -1, 11, -4)):
        R.line(fx, *P(x0, y0), *P(x1, y1))
    R.composite(cv, fx)
    return cv, dict(name='e_laugh', where='ground')


def pose_f_gag():
    """f) the gag: pulling the staff out of his mouth, up and to the right, slime and all."""
    H = place(head_variant(mouth='laugh', lens='dim'), dy=-2)
    N = arm(delt=(49.0, 31.0, 5.3), up=(50, 31, 55, 20, 4.6, 3.8), fore=(55, 20, 49, 8, 3.6, 3.2))
    mouth = (28.5, 21.5)
    head_c = (57.0, -19.0)
    cv = R.compose([tails(-2, 'mid'), body('legs'), body('torso'), body('far'), H], FW, FH)
    st = staff_line(mouth, head_c, orb='neutral', ferrule=False)
    R.composite(cv, st)
    R.composite(cv, N)
    fist_at(cv, *P(47.5, 5.5))
    fx = layer()
    dots(fx, [P(29, 25), P(29, 26), P(30, 27), P(31, 22), P(33, 17), P(34, 18), P(36, 13), P(24, 24), P(24, 25)], '8')
    dots(fx, [P(30, 26), P(33, 16), P(37, 12)], 'W')
    R.composite(cv, fx)
    return cv, dict(name='f_staff_from_mouth', where='ground')


STONE = ('t', 'T', 'y', 'Y')     # slate greys from his own palette: the pillar's rock


def rock(L, x, y, size=2):
    """A small outlined stone chip (size 1..3)."""
    shapes = {
        1: [".#.", "#T#", ".#."],
        2: [".##.", "#tT#", "#TY#", ".##."],
        3: [".###.", "#ttT#", "#tTy#", "#TyY#", ".###."],
    }
    rows = shapes[size]
    R.blk(L, int(x) - len(rows[0]) // 2, int(y) - len(rows) // 2, rows)


def puff(L, cx, cy, r):
    """A dust puff: a soft stone-grey ball, lit top-left, no keyline."""
    X, Y = R.centres(FW, FH)
    m = ((X - cx) / r) ** 2 + ((Y - cy) / (r * 0.8)) ** 2 <= 1
    v = R.lambert(R.sphere_normal(X, Y, cx, cy, r, r * 0.8))
    L[m] = np.where(v > 0.75, 'w', np.where(v > 0.4, 'v', 'T'))[m]


def impact(L, x, y, spread=1.0):
    """The staff-butt impact: a green earth flash, cracks in the floor, chips flying, dust either side."""
    for (dx, dy, r) in ((-9, -1, 3.0), (9, -1, 2.8), (-13, 0, 2.0), (13, 0, 2.2)):
        puff(L, x + dx * spread, y + dy, r)
    for (dx, dy, sz) in ((-7, -9, 2), (8, -11, 3), (13, -6, 1), (-3, -14, 1)):
        rock(L, x + dx * spread, y + dy, sz)
    for (dx, dy) in ((0, -3), (-2, -2), (2, -2), (-4, 0), (4, 0), (-3, 1), (3, 1)):
        R.line(L, int(x), int(y), int(x + dx * 1.6), int(y + dy * 1.6), '8')
    if 0 <= int(y) < FH:
        L[int(y), int(x)] = 'W'
    return L


def pose_g_slam():
    """g) the summoning slam (ground): crouched, staff driven into the floor at his side with a shout,
    orb flaring earth-green, the floor cracking, chips and dust bursting up."""
    dy = 3
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 27, 4.7, 3.8), fore=(6, 27, 3, 20, 3.6, 3.2), dy=dy)
    st = staff_line((2.5, 63.0), (2.5, 10.0), orb='earth')
    H = place(head_variant(mouth='shout', lens='flash'), dy=dy)
    cv = R.compose([tails(dy, 'up'), body('legs'), body('torso', dy=dy), body('near', dy=dy), H, st, A], FW, FH)
    fist_at(cv, *P(3, 18 + dy))
    ix, iy = P(2.5, 63)
    fx = layer()
    impact(fx, ix, iy - 1)
    cv = R.compose([cv, fx], FW, FH)
    for (x0, y0, x1, y1) in ((-4, 6, -4, 11), (9, 5, 9, 10), (-2, 0, -2, 4)):
        R.line(cv, *P(x0, y0), *P(x1, y1))
    return cv, dict(name='g_summon_slam', where='ground', impact=(ix, iy))


DAZED_LEGS = [  # sat down hard, legs out toward us in a V, soles up (64-space, x 1.., y 58..69)
    "..............#pppppqqqqqqqQQzzZzQQqqqqqqqQQQz#..............",
    ".............#pppppqqqqqqQQzz#zQQqqqqqqqqQQQQz#.............",
    "...........##pppppqqqqqqQQQz###QqqqpqqqqqqQQQQz##...........",
    "........###pppppqqqqqqQQQzz#...#qqqpqqqqqqqQQQQzz###........",
    ".....###xxxpppqqqqqqQQQzz##.....##qqpqqqqqqqQQQQzxxx###.....",
    "...##xxOOOx#####qqQQQzz##.........##qpqqqqqQQzz####xOOOxx##..",
    "..#xOOoooOOx#...#######.............#######.......#xOOoooOOx#.",
    ".#xOoooooOOx#......................................#xOoooooOOx#",
    ".#xOoooooOOx#......................................#xOoooooOOx#",
    ".#xxOOooOOxx#......................................#xxOOooOOxx#",
    "..#xxOOOOxx#........................................#xxOOOOxx#.",
    "...########..........................................########..",
]


SOLE = [  # a shoe seen from underneath: toe at the top, heel at the bottom (10 x 11)
    "..######..",
    ".#OOOOOO#.",
    "#OxxxxxxO#",
    "#OxOxxOxO#",
    "#OxxxxxxO#",
    "#OxOxxOxO#",
    ".#OxxxxO#.",
    ".#OOOOOO#.",
    ".#OxxxxO#.",
    ".#OOOOOO#.",
    "..######..",
]


def pose_h_dazed():
    """h) dazed on the floor after the fall: sat down hard, legs out in a V with the soles to us, hands
    flat behind, swirl lenses, tongue out, stars circling, headband drooping, staff dropped behind."""
    dy = 12
    X, Y = R.centres(FW, FH)
    legs = layer()
    for (a, b) in (((38.5, 85.0), (19.0, 89.0)), ((57.5, 85.0), (77.0, 89.0))):
        m = R.tcapsule_mask(a[0], a[1], b[0], b[1], 7.2, 6.0, FW, FH)
        v = R.lambert(R.tcapsule_normal(X, Y, a[0], a[1], b[0], b[1], 7.2, 6.0))
        R.paint_part(legs, m, R.quant(v, 'zQqp', [0.28, 0.58, 0.88]))
    R.blk(legs, 8, 84, SOLE)
    R.blk(legs, 78, 84, SOLE)
    torso = body('torso', dy=dy)
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 4, 40, 4.8, 4.0), fore=(4, 40, 1, 46, 3.6, 3.3), dy=dy)
    N = arm(delt=(49.0, 31.0, 5.3), up=(50, 32.5, 56, 40, 4.7, 4.1), fore=(56, 40, 60, 46, 3.8, 3.4), dy=dy)
    st = staff_line((66.0, 52.0), (72.0, 40.0), orb='neutral', ferrule=False)
    Hd = head_variant(mouth='dazed', lens='swirl')
    Hl = place(Hd, dy=dy - 2, dx=1)
    cv = R.compose([st, tails(dy - 2, 'droop', dx=1), A, N, torso, legs, Hl], FW, FH)
    fist_at(cv, *P(0, 47 + dy))
    fist_at(cv, *P(61, 47 + dy))
    for (x, y) in ((6, 2), (20, -3), (40, -3), (55, 3)):
        little_star(cv, *P(x, y + dy - 6))
    return cv, dict(name='h_dazed', where='ground', daze=P(31, dy - 8))

def frost(L, x, y, length=26, spread=0.55):
    """A cone of frost breath from (x, y) down-screen: streaks and flakes, no keyline."""
    for k in range(-3, 4):
        ang = math.pi / 2 + k * spread / 3
        x1, y1 = x + math.cos(ang) * length, y + math.sin(ang) * length
        ch = ('W', 'l', 'b')[abs(k) % 3]
        stroke(L, [(x + k * 0.6, y + 1), (x1, y1)], ch, 0.7 if k == 0 else 0.5)
    for (dx, dy) in ((-6, 10), (7, 13), (-9, 20), (10, 22), (0, 25), (-3, 16), (4, 6)):
        cx, cy = int(x + dx), int(y + dy)
        for (a, b) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= cx + a < FW and 0 <= cy + b < FH:
                L[cy + b, cx + a] = 'W' if (a, b) == (0, 0) else 'l'
    return L


def pose_i_cold_air():
    """i) blowing cold air down from the pillar: cheeks puffed, lips pursed, a stream of frost pouring
    out over his chest and down the ring; orb iced white."""
    legs = place(legs_narrow())
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 5, 33, 3.6, 3.2))
    st = staff_line((4.5, 61.5), (4.5, 8.5), orb='air')
    H = place(head_variant(mouth='blow', lens='dim'))
    cv = R.compose([tails(0, 'mid'), legs, body('torso'), body('near'), H, st, A], FW, FH)
    fist_at(cv, *P(4.5, 30))
    mx, my = P(27.5, 23)
    fx = layer()
    frost_mist(fx, mx, my, length=34, width=34)
    cv = R.compose([cv, fx], FW, FH)
    return cv, dict(name='i_cold_air', where='perch', mouth=(mx, my))

def pose_j_tremor():
    """j) the tremor slam on the pillar top: staff hauled up and driven down beside his near foot,
    orb flaring green, the stone cracking and spitting chips; the far fist pumped back."""
    dy = 2
    legs = place(legs_narrow())
    N = arm(delt=(49.0, 31.0, 5.3), up=(50, 33, 55, 27, 4.7, 3.8), fore=(55, 27, 52, 20, 3.6, 3.2), dy=dy)
    st = staff_line((51.5, 62.5), (51.5, 10.0), orb='earth')
    H = place(head_variant(mouth='shout', lens='flash'), dy=dy)
    A = arm(delt=(11.0, 31.5, 5.3), up=(10, 33, 6, 40, 4.8, 4.0), fore=(6, 40, 9, 45, 3.6, 3.3), dy=dy)
    cv = R.compose([tails(dy, 'up'), legs, body('torso', dy=dy), A, H, st, N], FW, FH)
    fist_at(cv, *P(51.5, 18 + dy))
    fist_at(cv, *P(9.5, 47 + dy))
    ix, iy = P(51.5, 63)
    fx = layer()
    impact(fx, ix, iy - 1, spread=0.6)
    cv = R.compose([cv, fx], FW, FH)
    return cv, dict(name='j_tremor_slam', where='perch', impact=(ix, iy))


POSES = [pose_a_idle, pose_b_cast, pose_c_wobble, pose_d_blast, pose_e_laugh, pose_f_gag, pose_g_slam,
         pose_h_dazed, pose_i_cold_air, pose_j_tremor]
