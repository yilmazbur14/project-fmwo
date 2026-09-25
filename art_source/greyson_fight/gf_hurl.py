"""greyson_hurl (4 frames): Greyson throws the armless Computah out of the ring, right after the
attach. The user, 2026-09-24 playtest: "during the greyson intro cutscene, after he has ripped the
cannon arm, greyson needs to throw computah out the ring so hes no longer in the way".

The cannon-arm look (the cannon on his LEFT arm, screen right, as in greyson_walk_cannon and
greyson_talk_cannon), on the approved rig (read-only, via gf_base): 112x112, feet at (56, 111).
Drawn with Computah lying on his screen-LEFT, where greyson_tear and greyson_attach leave him, and
thrown to screen-RIGHT; the code flips it, together with Computah, for the other rope.

  f0 grab     squatting and leaning in to his left, his right fist down at Computah's chest on
              the mat; the cannon swung out behind for balance; the menacing grin
  f1 press    upright and braced, Computah pressed overhead on his right arm ALONE while the
              cannon flexes up beside his head (fight pose B's cannon arm): a show-off; the
              approved flex face (gritted teeth, the vein swollen, the sweat bead)
  f2 heave    the throw: leaning hard to screen-right, his right hand flung open up and over his
              head after Computah, the cannon swept up to the right with it; roaring
  f3 settle   the smug cannon stance, exactly greyson_talk_cannon f0, so the walk and the talk
              pick up from it without a pop

Computah is NOT drawn here: the grip is empty and he is his own sprite (computah_armless on the
mat, then computah_armless_tumble). Each frame reports 'hand' (the hand's centre, in continuous
texels, (0, 0) the frame's top-left corner) and, in its docstring table below, which of
Computah's frames goes there.

    python -B gf_hurl.py      # prints each frame's numbers and audit; writes nothing
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_walk  # noqa: E402
import gf_limb  # noqa: E402
import gf_tear  # noqa: E402
import gf_cannon  # noqa: E402
import gf_attach  # noqa: E402
import gf_cannonset  # noqa: E402
import gf_faces  # noqa: E402
import gf_hands  # noqa: E402
import gf_faces_tk as FT  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face, gr_boots = B.K, B.gr_fig, B.gr_arms, B.gr_hands, \
    B.gr_face, B.gr_boots
mp, moved, shear, slid = gf_fig.mp, gf_tear.moved, gf_tear.shear, gf_tear.slid
HIP = gf_tear.HIP
CROWN = (56.0, 26)           # the approved mane's top keyline row, centred: his crown at rest
UP, LO = gf_tear.UPPER_LEN, gf_tear.LOWER_LEN


def along(p, deg, length):
    """The point `length` texels from p along a screen bearing (0 right, -90 straight up)."""
    a = math.radians(deg)
    return (p[0] + math.cos(a) * length, p[1] + math.sin(a) * length)


def lower_body(drop, lean, lat_flare):
    """The approved legs with the hips dropped by `drop`, the boots planted, and the trunk (neck,
    traps, chest, lats and abs) leaned by `lean` over the hips, as in greyson_tear."""
    hip = HIP + drop
    cv = K.Canvas()
    for side in (0, 1):
        cv.stamp(K.despeckle(gf_walk.posed_leg(side, drop, 0)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    P = gr_fig.Pose('idle')
    P.lat_flare = lat_flare
    cv.stamp(shear(moved(K.despeckle(gr_fig.torso(P)), 0, drop), lean, hip))
    cv.stamp(moved(gr_fig.trunks(), 0, drop))
    cv.stamp(moved(gr_fig.waistband(), 0, drop), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y + drop)] = 'k'
    return cv, hip


def upper_arm(S, E, side):
    """The approved idle arm's upper regions (delt, triceps, biceps) re-posed so the shoulder is
    S and the elbow E, shaded for `side`. The forearm is left out: the cannon replaces it."""
    W = along(E, math.degrees(math.atan2(E[1] - S[1], E[0] - S[0])), LO)
    polys, forms = gf_limb.repose(S, E, W)
    part = gf_fig.arm_layer(polys, forms, gr_arms.SPEC, side, keep=('delt', 'upper', 'biceps'))
    return K.despeckle(part)


def finish(cv, keep):
    """gf_fig.finish, then any colour pixel left touching transparency where two stamped parts
    meet (a hand's heel over a forearm, say) gets its keyline, and pinholes are closed again."""
    gf_fig.finish(cv, keep)
    seams = set()
    for (x, y), k in cv.px.items():
        if k == 'k':
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in cv.px:
                seams.add(q)
    for q in seams:
        cv.px[q] = 'k'
    gf_fig.finish(cv, keep)
    return cv


def head_part(face, extras=None):
    """The approved mane with a face (an approved, fight or takeover one) laid over it; returns
    (part, the face's own pixels, which the final sweep keeps)."""
    part = gr_face.mane()
    if face in FT.FACES:
        fp = FT.face(face)
    else:
        fp = gf_faces.face(face)
    part.update(fp)
    if extras:
        part.update(extras)
    return part, fp


# ------------------------------------------------------------------------------------ f0 grab

GRAB_DROP, GRAB_LEAN = 7, -6
GRAB_WRIST = (15.0, 88.0)             # his right wrist, down at the mat on his left
GRAB_FIST = (15.0, 90.5)              # the approved 'idle' fist's anchor under it
GRAB_CANNON = ((21.4, 70.0), (11.0, 92.0))  # elbow and muzzle, left-side coordinates: swung out


def grab():
    drop, lean = GRAB_DROP, GRAB_LEAN
    cv, hip = lower_body(drop, lean, 0.5)
    # his left arm, the cannon: the approved upper arm, the gauntlet swung out behind him for
    # balance (left-side coordinates, mirrored; see gf_tear for why the lean is subtracted)
    upper = gf_fig.arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 1,
                             keep=('delt', 'upper', 'biceps'))
    cv.stamp(shear(moved(K.despeckle(upper), 0, drop), lean, hip))
    (ex, ey), (mx_, my_) = GRAB_CANNON
    sl = slid(lean, ey + drop, hip)
    gun = gf_cannon.cannon(mp((ex - sl, ey + drop)), mp((mx_ - sl, my_ + drop)),
                           face=gf_walk.CANNON_FACE)
    cv.stamp(gun)
    # his right arm reaching down to his left, straight to the fist
    sh = (30.0 + slid(lean, 56 + drop, hip), 56.0 + drop)
    el = gf_tear.ik(sh, GRAB_WRIST)
    cv.stamp(gf_limb.arm(sh, el, GRAB_WRIST, 0))
    fist = gr_hands.fist('idle', 0, GRAB_FIST)
    cv.stamp(fist, outline=False)
    hx = int(round(slid(lean, 40 + drop, hip)))
    head, fp = head_part('menace')
    cv.stamp(moved(head, hx, drop), outline=False)
    keep = {(x + hx, y + drop) for (x, y) in fp}
    finish(cv, keep)
    return cv, {'name': 'grab', 'hand': gf_tear.centre(fist), 'crown': (CROWN[0] + hx, CROWN[1] + drop)}


