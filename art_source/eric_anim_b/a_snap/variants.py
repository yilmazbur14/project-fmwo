"""parametric body-layer variants (rendered in 96-space with the approved part code)"""
import math
import lib
import parts
from parts import torso_details
from lib import TH_CLOTH
import rig

_CAPE_BASE = [(48, 40), (30, 39), (17, 45), (11.5, 56), (8.5, 68), (6.5, 80), (5, 90),
              (7, 94.5), (10, 90.5), (13.5, 95.5), (18, 90), (22, 94), (26, 91), (30, 95.5), (34, 92),
              (48, 92),
              (62, 92.5), (66, 95.5), (70, 91), (74.5, 94.5), (79, 89.5), (83, 95), (86.5, 90.5), (90, 93.5), (91.5, 88),
              (89.5, 78), (87.5, 67), (84.5, 56), (79, 45), (66, 39)]


def cape_pts(sway=0.0, flare=0.0, lift=0.0, hem_y=None):
    out = []
    for x, y in _CAPE_BASE:
        t = max(0.0, (y - 50) / 45.0)
        nx = x + sway * t + (flare * t if x > 48 else -flare * t if x < 48 else 0)
        ny = y - lift * t
        if hem_y is not None and y > 86:
            ny = min(ny, hem_y + (y - 92))
        out.append((nx, ny))
    return out


def cape_layer(sway=0.0, flare=0.0, lift=0.0, hem_y=None, key=None):
    key = key or ('cape', round(sway, 2), round(flare, 2), round(lift, 2), hem_y)
    if key in rig._CACHE:
        return rig._CACHE[key]

    def fn(cv):
        pts = cape_pts(sway, flare, lift, hem_y)
        m = lib.poly(pts)
        cv.part(m, 'cape', ('sphere', 44, 56, 46, 46, 0.7), th=[9.0, 0.95, 0.80, 0.55, 0.2], bias=0)
        for p0, p1 in [((13, 62), (10, 86)), ((19, 70), (18, 89)), ((81, 64), (84, 86)), ((75, 72), (76, 88))]:
            q0 = (p0[0] + sway * max(0, (p0[1] - 50) / 45), p0[1])
            q1 = (p1[0] + sway * max(0, (p1[1] - 50) / 45), p1[1] - lift * max(0, (p1[1] - 50) / 45))
            ln = lib.inter(parts.seg_line(q0, q1), m)
            for y in range(96):
                for x in range(96):
                    if ln[y][x] and cv.px[y][x] != lib.BLACK:
                        cv.px[y][x] = lib.PALC['S']
    rig._CACHE[key] = rig._layer(fn)
    return rig._CACHE[key]


_TORSO = [(48, 33), (39, 34), (31, 37), (26, 42), (22.5, 49), (21, 56), (21.3, 61.5), (23.2, 65.8),
          (27.3, 69.2), (34, 71.4), (41, 72.4), (48, 72.7)]


def torso_layer(widen=0.0, drop=0.0):
    key = ('torso', widen, drop)
    if key in rig._CACHE:
        return rig._CACHE[key]

    def fn(cv):
        half = []
        for x, y in _TORSO:
            if y > 44:
                k = min(1.0, (y - 44) / 14.0)
                x = 48 - (48 - x) - widen * k
                y = y + drop * k
            half.append((x, y))
        m = lib.poly(lib.sym_pts(half))
        cv.part(m, 'plate', ('sphere', 46.5, 53, 28.5 + widen, 25.5, 0.05), th=lib.TH_METAL)
        torso_details(cv, m)
    rig._CACHE[key] = rig._layer(fn)
    return rig._CACHE[key]


def cape_kneel(flare=4.0, sway=0.0):
    key = ('cape_kneel', flare, sway)
    if key in rig._CACHE:
        return rig._CACHE[key]
    pts = []
    for x, y in _CAPE_BASE:
        t = max(0.0, (y - 50) / 45.0)
        ny = 40 + (y - 40) * 47.0 / 55.0 if y > 40 else y
        nx = x + sway * t + (flare * t if x > 48 else -flare * t if x < 48 else 0)
        pts.append((nx, ny))

    def fn(cv):
        m = lib.poly(pts)
        cv.part(m, 'cape', ('sphere', 44, 56, 46, 46, 0.7), th=[9.0, 0.95, 0.80, 0.55, 0.2], bias=0)
        for p0, p1 in [((12, 60), (8, 84)), ((18, 66), (16, 84)), ((82, 62), (86, 82)), ((76, 68), (78, 84))]:
            ln = lib.inter(parts.seg_line(p0, p1), m)
            for y in range(96):
                for x in range(96):
                    if ln[y][x] and cv.px[y][x] != lib.BLACK:
                        cv.px[y][x] = lib.PALC['S']
    rig._CACHE[key] = rig._layer(fn)
    return rig._CACHE[key]
