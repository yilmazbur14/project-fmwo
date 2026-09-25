"""Greyson's punching arms for the brawl, in SCREEN coordinates (the brawl is never flipped).

A punching arm is the approved flex delt on its shoulder, an upper arm and (for the fist) a
forearm traced as capsules along the pose's joints, shaded as the rig shades a limb (gr_muscle
Regions under tube forms, lit from the upper left, the rig's arm cuts), plus either the approved
'idle' fist (knuckles to the player) at the wrist, or the cannon gauntlet (gf_cannon) from the
elbow to its striking end.

    fist_arm(d, elbow, fist)                   his RIGHT arm (screen left) throwing a punch
    cannon_arm(d, elbow, gauntlet, face)       his LEFT arm (screen right), the gauntlet
Both return the parts to stamp, in order, and the anchors they carry. The shoulder sits where
the approved torso puts it, dropped d rows with the crouch.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402
from gr_muscle import Form, Region, RegionLayer  # noqa: E402

K, G, P = B.K, B.G, B.P
gr_arms, gr_hands, gf_cannon = G.gr_arms, G.gr_hands, G.gf_cannon

SHOULDER_L = (31.0, 56.5)            # his right shoulder joint (screen left), standing
SHOULDER_R = (K.AX - 31.0, 56.5)     # his left shoulder joint (screen right)
UPPER_SPEC = (1.6, 2.8, 2, 2)
FORE_SPEC = (1.5, 2.6, gr_arms.LINE, 3)
DELT_SPEC = gr_arms.FLEX_SPEC['delt']


def _delt(side, d):
    pts = gr_arms.FLEX['delt']
    form = gr_arms.FLEX_FORMS['delt']
    if side:
        pts, form = K.mpts(pts), gr_arms._mirror_form(form)
    cx, cy, rx, ry = form.ell
    return ([(x, y + d) for (x, y) in pts], Form(ellipsoid=(cx, cy + d, rx, ry), flat=form.flat))


def _shade(regions, base_form):
    return RegionLayer(base_form, regions).shade(cuts=gr_arms.CUTS)[0]


def upper_layer(side, d, elbow, r=(7.0, 6.6), delt=True):
    """The delt and the upper arm from the shoulder (dropped d) to `elbow` (screen)."""
    sh = SHOULDER_R if side else SHOULDER_L
    sh = (sh[0], sh[1] + d)
    regs = []
    if delt:
        dp, df = _delt(side, d)
        regs.append(Region('delt', K.poly(dp), amp=DELT_SPEC[0], round_px=DELT_SPEC[1],
                           cast=DELT_SPEC[2], depth=DELT_SPEC[3], form=df))
    up_form = Form(axis=[sh, elbow], r=r[0])
    regs.append(Region('upper', K.poly(P.capsule(sh, elbow, r[0], r[1])), amp=UPPER_SPEC[0],
                       round_px=UPPER_SPEC[1], cast=UPPER_SPEC[2], depth=UPPER_SPEC[3], form=up_form))
    return _shade(regs, up_form)


def forearm_layer(elbow, wrist, r=(6.2, 5.2)):
    f = Form(axis=[elbow, wrist], r=r[0])
    reg = Region('forearm', K.poly(P.capsule(elbow, wrist, r[0], r[1])), amp=FORE_SPEC[0],
                 round_px=FORE_SPEC[1], cast=FORE_SPEC[2], depth=FORE_SPEC[3], form=f)
    return _shade([reg], f)


def fist_part(centre, fist_map='idle'):
    """The approved fist (left-hand map: his right fist) placed with its CENTRE on `centre`."""
    f = gr_hands.fist(fist_map, 0, centre)
    xs = [x for (x, y) in f]
    ys = [y for (x, y) in f]
    c = ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
    cx, cy = int(round(centre[0])), int(round(centre[1]))
    return {(x + cx - c[0], y + cy - c[1]): k for (x, y), k in f.items()}


def fist_arm(d, elbow, fist, fist_map='idle', wrist_back=4.0, upper_r=(7.0, 6.6)):
    """His right arm (screen left) throwing: [(part, outline)] and the fist's centre. The
    forearm runs from the elbow to a wrist `wrist_back` short of the fist's centre."""
    ex, ey = elbow
    fx, fy = fist
    L = math.hypot(fx - ex, fy - ey) or 1.0
    wrist = (fx - (fx - ex) / L * wrist_back, fy - (fy - ey) / L * wrist_back)
    parts = [(K.despeckle(upper_layer(0, d, elbow, upper_r)), True),
             (K.despeckle(forearm_layer(elbow, wrist)), True),
             (fist_part(fist, fist_map), False)]
    return parts, (int(round(fx)), int(round(fy)))


def cannon_arm(d, elbow, gauntlet, face=0.3, upper_r=(7.0, 6.6), delt=True):
    """His left arm (screen right) with the gauntlet: [(part, outline)] and the cannon part
    (for the bore's centre)."""
    cn = gf_cannon.cannon(elbow, gauntlet, face=face)
    parts = [(K.despeckle(upper_layer(1, d, elbow, upper_r, delt)), True), (cn, True)]
    return parts, cn


def glow(cn, keys=('z', 'Z')):
    """The muzzle glowing: the bore's dark face lit from inside in his own palette (the eyes'
    pale blue round a white-hot centre), in place."""
    pts = [p for p, k in cn.items() if k in keys]
    if not pts:
        return cn
    xs = [x for (x, y) in pts]
    ys = [y for (x, y) in pts]
    cx, cy = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0
    rx, ry = max(1.0, (max(xs) - min(xs)) / 2.0 + 0.5), max(1.0, (max(ys) - min(ys)) / 2.0 + 0.5)
    for (x, y) in pts:
        e = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        cn[(x, y)] = 'W' if e < 0.30 else 'o' if e < 0.70 else 'O'
    return cn
