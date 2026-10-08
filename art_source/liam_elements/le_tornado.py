"""Liam's tornados for attack 3 (v3): spin (air), ignite, fire, out (+ optional form and spew).

Contract (ADDENDUM3 E.4): 48x112 cells, pivot (24, 108) = the base on the floor; the BASE RING (the
core the code hurts with, TORNADO_CORE 48x20 px radii) is drawn on rows 100-111, x 8-40 in every
sheet. The rest of the cell is headroom for tongues, wisps and smoke. Every loop is seamless (all
motion is periodic in the loop time t).

AIR reads as moving air: a see-through funnel (a faint body, denser at its silhouette like any volume
of spray) wound with wispy streaks that sweep round it - the front ones left to right, the back ones,
darker, the other way - their leading edges bright and their tails fraying; wisps peel off the rim and
orbit; ice chips ride round it; spray skirts the foot.

FIRE is the same funnel burning: a twisting column of flame, white-hot in its core and low down,
ribbons of brighter flame winding up it, tongues licking off both flanks and the crown and tearing off
into small flames, embers and smoke; embers spiral up round it; steam boils off the water at its foot.
"""
import math

import numpy as np

import le_rig as R
import le_fire as FI

TAU = math.tau
TW, TH = 48, 112
PIVOT = (24, 108)
Y_TOP, Y_FOOT = 24, 104
R_TOP, R_FOOT = 14.5, 2.0
BASE_C = (24.0, 105.5)          # the base ring: x 8-40, rows 100-111
BASE_RX, BASE_RY = 13.8, 5.4
NB = 3                      # streaks round the funnel
LIGHT_LEFT = True


def blank():
    return R.blank(TW, TH)


def radius(u):
    u = min(1.0, max(0.0, u))
    return R_FOOT + (R_TOP - R_FOOT) * (1 - u) ** 1.3


def axis(u, t, amp=1.0):
    """The funnel snakes: a wave travels down it once a loop; the foot stays pinned."""
    a = (1.0 + 1.7 * math.sin(math.pi * min(1.0, u * 1.1))) * (1 - 0.85 * u ** 6) * amp
    return PIVOT[0] + a * math.sin(TAU * (1.15 * u - t))


# the helix's vertical term: bands wind tighter where the funnel is thin (constant pitch angle)
_G = np.zeros(TH + 1)
for _y in range(1, TH + 1):
    _u = min(1.0, max(0.0, (_y - Y_TOP) / float(Y_FOOT - Y_TOP)))
    _G[_y] = _G[_y - 1] + 1.0 / max(1.6, 0.95 * radius(_u))


def rows(t, amp=1.0, y_from=Y_TOP, y_to=Y_FOOT):
    for y in range(y_from, y_to + 1):
        u = (y - Y_TOP) / float(Y_FOOT - Y_TOP)
        yield y, u, axis(u, t, amp), radius(u)


# ------------------------------------------------------------------ shared pieces
def orbit_xy(cx, cy, rr, phi, tilt=0.26):
    """A point on a horizontal circle round the axis, seen from the front and a little above:
    phi = 0 faces the viewer (lowest on screen), +pi/2 is to the right."""
    return cx + rr * math.sin(phi), cy + rr * tilt * math.cos(phi)


def funnel_mask(t, amp=1.0, grow=0.0, y_from=Y_TOP):
    m = np.zeros((TH, TW), bool)
    S = np.zeros((TH, TW))
    U = np.zeros((TH, TW))
    for y, u, cx, r in rows(t, amp, y_from):
        r2 = r + grow
        for x in range(TW):
            s = (x + 0.5 - cx) / r2
            if abs(s) <= 1.0:
                m[y, x] = True
                S[y, x] = s
                U[y, x] = u
    return m, S, U


def band_value(S, Y, t, back=False, nb=NB):
    th = np.arcsin(np.clip(S, -1, 1))
    if back:
        th = math.pi - th
    return (nb * th / TAU + _G[np.clip(Y, 0, TH)] - t) % 1.0


