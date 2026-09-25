"""Greyson posed for the juggle: the approved parts hinged at their joints and turned as one.

A Fig is one frame's pose, in the approved rig's own terms:
  angle, pivot, at, squash   the whole body: turned `angle` about `pivot` (his own space), the
                             pivot put on `at` (the frame), squashed on the screen (the crash);
  flare                      the lats' spread (the approved Pose.lat_flare; the breath swells it);
  arm = (up, fore)           his RIGHT arm, flesh (screen left in the front view): the upper arm
                             swung `up` degrees OUTWARD at the shoulder, the forearm a further
                             `fore` outward at the elbow; the delt turns half as far (it caps the
                             shoulder, which turns less than the arm; gf_limb's rule);
  gun = (up, fore)           his LEFT arm, the cannon arm: the flesh upper arm swung the same way,
                             and the cannon (his forearm, the approved fight idle's) at the elbow;
  gun_face                   how far the muzzle's face turns toward us (gf_cannon's `face`);
  legs = (l, r)              each leg swung outward at the hip, the boot with it;
  head, head_shift, face     the head tipped on the neck (degrees) and moved (his own space), and
                             the face on it.
OUTWARD is away from his middle for both sides: clockwise on screen for the screen-left limbs,
anticlockwise for the others.

Every part is the approved one, through gj_rig: nothing is redrawn, and the light stays upper left
at every angle. Build order is the approved one (gf_fig.pose_b's): legs, boots, torso, trunks,
waistband, the flesh arm, the cannon arm and its cannon, the fist, the head; then gf_fig.finish.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gj_rig as R  # noqa: E402

K, gr_arms, gr_hands, gf_cannon, gf_fig, gf_hands = (R.K, R.gr_arms, R.gr_hands, R.gf_cannon,
                                                      R.gf_fig, R.gf_hands)
mp = R.mp

BODY = (56.0, 68.0)       # his middle: the tumble turns about it
SOLES = (56.0, 111.0)     # his feet, on the approved frame's bottom row
HANDS = {'idle': gr_hands.IDLE_L, 'flex': gr_hands.FLEX_L, 'open': gf_hands.OPEN_L}


class Fig(object):
    def __init__(self, angle=0.0, pivot=BODY, at=(96.0, 100.0), squash=(1.0, 1.0), flare=0.5,
                 arm=(0.0, 0.0), gun=(0.0, 0.0), gun_face=0.62, legs=(0.0, 0.0), head=0.0,
                 head_shift=(0.0, 0.0), face='idle', hand='idle', hand_snap=True,
                 head_last=True, head_shear=True):
        self.angle, self.pivot, self.at, self.squash = angle, pivot, at, squash
        self.flare, self.arm, self.gun, self.gun_face = flare, arm, gun, gun_face
        self.legs, self.head, self.head_shift, self.face = legs, head, head_shift, face
        self.hand, self.hand_snap, self.head_last = hand, hand_snap, head_last
        self.head_shear = head_shear

    def body_tf(self):
        return R.Tf.make(self.angle, pivot=self.pivot, dest=self.at, squash=self.squash)


def _arm_tfs(Tb, side, up, fore):
    """{region: Tf} for an arm swung `up` outward at the shoulder and `fore` at the elbow, and
    the forearm's Tf (for the fist or the cannon)."""
    sg = -1.0 if side else 1.0
    S = mp(R.SHOULDER) if side else R.SHOULDER
    E = mp(R.ELBOW) if side else R.ELBOW
    t_up = Tb.sub(S, sg * up)
    t_delt = Tb.sub(S, sg * up * 0.5)
    t_lo = t_up.sub(E, sg * fore)
    return {'delt': t_delt, 'upper': t_up, 'biceps': t_up, 'forearm': t_lo, 'brach': t_lo}, t_lo


def _snapped(T, anchor, snap):
    """The fist's own Tf: T itself, or T's turn snapped to the nearest quarter turn about the
    fist's anchor pixel (a whole-pixel copy of the approved structure, no resampling)."""
    if not snap or T.whole():
        return T
    q = 90.0 * round(T.angle / 90.0)
    X, Y = T.fwd(*anchor)
    return R.Tf.make(q, pivot=anchor, dest=(round(X), round(Y)))


def draw(F, face_map, face_px, pad=0):
    """F: a Fig. face_map: the head (the mane with the face over it); face_px: the face's own
    pixels (kept by the final sweep). -> the Canvas. With `pad`, he is drawn into a canvas that
    much bigger all round and moved in by it, so nothing is clipped (for measuring)."""
    if pad:
        F = Fig(**dict(F.__dict__, at=(F.at[0] + pad, F.at[1] + pad)))
    Tb = F.body_tf()
    cv = K.Canvas(R.W + 2 * pad, R.H + 2 * pad)
    cv.fx = set()           # effect pixels (gj_fx), drawn after the figure
    t_legs = []
    for side in (0, 1):
        hip = mp(R.HIP) if side else R.HIP
        t_legs.append(Tb.sub(hip, (-1.0 if side else 1.0) * F.legs[side]))
    for side in (0, 1):
        cv.stamp(K.despeckle(R.t_leg(side, t_legs[side])))
    for side in (0, 1):
        part, ol = R.t_boot(side, t_legs[side])
        cv.stamp(part, outline=ol)
    cv.stamp(K.despeckle(R.t_torso(F.flare, Tb)))
    cv.stamp(R.t_trunks(Tb))
    cv.stamp(R.t_waistband(Tb), outline=False)
    for q in R.t_waistband_line(Tb):
        cv.px[q] = 'k'

    t_head = Tb.sub(R.NECK, F.head, F.head_shift)
    head, keep, head_ol = R.t_head(face_map, face_px, t_head,
                                   pivot=R.NECK if F.head_shear else None)
    if not F.head_last:
        cv.stamp(head, outline=head_ol)

    # his right arm, flesh
    ts, t_lo = _arm_tfs(Tb, 0, *F.arm)
    cv.stamp(K.despeckle(R.t_arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 0, ts)))
    # his left arm: the flesh upper arm, and the cannon on the forearm
    gs, g_lo = _arm_tfs(Tb, 1, *F.gun)
    cv.stamp(K.despeckle(R.t_arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 1, gs,
                                       keep=('delt', 'upper', 'biceps'))))
    p0 = gs['upper'].fwd(*mp(R.CANNON_SOCKET))
    p1 = g_lo.fwd(*mp(R.CANNON_MUZZLE))
    cv.stamp(gf_cannon.cannon(p0, p1, face=F.gun_face))
    # the fist on his right arm
    rows = HANDS[F.hand]
    fist_anchor = (int(round(R.FIST[0])), int(round(R.FIST[1])))
    part, ol = R.t_hand(rows, 0, R.FIST, _snapped(t_lo, fist_anchor, F.hand_snap))
    cv.stamp(part, outline=ol)
    if F.head_last:
        cv.stamp(head, outline=head_ol)
    gf_fig.finish(cv, keep)
    cv.tf = {'body': Tb, 'head': t_head, 'legs': t_legs, 'arm': t_lo, 'gun': g_lo,
             'muzzle': p1}
    cv.fig = F
    return cv


def extent(cv):
    return K.bbox(cv.px)
