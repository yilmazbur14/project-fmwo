"""jordan_hit.png: 2 frames, played once. The recoil when a punch or a blast lands. In v2's look.

  0  impact: everything above the belt jolts back, the head snaps back with his eyes squeezed shut
     and the greasy quiff knocked flat over his forehead, the stick arm flies off his hip (the tee's
     pinch at the hip lets go), the box tips out
  1  recoil: halfway back, wincing, the quiff still flopped, the box wobbling back the other way and
     the hand back on the hip

Both are built on v2's idle stance (the box held up beside his face), which is where he goes back to.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_box as BX  # noqa: E402
import janim_heads as HD  # noqa: E402

J = B.jordan
V = B.V2B
NAME = 'jordan_hit'
TIMES = [0.08, 0.14]
LOOP = False

GRIP_UV = (1, 19)
GRIP_XY = (64, 46)                 # the box's grip point in v2's idle
HEAD_AT = B.V2F.HEAD_AT[0]         # v2's idle head offset
NECK_PIVOT = (45, 33)

# His near hand flung open, fingers splayed back (to the left), the thin wrist on the right.
HAND_OPEN = B.rows_of([
    ".k.....",
    "kek.k..",
    ".kdkek.",
    "kedddkk",
    ".kcdddk",
    "kecdcck",
    ".kkkkk.",
])


def near_arm_flung(dx):
    """The hand knocked off his hip: the stick arm flies out behind him, the bony elbow leading, the
    fingers splayed; the fitted sleeve round the top of the upper arm (v2's, 2026-09-28)."""
    arm = V.limb([((40.6 + dx, 49.2), (33.2 + dx, 53), 1.55, 1.45), ((33.2 + dx, 53), (26.6 + dx, 55.4), 1.45, 1.3)],
                 knobs=((33.2 + dx, 53.2, 1.9),))
    sl = V.near_sleeve((40.6 + dx, 49.2), (33.2 + dx, 53))
    hand = B.amap(HAND_OPEN, 20 + dx, 52)
    return [(arm, True), (sl, True), (hand, False)]


def build(dx, box_deg, head, tilt, head_dx, flung):
    cv = B.Canvas(96, 96)
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    back = lambda part: B.shift(part, dx, 0)  # noqa: E731
    for part, ol in V.far_arm_box():
        cv.stamp(back(part), outline=ol)
    hx = HEAD_AT[0] + dx + head_dx
    cv.stamp(back(V.neck(HEAD_AT[0] + head_dx)))
    cv.stamp(back(V.shirt(1 if flung else 0)))
    B.dandruff(cv.px, dx, 0)
    hd = HD.head(head)
    if tilt:
        hd = B.tilt2(hd, tilt, NECK_PIVOT, 'xy')
        B.close_gaps(hd)
    cv.stamp(B.rec('head', B.shift(hd, hx, HEAD_AT[1])), outline=False)
    if flung:
        arm = near_arm_flung(dx)
        B.rec('hand_near', arm[2][0])
        B.stamp_all(cv, arm)
    else:
        hip = V.near_arm_hip()
        for part, ol in hip:
            cv.stamp(back(part), outline=ol)
        B.rec('hand_near', back(hip[2][0]))
    box = BX.box_at(box_deg, GRIP_UV, (GRIP_XY[0] + dx, GRIP_XY[1]))
    B.close_gaps(box)
    cv.stamp(B.rec('box', box), outline=False)
    cv.stamp(B.rec('hand_far', back(B.amap(V.FAR_HAND_BOX, *B.V2F.FAR_HAND_AT))), outline=False)
    return cv, set()


def builders():
    return [lambda: build(dx=-2, box_deg=11, head='pain', tilt=-8, head_dx=-1, flung=True),
            lambda: build(dx=-1, box_deg=-7, head='wince', tilt=-4, head_dx=0, flung=False)]


def frames_info():
    return B.make_frames(builders())


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.to_image(px))
        a = B.audit(px, fx)
        print(i, st, 'gaps', a['gaps'], 'lone', a['lone'], 'holes', a['holes'], 'keys', a['keys'])
