"""Danny's sumo limbs, each one form sculpted with its muscles as plateaus, plus open anatomy lines.

Geometry is written for the viewer's left and mirrored about x = 87.5; the light is re-run for the
mirrored side so both are lit from the upper left.
"""
from sumo_lib import (spoly, sculpt, ellipse, mirror_pts, mirror_set, taper_line, lower_edge,
                      upper_edge, crease, MIR, SKIN)
import sumo_lib as L

SKINSET = set(SKIN)


def _m(pts, side):
    return pts if side > 0 else mirror_pts(pts)


def _mp(pts_list, side):
    return [[(MIR - x, y) for (x, y) in pts] if side < 0 else pts for pts in pts_list]


def _x(pts, xf):
    """A pose's point transform on an outline (None: as drawn)."""
    return [xf(p) for p in pts] if xf else pts


def _xq(q, xf):
    """A pose's point transform on one pixel (None: as drawn)."""
    if not xf:
        return q
    x, y = xf(q)
    return (int(round(x)), int(round(y)))


# ------------------------------------------------------------------ ARMS
UPPER = [(19, 58), (15, 64), (12, 71), (10.5, 78), (11.5, 85), (15.5, 89), (21, 88.5), (27.5, 81),
         (34, 74), (39, 67.5), (42, 61), (36, 56), (27, 56)]
BICEPS = [(30, 61), (37, 59.5), (41, 63.5), (38, 70.5), (32, 77.5), (26, 84), (22.5, 82), (23.5, 74), (26.5, 67)]
TRICEPS = [(17, 61), (22, 60.5), (23.5, 68), (21, 78), (17, 85), (13, 84), (12, 76), (13.5, 68)]
ARM_LINE = [(24.5, 62), (24, 69), (22.5, 77), (20, 84.5)]

DELT = [(41, 34), (31, 34.5), (23.5, 38), (18.5, 44), (16, 51.5), (16, 59), (18, 66), (21.5, 71.5),
        (26, 70.5), (32, 67.5), (38.5, 64.5), (44.5, 59), (47.5, 51), (47, 43), (44.5, 37.5)]
DELT_FRONT = [(44, 38), (47, 45), (46, 55), (41, 62), (34, 66), (31.5, 58), (33.5, 46), (38.5, 39)]
DELT_SIDE = [(30, 36.5), (22.5, 40), (18, 48), (17.5, 58), (20.5, 66), (25, 68), (29, 60), (29.5, 47)]
DELT_GROOVE = [(33, 39), (31.5, 47), (30.5, 56), (28, 65)]

FORE = [(12, 83), (12.5, 89), (16.5, 94), (23, 96), (29, 96), (33.5, 94.5), (34, 88), (30, 84.5),
        (25, 81), (19.5, 79.5), (14.5, 80)]
BRACHIO = [(14, 81), (20, 80.2), (26, 82), (30, 86), (24.5, 88.5), (17, 88.5), (13, 86)]
FORE_LINE = [(13.5, 88.5), (19, 90), (25.5, 89.5), (31.5, 87)]


def upper_arm(side):
    m = spoly(_m(UPPER, side))
    lay = [(spoly(p), 2.2, 0.28) for p in _mp([BICEPS, TRICEPS], side)]
    return sculpt(m, lay, sigma=4.5, exposure=0.04)


def deltoid(side):
    m = spoly(_m(DELT, side))
    lay = [(spoly(p), 2.6, 0.25) for p in _mp([DELT_FRONT, DELT_SIDE], side)]
    return sculpt(m, lay, sigma=6.5, exposure=0.06)


def forearm(side):
    m = spoly(_m(FORE, side))
    lay = [(spoly(p), 2.0, 0.3) for p in _mp([BRACHIO], side)]
    return sculpt(m, lay, sigma=4.0, exposure=0.05)


def arm_lines(px, side, dx=0, dy=0):
    sh = lambda pts: [(x + dx, y + dy) for (x, y) in pts]  # noqa: E731
    taper_line(px, sh(_m(ARM_LINE, side)), 'k', taper_key='3', taper=0, only=SKINSET)
    taper_line(px, sh(_m(FORE_LINE, side)), 'k', taper_key='3', taper=3, only=SKINSET)