# ------------------------------------------------------------------------------------ f1 press

PRESS_DROP = 1
PRESS_SHOULDER = (30.0, 56.0)
PRESS_ELBOW = (28.6, 38.6)            # straight up: the approved upper arm's length
PRESS_WRIST = (28.0, 27.0)
PRESS_FIST = (28.0, 29.0)             # the approved raised ('flex') fist's anchor, its heel


def press():
    drop = PRESS_DROP
    cv, hip = lower_body(drop, 0, 1.5)
    # his left arm: fight pose B's, the delt, triceps and peaked biceps with the cannon standing
    # up from the elbow beside his head (gf_attach.worn's left arm, dropped with the hips)
    left = gf_fig.arm_layer(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC, 1,
                            keep=('delt', 'biceps', 'upper'))
    cv.stamp(moved(K.despeckle(left), 0, drop))
    ux, uy = gf_attach.UPRIGHT
    cv.stamp(gf_cannon.cannon(mp((13.6, 58.0 + drop)), mp((ux, uy + drop)), face=0.5))
    # his right arm straight up, pressing Computah overhead one-handed
    sh = (PRESS_SHOULDER[0], PRESS_SHOULDER[1] + drop)
    el = (PRESS_ELBOW[0], PRESS_ELBOW[1] + drop)
    wr = (PRESS_WRIST[0], PRESS_WRIST[1] + drop)
    cv.stamp(gf_limb.arm(sh, el, wr, 0))
    fist = gr_hands.fist('flex', 0, (PRESS_FIST[0], PRESS_FIST[1] + drop))
    cv.stamp(fist, outline=False)
    head, fp = head_part('flex', gr_face.SWEAT)
    cv.stamp(moved(head, 0, drop), outline=False)
    keep = {(x, y + drop) for (x, y) in fp}
    finish(cv, keep)
    info = {'name': 'press', 'hand': gf_tear.centre(fist), 'crown': (CROWN[0], CROWN[1] + drop),
            'fx': {(x, y + drop) for (x, y) in gr_face.SWEAT}}
    return cv, info


