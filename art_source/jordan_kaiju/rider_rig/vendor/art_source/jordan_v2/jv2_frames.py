"""Jordan v2 (thin, frail, greasy): the approval sprite. 2 frames of 96x96, feet on row 95, body
centred on column 48, facing screen-right in three-quarter view, like the approved redesign:

  frame 0  idle: slumped, the head pushed forward and sunk into his shoulders, a hand on his hip,
           the gold chase-edition box held up beside his face on a stick arm
  frame 1  the fist-pump: a stick arm punched skyward with the pink wristband, the pink pop and gold
           star bursting off the fist, the box hanging from his other hand at his hip

Build order is back to front, every outlined part keylined as it is stamped (the approved rig's
method). The face, the Peach print, the sneakers, the box, the fist, the pop cloud and the star are
the approved rig's own maps.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jv2_base as B  # noqa: E402
import jv2_body as body  # noqa: E402
import jv2_head as jhead  # noqa: E402

J = B.jordan

# the head's offset from the rig's head space: forward and down into the slump
HEAD_AT = {0: (3, 2), 1: (2, 1)}
# the box's offset from where the rig's BOX map sits (61, 25)
BOX_AT = {0: (2, 2), 1: (3, 41)}
FAR_HAND_AT = (61, 44)
LOW_HAND_AT = (61, 63)


def stamp_all(cv, parts):
    for part, ol in parts:
        cv.stamp(part, outline=ol)


def build(frame):
    cv = B.Canvas(96, 96)
    cv.stamp(body.legs())
    for s in body.shoes():
        cv.stamp(s, outline=False)
    stamp_all(cv, body.far_arm_box() if frame == 0 else body.far_arm_box_low())
    dx, dy = HEAD_AT[frame]
    cv.stamp(body.neck(dx))
    cv.stamp(body.shirt(frame))
    body.dandruff(cv.px)
    cv.stamp(B.shift(jhead.head(shout=(frame == 1)), dx, dy), outline=False)
    if frame == 0:
        stamp_all(cv, body.near_arm_hip())
        cv.stamp(J.box_part(*BOX_AT[0]), outline=False)
        cv.stamp(B.amap(body.FAR_HAND_BOX, *FAR_HAND_AT), outline=False)
    else:
        cv.stamp(J.pop_cloud())
        cv.stamp(B.amap(B.rows_of(J.STAR), 27, 0), outline=False)
        for q, k in J.GLINTS.items():
            cv.px[q] = k
        stamp_all(cv, body.raised_arm())
        cv.stamp(J.box_part(*BOX_AT[1]), outline=False)
        cv.stamp(B.amap(body.LOW_HAND, *LOW_HAND_AT), outline=False)
    return cv


# pixels that are effects and float free by design (the glints round the pop), frame coordinates
def fx_pixels(frame):
    if frame != 1:
        return set()
    return {(x + B.ANCHOR_SHIFT, y) for (x, y) in J.GLINTS}


def frame_px(frame):
    return B.finish(build(frame).px)


def frames():
    return B.image(frame_px(0)), B.image(frame_px(1))
