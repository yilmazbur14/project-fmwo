"""Greyson's brawl frames (the Punch-Out final phase), on the approved rig in the light crouch.

He faces the player, who stands right in front of him (drawn over him, head at his solar plexus),
so every frame is a FRONT view, never flipped: his right fist on screen left, the cannon gauntlet
(his left arm) on screen right.

Each builder returns (canvas, anchors), anchors in cell texels (x right, y down, feet (56, 111)):
  crown     the top of his hair on the head's centre line
  chin      two rows under the jaw's keyline, as the plan measures it
  fist      his right fist's centre
  gauntlet  the cannon's striking end: the centre of its muzzle ring
  muzzle    the centre of the bore's dark face (where a glow sits)
  contact   (strikes) the texel his punch lands on

    python -B gb_fig.py      # numbers and anchors of every frame; writes nothing
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402
import gb_body as BD  # noqa: E402
import gb_faces  # noqa: E402

K, G, P = B.K, B.G, B.P
gr_arms, gr_hands, gr_face = G.gr_arms, G.gr_hands, G.gr_face
gf_arms, gf_cannon = G.gf_arms, G.gf_cannon
Canvas, moved, mp = K.Canvas, BD.moved, P.mp

P.FACES_NEW.update({n: (lambda n=n: gb_faces.face(n)) for n in gb_faces.FACES})

CARRY_ELBOW = (24.0, 73.0)
CARRY_FISTPT = (41.0, 55.0)      # where the fight idle's fist sits on the carry arm


def rnd(p):
    return (int(round(p[0])), int(round(p[1])))


def fist_centre(part):
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    return ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)


def bore_centre(cannon_part):
    pts = [p for p, k in cannon_part.items() if k in ('z', 'Z')]
    return fist_centre(pts) if pts else None


def anchors(head_dy, head_dx, fist, cannon_p1, cannon_part, contact=None):
    crown = P.crown_of(moved(gr_face.mane(), head_dx, head_dy))
    out = {'crown': crown, 'chin': (56 + head_dx, B.JAW_ROW + head_dy + B.CHIN_BELOW_JAW),
           'fist': fist, 'gauntlet': rnd(cannon_p1), 'muzzle': bore_centre(cannon_part)}
    if contact is not None:
        out['contact'] = contact
    return out


FIST_TARGET = (42, 61)


def guard_arm_right(cv, d, sh=0.0, el=0.0, fist_map='flex', target=FIST_TARGET):
    """His right arm up in the guard: the fight idle's carry arm (fist in front of the chest)
    dropped with the body; the fist stood up in front of the chin, placed so its centre sits on
    `target`."""
    arm = P.Arm(gf_arms.CARRY, gf_arms.CARRY_FORMS, P.I_SHOULDER, CARRY_ELBOW, sh=sh, el=el)
    cv.stamp(moved(K.despeckle(P.arm_layer(arm, gf_arms.CARRY_SPEC, 0)), 0, d))
    fp = arm.fore(CARRY_FISTPT)
    f = gr_hands.fist(fist_map, 0, (fp[0], fp[1] + d))
    if target is not None:
        c = fist_centre(f)
        f = moved(f, target[0] - c[0], target[1] - c[1])
    return arm, f


def guard(d=4, head_dy=7, face='menace', gauntlet=(70.0, 63.0), lat=1.0, fist_map='idle',
          sh=6.0, el=-6.0, cn_face=0.35, fist=FIST_TARGET):
    """greyson_brawl_guard: the light crouch, the right fist up in front of the chin, the gauntlet
    up at the other cheek, muzzle up. `fist`: where the right fist's centre sits."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=lat)
    hp, fpx = BD.head(face, 0, head_dy)
    cv.stamp(hp, outline=False)
    arm, fist = guard_arm_right(cv, d, sh, el, fist_map, target=fist)
    # his left arm: the carry upper arm mirrored, the cannon rising from its elbow to the cheek
    cv.stamp(moved(K.despeckle(P.arm_layer(arm, gf_arms.CARRY_SPEC, 1,
                                           keep=('delt', 'upper', 'biceps'))), 0, d))
    e = mp(arm.upper(CARRY_ELBOW))
    p0 = (e[0], e[1] + d)
    cn = gf_cannon.cannon(p0, gauntlet, face=cn_face)
    cv.stamp(cn)
    cv.stamp(fist, outline=False)
    P.finish(cv, fpx)
    return cv, anchors(head_dy, 0, fist_centre(fist), gauntlet, cn)


