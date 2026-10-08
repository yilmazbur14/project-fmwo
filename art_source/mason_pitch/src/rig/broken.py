"""mason_broken: his knockdown / Break, 7 frames of 64x64 on mason_sheet's canvas (feet anchor (32, 63)).
Every pixel of him stays inside texels x 6..58 (his standing footprint and hurtbox).

  0 REEL        staggering back from the bonk, arms windmilling, eyes gone to rings
  1 TOTTER      tipping backward, one foot kicked up
  2 SIT_IMPACT  slammed onto his rump, legs splayed forward (soles to camera), dust
  3 BOUNCE      a small squash-bounce off the mat, dust spreading
  4 DAZED_A     sitting, head lolling left, tongue out          } the loop
  5 DAZED_B     sitting, head lolling right, tongue out         }
  6 DAZED_C     a twitch (optional): head up, a foot jerks, blink
Distinct from his defeat KO (mason_sheet 14, lying flat with X eyes): he sits up, ring eyes, no X.
"""
import math
import sys
sys.dont_write_bytecode = True

import rig
import props
import nugget_cast as NC
import frames as RF
import fastball as FB
import pitch as PT
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP, RED_HI, KHAKI, KHAKI_DK, FACE_SHAD)
from props import limb, lines, sweat
from fastball import arm, leg


