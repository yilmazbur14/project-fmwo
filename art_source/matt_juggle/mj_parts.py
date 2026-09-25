"""Pose helpers in the rig's own terms, for building the juggle frames.

Arms are mi_arms.bent arms given by two directions (upper arm, forearm) in LOCAL degrees: 0 points
right, 90 down, 180 left, 270 up (y down, so angles grow clockwise on screen). The shoulders are the
approved idle's: deltoid (25, 57) and shoulder joint (24, 60) on the screen-left arm, mirrored for
the right. The segment lengths are the idle's (upper arm 8.5, forearm 4.6), so a posed arm is the
same arm, swung.

Hands are the intro rig's maps (mi_hands). A hand pointing sideways uses a hand map turned by whole
quarter turns (exact), and its baked light is turned with it; mj_fig re-lights it from the
upper left like every other hand.

Legs are mi_legs.walk_legs in screen mode: each foot offset (fdx, fdy) and a knee lean, the rig's
own trouser outline and foot maps carried with the foot.
"""
import math

import mj_base as J
from mj_base import A, HANDS as HM, L, B

UPPER, FORE = 8.5, 4.6
SHOULDERS = {0: ((25, 57), (24, 60)), 1: ((71, 57), (72, 60))}


def _dir(deg):
    t = math.radians(deg)
    return math.cos(t), math.sin(t)


def turn_hand(hand, q):
    """A hand map and its anchor turned q quarter turns clockwise (exact)."""
    rows, (ac, ar) = hand
    rs = [r.replace(' ', '') for r in rows]
    for _ in range(q % 4):
        h, w = len(rs), len(rs[0])
        rs = [''.join(rs[h - 1 - r][c] for r in range(h)) for c in range(w)]
        ac, ar = h - 1 - ar, ac
    return rs, (ac, ar)


# which hand map points which way, per side: (map, quarter turns it was turned by)
OPEN = {
    # fingers pointing: down, up, left, right
    (0, 'down'): (HM.OPEN_DOWN_L, 0), (1, 'down'): (HM.OPEN_DOWN_R, 0),
    (0, 'up'): (HM.OPEN_UP_L, 0), (1, 'up'): (HM.OPEN_UP_R, 0),
    (0, 'left'): (HM.OPEN_UP_R, 3), (1, 'left'): (HM.OPEN_UP_L, 3),
    (0, 'right'): (HM.OPEN_UP_R, 1), (1, 'right'): (HM.OPEN_UP_L, 1),
}
FIST = {
    (0, 'down'): (HM.FIST_L, 0), (1, 'down'): (HM.FIST_R, 0),
    (0, 'up'): (HM.FIST_UP_L, 0), (1, 'up'): (HM.FIST_UP_R, 0),
    (0, 'left'): (HM.FIST_UP_L, 3), (1, 'left'): (HM.FIST_UP_R, 3),
    (0, 'right'): (HM.FIST_UP_L, 1), (1, 'right'): (HM.FIST_UP_R, 1),
}


def heading(deg):
    d = deg % 360
    if 45 <= d < 135:
        return 'down'
    if 135 <= d < 225:
        return 'left'
    if 225 <= d < 315:
        return 'up'
    return 'right'


class Arm:
    """A posed arm plus the quarter turns its hand map carries (for the relight)."""

    def __init__(self, arm, hand_q):
        self.arm = arm
        self.hand_q = hand_q


def arm(side, a_up, a_fore, hand='open', layer='mid', fore_layer=None, hand_layer=None,
        upper=UPPER, fore=FORE, face=None, shift=(0, 0)):
    """One arm swung to local directions a_up (shoulder -> elbow) and a_fore (elbow -> wrist).
    hand: 'open', 'fist' or None. face: force the hand's heading ('down', 'up', 'left', 'right').
    shift: move the whole arm, shoulder and all (a chest rising on a breath carries its arm)."""
    dc, s0 = SHOULDERS[side]
    dc = (dc[0] + shift[0], dc[1] + shift[1])
    s0 = (s0[0] + shift[0], s0[1] + shift[1])
    ux, uy = _dir(a_up)
    fx, fy = _dir(a_fore)
    elbow = (s0[0] + ux * upper, s0[1] + uy * upper)
    wrist = (elbow[0] + fx * fore, elbow[1] + fy * fore)
    hmap, q = None, 0
    if hand:
        table = OPEN if hand == 'open' else FIST
        base, q = table[(side, face or heading(a_fore))]
        hmap = turn_hand(base, q)
    a = A.bent(side, dc, s0, elbow, wrist, hand=hmap, layer=layer,
               fore_layer=fore_layer, hand_layer=hand_layer)
    return Arm(a, q)


