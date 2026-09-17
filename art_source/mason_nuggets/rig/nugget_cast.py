"""Mason frames 15-18 - Chicken Nugget Meteor Shower cast.

Built on the approved rig (rig.py / props.py / frames.py reproduce mason_sheet.png frames
0-14 pixel-for-pixel), so body, head, feet, palette and lighting match exactly.

15 PULL   pull out a giant striped nugget bucket, nuggets heaped to his chin, greedy face
16 HOIST  heave it up behind his head (comb stays in front), straining
17 HEAVE  fling: arms thrown up, the heap bursts out of the bucket skyward
18 SHOUT  hold pose: fists up, battle-cry at the sky (loops while the meteors fall)

Feet anchor: identical to idle (feet offsets 0) in every frame.
"""
import math
import rig
import nugprops as NP
from rig import BLACK, WHITE, hex2rgba
from props import limb, lines


# ----------------------------------------------------------------------------- face
def face_shout_up(c, fput):
    """battle cry at the sky: brows down, pupils rolled up, mouth wide open"""
    rig._scalp(fput)
    rig._pts(fput, [(27, 16), (28, 16), (29, 16), (30, 17), (36, 16), (35, 16), (34, 16), (33, 17)], BLACK)
    for x in list(range(28, 31)) + list(range(33, 36)):
        fput(x, 18, WHITE)
        fput(x, 19, WHITE)
    rig._pts(fput, [(29, 18), (34, 18)], BLACK)
    for y, (a, b) in {21: (28, 35), 22: (28, 35), 23: (28, 35), 24: (29, 34), 25: (30, 33)}.items():
        for x in range(a, b + 1):
            fput(x, y, BLACK)
    for x in range(29, 35):
        fput(x, 21, WHITE)
    rig._pts(fput, [(30, 24), (31, 24), (32, 24), (33, 24), (31, 25), (32, 25)], rig.RED_HI)


rig.EXPRESSIONS['shout_up'] = face_shout_up


# ----------------------------------------------------------------------------- props
def bucket(px, py, **kw):
    return NP.prop(lambda c: NP.bucket_lip(px, py, **kw))


def nug(cx, cy, rx=3.6, ry=2.9, a=0.0, bumps=((100, -0.2),), pits=((0, 0),)):
    return NP.prop(lambda c: [NP.nugget_part(cx, cy, rx, ry, math.radians(a), list(bumps), list(pits))])


def hand(x, y, r=3.5):
    return limb([(x, y), (x, y)], [r, r], frame='abs')


# two-row heap for the bucket held at the belly  (u, v, rx, ry, angle, bumps, pits)
HEAP_FULL = [
    (-14.3, -0.6, 4.4, 3.2, -20, [(120, -0.18), (-60, 0.10)], [(0, 0)]),
    (-7.1, -1.6, 4.6, 3.4, 10, [(60, -0.2), (-150, 0.12)], [(1, 0)]),
    (0.5, -1.4, 4.6, 3.4, -5, [(90, -0.2), (-30, -0.15), (200, 0.1)], [(-1, 0), (2, 1)]),
    (8.1, -1.8, 4.6, 3.3, 25, [(0, -0.2), (170, 0.1)], [(1, 0)]),
    (14.7, -0.5, 4.2, 3.1, -35, [(200, -0.2)], [(0, 0)]),
    (-10.5, -4.4, 4.2, 3.1, 30, [(60, -0.2)], [(0, 0)]),
    (-2.9, -5.0, 4.4, 3.2, -15, [(150, -0.2)], [(1, 0)]),
    (4.8, -4.8, 4.3, 3.1, 15, [(30, -0.2)], [(0, 0)]),
    (11.4, -4.1, 4.0, 3.0, -25, [(250, -0.2)], []),
]

# single row peeking over the rim when the bucket is up behind his head
HEAP_ROW = [
    (-15.5, -0.8, 4.0, 2.9, -20, [(120, -0.18), (-60, 0.10)], [(0, 0)]),
    (-9.0, -1.6, 4.4, 3.0, 10, [(60, -0.2), (-150, 0.12)], [(1, 0)]),
    (-2.5, -1.9, 4.4, 3.1, -5, [(90, -0.2), (-30, -0.15), (200, 0.1)], [(-1, 0), (2, 1)]),
    (4.0, -1.9, 4.4, 3.0, 25, [(0, -0.2), (170, 0.1)], [(1, 0)]),
    (10.0, -1.6, 4.2, 2.9, -35, [(200, -0.2)], [(0, 0)]),
    (16.0, -0.8, 3.8, 2.8, 15, [(250, -0.2)], []),
]

