"""Bixby's body in profile for the Flyby, facing right: torso, the black mane, necks, legs, paws, tail
and the wings, in the approved construction (art_source/bixby_redesign/body.py, rig_body.py,
rig_wings.py) and palette: the charcoal saddle with its violet rim over the back and shoulders, blood-red
flanks and upper legs with their fur tufts, bone chest, belly and lower legs, white paws with charcoal
claws, the black tail with Bixby's white flame tip, and the tattered bat wings with ember-rimmed tears.

The body is authored in design units and placed by a Body transform: scaled by k about the neck base
and moved, so it sits small behind the heads (the approved beast is all heads) and high, mostly over the
top of the screen on a pass. Limb thicknesses scale with it.
"""
import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)
import math

import body as RBODY
import rig_wings as RW
from pal import amap, fill, poly
from shapes import capsule, chain, edge, poly_line, recolor

import fb_shade as S

DARKER = {'u': 't', 't': 's', 's': 'r', 'r': 'q', 'x': 'y', 'w': 'x', 'y': 'z', 'd': 'c', 'c': 'b',
          'f': 'e', 'C': 'B', 'B': 'A'}


def darker(part):
    return {q: DARKER.get(k, k) for q, k in part.items()}


class Body:
    """Design units -> frame: p' = pivot + (p - pivot) * k + offset (+ bob on y)."""

    def __init__(self, k=1.0, pivot=(126, 72), offset=(0, 0), bob=0):
        self.k, self.pivot, self.offset, self.bob = k, pivot, offset, bob

    def p(self, pt):
        px, py = self.pivot
        return (px + (pt[0] - px) * self.k + self.offset[0], py + (pt[1] - py) * self.k + self.offset[1] + self.bob)

    def pts(self, pts):
        return [self.p(q) for q in pts]

    def r(self, radius):
        return radius * self.k


#TORSO (a deep keel of a chest, a tucked waist, the rump; the saddle over the back and shoulders)

TORSO = [(122, 64), (112, 58), (98, 58), (84, 61), (70, 64), (56, 66), (44, 66), (34, 70), (28, 78),
         (28, 88), (34, 98), (44, 104), (56, 104), (70, 108), (86, 114), (102, 118), (116, 116), (126, 108),
         (131, 96), (130, 84), (126, 72)]
SADDLE = [(128, 70), (122, 62), (112, 57), (98, 57), (84, 60), (70, 63), (56, 65), (44, 65), (33, 69),
          (27, 78), (28, 86), (36, 84), (48, 81), (62, 80), (76, 80), (90, 80), (102, 84), (108, 92),
          (114, 98), (120, 94), (124, 84)]
CHEST = [(131, 94), (126, 108), (116, 116), (102, 118), (98, 110), (106, 104), (116, 98), (124, 88)]
BELLY = [(102, 118), (86, 114), (70, 108), (58, 104), (62, 100), (74, 102), (88, 106), (100, 110)]


def torso(B):
    body = poly(B.pts(TORSO))
    sad = poly(B.pts(SADDLE)) & body
    chest = poly(B.pts(CHEST)) & body - sad
    belly = poly(B.pts(BELLY)) & body - sad - chest
    red = body - sad - chest - belly
    t = {}
    t.update(S.shade(red, 'fur'))
    t.update(S.shade(sad, 'black', rim='e', rim_side=(-1, 0.6)))
    t.update(S.shade(chest | belly, 'bone'))
    for (x, y) in red:                                   # the fur catches light under the saddle's edge
        if (x, y - 1) in sad:
            t[(x, y)] = 'u'
    for seg in ([(112, 98), (104, 106), (96, 108)], [(84, 86), (80, 96), (82, 104)], [(58, 86), (52, 96)]):
        for q in poly_line(B.pts(seg)):
            if q in red and t[q] in 'tu':
                t[q] = 's'
    for seg in ([(106, 60), (104, 70)], [(92, 60), (90, 72)], [(78, 63), (76, 74)], [(64, 65), (62, 76)],
                [(50, 67), (47, 78)], [(38, 70), (34, 80)], [(118, 70), (114, 82)]):
        for q in poly_line(B.pts(seg)):
            if q in sad and t[q] in 'cbd':
                t[q] = 'k'
    for seg in ([(126, 98), (121, 108)], [(120, 100), (114, 110)], [(110, 108), (104, 114)]):
        for q in poly_line(B.pts(seg)):
            if q in chest and t[q] in 'xw':
                t[q] = 'y'
    # the Hades cuts: black partings raking back through the red flank, as through the approved fur
    for seg in ([(106, 88), (101, 98)], [(94, 86), (89, 97)], [(82, 86), (77, 98)], [(70, 85), (65, 97)],
                [(58, 88), (54, 98)], [(100, 96), (97, 102)], [(76, 94), (73, 101)]):
        for q in poly_line(B.pts(seg)):
            if q in red and t[q] in 'tus':
                t[q] = 'k'
    return t