def _wisps(L, t, fire=False, count=7, mask=None, front=True):
    """Streaks peeling off the rim and orbiting it once a loop, rising as they go; drawn as arcs with a
    bright head and a fading tail. front=True draws the ones on the near side, False the far side (to
    go under the body)."""
    rnd = np.random.RandomState(7 if not fire else 8)
    for i in range(count):
        ph0 = rnd.rand() * TAU
        u0 = 0.08 + 0.75 * rnd.rand()
        rise = 0.12 + 0.1 * rnd.rand()
        ext = 1.12 + 0.3 * rnd.rand()
        ln = 1.0 + 0.8 * rnd.rand()                  # arc length in radians
        uu = u0 - rise * ((t + i / count) % 1.0)
        if uu < 0.02:
            continue
        y = Y_TOP + uu * (Y_FOOT - Y_TOP)
        cx = axis(uu, t)
        rr = radius(uu) * ext + 1.0
        phi = ph0 + TAU * t
        life = (t + i / count) % 1.0
        segs = 12
        for j in range(segs):
            a = phi - ln * j / segs
            is_front = math.cos(a) > -0.15
            if is_front != front:
                continue
            x, yy = orbit_xy(cx, y, rr, a)
            if not fire:
                c = 'W' if j < 2 else ('w' if j < 6 else 'v')
                if life > 0.75 and j > 5:
                    continue
            else:
                c = 'α' if j < 2 else ('β' if j < 5 else ('γ' if j < 8 else 'δ'))
            if not front and mask is not None:
                xi, yi = int(x), int(yy)
                if 0 <= xi < TW and 0 <= yi < TH and mask[yi, xi]:
                    continue
            FI.plot(L, x, yy, c)


def _chips(L, t, kind='ice', count=5, front=True, mask=None):
    """Bits carried round the funnel: ice chips (air) or embers (fire), with a motion streak."""
    rnd = np.random.RandomState(21 if kind == 'ice' else 22)
    for i in range(count):
        ph0 = rnd.rand() * TAU
        u0 = 0.25 + 0.65 * rnd.rand()
        ext = 1.2 + 0.35 * rnd.rand()
        rise = 0.35 if kind == 'ember' else 0.1
        life = (t + i / count) % 1.0
        uu = u0 - rise * life
        if uu < 0.03:
            continue
        y = Y_TOP + uu * (Y_FOOT - Y_TOP)
        cx = axis(uu, t)
        rr = radius(uu) * ext + 1.5
        a = ph0 + TAU * t * (2 if kind == 'ember' else 1)
        is_front = math.cos(a) > 0
        if is_front != front:
            continue
        x, yy = orbit_xy(cx, y, rr, a)
        xt, yt = orbit_xy(cx, y, rr, a - 0.45)
        if kind == 'ice':
            if not front and mask is not None and 0 <= int(x) < TW and 0 <= int(yy) < TH and mask[int(yy), int(x)]:
                continue
            R.line(L, int(xt), int(yt), int(x), int(yy), 'v')
            FI.plot(L, x, yy, 'W'); FI.plot(L, x + 1, yy, 'l'); FI.plot(L, x, yy + 1, 'b')
        else:
            if life > 0.8:
                FI.plot(L, x, yy, 'ε')
                continue
            R.line(L, int(xt), int(yt), int(x), int(yy), 'δ')
            FI.plot(L, x, yy, 'α' if life < 0.4 else 'β')


def _skirt(L, t, kind='spray', front=True, scale=1.0):
    """The base ring (rows 100-111, x 8-40 - the core the code hurts with). Spin: streaks of spray racing
    round it and puffs of spray riding it. Fire: see _base_fire (this draws its steam)."""
    cx, cy = BASE_C
    rx, ry = BASE_RX * scale, BASE_RY * scale
    if kind == 'spray':
        for i in range(3):
            head = TAU * (t + i / 3.0) + i * 0.7
            k = 0.78 + 0.11 * i
            for j in range(34):
                f = j / 33.0
                a = head - f * 2.4
                if (math.cos(a) > 0) != front:
                    continue
                x = cx + rx * k * math.sin(a)
                y = cy + ry * k * math.cos(a)
                if f > 0.6 and j % 2:
                    continue
                FI.plot(L, x, y, 'W' if f < 0.18 else ('w' if f < 0.55 else 'v'))
        n = 7
        for i in range(n):
            a = TAU * (i / float(n) + t)
            if (math.cos(a) > 0) != front:
                continue
            x = cx + rx * 0.9 * math.sin(a)
            y = cy + ry * 0.9 * math.cos(a) - 1.0
            FI.puff(L, x, y, (1.6 + 0.7 * ((i * 3) % 3) / 2.0) * scale, ramp=('W', 'l', 'v'), seed=i)
    else:
        n = 6
        for i in range(n):
            a = TAU * (i / float(n) + t * 0.5)
            if (math.cos(a) > 0) != front:
                continue
            life = (t + i / float(n)) % 1.0
            x = cx + rx * 0.95 * math.sin(a)
            y = cy + ry * 0.95 * math.cos(a) - 1.5 - life * 7
            FI.puff(L, x, y, (1.8 + 1.8 * life) * scale, ramp=FI.STEAM, dissolve=max(0.0, life - 0.45) * 1.7,
                    seed=i)


