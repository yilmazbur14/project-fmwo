"""STUDY, not part of the build. Stage 1 of frame 0: the first silhouette and part layout, flat-filled
and keylined, used to judge the pose before any shading. The final geometry lives in danny_v2.py,
torso.py and limbs.py and has moved on from these numbers."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sumo_lib import (Canvas, spoly, capsule, mirror_pts, view, grid, stats)  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else '.'


def sym(left):
    """A symmetric closed outline from its left half, listed top-centre -> bottom-centre."""
    right = mirror_pts(left[::-1])
    return left + right[1:-1] if left[0][0] == 87.5 else left + right


def both(pts):
    return [spoly(pts), spoly(mirror_pts(pts))]


TRAP = [(87.5, 20), (66, 22), (54, 26.5), (44, 31), (36, 35.5), (31, 41), (40, 48), (60, 50), (87.5, 51)]
TORSO = [(87.5, 36), (58, 38), (48, 44), (44.5, 56), (45.5, 70), (47, 84), (48.5, 94), (87.5, 96)]
CALF = [(10.5, 114), (6.5, 120), (5, 126), (6.5, 131), (11, 134), (25, 134), (32, 131.5), (36.5, 126),
        (37, 120), (34, 115), (22, 112)]
THIGH = [(66, 100), (52, 97.5), (40, 99), (28, 101.5), (17.5, 105.5), (10.5, 111), (7, 117.5), (8.5, 123.5),
         (15, 127), (26, 126.5), (38, 123), (52, 119.5), (67, 117.5)]
FOOT = [(9, 131), (5, 133), (3, 136.5), (3, 140.5), (5, 143), (37, 143), (40, 140.5), (39, 136), (35, 132.5)]
BELT = [(87.5, 91), (62, 91), (50, 91.5), (46, 94.5), (45, 101), (46.5, 106.5), (60, 109), (87.5, 110)]
APRON = [(87.5, 107), (70, 107), (69.5, 118), (69, 130), (87.5, 130)]
BELLY = [(87.5, 57), (71, 58), (59.5, 61.5), (52.5, 68), (49.5, 76), (49.5, 84), (52.5, 90), (59, 94),
         (68, 96.3), (78, 97.3), (87.5, 97.5)]
PEC = [(87, 42), (76, 40.5), (64, 41), (54.5, 44.5), (48.5, 51), (47.5, 58), (51, 64), (58, 68),
       (68, 69.5), (78, 68.5), (86, 65), (87, 58)]
DELT = [(40, 34.5), (30, 34.8), (22.5, 38.5), (17.5, 45), (15.5, 53), (17, 61), (21.5, 67), (28.5, 70),
        (36, 69.5), (42.5, 65), (46.5, 57.5), (47, 48), (44.5, 39.5)]
FACE = [(87.5, 10), (77, 10.5), (68.5, 13), (64, 18), (62, 25), (61.3, 32), (61.8, 38.5), (63.5, 44),
        (66.5, 48.5), (71, 51.5), (77, 53.3), (82.5, 54), (87.5, 54.2)]
CROWN = [(87.5, 2.5), (78.5, 2.9), (71, 4.7), (65.8, 7.7), (62.2, 11.8), (60.2, 16), (59.5, 20.5), (87.5, 20.5)]
CUFF = [(87.5, 18.5), (58.5, 18.5), (58, 24), (58.4, 30), (59.4, 35), (61.5, 38), (64.3, 35.8), (64.8, 29.8),
        (69, 27.2), (77, 26.3), (87.5, 26)]


def build():
    cv = Canvas()
    flat = lambda s, k: {p: k for p in s}  # noqa: E731
    cv.stamp(flat(spoly(sym(TRAP)), '5'))
    cv.stamp(flat(spoly(sym(TORSO)), '4'))
    for s in both(CALF):
        cv.stamp(flat(s, '4'))
    for s in both(THIGH):
        cv.stamp(flat(s, '5'))
    for s in both(FOOT):
        cv.stamp(flat(s, '6'))
    cv.stamp(flat(spoly(sym(BELT)), 'w'))
    cv.stamp(flat(spoly(sym(APRON), 1), 'V'))
    cv.stamp(flat(spoly(sym(BELLY)), '6'))
    for s in both(PEC):
        cv.stamp(flat(s, '5'))
    for side in (1, -1):
        up = capsule((30, 60), (17, 81), 11, 9.5)
        fo = capsule((19, 84), (40, 90), 9, 8)
        fist = spoly([(38, 84), (46, 81), (55, 82), (59, 87), (59, 95), (54, 99.5), (45, 100), (39, 96), (37, 90)])
        if side < 0:
            up, fo, fist = [{(175 - x, y) for (x, y) in s} for s in (up, fo, fist)]
        cv.stamp(flat(up, '4'))
        dl = spoly(DELT if side > 0 else mirror_pts(DELT))
        cv.stamp(flat(dl, '6'))
        cv.stamp(flat(fo, '5'))
        cv.stamp(flat(fist, '6'))
    cv.stamp(flat(spoly(sym(FACE)), '6'))
    cv.stamp(flat(spoly(sym(CROWN)), 'w'))
    cv.stamp(flat(spoly(sym(CUFF), 1), 'B'))
    return cv


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    im = build().image()
    im.save(os.path.join(OUT, 'blockin.png'))
    view(im, 4, os.path.join(OUT, 'blockin_4x.png'))
    from PIL import Image
    sil = Image.new('RGBA', im.size, (0, 0, 0, 0))
    a = im.getchannel('A')
    sil.paste((20, 20, 20, 255), (0, 0), a)
    view(sil, 3, os.path.join(OUT, 'silhouette_3x.png'), bg=(200, 200, 205, 255))
    print(stats(im), im.getbbox())