#MANE: the saddle's spiky black ruff, rising along the necks and over the withers

MANE = [(144, 84), (142, 62), (136, 68), (130, 42), (126, 60), (114, 36), (110, 58), (98, 36), (95, 58),
        (82, 42), (80, 62), (68, 50), (68, 66), (86, 66), (108, 64), (126, 70), (138, 84)]
# black partings from each spike's root toward its tip, and the lit ridge of each spike's leading edge
MANE_CUTS = [[(134, 64), (131, 48)], [(118, 58), (115, 42)], [(102, 58), (99, 42)], [(86, 60), (83, 46)]]
MANE_RIDGES = [[(136, 68), (130, 43)], [(126, 60), (115, 37)], [(110, 58), (99, 37)], [(95, 58), (83, 43)],
               [(80, 62), (69, 51)]]


def mane(B):
    """The saddle's spiky black ruff (the approved mantle) seen from the side: big spikes swept back
    along the necks and over the withers, lit along their leading edges, violet-rimmed behind."""
    m = S.shade(poly(B.pts(MANE)), 'black', rim='e', rim_side=(-1, 0.4))
    for seg in MANE_RIDGES:
        for q in poly_line(B.pts(seg)):
            if q in m and m[q] in 'cb':
                m[q] = 'd'
    for seg in MANE_CUTS:
        for q in poly_line(B.pts(seg)):
            if q in m and m[q] in 'cbd':
                m[q] = 'k'
    return m


def neck(a, b, r0=8.0, r1=7.0, rim=True):
    """A charcoal neck from the body (a) to a head (b), the saddle running up its back; only the nearest
    neck carries the violet rim (the ones behind would stack it into ripples)."""
    return S.shade(capsule(a, b, r0, r1), 'black', rim='e' if rim else None, rim_side=(-1, 0.5))


#PAWS in profile: toes pointing back (trailing in flight), pads up, charcoal claws hooked behind

FRONT_PAW_SIDE = [
    "...kkkkkk.",
    ".kkwwwxxxk",
    "kwwxxxxxyk",
    "kxkxxkxxyk",
    "kxxkxykyzk",
    ".kkkkkkkk.",
    "kdk.kdk...",
    ".k...k....",
]
HIND_PAW_SIDE = [
    "..kkkkk.",
    ".kwwxxxk",
    "kwxxxxyk",
    "kxkxkxzk",
    ".kkkkkk.",
    "kdk.kdk.",
    ".k...k..",
]