def clip_base(L):
    """Keep the base ring's rows (100-111) inside x 8-40, the core the code hurts with."""
    L[100:112, :8] = '.'
    L[100:112, 41:] = '.'
    return L


def _base_fire(L, t, front=True, power=1.0, scale=1.0):
    """The burning base ring: tongues standing on the ellipse, leaning out, on staggered clocks
    (front=False draws the far half, before the column)."""
    cx, cy = BASE_C
    rx, ry = BASE_RX * scale, BASE_RY * scale
    fd = FI.Field(TW, TH)
    emb = []
    n = 12
    for i in range(n):
        a = TAU * i / float(n) + 0.3
        if (math.cos(a) > 0) != front:
            continue
        x = cx + rx * 0.9 * math.sin(a)
        y = cy + ry * 0.9 * math.cos(a)
        H = (4.0 + 5.0 * power) * (0.75 + 0.5 * ((i * 7) % 5) / 4.0)
        FI.tongue(fd, x, y, (t + i * 0.19) % 1.0, H, 1.3 + 0.6 * power, seed=200 + i * 1.3,
                  up=(math.sin(a) * 0.45, -1.0), embers=emb, ember_every=3, temp=0.75, anchor=False)
    fd.render(L, fill=False)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)


TILT = 0.3
N_LINES = 12


def surf(u, a, t, rs=1.0, amp=1.0):
    """The screen point on the funnel's surface at height u, angle a (0 faces the viewer)."""
    u = min(1.0, max(0.0, u))
    y = Y_TOP + u * (Y_FOOT - Y_TOP)
    cx, r = axis(u, t, amp), radius(u) * rs
    return cx + r * math.sin(a), y + r * TILT * math.cos(a)


def spiral_line(L, t, u0, a_head, length, climb, front=True, ramp=('W', 'W', 'w', 'v'),
                back_ramp=('ν', 'ν', 'ξ', 'ξ'), rs=1.0, thick=False, amp=1.0, y_from=Y_TOP, shade='v'):
    """A streak on the funnel's surface: its head at angle a_head, height u0, trailing back `length`
    radians and dropping `climb` (in u) along it - the air climbs as it goes round. Near side bright
    (with a shade texel under it when thick), far side faint."""
    n = int(length / 0.02)
    for i in range(n):
        f = i / float(n)
        a = a_head - length * f
        u = u0 + climb * f
        if u < 0 or u > 1:
            continue
        isf = math.cos(a) > 0
        if isf != front:
            continue
        x, y = surf(u, a, t, rs, amp)
        if y < y_from:
            continue
        rp = ramp if front else back_ramp
        c = rp[min(3, int(f * 4))]
        if front and LIGHT_LEFT and math.sin(a) > 0.6 and c == 'W':
            c = 'w'
        FI.plot(L, x, y, c)
        if front and thick and f < 0.6:
            if L[min(TH - 1, int(y) + 1), min(TW - 1, max(0, int(x)))] in ('.', 'ξ', 'ν', 'μ'):
                FI.plot(L, x, y + 1, shade)


def veil(L, t, amp=1.0, y_from=Y_TOP, dense=1.0):
    """The funnel's body: see-through, denser toward its silhouette (a volume of spray seen edge-on)."""
    m, S, U = funnel_mask(t, amp, y_from=y_from)
    X = np.arange(TW)[None, :].repeat(TH, 0)
    Y = np.arange(TH)[:, None].repeat(TW, 1)
    nz = FI.hash01(X, Y, 3)
    edge = np.abs(S)
    out = np.full((TH, TW), '.', dtype='<U1')
    if dense >= 1.0:
        out[m & (edge > 0.8)] = 'μ'
        out[m & (edge <= 0.8) & (edge > 0.45)] = 'ν'
        out[m & (edge <= 0.45)] = 'ξ'
    else:
        out[m & (edge > 0.8)] = 'ν'
        out[m & (edge <= 0.8)] = 'ξ'
        out[m & (edge <= 0.45) & (nz < 0.5)] = '.'
    sel = (out != '.') & (L == '.')
    L[sel] = out[sel]
    return m


def edges(L, t, amp=1.0, y_from=Y_TOP):
    """The silhouette: long dashes flowing up both flanks (lit left, shadowed right)."""
    for side in (-1, 1):
        for y in range(max(Y_TOP, y_from), Y_FOOT):
            u = (y - Y_TOP) / float(Y_FOOT - Y_TOP)
            cx, r = axis(u, t, amp), radius(u)
            x = cx + side * (r - 0.3)
            dash = (y / 7.0 + t * 2 + (0.5 if side > 0 else 0)) % 1.0
            if dash < 0.72:
                if side < 0:
                    c = 'W' if dash < 0.18 else 'w'
                else:
                    c = 'v' if dash < 0.18 else 'T'
                FI.plot(L, x, y, c)


