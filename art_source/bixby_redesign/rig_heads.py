"""Heads for the animation rig: the approved heads, moved per pose, with expression variants.

mid_head(cv, bob, dx, dy, mouth, eyes, low_dy, fx) stamps the middle head straight onto cv.
side_head(bob, dx, dy, mouth, eyes, low_dx, low_dy) returns a canvas holding the RIGHT side head
(the rig mirrors it for the left).

Offsets are relative to the approved placements (frame.MID / frame.SIDE); low_dx/low_dy move the
collar and ruff relative to the head (a dropped jaw keeps its collar where the neck is).
Expressions: see rig_faces.MID_MOUTHS, MID_EYES, SIDE_MOUTHS, SIDE_EYES.
"""
import frame as FR
import heads
import midmaps
import rig_faces as RF
import rig_faces2  # noqa: F401  (registers the flight-set expressions)
from pal import BCanvas


def mid_xf(p, bob=0):
    return FR.xf(FR.MID, bob, p.get('dx', 0), p.get('dy', 0))


def mid_head(cv, bob=0, dx=0, dy=0, mouth='snarl', eyes='open', low_dx=0, low_dy=0, fx=None,
             tongue=None, brows=True):
    xf = FR.xf(FR.MID, bob, dx, dy)
    low = FR.xf(FR.MID, bob, dx + low_dx, dy + low_dy) if (low_dx or low_dy) else None
    off = int(round(FR.MID['cy'] - heads.HY)) + bob + dy        # the maps' row offset for this head
    snarl = mouth == 'snarl'
    variant = eyes != 'open'
    # the snarl is the approved frame 0: the procedural mouth and eyes sit under its hand maps
    heads.build(cv, xf, with_headband=True, features=snarl, low=low, brows=brows and not variant)
    if variant and snarl:
        # clear the procedural eyes back to bare skull before the variant goes on
        tmp = BCanvas()
        heads.build(tmp, xf, with_headband=True, features=False, low=low, brows=False)
        for y in range(24 + off, 39 + off):
            for x in range(76 + dx, 116 + dx):
                if (x, y) in tmp.px:
                    cv.px[(x, y)] = tmp.px[(x, y)]
    RF.mid_mouth(cv, mouth, dx, off, tongue)
    RF.mid_eyes(cv, eyes, dx, off)
    if fx == 'inhale':
        for q, k in FR.inhale_fx(off + 3).items():
            cv.px[(q[0] + dx, q[1])] = k


def side_head(bob=0, dx=0, dy=0, mouth='snarl', eyes='open', low_dx=0, low_dy=0, tongue=None):
    side = BCanvas()
    xf = FR.xf(FR.SIDE, bob, dx, dy)
    low = FR.xf(FR.SIDE, bob, dx + low_dx, dy + low_dy)
    heads.build(side, xf, tongue_flip=True, features=False, low=low)
    mdx = int(round(FR.SIDE['cx'] - FR.SIDE_REF[0])) + dx
    mdy = int(round(FR.SIDE['cy'] - FR.SIDE_REF[1])) + bob + dy
    RF.side_face(side, mouth, eyes, mdx, mdy, tongue)
    return side
