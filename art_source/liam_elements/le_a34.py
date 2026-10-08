"""Attacks 3 and 4 (DESIGN APPROVAL PASS, 2026-09-29): the pillar row, tornados (air, ignition, fire), the
fire quake ring, the steam (puffs and three fog densities), the red lunge triangle, the water jet /
extinguish puff / launch trail, the flame overlay for the impaled player, and the impact where Bixby's
fire column hits. Sizes are soft (the architect's contract comes later): every piece is a function of
a few constants at the top of its section.

Fire uses Bixby's approved flyby-curtain ramp exactly, so Liam's fire and his dog's fire are one fire.
Floor/FX pieces carry no keyline (the house FX rule); the pillars and the triangle do.
"""
import math

import numpy as np

import le_rig as R
import le_water as W
import le_pillar as PL
from le_ice import pnoise2

# ------------------------------------------------------------------ palettes (new keys, own colours)
FIRE = {   # bixby_flyby_curtain.png's 7 colours
    'α': (255, 242, 176, 255), 'β': (255, 196, 90, 255), 'γ': (255, 140, 46, 255), 'δ': (224, 86, 26, 255),
    'ε': (154, 42, 16, 255), 'ζ': (87, 12, 24, 255),
}
ROCK = {   # bixby_quake_ring.png's crack browns
    'η': (106, 60, 34, 255), 'θ': (44, 24, 16, 255), 'ι': (138, 85, 48, 255), 'κ': (74, 40, 24, 255),
}
STEAM = {  # semi-transparent vapour (steam must let the floor, the player and the tells read through)
    'λ': (255, 255, 255, 210), 'μ': (236, 242, 248, 175), 'ν': (208, 220, 232, 150), 'ξ': (184, 198, 214, 120),
}
FOG = {    # the fog tile's bands: pale blue-white at rising alpha
    'π': (232, 238, 244, 60), 'ρ': (232, 238, 244, 95), 'σ': (236, 241, 246, 130), 'τ': (240, 244, 248, 165),
    'υ': (244, 247, 250, 190),
}
TELL = {   # the parry badge's reds (parry_tell.png) + a hot core
    'φ': (217, 87, 99, 255), 'χ': (172, 50, 50, 255), 'ψ': (255, 196, 200, 255), 'ω': (110, 16, 28, 255),
}
for d in (FIRE, ROCK, STEAM, FOG, TELL):
    R.PAL.update(d)
FIRE_RAMP = 'ζεδγβαW'       # dark -> white-hot


def blank(w, h):
    return R.blank(w, h)


def centres(w, h):
    return R.centres(w, h)


# ------------------------------------------------------------------ the pillar row (side pillars: no runes)
def side_pillar(variant=0, seed=11):
    """A wall pillar: his slate column (same cell and anchor as liam_pillar.png), no runes; three variants
    at stand heights 50 / 44 / 47 so a row never reads as one stamp."""
    lift = (0, 6, 3)[variant]
    top = PL.TOP_Y0 + lift
    m = PL.silhouette(top=top)
    L = PL.paint_rock(m, top=top, seed=seed + variant * 7)
    PL.fissures(L, m)
    PL.moss(L, m, top=top, seed=seed + variant * 3)
    PL.keyline(L, m, top=top)
    PL.rubble(L, seed)
    return PL.clip(L)


def side_pillar_rise(k, variant=0):
    """3 key frames of a wall pillar punching up (a third, two thirds, full)."""
    full = side_pillar(variant)
    frac = (0.3, 0.65, 1.0)[k]
    if k == 2:
        return full
    height = PL.BASE_Y - PL.TOP_Y0 - (0, 6, 3)[variant]
    shift = int(round(height * (1 - frac)))
    body = full.copy()
    body[PL.BASE_Y - 1:, :] = '.'
    sunk = R.shift(body, 0, shift)
    sunk[PL.BASE_Y:, :] = '.'
    out = PL.blank()
    R.composite(out, sunk)
    PL.rubble(out, 5 + k, spread=1.1)
    PL.dust(out, [(12, 72, 4.5), (52, 72, 4.5)])
    return PL.clip(out)


# ------------------------------------------------------------------ tornados
TW_, TH_ = 48, 96
T_PIVOT = (24, 93)            # the funnel's foot on the floor: where it pulls from and the rings start


