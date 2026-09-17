import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ulib, uparts as P, ubits as B
from uhead import HEAD

HERE = os.path.dirname(os.path.abspath(__file__))
G_THRESH = [0.12, 0.42, 0.80, 0.95]
TO_CHAR = {'Q': 'E', 'L': 'T', 'G': 'B', 'g': 'b', 'X': 'Z'}


def torso_spans(dy):
    s = {22: (23, 26), 23: (22, 26), 24: (21, 29), 25: (21, 32), 26: (21, 34), 27: (21, 35),
         28: (22, 35), 29: (22, 36)}
    for y in range(30, 35): s[y] = (23, 36)
    for y in range(35, 40): s[y] = (23, 37)
    for y in range(40, 44): s[y] = (23, 36)
    return {y + dy: v for y, v in s.items()}


def torso(dy):
    ts = torso_spans(dy)
    lay = P.render(P.mask_spans(ts), P.span_normal(ts, 22 + dy, 43 + dy), P.RAMP_GREEN, 0.04, G_THRESH)
    for (x, y), c in list(lay.items()):
        if c != 'K' and y in (41 + dy, 42 + dy):       # black ribbed hem band
            lay[(x, y)] = TO_CHAR[c]
    # drawstring hanging from the collar
    for (x, y, c) in ((33, 27, 'w'), (33, 28, 'w'), (34, 29, 'w'), (34, 30, 'W')):
        lay[(x, y + dy)] = c
    # hood rim crease on the lump behind the neck
    for (x, y, c) in ((25, 23, 'g'), (24, 24, 'g'), (24, 25, 'g'), (25, 26, 'g')):
        if lay.get((x, y + dy), 'K') != 'K':
            lay[(x, y + dy)] = c
    # kangaroo-pocket opening: slanted seam with a lit lip above it
    for (x, y, c) in ((29, 34, 'L'), (30, 35, 'X'), (31, 36, 'X'), (31, 37, 'X'), (32, 38, 'X')):
        if lay.get((x, y + dy), 'K') != 'K':
            lay[(x, y + dy)] = c
    return lay


def arm(pts, far=False, cuff=2.2):
    ramp = P.RAMP_GREEN_FAR if far else P.RAMP_GREEN
    radii = [3.2, 2.9, 2.6]
    m = P.mask_stroke(pts, radii)
    lay = P.render(m, lambda x, y: P.stroke_normal(x, y, pts, radii), ramp, 0.0, G_THRESH)
    wx, wy = pts[-1]
    for k, c in list(lay.items()):
        if c != 'K' and (k[0] - wx) ** 2 + (k[1] - wy) ** 2 <= cuff * cuff:
            lay[k] = TO_CHAR[c]
    return lay


def fist(wrist, grip, far=False):
    ramp = P.RAMP_SKIN_FAR if far else P.RAMP_SKIN
    return B.limb([wrist, grip], [2.0, 2.3], ramp)


def leg(hip, knee, ankle, far=False):
    ramp = P.RAMP_CHAR_FAR if far else P.RAMP_CHAR
    return B.limb([hip, knee, ankle], [3.3, 2.9, 2.7], ramp)


POSES = [
    dict(dy=1,  # 0 contact A
         near_leg=((30, 45), (33, 51), (36, 58), 'toe_up', True),
         far_leg=((29, 45), (26, 51), (22, 57), 'heel_up', True),
         near_arm=[(29, 29), (27, 34), (25, 39)], near_tip=(24, 41), bag_ang=0,
         far_arm=[(30, 29), (34, 34), (39, 37)], far_tip=(41, 39)),
    dict(dy=0,  # 1 passing A
         near_leg=((30, 44), (30, 51), (30, 58), 'flat', True),
         far_leg=((30, 44), (34, 49), (31, 53), 'hang', False),
         near_arm=[(29, 28), (28, 33), (28, 38)], near_tip=(28, 40), bag_ang=-10,
         far_arm=[(30, 28), (30, 33), (31, 38)], far_tip=(31, 40)),
    dict(dy=1,  # 2 contact B
         near_leg=((29, 45), (26, 51), (22, 57), 'heel_up', True),
         far_leg=((31, 45), (34, 51), (37, 58), 'toe_up', True),
         near_arm=[(29, 29), (31, 34), (34, 38)], near_tip=(35, 40), bag_ang=0,
         far_arm=[(29, 29), (25, 34), (20, 37)], far_tip=(18, 39)),
    dict(dy=0,  # 3 passing B
         near_leg=((29, 44), (33, 50), (29, 55), 'hang', False),
         far_leg=((31, 44), (31, 51), (31, 58), 'flat', True),
         near_arm=[(29, 28), (30, 33), (30, 38)], near_tip=(30, 40), bag_ang=10,
         far_arm=[(30, 28), (30, 33), (31, 38)], far_tip=(31, 40)),
    dict(dy=0,  # 4 deliver A
         near_leg=((30, 44), (31, 51), (33, 58), 'flat', True),
         far_leg=((29, 44), (28, 51), (26, 58), 'flat', True),
         near_arm=[(30, 28), (35, 30), (41, 31)], near_tip=(43, 31), bag_ang=0, far_arm=None, lean=1),
    dict(dy=0,  # 5 deliver B: bag bobs 1px, front toe taps
         near_leg=((30, 44), (31, 51), (33, 58), 'toe_up', True),
         far_leg=((29, 44), (28, 51), (26, 58), 'flat', True),
         near_arm=[(30, 28), (35, 31), (41, 32)], near_tip=(43, 32), bag_ang=0, far_arm=None, lean=1),
]


def build(pose):
    dy = pose['dy']
    L = []
    if pose.get('far_arm'):
        L.append(arm(pose['far_arm'], far=True))
        L.append(fist(pose['far_arm'][-1], pose['far_tip'], far=True))
    for key, far in (('far_leg', True), ('near_leg', False)):
        hip, knee, ankle, ang, grounded = pose[key]
        sh, (ax, ay) = B.shoe(ankle[0], ankle[1], ang, far=far, ground=63 if grounded else None)
        L.append(sh)
        L.append(leg(hip, knee, (ax, ay - 1), far=far))
    L.append(P.sprite_layer(HEAD, 21 + pose.get('lean', 0), 5 + dy))
    L.append(torso(dy))
    tip = pose['near_tip']
    L.append(B.bag(tip[0], tip[1] + 1, pose['bag_ang']))
    L.append(arm(pose['near_arm']))
    L.append(fist(pose['near_arm'][-1], tip))
    return P.compose(L)


if __name__ == '__main__':
    frames = [build(p) for p in POSES]
    ulib.write_png(os.path.join(HERE, 'sheet_1x.png'), frames, 1)
    ulib.write_crop(os.path.join(HERE, 'all_crop.png'), frames, 14, 2, 50, 63, 5)
    if len(sys.argv) > 1:
        print(ulib.dump(frames[int(sys.argv[1])]))
