"""greyson_victory.png: 4 frames of 112x112, looping; feet (56, 111). He won: approved f2, pose B
(the front double biceps with the cannon standing up from his left elbow), held while he laughs.

  0  HA: the shoulders heave up a px, the head thrown back, the mouth wide open ('laugh')
  1  ha: settled, a big grin under the same happy eyes ('grin')
  2  HA: as 0, the head thrown back a px further, the lats spread wider
  3  ha: as 1

The body is gf_fig.pose_b rebuilt part by part (proved against approval f2 with its own flex face
before any frame is made), then moved and given the laughing faces. Like approval f2 he holds no
barbell: both hands are busy flexing.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402
import gan_faces as FC  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_victory'
TIMES = [0.14, 0.12, 0.14, 0.12]
LOOP = True


def build(face, dy=0, head_dy=0, lat=1.5):
    """gf_fig.pose_b with the upper body moved by dy, the head by a further head_dy, and `face`."""
    cv = B.Canvas()
    B.front_base(cv, lat_flare=lat, dy=dy)
    cv.stamp(B.moved(K.despeckle(B.gr_arms.arm('flex', 0)), 0, dy))
    cv.stamp(B.moved(K.despeckle(F.arm_layer(B.gr_arms.FLEX, B.gr_arms.FLEX_FORMS, B.gr_arms.FLEX_SPEC, 1,
                                             keep=('delt', 'biceps', 'upper'))), 0, dy))
    p0, p1 = F.mp((13.6, 58.0 + dy)), F.mp((15.0, 28.0 + dy))
    cv.stamp(B.rec('cannon', B.cannon(p0, p1, face=0.5)))
    B.rec('muzzle', p1)
    cv.stamp(B.rec('hand', B.gr_hands.fist('flex', 0, (15.0, 40.0 + dy))), outline=False)
    cv.stamp(B.rec('head', FC.head(face, 0, dy + head_dy)), outline=False)
    return B.finish(cv, FC.keep(face, 0, dy + head_dy)), set()


def check_base():
    """The rebuild with the approved flex face must be approval f2, pixel for pixel."""
    B.make_frames([lambda: build('flex')], approved={0: 2})


def builders():
    return [lambda: build('laugh', dy=-1, head_dy=-1, lat=1.7),
            lambda: build('grin', dy=0, head_dy=0, lat=1.5),
            lambda: build('laugh', dy=-1, head_dy=-2, lat=1.8),
            lambda: build('grin', dy=0, head_dy=0, lat=1.6)]


def frames_info():
    check_base()
    return B.make_frames(builders())


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.image(px))
        a = B.audit(px, fx)
        print(i, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()},
              {k: len(v) for k, v in a.items()}, 'bbox', B.bbox(px))