# ------------------------------------------------------------------ LEGS
THIGH = [(64, 101), (52, 99.5), (42, 99.5), (33, 101), (25, 103.5), (18.5, 107), (14, 111), (12, 115),
         (12.5, 118.5), (16, 120), (23, 119.5), (31, 118), (43, 117), (55, 116.5), (67, 116.5)]
QUAD = [(60, 100), (44, 99.8), (32, 101.3), (23.5, 104.5), (17.5, 109), (15, 113), (19, 114.5), (26, 112),
        (36, 110), (48, 108.5), (60, 107.5)]
TEARDROP = [(17, 115.5), (21, 113), (27, 114.5), (29.5, 117.5), (26, 120.5), (19.5, 121), (16.5, 119)]
KNEE = [(12.5, 111.5), (15, 109), (18, 110.5), (18.5, 115), (16, 118.5), (13, 117.5)]

# the calf shows its full outward bulge under the knee; the ankle pinches in above the foot
CALF = [(15, 116), (10.5, 120.5), (7.5, 126), (7.5, 130.5), (10, 134), (19, 135.5), (28, 135), (32.5, 132),
        (34.5, 127), (34, 121.5), (30, 117.5), (22, 115)]
CALF_OUT = [(14, 118), (10, 122), (8.5, 127), (10, 131.5), (14.5, 131), (16.5, 125), (16.5, 119)]
CALF_IN = [(26, 118.5), (31, 120), (33.5, 125), (32.5, 130), (28.5, 132.5), (25.5, 128), (25, 122)]
SHIN_L = [(18.5, 119), (18.5, 125), (17, 131)]
SHIN_R = [(25, 120), (25, 126), (26, 131)]

FOOT = [(12, 133), (7, 135), (3.5, 137.5), (2.5, 140.5), (4, 142.5), (34, 142.5), (36.5, 140.5), (35, 136.5),
        (30, 133.5)]
ANKLE_WRAP = [(11, 129.5), (21, 129.5), (32, 129.5), (32.5, 132), (31, 134), (21, 134.5), (11.5, 134), (10, 132)]


def calf(side, xf=None):
    m = spoly(_x(_m(CALF, side), xf))
    lay = [(spoly(_x(p, xf)), 2.2, 0.3) for p in _mp([CALF_OUT, CALF_IN], side)]
    return sculpt(m, lay, sigma=5.0, exposure=0.04, tilt=(0.0, -0.2))


def thigh(side, xf=None):
    m = spoly(_x(_m(THIGH, side), xf))
    lay = [(spoly(_x(p, xf)), s, a) for p, s, a in zip(_mp([QUAD, TEARDROP, KNEE], side), (3.0, 2.0, 1.8),
                                                        (0.3, 0.28, 0.2))]
    return sculpt(m, lay, sigma=6.0, bulge=0.45, exposure=0.08, tilt=(0.0, -0.55))


def leg_lines(px, side, creases=True, xf=None):
    """Only the lines that read as anatomy at 3x. Black lines on the thigh read as cracks (and a
    teardrop edge plus a quad crease made a shape at the knee that read as a closed eye), so the
    thigh's muscles are marked in dark skin, not black."""
    # the kneecap catches the light at the front of the knee
    for (x, y) in ((13, 113), (14, 113), (13, 114), (14, 112)):
        q = _xq((x, y) if side > 0 else (MIR - x, y), xf)
        if px.get(q) in SKINSET:
            px[q] = '7' if side > 0 else '6'
    if creases:
        # the quad's lower edge, from above the knee half-way back to the hip
        quad = spoly(_x(_m(QUAD, side), xf))
        le = lower_edge(quad)
        xs = [x for x, y in le]
        knee_x = min(xs) if side > 0 else max(xs)
        for (x, y) in le:
            d = abs(x - knee_x)
            if 4 <= d <= 22 and px.get((x, y)) in set('4567'):
                px[(x, y)] = '3' if d <= 16 else '4'
        # the teardrop's upper edge above the knee
        td = spoly(_x(_m(TEARDROP, side), xf))
        for (x, y) in upper_edge(td):
            if px.get((x, y)) in set('4567'):
                px[(x, y)] = '3'
    # the shin: one line on the inside of the calf's outer head, fading at the knee
    pts = _x(_m(SHIN_R, side), xf)
    taper_line(px, pts[::-1], 'k', taper_key='3', taper=2, only=SKINSET)


