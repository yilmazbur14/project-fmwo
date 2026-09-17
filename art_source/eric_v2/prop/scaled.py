"""Re-render the approved Eric body at a smaller GEOMETRIC scale (not a pixel downscale).
All masks and shading models are rebuilt from scaled shape coordinates, so outlines stay 1px and
ramps are recomputed at the new size. Hand-drawn details are re-authored at the new size below."""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'anim'))

import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT

S = 0.80            # body scale
HS = 0.84           # head scale (kept a touch larger so the face stays readable)
AX, AY = 48.0, 96.0  # scale anchor: body centre line, ground


def T(x, y, s=None):
    s = S if s is None else s
    return (AX + (x - AX) * s, AY + (y - AY) * s)


_orig_poly = lib.poly
_orig_ell = lib.ell
_orig_normals = lib.normals


def spoly(pts):
    return _orig_poly([T(x, y) for x, y in pts])


def sell(cx, cy, rx, ry, ang=0.0):
    x, y = T(cx, cy)
    return _orig_ell(x, y, rx * S, ry * S, ang)


def snormals(mask, model):
    k = model[0]
    if k == 'sphere':
        _, cx, cy, rx, ry = model[:5]
        x, y = T(cx, cy)
        model = ('sphere', x, y, rx * S, ry * S) + tuple(model[5:])
    elif k == 'cyl':
        _, p0, p1, r = model[:4]
        model = ('cyl', T(*p0), T(*p1), r * S) + tuple(model[4:])
    elif k == 'dist':
        model = ('dist', model[1] * S) + tuple(model[2:])
    return _orig_normals(mask, model)


import parts
import weapons

_orig_arc = parts.arc_line
_orig_seg = parts.seg_line


def sarc(cx, cy, rx, ry, x0, x1):
    x, y = T(cx, cy)
    return _orig_arc(x, y, rx * S, ry * S, int(math.floor(T(x0, 0)[0])), int(math.ceil(T(x1, 0)[0])))


def sseg(p0, p1):
    return _orig_seg(T(*p0), T(*p1))


class scaled_geometry:
    """context manager patching the part modules to build scaled shapes"""
    def __enter__(self):
        self.saved = (parts.poly, parts.ell, weapons.poly, weapons.ell, parts.arc_line, parts.seg_line, lib.normals)
        parts.poly = spoly
        parts.ell = sell
        weapons.poly = spoly
        weapons.ell = sell
        parts.arc_line = sarc
        parts.seg_line = sseg
        lib.normals = snormals
        return self

    def __exit__(self, *a):
        (parts.poly, parts.ell, weapons.poly, weapons.ell, parts.arc_line, parts.seg_line, lib.normals) = self.saved


def at(x, y):
    """scaled integer pixel position for a 96-space pixel coordinate"""
    X, Y = T(x + 0.5, y + 0.5)
    return int(math.floor(X)), int(math.floor(Y))


# ------------------------------------------------------------------ hand details re-authored at the new size
ROUNDEL = """
..kkkkk..
.kWAAABk.
kWAAXABBk
kAAAXABBk
kAXXXXyBk
kAAAyBBCk
kBAAyBCCk
.kBBBCCk.
..kkkkk..
"""

BUCKLE = """
kkkkkk
kgGGhk
kGnnHk
khHHHk
kkkkkk
"""

STRAP = """
kmnk
kmnk
kGhk
kmnk
kmok
kkkk
"""

LEG_L = [
    "......kWAABBBBBCCDk...",
    ".....kBBBBBCCCCCDDEk..",
    "...kkkkkkkkkkkkkkkkkk.",
    "..kAWWAAABBBBBBBCCCDk.",
    ".kkkkkkkkkkkkkkkkkkkkk",
    "kAWWAAAABBBBBBBBCCCDDk",
    "kBBCCCCCCCCCCCDDDDDEEk",
    ".kkkkkkkkkkkkkkkkkkkk.",
]