def _lines(t, n_lines):
    for i in range(n_lines):
        ph = i / float(n_lines)
        u0 = ((ph + t * 0.35) % 1.0) * 0.95
        a_head = TAU * (ph * 2.3 + t)
        yield u0, a_head


def _air_body(L, t, amp=1.0, y_from=Y_TOP, alpha_body=True, n_lines=N_LINES):
    m, S, U = funnel_mask(t, amp, y_from=y_from)
    for u0, a_head in _lines(t, n_lines):
        spiral_line(L, t, u0, a_head, 4.6, 0.12, front=False, amp=amp, y_from=y_from, rs=1.02)
    if alpha_body:
        veil(L, t, amp, y_from, dense=0.5)
    for u0, a_head in _lines(t, n_lines):
        spiral_line(L, t, u0, a_head, 4.6, 0.12, front=True, thick=u0 < 0.7, amp=amp, y_from=y_from, rs=1.02)
    return m


def orbit_arcs(L, t, front=True, count=3, mask=None, amp=1.0, ramp=('W', 'W', 'w', 'v')):
    """Long wind arcs whipping round outside the funnel (one lap a loop, two at the rope)."""
    for i in range(count):
        u = 0.22 + 0.6 * i / max(1, count - 1)
        rs = 1.35 + 0.15 * (i % 2)
        a_head = TAU * (t * (1 + (i == count - 1)) + i * 0.37)
        n = 70
        for j in range(n):
            f = j / float(n)
            a = a_head - 2.6 * f
            if (math.cos(a) > 0) != front:
                continue
            x, y = surf(u + 0.04 * f, a, t, rs, amp)
            c = ramp[min(3, int(f * 4))]
            if not front:
                c = 'ν' if f < 0.5 else 'ξ'
                if mask is not None and 0 <= int(x) < TW and 0 <= int(y) < TH and mask[int(y), int(x)]:
                    continue
            if f > 0.7 and j % 2:
                continue
            FI.plot(L, x, y, c)
            if front and f < 0.45:
                FI.plot(L, x, y + 1, 'w' if f < 0.2 else 'v')


def _crown_air(L, t, amp=1.0, u_top=0.0, hooks=4, scale=1.0):
    """The open top (at height u_top): the near rim of the mouth, and hooks of air curling off it as it
    spins."""
    for i in range(90):
        a = -math.pi / 2 + math.pi * i / 89
        x, y = surf(u_top, a, t, 1.0, amp)
        FI.plot(L, x, y, 'W' if math.sin(a) < 0.35 else 'w')
    for i in range(hooks):
        a0 = TAU * (t + i / float(hooks))
        if math.cos(a0) < -0.3:
            continue
        x0, y0 = surf(u_top, a0, t, 1.0, amp)
        side = 1 if math.sin(a0) >= 0 else -1
        for j in range(14):
            f = j / 13.0
            ang = f * 4.2
            rr = (1.0 + f * 3.2) * scale
            x = x0 + side * (math.sin(ang) * rr + f * 3.0 * scale)
            y = y0 - 1 - f * 4.5 * scale - math.cos(ang) * rr * 0.6
            c = 'W' if f < 0.3 else ('w' if f < 0.65 else 'v')
            if f > 0.7 and j % 2:
                continue
            FI.plot(L, x, y, c)


def tornado_air(k, n=8):
    """n-frame loop: moving air."""
    t = k / n
    L = blank()
    m, _, _ = funnel_mask(t)
    _skirt(L, t, 'spray', front=False)
    orbit_arcs(L, t, front=False, mask=m)
    _chips(L, t, 'ice', front=False, mask=m)
    _air_body(L, t)
    _crown_air(L, t)
    orbit_arcs(L, t, front=True)
    _chips(L, t, 'ice', front=True)
    _skirt(L, t, 'spray', front=True)
    return clip_base(L)


