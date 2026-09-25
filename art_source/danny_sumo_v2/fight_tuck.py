"""The Sumo Smash tuck (the user's reference of 2026-09-24, images/23.png): a compact cannonball in the
front view. Both knees hauled up to the chest, both fists clamped on top of the knees, the big bare
soles of both feet toward the viewer, the head tucked down between the knees (awake, gritted), the
mawashi round the rear at the bottom, the rear leading the fall. An original homage: Danny's own
parts, his beanie, collar, chain, mawashi, apron and wraps, and no kabuki paint.

Built the approved rig's way. The torso, collar, chain, deltoids, upper arms, fists, wraps, mawashi,
rope and apron are the approved parts (moved, and for the squash, reshaped as geometry); the knees,
shins, soles and the forearms that grip the knees are new forms drawn in the same method (one keylined
sculpted form each, anatomy as open lines). Every part goes through one transform `xf` (the hover's
rock, the descent's stretch, the impact's squash) BEFORE it is lit, so the light stays upper left
however the ball is squashed or turned. The head is laid on unsquashed (the juggle's rule: the face
must read).

Frame: the rig's 176 x 144, the rear's keyline on row 143 at the centre column, the rear contact.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fight as FT  # noqa: E402
import anim  # noqa: E402
import sumo_lib as L  # noqa: E402
from sumo_lib import spoly, sculpt, shade, taper_line, ellipse, MIR, SKIN  # noqa: E402
import gear as G  # noqa: E402
import hands as HN  # noqa: E402
import limbs as LB  # noqa: E402
import torso as T  # noqa: E402
import danny_v2 as D  # noqa: E402

SKINSET = set(SKIN)
CX = 87.5


class Xf:
    """p -> squash (sx, sy) about `base`, turn `deg` about `pivot`, then move. Has .inverse."""

    def __init__(self, sx=1.0, sy=1.0, base=(CX, 143.0), deg=0.0, pivot=(CX, 90.0), move=(0.0, 0.0)):
        self.sx, self.sy, self.base, self.deg, self.pivot, self.move = sx, sy, base, deg, pivot, move

    def __call__(self, p):
        x = self.base[0] + (p[0] - self.base[0]) * self.sx
        y = self.base[1] + (p[1] - self.base[1]) * self.sy
        a = math.radians(self.deg)
        c, s = math.cos(a), math.sin(a)
        dx, dy = x - self.pivot[0], y - self.pivot[1]
        return (self.pivot[0] + dx * c - dy * s + self.move[0], self.pivot[1] + dx * s + dy * c + self.move[1])

    def inverse(self, q):
        a = math.radians(-self.deg)
        c, s = math.cos(a), math.sin(a)
        dx, dy = q[0] - self.move[0] - self.pivot[0], q[1] - self.move[1] - self.pivot[1]
        x, y = self.pivot[0] + dx * c - dy * s, self.pivot[1] + dx * s + dy * c
        return (self.base[0] + (x - self.base[0]) / self.sx, self.base[1] + (y - self.base[1]) / self.sy)


def after(first, xf):
    """first, then xf: a point transform with .inverse."""
    def f(p):
        return xf(first(p))
    f.inverse = lambda q: first.inverse(xf.inverse(q))
    return f


def moved(dx, dy):
    f = lambda p: (p[0] + dx, p[1] + dy)  # noqa: E731
    f.inverse = lambda q: (q[0] - dx, q[1] - dy)
    return f


def m_(pts, side):
    return pts if side > 0 else [(MIR - x, y) for (x, y) in pts]


def X(pts, side, xf):
    return [xf(p) for p in m_(pts, side)]


# ------------------------------------------------------------------ NEW PARTS (viewer's left; mirrored)
# Seen from the front, a leg hauled up to the chest folds into three shapes: the knee cap on top
# (the fist clamps it), the sole of the foot right under it pointing at the viewer (the shin is
# behind it, end on), and round them both the underside of the thigh and the buttock, sweeping down
# and out to the rear at the bottom.
THIGH = [(56, 70), (45, 72.5), (36, 80), (30, 92), (28, 104), (30, 115), (36, 123), (46, 128),
         (60, 129.5), (74, 128), (84, 120), (84, 106), (77, 90), (68, 76)]
QUAD = [(52, 76), (41, 81), (34, 92), (32, 104), (36, 114), (46, 120), (56, 112), (60, 98), (60, 84)]
KNEE = [(39, 68), (42.5, 59), (50.5, 53.5), (61, 53), (69.5, 58), (73, 67), (71, 77), (63.5, 83.5), (52, 84),
        (43, 78.5)]
KNEE_CAP = [(46, 66), (52, 61), (61, 61), (66.5, 66), (64.5, 74), (56, 77.5), (48, 74)]
# the sole to the viewer, toes up (the approved seated foot's design, nearer): the ball of the foot
# broad under a row of toes, the big toe on the inside (toward the centre), the heel narrower
SOLE_BODY = [(48.5, 94), (46.5, 103), (47, 112), (50, 119.5), (55, 124), (61, 125), (66.5, 122.5),
              (70.5, 115), (72.5, 105), (72, 95), (67, 90.5), (53, 91)]
SOLE = [(53, 97), (51.5, 105), (53, 114), (57, 119.5), (63, 119), (67, 112), (68, 103), (65.5, 96), (59, 94.5)]
TOES = [((66.4, 89.2), 4.3), ((60.4, 87.6), 3.3), ((55.4, 88.0), 3.0), ((51.0, 89.6), 2.7), ((47.4, 92.4), 2.4)]
ARCH = [(50, 102), (51, 110), (54, 117)]
BAND_C = (87.5, 100.0)       # the mawashi hugging the bottom of the ball: between two ellipses
BAND_OUT = (60.0, 43.0)
BAND_IN = (54.0, 31.0)
# the forearm, from the elbow at his side up round the outside of the knee to the fist on top of it
ELBOW = (17.0, 96.0)
WRIST = (39.0, 66.0)
FIST_AT = (38.0, 40.0)              # hands.fist's (ox, oy): the fist over the top of the knee


def limb(p0, p1, r0, r1, bellies, xf, exposure=0.05):
    a, b = xf(p0), xf(p1)
    k = math.hypot(b[0] - a[0], b[1] - a[1]) / (math.hypot(p1[0] - p0[0], p1[1] - p0[1]) or 1.0)
    return FT.limb(a, b, r0 * k, r1 * k, exposure=exposure, bellies=[(t0, t1, r * k, o * k) for (t0, t1, r, o) in bellies])


def xf_scale(xf):
    a, b = xf((0.0, 0.0)), xf((10.0, 0.0))
    c = xf((0.0, 10.0))
    return (math.hypot(b[0] - a[0], b[1] - a[1]) + math.hypot(c[0] - a[0], c[1] - a[1])) / 20.0


def foot(cv, side, xf, sd):
    """One sole to the viewer: the body, then each toe its own keylined form along the top (the
    little toe first, the big toe last and in front), as the approved fist builds its fingers.
    Lit after the pose; the arch as an open line."""
    cv.stamp(sculpt(spoly(X(SOLE_BODY, side, xf)), [(spoly(X(SOLE, side, xf)), 2.0, 0.25)], sigma=3.5,
                    exposure=0.1), shadow=sd, under=1)
    k = xf_scale(xf)
    for (c, r) in TOES[::-1]:
        q = xf(c if side > 0 else (MIR - c[0], c[1]))
        toe = ellipse(q[0], q[1] - 0.3 * r, r * k, r * k * 1.12)
        cv.stamp(shade(toe, sigma=max(1.2, r * 0.55), exposure=0.12, cuts=L.CUTS, wrap=L.SKIN_WRAP))
    taper_line(cv.px, X(ARCH, side, xf), '3', only=SKINSET)


def _close(mask):
    """Fill the single-pixel holes a transformed pixel set can leave."""
    out = set(mask)
    for (x, y) in list(mask):
        for q in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
            if q not in out and sum(n in out for n in ((q[0] + 1, q[1]), (q[0] - 1, q[1]), (q[0], q[1] + 1),
                                                          (q[0], q[1] - 1))) >= 3:
                out.add(q)
    return out


def band_local():
    (cx, cy), (ro, qo), (ri, qi) = BAND_C, BAND_OUT, BAND_IN
    out = set()
    for y in range(int(cy), int(cy + qo) + 2):
        for x in range(int(cx - ro) - 1, int(cx + ro) + 2):
            o = ((x - cx) / ro) ** 2 + ((y - cy) / qo) ** 2
            i = ((x - cx) / ri) ** 2 + ((y - cy + 4) / qi) ** 2
            if o <= 1.0 and i > 1.0 and y >= cy + 16:
                out.add((x, y))
    return out


def band(xf):
    """The mawashi round the bottom of the ball, in the beanie's ribs: the region between two
    ellipses under the thighs, its ribs running across it (radial), lit after the pose."""
    cx, cy = BAND_C
    mask = set()
    loc = band_local()
    # transform the pixel set: sample the destination through the inverse, so nothing tears
    xs = [xf(p) for p in loc]
    x0, x1 = int(min(p[0] for p in xs)) - 2, int(max(p[0] for p in xs)) + 3
    y0, y1 = int(min(p[1] for p in xs)) - 2, int(max(p[1] for p in xs)) + 3
    for y in range(y0, y1):
        for x in range(x0, x1):
            lx, ly = xf.inverse((x, y))
            if (int(round(lx)), int(round(ly))) in loc:
                mask.add((x, y))
    idx = L.rank(mask, D.KNIT_DIST, sigma=4)

    def rib(x, y):
        lx, ly = xf.inverse((x, y))
        return math.degrees(math.atan2(ly - cy, lx - cx)) / 7.0
    return L.knit(idx, D.PATTERN, rib, D.KNIT)


def band_rope(xf):
    """The gold rope along the band's top edge (where it meets the thighs), a two-pixel twist."""
    (cx, cy), (ri, qi) = BAND_C, BAND_IN
    pts = []
    for a in range(24, 157, 4):
        t = math.radians(a)
        pts.append(xf((cx - ri * math.cos(t) * 1.0, cy - 4 + qi * math.sin(t) * 1.0)))
    path = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = L.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by)))
        if path and seg[0] == path[-1]:
            seg = seg[1:]
        path.extend(seg)
    part = {}
    for i, (x, y) in enumerate(path):
        ph = i % 3
        part[(x, y)] = ('Y', 'o', 'O')[ph]
        part[(x, y + 1)] = ('o', 'O', 'g')[ph]
    return part


