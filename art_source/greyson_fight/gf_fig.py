"""Greyson's fight frames, built on the approved rig (read-only, via gf_base).

Each front-view frame reuses the approved parts exactly where the pose allows (legs, boots, torso,
trunks, the mane and the approved faces), and differs only where the fight needs it:
  - his LEFT arm (screen right in a front view) wears Computah's cannon over the forearm
    (gf_cannon): the approved delt, triceps and biceps stay flesh, the cannon replaces the forearm
    and the fist;
  - his RIGHT arm (screen left) is flesh, in the pose's own position.
Back views (the rear V, the three-quarter back twist) are built in gf_back.

    python -B gf_fig.py      # prints each frame's numbers and audit; writes nothing
Writing files is gf_export.py's job alone.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_cannon  # noqa: E402
import gf_arms  # noqa: E402
import gf_faces  # noqa: E402
import gf_barbell  # noqa: E402
import gf_back  # noqa: E402
import gf_hands  # noqa: E402
from gr_muscle import Region, RegionLayer  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face, gr_boots = B.K, B.gr_fig, B.gr_arms, B.gr_hands, \
    B.gr_face, B.gr_boots
Canvas, poly, mpts = K.Canvas, K.poly, K.mpts


def arm_layer(polys, forms, spec, side, keep=None):
    """gr_arms.arm, but only the regions named in `keep` (all when None). Left-side coordinates,
    mirrored for side 1 (points and forms mirrored, the light kept upper left)."""
    regions = []
    for name, pts in polys.items():
        if keep is not None and name not in keep:
            continue
        amp, rnd, cast, depth = spec[name]
        pts = mpts(pts) if side else pts
        form = gr_arms._mirror_form(forms[name]) if side else forms[name]
        regions.append(Region(name, poly(pts), amp=amp, round_px=rnd, cast=cast, depth=depth,
                              form=form))
    base = forms['upper'] if not side else gr_arms._mirror_form(forms['upper'])
    return RegionLayer(base, regions).shade(cuts=gr_arms.CUTS)[0]


def finish(cv, keep=()):
    """The last sweep on every frame: orphan skin tones (the hand-drawn face keeps its pixels),
    then any transparent pixel boxed in on four sides (a pinhole between two keylines) is closed
    with keyline, as the approved frames' lines would have it."""
    K.despeckle(cv.px, keep=set(keep))
    x0, y0, x1, y1 = K.bbox(cv.px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in cv.px and all(q in cv.px for q in
                                           ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                cv.px[(x, y)] = 'k'
    return cv


def mp(p):
    """Mirror a left-side point to the right side."""
    return (B.AX - p[0], p[1])


# ------------------------------------------------------------------------------------ frames

def front_base(cv, lat_flare):
    """Legs, boots, torso, trunks and waistband: the approved parts, unchanged."""
    P = gr_fig.Pose('idle')
    P.lat_flare = lat_flare
    for side in (0, 1):
        cv.stamp(K.despeckle(gr_fig.leg(side)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    cv.stamp(K.despeckle(gr_fig.torso(P)))
    cv.stamp(gr_fig.trunks())
    cv.stamp(gr_fig.waistband(), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y)] = 'k'


def pose_b():
    """Pose B, the front double biceps (ref 26.png), on the approved f1: his right arm exactly
    as approved; his left arm keeps the approved delt, triceps and peaked biceps, and the cannon
    stands up from the elbow where the forearm and fist were, the muzzle at temple height."""
    cv = Canvas()
    front_base(cv, lat_flare=1.5)
    cv.stamp(K.despeckle(gr_arms.arm('flex', 0)))
    cv.stamp(K.despeckle(arm_layer(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC, 1,
                                   keep=('delt', 'biceps', 'upper'))))
    p0, p1 = mp((13.6, 58.0)), mp((15.0, 28.0))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.5))
    cv.stamp(gr_hands.fist('flex', 0, (15.0, 40.0)), outline=False)
    cv.stamp(gr_face.head('flex'), outline=False)
    return finish(cv, gr_face.face('flex'))


def spirit():
    """The spirit-bomb raise: the cannon arm ALONE thrust straight up, muzzle to the sky (the
    user: "greyson will be doing it with one arm, his cannon arm only"); the other arm down at
    his side, fist clenched and braced, exactly the approved idle arm; the roar face. The sphere
    is another artist's effect and is not drawn here."""
    cv = Canvas()
    front_base(cv, lat_flare=1.0)
    cv.stamp(K.despeckle(gr_arms.arm('idle', 0)))
    cv.stamp(K.despeckle(arm_layer(gf_arms.RAISED, gf_arms.RAISED_FORMS, gf_arms.RAISED_SPEC, 1)))
    ex, ey = gf_arms.RAISED_ELBOW
    cv.stamp(gf_cannon.cannon(mp((ex, ey + 1.5)), mp((ex + 0.4, 7.0)), face=0.5))
    cv.stamp(gr_hands.fist('idle', 0, (25.0, 84.5)), outline=False)
    cv.stamp(gf_faces.head('roar'), outline=False)
    return finish(cv, gf_faces.face('roar'))


PLATE_C = (12.5, 30.5)           # the plate's centre, up behind his right shoulder
BAR_GRIP = (44.5, 61.5)          # the bar's grip end, below his fist


def idle():
    """The fight idle: the ready stance with his weapons. The barbell rests on his right
    shoulder, gripped in front of the chest, its one plate up behind the shoulder, ready to come
    over in a slam; the cannon hangs from his left elbow, muzzle down and a little out, the bore
    turned toward us like Computah's own idle; the approved legs and trunk; a menacing grin."""
    cv = Canvas()
    front_base(cv, lat_flare=0.5)
    cv.stamp(K.despeckle(arm_layer(gf_arms.CARRY, gf_arms.CARRY_FORMS, gf_arms.CARRY_SPEC, 0)))
    cv.stamp(K.despeckle(arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 1,
                                   keep=('delt', 'upper', 'biceps'))))
    cv.stamp(gf_cannon.cannon(mp((21.4, 70.0)), mp((13.8, 95.0)), face=0.62))
    cv.stamp(gf_faces.head('menace'), outline=False)
    cv.stamp(gf_barbell.plate(PLATE_C))
    cv.stamp(gf_barbell.bar(PLATE_C, BAR_GRIP))
    cv.stamp(gr_hands.fist('idle', 0, (41.0, 55.0)), outline=False)
    return finish(cv, gf_faces.face('menace'))


