"""Greyson's walks, on the approved rig (read-only, via gf_base): the pre-cannon takeover stomp
(greyson_walk) and, later, the cannon-arm walk (greyson_walk_cannon).

The house walk (Matt's approved matt_walk, Burak's burak_walk): the body stays front-on, the head
turns three-quarters toward the way he walks, and the feet take turns. Six frames at 0.10 s,
looping: 0 contact, 1 lift, 2 pass, 3 contact, 4 lift, 5 pass. Drawn facing screen-RIGHT; the
code flips it for the other way.

A heavy bodybuilder stomp: the hips drop hard on each contact (the knees give), the stepping knee
comes up high on the pass, and the arms, held out by the lats, swing only a little, against the
legs. The legs are the approved legs RE-POSED, not resampled: their outline polygon and muscle
bumps are moved through a piecewise map (hip, knee, ankle) and shaded again, so every outline
stays a clean pixel line. Everything above the legs rides the hip drop as one piece.

    python -B gf_walk.py      # prints each frame's numbers; writes nothing
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
import gf_fig  # noqa: E402
import gf_cannon  # noqa: E402
from gr_muscle import Bump, Form, Layer  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face, gr_boots = B.K, B.gr_fig, B.gr_arms, B.gr_hands, \
    B.gr_face, B.gr_boots

HIP_Y, KNEE_Y, ANKLE_Y = 78.5, 97.2, 102.4      # the approved leg's joints (gr_fig.leg)
LEG_PTS = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6), (53.4, 98.8),
           (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]


def _check_leg_copy():
    """LEG_PTS must be the approved leg's own outline: re-posing with no drop and no lift has to
    give back the approved leg pixel for pixel."""
    a = gr_fig.leg(0)
    b = posed_leg(0, 0, 0)
    if a != b:
        raise SystemExit('gf_walk.LEG_PTS no longer matches gr_fig.leg; the approved leg changed')


def ymap(drop, lift):
    """The leg's vertical map for a hip drop (down, px) and a foot lift (up, px): the hip rides
    the drop, the knee takes half the drop and rises by just over half the lift, the ankle
    rises by the lift."""
    hip = HIP_Y + drop
    knee = KNEE_Y + 0.5 * drop - 0.55 * lift
    ankle = ANKLE_Y - lift

    def f(y):
        if y <= HIP_Y:
            return y + drop
        if y <= KNEE_Y:
            t = (y - HIP_Y) / (KNEE_Y - HIP_Y)
            return hip + (knee - hip) * t
        t = (y - KNEE_Y) / (ANKLE_Y - KNEE_Y)
        return knee + (ankle - knee) * t

    def scale(y):
        if y <= HIP_Y:
            return 1.0
        if y <= KNEE_Y:
            return (knee - hip) / (KNEE_Y - HIP_Y)
        return max(0.35, (ankle - knee) / (ANKLE_Y - KNEE_Y))
    return f, scale


def posed_leg(side, drop, lift, dx=0.0):
    """The approved leg (gr_fig.leg) with the hip dropped by `drop` and the foot lifted by
    `lift`; `dx` slides the knee and foot sideways (a stepping foot swings in under the body).
    With drop = lift = dx = 0 it is the approved leg exactly."""
    f, scale = ymap(drop, lift)

    def xy(p):
        x, y = p
        w = 0.0 if y <= HIP_Y else min(1.0, (y - HIP_Y) / (ANKLE_Y - HIP_Y))
        return (x + dx * w, f(y))

    pts = [xy(p) for p in LEG_PTS]
    bumps = []
    for b in gr_fig.LEG_BUMPS:
        c = xy(b.c)
        s = scale(b.c[1])
        bumps.append(Bump(b.name, c, b.a * s if abs(b.ang - 90) < 45 else b.a, b.b, b.ang, b.amp,
                          b.z0, b.p, b.prof, b.cast, b.depth, b.taper, b.skew))
    bumps = gr_fig.side_bumps(bumps, side)
    pix = K.poly(gr_fig.mps(pts, side))
    top, bot = xy((46.2, 80.0)), xy((46.2 + 0.0, 104.0))
    c0, c1 = gr_fig.mp(top, side), gr_fig.mp(bot, side)
    form = Form(axis=[(c0[0], c0[1]), (c1[0], c1[1])], r=9.5)
    lay = Layer(pix, form, bumps, floor=0.2, strength=1.0)
    return lay.shade_owned(cuts=gr_fig.CUTS)[0]


# ------------------------------------------------------------------------------------ the cycle

# (hip drop, lift of the screen-LEFT foot, lift of the screen-RIGHT foot, arm swing) per frame.
# Swing +1: the screen-right fist forward (up and in), the screen-left one back; -1 the reverse.
CYCLE = [
    ('contact', 2, 0, 0, 0),     # the right foot has just stamped down: hips at their lowest
    ('lift', 1, 3, 0, 1),        # the left foot peels off
    ('pass', 0, 7, 0, 1),        # the left knee comes up high
    ('contact', 2, 0, 0, 0),     # the left foot stamps down
    ('lift', 1, 0, 3, -1),       # the right foot peels off
    ('pass', 0, 0, 7, -1),       # the right knee comes up high
]
STEP_DX = 1.5                    # a lifted foot swings in a little under the body


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


SWING_FWD = (1.0, -2.0)          # a forward swing: the forearm and fist up 2 and in 1 (left-side
SWING_BACK = (-1.0, 1.0)         # coordinates, +x toward the body); back: down 1 and out 1


def swung_arm(side, swing):
    """The approved idle arm (gr_arms.IDLE's traced polygons) with its forearm and fist carried
    forward (up and a little in, the way a forward swing reads from the front) or back (down and
    a little out), re-shaded from the polygons so the keyline never tears. `swing` +1 swings the
    screen-RIGHT arm forward and the left one back; -1 the reverse; 0 is the approved arm.
    -> (part, (dx, dy)) with the shift in left-side coordinates, for the fist."""
    if not swing:
        return gr_arms.arm('idle', side), (0.0, 0.0)
    fwd = (swing > 0) == bool(side)          # does THIS arm swing forward?
    dx, dy = SWING_FWD if fwd else SWING_BACK
    polys = dict(gr_arms.IDLE)
    forms = dict(gr_arms.IDLE_FORMS)
    for name in ('forearm', 'brach'):
        polys[name] = [(x + dx, y + dy) for (x, y) in gr_arms.IDLE[name]]
        f = gr_arms.IDLE_FORMS[name]
        (x0, y0), (x1, y1) = f.axis
        forms[name] = Form(axis=[(x0 + dx, y0 + dy), (x1 + dx, y1 + dy)], r=f.r, flat=f.flat)
    return gf_fig.arm_layer(polys, forms, gr_arms.SPEC, side), (dx, dy)


# The cannon arm as worn in the fight idle (gf_fig.idle): the approved upper arm, and the gauntlet
# hanging from the elbow, muzzle down and a little out. Left-side coordinates, mirrored onto his
# left arm.
CANNON_ELBOW, CANNON_MUZZLE, CANNON_FACE = (21.4, 70.0), (13.8, 95.0), 0.62


def cannon_arm(swing, drop):
    """His left arm with the cannon on, for side 1, swung like swung_arm's forearm: the upper arm
    stays, the muzzle end carries the swing."""
    upper = gf_fig.arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 1,
                             keep=('delt', 'upper', 'biceps'))
    dx, dy = (0.0, 0.0)
    if swing:
        dx, dy = SWING_FWD if swing > 0 else SWING_BACK
    ex, ey = CANNON_ELBOW
    mx_, my_ = CANNON_MUZZLE
    gun = gf_cannon.cannon(gf_fig.mp((ex, ey + drop)), gf_fig.mp((mx_ + dx, my_ + dy + drop)),
                           face=CANNON_FACE)
    return moved(K.despeckle(upper), 0, drop), gun


def frame(i, head=None, cannon=False):
    """Walk frame i (0-5) -> (canvas, info). `head` is a (part, keep) pair for the head; the
    approved idle head when None. `cannon` puts Computah's cannon on his left arm (the
    cannon-arm walk); without it this is the shipped pre-cannon walk, unchanged."""
    name, drop, lift_l, lift_r, swing = CYCLE[i]
    cv = K.Canvas()
    legs = {0: posed_leg(0, drop, lift_l, STEP_DX if lift_l else 0.0),
            1: posed_leg(1, drop, lift_r, STEP_DX if lift_r else 0.0)}
    # A lifted knee comes up toward us and its shin runs back, so its boot sits BEHIND the knee:
    # the lifted boot first, then the planted leg, the lifted leg over both, and the planted boot
    # last (its cuff over its own calf, as in the approved stance).
    lifts = {0: lift_l, 1: lift_r}

    def boot(side):
        dx = int(round(STEP_DX)) if lifts[side] else 0
        return moved(gr_boots.boot(side), dx if side == 0 else -dx, -lifts[side])

    lifted = [s for s in (0, 1) if lifts[s]]
    planted = [s for s in (0, 1) if not lifts[s]]
    for side in lifted:
        cv.stamp(boot(side), outline=False)
    for side in planted + lifted:
        cv.stamp(K.despeckle(legs[side]))
    for side in planted:
        cv.stamp(boot(side), outline=False)
    P = gr_fig.Pose('idle')
    cv.stamp(moved(K.despeckle(gr_fig.torso(P)), 0, drop))
    cv.stamp(moved(gr_fig.trunks(), 0, drop))
    cv.stamp(moved(gr_fig.waistband(), 0, drop), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y + drop)] = 'k'
    fists = []
    for side in (0, 1):
        if cannon and side == 1:
            upper, gun = cannon_arm(swing, drop)
            cv.stamp(upper)
            cv.stamp(gun)
            continue
        arm, (sx, sy) = swung_arm(side, swing)
        cv.stamp(moved(K.despeckle(arm), 0, drop))
        fists.append((side, (P.fist[0] + sx, P.fist[1] + sy + drop)))
    for side, c in fists:
        cv.stamp(gr_hands.fist('idle', side, c), outline=False)
    if head is None:
        hpart, keep = gr_face.head('idle'), gr_face.face('idle')
    else:
        hpart, keep = head
    cv.stamp(moved(hpart, 0, drop), outline=False)
    keep = {(x, y + drop) for (x, y) in keep}
    finish(cv, keep)
    info = {'name': name, 'drop': drop, 'lift': (lift_l, lift_r)}
    return cv, info


def finish(cv, keep=()):
    """As gf_fig.finish: orphan skin tones swept (the face keeps its pixels), pinholes closed."""
    K.despeckle(cv.px, keep=set(keep))
    x0, y0, x1, y1 = K.bbox(cv.px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in cv.px and all(q in cv.px for q in
                                           ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                cv.px[(x, y)] = 'k'
    return cv


_check_leg_copy()

if __name__ == '__main__':
    for i in range(6):
        cv, info = frame(i)
        a = B.audit(cv.px)
        print(i, info, K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()})