def foot(side, xf=None):
    m = spoly(_x(_m(FOOT, side), xf))
    return sculpt(m, [], sigma=3.0, exposure=0.05, tilt=(0.0, -0.5))


# Toes at the leading end of each foot: the foot points out and towards the viewer, so the toes are
# a row along its outer-lower edge, the big toe nearest, the little toe furthest. (x_at_sole, height)
# of each split, viewer's-left foot; each split leans outwards as it rises.
TOE_SPLITS = [(6, 3), (9, 4), (12.5, 4), (17, 5)]
TOE_CROWNS = [(4, 139), (7, 139), (10, 138), (14, 138), (20, 138), (21, 138)]


def toes(px, side, xf=None):
    for (x, hgt) in TOE_SPLITS:
        for j in range(hgt):
            q = (int(round(x - j * 0.4)), 142 - j)
            if side < 0:
                q = (MIR - q[0], q[1])
            q = _xq(q, xf)
            if px.get(q) in SKINSET:
                px[q] = 'k'
    for (x, y) in TOE_CROWNS:
        q = _xq((x, y) if side > 0 else (MIR - x, y), xf)
        if px.get(q) in SKINSET:
            px[q] = '7' if side > 0 else '6'


def ankle_wrap_poly(pts, side):
    """White bandage round an ankle given by its outline, wound on the diagonal like the wrist
    wraps; side picks which way the turns lean and which edge is in shade."""
    import lib as jl
    body = spoly(pts, 1)
    part = {p: 'W' for p in body}
    for (x, y) in body:
        u = x if side > 0 else MIR - x
        if (u + y) % 4 == 0:
            part[(x, y)] = 'H'
    jl.rim(part, 'H', 0, 1, depth=1)
    jl.rim(part, 'h', 1, 0, depth=1)
    if side < 0:
        jl.rim(part, 'h', 0, 1, depth=1)
    return part


def ankle_wrap(side, xf=None):
    return ankle_wrap_poly(_x(_m(ANKLE_WRAP, side), xf), side)


# ------------------------------------------------------------------ DEFEAT: LIMP ARMS, SEATED LEGS
# The ready stance's upper arm and deltoid, then a forearm that simply hangs, the wrap at the wrist
# and a loose hand resting on the thigh. Viewer's left; mirrored.
LIMP_FORE = [(11.5, 84), (10.5, 91), (11.5, 98), (14, 103.5), (18.5, 106), (23.5, 104.5), (25.5, 99), (25, 91.5),
             (22.5, 86), (17, 82)]
LIMP_BRACHIO = [(11.5, 85.5), (17, 84), (22, 87.5), (22, 94), (17, 96.5), (12.5, 93.5)]
LIMP_WRAP = [(13.5, 102), (24.5, 101.5), (25.5, 104.5), (24.5, 108.5), (14.5, 109), (13, 105.5)]
LIMP_HAND = [(14, 107.5), (12.5, 112), (13.5, 117), (17, 120.5), (21.5, 120.5), (25, 117), (26, 112), (25, 107.5)]
LIMP_FINGERS = [((17, 115), (17, 120)), ((20.5, 115.5), (20.5, 120))]
LIMP_LINE = [(12.5, 92), (17, 95.5), (22.5, 95)]


def limp_forearm(side):
    return sculpt(spoly(_m(LIMP_FORE, side)), [(spoly(p), 2.0, 0.3) for p in _mp([LIMP_BRACHIO], side)],
                  sigma=4.0, exposure=0.04)


def limp_hand(side):
    return sculpt(spoly(_m(LIMP_HAND, side)), [], sigma=3.0, exposure=0.04)


def limp_lines(px, side, dx=0, dy=0):
    sh = lambda pts: [(x + dx, y + dy) for (x, y) in pts]  # noqa: E731
    taper_line(px, sh(_m(ARM_LINE, side)), 'k', taper_key='3', taper=0, only=SKINSET)
    taper_line(px, sh(_m(LIMP_LINE, side)), 'k', taper_key='3', taper=2, only=SKINSET)


