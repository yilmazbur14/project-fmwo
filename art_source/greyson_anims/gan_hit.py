"""greyson_hit.png: 2 frames of 112x112, played once; feet (56, 111). The recoil when a hit lands.

  0  impact: everything above the boots jolts back (the legs lean from planted feet), the head snaps
     back with his eyes squeezed shut, the barbell knocked up off his shoulder, the cannon flung out
  1  recoil: halfway back, still wincing, the bar dropping back onto the shoulder, the cannon swinging in

Built on the fight idle's stance (the barbell on his shoulder), which is where he goes back to.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
import gan_faces as FC  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_hit'
TIMES = [0.08, 0.14]
LOOP = False

PLATE_C = F.PLATE_C
BAR_GRIP = F.BAR_GRIP
FIST = (41.0, 55.0)
SOCKET, MUZZLE = F.mp((21.4, 70.0)), F.mp((13.8, 95.0))


def build(dx, head_dx, head_dy, face, plate_d, grip_d, muzzle_d, lat=0.5):
    cv = B.Canvas()
    B.front_base(cv, lat_flare=lat, dx=dx, legs=B.squash_legs(dx=dx))
    R = B.CARRY_REF
    cv.stamp(B.arm((R.S[0] + dx, R.S[1]), (R.E[0] + dx, R.E[1]),
                   (R.Wr[0] + dx + grip_d[0], R.Wr[1] + grip_d[1]), tri=R.tri, ref=R))
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, dx, 0))
    s = (SOCKET[0] + dx, SOCKET[1])
    m = (MUZZLE[0] + dx + muzzle_d[0], MUZZLE[1] + muzzle_d[1])
    cannon = B.rec('cannon', B.cannon(s, m, face=0.62))
    B.rec('muzzle', m)
    cv.stamp(cannon)
    cv.stamp(B.rec('head', FC.head(face, dx + head_dx, head_dy)), outline=False)
    pc = (PLATE_C[0] + dx + plate_d[0], PLATE_C[1] + plate_d[1])
    grip = (BAR_GRIP[0] + dx + grip_d[0], BAR_GRIP[1] + grip_d[1])
    for p, ol in B.barbell(grip, pc):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (FIST[0] + dx + grip_d[0], FIST[1] + grip_d[1]))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, FC.keep(face, dx + head_dx, head_dy)), set()


def builders():
    return [lambda: build(dx=-2, head_dx=-2, head_dy=-1, face='hurt', plate_d=(2, -6), grip_d=(0, -2),
                          muzzle_d=(4, -3), lat=0.8),
            lambda: build(dx=-1, head_dx=-1, head_dy=0, face='hurt', plate_d=(1, -2), grip_d=(0, -1),
                          muzzle_d=(1, -1), lat=0.6)]


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
