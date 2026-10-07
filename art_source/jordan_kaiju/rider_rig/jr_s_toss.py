"""jordan_toss: 3 frames, once (0.08, 0.08, 0.14). The intro: he flings the toy kaiju off to the left side
of the ring (the kaiju's home), a cocky backhand toss over his near shoulder, the open box still up in
his far hand.

  0  wind-up: the toy on his palm swung in across his chest to the far shoulder, body twisted to the right
     (TOY = where kaiju_toy FEET goes)
  1  release: the backhand fling, the stick arm whipped out to the left, the hand flung open, a speed
     streak along the swing (HAND = the release texel: the code's toy leaves from here)
  2  follow-through: the arm carried on down to the left, a smug grin after it
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_sheet as S   # noqa: E402
import jr_s_box_open as BO  # noqa: E402
import jr_s_ride_throw as RT  # noqa: E402

NAME = 'jordan_toss'
TIMES = [0.08, 0.08, 0.14]
LOOP = False
KIND = 'mat'
OFFSET = (-1, 0)
NOTE = 'Standing (SOLES row 95). TOY on f0 (kaiju_toy FEET), HAND on f1 = where the tossed toy leaves his hand.'
V = F.V


def arm(wrist, rows, at, twist=(0, 0), bend=1):
    sh = (F.NEAR_ROOT[0] + twist[0], F.NEAR_ROOT[1] + twist[1])
    el = F.ik(sh, wrist, F.UPPER_L, F.FORE_L, bend)
    return F.near_arm(sh, el, wrist) + [(F.map_at(F.BAND, int(wrist[0]) - 3, int(wrist[1]) - 1), False),
                                         (F.map_at(rows, *at), False)]


def f0():
    fig = F.Fig()
    near = arm((56.0, 51.5), F.PALM_UP, (53, 45), twist=(2, 0), bend=1)
    BO.standing(fig, near, F.head('grin', dx=F.HEAD_AT[0] + 1, dy=F.HEAD_AT[1], tilt=5), F.open_box(0, 0))
    return fig, {'TOY': (57, 45)}, 'wind-up, the toy across his chest'


def f1():
    fig = F.Fig()
    near = arm((22.5, 41.5), F.HAND_OPEN_BACK, (16, 38), twist=(-1, 0), bend=-1)
    BO.standing(fig, near, F.head('shout', dx=F.HEAD_AT[0] - 1, dy=F.HEAD_AT[1], tilt=-6), F.open_box(0, 0))
    fig.fxput(RT.streak([(52, 36), (44, 33), (34, 33), (26, 36)], 'W') | RT.streak([(50, 40), (42, 37), (33, 37)], 'Q'),
              under=True)
    return fig, {'HAND': (17, 40)}, 'release: the backhand fling'


def f2():
    fig = F.Fig()
    near = arm((24.0, 55.0), F.HAND_OPEN_BACK, (17, 52), twist=(-1, 1), bend=-1)
    BO.standing(fig, near, F.head('smug', dx=F.HEAD_AT[0] - 1, dy=F.HEAD_AT[1] + 1, tilt=-3), F.open_box(0, 0))
    return fig, {}, 'follow-through, smug'


def frames():
    out = []
    for b in (f0, f1, f2):
        fig, a, note = b()
        a = dict(a)
        a['SOLES'] = (49, 95)
        a['CROWN'] = S.crown(fig.px, fig.pts['head'])
        fr = S.to_frame(fig, OFFSET, a, on_mat=True, note=note)
        S.fill_holes(fr.px)
        out.append(fr)
    return out
