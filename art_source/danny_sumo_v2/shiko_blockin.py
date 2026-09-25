"""STUDY, not part of the build. The shiko-stomp silhouette tried for frame 1 and dropped: at
this build a front view has no room for the raised leg to go up without crossing in front of the far
shoulder, and a shallower lift reads as a kick or an arm. The pose transform it exercises
(torso.rot, knit_part_xf, gear.*_xf) is kept for a future shiko sheet. Flat fills + keylines."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sumo_lib import Canvas, spoly, capsule, view, mirror_pts  # noqa: E402
import torso as T  # noqa: E402
import danny_v2 as D  # noqa: E402
import limbs as LB  # noqa: E402
from PIL import Image  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'

XF = T.rot((87.5, 100.0), -14.0, shift=(-3.0, 1.0))
HEAD_SHIFT = (-15, 2)


def X(pts):
    return [XF(p) for p in pts]


# standing leg (viewer's left): the weight is on it; knee bent out, shin plumb, foot planted
S_THIGH = [(68, 108), (56, 107.5), (44, 109), (34, 112), (27.5, 116.5), (24.5, 122), (26, 127), (31, 129.5),
           (41, 129), (53, 126.5), (65, 124.5), (74, 124)]
S_CALF = [(28, 121), (24, 126), (23, 131.5), (25.5, 135.5), (32, 137.5), (41.5, 137.5), (47, 135), (48.5, 130),
          (47, 125), (41, 121.5)]
S_FOOT = [(29, 133.5), (23, 135.5), (19.5, 138.5), (19, 141), (20.5, 142.5), (57, 142.5), (59.5, 140.5),
          (57.5, 136.5), (49, 133.5)]
# raised leg (viewer's right): from under the belt's lifted end, a thick straight diagonal to a soft
# knee, the shin on up to a foot turned sole-out at shoulder height
R_THIGH = [(104, 104), (113, 97.5), (123, 91), (133, 85), (142, 79.5), (149, 76), (155, 76.5), (159.5, 81),
           (160, 88), (156, 94), (148, 99), (137, 105), (125, 112), (114, 118), (104, 120), (99, 115)]
R_CALF = [(150, 76), (155, 70), (160.5, 64.5), (166, 60.5), (171, 60), (174.5, 64), (174.5, 71), (171.5, 78),
          (166, 85), (159.5, 91)]
R_FOOT = [(163, 62), (163, 54), (165, 46.5), (168.5, 41.5), (172.5, 40), (175, 43), (175, 51), (175, 59),
          (173, 65), (168, 66)]


def build():
    cv = Canvas()
    flat = lambda s, k: {p: k for p in s}  # noqa: E731
    # standing leg
    cv.stamp(flat(spoly(S_CALF), '4'))
    cv.stamp(flat(spoly(S_THIGH), '5'))
    cv.stamp(flat(spoly(S_FOOT), '6'))
    # raised leg
    cv.stamp(flat(spoly(R_CALF), '4'))
    cv.stamp(flat(spoly(R_FOOT), '6'))
    cv.stamp(flat(spoly(R_THIGH), '5'))
    # belt, apron
    cv.stamp(flat(spoly(X(D.sym(D.BELT))), 'w'))
    ax, ay = XF((87.5, 107.0))
    ap = spoly([(ax - 17.5, ay), (ax + 17.5, ay), (ax + 17.5, ay + 23), (ax - 17.5, ay + 23)], 0)
    cv.stamp(flat(ap, 'V'))
    # torso
    cv.stamp(flat(T.mask(XF), '6'))
    # arms
    for side in (1, -1):
        dl = LB.DELT if side > 0 else mirror_pts(LB.DELT)
        if side > 0:
            up = capsule((17, 78), (15, 98), 10.5, 9)
            fo = capsule((16, 100), (30, 114), 8.5, 7.5)
            hand = spoly([(26, 108), (33, 105.5), (41, 107), (43, 113), (39, 118), (30, 118), (25, 114)])
        else:
            up = capsule((138, 56), (152, 64), 9.5, 8.5)
            fo = capsule((153, 66), (150, 74), 8, 7)
            hand = spoly([(141, 70), (149, 67.5), (157, 69), (158, 76), (153, 80), (144, 79.5)])
        cv.stamp(flat(up, '4'))
        cv.stamp(flat(spoly(X(dl)), '6'))
        cv.stamp(flat(fo, '5'))
        cv.stamp(flat(hand, '6'))
    # head
    dx, dy = HEAD_SHIFT
    cv.stamp(flat(spoly([(x + dx, y + dy) for (x, y) in D.sym(D.FACE)]), '6'))
    cv.stamp(flat(spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CROWN)]), 'w'))
    cv.stamp(flat(spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CUFF)], 1), 'B'))
    return cv


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    im = build().image()
    view(im, 3, os.path.join(OUT, 'shiko_blockin_3x.png'))
    sil = Image.new('RGBA', im.size, (0, 0, 0, 0))
    sil.paste((20, 20, 20, 255), (0, 0), im.getchannel('A'))
    view(sil, 3, os.path.join(OUT, 'shiko_sil_3x.png'), bg=(200, 200, 205, 255))
    print(im.getbbox())