# The apron blown out to the side by the fall (the reference's fluttering cloth): the approved navy
# apron with its light-blue border and the Fuji's snowcap, its gold fringe at the free end.
FLAG = [
    "...........kkkkkkkkkk",
    "........kkkUUUUUUUUUk",
    ".....kkkVVVVVVVVVVUUk",
    "..kkkXVVVVVVWWVVVVVUk",
    "kkXXXVVVVVWWWwVVVVUUk",
    "kXVVVVVVVWWWwwBVVVUk.",
    "kXVVVVVVBBXwBBBVVUUk.",
    "kXVVVVVBBBXBBBBBVUk..",
    "kBBBBBBBBBBBBBBBUUk..",
    "kkkkkkkkkkkkkkkkkk...",
]
FRINGE = [
    "..o",
    "Yoo",
    "..o",
    "Yoo",
    "..o",
    "Yoo",
    "..o",
    "Yoo",
]


def flag(at):
    """The flying apron with its top-right corner at `at` (it trails off to the viewer's left)."""
    x0 = int(round(at[0])) - len(FLAG[0]) + 1
    y0 = int(round(at[1]))
    part = {}
    for r, row in enumerate(FLAG):
        for c, ch in enumerate(row):
            if ch != '.':
                part[(x0 + c, y0 + r)] = ch
    for r, row in enumerate(FRINGE):
        for c, ch in enumerate(row):
            if ch != '.':
                part[(x0 - 3 + c, y0 + 1 + r)] = ch
    return part


