"""The fastball nugget: the nugget meteor's own breaded nugget (art_source/mason_nuggets/meteor.py
paint_nugget - its dome normal, crumb noise, crunchy pits and DB32 breading ramp), drawn smaller
and without the meteor's fire-lit rim. Light stays fixed at the cast's upper left whatever the spin,
because the spin turns the surface (lumps, pits, crumbs) and not the light.

`paint(put, cx, cy, rot)` draws one nugget at a sub-pixel centre with its 1px black keyline.
"""
import math

K      = '#000000'
N_HI   = '#EEC39A'   # DB32 cream - breading highlight (Mason CREAM)
N_BASE = '#D9A066'   # DB32 tan - golden breading (props.NUG)
N_WARM = '#C27C3E'   # warm golden-brown mid (nugget_meteor's NM_WARM)
N_MID  = '#AE8358'   # Mason CREAM_DEEP
N_DEEP = '#8F563B'   # DB32 brown - pits / core shadow
N_DARK = '#663931'   # DB32 dark brown - deepest crevices

RX, RY = 5.7, 4.5
# lumps on the rim: (amplitude, harmonic, phase) - the meteor's set, which gives the nugget its
# lopsided "boot" outline so a quarter turn is visible
BUMPS = [(0.06, 2, 1.3), (0.09, 3, 0.2), (0.05, 5, 2.2), (0.05, 11, 0.8)]
LIGHT = (-0.55, -0.62, 0.56)
_n = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _n for c in LIGHT)
PITS = ((-2.2, -1.1), (1.8, 1.6), (3.0, -1.7), (-0.4, 2.3))


def hash01(x, y, seed=0):
    h = (x * 374761393 + y * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def mask(cx, cy, rot, rx=RX, ry=RY):
    m = {}
    cr, sr = math.cos(rot), math.sin(rot)
    R = int(max(rx, ry) * 1.3) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = dx * cr + dy * sr
            v = -dx * sr + dy * cr
            th = math.atan2(v / ry, u / rx)
            lim = 1.0 + sum(a * math.cos(k * th + ph) for a, k, ph in BUMPS)
            d = math.hypot(u / rx, v / ry) / lim
            if d <= 1.0:
                m[(x, y)] = (u, v, d)
    return m


def paint(put, cx, cy, rot, rx=RX, ry=RY, outline=True):
    m = mask(cx, cy, rot, rx, ry)
    cr, sr = math.cos(rot), math.sin(rot)
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    rim = {p for p in m if any((p[0] + a, p[1] + b) not in m for a, b in N4)}
    for (x, y), (u, v, d) in m.items():
        k_ = min(1.0, d) ** 3
        nzl = math.sqrt(max(0.0, 1.0 - k_)) * 0.85 + 0.15
        nul, nvl = (u / rx) * k_ ** 0.5, (v / ry) * k_ ** 0.5
        nx = nul * cr - nvl * sr
        ny = nul * sr + nvl * cr
        ln = math.sqrt(nx * nx + ny * ny + nzl * nzl) or 1.0
        I = (nx * LIGHT[0] + ny * LIGHT[1] + nzl * LIGHT[2]) / ln
        lu, lv = int(math.floor(u + 20)), int(math.floor(v + 20))
        I += (hash01(lu, lv, 7) - 0.5) * 0.16
        if I > 0.74:
            c = N_HI
        elif I > 0.42:
            c = N_BASE
        elif I > 0.14:
            c = N_WARM
        else:
            c = N_DEEP
        hc = hash01(lu, lv, 31)
        if d < 0.86:
            if hc > 0.84 and c == N_BASE and I > 0.50:
                c = N_HI
            elif hc < 0.13 and c == N_BASE:
                c = N_WARM
            elif hc < 0.10 and c == N_WARM:
                c = N_DEEP
        put(x, y, c)
    for (pu, pv) in PITS:
        x = int(math.floor(cx + pu * cr - pv * sr))
        y = int(math.floor(cy + pu * sr + pv * cr))
        if (x, y) in m and (x, y) not in rim:
            put(x, y, N_DEEP)
    if outline:
        out = set()
        for (x, y) in m:
            for a, b in N4:
                if (x + a, y + b) not in m:
                    out.add((x + a, y + b))
        for p in out:
            put(p[0], p[1], K)
    return set(m)
