"""Air FX (no keyline): the round-blast gust burst, the launched-player trail, and attack 2's cold breath.

Palette: his whites and pale blues (W, w, v, l, b) plus the water's pale aqua (~) for frost.
"""
import math

import numpy as np

import le_rig as R
import le_water  # noqa: F401  (registers the shared water ramp keys used for frost)


def _plot(L, x, y, ch):
    h, w = L.shape
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < w and 0 <= yi < h:
        L[yi, xi] = ch


def _arc(L, cx, cy, rx, ry, a0, a1, ch, thick=1, gap_every=0):
    n = max(8, int(abs(a1 - a0) / 2))
    for i in range(n + 1):
        if gap_every and (i // 3) % gap_every == gap_every - 1:
            continue
        a = math.radians(a0 + (a1 - a0) * i / n)
        for t in range(thick):
            _plot(L, cx + (rx - t) * math.cos(a), cy + (ry - t * 0.8) * math.sin(a), ch)


def _swirl(L, cx, cy, r, turns=1.4, ch_in='W', ch_out='l', rot=0.0):
    n = 80
    for i in range(n):
        u = i / (n - 1)
        a = rot + 2 * math.pi * turns * u
        rr = 1.0 + r * u
        _plot(L, cx + rr * math.cos(a), cy + rr * 0.85 * math.sin(a), ch_in if u < 0.55 else ch_out)


# ------------------------------------------------------------------ gust burst: 48 x 48, pivot (24, 24)
GUST_PIVOT = (24, 24)


def gust_burst(k):
    """0 the air cracks off the staff tip (a tight white swirl); 1 the burst: crescents fan out down the
    ring; 2 the front rolls on and widens; 3 streaks thin out. Opens toward +y (at the player)."""
    L = R.blank(48, 48)
    cx, cy = GUST_PIVOT
    if k == 0:
        _swirl(L, cx, cy, 6, 1.6)
        _arc(L, cx, cy + 1, 9, 7, 20, 160, 'l', thick=1)
        for a in (40, 90, 140):
            _plot(L, cx + 11 * math.cos(math.radians(a)), cy + 9 * math.sin(math.radians(a)), 'W')
    elif k == 1:
        _swirl(L, cx, cy, 5, 1.3, rot=1.0)
        _arc(L, cx, cy + 2, 12, 9, 15, 165, 'W', thick=2)
        _arc(L, cx, cy + 4, 17, 13, 25, 155, 'l', thick=1, gap_every=4)
        for x0 in (-14, -7, 0, 7, 14):
            for t in range(4):
                _plot(L, cx + x0 + x0 * 0.05 * t, cy + 14 + t * 2, 'l' if t < 2 else 'w')
    elif k == 2:
        _swirl(L, cx, cy, 4, 1.1, ch_in='l', ch_out='w', rot=2.0)
        _arc(L, cx, cy + 5, 17, 12, 10, 170, 'W', thick=2, gap_every=5)
        _arc(L, cx, cy + 8, 22, 15, 20, 160, 'l', thick=1, gap_every=3)
        for x0 in (-18, -10, -3, 4, 11, 18):
            for t in range(5):
                _plot(L, cx + x0 + x0 * 0.06 * t, cy + 18 + t * 2, 'l' if t < 2 else 'w')
    else:
        _arc(L, cx, cy + 9, 21, 14, 25, 155, 'l', thick=1, gap_every=2)
        _arc(L, cx, cy + 12, 23, 16, 35, 145, 'w', thick=1, gap_every=2)
        for x0 in (-20, -12, -4, 5, 13, 20):
            for t in range(3):
                _plot(L, cx + x0, cy + 21 + t * 3, 'w' if t < 2 else 'v')
    return L


# ------------------------------------------------------------------ trail: 24 x 32, pivot (12, 31)
TRAIL_PIVOT = (12, 31)


def trail(k):
    """Streaks trailing ABOVE a player being blown down the ring (3-frame loop), pivot = bottom centre,
    placed on the player's feet. Streaks slide down a third of their spacing per frame."""
    L = R.blank(24, 32)
    for i, x in enumerate((3, 7, 11, 15, 19)):
        off = (k * 4 + i * 5) % 12
        top = 2 + off
        ln = 10 + (i * 7) % 9
        for t in range(ln):
            y = top + t
            if y < 30:
                ch = 'W' if t > ln - 4 else ('l' if t > ln // 2 else 'w')
                _plot(L, x + (1 if (t // 4) % 2 else 0) * (1 if i % 2 else -1), y, ch)
    # a small swirl riding the trail
    _swirl(L, 12 + (k - 1) * 3, 10 + k * 4, 3, 1.2, ch_in='W', ch_out='l', rot=k)
    return L


# ------------------------------------------------------------------ cold breath: 40 x 100, pivot (20, 2)
BREATH_PIVOT = (20, 2)


def _wisp(L, pts, radii, ch_core, ch_edge):
    h, w = L.shape
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        m = R.tcapsule_mask(ax, ay, bx, by, radii[i], radii[i + 1], w, h)
        m2 = R.tcapsule_mask(ax, ay, bx, by, radii[i] * 0.5, radii[i + 1] * 0.5, w, h)
        L[m & ~m2 & (L == '.')] = ch_edge
        L[m2] = ch_core


def cold_breath(k):
    """0 start (the first gust out of his lips, ~40 long); 1-2 the plume looping (full ~97 to the
    pillar's foot, wisps curling alternately); 3 end (breaking up). At most 40 wide."""
    L = R.blank(40, 100)
    px, py = BREATH_PIVOT
    length = (40, 97, 97, 97)[k]
    for j, side in enumerate((-1, 0, 1)):
        pts, radii = [], []
        wob = (0.0, 1.0, -1.0, 0.0)[k]
        for i in range(30):
            u = i / 29
            spread = side * 15 * u ** 0.9
            curl = math.sin(u * math.pi * 2.2 + j + wob) * 2.4 * u
            pts.append((px + spread + curl, py + u * length))
            radii.append(0.6 + 2.2 * math.sin(math.pi * min(1.0, u * 1.08)) * (0.6 if k == 3 else 1.0))
        if k == 3:
            pts, radii = pts[8:], radii[8:]
        _wisp(L, pts, radii, 'W' if side == 0 else 'l', '~')
    # misty puffs where the wisps roll, and flakes
    for (x, y, r) in ((20, 30, 3.0), (13, 55, 3.5), (27, 62, 3.5), (18, 84, 4.0), (31, 88, 3.0), (8, 90, 3.0)):
        if y < length + 4 and k != 0:
            X, Y = R.centres(40, 100)
            m = ((X - x) / r) ** 2 + ((Y - y) / (r * 0.75)) ** 2 <= 1
            v = R.lambert(R.sphere_normal(X, Y, x, y, r, r * 0.75))
            if k == 3:
                m &= (X + Y) % 3 != 0
            L[m] = np.where(v > 0.6, 'W', np.where(v > 0.3, 'l', '~'))[m]
    for (x, y) in ((5, 20), (34, 26), (9, 44), (33, 48), (4, 70), (36, 74), (15, 96), (26, 36)):
        if y < length and k != 3 or (k == 3 and y > 50):
            for (a, b) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                _plot(L, x + a, y + b, 'W' if (a, b) == (0, 0) else 'l')
    return L