FIST_V_S = """
..kkkkkkk..
.kIIIIIJJk.
kIIIIIJJJKk
kIkkkkkkkKk
kJkJKKLLkLk
kKkkkkkkkLk
kKkKLLMMkMk
kLkkkkkkkMk
.kLLMMMMNk.
..kkkkkkk..
"""

FIST_AKIMBO_S = """
.kkkkkkk.
kIIIIJJJk
kIIIJJJKk
kkkkkkkkk
kJkKkLkLk
kKkLkMkMk
kLkMkMkNk
.kkkkkkk.
"""


def right_leg_rows(left):
    shift = {'W': 'A', 'A': 'B'}
    out = []
    for row in left:
        chars = list(row[::-1])
        i = 0
        while i < len(chars):
            if chars[i] not in 'k.':
                j = i
                while j < len(chars) and chars[j] not in 'k.':
                    j += 1
                chars[i:j] = [shift.get(c, c) for c in chars[i:j][::-1]]
                i = j
            else:
                i += 1
        out.append(''.join(chars))
    return out


def stamp_legs_s(cv):
    x0, y0 = 23, 88
    cv.stamp('\n'.join(LEG_L), x0, y0)
    cv.stamp('\n'.join(right_leg_rows(LEG_L)), 95 - (x0 + len(LEG_L[0]) - 1), y0)


def pauldron_details_s(cv, f, dome, l1, l2):
    right = f is not parts.ID
    cx0, cy0 = T(23.5 if not right else 96 - 23.5, 41.3)
    ang = -12 if not right else 12
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    for y in range(96):
        for x in range(96):
            if not dome[y][x] or cv.px[y][x] == BLACK:
                continue
            dx, dy = x + 0.5 - cx0, y + 0.5 - cy0
            uu = (dx * ca + dy * sa) / (13.6 * S)
            vv = (-dx * sa + dy * ca) / (10.6 * S)
            t = math.sqrt(uu * uu + vv * vv)
            if vv < 0.15:
                continue
            if 0.68 <= t < 0.79:
                cv.px[y][x] = _DARKER.get(cv.px[y][x], cv.px[y][x])
            elif 0.79 <= t < 0.92:
                cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
    rx, ry = T(23.5 if not right else 96 - 23.5, 41.0)
    cv.stamp(ROUNDEL, int(round(rx)) - 4, int(round(ry)) - 4)
    for (x, y) in [(13, 49), (20, 51), (27, 52), (12, 54), (18, 57)]:
        X, Y = at(x if not right else 95 - x, y)
        if cv.px[Y][X] not in (None, BLACK):
            cv.set(X, Y, 'E')
            if cv.px[Y - 1][X - 1] not in (None, BLACK):
                cv.set(X - 1, Y - 1, 'W')


def tasset_details_s(cv):
    for flip in (False, True):
        for x, y in [(27, 75), (43, 79), (42, 84)]:
            X, Y = at(95 - x if flip else x, y)
            if cv.px[Y][X] not in (None, BLACK):
                cv.set(X, Y, 'E')
                if cv.px[Y - 1][X - 1] not in (None, BLACK):
                    cv.set(X - 1, Y - 1, 'W')


def belt_details_s(cv):
    bx, by = T(48, 74.5)
    cv.stamp(BUCKLE, int(round(bx)) - 3, int(round(by)) - 1)
    for sx in (34.5, 61.5):
        x, y = T(sx, 73.5)
        cv.stamp(STRAP, int(round(x)) - 2, int(round(y)))


def akimbo_arm_s(cv):
    """scaled copy of weapons.arm_right_front with the smaller fist"""
    va = parts.poly([(82.5, 61.5), (91.8, 65.5), (84.5, 75.5), (76.5, 77), (74.5, 70.5)])
    cv.part(va, 'plate', ('cyl', (91, 64), (75, 74), 6.5), th=TH_METAL)
    el = parts.ell(87.3, 64.8, 5.2, 5.0)
    cv.part(el, 'plate', ('sphere', 86.5, 64, 5.5, 5.5), th=TH_METAL)
    fx, fy = T(72, 72)
    cv.stamp(FIST_AKIMBO_S, int(round(fx)) - 4, int(round(fy)) - 4)