def _funnel(phase, kind='air', fire_from=None):
    """A funnel as a surface of revolution: wide at the top, a thin foot. Helical streaks wind up it
    (they turn a quarter per frame), lit from the upper left. kind 'air' leaves the dim streak gaps open
    (you see the ring through it); 'fire' is solid with a white-hot core. fire_from: rows >= burn."""
    L = blank(TW_, TH_)
    for y in range(2, 91):
        u = (y - 2) / 88.0                                  # 0 top .. 1 foot
        half = 2.6 + 19.5 * (1 - u) ** 1.35
        cx = 24 + 2.2 * math.sin(u * 5.0 + phase * math.pi / 2)
        burning = kind == 'fire' or (fire_from is not None and y >= fire_from)
        for x in range(TW_):
            dx = (x + 0.5 - cx) / half
            if abs(dx) > 1.0:
                continue
            th = math.asin(max(-1.0, min(1.0, dx)))          # -pi/2 .. pi/2 across the front
            stripe = ((th / math.pi) * 2.6 + y / 9.0 - phase * 0.25) % 1.0
            lit = 0.55 - 0.45 * dx                           # the left side catches the light
            edge = abs(dx) > 0.86
            if burning:
                v = lit * 0.6 + (0.45 if stripe < 0.35 else (0.15 if stripe < 0.6 else -0.05))
                v += 0.25 * (1 - abs(dx)) * (1 - u * 0.3)   # hot core
                ramp = 'εδγβαW'
                idx = int(max(0, min(len(ramp) - 1, v * len(ramp))))
                ch = ramp[idx] if not edge else ('ζ' if dx > 0 else 'δ')
                L[y, x] = ch
            else:
                if stripe > 0.62 and not edge:
                    continue                                  # airy gaps between the streaks
                v = lit * 0.7 + (0.4 if stripe < 0.3 else 0.1)
                ramp = 'TvwW'
                idx = int(max(0, min(len(ramp) - 1, v * len(ramp))))
                L[y, x] = ramp[idx] if not edge else ('v' if dx < 0 else 'T')
        # wisps flicking off the rim
        if (y + phase * 3) % 11 == 0:
            side = 1 if (y // 11) % 2 else -1
            for t in range(1, 4):
                xx = int(round(cx + side * (half + t)))
                if 0 <= xx < TW_:
                    L[y - (t // 2), xx] = ('β' if burning else 'w') if t < 3 else ('γ' if burning else 'v')
    # the foot: a churning skirt on the floor (dust, or a ring of flame)
    X, Y = centres(TW_, TH_)
    burning_foot = kind == 'fire' or (fire_from is not None and fire_from <= 90)
    for (ddx, r) in ((-7, 3.4), (7, 3.4), (0, 4.2)):
        m = ((X - 24 - ddx) / r) ** 2 + ((Y - 92) / (r * 0.55)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, 24 + ddx, 92, r, r * 0.55))
        if burning_foot:
            L[m] = np.where(v > 0.6, 'β', np.where(v > 0.3, 'γ', 'δ'))[m]
        else:
            L[m] = np.where(v > 0.6, 'w', np.where(v > 0.3, 'v', 'T'))[m]
    return L


def _orbit(L, phase, items, ember):
    for j, (h, rr) in enumerate(items):
        a = math.radians(phase * 90 + j * 140)
        x = 24 + rr * math.cos(a)
        y = h + rr * 0.25 * math.sin(a)
        xi, yi = int(round(x)), int(round(y))
        if 0 < xi < TW_ - 1 and 0 < yi < TH_ - 1:
            if ember:
                L[yi, xi] = 'β'
                L[yi - 1, xi] = 'α'
            else:
                R.blk(L, xi - 1, yi - 1, ['TT', 'yY'])
    return L


AIR_DEBRIS = [(30, 23), (55, 16), (74, 10), (44, 20)]


def tornado_air(k):
    """4-frame loop: a grey-white funnel with streaks winding up it, stones orbiting."""
    return _orbit(_funnel(k, 'air'), k, AIR_DEBRIS, False)


def tornado_ignite(k):
    """3 frames: fire catches at the foot and races up the funnel (0 foot, 1 half, 2 all ablaze)."""
    L = _funnel(k, 'air', fire_from=(66, 36, 0)[k])
    return _orbit(L, k, AIR_DEBRIS, k == 2)


def tornado_fire(k):
    """4-frame loop: the fire tornado - white-hot streaks, deep reds on the shadow side, embers flung
    round it, a smudge of smoke off the top."""
    L = _funnel(k, 'fire')
    _orbit(L, k, [(30, 23), (52, 17), (70, 12), (40, 21), (60, 15)], True)
    for (x, y) in ((10 + k * 3, 1), (32 - k * 2, 1), (20, 0 + k % 2)):
        if 0 <= x < TW_ - 1:
            L[y, x] = 'θ'
            L[y, x + 1] = 'κ'
    return L


# ------------------------------------------------------------------ the fire quake ring (Bixby's format)
RW_, RH_ = 40, 32
RING_ANGLES = (0, 15, 30, 45, 60, 75, 90)      # segment tangent, rows 0..6 (as bixby_quake_ring.png)


def ring_segment(angle_deg, k):
    """40x32 segment: a scorched crack along the tangent with lava in it, and flame tongues standing up
    off it (fire always rises, whatever the tangent). 4-frame flicker."""
    L = blank(RW_, RH_)
    cx, cy = 20, 20
    a = math.radians(angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    half = 17 - 5 * abs(math.sin(a))
    X, Y = centres(RW_, RH_)
    s = (X - cx) * ux + (Y - cy) * uy
    t = -(X - cx) * uy + (Y - cy) * ux
    band = (np.abs(s) <= half) & (np.abs(t) <= 2.6)
    n = pnoise2(8, 71 + k)[:RH_, :RW_]
    L[band] = np.where(np.abs(t[band]) > 1.6, 'θ', np.where(n[band] > 0.5, 'κ', 'η'))
    core = (np.abs(s) <= half - 1) & (np.abs(t) <= 0.9)
    L[core] = np.where(n[core] > 0.55, 'β', 'γ')
    # flame tongues standing up along the crack
    rnd = np.random.RandomState(81 + k)
    for i in range(7):
        ss = -half + 2 + i * (2 * half - 4) / 6.0 + rnd.uniform(-1, 1)
        bx, by = cx + ss * ux, cy + ss * uy
        hgt = rnd.randint(6, 12)
        for j in range(hgt):
            u = j / hgt
            w = max(0, int(round(1.6 * (1 - u))))
            xx = bx + math.sin(u * 3 + k + i) * 1.2
            yy = by - 1 - j
            ramp = 'δγβα' if j < hgt - 2 else 'γδ'
            ch = ramp[min(len(ramp) - 1, int(u * len(ramp)))]
            for dx in range(-w, w + 1):
                xi, yi = int(round(xx + dx)), int(round(yy))
                if 0 <= xi < RW_ and 0 <= yi < RH_:
                    L[yi, xi] = 'α' if (dx == 0 and u < 0.5) else ch
    return L


def ring_sheet():
    """7 rows (tangent 0..90 degrees) x 4 frames, as one grid (row-major)."""
    return [[ring_segment(a, k) for k in range(4)] for a in RING_ANGLES]


# ------------------------------------------------------------------ steam
def steam_puff(k):
    """24x32, 5 frames, pivot (12, 30): a puff forms on the wet floor, rises, spreads, and thins away."""
    L = blank(24, 32)
    X, Y = centres(24, 32)
    cy = 27 - k * 4.5
    r = 3.0 + k * 1.6
    for (dx, dy, rr) in ((0, 0, r), (-r * 0.6, 1.5, r * 0.7), (r * 0.6, 1.2, r * 0.75), (0, -r * 0.5, r * 0.65)):
        m = ((X - 12 - dx) / rr) ** 2 + ((Y - cy - dy) / (rr * 0.85)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, 12 + dx, cy + dy, rr, rr * 0.85))
        ch = np.where(v > 0.75, 'λ', np.where(v > 0.45, 'μ', 'ν'))
        if k >= 3:
            thin = ((X + Y + k).astype(int) % (2 if k == 3 else 3)) == 0
            m &= ~thin
            ch = np.where(ch == 'λ', 'μ', np.where(ch == 'μ', 'ν', 'ξ'))
        L[m] = ch[m]
    return L


FOG_T = 128


def _pnoise_t(size, cell, seed):
    rnd = np.random.RandomState(seed)
    n = size // cell
    g = rnd.rand(n + 1, n + 1)
    g[-1, :] = g[0, :]
    g[:, -1] = g[:, 0]
    ys, xs = np.mgrid[0:size, 0:size]
    fx, fy = xs / cell, ys / cell
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


FOG_FIELD = 0.55 * _pnoise_t(FOG_T, 32, 3) + 0.3 * _pnoise_t(FOG_T, 16, 4) + 0.15 * _pnoise_t(FOG_T, 8, 5)


def fog(density):
    """A seamless 128x128 fog tile (scroll it slowly). density 0 light, 1 medium, 2 'very hard to see'.
    Banded alpha (pixel art, no smooth gradients); the thickest band tops out at ~75 % opacity, so a
    dark figure still shows through and the tells, drawn above it, stay crisp."""
    L = blank(FOG_T, FOG_T)
    f = FOG_FIELD
    if density == 0:
        bands = ((0.62, 'π'), (0.7, 'ρ'))
    elif density == 1:
        bands = ((0.48, 'π'), (0.56, 'ρ'), (0.64, 'σ'))
    else:
        bands = ((0.0, 'π'), (0.36, 'ρ'), (0.46, 'σ'), (0.56, 'τ'), (0.66, 'υ'))
    for th, ch in bands:
        L[f >= th] = ch
    return L


# ------------------------------------------------------------------ the red lunge triangle
TRI = 26


def triangle(k):
    """26x26, pivot (13, 13), pointing RIGHT (the code turns it to aim at the player). 0 pops in small and
    white-hot; 1 settled; 2 pulse; 3 the 'now' flash as he lunges. Red fill (the parry badge's reds),
    a white inner rim and the black keyline, plus a dark halo so it cuts through the palest steam."""
    L = blank(TRI, TRI)
    X, Y = centres(TRI, TRI)
    scale = (0.62, 1.0, 1.08, 1.0)[k]
    cx, cy = 13, 13
    # triangle pointing right: vertices relative to centre
    pts = [(-8.5, -10.0), (10.5, 0.0), (-8.5, 10.0)]
    pts = [(cx + px * scale, cy + py * scale) for px, py in pts]
    m = R.poly_mask(pts, TRI, TRI)
    halo = m.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        halo |= np.roll(np.roll(m, dx, axis=1), dy, axis=0)
    L[halo & ~m] = 'ω'
    fill = np.where(Y < cy, 'φ', 'χ')
    if k == 0:
        fill = np.full(Y.shape, 'ψ')
    if k == 3:
        fill = np.where(Y < cy, 'ψ', 'φ')
    L[m] = fill[m]
    ol = R.outline_pixels(m, prune=True)
    inner = m & ~ol
    inner_ol = R.outline_pixels(inner, prune=True)
    L[inner_ol] = 'W' if k != 0 else 'ψ'
    L[ol] = '#'
    if k == 2:                                   # a pulse ring just outside
        pts2 = [(cx + px * 1.25, cy + py * 1.25) for px, py in [(-8.5, -10.0), (10.5, 0.0), (-8.5, 10.0)]]
        m2 = R.poly_mask(pts2, TRI, TRI)
        o2 = R.outline_pixels(m2, prune=True) & (L == '.')
        L[o2] = 'φ'
    if k == 3:
        for (x, y) in ((2, 2), (23, 3), (2, 23), (24, 22)):
            L[y, x] = 'W'
    return L


# ------------------------------------------------------------------ water: jet, head, trail, extinguish
def water_jet(k):
    """32x12 tile, seamless left-right, pointing RIGHT, 3-frame loop: a hard jet of water."""
    L = blank(32, 12)
    X, Y = centres(32, 12)
    ph = k / 3.0
    wob = np.sin((X / 32.0 + ph) * 2 * math.pi * 2) * 0.8
    d = np.abs(Y - 6 - wob * 0.4)
    L[d <= 4.2] = '%'
    L[d <= 3.2] = '='
    L[d <= 2.0] = '+'
    L[d <= 0.9] = 'l'
    streak = ((X.astype(int) + int(ph * 32)) % 8 < 3) & (d <= 1.2)
    L[streak] = 'W'
    for x in range(0, 32, 5):
        xx = (x + int(ph * 32) + 2) % 32
        L[1 if (x // 5) % 2 else 10, xx] = 'l'
    return L


def water_head(k):
    """24x24, pivot (4, 12): where the jet slams into the player - a fan of spray thrown forward."""
    L = blank(24, 24)
    X, Y = centres(24, 24)
    r = (5, 8, 10)[k]
    core = ((X - 5) / (r * 0.7)) ** 2 + ((Y - 12) / r) ** 2 <= 1
    L[core] = np.where(np.abs(Y[core] - 12) < r * 0.4, 'W', 'l')
    for i in range(9):
        a = math.radians(-60 + i * 15)
        for t in range(3):
            x = 5 + (r + 2 + t * 2) * math.cos(a)
            y = 12 + (r + 2 + t * 2) * math.sin(a)
            if 0 <= int(x) < 24 and 0 <= int(y) < 24:
                L[int(y), int(x)] = ('W', 'l', '+')[t]
    return L


def water_trail(k):
    """24x32, pivot (12, 31): drops and streaks behind a player washed down the ring (3-frame loop)."""
    L = blank(24, 32)
    for i, x in enumerate((4, 9, 13, 18, 21)):
        off = (k * 4 + i * 5) % 12
        top = 2 + off
        ln = 8 + (i * 5) % 7
        for t in range(ln):
            y = top + t
            if y < 30:
                L[y, x] = 'l' if t > ln - 3 else ('+' if t % 3 else '=')
        if top > 3:
            L[top - 2, x] = 'l'
    return L


def extinguish(k):
    """32x32, pivot (16, 20), 4 frames: water hits the flames - a hiss of steam balls out and thins,
    with the last embers dying."""
    L = blank(32, 32)
    X, Y = centres(32, 32)
    rr = (5, 8, 11, 12)[k]
    for (dx, dy, f) in ((0, 0, 1.0), (-rr * 0.55, 2, 0.7), (rr * 0.55, 1, 0.75), (0, -rr * 0.5, 0.7)):
        r = rr * f
        m = ((X - 16 - dx) / r) ** 2 + ((Y - 20 - dy + k * 1.5) / (r * 0.85)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, 16 + dx, 20 + dy - k * 1.5, r, r * 0.85))
        ch = np.where(v > 0.7, 'λ', np.where(v > 0.4, 'μ', 'ν'))
        if k == 3:
            m &= ((X + Y).astype(int) % 2) == 0
        L[m] = ch[m]
    for (x, y) in ((6, 24), (25, 23), (10, 28), (22, 29))[:4 - k]:
        L[y, x] = 'δ'
        L[y - 1, x] = 'γ'
    return L


# ------------------------------------------------------------------ fire on the impaled player, and the column's hit
def flame_overlay(k):
    """24x36, pivot (12, 34) = the player's feet: flames licking up round a player-sized figure (the
    player's sprite is shared; this is drawn over it). 4-frame loop; the middle stays open so he reads."""
    L = blank(24, 36)
    rnd = np.random.RandomState(91 + k)
    for i in range(9):
        side = -1 if i % 2 == 0 else 1
        bx = 12 + side * (4 + (i // 2) % 3 * 2) + rnd.uniform(-1, 1)
        by = 34 - (i // 2) * 6 - rnd.uniform(0, 2)
        hgt = rnd.randint(7, 13)
        for j in range(hgt):
            u = j / hgt
            w = max(0, int(round(1.8 * (1 - u))))
            xx = bx + math.sin(u * 3 + k * 1.3 + i) * 1.4 * (1 if side > 0 else -1)
            yy = by - j
            ramp = 'δγβα'
            ch = ramp[min(3, int(u * 4))]
            for dx in range(-w, w + 1):
                xi, yi = int(round(xx + dx)), int(round(yy))
                if 0 <= xi < 24 and 0 <= yi < 36:
                    L[yi, xi] = 'α' if (dx == 0 and u < 0.35) else ch
    for (x, y) in ((6 + k, 3), (17 - k, 6), (11, 1 + k % 2)):
        L[y, x] = 'β'
    return L


def fire_hit(k):
    """48x32, pivot (24, 16): where Bixby's fire column (bixby_flyby_curtain.png stacked down from off
    screen) lands on the impaled player - a crown of flame bursting out sideways, 3 frames."""
    L = blank(48, 32)
    X, Y = centres(48, 32)
    r = (8, 13, 17)[k]
    core = ((X - 24) / r) ** 2 + ((Y - 16) / (r * 0.55)) ** 2 <= 1
    v = ((X - 24) / r) ** 2 + ((Y - 16) / (r * 0.55)) ** 2
    L[core] = np.where(v[core] < 0.25, 'W', np.where(v[core] < 0.55, 'α', np.where(v[core] < 0.8, 'β', 'γ')))
    for i in range(10):
        a = math.radians(180 + i * 20 + k * 7)
        for t in range(5):
            x = 24 + (r + t * 1.6) * math.cos(a) * 1.2
            y = 16 + (r * 0.55 + t) * math.sin(a) * 0.9
            if 0 <= int(x) < 48 and 0 <= int(y) < 32:
                L[int(y), int(x)] = FIRE_RAMP[max(1, 5 - t)]
    return L
