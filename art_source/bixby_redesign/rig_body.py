"""Posable body parts for the animation rig (right side authored; mirror for the left).

Same look as body.py, whose functions are fixed to the approved hover. Here every joint is a
parameter, and the defaults reproduce body.py pixel for pixel (see rig.regress()). Details that ride a
joint (the elbow and thigh tufts, their black cuts) are stored relative to that joint and turn with the
limb, so a re-posed leg keeps its fur.
"""
import math

from pal import amap, fill, poly
from shapes import capsule, chain, edge, half, poly_line, recolor, spt
import body as B

# the approved hover skeleton (right side)
FRONT = dict(shoulder=(119, 100), sh_end=(124, 110), arm_top=(123, 108), elbow=(128, 119),
             fore_top=(127, 121), wrist=(124, 137), paw=(123, 143))
HIND = dict(hip=(136, 110), hock=(152, 128), ankle=(152, 139), paw=(153, 144))

_F_TUFT = [(130, 112), (137, 117), (133, 118), (138, 123), (131, 124), (128, 126)]
_F_CUTS = [[(130, 115), (134, 120)], [(127, 113), (128, 118)]]
_F_GROOVE = [(128, 124), (126, 133)]
_H_TUFT = [(146, 110), (158, 115), (152, 118), (159, 122), (152, 124)]
_H_CUTS = [[(149, 115), (154, 121)], [(141, 118), (146, 124)]]


def _ang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def _carry(pts, old_origin, old_ang, new_origin, new_ang):
    """Move points riding a joint along with it: rotate about the joint by the change in limb angle,
    then translate. At zero change this is the identity (no rounding drift)."""
    da = new_ang - old_ang
    c, s = math.cos(da), math.sin(da)
    out = []
    for (x, y) in pts:
        rx, ry = x - old_origin[0], y - old_origin[1]
        if abs(da) > 1e-9:
            rx, ry = rx * c - ry * s, rx * s + ry * c
        out.append((new_origin[0] + rx, new_origin[1] + ry))
    return out


def front_leg(J=None, dx=0, dy=0):
    """[shoulder, upper arm, forearm] parts. J overrides joints of FRONT (absolute coordinates)."""
    F = dict(FRONT)
    if J:
        F.update(J)
    F = {k: (v[0] + dx, v[1] + dy) for k, v in F.items()}
    shoulder = fill(capsule(F['shoulder'], F['sh_end'], 10, 9), 'c')
    B.black_shade(shoulder)
    sh_cut = _carry([(116, 104), (122, 113)], FRONT['shoulder'], _ang(FRONT['shoulder'], FRONT['sh_end']),
                    F['shoulder'], _ang(F['shoulder'], F['sh_end']))
    for q in poly_line(sh_cut):
        if q in shoulder and shoulder[q] == 'c':
            shoulder[q] = 'b'
    upper = fill(capsule(F['arm_top'], F['elbow'], 8, 7), 't')
    a0 = _ang(FRONT['arm_top'], FRONT['elbow'])
    a1 = _ang(F['arm_top'], F['elbow'])
    tuft = _carry(_F_TUFT, FRONT['elbow'], a0, F['elbow'], a1)
    upper.update({p: 't' for p in poly(tuft)})
    recolor(upper, edge(upper, 0, -1, 1), 'u')
    recolor(upper, edge(upper, 1, 0, 1), 's')
    recolor(upper, edge(upper, 0, 1, 2), 's')
    recolor(upper, edge(upper, 0, 1, 1), 'r')
    for seg in _F_CUTS:
        for q in poly_line(_carry(seg, FRONT['elbow'], a0, F['elbow'], a1)):
            if q in upper:
                upper[q] = 'k'
    fore = fill(capsule(F['fore_top'], F['wrist'], 6.4, 5.4), 'x')
    recolor(fore, edge(fore, -1, 0, 2), 'w', only='x')
    recolor(fore, edge(fore, 1, 0, 3), 'y')
    recolor(fore, edge(fore, 1, 0, 1), 'z')
    g = _carry(_F_GROOVE, FRONT['fore_top'], _ang(FRONT['fore_top'], FRONT['wrist']),
               F['fore_top'], _ang(F['fore_top'], F['wrist']))
    for q in poly_line(g):
        if q in fore and fore[q] == 'x':
            fore[q] = 'y'
    return [shoulder, upper, fore]


