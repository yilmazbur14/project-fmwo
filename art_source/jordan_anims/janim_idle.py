"""jordan_idle.png: 4 frames, looping. A slouchy breath while he tilts the box to admire it.

  0  the approved idle frame, pixel for pixel (the rig's own frame 0)
  1  breath out: everything above the belt sinks a pixel into the slouch; the box starts to tip
  2  still sunk, the box tipped out toward the crowd so the window catches the light; his eye slides
     onto it, the far brow cocks up and the mouth curls: he is admiring it
  3  breathing back in to the approved height, the box tipping back, still pleased with it

Built exactly like v2's frame 0 (jv2_frames.build(0)), back to front, with the upper body offset.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_box as BX  # noqa: E402
import janim_heads as HD  # noqa: E402

J = B.jordan
NAME = 'jordan_idle'
TIMES = [0.2, 0.16, 0.2, 0.16]
LOOP = True
APPROVED = {0: 0}          # frame 0 is the approved v2 frame 0

# The box's own point under his thumb (box-local), and where it sits in build coordinates in the
# approved frame; the box turns about it.
GRIP_UV = (1, 19)
GRIP_XY = (64, 46)
HEAD_AT = B.V2F.HEAD_AT[0]         # v2's idle head: forward and down into the slump


def sparkle(cx, cy):
    """The approved frame's glint: a white centre with pink arms (free-floating, no keyline)."""
    out = {(cx, cy): 'W'}
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        out[(cx + dx, cy + dy)] = 'Q'
    return out


def window_streak(part, x0, y0, length, keys='x'):
    """A diagonal highlight across the box's window plastic (only over window 'w' pixels)."""
    for i in range(length):
        q = (x0 + i, y0 + i)
        if part.get(q) == 'w':
            part[q] = keys
        q2 = (x0 + i + 1, y0 + i)
        if part.get(q2) == 'w':
            part[q2] = keys


def build(dip=0, box_deg=0, head='idle', streak=None, glint=None):
    V = B.V2B
    cv = B.Canvas(96, 96)
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    up = lambda part: B.shift(part, 0, dip)  # noqa: E731
    for part, ol in V.far_arm_box():
        cv.stamp(up(part), outline=ol)
    cv.stamp(up(V.neck(HEAD_AT[0])))
    cv.stamp(up(V.shirt(0)))
    B.dandruff(cv.px, 0, dip)
    cv.stamp(B.rec('head', HD.head(head, HEAD_AT[0], HEAD_AT[1] + dip)), outline=False)
    hip = V.near_arm_hip()
    for part, ol in hip:
        cv.stamp(up(part), outline=ol)
    B.rec('hand_near', up(hip[2][0]))
    box = BX.box_at(box_deg, GRIP_UV, (GRIP_XY[0], GRIP_XY[1] + dip))
    if streak:
        window_streak(box, streak[0], streak[1] + dip, streak[2])
    B.close_gaps(box)
    cv.stamp(B.rec('box', box), outline=False)
    cv.stamp(B.rec('hand_far', up(B.amap(V.FAR_HAND_BOX, *B.V2F.FAR_HAND_AT))), outline=False)
    fx = {}
    if glint:
        fx = B.rec('glint', sparkle(glint[0], glint[1] + dip))
        for q, k in fx.items():
            cv.px[q] = k
    return cv, set(fx)


def builders():
    return [lambda: build(dip=0, box_deg=0, head='idle'),
            lambda: build(dip=1, box_deg=4, head='idle'),
            lambda: build(dip=1, box_deg=8, head='admire', streak=(67, 35, 7), glint=(80, 26)),
            lambda: build(dip=0, box_deg=4, head='admire')]


def frames_info():
    return B.make_frames(builders(), approved=APPROVED)


def frames():
    """[(frame px, fx pixels)] in frame coordinates."""
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.to_image(px))
        a = B.audit(px, fx)
        print(i, st, {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()})