# ------------------------------------------------------------------ THE TUCK
DEFAULT = dict(
    xf=None,               # Xf for the whole ball (hover rock, stretch, squash)
    body_dy=8,             # the approved torso's drop
    head=(0, 12),          # the head's (dx, dy) from its approved place: tucked down into the shoulders
    eyes='awake', mouth='grit', puff=0.0, jaw=0,
    grip=0.0,              # 0 fists clamped on the knees; 1 the hands flung off them (the impact)
    knee_dy=0.0,           # the legs pulled in tighter (-) or loosened (+)
)


def build(spec, canvas=None):
    s = dict(DEFAULT, **spec)
    xf = s['xf'] or Xf()
    cv = canvas or FT.FreeCanvas()
    sd = FT.shadow()
    bxf = after(moved(0, s['body_dy']), xf)                    # the torso and everything on it
    lxf = after(moved(0, s['knee_dy']), xf)                    # the legs

    # 1. the torso's own belt stays under the ball (the approved part, hidden by the legs)
    belt = D.knit_part_xf(spoly([bxf(p) for p in D.sym(D.BELT)]), 40.0, bxf, sigma=5)
    cv.stamp(belt, shadow=sd)

    # 2. the torso (the approved one form), squeezed between the thighs; its anatomy lines
    m, part = T.build(xf=bxf, a_pec=0.32, a_belly=0.45)
    cv.stamp(part, shadow=sd, under=1)
    T.lines(cv.px, xf=bxf)

    # 3. deltoids and the upper arms hanging at his sides
    for side in (1, -1):
        cv.stamp(sculpt(spoly(X(LB.UPPER, side, bxf)), [(spoly(X(p, side, bxf)), 2.2, 0.28)
                                                          for p in (LB.BICEPS, LB.TRICEPS)], sigma=4.5, exposure=0.04),
                 shadow=sd)
        cv.stamp(sculpt(spoly(X(LB.DELT, side, bxf)), [(spoly(X(p, side, bxf)), 2.6, 0.25)
                                                         for p in (LB.DELT_FRONT, LB.DELT_SIDE)], sigma=6.5, exposure=0.06),
                 shadow=sd, under=1)
        taper_line(cv.px, X(LB.ARM_LINE, side, bxf), 'k', taper_key='3', taper=0, only=SKINSET)

    # 4. the collar and chain on the chest
    cv.stamp(G.gold_chain_xf(bxf))
    cv.stamp(G.collar_xf(bxf), shadow=sd)

    # 5. the head, tucked down between the knees (laid on unsquashed)
    hx, hy = xf((CX, 30.0))
    hdx = int(round(hx - CX)) + s['head'][0]
    hdy = int(round(hy - 30.0)) + s['head'][1]
    hs = dict(FT.DEFAULT, body=(hdx, hdy), eyes=s['eyes'], mouth=s['mouth'], bubble=0, puff=s['puff'],
              jaw=s['jaw'])
    FT.head(cv, hs)

    # 6. the mawashi round the bottom of the ball, its rope, the apron flying off it; then the
    #    thighs' undersides, the soles under the knees, and the knees on top
    cv.stamp(band(xf), shadow=sd)
    cv.stamp(band_rope(xf))
    fa = xf((52.0, 126.0))
    fl = flag(fa)
    cloth = {q: k for q, k in fl.items() if k not in 'Yo'}
    cv.stamp(cloth, outline=False)
    cv.stamp({q: k for q, k in fl.items() if k in 'Yo'})
    for side in (1, -1):
        cv.stamp(sculpt(spoly(X(THIGH, side, lxf)), [(spoly(X(QUAD, side, lxf)), 3.0, 0.3)], sigma=6.0,
                        bulge=0.45, exposure=0.02, tilt=(0.0, 0.25)), shadow=sd, under=1)
    for side in (1, -1):
        foot(cv, side, lxf, sd)
    for side in (1, -1):
        cv.stamp(sculpt(spoly(X(KNEE, side, lxf)), [(spoly(X(KNEE_CAP, side, lxf)), 2.2, 0.35)], sigma=4.5,
                        exposure=0.1, tilt=(0.0, -0.3)), shadow=sd, under=1)

    # 7. the forearms coming up round the knees, the wraps, the fists clamped on top
    for side in (1, -1):
        e, w = X([ELBOW, WRIST], side, bxf)
        out = -side * 3.0
        fore = FT.limb(e, w, 10.0, 7.4, exposure=0.05, bellies=[(0.02, 0.5, 7.2, out), (0.12, 0.62, 6.2, -out)])
        cv.stamp(fore, shadow=sd, under=1)
        FT.crease(cv.px, e, w, 0.14, 0.6, -side * 0.6, taper=3)
        cv.stamp(anim.wrap_band(FT.wrap_at(e, w, 0.9, 8.4), side))
        # hands.fist mirrors itself for side -1: move each by what the pose does at its own centre
        c = (FIST_AT[0] + 13.5, FIST_AT[1] + 11.0)
        c = c if side > 0 else (MIR - c[0], c[1])
        d = bxf(c)
        ddx, ddy = d[0] - c[0], d[1] - c[1]
        ox = FIST_AT[0] + (ddx if side > 0 else -ddx)
        cv.stamp(HN.fist(side, int(round(ox)), int(round(FIST_AT[1] + ddy))), outline=False, shadow=sd)
    L.clean_lone(cv.px)
    return cv
