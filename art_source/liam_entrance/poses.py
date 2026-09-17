"""Liam standing poses for the slap sequence, built on liam.png (head, torso, legs reused exactly).
Every pose returns a Canvas of size (PW, PH) with liam.png placed at (POX, POY) so the feet stay on the same rows:
liam.png row 63 (soles) -> pose row POY + 63."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from liamkit import *

PW, PH = 80, 88
POX, POY = 8, 24

HAND = {'#': BLACK, 'a': L_SKIN[0], 's': L_SKIN[1], 'd': L_SKIN[2], 'f': L_SKIN[3], 'g': L_SKIN[4], 'W': WHITE}

# open blade hand, palm toward screen-left, fingers up (raised for the slap)
HAND_BLADE_UP = """
..###...
.#asd#..
.#asd#..
.#asdd#.
##asdd#.
#s#asdd#
#ss#sdd#
#sssssd#
#ssssdd#
.#ssddf#
..#dff#.
...###..
"""

# flat hand slapping down, fingers pointing screen-left
HAND_FLAT_LEFT = """
...#######..
.##asssssd#.
#aasssssdd##
#ssssssdddd#
.#ddddffff#.
..########..
"""

# thumbs up (right hand, thumb on top)
HAND_THUMB = """
..##...
.#as#..
.#as#..
.#as###
##asssd#
#asssdd#
#s#sdsd#
#ssddfd#
.#dfff#.
..####..
"""


def jacket_tube(cv, pts, r0, r1):
    m = tube(pts, (r0, r1))
    cv.part(m, L_JACKET, ('dist', 3.2, 0.25), [9.0, 0.86, 0.58, 0.28, 0.06])
    return m


def wristband(cv, p0, p1, r=3.1):
    band = capsule(p0, p1, r)
    cv.part(band, L_COLLAR, ('cyl', p0, p1, r + 0.2, 0.3), [9.0, 0.6, 0.25])
    return band


def base(remove_left=True, remove_right=False):
    src = load_liam()
    cv = Canvas(PW, PH)
    cv.blit(src, POX, POY)
    if remove_left:
        cut(cv, region(cv, [(x + POX, y + POY) for x, y in SEED_LARM]))
    if remove_right:
        cut(cv, region(cv, [(x + POX, y + POY) for x, y in SEED_RARM]))
    return cv


def L(x, y):
    """liam.png coords -> pose canvas coords"""
    return (x + POX, y + POY)


def windup():
    cv = base()
    jacket_tube(cv, [L(14, 31), L(7, 20), L(9, 8)], 4.9, 4.1)
    wristband(cv, L(9, 5), L(10, 3), 3.2)
    x, y = L(6, -8)
    cv.stamp(HAND_BLADE_UP, x, y, HAND)
    return cv


def smack():
    cv = base()
    jacket_tube(cv, [L(14, 31), L(5, 37), L(-4, 42)], 4.9, 4.2)
    wristband(cv, L(-6, 43), L(-8, 44), 3.2)
    x, y = L(-20, 41)
    cv.stamp(HAND_FLAT_LEFT, x, y, HAND)
    return cv


def likes_it():
    cv = base(remove_left=True, remove_right=True)
    # left hand resting on Bixby's back
    jacket_tube(cv, [L(14, 31), L(6, 38), L(-2, 42)], 4.9, 4.2)
    wristband(cv, L(-4, 43), L(-6, 44), 3.2)
    x, y = L(-17, 42)
    cv.stamp(HAND_FLAT_LEFT, x, y, HAND)
    # right arm: thumbs up beside the chest
    jacket_tube(cv, [L(46, 30), L(56, 37), L(55, 30)], 4.9, 4.0)
    wristband(cv, L(55, 27), L(55, 26), 3.3)
    x, y = L(51, 15)
    cv.stamp(HAND_THUMB, x, y, HAND)
    return cv


if __name__ == '__main__':
    import view
    view.row([windup(), smack(), likes_it()], 6, 'liam_slap_poses_6x.png')
    print('ok')
