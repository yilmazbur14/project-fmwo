"""greyson_idle.png: 4 frames of 112x112, looping; feet (56, 111). The fight idle, with the barbell.

  0  the approved fight idle (greyson_fight_approval.png f0), pixel for pixel
  1  breath in: the chest rises a pixel, the lats spread, and he lifts the barbell off his shoulder
  2  the top of the breath, the bar at the top of its bounce, the cannon swinging a pixel out
  3  breathing out, the bar coming back down onto the shoulder

Built exactly like the approved idle (gf_fig.idle), back to front: the approved legs, torso, trunks
and waistband; his right arm in the approved barbell carry (retargeted onto the lifted wrist); the
approved upper left arm; Computah's cannon over the forearm; the 'menace' head; the plate, the bar,
the fist round the bar.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_idle'
TIMES = [0.2, 0.16, 0.2, 0.16]
LOOP = True
APPROVED = {0: 0}                     # frame 0 is the approval sheet's frame 0

PLATE_C = F.PLATE_C                   # (12.5, 30.5)
BAR_GRIP = F.BAR_GRIP                 # (44.5, 61.5)
FIST = (41.0, 55.0)
SOCKET, MUZZLE = F.mp((21.4, 70.0)), F.mp((13.8, 95.0))


def build(dy=0, lat=0.5, bar=0, sway=0):
    """dy: the upper body's rise (negative is up); bar: the barbell's lift on top of it; sway: the
    cannon's muzzle swung out (px)."""
    cv = B.Canvas()
    B.front_base(cv, lat_flare=lat, torso_dy=dy)
    R = B.CARRY_REF
    if dy == 0 and bar == 0:
        right = K.despeckle(F.arm_layer(B.gf_arms.CARRY, B.gf_arms.CARRY_FORMS, B.gf_arms.CARRY_SPEC, 0))
    else:
        right = B.arm((R.S[0], R.S[1] + dy), (R.E[0], R.E[1] + dy), (R.Wr[0], R.Wr[1] + dy + bar),
                      tri=R.tri, ref=R)
    cv.stamp(right)
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, 0, dy))
    s = (SOCKET[0], SOCKET[1] + dy)
    m = (MUZZLE[0] + sway, MUZZLE[1] + dy)
    cannon = B.rec('cannon', B.gf_cannon.cannon(s, m, face=0.62))
    B.rec('muzzle', m)
    cv.stamp(cannon)
    head = B.moved(B.gf_faces.head('menace'), 0, dy)
    cv.stamp(B.rec('head', head), outline=False)
    pc = (PLATE_C[0], PLATE_C[1] + dy + bar)
    grip = (BAR_GRIP[0], BAR_GRIP[1] + dy + bar)
    cv.stamp(B.rec('plate', B.gf_barbell.plate(pc)))
    cv.stamp(B.rec('bar', B.gf_barbell.bar(pc, grip)))
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (FIST[0], FIST[1] + dy + bar))
    cv.stamp(B.rec('hand', fist), outline=False)
    face = B.moved(B.gf_faces.face('menace'), 0, dy)
    return B.finish(cv, face), set()


def builders():
    return [lambda: build(),
            lambda: build(dy=-1, lat=0.8, bar=-1),
            lambda: build(dy=-1, lat=1.0, bar=-2, sway=1),
            lambda: build(dy=0, lat=0.7, bar=-1, sway=1)]


def frames_info():
    return B.make_frames(builders(), approved=APPROVED)


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()},
              {k: len(v) for k, v in a.items()})
