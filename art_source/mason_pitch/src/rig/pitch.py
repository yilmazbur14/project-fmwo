"""mason_pitch: the full Nugget Fastball sheet, 15 frames of 64x64 on mason_sheet's canvas (feet (32, 63)).

Built on the approved rig through fastball.py (the approval pass), so SET and RELEASE are the user-approved
frames pixel for pixel (build_full.py asserts it). Drawn throwing toward screen-left; the code mirrors it.

   0 READY          called shot: glove arm pointing at the batter, nugget in the other hand, smug grin
   1 STRETCH        hands together at the chest, nugget hidden, eyes narrowed
   2 KICK           lead knee rising, hands separating
   3 SET            (approved) knee up, nugget cocked behind his head  - badge / X frame
   4 RELEASE        (approved) arm whipped through, smear, nugget leaving low-left
   5 FOLLOW         follow-through, arm across his body, HYAH (held while a home run flies back)
   6 PUMP           RELEASE's body, nugget still in his hand, no smear, no streaks
   7 PUMP_HOLD      nugget held up by his face, wink and tongue ("gotcha"), finger wag
   8 CHANGE_A       changeup tell: no kick, rocked back, hand on hip, nugget pinched up by his face, pinky out, glint
   9 CHANGE_B       rocked forward, same grip
  10 CHANGE_SET     nugget drawn back low at the hip for a lob, grin           - badge frame
  11 CHANGE_RELEASE soft underhand lob, nugget floating off the fingertips, small puff, no smear
  12 BONK_A         forehead smacked: head snapped back, > < yelp (no nugget, no star: the code's ball and
                    nugget_bonk.png sit on top)
  13 BONK_B         reeling, dazed ring eyes, sweat drops
  14 BONK_C         shaking it off: scowl, hands coming back in toward STRETCH, shake lines
"""
import math
import sys
sys.dont_write_bytecode = True

import rig
import props
import nugprops as NP
import nugget_cast as NC
import fastball as FB
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP, RED, RED_HI,
                 YEL, YEL_MID, YEL_DEEP, KHAKI, KHAKI_DK, FACE_SHAD, FACE_LIT)
from props import limb, lines, star, sweat
from fastball import arm, arm_shadowed, leg, _claw, nug, fan, streaks


# ----------------------------------------------------------------------------- faces
def face_smug(c, fput):
    """called shot: heavy lids, eyes slid toward the batter (screen-left), a one-sided smirk"""
    rig._scalp(fput)
    for x in list(range(28, 31)) + list(range(33, 36)):
        fput(x, 17, BLACK)
        fput(x, 18, WHITE)
        fput(x, 19, WHITE)
    rig._pts(fput, [(28, 18), (28, 19), (33, 18), (33, 19)], BLACK)
    rig._pts(fput, [(29, 23), (30, 23), (31, 23), (32, 23), (33, 22), (34, 21)], BLACK)
    rig._pts(fput, [(30, 22), (31, 22), (32, 22), (33, 21)], WHITE)
    rig._pts(fput, [(29, 22), (34, 20)], BLACK)


def face_narrow(c, fput):
    """the stretch: eyes narrowed to slits under a black lid line, mouth set flat"""
    rig._scalp(fput)
    rig._pts(fput, [(27, 17), (28, 17), (29, 17), (30, 18), (36, 17), (35, 17), (34, 17), (33, 18)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)):
        fput(x, 19, WHITE)
    rig._pts(fput, [(28, 18), (29, 18), (34, 18), (35, 18)], FACE_SHAD)
    rig._pts(fput, [(29, 19), (34, 19)], BLACK)
    for x in range(30, 34):
        fput(x, 23, BLACK)


def face_innocent(c, fput):
    """the changeup: brows up, eyes wide and rolled up, lips pursed in a whistle - nothing to see here"""
    rig._scalp(fput)
    rig._pts(fput, [(28, 15), (29, 15), (30, 15), (33, 15), (34, 15), (35, 15)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)):
        for y in (17, 18, 19):
            fput(x, y, WHITE)
    rig._pts(fput, [(29, 17), (34, 17)], BLACK)
    rig._pts(fput, [(31, 22), (32, 22), (30, 23), (33, 23), (31, 24), (32, 24)], BLACK)
    rig._pts(fput, [(31, 23), (32, 23)], RED_HI)