def hook_l_strike(d=4, head=(-2, 7), elbow=(84.0, 64.0), contact=(56.0, 73.0), face='flex',
                  cn_face=0.3, stub=True, fist_map='idle'):
    """greyson_brawl_hook_l STRIKE: the cannon hook landing. His left shoulder driven forward,
    the upper arm pointing at the player (foreshortened to its delt and a stub), the gauntlet
    swung level across his chest so its muzzle ring lands on the player's head point; the right
    fist stays up in the guard; teeth gritted."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=1.2)
    hp, fpx = BD.head(face, head[0], head[1])
    cv.stamp(hp, outline=False)
    arm, fist = guard_arm_right(cv, d, 6.0, -6.0, fist_map)
    # the punching arm: the approved flex delt and a short capsule for the upper arm, in
    # left-side coordinates, mirrored to screen right
    sh_pt = (31.0, 56.5)
    el_l = mp(elbow)
    el_l = (el_l[0], el_l[1] - d)
    polys = {'delt': gr_arms.FLEX['delt'], 'upper': P.capsule(sh_pt, el_l, 7.0, 6.6)}
    if not stub:
        polys['upper'] = polys['delt']
    forms = {'delt': gr_arms.FLEX_FORMS['delt'], 'upper': P.Form(axis=[sh_pt, el_l], r=7.0)}
    spec = {'delt': gr_arms.FLEX_SPEC['delt'], 'upper': (1.6, 2.8, 2, 2)}
    punch = P.Arm(polys, forms, sh_pt, el_l)
    cv.stamp(moved(K.despeckle(P.arm_layer(punch, spec, 1)), 0, d))
    cn = gf_cannon.cannon(elbow, contact, face=cn_face)
    cv.stamp(cn)
    cv.stamp(fist, outline=False)
    P.finish(cv, fpx)
    return cv, anchors(head[1], head[0], fist_centre(fist), contact, cn, contact=rnd(contact))


def dazed(d=6, head_dy=13, lat=0.5):
    """greyson_brawl_dazed: slumped. The knees gone, the guard dropped: both arms hanging (the
    approved idle arm, the fight idle's hanging cannon), the head sagging forward onto his
    chest, the dazed face. Chin at 46 above the soles."""
    cv = Canvas()
    BD.front_base(cv, d, lat_flare=lat)
    arm = P.Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, P.I_SHOULDER, P.I_ELBOW)
    cv.stamp(moved(K.despeckle(P.arm_layer(arm, gr_arms.SPEC, 0)), 0, d))
    up = P.Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, P.I_SHOULDER, P.I_ELBOW)
    cv.stamp(moved(K.despeckle(P.arm_layer(up, gr_arms.SPEC, 1, keep=('delt', 'upper', 'biceps'))),
                   0, d))
    p0, p1 = mp(P.CANNON_HANG[0]), mp(P.CANNON_HANG[1])
    p0, p1 = (p0[0], p0[1] + d), (p1[0], p1[1] + d)
    cn = gf_cannon.cannon(p0, p1, face=0.62)
    cv.stamp(cn)
    fist = gr_hands.fist('idle', 0, (P.IDLE_FIST[0], P.IDLE_FIST[1] + d))
    cv.stamp(fist, outline=False)
    hp, fpx = BD.head('dazed', 0, head_dy)
    cv.stamp(hp, outline=False)
    P.finish(cv, fpx)
    return cv, anchors(head_dy, 0, fist_centre(fist), p1, cn)


APPROVAL = [('greyson_brawl_guard f0', guard, {}),
            ('greyson_brawl_hook_l strike', hook_l_strike, {}),
            ('greyson_brawl_dazed f0', dazed, {})]


if __name__ == '__main__':
    for title, fn, kw in APPROVAL:
        cv, a = fn(**kw)
        st = K.stats(cv.image())
        au = G.audit(cv.px)
        print('%-28s black %.1f%% colours %d bbox %s' % (title, 100 * st['black'], st['colours'], K.bbox(cv.px)))
        print('   ', a, 'clean' if not any(au.values()) else {k: len(v) for k, v in au.items() if v})
