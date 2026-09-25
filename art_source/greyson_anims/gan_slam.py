"""greyson_slam.png: 5 frames of 112x112, played once per slam; feet (56, 111). The barbell hammered
into the floor beside him (it plants the eruption zone under the player).

  0  lift: both arms haul the barbell up over his head, the cannon arm raised to help
  1  peak: the bar up high, the plate straight above his head, the body arched, straining
  2  the swing: the bar coming down over his right side, a speed arc behind the plate
  3  IMPACT: the plate driven into the floor beside his right boot, crouched into it, both arms down
     on the bar, the cannon pressed on it; grit thrown up round the plate (the IMPACT texel)
  4  recover: the plate lifting off the floor as he straightens

Facing right: the plate lands at his right. His right hand grips the bar; the cannon arm helps.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_slam'
# lift + peak + swing = 0.40 s puts the IMPACT on the plan's slam beat (wind-up 2.00-2.40, SLAM at 2.40)
TIMES = [0.15, 0.2, 0.05, 0.14, 0.16]
LOOP = False
IMPACT_FRAME = 3


def cannon_arm(S, E, muzzle, ref=None, tri=(1, 0), face=0.5):
    parts = [(B.arm(S, E, None, tri=tri, ref=ref or B.IDLE_REF), True)]
    c = B.cannon((E[0], E[1] + 0.5), muzzle, face=face)
    B.rec('cannon', c)
    B.rec('muzzle', muzzle)
    parts.append((c, True))
    return parts


def lift():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.5)
    head = B.gr_face.head('flex')
    for p, ol in cannon_arm((84.0, 55.0), (86.0, 36.0), (84.0, 13.0), ref=B.RAISED_REF):
        cv.stamp(p, outline=ol)
    cv.stamp(B.arm((28.0, 55.0), (27.0, 37.0), (32.0, 24.0), tri=(-1, 0), ref=B.RAISED_REF,
                   fore_ref=B.IDLE_REF))
    cv.stamp(B.rec('head', head), outline=False)
    grip, pc = (34.0, 17.0), (92.0, 14.0)
    for p, ol in B.barbell(grip, pc, squash=0.5):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    cv.stamp(B.rec('hand', B.gr_hands.fist('flex', 0, (32.5, 22.0))), outline=False)
    keep = dict(B.gr_face.face('flex'))
    keep.update(B.gr_face.SWEAT)
    return B.finish(cv, keep), set()


def peak():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.8, torso_dy=-1)
    head = B.moved(B.gr_face.head('flex'), 0, -1)
    for p, ol in cannon_arm((84.0, 54.0), (83.0, 35.0), (72.0, 16.0), ref=B.RAISED_REF):
        cv.stamp(p, outline=ol)
    cv.stamp(B.arm((28.0, 54.0), (29.0, 35.0), (40.0, 22.0), tri=(-1, 0), ref=B.RAISED_REF,
                   fore_ref=B.IDLE_REF))
    cv.stamp(B.rec('head', head), outline=False)
    grip, pc = (44.0, 19.0), (57.0, 12.5)
    for p, ol in B.barbell(grip, pc, squash=0.82):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    cv.stamp(B.rec('hand', B.gr_hands.fist('flex', 0, (41.0, 21.0))), outline=False)
    keep = B.moved(B.gr_face.face('flex'), 0, -1)
    keep.update(B.moved(B.gr_face.SWEAT, 0, -1))
    return B.finish(cv, keep), set()


def swing():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.4, dy=1, legs=B.squash_legs(drop=(90,), spread=1))
    head = B.moved(B.gf_faces.head('roar'), 0, 1)
    cv.stamp(B.rec('head', head), outline=False)
    for p, ol in cannon_arm((84.0, 57.0), (95.0, 64.0), (93.0, 44.0), ref=B.IDLE_REF, tri=(1, 0)):
        cv.stamp(p, outline=ol)
    cv.stamp(B.arm((28.0, 57.0), (39.0, 69.0), (58.0, 64.0), tri=(-0.3, 1), ref=B.IDLE_REF))
    grip, pc = (61.0, 62.0), (95.0, 40.0)
    for p, ol in B.barbell(grip, pc, squash=0.5):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    cv.stamp(B.rec('hand', B.gr_hands.fist('idle', 0, (60.0, 58.0))), outline=False)
    fx = B.streaks([(62, 6), (80, 10), (94, 18), (104, 30)], 'X')
    fx.update(B.streaks([(68, 14), (84, 18), (97, 27)], 'W'))
    for q, k in fx.items():
        if q not in cv.px:
            cv.px[q] = k
    return B.finish(cv, B.moved(B.gf_faces.face('roar'), 0, 1)), set(q for q in fx if cv.px.get(q) == fx[q])


GRIT = [(-7, -3), (-9, -6), (-5, -8), (6, -4), (9, -7), (4, -9), (-11, -1), (11, -2)]


def impact():
    drop = (84, 88, 92, 96)
    dy = len(drop)
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.0, dy=dy, legs=B.squash_legs(drop=drop, spread=2))
    head = B.moved(B.gf_faces.head('roar'), 0, dy + 1)
    cv.stamp(B.rec('head', head), outline=False)
    for p, ol in cannon_arm((84.0, 56.0 + dy), (93.0, 68.0 + dy), (93.0, 90.0), ref=B.IDLE_REF, tri=(1, 0)):
        cv.stamp(p, outline=ol)
    cv.stamp(B.arm((28.0, 56.0 + dy), (40.0, 70.0 + dy), (62.0, 76.0), tri=(-0.3, 1), ref=B.IDLE_REF))
    grip, pc = (66.0, 79.0), (92.0, 100.5)
    for p, ol in B.barbell(grip, pc, squash=0.62, ang=-60):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    B.rec('impact', (92.0, 111.0))
    cv.stamp(B.rec('hand', B.gr_hands.fist('idle', 0, (64.0, 72.0))), outline=False)
    fx = {}
    for (gx, gy) in GRIT:
        q = (int(92 + gx), int(108 + gy))
        if q not in cv.px and 0 < q[0] < 111:
            fx[q] = 'X' if (gx + gy) % 2 else 'x'
    for q, k in fx.items():
        cv.px[q] = k
    return B.finish(cv, B.moved(B.gf_faces.face('roar'), 0, dy + 1)), set(fx)


def recover():
    drop = (88, 94)
    dy = len(drop)
    cv = B.Canvas()
    B.front_base(cv, lat_flare=0.8, dy=dy, legs=B.squash_legs(drop=drop, spread=1))
    head = B.moved(B.gf_faces.head('menace'), 0, dy)
    cv.stamp(B.rec('head', head), outline=False)
    for p, ol in cannon_arm((84.0, 56.0 + dy), (91.0, 71.0 + dy), (98.0, 94.0), ref=B.IDLE_REF, tri=(1, 0)):
        cv.stamp(p, outline=ol)
    cv.stamp(B.arm((28.0, 56.0 + dy), (38.0, 70.0 + dy), (60.0, 74.0), tri=(-0.3, 1), ref=B.IDLE_REF))
    grip, pc = (64.0, 76.0), (90.0, 92.0)
    for p, ol in B.barbell(grip, pc, squash=0.6, ang=-55):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    cv.stamp(B.rec('hand', B.gr_hands.fist('idle', 0, (62.0, 70.0))), outline=False)
    return B.finish(cv, B.moved(B.gf_faces.face('menace'), 0, dy)), set()


def builders():
    return [lift, peak, swing, impact, recover]


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
