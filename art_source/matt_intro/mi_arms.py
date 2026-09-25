"""Matt's arms in any pose.

The rig (art_source/matt/matt.py) only knows arms that hang: an upper-arm rotation, a forearm
rotation and a shoulder shrug, with the sleeve cut level at the wrist. Gestures need arms that bend
up, cross the chest or go behind the head, so this module rebuilds the same sleeve from its parts
for any shoulder -> elbow -> wrist, with everything the approved sleeve has:

  - the deltoid as an ellipsoid (it carries the shoulder's speaker port),
  - the upper arm and forearm as tapered capsules, each shaded as its own cylinder,
  - the bunched forearm's two black ridge lines with a lit crest under each (Exploud's ridged arms),
  - the yellow ribbed cuff square to the forearm, its ribs running along it,
  - a hand map placed at the wrist.

Arms given as `hang(...)` go through the rig's own arm code unchanged, so a pose that only swings
or shrugs the arms is pixel-for-pixel the approved construction.

Coordinates are frame coordinates. side 0 is the screen-left arm (his right), side 1 the
screen-right arm (his left). Light stays upper left on both: nothing here mirrors pixels.
"""
import math

import mi_base as B
from mi_base import capsule, ellipse, poly, sh, matt, details, moved

LAV = matt.LAV
YEL = matt.YEL


def unit(dx, dy):
    ln = math.hypot(dx, dy) or 1.0
    return dx / ln, dy / ln


class Arm:
    """One arm's pose. Build with hang() for the rig's hanging arms or bent() for anything else."""

    def __init__(self, side):
        self.side = side
        self.compat = False
        self.P = None
        self.dc = self.s0 = self.s1 = self.s2 = None
        self.hand = None             # (part, anchor) or None: the hand's own map, placed below
        self.hand_part = None        # a ready-placed hand part (frame coordinates)
        self.port = True
        self.layers = {}             # part name -> 'back' | 'mid' | 'front'
        self.cut_back = None         # optional: pixels of the forearm to leave out (hidden)


def hang(side, upper_rot=0.0, fore_rot=0.0, shoulder_dy=0, dx=0, dy=0, fist=True):
    """The rig's own hanging arm (matt.arm_parts), fist and port included, optionally nudged
    by whole pixels (dx, dy) for a tremble or a bob."""
    a = Arm(side)
    a.compat = True
    P = matt.Pose(False)
    P.upper_rot, P.fore_rot, P.shoulder_dy = upper_rot, fore_rot, shoulder_dy
    a.P = P
    a.nudge = (dx, dy)
    a.fist = fist
    return a


def bent(side, dc, s0, elbow, wrist, hand=None, port=True, ridges=True, cuff=True,
         layer='mid', fore_layer=None, hand_layer=None, fore_hidden=None):
    """A sleeve for any shoulder -> elbow -> wrist. `hand` is (map rows, anchor (col, row) in the
    map, i.e. the map pixel that sits on the hand's attach point) or None. The attach point is
    3 px past the wrist along the forearm, as on the approved fists."""
    a = Arm(side)
    a.dc, a.s0, a.s1, a.s2 = dc, s0, elbow, wrist
    a.hand = hand
    a.port = port
    a.ridges = ridges
    a.cuff = cuff
    a.layer = layer
    a.fore_layer = fore_layer or layer
    a.hand_layer = hand_layer or a.fore_layer
    a.fore_hidden = fore_hidden
    return a


# ---------------------------------------------------------------------------------------- the rig's arm

def _hang_parts(a):
    """[(part, outline, layer)] for a hanging arm, via the rig's own code."""
    P = a.P
    dx, dy = a.nudge
    out = []
    for part, ol in matt.arm_parts(P, a.side):
        out.append((moved(part, dx, dy), ol, 'mid'))
    (pdx, pdy), (fdx, fdy) = matt.arm_offsets(P)
    pl, pr = details.ports()
    if a.side == 0:
        out.append((moved(pl, pdx + dx, pdy + dy), False, 'mid'))
    else:
        out.append((moved(pr, -pdx + dx, pdy + dy), False, 'mid'))
    if a.fist:
        fl, fr = details.fists()
        if a.side == 0:
            out.append((moved(fl, fdx + dx, fdy + dy), False, 'mid'))
        else:
            out.append((moved(fr, -fdx + dx, fdy + dy), False, 'mid'))
    return out


def hang_wrist(a):
    """Where a hanging arm's wrist is, in frame coordinates (for effects placed near the fist)."""
    _, _, _, s2, _ = matt.arm_geometry(a.P)
    x, y = s2
    if a.side:
        x = B.AX - x
    return x + a.nudge[0], y + a.nudge[1]


# ---------------------------------------------------------------------------------------- any pose