def tornado_form(k, n=6):
    """n frames, once: the gust lands and a whirl of spray spins up off the ice, then the funnel climbs
    out of it, widening as it goes, until it stands full height (then tornado_air loops)."""
    t = k / 8.0
    grow = [0.0, 0.2, 0.42, 0.66, 0.88, 1.0][k] if n == 6 else k / (n - 1.0)
    L = blank()
    sc = 0.45 + 0.55 * min(1.0, grow * 1.4)
    _skirt(L, t, 'spray', front=False, scale=sc)
    if grow > 0:
        y_from = int(Y_FOOT - grow * (Y_FOOT - Y_TOP))
        u_top = (y_from - Y_TOP) / float(Y_FOOT - Y_TOP)
        part = blank()
        _air_body(part, t, amp=0.5 + 0.5 * grow, y_from=y_from, n_lines=int(5 + 7 * grow))
        R.composite(L, part)
        _crown_air(L, t, amp=0.5 + 0.5 * grow, u_top=u_top, hooks=3 if grow < 1 else 4, scale=0.7 + 0.3 * grow)
        if grow >= 0.66:
            orbit_arcs(L, t, front=True, count=1 if grow < 1 else 3)
    else:
        # the gust hitting the floor: a flat whirl of streaks round the foot
        fx, fy = PIVOT[0], Y_FOOT - 1
        for ring, rr in enumerate((10.0, 7.0, 4.0)):
            for j in range(40):
                f = j / 39.0
                a = TAU * t + ring * 1.9 - f * 3.4
                x, y = orbit_xy(fx, fy - ring * 1.5, rr, a, tilt=0.34)
                c = 'W' if f < 0.15 else ('w' if f < 0.5 else 'v')
                if f > 0.7 and j % 2:
                    continue
                FI.plot(L, x, y, c)
    _chips(L, t, 'ice', front=True, count=int(2 + 3 * grow))
    _skirt(L, t, 'spray', front=True, scale=sc)
    return clip_base(L)


# ------------------------------------------------------------------ FIRE
NB_FIRE = 2
SLIM = 0.86


def _ripple(y, t, side):
    """The flanks of the burning column ripple upward like flame (periodic in t)."""
    ph = 0.37 if side > 0 else 0.0
    return 0.9 * math.sin(TAU * (y / 9.0 + 2 * t + ph)) + 0.6 * math.sin(TAU * (y / 4.6 + 3 * t + ph * 2))


def fire_mask(t, amp=1.0, y_from=Y_TOP, slim=SLIM, pinch=None):
    """The burning column from y_from down: the funnel a little slimmer, its flanks rippling upward like
    flame and its top edge ragged. pinch=(y, depth) narrows it to a waist at y (burning through)."""
    m = np.zeros((TH, TW), bool)
    S = np.zeros((TH, TW))
    U = np.zeros((TH, TW))
    RR = np.ones((TH, TW))
    for y, u, cx, r in rows(t, amp, y_from):
        r2 = max(1.2, r * slim)
        if pinch is not None:
            r2 *= 1.0 - pinch[1] * math.exp(-((y - pinch[0]) / 4.0) ** 2)
        left = cx - r2 - _ripple(y, t, -1) * (0.4 + 0.6 * (1 - u))
        right = cx + r2 + _ripple(y, t, 1) * (0.4 + 0.6 * (1 - u))
        for x in range(TW):
            xc = x + 0.5
            if y < y_from + 4 and y < y_from + 1.5 + 1.5 * math.sin(TAU * (x / 7.0 - 2 * t)) + 1.2 * math.sin(
                    TAU * (x / 3.7 + 3 * t)):
                continue                                   # the top edge is ragged too
            if left <= xc <= right:
                m[y, x] = True
                S[y, x] = max(-1.0, min(1.0, (xc - cx) / r2))
                U[y, x] = u
                RR[y, x] = r2
    return m, S, U, RR


def fire_heat(S, U, RR, t, heat_scale=1.0, spin=2):
    """The column's own heat: a hot core, hotter low down, hot ribbons winding up it (drawn on the near
    surface with the same tilt as the air streaks), the right-hand flank a shade cooler."""
    Y = np.arange(TH)[:, None].repeat(TW, 1) + 0.5
    a = np.arcsin(np.clip(S, -1, 1))
    yw = Y - RR * TILT * np.cos(a)
    g = np.interp(yw, np.arange(TH + 1), _G)
    h = (NB_FIRE * a / TAU + g * 0.55 - spin * t * 0.5) % 1.0
    ribbon = np.where(h < 0.18, 0.3, np.where(h < 0.3, 0.14, np.where((h > 0.56) & (h < 0.72), -0.1, 0.0)))
    core = np.clip(1 - S ** 2, 0, 1) ** 1.5
    heat = 0.14 + 0.3 * core + 0.16 * U + ribbon - 0.14 * np.clip(S - 0.3, 0, 1)
    heat -= 0.18 * np.clip((0.07 - U) / 0.07, 0, 1)            # the crown cools into its tongues
    return np.clip(heat * heat_scale, 0, 1)


