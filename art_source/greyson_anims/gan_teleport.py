"""greyson_teleport.png: 3 frames of 112x112; feet (56, 111). The crouch and brace before he vanishes
(the FX artist's warp draws the beam); played backwards it is his landing on the way in.

  0  crouch: knees bending out, the barbell hugged in on his shoulder, the cannon pulled in low
  1  brace: sunk deep into the squat, chin down, every muscle clenched (the flex grimace)
  2  spring: he drives up out of the squat, stretched tall, as the beam takes him

Built on the approved front parts: the legs squashed (rows taken out of the thighs and shins, the
knees opening outward, the soles fixed on row 111) and everything above them sunk to match.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_teleport'
TIMES = [0.1, 0.1, 0.05]
LOOP = False

PLATE_C = F.PLATE_C
BAR_GRIP = F.BAR_GRIP
FIST = (41.0, 55.0)
SOCKET, MUZZLE = F.mp((21.4, 70.0)), F.mp((13.8, 95.0))


def build(drop, spread, face, lat=0.8, stretch=(), tuck=0):
    """drop: leg rows taken out (the body sinks that many px); stretch: leg rows doubled (the body
    rises that many px, the spring); tuck: the cannon pulled in toward the body (px)."""
    dy = len(drop) - len(stretch)
    cv = B.Canvas()
    B.front_base(cv, lat_flare=lat, dy=dy, legs=B.squash_legs(drop=drop, spread=spread, stretch=stretch))
    R = B.CARRY_REF
    cv.stamp(B.arm((R.S[0], R.S[1] + dy), (R.E[0] + 1, R.E[1] + dy), (R.Wr[0], R.Wr[1] + dy - 1),
                   tri=R.tri, ref=R))
    upper = K.despeckle(F.arm_layer(B.gr_arms.IDLE, B.gr_arms.IDLE_FORMS, B.gr_arms.SPEC, 1,
                                    keep=('delt', 'upper', 'biceps')))
    cv.stamp(B.moved(upper, 0, dy))
    s = (SOCKET[0] - tuck * 0.3, SOCKET[1] + dy)
    m = (MUZZLE[0] - tuck, MUZZLE[1] + dy - tuck * 0.5)
    cannon = B.rec('cannon', B.cannon(s, m, face=0.62))
    B.rec('muzzle', m)
    cv.stamp(cannon)
    head = B.moved(B.gf_faces.head(face) if face != 'flex' else B.gr_face.head('flex'), 0, dy + 1)
    cv.stamp(B.rec('head', head), outline=False)
    pc = (PLATE_C[0] + 2, PLATE_C[1] + dy + 1)
    grip = (BAR_GRIP[0], BAR_GRIP[1] + dy - 1)
    for p, ol in B.barbell(grip, pc):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('idle', 0, (FIST[0], FIST[1] + dy - 1))
    cv.stamp(B.rec('hand', fist), outline=False)
    keep = B.moved(B.gf_faces.face(face) if face != 'flex' else B.gr_face.face('flex'), 0, dy + 1)
    if face == 'flex':
        keep.update(B.moved(B.gr_face.SWEAT, 0, dy + 1))
    return B.finish(cv, keep), set()


def builders():
    return [lambda: build(drop=(84, 90, 96), spread=1, face='menace', lat=0.8, tuck=1),
            lambda: build(drop=(82, 85, 88, 91, 94, 97), spread=2, face='flex', lat=1.2, tuck=3),
            lambda: build(drop=(), spread=0, face='roar', lat=1.4, stretch=(86, 94))]


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