def hind_leg(J=None, dx=0, dy=0):
    """[thigh, shin] parts. J overrides joints of HIND (absolute coordinates)."""
    H = dict(HIND)
    if J:
        H.update(J)
    H = {k: (v[0] + dx, v[1] + dy) for k, v in H.items()}
    thigh = fill(capsule(H['hip'], H['hock'], 10, 6.5), 't')
    a0 = _ang(HIND['hip'], HIND['hock'])
    a1 = _ang(H['hip'], H['hock'])
    thigh.update({p: 't' for p in poly(_carry(_H_TUFT, HIND['hock'], a0, H['hock'], a1))})
    recolor(thigh, edge(thigh, 0, -1, 1), 'u')
    recolor(thigh, edge(thigh, 1, 0, 1), 's')
    recolor(thigh, edge(thigh, 0, 1, 2), 's')
    recolor(thigh, edge(thigh, 0, 1, 1), 'r')
    for seg in _H_CUTS:
        for q in poly_line(_carry(seg, HIND['hock'], a0, H['hock'], a1)):
            if q in thigh:
                thigh[q] = 'k'
    shin = fill(capsule(H['hock'], H['ankle'], 5, 4.6), 'x')
    recolor(shin, edge(shin, -1, 0, 1), 'w', only='x')
    recolor(shin, edge(shin, 1, 0, 2), 'y')
    recolor(shin, edge(shin, 1, 0, 1), 'z')
    return [thigh, shin]


# Planted paws: the hanging paw maps with the claws cut down to stubs resting on the ground, so the
# claw row is the ground row. (Rows are the same as body.FRONT_PAW / HIND_PAW above the claws.)
FRONT_PAW_PLANTED = B.FRONT_PAW[:11] + [
    ".kkk. kkkk. kkkk. kkk.",   # claw stubs on the ground, under each toe
]
HIND_PAW_PLANTED = B.HIND_PAW[:9] + [
    ".kkk. kkk.k kk.kk k.",
]
# paw map top-left relative to the paw centre (from body.FRONT_PAW_XY / HIND_PAW_XY)
FRONT_PAW_OFF = (B.FRONT_PAW_XY[0] - FRONT['paw'][0], B.FRONT_PAW_XY[1] - FRONT['paw'][1])
HIND_PAW_OFF = (B.HIND_PAW_XY[0] - HIND['paw'][0], B.HIND_PAW_XY[1] - HIND['paw'][1])


def paw(front=True, centre=None, planted=False, dx=0, dy=0):
    """A paw map placed by its centre. Hanging paws hook their claws 3 rows below the toes; planted
    ones end on the claw-stub row (the ground)."""
    if front:
        rows = FRONT_PAW_PLANTED if planted else B.FRONT_PAW
        c = centre or FRONT['paw']
        off = FRONT_PAW_OFF
    else:
        rows = HIND_PAW_PLANTED if planted else B.HIND_PAW
        c = centre or HIND['paw']
        off = HIND_PAW_OFF
    return amap(rows, int(round(c[0] + off[0] + dx)), int(round(c[1] + off[1] + dy)))


def paw_ground_y(front=True, centre=None, planted=True):
    """The ground row under a planted paw placed at this centre (its claw-stub row)."""
    c = centre or (FRONT['paw'] if front else HIND['paw'])
    off = FRONT_PAW_OFF if front else HIND_PAW_OFF
    rows = FRONT_PAW_PLANTED if front else HIND_PAW_PLANTED
    return int(round(c[1] + off[1])) + len(rows) - 1


def torso(dx=0, dy=0):
    """mantle (black saddle ruff), belly and chest, as body.py draws them, moved as one."""
    parts = [B.mantle(dy), B.belly(dy), B.chest(dy)]
    if dx:
        parts = [{(x + dx, y): k for (x, y), k in p.items()} for p in parts]
    return parts


def side_neck(base=(118, 98), top=(142, 82), dx=0, dy=0):
    n = fill(capsule((base[0] + dx, base[1] + dy), (top[0] + dx, top[1] + dy), 10, 10), 'c')
    B.black_shade(n)
    return n


def tail(path, r0=4.2, r1=2.8):
    t = fill(chain(path, r0, r1), 'c')
    recolor(t, edge(t, 0, -1, 1), 'd')
    recolor(t, edge(t, 0, 1, 1), 'b')
    recolor(t, edge(t, -1, 0, 1), 'e')
    return t


TAIL_TIP = [(6, 118), (5, 110), (8, 102), (10, 106), (12, 95), (15, 103), (19, 94), (18, 106),
            (16, 116), (12, 121)]
TAIL_TIP_BASE = (12, 118)       # where the tip meets the tail's end in the approved pose


def tail_tip(at=(12, 118)):
    """Bixby's white flame tip, placed by its base."""
    pts = [(x - TAIL_TIP_BASE[0] + at[0], y - TAIL_TIP_BASE[1] + at[1]) for (x, y) in TAIL_TIP]
    t = fill(poly(pts), 'x')
    recolor(t, edge(t, -1, 0, 1), 'w')
    recolor(t, edge(t, 1, 0, 1), 'y')
    recolor(t, edge(t, 0, 1, 1), 'y')
    return t