def _rim_tongues(fd, t, emb, y_from=Y_TOP, scale=1.0, amp=1.0, seed=0, slim=SLIM):
    """Tongues licking off both flanks (outward, curling up), bigger toward the crown, at irregular
    spacing and sizes, each on its own clock; and big tongues up off the crown."""
    rnd = np.random.RandomState(301 + seed)
    for side in (-1, 1):
        y = y_from + (5 if side < 0 else 9)
        while y < Y_FOOT - 7:
            sz = 0.7 + 0.55 * rnd.rand()
            u = (y - Y_TOP) / float(Y_FOOT - Y_TOP)
            cx, r = axis(u, t, amp), max(1.2, radius(u) * slim)
            edge = cx + side * (r + _ripple(y, t, side) * (0.4 + 0.6 * (1 - u)) - 0.6)
            H = (5.0 + 8.0 * (1 - u)) * scale * sz
            r0 = (1.7 + 1.3 * (1 - u)) * scale * (0.8 + 0.2 * sz)
            FI.tongue(fd, edge, y, t, H, r0, seed=seed + y * 0.37 + side * 11, rate=5,
                      up=(side * 0.85, -0.53), embers=emb, ember_every=4, sway=0.7, temp=0.6, anchor=False,
                      curl=H * 0.55)
            y += int(7 + 7 * rnd.rand() + 4 * (1 - u))
    if y_from <= Y_TOP + 2:
        cx, r = axis(0.0, t, amp), R_TOP * slim
        hs = (0.75, 1.0, 0.65, 0.9, 1.0, 0.7)
        for i, fx in enumerate(np.linspace(-r + 2.0, r - 2.0, 6)):
            H = (9 + 9 * hs[i] * (1 - 0.5 * abs(fx) / r)) * scale
            FI.tongue(fd, cx + fx, Y_TOP + 4.0, t, H, (2.2 + 0.8 * (1 - abs(fx) / r)) * scale,
                      seed=seed + 50 + i * 2.3, rate=6, up=(fx / r * 0.5, -1.0), embers=emb, ember_every=2,
                      temp=0.62, anchor=False, curl=H * 0.6)


def _smoke_crown(L, t, dense=1.0, cx=None, top=Y_TOP):
    """Dark smoke boiling off the crown, rolling up, drifting and dissolving (under the flames)."""
    if cx is None:
        cx = axis(0.0, t)
    for i in range(6):
        life = (t + i / 6.0) % 1.0
        x = cx + ((i * 7) % 6 - 2.5) * 5.5 + math.sin(TAU * (life + i * 0.3)) * 2.5 + life * 3
        y = top - 3 - life * 15
        rad = (2.6 + 3.0 * life) * dense
        FI.puff(L, x, y, rad, ramp=FI.SMOKE_DARK, dissolve=max(0.0, life - 0.45) * 1.6, seed=40 + i)


def tornado_fire(k, n=8, heat_scale=1.0, amp=1.0, flare=0.0):
    """n-frame loop: the fire tornado."""
    t = k / n
    L = blank()
    m, S, U, RR = fire_mask(t, amp)
    _smoke_crown(L, t)
    _skirt(L, t, 'steam', front=False)
    _base_fire(L, t, front=False)
    fd = FI.Field(TW, TH)
    emb = []
    _rim_tongues(fd, t, emb, amp=amp, scale=1.0 + flare)
    fd.render(L, base_inside=m, base_heat=fire_heat(S, U, RR, t, heat_scale + flare * 0.5))
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_DARK)
    _chips(L, t, 'ember', front=True)
    _base_fire(L, t, front=True)
    _skirt(L, t, 'steam', front=True)
    return clip_base(L)