# ------------------------------------------------------------------------------------ f2 heave

HEAVE_DROP, HEAVE_LEAN = 2, 9
HEAVE_ARM = (-80.0, -48.0)            # screen bearings of his right upper arm and forearm
HEAVE_CANNON = (-118.0, -104.0)       # left-side bearings of his left upper arm and the cannon
CANNON_LEN = 30.0                     # the worn gauntlet's length in pose B and the raise


def heave():
    drop, lean = HEAVE_DROP, HEAVE_LEAN
    cv, hip = lower_body(drop, lean, 1.2)
    # his left arm, the cannon, swept up to the right after the throw (left-side coordinates,
    # mirrored: a bearing toward smaller x here points to the screen's right)
    sl = slid(lean, 56 + drop, hip)
    S = (30.0 - sl, 56.0 + drop)
    E = along(S, HEAVE_CANNON[0], UP)
    cv.stamp(upper_arm(S, E, 1))
    M = along(E, HEAVE_CANNON[1], CANNON_LEN)
    cv.stamp(gf_cannon.cannon(mp((E[0] + 0.3, E[1] + 1.2)), mp(M), face=0.5))
    # his right arm flung up and over his head, the hand open: Computah has just left it
    S = (30.0 + sl, 56.0 + drop)
    E = along(S, HEAVE_ARM[0], UP)
    W = along(E, HEAVE_ARM[1], LO)
    cv.stamp(gf_limb.arm(S, E, W, 0))
    hand = gf_hands.hand('open', 0, (W[0] + 0.5, W[1] - 1.0))
    hx = int(round(slid(lean, 40 + drop, hip)))
    head, fp = head_part('roar')
    cv.stamp(moved(head, hx, drop), outline=False)
    cv.stamp(hand, outline=False)
    keep = {(x + hx, y + drop) for (x, y) in fp}
    finish(cv, keep)
    return cv, {'name': 'heave', 'hand': gf_tear.centre(hand), 'crown': (CROWN[0] + hx, CROWN[1] + drop)}


# ------------------------------------------------------------------------------------ f3 settle

def settle():
    cv = gf_cannonset.stance('smug')
    return cv, {'name': 'settle', 'mouth': FT.MOUTH['smug'], 'crown': CROWN}


FRAMES = [grab, press, heave, settle]

# Which of Computah's frames goes on the hand, per frame (the coordinator relays these):
#   f0  computah_armless f0, lying as greyson_attach left him; the hand closes on his chest
#   f1  computah_armless_tumble f0 ('held', level, limp), its GRIP texel on the hand, drawn
#       BEHIND Greyson so the fist reads as gripping him
#   f2  computah_armless_tumble f0 at the hand on the frame's first tick, then launched up and
#       to the right over the rope, f1-f4 looping
#   f3  none: he is gone


def frame(i):
    return FRAMES[i]()


if __name__ == '__main__':
    for i in range(len(FRAMES)):
        cv, info = frame(i)
        a = B.audit(cv.px, info.get('fx', ()))
        print(i, info['name'], K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()}, 'hand', info.get('hand'))
