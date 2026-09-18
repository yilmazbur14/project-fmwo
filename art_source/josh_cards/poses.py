"""Pose algebra for Josh's animation set.

body.py already draws every part of him (legs, sneakers, tapered-capsule arms, coat, tee, belt,
collar, hem) from a pose dict.  This module adds:

  * the canonical BASE pose, spelled out with a `neck` so the whole figure can move,
  * transforms (shift, crouch, lean, arm/leg setters) so a frame is described as a delta from
    the approved standing pose instead of re-typed coordinates,
  * a build() that runs body.py's own drawing calls in body.py's own order, with two extra
    hooks: coat tails behind the figure, and a configurable front/back arm.

`l_arm` / `r_arm` in a pose dict are z-order slots, not anatomy: l_arm is drawn in FRONT of the
coat, r_arm BEHIND it.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
import rig
import body as BD
import cards as CD
from rig import hcap, hdome, hbump, SKIN, IVORY, JEAN, BLACK, RED, TH_LIMB, TH_6, TH_5, TH_4, TH_BLK

IV_TH = [0.0, 0.13, 0.32, 0.58, 0.87]

# ---------------------------------------------------------------- the canonical pose
# LEAN build.  body.POSE0 is the stocky standing pose the first pass shipped; the user asked for a
# smaller, skinnier card magician, so the trunk is 20% narrower, the waist is nipped in, the duster
# is longer with a flared hem, and the limbs are longer and much thinner.  Feet still land on row
# 79 and the figure is still centred on x=40.
BASE = dict(BD.POSE0)
BASE.update(
    neck=[(35, 46), (45, 46), (46, 53), (34, 53)],
    neck_axis=((40, 46), (40, 54), 4.5, 4.0),
    torso=[(37, 47), (35, 49), (32, 51), (31, 55), (32, 59), (31, 62), (30, 67),
           (34, 66), (40, 64), (46, 66), (50, 67), (49, 62), (48, 59), (49, 55),
           (48, 51), (45, 49), (43, 47)],
    tee=[(36, 49), (44, 49), (45, 56), (43, 63), (37, 63), (35, 56)],
    collar_l=[(33, 47), (37, 50), (37, 56), (34, 56), (31, 52), (31, 48)],
    collar_r=[(47, 47), (43, 50), (43, 56), (46, 56), (49, 52), (49, 48)],
    collar_lining=[(35, 50, ["Qq"]), (35, 51, ["QQq"]), (36, 52, ["QQ"]), (36, 53, ["Qq"]),
                   (36, 54, ["Qq"]), (36, 55, ["qq"]),
                   (43, 50, ["qQ"]), (42, 51, ["qQQ"]), (42, 52, ["QQ"]), (42, 53, ["qQ"]),
                   (42, 54, ["qQ"]), (42, 55, ["qq"])],
    belt=(33, 47, 58),
    coat_lines=[(33, 55, ["u"]), (33, 56, ["U"]), (33, 57, ["U"]),
                (47, 55, ["U"]), (47, 56, ["U"])],
    l_arm=((32, 54), (29, 62), (26, 70), (25, 73), 4.0, 3.0, 2.5, 3.3),
    r_arm=((48, 54), (51, 62), (54, 70), (55, 73), 3.9, 2.9, 2.4, 3.2),
    l_leg=((36, 61), (34, 69), (33, 77), 4.2, 3.5, 3.0),
    r_leg=((44, 62), (46, 69), (47, 77), 4.0, 3.4, 2.9),
    l_shoe=[(29, 75), (38, 75), (39, 77), (37, 79), (27, 79), (26, 77)],
    r_shoe=[(42, 75), (51, 75), (53, 77), (52, 79), (42, 79), (41, 77)],
)

BULK = 1.0                         # >1 puts weight back into the chest and shoulders
SLIM_W = 0.80                      # trunk narrowing factor for per-frame pose overrides
LIMB = 0.76                        # limb thickness factor


def nx(v, k=SLIM_W):
    return int(round(40 + (v - 40) * k))


POLY_KEYS = ('torso', 'tee', 'collar_l', 'collar_r', 'l_shoe', 'r_shoe', 'neck')
BLOCK_KEYS = ('collar_lining', 'coat_lines')
ARM_KEYS = ('l_arm', 'r_arm')
LEG_KEYS = ('l_leg', 'r_leg')
TAIL_KEYS = ('tail_back', 'tail_mid', 'tail_front')


# ---------------------------------------------------------------- transforms
def _poly(p, dx, dy):
    return [(x + dx, y + dy) for (x, y) in p]


def _blocks(b, dx, dy):
    return [(x + dx, y + dy, rows) for (x, y, rows) in b]


def _arm(a, dx, dy):
    S, E, Wr, Hn = a[:4]
    return ((S[0] + dx, S[1] + dy), (E[0] + dx, E[1] + dy),
            (Wr[0] + dx, Wr[1] + dy), (Hn[0] + dx, Hn[1] + dy)) + tuple(a[4:])


def _leg(l, dx, dy):
    Hp, K, A = l[:3]
    return ((Hp[0] + dx, Hp[1] + dy), (K[0] + dx, K[1] + dy), (A[0] + dx, A[1] + dy)) + tuple(l[3:])


def shift(P, dx, dy, keys=None):
    """Translate the whole figure (or just `keys`)."""
    Q = dict(P)
    for k in POLY_KEYS + BLOCK_KEYS + ARM_KEYS + LEG_KEYS + TAIL_KEYS + ('belt', 'neck_axis'):
        if k not in P or P[k] is None or (keys and k not in keys):
            continue
        if k in POLY_KEYS or k in TAIL_KEYS:
            Q[k] = ([_poly(p, dx, dy) for p in P[k]] if k in TAIL_KEYS else _poly(P[k], dx, dy))
        elif k in BLOCK_KEYS:
            Q[k] = _blocks(P[k], dx, dy)
        elif k in ARM_KEYS:
            Q[k] = _arm(P[k], dx, dy)
        elif k in LEG_KEYS:
            Q[k] = _leg(P[k], dx, dy)
        elif k == 'belt':
            x0, x1, y0 = P[k]
            Q[k] = (x0 + dx, x1 + dx, y0 + dy)
        elif k == 'neck_axis':
            a, b, r0, r1 = P[k]
            Q[k] = ((a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy), r0, r1)
    return Q


UPPER = ('torso', 'tee', 'collar_l', 'collar_r', 'neck', 'neck_axis', 'collar_lining',
         'coat_lines', 'belt', 'l_arm', 'r_arm', 'tail_back', 'tail_front')


def bob(P, dy, dx=0):
    """Move everything above the hips; legs keep their feet planted, hips follow."""
    Q = shift(P, dx, dy, keys=UPPER)
    for k in LEG_KEYS:
        Hp, K, A = P[k][:3]
        Q[k] = ((Hp[0] + dx, Hp[1] + dy), K, A) + tuple(P[k][3:])
    return Q


def lean(P, top, bottom=0.0, pivot=66):
    """Shear the upper body sideways: `top` px at the shoulders falling to `bottom` at `pivot`."""
    def f(x, y):
        t = max(0.0, min(1.0, (pivot - y) / float(pivot - 45)))
        return x + int(round(bottom + (top - bottom) * t))
    Q = dict(P)
    for k in ('torso', 'tee', 'collar_l', 'collar_r', 'neck'):
        Q[k] = [(f(x, y), y) for (x, y) in P[k]]
    for k in BLOCK_KEYS:
        Q[k] = [(f(x, y), y, rows) for (x, y, rows) in P[k]]
    for k in TAIL_KEYS:
        if P.get(k):
            Q[k] = [[(f(x, y), y) for (x, y) in poly] for poly in P[k]]
    for k in ARM_KEYS:
        a = P[k]
        S = (f(*a[0]), a[0][1])
        Q[k] = (S,) + tuple(a[1:])
    x0, x1, y0 = P['belt']
    d = f(x0, y0) - x0
    Q['belt'] = (x0 + d, x1 + d, y0)
    a, b, r0, r1 = P['neck_axis']
    Q['neck_axis'] = ((f(*a), a[1]), (f(*b), b[1]), r0, r1)
    for k in LEG_KEYS:
        Hp, K, A = P[k][:3]
        Q[k] = ((f(*Hp), Hp[1]), K, A) + tuple(P[k][3:])
    return Q


def arms(P, front=None, back=None):
    Q = dict(P)
    if front is not None:
        Q['l_arm'] = front
    if back is not None:
        Q['r_arm'] = back
    return Q


def legs(P, l=None, r=None, lshoe=None, rshoe=None):
    Q = dict(P)
    for k, v in (('l_leg', l), ('r_leg', r), ('l_shoe', lshoe), ('r_shoe', rshoe)):
        if v is not None:
            Q[k] = v
    return Q


def with_(P, **kw):
    Q = dict(P)
    Q.update(kw)
    return Q


def A(S, E, Wr, Hn, r_sh=5.2, r_el=4.0, r_wr=3.2, hand=3.9):
    """Arm for the lean build.  The shoulder pulls in toward the spine for the narrower chest and
    the limb is thinned, but the elbow / wrist / hand keep the reach they were authored with - so
    a longer, skinnier arm lands on exactly the same fingertips, and every card release pixel in
    the sheet contract stays put."""
    return ((nx(S[0], 0.78), S[1] + 3), E, Wr, Hn,
            r_sh * LIMB, r_el * LIMB, r_wr * LIMB, hand * 0.84)


def L(Hp, K, An, r_h=5.4, r_k=4.6, r_a=4.0):
    """Leg for the lean build: narrow hips, a longer shin, a much thinner limb."""
    return ((nx(Hp[0], 0.62), Hp[1]), (nx(K[0], 0.86), K[1] + 1), (nx(An[0], 0.92), An[1] + 1),
            r_h * 0.78, r_k * 0.76, r_a * 0.76)


def foot(cx, sole, w=11, h=6, toe=0):
    """Slim boot: cx = centre, sole = bottom row, toe = +px of toe overhang (sign = side)."""
    cx = nx(cx, 0.94)
    w, h = max(8, w - 2), max(4, h - 1)
    x0, x1 = cx - w // 2, cx + (w - w // 2)
    y0 = sole - h
    if toe >= 0:
        return [(x0, y0), (x1 + toe, y0), (x1 + toe + 1, sole - 2), (x1 + toe, sole),
                (x0 - 1, sole), (x0 - 2, sole - 2)]
    return [(x0 + toe, y0), (x1, y0), (x1 + 1, sole - 2), (x1, sole),
            (x0 + toe - 1, sole), (x0 + toe - 2, sole - 2)]


TRUNK_KEYS = ('torso', 'tee', 'collar_l', 'collar_r', 'neck')


def trunk(P, k=SLIM_W, dy=0):
    """Narrow a hand-authored trunk (the ride / recovery / kneeling poses) onto the lean build."""
    Q = dict(P)
    for key in TRUNK_KEYS:
        if P.get(key):
            Q[key] = [(nx(x, k), y + dy) for (x, y) in P[key]]
    for key in BLOCK_KEYS:
        if P.get(key):
            Q[key] = [(nx(x, k), y + dy, rows) for (x, y, rows) in P[key]]
    if P.get('belt'):
        x0, x1, y0 = P['belt']
        Q['belt'] = (nx(x0, k), nx(x1, k), y0 + dy)
    if P.get('neck_axis'):
        a, b, r0, r1 = P['neck_axis']
        Q['neck_axis'] = ((nx(a[0], k), a[1] + dy), (nx(b[0], k), b[1] + dy), r0 * 0.8, r1 * 0.8)
    return Q


# ---------------------------------------------------------------- drawing
def _cent(poly):
    return (sum(x for (x, y) in poly) / float(len(poly)),
            sum(y for (x, y) in poly) / float(len(poly)))


REF_TORSO = _cent(BASE['torso'])
REF_TEE = _cent(BASE['tee'])


def _delta(poly, ref):
    cx, cy = _cent(poly)
    return cx - ref[0], cy - ref[1]


def arm(c, S, E, Wr, Hnd, r_sh, r_el, r_wr, hand_r=3.8, sleeve_ramp=IVORY, cuff=True):
    """Josh's arm, rebuilt to read at 3x as THREE parts instead of a barber pole.

    body.arm() alternates cream sleeve / red elbow cuff / bare skin forearm / red fist, which on
    the short arms of the approved standing sprite is fine but on an extended arm turns into
    red-white-red-white banding.  Here the duster sleeve runs almost the whole limb, there is
    exactly ONE red cuff band, and it sits hard against a shaped red glove so the hand reads as a
    single red terminal with a thumb, not a ball on a stick.
    """
    under = copy(c)
    m_up = tcapsule_mask(S[0], S[1], E[0], E[1], r_sh, r_el)
    m_fo = tcapsule_mask(E[0], E[1], Wr[0], Wr[1], r_el, r_wr)

    # --- shaped glove: palm + thumb nub set perpendicular to the forearm, on the leading side
    ax, ay = Hnd[0] - Wr[0], Hnd[1] - Wr[1]
    _ln = math.hypot(ax, ay) or 1.0
    ax, ay = ax / _ln, ay / _ln
    px_, py_ = -ay, ax
    palm = ellipse_mask(Hnd[0] - ax * 0.35, Hnd[1] - ay * 0.35, hand_r, hand_r * 1.02)
    thumb = ellipse_mask(Hnd[0] + px_ * hand_r * 0.85 - ax * hand_r * 0.55,
                         Hnd[1] + py_ * hand_r * 0.85 - ay * hand_r * 0.55,
                         hand_r * 0.52, hand_r * 0.52)
    knuck = ellipse_mask(Hnd[0] + ax * hand_r * 0.42, Hnd[1] + ay * hand_r * 0.42,
                         hand_r * 0.72, hand_r * 0.72)
    m_hd = m_or(palm, thumb, knuck)
    full = m_or(m_up, m_fo, m_hd)

    def hf(px, py):
        return max(hcap(px, py, S[0], S[1], E[0], E[1], r_sh, r_el),
                   hcap(px, py, E[0], E[1], Wr[0], Wr[1], r_el, r_wr),
                   hdome(px, py, Hnd[0] - ax * 0.35, Hnd[1] - ay * 0.35, hand_r, hand_r * 1.02, hand_r),
                   hdome(px, py, Hnd[0] + px_ * hand_r * 0.85 - ax * hand_r * 0.55,
                         Hnd[1] + py_ * hand_r * 0.85 - ay * hand_r * 0.55,
                         hand_r * 0.52, hand_r * 0.52, hand_r * 0.62))

    sleeve = m_sub(m_or(m_up, m_fo), m_hd)
    BD.paint(c, sleeve, hf, sleeve_ramp, [0.0, 0.13, 0.32, 0.58, 0.87], zscale=0.95)
    BD.paint(c, m_hd, hf, RED, TH_5, zscale=0.95)

    if cuff:
        # one band, perpendicular to the forearm, sitting right where the sleeve meets the glove
        cl = math.hypot(Wr[0] - E[0], Wr[1] - E[1]) or 1.0
        t = max(0.0, 1.0 - 2.0 / cl)
        cx = E[0] + (Wr[0] - E[0]) * t
        cy = E[1] + (Wr[1] - E[1]) * t
        ang = math.degrees(math.atan2(Wr[0] - E[0], -(Wr[1] - E[1])))
        band = blank()
        CD.draw_card(band, cx, cy, r_wr * 2 + 3.0, 3.0, ang, face='q', shade='L', dark='L',
                     outline=None)
        for y in range(H):
            for x in range(W):
                if band[y][x] != '.' and sleeve[y][x]:
                    c[y][x] = band[y][x]

    # knuckle crease so the glove reads as a hand, not a blob
    for y in range(H):
        for x in range(W):
            if m_hd[y][x] and thumb[y][x] and not palm[y][x] and c[y][x] in RED:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < H and palm[Y][X] and c[Y][X] in RED:
                        c[y][x] = 'L'
                        break
    BD.outline_only(c, full, under)
    return full


TAIL_RAMP = 'IIiUuN'


def cloth(c, poly, ramp=TAIL_RAMP, th=IV_TH, root=None, lining=True):
    """A flapping coat tail: the same ivory ramp and 1px outline as the coat body.  `root` is the
    end still attached to him - it stays lit, the free tip falls away into shadow.  `lining` paints
    the red inside of the duster along the leading edge, the way it shows when the coat lifts."""
    m = poly_mask(poly)
    xs = [x for (x, y) in poly]
    ys = [y for (x, y) in poly]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    rx = max(5.0, (max(xs) - min(xs)) / 2.1)
    ry = max(6.0, (max(ys) - min(ys)) / 1.3)
    hx, hy = root if root else (cx - rx * 0.35, cy - ry * 0.3)
    under = copy(c)
    BD.paint(c, m, lambda px, py: hdome(px, py, hx - rx * 0.15, hy, rx, ry, 6.5), ramp, th, 0.9)
    # ONE fold running the length of the sheet, so it reads as cloth rather than a flat wing
    for x in range(W):
        col = sorted(y for y in range(H) if m[y][x])
        if len(col) < 5:
            continue
        y = col[int(len(col) * 0.66)]
        if c[y][x] in ramp:
            c[y][x] = ramp[max(0, ramp.index(c[y][x]) - 2)]
    BD.outline_only(c, m, under)
    if lining:
        # red duster lining only where the coat turns over at the ROOT - an accent, not a stripe
        # running the length of the tail
        cols = sorted(x for x in range(W) if any(m[y][x] for y in range(H)))
        if cols:
            near = cols[-9:] if (root and root[0] >= (cols[0] + cols[-1]) / 2) else cols[:9]
            for x in near:
                col = sorted(y for y in range(H) if m[y][x])
                if len(col) < 4:
                    continue
                y = col[0] + 1
                if c[y][x] in ramp:
                    c[y][x] = 'Q'
    return m


def bulk(P, k):
    """Candidate B: widen the trunk and thicken the arms so the fuller head sits on a body that
    can carry it, without losing the lean gambler line in the legs."""
    if k == 1.0:
        return P
    Q = trunk(P, k=k)
    for key in ARM_KEYS:
        if P.get(key):
            a = Q[key]
            Q[key] = a[:4] + (a[4] * k, a[5] * k, a[6] * k, a[7])
    return Q


def build(c, P):
    """body.build_body's exact sequence, with the pose's own neck plus optional coat tails."""
    P = bulk(P, BULK)
    for poly in P.get('tail_back', []) or []:
        cloth(c, poly, root=max(poly, key=lambda p: p[0]))
    BD.leg(c, *P['l_leg'])
    BD.leg(c, *P['r_leg'])
    BD.shoe(c, P['l_shoe'], toe_left=True)
    BD.shoe(c, P['r_shoe'], toe_left=False)
    if P.get('r_arm'):
        arm(c, *P['r_arm'])
    under = copy(c)
    nm = poly_mask(P['neck'])
    (na, nb, nr0, nr1) = P['neck_axis']
    BD.paint(c, nm, lambda px, py: hcap(px, py, na[0], na[1], nb[0], nb[1], nr0, nr1), SKIN, TH_LIMB, 0.95)
    BD.outline_only(c, nm, under)
    under = copy(c)
    tmask = poly_mask(P['torso'])
    tdx, tdy = _delta(P['torso'], REF_TORSO)

    def th_(px, py):
        return BD.torso_h(px - tdx, py - tdy)

    BD.paint(c, tmask, th_, IVORY, IV_TH, 0.9)
    despeckle(c, chars=IVORY, region=tmask)
    BD.outline_only(c, tmask, under)
    tm = m_and(poly_mask(P['tee']), tmask)
    under = copy(c)
    edx, edy = _delta(P['tee'], REF_TEE)
    BD.paint(c, tm, lambda px, py: hdome(px, py, 40.0 + edx, 58.0 + edy, 6.5, 12.0, 5.0),
             BLACK, TH_BLK, 0.9)
    BD.outline_only(c, tm, under)
    BD.belt(c, P)
    BD.collar(c, P)
    BD.coat_detail(c, P, tmask, tm)
    # a streaming coat tail belongs to the coat: over the legs, under the arms
    for poly in P.get('tail_mid', []) or []:
        cloth(c, poly, root=max(poly, key=lambda p: p[0]))
    if P.get('l_arm'):
        arm(c, *P['l_arm'])
    for poly in P.get('tail_front', []) or []:
        cloth(c, poly)
    return c
