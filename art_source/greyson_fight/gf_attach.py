"""greyson_attach (3 frames): Greyson jams Computah's cannon onto his left arm (PLAN.md section 6:
"ATTACH (1.0 s): he jams it on, CLANK (shake 8, a green flicker), a flex, and the cannon-arm set
from here on"). Approved rig (read-only, via gf_base), 112x112, feet at (56, 111).

  f0 up       straight on from greyson_tear f4: his right fist still high with the torn arm in it
              (the prop at the same texel), his left arm coming up into the approved double
              biceps; crying and furious
  f1 CLANK    the cannon is on: his left forearm is in the socket (gf_cannon, the worn gauntlet),
              still jolted outward from the jam; a roar through the tears. The shake and the
              green flicker cover the change of hands
  f2 flex     the approved fight pose B, the cannon standing up from his left elbow, with the
              menacing grin: from here on he is smug and the cannon-arm set takes over

In f0 the prop's grip (28, 25) goes on his right fist ('hand'); in f1 and f2 the cannon is part of
his sprite. The cannon's shape is gf_cannon's, unchanged (the prop is built to match it).

    python -B gf_attach.py      # prints each frame's numbers and audit; writes nothing
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_cannon  # noqa: E402
import gf_faces  # noqa: E402
import gf_tear  # noqa: E402
import gf_faces_tk as FT  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face = B.K, B.gr_fig, B.gr_arms, B.gr_hands, B.gr_face
mp = gf_fig.mp

FACE_ROWS = {'rage': FT.RAGE, 'roar_tears': gf_tear.ROAR_TEARS, 'menace': gf_faces.MENACE}


def face_part(name):
    out = {}
    for r, row in enumerate(FACE_ROWS[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FT.FX0 + c, FT.FY0 + r)] = ch
    return out


def head(name):
    part = gr_face.mane()
    fp = face_part(name)
    part.update(fp)
    return part, fp


def up(face):
    """The approved double biceps, both arms flesh (gr_fig.build('flex')'s body), with a face."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=1.5)
    for side in (0, 1):
        cv.stamp(K.despeckle(gr_arms.arm('flex', side)))
    hold = gr_hands.fist('flex', 0, (15.0, 40.0))
    cv.stamp(hold, outline=False)
    cv.stamp(gr_hands.fist('flex', 1, (15.0, 40.0)), outline=False)
    hp, fp = head(face)
    cv.stamp(hp, outline=False)
    gf_fig.finish(cv, fp)
    return cv, gf_tear.centre(hold)


def worn(face, muzzle):
    """Fight pose B's body (gf_fig.pose_b): the right arm the approved flex, the left arm's delt,
    triceps and biceps with the cannon standing up from the elbow to `muzzle` (left-side
    coordinates, mirrored onto his left arm), and a face."""
    cv = K.Canvas()
    gf_fig.front_base(cv, lat_flare=1.5)
    cv.stamp(K.despeckle(gr_arms.arm('flex', 0)))
    cv.stamp(K.despeckle(gf_fig.arm_layer(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC, 1,
                                          keep=('delt', 'biceps', 'upper'))))
    cv.stamp(gf_cannon.cannon(mp((13.6, 58.0)), mp(muzzle), face=0.5))
    cv.stamp(gr_hands.fist('flex', 0, (15.0, 40.0)), outline=False)
    hp, fp = head(face)
    cv.stamp(hp, outline=False)
    gf_fig.finish(cv, fp)
    return cv


FRAMES = [('up', 'rage'), ('clank', 'roar_tears'), ('flex', 'menace')]
UPRIGHT = (15.0, 28.0)       # fight pose B's muzzle (gf_fig.pose_b)
JOLTED = (11.6, 29.8)        # the cannon knocked outward by the jam


def frame(i):
    name, face = FRAMES[i]
    if name == 'up':
        cv, hand = up(face)
        return cv, {'name': name, 'hand': hand}
    muz = JOLTED if name == 'clank' else UPRIGHT
    cv = worn(face, muz)
    return cv, {'name': name, 'muzzle': (K.AX - muz[0], muz[1])}


def _check_pose_b():
    """f2 must be fight pose B exactly, apart from the face."""
    a = gf_fig.pose_b().px
    b = worn('menace', UPRIGHT).px
    face = set(face_part('menace')) | set(gr_face.face('flex')) | set(gr_face.SWEAT)
    diff = [p for p in set(a) | set(b) if a.get(p) != b.get(p) and p not in face]
    if diff:
        raise SystemExit('gf_attach f2 has drifted from fight pose B off the face: %s' % diff[:6])


_check_pose_b()

if __name__ == '__main__':
    for i in range(len(FRAMES)):
        cv, info = frame(i)
        a = B.audit(cv.px)
        print(i, info['name'], K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()}, info)