def limp_fingers(px, side, dx=0, dy=0):
    for a, b in LIMP_FINGERS:
        pts = _m([a, b], side)
        taper_line(px, [(x + dx, y + dy) for (x, y) in pts], 'k', only=SKINSET)


# Seated (the defeat): he sinks straight down onto his backside, thighs flat on the canvas and
# splayed, soles turned to the viewer with the toes up. Drawn in place for a body lowered 10px.
THIGH_SIT = [(70, 111), (58, 110), (46, 110.5), (35, 112.5), (26, 116), (19, 121), (14.5, 127), (13, 133),
             (15, 138.5), (21, 142), (32, 142.5), (46, 142), (58, 140.5), (70, 138)]
QUAD_SIT = [(66, 111), (52, 110.5), (40, 111.5), (30, 114.5), (22, 119), (17, 125), (22, 126), (32, 121),
            (44, 118), (56, 117), (66, 117)]
FOOT_SIT = [(9, 117.5), (5, 120.5), (3, 126), (3, 133), (5, 139), (9.5, 142.5), (15.5, 142), (18.5, 137), (19, 128),
            (16.5, 121)]
SOLE_SIT = [(8, 122), (5.5, 127), (6, 135), (10, 139.5), (14.5, 138), (16.5, 131), (15.5, 124)]
TOE_SPLITS_SIT = [((7, 118), (7, 120)), ((10, 117), (10, 119.5)), ((13, 117.5), (13, 120)), ((15.5, 119), (15.5, 121.5))]


def thigh_sit(side, dy=0):
    sh = lambda pts: [(x, y + dy) for (x, y) in pts]  # noqa: E731
    return sculpt(spoly(sh(_m(THIGH_SIT, side))), [(spoly(sh(p)), 3.0, 0.3) for p in _mp([QUAD_SIT], side)],
                  sigma=6.0, bulge=0.45, exposure=0.08, tilt=(0.0, -0.55))


def foot_sit(side):
    return sculpt(spoly(_m(FOOT_SIT, side)), [(spoly(p), 2.0, 0.25) for p in _mp([SOLE_SIT], side)],
                  sigma=3.0, exposure=0.1)


def toes_sit(px, side):
    for a, b in TOE_SPLITS_SIT:
        taper_line(px, _m([a, b], side), 'k', only=SKINSET)


# Seated: the forearm angles in so the palm rests on top of the thigh, clear of the sole.
REST_FORE = [(11.5, 84), (11.5, 91), (14.5, 97.5), (20, 103), (27, 107), (33, 108.5), (37, 105), (35, 99.5),
             (29.5, 93.5), (23.5, 87), (18, 82)]
REST_BRACHIO = [(12, 85.5), (18, 84), (24, 88.5), (27, 94), (21, 96), (14.5, 92.5)]
REST_WRAP = [(28.5, 101.5), (37.5, 101), (39.5, 104.5), (38.5, 109), (30, 110.5), (27.5, 106)]
REST_HAND = [(29.5, 107), (28, 111.5), (29.5, 116.5), (33.5, 119.5), (38.5, 119), (42, 115), (42.5, 110),
             (40.5, 106.5)]
REST_FINGERS = [((33.5, 114), (33.5, 119)), ((37.5, 114.5), (37.5, 118.5))]
REST_LINE = [(13, 91), (18.5, 96), (25, 99)]


def rest_forearm(side):
    return sculpt(spoly(_m(REST_FORE, side)), [(spoly(p), 2.0, 0.3) for p in _mp([REST_BRACHIO], side)],
                  sigma=4.0, exposure=0.04)


def rest_hand(side):
    return sculpt(spoly(_m(REST_HAND, side)), [], sigma=3.0, exposure=0.05)


def rest_lines(px, side, dx=0, dy=0):
    sh = lambda pts: [(x + dx, y + dy) for (x, y) in pts]  # noqa: E731
    taper_line(px, sh(_m(ARM_LINE, side)), 'k', taper_key='3', taper=0, only=SKINSET)
    taper_line(px, sh(_m(REST_LINE, side)), 'k', taper_key='3', taper=2, only=SKINSET)
    for a, b in REST_FINGERS:
        taper_line(px, sh(_m([a, b], side)), 'k', only=SKINSET)
