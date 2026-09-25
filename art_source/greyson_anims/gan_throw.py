"""greyson_throw.png: 4 frames of 112x112, played once per plate; feet (56, 111). He whips the barbell
over his head and flings a weight plate off its end (the plates are his parryable attack).

  0  wind-up (the tell, held while the parry badge shows): the bar cocked up behind his right
     shoulder, the arm in the approved double-biceps shape, the plate high behind him
  1  the whip: the arm snaps up overhead, the bar sweeping over his head, a speed arc behind it
  2  RELEASE: the arm chops down across his body, the bar's end whips out bare at his right as the
     plate flies off it (the FX artist's greyson_plate starts at the RELEASE texel)
  3  follow-through: the bar carried on down across him, empty

His right hand (screen left) holds the bar; the cannon on his left arm swings as a counterweight.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402

K = B.K
F = B.gf_fig
NAME = 'greyson_throw'
# f0 + f1 = 0.35 s puts the RELEASE on the plan's first plate (0.35 s, the parry tell's length); plates 2
# and 3 (0.75, 1.15) replay f1-f3 from 0.08 s before each release.
TIMES = [0.27, 0.08, 0.1, 0.16]
LOOP = False
RELEASE_FRAME = 2


def cannon_arm(E, muzzle, dy=0, face=0.55, S=(84.0, 56.0), ref=None, tri=(1, 0)):
    """His left arm: the upper arm retargeted from an approved arm, the cannon from the elbow."""
    parts = [(B.arm((S[0], S[1] + dy), (E[0], E[1] + dy), None, tri=tri, ref=ref or B.IDLE_REF), True)]
    c = B.cannon((E[0], E[1] + dy + 0.5), (muzzle[0], muzzle[1] + dy), face=face)
    B.rec('cannon', c)
    B.rec('muzzle', (muzzle[0], muzzle[1] + dy))
    parts.append((c, True))
    return parts


def windup():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.2)
    Wr = (19.0, 44.0)
    cv.stamp(B.arm((28.0, 55.0), (15.0, 57.0), Wr, tri=(0, 1), ref=B.FLEX_REF))
    for p, ol in cannon_arm((90.0, 71.5), (99.5, 95.0)):
        cv.stamp(p, outline=ol)
    head = B.gf_faces.head('menace')
    cv.stamp(B.rec('head', head), outline=False)
    grip = (19.5, 37.5)
    pc = (13.5, 15.5)
    for p, ol in B.barbell(grip, pc, squash=0.78):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('flex', 0, (Wr[0], Wr[1] - 3.0))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, B.gf_faces.face('menace')), set()


def whip():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.5)
    for p, ol in cannon_arm((91.5, 70.0), (102.0, 93.0)):
        cv.stamp(p, outline=ol)
    head = B.gf_faces.head('roar')
    cv.stamp(B.rec('head', head), outline=False)
    Wr = (36.0, 25.0)
    cv.stamp(B.arm((28.0, 55.0), (29.0, 38.0), Wr, tri=(-1, 0), ref=B.RAISED_REF, fore_ref=B.IDLE_REF))
    grip = (38.0, 18.0)
    pc = (63.0, 11.5)
    for p, ol in B.barbell(grip, pc, squash=0.55):
        cv.stamp(p, outline=ol)
    B.rec('plate_c', pc)
    fist = B.gr_hands.fist('flex', 0, (Wr[0] + 1.0, Wr[1] - 2.0))
    cv.stamp(B.rec('hand', fist), outline=False)
    fx = B.streaks([(8, 30), (14, 16), (26, 6), (44, 1)], 'X')
    fx.update(B.streaks([(18, 22), (27, 12), (40, 5)], 'W'))
    for q, k in fx.items():
        if q not in cv.px:
            cv.px[q] = k
    return B.finish(cv, B.gf_faces.face('roar')), set(q for q in fx if cv.px.get(q) == fx[q])


def release():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=1.0)
    for p, ol in cannon_arm((92.0, 69.5), (100.5, 92.5)):
        cv.stamp(p, outline=ol)
    head = B.gf_faces.head('roar')
    cv.stamp(B.rec('head', head), outline=False)
    Wr = (55.0, 66.0)
    cv.stamp(B.arm((28.0, 56.0), (38.0, 69.0), Wr, tri=(-0.3, 1), ref=B.IDLE_REF))
    grip = (58.0, 64.0)
    end = (84.0, 84.0)
    for p, ol in B.barbell(grip, None, bare_end=end):
        cv.stamp(p, outline=ol)
    B.rec('release', (88.0, 87.0))
    fist = B.gr_hands.fist('idle', 0, (57.0, 60.0))
    cv.stamp(B.rec('hand', fist), outline=False)
    fx = B.streaks([(70, 44), (84, 56), (92, 72), (92, 84)], 'X')
    fx.update(B.streaks([(64, 50), (78, 62), (86, 76)], 'W'))
    for q, k in fx.items():
        if q not in cv.px:
            cv.px[q] = k
    return B.finish(cv, B.gf_faces.face('roar')), set(q for q in fx if cv.px.get(q) == fx[q])


def follow():
    cv = B.Canvas()
    B.front_base(cv, lat_flare=0.8)
    for p, ol in cannon_arm((91.0, 70.5), (100.0, 94.0)):
        cv.stamp(p, outline=ol)
    head = B.gf_faces.head('menace')
    cv.stamp(B.rec('head', head), outline=False)
    Wr = (60.0, 72.0)
    cv.stamp(B.arm((28.0, 56.0), (39.0, 70.0), Wr, tri=(-0.3, 1), ref=B.IDLE_REF))
    grip = (63.0, 74.0)
    end = (88.0, 97.0)
    for p, ol in B.barbell(grip, None, bare_end=end):
        cv.stamp(p, outline=ol)
    fist = B.gr_hands.fist('idle', 0, (62.0, 69.0))
    cv.stamp(B.rec('hand', fist), outline=False)
    return B.finish(cv, B.gf_faces.face('menace')), set()


def builders():
    return [windup, whip, release, follow]


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
