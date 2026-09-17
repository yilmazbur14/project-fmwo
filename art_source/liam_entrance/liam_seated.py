"""Liam seated on the throne, smug welcome (liam_throne_seated.png).
Frame 88x64.  liam.png's pixels are placed at x+16 (head/torso/right hand-on-hip arm reused exactly);
the left arm is redrawn raised in an open-palm welcome and the legs are redrawn seated, knees apart.
Anchor: (46, 46) = centre of the belt's bottom edge -> place on throne SEAT (64, 86): frame top-left at (18, 40)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from liamkit import *
import view

FW, FH = 88, 64
OX = 16
ANCHOR = (46, 46)

HAND = {'#': BLACK, 'a': L_SKIN[0], 's': L_SKIN[1], 'd': L_SKIN[2], 'f': L_SKIN[3], 'g': L_SKIN[4]}

OPEN_PALM = """
..####....
.#asss#...
#asssdd#..
#asdsdd#..
#asdsdd#..
#asdsdd##.
#ssssdd#s#
#ssssdd#s#
#sssssdsd#
.#sssddfd#
..#ddfff#.
...#####..
"""


def jacket_tube(cv, pts, r0, r1):
    m = tube(pts, (r0, r1))
    cv.part(m, L_JACKET, ('dist', 3.2, 0.25), [9.0, 0.86, 0.58, 0.28, 0.06])
    return m


def seated_legs(cv):
    # hip block under the belt, thighs foreshortened toward the camera (knee caps), shins straight down, shoes
    for kx, sx in ((31, 29), (61, 63)):
        shin = capsule((kx, 53), (sx, 58), 4.9, 4.6)
        cv.part(shin, L_PANTS, ('cyl', (kx - 5, 0), (kx - 5, 1), 5.5, 0.25), [9.0, 0.8, 0.5, 0.2])
    for sx, d in ((29, -1), (63, 1)):
        shoe = poly([(sx - 7, 63), (sx + 7, 63), (sx + 7 + d, 61), (sx + 5, 58), (sx - 5, 58), (sx - 7 + d, 61)])
        cv.part(shoe, L_SHOES, ('sphere', sx - 3, 58, 10, 6, 0.1), [9.0, 0.78, 0.35])
        for x in range(sx - 6, sx + 7):
            if cv.get(x, 62) not in (None, BLACK):
                cv.put(x, 62, L_SHOES[2])
    hips = poly([(29, 45), (63, 45), (66, 49), (26, 49)])
    cv.part(hips, L_PANTS, ('flat', 0.0, 0.3), [9.0, 0.95, 0.6, 0.3])
    for kx in (31, 61):
        th = ell(kx, 50, 9.2, 5.2)
        cv.part(th, L_PANTS, ('sphere', kx - 3, 48.5, 10.5, 7, 0.2), [9.0, 0.82, 0.55, 0.25, -0.1])
    cv.put(46, 50, BLACK)
    cv.put(46, 51, BLACK)


def welcome_arm(cv):
    # sleeve: shoulder -> elbow out/down -> forearm raised
    jacket_tube(cv, [(28, 32), (19, 36), (13, 31)], 4.8, 4.0)
    # white wristband across the wrist
    band = capsule((10, 27), (14, 29), 3.0)
    cv.part(band, L_COLLAR, ('cyl', (10, 27), (14, 29), 3.2, 0.3), [9.0, 0.6, 0.25])
    cv.stamp(OPEN_PALM, 5, 15, HAND)


def build():
    src = load_liam()
    base = Canvas(FW, FH)
    base.blit(src, OX, 0)
    cut(base, region(base, [(x + OX, y) for x, y in SEED_LARM]))
    cut(base, region(base, [(x + OX, y) for x, y in SEED_LEGS]))
    legs = Canvas(FW, FH)
    seated_legs(legs)
    out = Canvas(FW, FH)
    out.blit(legs)
    out.blit(base)
    welcome_arm(out)
    return out


if __name__ == '__main__':
    cv = build()
    print(view.zoom(cv, 8, 'liam_seated_8x.png'))
