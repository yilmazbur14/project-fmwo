"""The slap: 3 key frames of Liam beside Bixby (liam_slap_keys.png) + the fed-up frame (bixby_fedup.png).
Frames are 128x96 with a shared layout so the whole gag plays as one storyboard:
  Bixby 64x64 frame top-left (BX, BY) = (4, 32)  -> his feet on row 95
  Liam  liam.png   top-left (LX, LY) = (58, 32)  -> soles on row 95
Order: 0 wind-up, 1 SMACK impact, 2 "he likes it!" (thumbs up, Bixby glares)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from liamkit import *
import poses
from liam_seated import OPEN_PALM
import bixby_faces
import fx
import view

FW, FH = 128, 96
BX, BY = 4, 32
LX, LY = 58, 32


def L(x, y):
    return (x + LX, y + LY)


def liam_base(remove_left=True, remove_right=False, dx=0):
    src = load_liam()
    cv = Canvas(FW, FH)
    cv.blit(src, LX + dx, LY)
    if remove_left:
        cut(cv, region(cv, [(x + LX + dx, y + LY) for x, y in SEED_LARM]))
    if remove_right:
        cut(cv, region(cv, [(x + LX + dx, y + LY) for x, y in SEED_RARM]))
    return cv


def bixby():
    return from_png(BIX_PNG)


def frame_windup():
    cv = Canvas(FW, FH)
    cv.blit(bixby(), BX, BY)
    li = liam_base(dx=1)
    poses.jacket_tube(li, [L(15, 31), L(8, 20), L(10, 8)], 4.9, 4.1)
    poses.wristband(li, L(10, 5), L(11, 3), 3.2)
    li.stamp(OPEN_PALM, *L(5, -8), poses.HAND)
    # whoosh arcs behind the raised hand
    fx.motion_arc(cv, LX + 24, LY + 12, 24, 196, 244, 1, WHITE)
    fx.motion_arc(cv, LX + 24, LY + 12, 20, 202, 238, 1, WHITE, dashed=True)
    cv.blit(li)
    return cv


def frame_smack():
    cv = Canvas(FW, FH)
    cv.blit(bixby(), BX, BY + 1)                      # squashed down a pixel by the blow
    bixby_faces.flinch(cv, BX, BY + 1)
    # swing arcs from the wind-up position down to the impact
    fx.motion_arc(cv, LX + 12, LY + 31, 27, 178, 256, 1, WHITE)
    fx.motion_arc(cv, LX + 12, LY + 31, 23, 184, 250, 1, WHITE, dashed=True)
    fx.starburst(cv, 51, 73, 20, 9, n=11, seed=3)
    for a, r0, r1 in ((200, 22, 28), (235, 21, 27), (160, 22, 27), (120, 21, 26), (275, 20, 25)):
        import math
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        fx.speed_line(cv, 51 + ca * r0, 73 + sa * r0 * 0.85, 51 + ca * r1, 73 + sa * r1 * 0.85, BLACK)
    li = liam_base(dx=-2)
    poses.jacket_tube(li, [L(12, 31), L(5, 35), L(-1, 39)], 4.9, 4.2)
    poses.wristband(li, L(-3, 40), L(-5, 41), 3.2)
    li.stamp(poses.HAND_FLAT_LEFT, *L(-15, 37), poses.HAND)
    cv.blit(li)
    w = fx.text_width('SMACK!')
    fx.lettering(cv, 'SMACK!', 58 - w // 2, 8)
    return cv


def frame_likes():
    cv = Canvas(FW, FH)
    cv.blit(bixby(), BX, BY)
    bixby_faces.glare(cv, BX, BY)
    li = liam_base(remove_right=True)
    poses.jacket_tube(li, [L(14, 31), L(7, 37), L(1, 41)], 4.9, 4.2)
    poses.wristband(li, L(-1, 42), L(-3, 43), 3.2)
    li.stamp(poses.HAND_FLAT_LEFT, *L(-13, 39), poses.HAND)
    poses.jacket_tube(li, [L(46, 30), L(57, 37), L(56, 29)], 4.9, 4.0)
    poses.wristband(li, L(56, 26), L(56, 25), 3.3)
    li.stamp(poses.HAND_THUMB, *L(52, 14), poses.HAND)
    cv.blit(li)
    # sparkle off the grin/glasses
    sp = """
...W...
...W...
WWWWWWW
...W...
...W...
"""
    cv.stamp(sp, LX + 30, LY + 9, {'W': WHITE})
    return cv


def frame_fedup():
    cv = Canvas(FW, FH)
    cv.blit(bixby(), BX, BY)
    bixby_faces.snarl(cv, BX, BY)
    li = liam_base(dx=1)
    poses.jacket_tube(li, [L(15, 31), L(8, 20), L(10, 8)], 4.9, 4.1)
    poses.wristband(li, L(10, 5), L(11, 3), 3.2)
    li.stamp(OPEN_PALM, *L(5, -8), poses.HAND)
    cv.blit(li)
    return cv


def build():
    return [frame_windup(), frame_smack(), frame_likes()], frame_fedup()


if __name__ == '__main__':
    keys, fed = build()
    view.row(keys + [fed], 4, 'slap_keys_4x.png', panel=view.FLOOR)
    print('ok')