def _bent_parts(a):
    dc, s0, s1, s2 = a.dc, a.s0, a.s1, a.s2
    ax, ay = unit(s2[0] - s1[0], s2[1] - s1[1])        # forearm axis, elbow -> wrist
    nx, ny = -ay, ax                                   # across it
    delt = ellipse(dc[0], dc[1], 7.4, 6.8)
    up = capsule(s0, s1, 5.6, 5.2)
    fo = capsule(s1, s2, 5.2, 4.9)

    def beyond_wrist(p):
        return (p[0] - s2[0]) * ax + (p[1] - s2[1]) * ay > 0.0

    fore = {p for p in fo if not beyond_wrist(p)}
    upper_set = {p for p in up if p not in fore} | set()
    # a pixel in both capsules belongs to whichever segment it is nearer
    def seg_d(p, a0, a1):
        vx, vy = a1[0] - a0[0], a1[1] - a0[1]
        L2 = vx * vx + vy * vy or 1.0
        t = max(0.0, min(1.0, ((p[0] - a0[0]) * vx + (p[1] - a0[1]) * vy) / L2))
        qx, qy = a0[0] + vx * t, a0[1] + vy * t
        return math.hypot(p[0] - qx, p[1] - qy)
    both = {p for p in up if p in fore}
    for p in both:
        if seg_d(p, s0, s1) < seg_d(p, s1, s2):
            fore.discard(p)
            upper_set.add(p)
    delt_part = {p: 'C' for p in delt}
    upper = {p: 'C' for p in upper_set if p not in delt}
    forearm = {p: 'C' for p in fore if p not in delt}
    sh.ellipsoid(delt_part, dc[0], dc[1], 7.8, 7.2, *LAV)
    sh.cylinder(upper, s0, s1, 6.0, *LAV)
    sh.cylinder(forearm, s1, s2, 6.0, *LAV)
    if a.ridges:
        for d in (-0.5, 2.5):
            for (x, y) in list(forearm):
                along = (x - s1[0]) * ax + (y - s1[1]) * ay
                if d - 0.5 <= along < d + 0.5:
                    forearm[(x, y)] = 'k'
                elif d + 0.5 <= along < d + 1.5 and forearm[(x, y)] in 'CD':
                    forearm[(x, y)] = B.LIGHTER[forearm[(x, y)]]
    if a.fore_hidden:
        for p in list(forearm):
            if p in a.fore_hidden:
                del forearm[p]
    sleeve_mid = dict(delt_part)
    sleeve_mid.update(upper)
    out = []
    if a.fore_layer == a.layer:
        sleeve_mid.update(forearm)
        out.append((sleeve_mid, True, a.layer))
    else:
        out.append((forearm, True, a.fore_layer))
        out.append((sleeve_mid, True, a.layer))
    if a.cuff:
        # the band: across -6..+6 at the wrist side, -6.5..+6.5 at the hand side, along +1..+2.8
        def at(al, ac):
            return (s2[0] + ax * al + nx * ac, s2[1] + ay * al + ny * ac)
        band = [at(1.0, -6.0), at(1.0, 6.0), at(2.8, 6.5), at(2.8, -6.5)]
        cuff = {p: 'c' for p in poly(band)}
        cc = (s2[0] + ax * 1.5, s2[1] + ay * 1.5)
        sh.cylinder(cuff, (cc[0] - ax * 5, cc[1] - ay * 5), (cc[0] + ax * 7, cc[1] + ay * 7), 7.0, *YEL)
        for (x, y) in list(cuff):
            across = (x - cc[0]) * nx + (y - cc[1]) * ny
            if round(across) % 2 == 0 and cuff[(x, y)] in 'bc':
                cuff[(x, y)] = B.DARKER[cuff[(x, y)]]
        out.append((cuff, True, a.fore_layer))
    if a.port:
        pl, pr = details.ports()
        if a.side == 0:
            out.append((moved(pl, round(dc[0] - 25), round(dc[1] - 57)), False, a.layer))
        else:
            out.append((moved(pr, round(dc[0] - 71), round(dc[1] - 57)), False, a.layer))
    if a.hand is not None:
        rows, (ac, ar) = a.hand
        hx = s2[0] + ax * 3.0
        hy = s2[1] + ay * 3.0
        part = B.amap(rows, int(round(hx)) - ac, int(round(hy)) - ar)
        out.append((part, False, a.hand_layer))
    if a.hand_part is not None:
        out.append((a.hand_part, False, a.hand_layer))
    return out


def parts(a):
    """[(part, outline, layer)] in stamp order for one arm."""
    return _hang_parts(a) if a.compat else _bent_parts(a)


def attach(a):
    """The hand's attach point (3 px past the wrist along the forearm) for a bent arm."""
    ax, ay = unit(a.s2[0] - a.s1[0], a.s2[1] - a.s1[1])
    return a.s2[0] + ax * 3.0, a.s2[1] + ay * 3.0
