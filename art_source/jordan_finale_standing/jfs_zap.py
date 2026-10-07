"""jordan_zap.png: 5 frames, played once. His disintegration gesture, facing screen-right like every
sheet of his (the code mirrors him to face Liam).

  0  wind-up: his left arm flung up and back, the hand hooked open over his shoulder, pink sparks
     gathering in it; the right fist clenched at his side; teeth clenched
  1  thrust: the arm snapped out straight at the target, one finger pointing, the pink energy
     bursting and crackling off the fingertip, speed lines where the hand came down from; shouting
  2  hold: arm locked out, a steady white-hot ball of pink at the fingertip, crackling; the zap line
     leaves from here (the fingertip is ZAP_TIP); a snarl
  3  recover: the arm dropping, the finger smoking, two pink wisps curling off it; seething. It is the
     frame he holds while Liam comes apart.
  4  arms up (the disintegrate-the-rest beat, played on its own): both fists punched up over his
     head, energy crackling round them, shouting; everything else as the zap
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402
import jfs_faces as FA  # noqa: E402
import jfs_parts as P  # noqa: E402

V = B.V
J = B.J
NAME = 'jordan_zap'
TIMES = [0.12, 0.08, 0.35, 0.15, 1.0]
LOOP = False
HEAD_AT = (4, 3)

# the thrust: the arm straight out from the shoulder, level, the hand pointing
OUT_ELBOW, OUT_WRIST = (64.6, 47.6), (70.4, 47.0)
POINT_AT = (69, 44)                       # POINT_R's top-left: the fingertip lands at (79, 46)
ZAP_TIP_BUILD = (POINT_AT[0] + P.POINT_TIP[0], POINT_AT[1] + P.POINT_TIP[1])
# the recover: the arm dropping away, the hand still pointing
DROP_ELBOW, DROP_WRIST = (63.6, 52.2), (68.6, 55.6)
DROP_AT = (67, 53)


def base(cv, face, far_parts):
    """Legs, shoes, the far arm (behind the tee), the neck, the fitted tee, dandruff, the head."""
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    B.stamp_all(cv, far_parts)
    cv.stamp(V.neck(HEAD_AT[0]))
    cv.stamp(V.shirt(1))
    B.AB.dandruff(cv.px, 0, 0)
    hd = FA.head(face, *HEAD_AT)
    cv.stamp(hd, outline=False)
    return hd


def energy(cv, fx, part):
    for q, k in part.items():
        if q not in cv.px or cv.px[q] in ('W', 'Q', 'P', 'q'):
            cv.px[q] = k
            fx.add(q)


def windup():
    cv = B.Canvas(96, 96)
    el, wr = (65.4, 39.6), (66.6, 29.4)
    far = P.far_arm_raised(el, wr)
    hd = base(cv, 'glare_shut', far)
    hand = P.at(P.CLAW_R, wr[0] - P.CLAW_WRIST[0] + 0.5, wr[1] - P.CLAW_WRIST[1] - 0.5)
    cv.stamp(hand, outline=False)
    near, _nf = P.near_arm_tense()
    B.stamp_all(cv, near)
    fx = set()
    energy(cv, fx, P.crackle(66, 18, 2.2, 'gather'))
    FA.anger(cv, hd, fx)
    return cv, fx


def thrust(which):
    cv = B.Canvas(96, 96)
    far = P.far_arm_out(OUT_ELBOW, OUT_WRIST)
    face = 'glare_open' if which == 'burst' else 'rage_shut'
    hd = base(cv, face, far)
    cv.stamp(P.at(P.POINT_R, *POINT_AT), outline=False)
    near, _nf = P.near_arm_tense()
    B.stamp_all(cv, near)
    fx = set()
    tx, ty = ZAP_TIP_BUILD
    if which == 'burst':
        energy(cv, fx, P.crackle(tx + 4, ty, 3.4, 'burst'))
        # the snap of it: speed lines left where the hand came down from over his shoulder
        for (x0, y0, n, k) in ((68, 36, 5, 'W'), (71, 38, 4, 'Q'), (74, 40, 3, 'W'), (65, 39, 3, 'Q')):
            for j in range(n):
                q = (x0 + j, y0 + j // 2)
                if q not in cv.px:
                    cv.px[q] = k
                    fx.add(q)
    else:
        energy(cv, fx, P.crackle(tx + 3, ty, 2.4, 'hold'))
    cv.px[(tx, ty)] = 'Q'                      # the fingertip lit by it
    FA.anger(cv, hd, fx, flip_steam=(which == 'burst'))
    return cv, fx


def recover():
    cv = B.Canvas(96, 96)
    far = P.far_arm_out(DROP_ELBOW, DROP_WRIST)
    hd = base(cv, 'glare_shut', far)
    cv.stamp(P.at(P.POINT_R, *DROP_AT), outline=False)
    near, _nf = P.near_arm_tense()
    B.stamp_all(cv, near)
    fx = set()
    energy(cv, fx, P.wisps(DROP_AT[0] + P.POINT_TIP[0] + 1, DROP_AT[1] + P.POINT_TIP[1] - 1))
    FA.anger(cv, hd, fx)
    return cv, fx


def arms_up():
    cv = B.Canvas(96, 96)
    el, wr = (63.8, 35.4), (66.8, 23.6)
    far = P.far_arm_raised(el, wr)
    hd = base(cv, 'glare_open', far)
    far_fist = P.at(P.FIST_UP_FAR, wr[0] - 4.0, wr[1] - 10.5)
    cv.stamp(far_fist, outline=False)
    B.stamp_all(cv, V.raised_arm())
    fx = set()
    energy(cv, fx, P.arc_between((33, 9), (64, 9), amp=2))
    energy(cv, fx, P.crackle(31, 11, 2.4, 'up'))
    energy(cv, fx, P.crackle(67, 11, 2.4, 'up'))
    FA.anger(cv, hd, fx, steam=False)
    return cv, fx


def builders():
    return [windup, lambda: thrust('burst'), lambda: thrust('hold'), recover, arms_up]


def frames():
    out = []
    for b in builders():
        cv, fx = b()
        out.append((B.fill_holes(B.finish(cv)), {(x + B.ANCHOR_SHIFT, y) for (x, y) in fx}))
    return out
