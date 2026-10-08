"""Mason - Nugget Fastball approval pass (scratch only, never writes into Assets/).

Built on the approved rig (rig.py / props.py / nugprops.py, copied unchanged from art_source and
checked to reproduce all 19 frames of the live mason_sheet.png pixel for pixel), so his body, head,
feet, palette and light are his own. Only the poses, two expressions and the props are new.

  windup   leg kick: lead (screen-left) knee up, nugget cocked up behind his head on the throwing side
  release  stride planted wide, arm whipped through over the top, nugget leaving the hand
  bonked   the parried nugget comes back and bonks him on the forehead
"""
import math
import sys
sys.dont_write_bytecode = True

import rig
import props
import nugprops as NP
import nugget_cast as NC          # registers face 'shout_up'; render_pose() handles 'behind'
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP, RED, RED_HI,
                 YEL, YEL_MID, YEL_DEEP, KHAKI, KHAKI_DK, FACE_SHAD)
from props import limb, lines, star, sweat

GLINT = props.GLINT


# ----------------------------------------------------------------------------- faces
def face_aim(c, fput):
    """game face: brows slammed down, one eye squinted along the aim, tongue poked out of the
    corner of a determined grin"""
    rig._scalp(fput)
    rig._pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    # left eye squinted shut along the aim, right eye wide on the target
    rig._pts(fput, [(28, 19), (29, 19), (30, 19)], BLACK)
    rig._pts(fput, [(28, 18), (29, 18), (30, 18)], rig.FACE_LIT)
    for x in (33, 34, 35):
        fput(x, 18, WHITE)
        fput(x, 19, WHITE)
    rig._pts(fput, [(34, 19), (34, 18)], BLACK)
    # determined grin, teeth clenched, tongue out of the left corner
    for x in range(29, 36):
        fput(x, 22, BLACK)
    rig._pts(fput, [(30, 23), (31, 23), (32, 23), (33, 23), (34, 23)], BLACK)
    rig._pts(fput, [(30, 22), (31, 22), (32, 22), (33, 22), (34, 22)], WHITE)
    rig._pts(fput, [(35, 21), (29, 23)], BLACK)
    rig._pts(fput, [(28, 23), (28, 24), (29, 24)], RED_HI)
    rig._pts(fput, [(27, 23), (27, 24), (28, 25), (29, 25), (30, 24)], BLACK)