def arms(*pair):
    """[Arm, Arm] -> (the mi_arms list for the Fig, {side: baked-light degrees} for the relight)."""
    return [p.arm for p in pair], {p.arm.side: 90 * p.hand_q for p in pair if p.hand_q}


def legs(left=(0, 0, 0.0), right=(0, 0, 0.0), hip_dy=0, back=0):
    """Both legs: (fdx, fdy, lean) for the screen-left and screen-right foot, screen mode."""
    return lambda f: L.walk_legs(hip_dy, left, right, back=back, screen=True)


# ------------------------------------------------------------------------------ the breath
# matt.sweatshirt and matt.hem_band, line for line, with the screen-left half of each outline let
# out by `db` texels (x - db for every point left of the axis). Lying on his back with his head to
# the right (turned 90), that half of him faces up off the mat, so letting it out is his chest
# rising on a breath while the side on the canvas stays put. At db 0 both are the rig's own parts
# pixel for pixel (checked in _selftest).
def _let_out(half, db):
    left = [(x - db if x < 48 else x, y) for (x, y) in half]
    right = [(96 - x, y) for (x, y) in reversed(half) if x != 48]
    return left + right


def breath_torso(P, db):
    from mj_base import matt, sh, pal
    from lib import fill, poly
    part = fill(poly(_let_out([(48, 48.5), (41, 49), (36, 50.5), (31.5, 52.5), (30.5, 56), (31, 61),
                               (32, 65), (32.5, 68.5), (33, 71), (48, 71)], db)), 'C')
    sh.ellipsoid(part, 47 - db / 2.0, 58, 19 + db / 2.0, 15, 'ABCDE', (0.93, 0.76, 0.36, 0.0))
    for (x, y) in list(part):
        row = [px for (px, py) in part if py == y]
        edge = min(x - min(row), max(row) - x)
        if 57 <= y <= 70 and edge <= 1:
            part[(x, y)] = pal.DARKER[part[(x, y)]]
        if not P.roar and 57 <= y <= 58 and 40 <= x <= 56:
            part[(x, y)] = pal.DARKER[part[(x, y)]]
    return part


def breath_hem(P, db):
    from mj_base import sh
    from lib import fill, poly
    part = fill(poly(_let_out([(48, 68.5), (33.5, 68.5), (32.5, 70.5), (33.5, 72.5), (48, 72.5)], db)),
                'c')
    sh.ellipsoid(part, 46 - db / 2.0, 66, 17 + db / 2.0, 8, 'abcde', (0.9, 0.62, 0.28, -0.1))
    return part


def _selftest():
    from mj_base import matt
    P = matt.Pose(False)
    a = breath_torso(P, 0) == matt.sweatshirt(P)
    b = breath_hem(P, 0) == matt.hem_band(P)
    print('breath_torso(0) vs matt.sweatshirt:', 'identical' if a else 'DIFFERENT')
    print('breath_hem(0) vs matt.hem_band:', 'identical' if b else 'DIFFERENT')
    return a and b


def spikes_scaled(sp, k_len=1.0, k_ang=1.0, d_len=0.0, bend=None):
    """A crest spec with every spike's angle scaled (a flare spreads them), its length scaled or
    extended, and optionally every bend replaced."""
    out = []
    for (a, r0, r1, w0, w1, b) in sp:
        out.append((a * k_ang, r0, r1 * k_len + d_len, w0, w1, b if bend is None else bend))
    return out