def tornado_ignite(k, n=6):
    """n frames, once: 0 a spark (from Liam's staff) is sucked into the foot; 1-4 the foot catches and
    fire races up the funnel - a white-hot burning front eating the air, tongues licking up past it -
    5 the crown catches and the whole column flares with a burst of sparks (then tornado_fire loops)."""
    t = k / 8.0
    L = blank()
    prog = [0.0, 0.16, 0.4, 0.66, 0.9, 1.0][k] if n == 6 else k / (n - 1.0)
    fx, fy = PIVOT[0], Y_FOOT
    if k == 0:
        L = tornado_air(0)
        # the spark: a bright point curling in to the foot, a flame catching there
        for j in range(12):
            a = 0.9 + j * 0.42
            x = fx + 3 + math.cos(a) * (1.5 + j * 1.1)
            y = fy - 5 - j * 0.55 + math.sin(a) * 1.3
            FI.plot(L, x, y, 'W' if j < 1 else ('α' if j < 3 else ('β' if j < 6 else ('γ' if j < 9 else 'δ'))))
        fd = FI.Field(TW, TH)
        FI.tongue(fd, fx, fy - 1, 0.35, 5, 1.7, seed=3)
        fd.render(L)
        return L
    front_y = int(Y_FOOT - prog * (Y_FOOT - Y_TOP + 6))
    if prog < 1.0:
        # the air above the burning front, still spinning
        air = blank()
        _air_body(air, t)
        air[front_y + 2:] = '.'
        _crown_air(air, t)
        R.composite(L, air)
    else:
        _smoke_crown(L, t, dense=1.25)
    if k >= 2:
        _base_fire(L, t, front=False, power=min(1.0, 0.3 + 0.25 * (k - 1)))
    m, S, U, RR = fire_mask(t, 1.0, y_from=max(Y_TOP, front_y))
    heat = fire_heat(S, U, RR, t, 1.0 + (0.2 if k == n - 1 else 0.0))
    Y = np.arange(TH)[:, None].repeat(TW, 1)
    if prog < 0.9:
        heat = np.where(m & (Y < front_y + 5), np.maximum(heat, 0.9 - (Y - front_y) * 0.06), heat)   # the white-hot front
    fd = FI.Field(TW, TH)
    emb = []
    _rim_tongues(fd, t, emb, y_from=(Y_TOP if prog >= 0.9 else max(Y_TOP, front_y)),
                 scale=1.0 + (0.3 if k == n - 1 else 0.0))
    if prog < 1.0:
        uu = (front_y - Y_TOP) / float(Y_FOOT - Y_TOP)
        cx, r = axis(uu, t), max(1.5, radius(uu) * SLIM)
        cnt = max(2, int(r / 2.4))
        for i, dx in enumerate(np.linspace(-r + 1.2, r - 1.2, cnt)):
            H = 8 + 7 * (1 - abs(dx) / max(r, 1)) + (i % 2) * 3
            FI.tongue(fd, cx + dx, front_y + 3, (t * 2 + i * 0.29) % 1.0, H, 2.1, seed=60 + i * 1.7 + k,
                      rate=6, embers=emb, temp=0.8, anchor=False, up=(dx / max(r, 1) * 0.35, -1.0))
    fd.render(L, base_inside=m, base_heat=heat)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    if k == n - 1:
        # the whoosh: sparks thrown off the crown in a ring
        cx = axis(0.0, t)
        for i in range(16):
            a = TAU * i / 16
            x, y = cx + math.cos(a) * (R_TOP + 5), Y_TOP - 2 + math.sin(a) * 6
            FI.plot(L, x, y, 'α' if i % 2 else 'β')
            FI.plot(L, x - math.cos(a), y - math.sin(a) * 0.4, 'γ')
    _chips(L, t, 'ember', front=True, count=1 + k)
    if k >= 2:
        _base_fire(L, t, front=True, power=min(1.0, 0.3 + 0.25 * (k - 1)))
    _skirt(L, t, 'steam' if k >= 2 else 'spray', front=True, scale=0.7 + 0.08 * k)
    return clip_base(L)


def _floor_ring(fd, emb, cx, cy, rad, t, power, seed=0, half='front'):
    """Half a flat ring of flame racing out along the floor (flattened like the floor, 0.36): tongues
    standing on the ellipse, leaning outward. half='back' is the far side (drawn before the column)."""
    n = max(8, int(rad * 1.3))
    for i in range(n):
        a = TAU * i / n
        if (math.sin(a) >= 0) != (half == 'front'):
            continue
        x, y = cx + rad * math.cos(a), cy + rad * 0.36 * math.sin(a)
        H = (3 + 7 * power) * (0.7 + 0.6 * ((i * 7) % 5) / 4.0)
        FI.tongue(fd, x, y, (t + i * 0.23) % 1.0, H, 1.1 + 0.8 * power, seed=seed + i * 1.3,
                  up=(math.cos(a) * 0.55, -1.0), embers=emb, ember_every=3, temp=0.75, anchor=False)


def _rocks(L, cx, cy, u, spread=1.0, seed=0):
    """Chunks of floor thrown up and out on arcs (u 0..1 across their flight)."""
    rnd = np.random.RandomState(seed)
    for i in range(7):
        a = TAU * rnd.rand()
        v = 10 + 8 * rnd.rand()
        x = cx + math.cos(a) * (6 + 16 * u) * spread
        y = cy + math.sin(a) * (6 + 16 * u) * 0.36 * spread - v * u * (1 - u) * 2.2
        FI.plot(L, x, y, 'ι'); FI.plot(L, x + 1, y, 'η'); FI.plot(L, x, y + 1, 'κ'); FI.plot(L, x + 1, y + 1, 'θ')
        FI.plot(L, x - 1, y, 'θ'); FI.plot(L, x, y - 1, 'θ')


