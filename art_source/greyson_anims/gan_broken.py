"""greyson_broken.png: 4 frames of 112x112, looping; feet (56, 111). Broken: dazed and wobbling (the
tiered uppercut's window; the daze stars circle over his crown, which is reported per frame).

  0  swaying to his right (screen left), the head lolling after it
  1  back through the middle
  2  swaying to his left (screen right)
  3  back through the middle, the head dipping

Knees half-buckled, the barbell hanging from his loose grip with its plate dragging on the floor at
his side, the cannon arm hanging dead, the 'daze' face (wall-eyed, tongue out).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
import gan_faces as FC  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_broken'
TIMES = [0.2, 0.16, 0.2, 0.16]
LOOP = True

DROP = (86, 94)


def build(sway, head_dx, head_dy):
    dy = len(DROP)
    cv = B.Canvas()
    B.front_base(cv, lat_flare=0.3, dx=sway, dy=dy, legs=B.squash_legs(drop=DROP, spread=1, dx=sway))
    # his right arm hanging, the barbell dragging from the loose fist
    S = (28.0 + sway, 56.0 + dy)
    E = (23.0 + sway, 73.0 + dy)
    Wr = (25.5 + sway, 84.0 + dy)
    cv.stamp(B.arm(S, E, Wr, tri=(-1, 0), ref=B.IDLE_REF))
    # his left arm hanging dead, the cannon's muzzle near the floor
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, sway, dy))
    s = (90.6 + sway, 70.0 + dy)
    m = (95.0 + sway, 97.0)
    cannon = B.rec('cannon', B.cannon(s, m, face=0.5))
    B.rec('muzzle', m)
    cv.stamp(cannon)
    cv.stamp(B.rec('head', FC.head('daze', sway + head_dx, dy + head_dy)), outline=False)
    grip = (24.0 + sway, 92.0 + dy)
    pc = (13.5, 100.0)
    for p, ol in B.barbell(grip, pc, squash=0.6, ang=-70):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (25.0 + sway, 84.5 + dy))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, FC.keep('daze', sway + head_dx, dy + head_dy)), set()


def builders():
    return [lambda: build(sway=-1, head_dx=-2, head_dy=0),
            lambda: build(sway=0, head_dx=0, head_dy=1),
            lambda: build(sway=1, head_dx=2, head_dy=0),
            lambda: build(sway=0, head_dx=0, head_dy=2)]


def frames_info():
    return B.make_frames(builders())


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()},
              {k: len(v) for k, v in a.items()}, 'bbox', B.bbox(px))
