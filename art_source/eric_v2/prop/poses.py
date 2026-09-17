"""Proportion-pass poses: new base idle and the widest whirlwind frame."""
import math
import pose as P

FW, FH = 256, 192
UP = (-1.0, -5.0)          # idle lean, 1 px out per 5 px up


def base_idle():
    fr = P.Big(FW, FH)
    P.body(fr)
    fist = (92, 163)
    L = math.hypot(*UP)
    u = (UP[0] / L, UP[1] / L)
    guard = (fist[0] + u[0] * 10, fist[1] + u[1] * 10)
    # forearm + elbow tucked against the belly, reaching out to the grip
    P.limb(fr, (105, 162), (95, 163), 9)
    P.cop(fr, (105, 162), 4.3, 4.1)
    P.sword(fr, guard, UP)
    P.fist(fr, *fist)
    return fr


def whirl_wide():
    """front-facing spin frame, blade fully extended to his left (viewer right) at belt height,
    both hands on the grip in front of the belly, low motion smear around him."""
    fr = P.Big(FW, FH)
    import fxbig
    import body_s, variants_s
    fxbig.whirl_smear(fr, back=True)
    P.body(fr, skip=('armR_front', 'cape'), extra_first={'cape': variants_s.cape_swing(-4.0)})
    hands = (126, 166)
    # both forearms come in from the sides to the grip
    P.limb(fr, (108, 158), (118, 166), 9)
    P.cop(fr, (107, 157), 4.3, 4.1)
    P.limb(fr, (148, 158), (134, 166), 9)
    P.cop(fr, (149, 157), 4.3, 4.1)
    P.sword(fr, (hands[0] + 14, hands[1] + 1), (1.0, 0.06))
    P.fist(fr, hands[0] - 3, hands[1], horizontal=True)
    P.fist(fr, hands[0] + 6, hands[1], horizontal=True)
    fxbig.whirl_smear(fr, back=False)
    return fr