def back_base(cv, flare):
    """Legs, boots, torso, trunks and waistband seen from behind (gf_back), on the approved
    outlines."""
    for side in (0, 1):
        cv.stamp(K.despeckle(gf_back.back_leg(side)))
    for side in (0, 1):
        cv.stamp(gf_back.back_boot(side), outline=False)
    cv.stamp(K.despeckle(gf_back.back_torso(flare)))
    cv.stamp(gf_back.back_trunks())
    cv.stamp(gf_back.back_waistband(), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y)] = 'k'


def pose_c():
    """Pose C, the rear V (ref 27.png): his back to us, both arms up and out in a wide V. From
    behind his LEFT arm is on the screen's left, so that side of the V is the cannon, muzzle to
    the upper left; his right hand is open with the fingers spread, as in the reference. The
    lats flare wide; the mane hangs down the back."""
    cv = Canvas()
    back_base(cv, flare=3.2)
    cv.stamp(gf_back.back_head(), outline=False)
    cv.stamp(K.despeckle(arm_layer(gf_arms.REAR_V, gf_arms.REAR_V_FORMS, gf_arms.REAR_V_SPEC, 0,
                                   keep=('delt', 'upper', 'biceps'))))
    cv.stamp(K.despeckle(arm_layer(gf_arms.REAR_V, gf_arms.REAR_V_FORMS, gf_arms.REAR_V_SPEC, 1)))
    ex, ey = gf_arms.REAR_V_ELBOW
    cv.stamp(gf_cannon.cannon((ex + 0.4, ey + 1.4), (ex - 8.0, ey - 25.6), face=0.5))
    cv.stamp(gf_hands.hand('open', 1, gf_arms.REAR_V_WRIST), outline=False)
    return finish(cv)


def pose_a():
    """Pose A, the three-quarter back twist (ref 25.png, "the Arnold"): his back to us, the head
    turned to his left in profile, looking along the extended arm; that arm is his left, so it
    is the cannon, aimed out to the screen's left (angled down a little and foreshortened toward
    us so it stays inside the frame, which shows its bore); his right arm up with the elbow high
    and the fist at the back of his head."""
    cv = Canvas()
    back_base(cv, flare=2.4)
    cv.stamp(K.despeckle(arm_layer(gf_arms.TWIST_UP, gf_arms.TWIST_UP_FORMS, gf_arms.TWIST_SPEC,
                                   1)))
    hair, face = gf_back.profile_head()
    cv.stamp(hair)
    cv.stamp(face, outline=False)
    cv.stamp(gr_hands.fist('flex', 1, gf_arms.TWIST_FIST), outline=False)
    cv.stamp(K.despeckle(arm_layer(gf_arms.TWIST_EXT, gf_arms.TWIST_EXT_FORMS, gf_arms.TWIST_SPEC,
                                   0)))
    ex, ey = gf_arms.TWIST_EXT_ELBOW
    cv.stamp(gf_cannon.cannon((ex + 1.2, ey), (ex - 9.6, ey + 9.6), face=0.72))
    return finish(cv, face)


FRAMES = {'idle': idle, 'pose_a': pose_a, 'pose_b': pose_b, 'pose_c': pose_c, 'spirit': spirit}


def build(name):
    return FRAMES[name]()


if __name__ == '__main__':
    for name in FRAMES:
        cv = build(name)
        a = B.audit(cv.px)
        print(name, K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()})