BUCKET = dict(wt=40, wb=32)     # same bucket in every frame


# ----------------------------------------------------------------------------- poses
PULL = dict(
    body=(0, 1, 1.0, 1.0), wing_r_mode='off', wing_l_mode='off',
    face='chomp_open', googly='in', sym=True,
    over=[limb([(12, 39), (7, 43), (9, 47)], [3.0, 3.3, 3.5], frame='abs'),
          limb([(51, 39), (56, 43), (54, 47)], [3.0, 3.3, 3.5], frame='abs'),
          bucket(31.5, 36.5, h=16, contents='heap', heap=HEAP_FULL, **BUCKET),
          hand(11, 46, 3.6), hand(52, 46, 3.6)])

HOIST = dict(
    body=(0, 2, 1.06, 0.90), wing_r_mode='off', wing_l_mode='off',
    face='strain', googly='lag_up', sym=True,
    behind=[bucket(31.5, 6.5, h=12, contents='heap', heap=HEAP_ROW, **BUCKET)],
    under=[limb([(12, 40), (4, 29), (11, 15)], [3.0, 3.4, 3.9], frame='abs', grooves=[(11, 13), (10, 13)]),
           limb([(51, 40), (59, 29), (52, 15)], [3.0, 3.4, 3.9], frame='abs', grooves=[(52, 13), (53, 13)])])

HEAVE = dict(
    body=(0, 1, 1.02, 0.96), wing_r_mode='off', wing_l_mode='off',
    face='shout_up', googly='lag_up', sym=True,
    behind=[bucket(31.5, 6.0, h=12, contents='empty', **BUCKET)],
    over=[limb([(12, 39), (7, 31), (5, 22)], [3.0, 3.6, 4.4], frame='abs', grooves=[(5, 20), (6, 21)]),
          limb([(51, 39), (56, 31), (58, 22)], [3.0, 3.6, 4.4], frame='abs', grooves=[(57, 20), (58, 21)]),
          nug(21, 4.0, 3.4, 2.6, 20), nug(42, 4.0, 3.4, 2.6, -20),
          nug(11, 4.5, 3.8, 2.9, -30), nug(52, 4.5, 3.8, 2.9, 35),
          nug(5, 12.0, 3.3, 2.7, -50), nug(58, 12.0, 3.3, 2.7, 50),
          NP.speed_lines([[(14, 8), (16, 11)], [(49, 8), (47, 11)], [(8, 16), (11, 18)], [(55, 16), (52, 18)]])])

SHOUT = dict(
    body=(0, 0, 1.0, 1.02), wing_r_mode='off', wing_l_mode='off',
    face='shout_up', googly='lag_up', sym=True,
    over=[limb([(12, 38), (7, 31), (5, 23)], [3.0, 3.6, 4.6], frame='abs', grooves=[(5, 21), (6, 22)]),
          limb([(51, 38), (56, 31), (58, 23)], [3.0, 3.6, 4.6], frame='abs', grooves=[(57, 21), (58, 22)]),
          lines([[(14, 9), (11, 7)], [(12, 13), (9, 12)], [(49, 9), (52, 7)], [(51, 13), (54, 12)]], local='head')])

FRAMES = [('nugget_pull', PULL), ('nugget_hoist', HOIST), ('nugget_heave', HEAVE), ('nugget_shout', SHOUT)]


class _Ctx:
    pass


def render_pose(pose):
    """rig.render + optional 'behind' props composited under the whole figure"""
    behind = pose.get('behind', [])
    g = rig.render({k: v for k, v in pose.items() if k != 'behind'})
    if not behind:
        return g
    layer = {}
    c = _Ctx()
    c.head, c.bdx, c.bdy = (0, 0), 0, 0
    c.put = lambda x, y, col: layer.__setitem__((x, y), col) if (0 <= x < 64 and 0 <= y < 64) else None
    for fn in behind:
        fn(c)
    for (x, y), col in layer.items():
        if g[y][x][3] == 0:
            g[y][x] = hex2rgba(col)
    return g