def face_thud(c, fput):
    """the landing: ring eyes, mouth dropped open"""
    rig._scalp(fput)
    for (cx, cy) in ((29, 18), (34, 18)):
        for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            fput(cx + dx, cy + dy, BLACK)
        fput(cx, cy, WHITE)
    for y, (a, b) in {21: (30, 33), 22: (29, 34), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    rig._pts(fput, [(31, 23), (32, 23)], RED_HI)


def face_daze_tongue(c, fput):
    """sitting dazed: ring eyes, jaw hanging, tongue lolling (the KO's mouth, without the KO's X eyes)"""
    rig._scalp(fput)
    for (cx, cy) in ((29, 18), (34, 18)):
        for (dx, dy) in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            fput(cx + dx, cy + dy, BLACK)
        fput(cx, cy, WHITE)
    for y, (a, b) in {21: (29, 34), 22: (29, 34), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    rig._pts(fput, [(31, 23), (32, 23), (33, 23), (31, 24), (32, 24), (33, 24), (32, 25), (33, 25)], RED_HI)
    rig._pts(fput, [(34, 24), (34, 25)], BLACK)


def face_blink(c, fput):
    """the twitch: eyes snapped shut, tongue still out"""
    rig._scalp(fput)
    rig._pts(fput, [(28, 18), (29, 18), (30, 18), (33, 18), (34, 18), (35, 18)], BLACK)
    for y, (a, b) in {21: (29, 34), 22: (29, 34), 23: (29, 34), 24: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    rig._pts(fput, [(31, 23), (32, 23), (33, 23), (31, 24), (32, 24), (33, 24), (32, 25), (33, 25)], RED_HI)
    rig._pts(fput, [(34, 24), (34, 25)], BLACK)


rig.EXPRESSIONS['thud'] = face_thud
rig.EXPRESSIONS['daze_tongue'] = face_daze_tongue
rig.EXPRESSIONS['blink'] = face_blink


def dust(cx, cy, r, ring=False):
    """a dust puff on the mat in his own creams, no keyline; ring=True hollows it as it spreads"""
    def f(c):
        cur = getattr(c, 'cur', lambda x, y: None)
        for dy in range(-int(r) - 1, int(r) + 2):
            for dx in range(-int(r) - 1, int(r) + 2):
                d = math.hypot(dx * 0.8, dy * 1.25)
                if d > r or (ring and d < r - 1.6):
                    continue
                if cur(cx + dx, cy + dy) is not None:
                    continue
                col = WHITE if (dx * 0.7 + dy) < -r * 0.4 else (CREAM_HI if (dx * 0.7 + dy) < r * 0.3 else CREAM_MID)
                c.put(cx + dx, cy + dy, col)
    return f


def sole(heel, toes):
    return RF.sole_foot(heel, toes)


def arcs(segs):
    """windmill motion arcs, white, no keyline"""
    return lines(segs, col=WHITE)


# 0 REEL
REEL = dict(
    body=(1, 0, 1.0, 1.0), shear=0.12, head=(1, 0),
    wing_r_mode='off', wing_l_mode='off',
    foot_l=(0, -3),
    face='dazed', googly='reel', sym=False,
    over=[arm([(50, 38), (53, 31), (52, 24)], [3.0, 3.4, 3.7], grooves=[(51, 21), (52, 21)]),
          arm([(14, 40), (11, 45), (12, 50)], [3.0, 3.4, 3.6], grooves=[(11, 52), (12, 53)]),
          arcs([[(56, 25), (57, 29), (56, 33)], [(7, 46), (7, 50), (8, 53)]]),
          sweat([(14, 6)])],
)

# 1 TOTTER - tipping back: weight on the left foot, the right leg kicked up toward the camera (sole showing).
TOTTER = dict(
    body=(-1, 0, 0.99, 1.02), shear=-0.10, head=(-2, 0),
    wing_r_mode='off', wing_l_mode='off',
    foot_l=(2, 0),
    sections={'leg_r': []},
    face='thud', googly='up', sym=False,
    over=[arm([(13, 39), (10, 32), (11, 25)], [3.0, 3.4, 3.7], grooves=[(10, 22), (11, 22)]),
          arm([(48, 39), (52, 33), (52, 26)], [3.0, 3.4, 3.7], grooves=[(51, 23), (52, 23)]),
          leg([(37, 52), (43, 53), (47, 51)], [3.0, 3.0, 2.8]),
          sole((47, 52), [(44, 46), (48, 45), (52, 47)])],
)

# 2 SIT_IMPACT - slammed down on his rump, legs splayed forward, soles to the camera, dust out both sides.
SIT = dict(
    body=(0, 9, 1.06, 0.86), head=(0, 1),
    wing_r_mode='off', wing_l_mode='off',
    feet_detached=True,
    face='thud', googly='crossed', sym=False,
    over=[arm([(12, 47), (9, 52), (10, 57)], [3.0, 3.3, 3.5]),
          arm([(51, 47), (54, 52), (53, 57)], [3.0, 3.3, 3.5]),
          sole((20, 59), [(15, 53), (18, 51), (22, 52)]),
          sole((43, 59), [(41, 52), (45, 51), (48, 53)]),
          dust(10, 61, 3.0), dust(53, 61, 3.0), sweat([(12, 10)]), sweat([(50, 9)])],
)

# 3 BOUNCE - a small squash-bounce up off the mat
BOUNCE = dict(
    body=(0, 7, 1.04, 0.90), head=(0, 0),
    wing_r_mode='off', wing_l_mode='off',
    feet_detached=True,
    face='thud', googly='crossed', sym=False,
    over=[arm([(12, 46), (9, 50), (9, 55)], [3.0, 3.3, 3.5]),
          arm([(51, 46), (54, 50), (54, 55)], [3.0, 3.3, 3.5]),
          sole((20, 58), [(15, 52), (18, 50), (22, 51)]),
          sole((43, 58), [(41, 51), (45, 50), (48, 52)]),
          dust(10, 61, 3.6, ring=True), dust(53, 61, 3.6, ring=True), sweat([(10, 6)]), sweat([(52, 5)])],
)


def _dazed(head, googly, face='daze_tongue', twitch=False):
    f_r = (43, 58) if twitch else (43, 59)
    toes_r = [(41, 51), (45, 50), (48, 52)] if twitch else [(41, 52), (45, 51), (48, 53)]
    # a sweat drop on the side his head lolls away from (dazed), a jolt of two on the twitch
    extra = [sweat([(48, 10)]), sweat([(13, 12)])] if twitch else [sweat([(13 if head[0] > 0 else 48, 11)])]
    return dict(
        body=(0, 9, 1.06, 0.86), head=head,
        wing_r_mode='off', wing_l_mode='off',
        feet_detached=True,
        face=face, googly=googly, sym=False,
        over=[arm([(12, 47), (9, 52), (10, 57)], [3.0, 3.3, 3.5]),
              arm([(51, 47), (54, 52), (53, 57)], [3.0, 3.3, 3.5]),
              sole((20, 59), [(15, 53), (18, 51), (22, 52)]),
              sole(f_r, toes_r)] + extra,
    )


DAZED_A = _dazed((-4, 1), 'crossed')
DAZED_B = _dazed((4, 1), 'wall')
DAZED_C = _dazed((0, 0), 'up', face='blink', twitch=True)

FRAMES = [('reel', REEL), ('totter', TOTTER), ('sit_impact', SIT), ('bounce', BOUNCE),
          ('dazed_a', DAZED_A), ('dazed_b', DAZED_B), ('dazed_c', DAZED_C)]


def render(pose):
    return NC.render_pose(pose)