def tornado_spew(k, n=5):
    """n frames, once every 1.5 s, drawn INSTEAD of the loop: 0 the column draws in and flares white at
    the foot; 1 SPEW - a flat ring of flame bursts out of the foot along the floor, chunks of floor
    thrown; 2-3 the ring races out to the column's edge (radius 20 texels = 60 px, where the quake-ring
    segments take over), rocks landing; 4 settles back into the loop."""
    t = k / 8.0
    fx, fy = PIVOT[0], Y_FOOT
    if k == 0:
        L = blank()
        _base_fire(L, t, front=False, power=1.4)
        R.composite(L, tornado_fire(0, 8, heat_scale=1.2, amp=0.6))
        _base_fire(L, t, front=True, power=1.4)
        return L
    if k >= 4:
        return tornado_fire(k % 8, 8)
    rad = [0, 7.0, 13.5, 20.0][k]
    power = [0, 1.0, 0.75, 0.45][k]
    L = blank()
    fd = FI.Field(TW, TH)
    emb = []
    _floor_ring(fd, emb, fx, fy - 0.5, rad, t, power, seed=70, half='back')
    fd.render(L, fill=False)
    R.composite(L, tornado_fire(k % 8, 8, heat_scale=1.1 if k == 1 else 1.0, flare=0.2 if k == 1 else 0.0))
    fd = FI.Field(TW, TH)
    _floor_ring(fd, emb, fx, fy - 0.5, rad, t, power, seed=70, half='front')
    fd.render(L, fill=False)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    _rocks(L, fx, fy - 1, [0, 0.3, 0.65, 0.95][k], seed=5)
    return L


def tornado_die(k, n=6):
    """n frames, once (liam_tornado_out, burnout_time): 0 it gutters (tongues shrink, the column and its
    burning base dim); 1 it thins and burns through at the waist; 2 the top, cooling, rises away as smoke
    while the base ring burns low; 3 the water takes the ring with a hiss of steam; 4-5 steam, smoke and
    the last embers go out."""
    t = k / 8.0
    fx, fy = PIVOT[0], Y_FOOT
    L = blank()
    if k <= 1:
        slim = SLIM * (0.9 - 0.18 * k)
        m, S, U, RR = fire_mask(t, 1.2, slim=slim, pinch=(Y_TOP + 44, 0.85) if k == 1 else None)
        _smoke_crown(L, t, dense=1.1 + 0.3 * k)
        _base_fire(L, t, front=False, power=0.75 - 0.25 * k)
        fd = FI.Field(TW, TH)
        emb = []
        _rim_tongues(fd, t, emb, scale=0.75 - 0.25 * k, amp=1.2, slim=slim)
        fd.render(L, base_inside=m, base_heat=fire_heat(S, U, RR, t, 0.82 - 0.14 * k))
        FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
        _base_fire(L, t, front=True, power=0.75 - 0.25 * k)
        _skirt(L, t, 'steam', front=True)
        return L
    u = (k - 2) / float(n - 3)
    # the torn-off top rising away as smoke, the last of its fire guttering inside it
    for i in range(6):
        y = Y_TOP + 6 + i * 7 - u * 18 - (4 if k == 2 else 0)
        rad = 3.4 + (5 - i) * 0.45 + u * 2.2
        FI.puff(L, fx + math.sin(i * 1.7 + u * 3) * 3, y, rad, ramp=FI.SMOKE_DARK,
                dissolve=min(1.0, u * 1.1 + i * 0.04), seed=80 + i)
    if k == 2:
        fd = FI.Field(TW, TH)
        emb = []
        for i, (dx, yy) in enumerate(((-5, 44), (2, 40), (6, 47), (-1, 50))):
            FI.tongue(fd, fx + dx, Y_TOP + yy, (t + i * 0.3) % 1.0, 6, 1.6, seed=120 + i, embers=emb, temp=0.35,
                      anchor=False)
        fd.render(L)
        FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    # the base ring burning low, then out
    p = max(0.0, 0.45 - u * 0.9)
    if p > 0:
        _base_fire(L, t, front=False, power=p)
        _base_fire(L, t, front=True, power=p)
    # embers winking out on the ring
    for i in range(6):
        a = TAU * i / 6.0 + 0.4
        life = u * 1.5 - i * 0.08
        if 0 < life < 1:
            x = BASE_C[0] + BASE_RX * 0.8 * math.sin(a)
            y = BASE_C[1] + BASE_RY * 0.8 * math.cos(a) - life * 4
            FI.plot(L, x, y, 'β' if life < 0.3 else ('δ' if life < 0.6 else ('ε' if life < 0.85 else 'ϖ')))
    # the hiss of steam as the water takes it
    for i in range(5):
        FI.puff(L, fx - 11 + i * 5.5, fy - 1 - u * 12 - (i % 2) * 3, 2.4 + u * 3.6, ramp=FI.STEAM,
                dissolve=max(0.0, u - 0.35) * 1.4, seed=95 + i)
    return clip_base(L)