def paw_side(front, at):
    rows = FRONT_PAW_SIDE if front else HIND_PAW_SIDE
    return amap(rows, int(round(at[0])) - len(rows[0]) // 2, int(round(at[1])) - 2)


#LEGS (the rig's leg construction with scalable radii: rig_body.front_leg / hind_leg)

def _carry(pts, o0, a0, o1, a1):
    da = a1 - a0
    c, s = math.cos(da), math.sin(da)
    out = []
    for (x, y) in pts:
        rx, ry = x - o0[0], y - o0[1]
        rx, ry = rx * c - ry * s, rx * s + ry * c
        out.append((o1[0] + rx, o1[1] + ry))
    return out


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def front_leg(B, shoulder, elbow, wrist, paw):
    """Shoulder (charcoal, the saddle's), upper arm (red, the elbow tuft raking back), forearm (bone), paw."""
    S0, E, Wr, P = B.p(shoulder), B.p(elbow), B.p(wrist), B.p(paw)
    sh_end = (S0[0] + (E[0] - S0[0]) * 0.35, S0[1] + (E[1] - S0[1]) * 0.35)
    sh = fill(capsule(S0, sh_end, B.r(10), B.r(9)), 'c')
    RBODY.black_shade(sh)
    upper = fill(capsule(sh_end, E, B.r(8), B.r(7)), 't')
    # the elbow tuft: two flame blades raking back from the elbow, turned with the arm
    a0 = _ang((123, 108), (128, 119))
    a1 = _ang(sh_end, E)
    tuft = _carry([(130, 112), (137, 117), (133, 118), (138, 123), (131, 124), (128, 126)], (128, 119), a0, E, a1)
    tuft = [(E[0] + (x - E[0]) * B.k, E[1] + (y - E[1]) * B.k) for (x, y) in tuft]
    upper.update({q: 't' for q in poly(tuft)})
    recolor(upper, edge(upper, 0, -1, 1), 'u')
    recolor(upper, edge(upper, 1, 0, 1), 's')
    recolor(upper, edge(upper, 0, 1, 2), 's')
    recolor(upper, edge(upper, 0, 1, 1), 'r')
    for seg in ([(130, 115), (134, 120)], [(127, 113), (128, 118)]):
        pts = _carry(seg, (128, 119), a0, E, a1)
        pts = [(E[0] + (x - E[0]) * B.k, E[1] + (y - E[1]) * B.k) for (x, y) in pts]
        for q in poly_line(pts):
            if q in upper:
                upper[q] = 'k'
    fore = fill(capsule(E, Wr, B.r(6.4), B.r(5.4)), 'x')
    recolor(fore, edge(fore, 0, -1, 1), 'w', only='x')
    recolor(fore, edge(fore, 0, 1, 2), 'y')
    recolor(fore, edge(fore, 0, 1, 1), 'z')
    return [sh, upper, fore, paw_side(True, P)]


def hind_leg(B, hip, hock, ankle, paw):
    """Thigh (red, the tuft off its back), shin (bone), paw."""
    H0, K, A, P = B.p(hip), B.p(hock), B.p(ankle), B.p(paw)
    thigh = fill(capsule(H0, K, B.r(10), B.r(6.5)), 't')
    a0 = _ang((136, 110), (152, 128))
    a1 = _ang(H0, K)
    tuft = _carry([(146, 110), (158, 115), (152, 118), (159, 122), (152, 124)], (152, 128), a0, K, a1)
    tuft = [(K[0] + (x - K[0]) * B.k, K[1] + (y - K[1]) * B.k) for (x, y) in tuft]
    thigh.update({q: 't' for q in poly(tuft)})
    recolor(thigh, edge(thigh, 0, -1, 1), 'u')
    recolor(thigh, edge(thigh, 1, 0, 1), 's')
    recolor(thigh, edge(thigh, 0, 1, 2), 's')
    recolor(thigh, edge(thigh, 0, 1, 1), 'r')
    for seg in ([(149, 115), (154, 121)], [(141, 118), (146, 124)]):
        pts = _carry(seg, (152, 128), a0, K, a1)
        pts = [(K[0] + (x - K[0]) * B.k, K[1] + (y - K[1]) * B.k) for (x, y) in pts]
        for q in poly_line(pts):
            if q in thigh:
                thigh[q] = 'k'
    shin = fill(capsule(K, A, B.r(5), B.r(4.6)), 'x')
    recolor(shin, edge(shin, 0, -1, 1), 'w', only='x')
    recolor(shin, edge(shin, 0, 1, 2), 'y')
    recolor(shin, edge(shin, 0, 1, 1), 'z')
    return [thigh, shin, paw_side(False, P)]


#TAIL (black, violet-rimmed, Bixby's white flame tip)

TAIL_TIP = [(6, 118), (5, 110), (8, 102), (10, 106), (12, 95), (15, 103), (19, 94), (18, 106), (16, 116), (12, 121)]


def tail(B, path, tip_base):
    t = fill(chain(B.pts(path), B.r(4.6), B.r(3.0)), 'c')
    recolor(t, edge(t, 0, -1, 1), 'd')
    recolor(t, edge(t, 0, 1, 1), 'b')
    recolor(t, edge(t, -1, 0, 1), 'e')
    bx, by = B.p(tip_base)
    k = B.k
    pts = [(bx + (x - 12) * k, by + (y - 118) * k) for (x, y) in TAIL_TIP]
    tip = fill(poly(pts), 'x')
    recolor(tip, edge(tip, -1, 0, 1), 'w')
    recolor(tip, edge(tip, 1, 0, 1), 'y')
    recolor(tip, edge(tip, 0, 1, 1), 'y')
    return [t, tip]


#THE APPROVED WINGBEAT, reused: flying right, his wing reaches back from the shoulder exactly as the approved
# hover's left wing reaches out (rig_wings UP, MID, DOWN, MID_UP mirrored), so the side view keeps the
# approved wing art, beat for beat.

APPROVED_BEAT = [RW.UP, RW.MID, RW.DOWN, RW.MID_UP]


def approved_wing(i, at, kw=1.0):
    """Wing parts for beat i: the approved right wing scaled kw about its shoulder, mirrored about the
    shoulder's column (so it reaches back), its shoulder moved to `at` (frame)."""
    P0 = APPROVED_BEAT[i]
    sx, sy = P0['shoulder']
    P = RW.moved(P0, sx=kw, sy=kw, about=(sx, sy))
    parts = RW.parts(P)
    ax, ay = at
    out = []
    for p in parts:
        out.append({(int(round(2 * sx - x - sx + ax)), int(round(y - sy + ay))): k for (x, y), k in p.items()})
    return out
