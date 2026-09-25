"""Danny's evolved sumo form, redesign v2: the idle ready stance (frame 0).

176x144, anchor (88, 144), soles' keyline on row 143. Built back to front. The torso is one form with
its muscles sculpted on it; each limb is one form with its own muscles; every part cuts its black
keyline into what is behind it, and open lines draw the anatomy inside the forms.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sumo_lib import (Canvas, spoly, mirror_pts, stats, view, dump, patch)  # noqa: E402,F401
import sumo_lib as L  # noqa: E402
import face as F  # noqa: E402
import gear as G  # noqa: E402
import hands as HN  # noqa: E402
import limbs as LB  # noqa: E402
import torso as T  # noqa: E402

CX = 87.5
SHADOW = (2, 3)          # cast-shadow offset: light from the upper left
ANKLE_WRAPS = True


def sym(left):
    right = mirror_pts(left[::-1])
    return left + right[1:-1] if left[0][0] == CX else left + right


# ---------------------------------------------------------------- HEAD AND BELT GEOMETRY
FACE = [(87.5, 8), (77, 8.5), (68.5, 11), (64, 16), (62, 23), (61.3, 30), (61.8, 36.5), (63.5, 42),
        (66.5, 46.5), (71, 49.5), (77, 51.3), (82.5, 52), (87.5, 52.2)]
CROWN = [(87.5, 2.5), (78.5, 2.9), (71, 4.7), (65.8, 7.7), (62.2, 11.8), (60.2, 16), (59.5, 20.5), (87.5, 20.5)]
CUFF = [(87.5, 18.5), (58.5, 18.5), (58, 24), (58.4, 30), (59.4, 35), (61.5, 38), (64.3, 35.8), (64.8, 29.8),
        (69, 27.2), (77, 26.3), (87.5, 26)]
BELT = [(87.5, 91), (62, 91), (50, 91.5), (46, 94.5), (45, 101), (46.5, 106.5), (60, 109), (87.5, 110)]


# ---------------------------------------------------------------- KNIT
KNIT = {'L': 'uvwx', 'B': 'UVBX'}      # light-blue and blue stripe ramps, dark -> light
KNIT_DIST = (0.08, 0.22, 0.5, 0.2)
PATTERN = 'BBLLL'


def row_span(pixels):
    rows = {}
    for (x, y) in pixels:
        lo, hi = rows.get(y, (x, x))
        rows[y] = (min(lo, x), max(hi, x))
    return rows


def meridians(pixels, rref, offset=1.0, cx=CX, floor=0.62):
    """Stripe position for a knit wrapped round a dome or cylinder: equal steps in angle, so the ribs
    crowd together towards the sides and converge where the shape narrows. floor stops the
    convergence at that fraction of the widest row, so the ribs over the crown stay at least a
    pixel wide instead of breaking into a checker."""
    rows = row_span(pixels)
    widest = max((hi - lo + 1) / 2.0 for lo, hi in rows.values())

    def f(x, y):
        lo, hi = rows[y]
        r = max((hi - lo + 1) / 2.0, floor * widest)
        t = max(-1.0, min(1.0, (x - cx) / r))
        return math.asin(t) * rref + offset
    return f


def knit_part(mask, rref, dist=KNIT_DIST, **kw):
    return L.knit(L.rank(mask, dist, **kw), PATTERN, meridians(mask, rref), KNIT)


def knit_part_at(mask, rref, dx, dist=KNIT_DIST, **kw):
    """The knit on a part that has been moved sideways by dx (the ribs stay centred on it)."""
    return L.knit(L.rank(mask, dist, **kw), PATTERN, meridians(mask, rref, cx=CX + dx), KNIT)


def knit_part_xf(mask, rref, xf, dist=KNIT_DIST, **kw):
    """The knit on a band that a pose has turned: each pixel takes the stripe of the point it came
    from, so the ribs lean with the band instead of standing plumb."""
    inv = xf.inverse
    src = {q: inv(q) for q in mask}
    rows = {}
    for (x0, y0) in src.values():
        yy = int(round(y0))
        lo, hi = rows.get(yy, (x0, x0))
        rows[yy] = (min(lo, x0), max(hi, x0))

    def f(x, y):
        x0, y0 = src[(x, y)]
        yy = int(round(y0))
        if yy not in rows:
            yy = min(rows, key=lambda r: abs(r - yy))
        lo, hi = rows[yy]
        r = (hi - lo + 1) / 2.0
        t = max(-1.0, min(1.0, (x0 - CX) / r))
        return math.asin(t) * rref + 1.0
    return L.knit(L.rank(mask, dist, **kw), PATTERN, f, KNIT)


# ---------------------------------------------------------------- BUILD
# The build is in stages so a second pose can swap the arms and the face and keep the rest.
def stage_legs(cv):
    """Calves, thighs over the knees, feet, and the ankle wraps over the instep's top edge (the
    lower leg is short, so the wrap goes where the calf meets the foot and hides neither)."""
    for side in (1, -1):
        cv.stamp(LB.calf(side))
    for side in (1, -1):
        cv.stamp(LB.thigh(side), shadow=SHADOW)
        LB.leg_lines(cv.px, side)
    for side in (1, -1):
        cv.stamp(LB.foot(side), shadow=SHADOW)
        LB.toes(cv.px, side)
        if ANKLE_WRAPS:
            cv.stamp(LB.ankle_wrap(side))


def stage_belt(cv):
    """The mawashi band in the beanie's knit, the apron hanging from it, the rope."""
    cv.stamp(knit_part(spoly(sym(BELT)), 40.0, sigma=5), shadow=SHADOW)
    cv.stamp(G.apron(), shadow=SHADOW)
    cv.stamp(G.fringe())
    cv.stamp(G.rope(), shadow=SHADOW)


