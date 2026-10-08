"""The rider composer: Jordan astride the kaiju's head, built exactly in jr_ride.build's order (the
approved rider's) with every part replaceable: the upper body's lean, the head, either arm, the box,
the near shin's swing. With the defaults it IS the approved rider (checked in _selftest).

Build coordinates throughout; SEAT_PT (49, 70) is the texel he sits on (the kaiju's RIDER_SEAT).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jr_common as C  # noqa: E402
import jr_fig as F     # noqa: E402
import jr_ride as R    # noqa: E402

V, JB = F.V, F.JB
K = C


def near_leg_swing(sdx=0, sdy=0):
    """jr_ride.near_leg with the dangling shin swung: the ankle (and the stacks and shoe) moved by
    (sdx, sdy); the thigh and knee stay. sdx = sdy = 0 is jr_ride.near_leg exactly."""
    thigh = JB.kit.capsule((46.4, 68.6), (53.6, 71.4), 2.6, 2.4)
    knee = K.ellipse(54.4, 72.0, 2.5, 2.3)
    shin = JB.kit.capsule((54.2, 73.2), (53.8 + sdx, 81.0 + sdy), 1.9, 1.9)
    stack = K.poly([(51.2 + sdx, 80.0 + sdy), (56.6 + sdx, 80.0 + sdy), (57.0 + sdx, 83.6 + sdy),
                    (50.6 + sdx, 83.6 + sdy)])
    part = R._jeans(thigh | knee | shin | stack)
    for (x, y) in list(part):
        if part[(x, y)] == 'N' and (x, y - 1) not in part and x < 54:
            part[(x, y)] = 's'
    for q in ((53, 70), (54, 70), (55, 71)):
        if q in part:
            part[q] = 'S'
    K.stroke(part, [(51 + sdx, 81 + sdy), (53 + sdx, 82 + sdy), (56 + sdx, 81 + sdy)], 'n', only='NsS')
    K.stroke(part, [(52 + sdx, 83 + sdy), (55 + sdx, 83 + sdy)], 's', only='N')
    return part


def near_shoe(sdx=0, sdy=0, heel_k=True):
    """The approved dangling sneaker moved with the shin. heel_k: one keyline pixel over its heel at
    (49, 82): the approved rider leaves that heel pixel touching the kaiju's skin behind it (a gap
    in the rider on its own); every frame but the approved one closes it."""
    part = C.shift(R.near_shoe(), sdx, sdy)
    if heel_k:
        part[(49 + sdx, 82 + sdy)] = 'k'
    return part


def rider(up=(0, 0), head=None, far=None, near=None, box=None, far_hand=None, shin=(0, 0),
          shirt_frame=0, near_over_box=False, far_leg_on=True, extra_under=None, fig=None, approved=False):
    """Compose a rider frame (a jr_fig.Fig). Defaults = the approved rider.
      up        (dx, dy) of the upper body: neck, tee, dandruff (arms, head, box are given absolute)
      head      a head part (absolute); default: 'admire' at HEAD_AT + up
      far       far arm parts [(part, outline)]; default v2's far_arm_box moved by up
      near      near arm parts [(part, outline)]; default v2's near_arm_hip moved by up
      box       the box part (absolute, stamped without outline) or False for none; default open box + up
      far_hand  the far hand part or False; default v2's FAR_HAND_BOX + up
      shin      the dangling near shin's swing (dx, dy)
      near_over_box  stamp the near arm after the box (an arm reaching in front of it)."""
    ux, uy = up
    fig = fig or F.Fig()
    if far_leg_on:
        fig.stamp(R.far_leg())
    fig.stamp(R.seat())
    if extra_under:
        for part, ol in extra_under:
            fig.stamp(part, ol)
    fig.stamp_all(far if far is not None else F.far_arm_box(ux, uy))
    fig.stamp(C.shift(V.neck(F.HEAD_AT[0]), ux, uy))
    fig.stamp(C.shift(V.shirt(shirt_frame), ux, uy))
    JB.dandruff(fig.px, ux, uy)
    hd = head if head is not None else F.head('admire', dx=F.HEAD_AT[0] + ux, dy=F.HEAD_AT[1] + uy)
    fig.stamp(hd, outline=False, name='head')
    fig.stamp(near_shoe(*shin, heel_k=not approved), outline=False)
    fig.stamp(near_leg_swing(*shin))
    nr = near if near is not None else F.near_arm_hip(ux, uy)
    if not near_over_box:
        fig.stamp_all(nr)
    bx = box if box is not None else F.open_box(ux, uy)
    if bx is not False:
        fig.stamp(bx, outline=False, name='box')
    fh = far_hand if far_hand is not None else F.far_hand_box(ux, uy)
    if fh is not False:
        fig.stamp(fh, outline=False, name='far_hand')
    if near_over_box:
        fig.stamp_all(nr)
    return fig


def _selftest():
    got = rider(approved=True).px
    ref = R.build('admire')
    ok = got == {q: k for q, k in ref.items()}
    print('rider() with the defaults == jr_ride.build(admire) (the approved rider):', ok)
    return ok


if __name__ == '__main__':
    sys.exit(0 if _selftest() else 1)