def face_hyah(c, fput):
    """the release yell: brows down, pupils down on the target, mouth wide open"""
    rig._scalp(fput)
    rig._pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)):
        fput(x, 18, WHITE)
        fput(x, 19, WHITE)
    rig._pts(fput, [(29, 19), (34, 19)], BLACK)
    for y, (a, b) in {21: (28, 35), 22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    for x in range(29, 35):
        fput(x, 21, WHITE)
    rig._pts(fput, [(30, 24), (31, 24), (32, 24), (33, 24), (31, 25), (32, 25)], RED_HI)


def face_bonked(c, fput):
    """bonked, not beaten: eyes squeezed into > <, brows flung up, mouth open in a yelp with the
    tongue out (X eyes are his KO face, so they stay out of a single bonk)"""
    rig._scalp(fput)
    rig._pts(fput, [(28, 15), (29, 15), (34, 15), (35, 15)], BLACK)
    rig._pts(fput, [(28, 17), (29, 18), (30, 18), (28, 19)], BLACK)
    rig._pts(fput, [(35, 17), (34, 18), (33, 18), (35, 19)], BLACK)
    for y, (a, b) in {21: (29, 34), 22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    for x in range(30, 34):
        fput(x, 21, WHITE)
    rig._pts(fput, [(30, 24), (31, 24), (32, 24), (31, 25), (32, 25), (32, 23), (31, 23)], RED_HI)


rig.EXPRESSIONS['aim'] = face_aim
rig.EXPRESSIONS['hyah'] = face_hyah
rig.EXPRESSIONS['bonked'] = face_bonked
# googly pupils are loose costume eyes; only offsets that keep clear of the rim are legal
rig.GOOGLY['bonk'] = ((-2, -1), (1, -2))
rig.GOOGLY['flung'] = ((-1, -2), (1, -2))
for _k in ('bonk', 'flung'):
    _l, _r = rig.GOOGLY[_k]
    assert rig._googly_clean(rig.PLUS, _l) and rig._googly_clean(rig.EX, _r), _k


# ----------------------------------------------------------------------------- pieces
def khaki_colour(x, y, val):
    v = props.cyl_lum(val)
    return KHAKI if v > -0.05 else KHAKI_DK


def leg(pts, radii):
    """a khaki trouser leg as its own outlined piece (abs coords)"""
    return limb(pts, radii, colour=khaki_colour, frame='abs')


def claw(heel, toes):
    """a lifted chicken foot seen from the front, three toes hanging (abs coords)"""
    return NC.__dict__.get('sole_foot', None) or _claw(heel, toes)


def _claw(heel, toes):
    def f(c):
        m = {}
        for tip in toes:
            mm = props.limb_mask([heel, tip], [2.6, 1.8])
            for k, v in mm.items():
                if k not in m or v[0] < m[k][0]:
                    m[k] = v
        pad = props.limb_mask([heel, (heel[0], heel[1] + 0.5)], [3.4, 3.4])
        for k, v in pad.items():
            if k not in m or v[0] < m[k][0]:
                m[k] = v
        props.mask_draw(c, m, props.yellow_colour)
    return f


def arm(pts, radii, grooves=()):
    return limb(pts, radii, frame='abs', grooves=grooves)


def held_nugget(cx, cy, a=-15.0, rx=4.3, ry=3.3):
    return NP.prop(lambda c: [NP.nugget_part(cx, cy, rx, ry, math.radians(a),
                                             [(110, -0.18), (-40, 0.10), (200, 0.08)],
                                             [(0, 0), (2, 1)])])


def smear(poly_pts, col=WHITE, edge=CREAM_HI):
    """an anime smear: a filled crescent with no keyline (effects carry none), lit edge inside"""
    def f(c):
        line, inter = rig.raster(poly_pts)
        cur = getattr(c, 'cur', lambda x, y: None)
        for (x, y) in inter | line:
            if cur(x, y) is None:
                c.put(x, y, col)
    return f


def dots(pts, col):
    def f(c):
        for p in pts:
            c.put(p[0], p[1], col)
    return f


import nugget as NUG


def nug(cx, cy, rot_deg=17.0):
    """the fastball nugget itself (nugget.py), the same pixels the projectile sheet uses"""
    def f(c):
        NUG.paint(c.put, cx, cy, math.radians(rot_deg))
    return f


def arm_shadowed(pts, radii, grooves=(), drop=2):
    """an arm laid across his own body: the arm, plus a contact shadow `drop` px under it on the
    body (one ramp step down), so cream-on-cream stays two shapes at 3x"""
    draw = arm(pts, radii, grooves=grooves)
    def f(c):
        m = props.limb_mask(pts, radii)
        for (x, y) in m:
            for d in range(1, drop + 1):
                q = (x, y + d)
                if q in m or q not in c.inter:
                    continue
                col = c.cur(*q)
                if col in rig.STEP and col != BLACK:
                    c.put(q[0], q[1], rig.STEP[col])
        draw(c)
    return f


def burst(cx, cy, r=6, core=YEL, tips=WHITE):
    """comic impact: an 8-spoke star, white spokes over a yellow core, no keyline"""
    def f(c):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                ax, ay = abs(dx), abs(dy)
                d = math.hypot(dx, dy)
                main = (ax == 0 and ay <= r) or (ay == 0 and ax <= r)
                diag = (ax == ay and d <= r * 0.75)
                thick = (ax <= 1 and ay <= r - 2) or (ay <= 1 and ax <= r - 2)
                if d <= 2.2:
                    c.put(cx + dx, cy + dy, core)
                elif main or diag or thick:
                    c.put(cx + dx, cy + dy, tips)
        c.put(cx, cy, WHITE)
    return f


# ----------------------------------------------------------------------------- poses
# 1. WIND-UP: lead knee up, nugget cocked high behind his head, glove arm pointing at the target.
WINDUP = dict(
    body=(1, 0, 0.98, 1.04), shear=0.09, head=(0, 1),
    wing_r_mode='off', wing_l_mode='off',
    foot_r=(-2, 0),
    sections={'leg_l': []},
    face='aim', googly='in', sym=False,
    behind=[arm([(50, 37), (59, 28), (59, 18), (55, 11)], [3.0, 3.5, 3.9, 4.3], grooves=[(53, 9), (54, 10)])],
    over=[arm([(14, 39), (9, 36), (5, 34)], [3.0, 3.4, 3.7], grooves=[(5, 32), (6, 33)]),
          leg([(25, 52), (16, 42), (13, 48)], [3.0, 3.0, 2.6]),
          _claw((13, 49), [(9, 54), (13, 55), (17, 54)]),
          nug(53.5, 7.0, 17.0)],
)


def fan(pivot, r_mid, half_w, a0, a1, tail=CREAM_HI, head=WHITE):
    """anime arm smear: a band around `pivot` at radius r_mid, from angle a0 (thin tail) to a1
    (full width, where the hand is now). Degrees, screen-clockwise. No keyline."""
    def f(c):
        cur = getattr(c, 'cur', lambda x, y: None)
        px, py = pivot
        R = int(r_mid + half_w + 2)
        for y in range(int(py) - R, int(py) + R + 1):
            for x in range(int(px) - R, int(px) + R + 1):
                dx, dy = x + 0.5 - px, y + 0.5 - py
                r = math.hypot(dx, dy)
                a = math.degrees(math.atan2(dy, dx))
                t = (a - a0) / (a1 - a0)
                if not (0.0 <= t <= 1.0):
                    continue
                w = half_w * (t ** 0.8)
                if abs(r - r_mid) <= w and cur(x, y) is None:
                    c.put(x, y, head if t > 0.35 else tail)
    return f


def streaks(segs, col=WHITE):
    return lines(segs, col=col)


# 2. RELEASE: arm whipped over the top and through across his body (the smear shows its path round
#    his right side), lead foot planted, back foot off the mat, nugget out of the hand low-left.
RELEASE = dict(
    body=(-1, 2, 1.05, 0.94), shear=-0.10, head=(-2, 2),
    wing_r_mode='off', wing_l_mode='off',
    foot_l=(4, 0), foot_r=(3, -4),
    face='hyah', googly='swing_l', sym=False,
    behind=[fan((47.0, 37.0), 13.0, 3.8, -105.0, 80.0)],
    over=[arm([(13, 40), (7, 37), (4, 40)], [3.0, 3.4, 3.7], grooves=[(2, 41), (3, 42)]),
          arm_shadowed([(47, 37), (39, 44), (31, 49), (25, 51)], [3.0, 3.5, 3.9, 4.6], grooves=[(22, 52), (22, 53)]),
          streaks([[(17, 50), (22, 48)], [(18, 54), (23, 52)], [(15, 58), (19, 57)]]),
          nug(10.5, 56.5, -40.0)],
)

# 3. BONKED: the parried nugget comes back and bonks him on the forehead.
BONKED = dict(
    body=(1, 1, 1.03, 0.97), shear=0.12, head=(2, -1),
    wing_r_mode='off', wing_l_mode='off',
    foot_l=(-1, -3),
    face='bonked', googly='bonk', sym=False,
    over=[arm([(50, 38), (55, 33), (58, 28)], [3.0, 3.5, 4.0], grooves=[(58, 25), (59, 26)]),
          arm([(13, 40), (8, 44), (5, 49)], [3.0, 3.4, 3.8], grooves=[(4, 51), (5, 51)]),
          burst(44, 11, 6),
          streaks([[(48, 8), (50, 6)], [(50, 11), (52, 10)]]),
          nug(55.5, 8.0, 75.0),
          star(10, 4), star(2, 13), sweat([(17, 7)])],
)

FRAMES = [('windup', WINDUP), ('release', RELEASE), ('bonked', BONKED)]


def render(pose):
    return NC.render_pose(pose)