def face_dazed(c, fput):
    """reeling: eyes gone to little rings, mouth wobbling"""
    rig._scalp(fput)
    for (cx, cy) in ((29, 18), (34, 18)):
        for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            fput(cx + dx, cy + dy, BLACK)
        fput(cx, cy, WHITE)
    rig._pts(fput, [(29, 23), (30, 22), (31, 23), (32, 22), (33, 23), (34, 22)], BLACK)


def face_scowl(c, fput):
    """shaking it off: brows slammed, eyes hard, teeth gritted"""
    rig._scalp(fput)
    rig._pts(fput, [(27, 16), (28, 16), (29, 17), (30, 17), (36, 16), (35, 16), (34, 17), (33, 17)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)):
        fput(x, 18, WHITE)
        fput(x, 19, WHITE)
    rig._pts(fput, [(30, 19), (33, 19)], BLACK)
    for x in range(29, 35):
        fput(x, 22, BLACK)
        fput(x, 24, BLACK)
        fput(x, 23, WHITE)
    rig._pts(fput, [(28, 23), (35, 23), (31, 23), (32, 23)], BLACK)


def face_lob(c, fput):
    """the lob: easy grin, eyes on the batter"""
    rig._scalp(fput)
    for x in list(range(28, 31)) + list(range(33, 36)):
        for y in (17, 18, 19):
            fput(x, y, WHITE)
    rig._pts(fput, [(28, 18), (28, 19), (33, 18), (33, 19)], BLACK)
    for y, (a, b) in {22: (28, 35), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    for x in range(29, 35):
        fput(x, 22, WHITE)
    rig._pts(fput, [(31, 24), (32, 24)], RED_HI)


for _n, _f in (('smug', face_smug), ('narrow', face_narrow), ('innocent', face_innocent),
               ('dazed', face_dazed), ('scowl', face_scowl), ('lob', face_lob)):
    rig.EXPRESSIONS[_n] = _f
rig.GOOGLY['left'] = ((-1, 0), (-1, 0))
rig.GOOGLY['up'] = ((0, -2), (0, -2))
rig.GOOGLY['reel'] = ((1, -2), (-1, 0))


# ----------------------------------------------------------------------------- props
def pinky_glint(x, y):
    """the changeup grip's glint, a tiny 4-point sparkle in his own black-outlined star style"""
    return NP.sparkle(x, y, 1)


def puff(cx, cy, r=2.6):
    """a soft cream puff, no keyline (effects carry none)"""
    def f(c):
        cur = getattr(c, 'cur', lambda x, y: None)
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                d = math.hypot(dx, dy)
                if d <= r and cur(cx + dx, cy + dy) is None:
                    c.put(cx + dx, cy + dy, WHITE if (dx + dy) < -1 else CREAM_HI)
    return f


def shake(local='head'):
    """head-shake lines either side of his head, black like his phone-shout lines"""
    return lines([[(8, 8), (5, 7)], [(7, 13), (4, 13)], [(55, 8), (58, 7)], [(56, 13), (59, 13)]], local=local)


def pinky(x, y, side=1):
    """a pinky crooked out of the grip: a 2-texel nub, keylined"""
    def f(c):
        pts = [(x, y), (x + side, y - 1)]
        m = props.limb_mask(pts, [1.3, 1.1])
        props.mask_draw(c, m, props.wing_colour)
    return f


# ----------------------------------------------------------------------------- poses
# 0 READY - called shot. Glove arm straight out at the batter (screen-left), nugget resting in the throwing hand.
READY = dict(
    body=(0, 0, 1.0, 1.0), shear=0.03,
    wing_r_mode='off', wing_l_mode='off',
    face='smug', googly='left', sym=False,
    over=[arm([(14, 38), (9, 36), (5, 35)], [3.0, 3.3, 3.5], grooves=[(3, 34), (4, 35)]),
          arm([(50, 38), (54, 43), (54, 48)], [3.0, 3.4, 3.8], grooves=[(56, 50), (55, 51)]),
          nug(54.0, 43.5, 17.0)],
)

# 1 STRETCH - hands together at the chest, nugget hidden in them, standing tall.
STRETCH = dict(
    body=(0, 0, 0.99, 1.03), head=(0, 1),
    wing_r_mode='off', wing_l_mode='off',
    face='narrow', googly='normal', sym=False,
    over=[arm_shadowed([(13, 39), (19, 43), (28, 42)], [3.0, 3.4, 3.8]),
          arm_shadowed([(50, 39), (44, 43), (35, 42)], [3.0, 3.4, 3.8]),
          arm([(31.5, 41), (31.5, 41)], [4.6, 4.6])],
)

# 2 KICK - lead knee rising, hands separating: glove arm reaching out, throwing hand swinging back and up.
KICK = dict(
    body=(1, 0, 0.99, 1.03), shear=0.05, head=(0, 1),
    wing_r_mode='off', wing_l_mode='off',
    foot_r=(-1, 0),
    sections={'leg_l': []},
    face='narrow', googly='in', sym=False,
    behind=[arm([(50, 37), (57, 33), (58, 26)], [3.0, 3.5, 3.9], grooves=[(58, 23), (59, 24)])],
    over=[arm([(14, 39), (10, 40), (6, 41)], [3.0, 3.3, 3.6], grooves=[(4, 41), (4, 42)]),
          leg([(25, 52), (19, 47), (17, 52)], [3.0, 3.0, 2.6]),
          _claw((17, 53), [(13, 58), (17, 59), (21, 58)]),
          nug(56.5, 21.0, 60.0)],
)

SET = FB.WINDUP
RELEASE = FB.RELEASE

# 5 FOLLOW - arm all the way through and down across him, lead foot planted, back foot up, still yelling.
FOLLOW = dict(
    body=(-2, 3, 1.05, 0.93), shear=-0.12, head=(-3, 3),
    wing_r_mode='off', wing_l_mode='off',
    foot_l=(4, 0), foot_r=(2, -2),
    face='hyah', googly='swing_l', sym=False,
    over=[arm([(13, 41), (8, 37), (6, 41)], [3.0, 3.4, 3.7], grooves=[(4, 42), (5, 43)]),
          arm_shadowed([(46, 39), (37, 46), (28, 51), (20, 54)], [3.0, 3.5, 3.9, 4.5], grooves=[(17, 55), (17, 56)])],
)

# 6 PUMP - RELEASE's body exactly; the nugget never leaves the hand.
PUMP = dict(RELEASE)
PUMP['behind'] = []
PUMP['over'] = [RELEASE['over'][0], RELEASE['over'][1], nug(23.5, 51.5, -40.0)]

# 7 PUMP_HOLD - "gotcha": nugget held up by his face, glove hand wagging a finger, wink and tongue.
PUMP_HOLD = dict(
    body=(0, 0, 1.0, 1.0), shear=0.04,
    wing_r_mode='off', wing_l_mode='off',
    face='aim', googly='in', sym=False,
    over=[arm([(14, 39), (8, 33), (8, 25)], [3.0, 3.3, 3.5], grooves=[(8, 22), (9, 22)]),
          arm([(50, 38), (57, 35), (56, 30)], [3.0, 3.4, 3.8], grooves=[(54, 28), (55, 28)]),
          nug(54.5, 27.0, -10.0)],
)

# 8/9 CHANGE_A/B - the changeup's tell: feet planted (no kick), glove hand on his hip, nugget pinched up beside
# his face with the pinky out and a glint; rocked back (A) then forward (B). Innocent whistle.
def _change(dx, shear, head, feet):
    hx = dx + rig.rh(shear * 23) + head[0]
    return dict(
        body=(dx, 0, 1.0, 1.0), shear=shear, head=head, foot_l=feet[0], foot_r=feet[1],
        wing_r_mode='off', wing_l_mode='off',
        face='innocent', googly='up', sym=False,
        over=[arm([(14 + dx, 39), (7 + dx, 44), (12 + dx, 49)], [3.0, 3.4, 3.6], grooves=[(13 + dx, 51), (14 + dx, 50)]),
              arm([(50 + dx, 38), (54 + dx, 39), (49 + hx, 34)], [3.0, 3.4, 3.6], grooves=[(48 + hx, 32), (49 + hx, 32)]),
              nug(45.5 + hx, 29.5, 30.0),
              pinky(52 + hx, 33, 1),
              pinky_glint(40 + hx, 23)],
    )


CHANGE_A = _change(3, 0.12, (1, 0), ((1, -2), (0, 0)))
CHANGE_B = _change(-3, -0.10, (-1, 1), ((0, 0), (-1, -2)))

# 10 CHANGE_SET - nugget drawn back low by the hip for the lob, glove arm aiming, easy grin.
CHANGE_SET = dict(
    body=(1, 0, 1.0, 1.0), shear=0.06,
    wing_r_mode='off', wing_l_mode='off',
    face='grin', googly='left', sym=False,
    over=[arm([(14, 39), (9, 37), (5, 37)], [3.0, 3.3, 3.5], grooves=[(3, 36), (4, 37)]),
          arm([(51, 41), (56, 47), (56, 52)], [3.0, 3.4, 3.8], grooves=[(58, 54), (57, 55)]),
          nug(55.0, 54.5, 80.0)],
)

# 11 CHANGE_RELEASE - soft underhand lob: arm swung forward and up across him, nugget floating off the
# fingertips up-left, a small puff under it. No smear.
CHANGE_RELEASE = dict(
    body=(-1, 1, 1.02, 0.97), shear=-0.05,
    wing_r_mode='off', wing_l_mode='off',
    foot_r=(1, -2),
    face='lob', googly='left', sym=False,
    over=[arm([(14, 40), (9, 44), (8, 49)], [3.0, 3.3, 3.6], grooves=[(7, 51), (8, 52)]),
          arm_shadowed([(49, 39), (42, 47), (31, 49), (22, 45)], [3.0, 3.4, 3.8, 4.2], grooves=[(19, 44), (19, 45)]),
          puff(13, 45, 3.0), puff(18, 48, 2.0),
          nug(11.5, 36.5, -20.0)],
)

# 12-14 BONK - the approval pass's bonk, minus the baked nugget and star (the code's ball and nugget_bonk.png).
BONK_A = dict(FB.BONKED)
BONK_A['over'] = [FB.BONKED['over'][0], FB.BONKED['over'][1], sweat([(17, 7)]), sweat([(47, 5)])]

BONK_B = dict(
    body=(-1, 1, 1.03, 0.97), shear=-0.08, head=(-2, 1),
    wing_r_mode='off', wing_l_mode='off',
    foot_r=(1, -3),
    face='dazed', googly='reel', sym=False,
    over=[arm([(13, 40), (7, 37), (4, 32)], [3.0, 3.4, 3.8], grooves=[(3, 30), (4, 30)]),
          arm([(50, 40), (55, 46), (57, 51)], [3.0, 3.4, 3.8], grooves=[(58, 53), (57, 54)]),
          sweat([(14, 6)]), sweat([(50, 3)])],
)

BONK_C = dict(
    body=(0, 0, 1.0, 1.0), shear=0.0,
    wing_r_mode='off', wing_l_mode='off',
    face='scowl', googly='normal', sym=False,
    over=[arm([(13, 39), (16, 45), (23, 46)], [3.0, 3.4, 3.7]),
          arm([(50, 39), (47, 45), (40, 46)], [3.0, 3.4, 3.7]),
          shake()],
)

FRAMES = [('ready', READY), ('stretch', STRETCH), ('kick', KICK), ('set', SET), ('release', RELEASE),
          ('follow', FOLLOW), ('pump', PUMP), ('pump_hold', PUMP_HOLD), ('change_a', CHANGE_A),
          ('change_b', CHANGE_B), ('change_set', CHANGE_SET), ('change_release', CHANGE_RELEASE),
          ('bonk_a', BONK_A), ('bonk_b', BONK_B), ('bonk_c', BONK_C)]
assert len(FRAMES) == 15


def render(pose):
    return NC.render_pose(pose)