def stage_torso(cv):
    """The torso: one form, its belly riding over the belt."""
    m, part = T.build(a_pec=0.32, a_belly=0.45)
    cv.stamp(part, shadow=SHADOW, under=1)
    T.lines(cv.px)


def stage_arms_ready(cv):
    """The ready stance's arms: upper arm, deltoid cap over it, forearm, wrap, fist."""
    for side in (1, -1):
        cv.stamp(LB.upper_arm(side), shadow=SHADOW)
        cv.stamp(LB.deltoid(side), shadow=SHADOW, under=1)
        cv.stamp(LB.forearm(side), shadow=SHADOW)
        LB.arm_lines(cv.px, side)
        cv.stamp(HN.wrap(side), shadow=SHADOW)
        cv.stamp(HN.fist(side), outline=False, shadow=SHADOW)


def stage_neck(cv):
    """The gold chain on the pecs, and the collar scrap it hangs from."""
    cv.stamp(G.gold_chain())
    cv.stamp(G.collar(), shadow=SHADOW)


def stage_head(cv, features=None, bubble=True):
    """The face's cel shapes and features, then the beanie pulled down over the whole skull.
    features: a function (cv) that draws the eyes, nose and mouth; default the sleepy face."""
    cv.stamp(F.face_base(spoly(sym(FACE))), shadow=SHADOW)
    if features is None:
        F.features(cv, bubble_at=None)
    else:
        features(cv)
    crown = spoly(sym(CROWN))
    cv.stamp(knit_part(crown, 27.0, sigma=9), shadow=SHADOW)
    cv.stamp(knit_part(spoly(sym(CUFF), 1), 27.0, sigma=4))
    if bubble:
        cv.stamp(F.bubble(97.0, 41.5, r=4.4))


def build():
    cv = Canvas()
    stage_legs(cv)
    stage_belt(cv)
    stage_torso(cv)
    stage_arms_ready(cv)
    stage_neck(cv)
    stage_head(cv)
    L.clean_lone(cv.px)
    return cv


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '.'
    os.makedirs(out, exist_ok=True)
    im = build().image()
    im.save(os.path.join(out, 'v2_f0.png'))
    view(im, 4, os.path.join(out, 'v2_f0_4x.png'))
    print(stats(im))
