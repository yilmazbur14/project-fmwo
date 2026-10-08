"""Attacks 3-4 FX, v3 ("see and feel the elements"). Every loop is seamless; extra frames everywhere.

  FIRE lives and dies at its edges (le_fire): outlined tongues in Bixby's approved colours that neck,
  tear off and cool on the way up (a small flame, a red blob, a dark ember, a curl of smoke).
  WIND is moving air (le_tornado): see-through funnels wound with streaks, wisps whipping round.
  WATER sprays, drips and slams; STEAM billows, drifts and dissolves from its edges.

Tornados live in le_tornado.py and are re-exported here. Sizes, pivots, counts and times are in
DESIGN (bottom) - the build writes them to anchors.json.
"""
import math

import numpy as np

import le_rig as R
import le_a34 as A          # palettes (fire, rock, steam, fog, tell) + the v1 pieces kept for reference
import le_fire as FI
import le_tornado as TN
from le_tornado import tornado_air, tornado_form, tornado_ignite, tornado_fire, tornado_spew, tornado_die

TAU = math.tau
FIRE_RAMP = A.FIRE_RAMP
plot = FI.plot
blank = R.blank

# translucent water (the ball round the washed-away player, and spray), dense -> thin
WATER_A = {'ϙ': (159, 220, 247, 200), 'ϛ': (111, 179, 232, 165), 'ϝ': (69, 150, 224, 130)}
R.PAL.update(WATER_A)


# ================================================================== the fire quake ring (Bixby's format)
RW, RH = 40, 32
RING_PIVOT = (20, 16)                     # the crack's centre on the floor (BixbyCombinedArtLayout)
RING_ROW_DEG = (0.0, 13.65, 28.05, 45.0, 61.95, 76.35, 90.0)     # mid-bucket screen tangents
RING_GROUND = [(15, -5, 5), (19, -9, 8), (20, -8, 8), (20, -12, 10), (17, -14, 13), (15, -16, 15), (13, -15, 14)]


def _plates(L, row, seed=3):
    """The broken floor either side of the crack: plates (nearest-seed cells) heaved up, lit from the
    upper left, dark gaps between them; returns the along/across coordinate arrays."""
    ang = math.radians(RING_ROW_DEG[row])
    ux, uy = math.cos(ang), -math.sin(ang)             # rows 1-5 rise to the right
    X, Y = R.centres(RW, RH)
    cx, cy = RING_PIVOT
    s = (X - cx) * ux + (Y - cy) * uy
    q = -(X - cx) * uy + (Y - cy) * ux                  # across (screen)
    hw, top, bot = RING_GROUND[row]
    half_len = hw / max(0.35, abs(ux)) if row < 6 else abs(top)
    half_len = min(half_len, 19.0)
    thick = 4.2 + 5.5 * math.sin(ang) ** 1.3           # the band is flattened like the floor
    rnd = np.random.RandomState(seed + row * 17)
    seeds = []
    for i in range(14):
        ss = -half_len + (2 * half_len) * (i + rnd.rand() * 0.8) / 14.0
        qq = (rnd.rand() - 0.5) * 2 * thick
        seeds.append((cx + ss * ux - qq * uy, cy + ss * uy + qq * ux, rnd.rand()))
    band = (np.abs(s) <= half_len - 0.5 * np.abs(q) / max(thick, 1) * 3) & (np.abs(q) <= thick + 0.8)
    edge_n = FI.hash01(np.floor(X), np.floor(Y), row + 5)
    band &= ~((np.abs(q) > thick - 0.8) & (edge_n < 0.45))
    band &= ~((np.abs(s) > half_len - 2.5) & (edge_n < 0.5))
    d1 = np.full(X.shape, 1e9)
    d2 = np.full(X.shape, 1e9)
    idx = np.zeros(X.shape, int)
    for i, (sx, sy, _) in enumerate(seeds):
        d = (X - sx) ** 2 + (Y - sy) ** 2
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        idx = np.where(closer, i, idx)
        d1 = np.where(closer, d, d1)
    gap = (np.sqrt(d2) - np.sqrt(d1)) < 0.9
    tone = np.array([sd[2] for sd in seeds])[idx]
    col = np.where(tone > 0.66, 'ι', np.where(tone > 0.3, 'η', 'κ'))
    # the lip of each plate facing the crack is its dark side (heaved up)
    lip = (np.abs(q) < 2.6) & (np.abs(q) >= 1.3)
    col = np.where(lip, 'θ', col)
    col = np.where(gap, 'θ', col)
    L[band] = col[band]
    return s, q, half_len, thick, band


def ring_segment(row, k, n=8):
    """40x32, pivot (20, 16) on the crack's centre line at floor level (BixbyCombinedArtLayout's ring
    contract), rows 1-5 rising to the right. The floor splits along the ring, lava glows in the crack,
    and flame tongues stand up off it (fire always rises, whatever the tangent), tearing off into embers
    and smoke on staggered clocks; where the lava meets the water a puff of steam hisses up."""
    L = blank(RW, RH)
    t = k / float(n)
    s, q, half_len, thick, band = _plates(L, row)
    # the crack: a jagged glowing line
    wob = 0.6 * np.sin(s * 1.3 + 1.7) + 0.4 * np.sin(s * 2.9)
    d = np.abs(q - wob)
    crack = band & (d < 1.4) & (np.abs(s) < half_len - 1)
    glow = np.sin(s * 0.8 - TAU * t * 2) > 0.3
    L[crack] = np.where(d[crack] < 0.6, np.where(glow[crack], 'α', 'β'), np.where(glow[crack], 'γ', 'δ'))
    # flames
    ang = math.radians(RING_ROW_DEG[row])
    ux, uy = math.cos(ang), -math.sin(ang)
    fd = FI.Field(RW, RH)
    emb = []
    cx, cy = RING_PIVOT
    # one main tongue per segment (segments stand 48 px apart, so the ring reads as a line of flames with
    # the broken floor between them), and two low licks either side on their own clocks
    if row < 4:
        spots = ((0.0, 13.0, 2.4), (-0.55, 5.0, 1.4), (0.55, 5.5, 1.4))
    elif row < 6:
        spots = ((0.05, 10.0, 2.2), (-0.55, 4.5, 1.3), (0.6, 4.0, 1.3))
    else:
        spots = ((0.0, 9.5, 2.2), (0.55, 4.0, 1.2))
    for i, (f, H, r0) in enumerate(spots):
        ss = f * (half_len - 2)
        bx, by = cx + ss * ux, cy + ss * uy
        FI.tongue(fd, bx, by, (t + i * 0.37) % 1.0, H, r0, seed=row * 5 + i * 1.9, rate=7,
                  embers=emb, ember_every=2, temp=0.72)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    # steam where the lava meets the water, one end then the other
    end = 1 if k < n // 2 else -1
    life = (t * 2) % 1.0
    ex, ey = cx + end * (half_len - 1) * ux, cy + end * (half_len - 1) * uy
    FI.puff(L, ex, ey - 2 - life * 6, 1.6 + life * 2.2, ramp=FI.STEAM, dissolve=max(0.0, life - 0.4) * 1.6, seed=row)
    return L


def ring_dying(row, k, n=8):
    """The optional dying rows (played once over quake_die_time when the ring reaches its max radius):
    the tongues shrink and tear off into embers and smoke, the lava in the crack cools from yellow to
    red to dark, steam hisses off it, and the broken floor is left."""
    L = blank(RW, RH)
    u = k / float(n - 1)
    t = k / 8.0
    s, q, half_len, thick, band = _plates(L, row)
    wob = 0.6 * np.sin(s * 1.3 + 1.7) + 0.4 * np.sin(s * 2.9)
    d = np.abs(q - wob)
    crack = band & (d < 1.4) & (np.abs(s) < half_len - 1)
    ramp = ('β', 'γ', 'δ', 'ε', 'θ')
    c_in = ramp[min(4, int(u * 5))]
    c_out = ramp[min(4, int(u * 5) + 1)]
    L[crack] = np.where(d[crack] < 0.6, c_in, c_out)
    ang = math.radians(RING_ROW_DEG[row])
    ux, uy = math.cos(ang), -math.sin(ang)
    cx, cy = RING_PIVOT
    p = max(0.0, 1.0 - u * 1.5)
    fd = FI.Field(RW, RH)
    emb = []
    if p > 0:
        for i, f in enumerate((-0.55, 0.0, 0.55)):
            ss = f * (half_len - 2)
            FI.tongue(fd, cx + ss * ux, cy + ss * uy, (t + i * 0.37) % 1.0, (4 + 8 * p) * (0.9 + 0.2 * (i == 1)),
                      1.2 + 1.0 * p, seed=row * 5 + i * 1.9, rate=7, embers=emb, ember_every=1, temp=0.5 + 0.4 * p)
        fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    for i, f in enumerate((-0.5, 0.1, 0.6)):
        life = min(1.0, u * 1.3 - i * 0.1)
        if life <= 0:
            continue
        ss = f * (half_len - 2)
        FI.puff(L, cx + ss * ux, cy + ss * uy - 2 - life * 7, 1.5 + life * 2.6, ramp=FI.STEAM,
                dissolve=max(0.0, life - 0.5) * 1.8, seed=row * 3 + i)
    if u > 0.55:                          # the scar settles back into the floor as the ring frees itself
        X_, Y_ = np.meshgrid(np.arange(RW), np.arange(RH))
        gone = FI.hash01(np.floor(X_ / 2.0), np.floor(Y_ / 2.0), 7 + row) < (u - 0.55) / 0.45
        L[gone] = '.'
    return L


def ring_sheet(n=8, dying=True):
    """7 rows (Bixby's tangent buckets) x n frames, then (dying=True) the 7 dying rows."""
    rows = [[ring_segment(r, k, n) for k in range(n)] for r in range(7)]
    if dying:
        rows += [[ring_dying(r, k, n) for k in range(n)] for r in range(7)]
    return rows


# ================================================================== steam
def steam_puff(k, n=8):
    """24x40, pivot (12, 38) on the floor, n frames once: a bubble of steam lifts off the wet floor,
    swells and rolls as it rises, sheds a smaller puff, then tears into scraps from its edges and is gone."""
    L = blank(24, 40)
    u = k / float(n - 1)
    cy = 35 - u * 24
    r = 2.4 + 5.2 * min(1.0, u * 1.4)
    wob = math.sin(u * 5) * 1.3
    diss = max(0.0, (u - 0.45) / 0.55) ** 0.9
    FI.puff(L, 12 + wob, cy, r, ramp=FI.STEAM, dissolve=diss, seed=11,
            lobes=((0.0, 0.0, 1.0), (-0.6, 0.3, 0.66), (0.62, 0.26, 0.7), (0.15, -0.52, 0.62 + 0.1 * u)))
    if 0.2 < u < 0.9:                         # the little puff it sheds, falling behind and fading first
        v = (u - 0.2) / 0.7
        FI.puff(L, 12 - wob * 0.5 + 4 * v, cy + r + 2 - v * 2, 1.6 + v, ramp=FI.STEAM,
                dissolve=min(1.0, v * 1.3), seed=12)
    return L


def wisp(k, n=8):
    """16x40, pivot (8, 39), n-frame loop: threads of vapour rising off standing water - thick and dense at
    the water, curling, thinning to dashes and gone at the top."""
    L = blank(16, 40)
    t = k / float(n)
    for i in range(3):
        ph = (t + i / 3.0) % 1.0
        base_y = 38 - ph * 22
        ln = 12
        for j in range(ln):
            f = j / float(ln - 1)
            age = ph + f * 0.35
            y = base_y - j * 1.2
            x = 8 + (i - 1) * 2.5 + math.sin(j * 0.55 + ph * TAU + i * 2.1) * (0.8 + j * 0.28) + ph * 2
            if y < 1 or y >= 40:
                continue
            if age > 0.85 and j % 2:
                continue
            c = FI.STEAM[min(3, int(age * 3.2))]
            plot(L, x, y, c)
            if f < 0.55 and age < 0.7:
                plot(L, x + 1, y, FI.STEAM[min(3, int(age * 3.2) + 1)])
    return L


def steam_vent(k, n=8):
    """32x48, pivot (16, 46), n-frame loop: a column of steam boiling off hot water (at a tornado's foot or
    a quake crack): puffs rolling up and tearing apart."""
    L = blank(32, 48)
    t = k / float(n)
    for i in range(5):
        life = (t + i / 5.0) % 1.0
        x = 16 + math.sin(TAU * (life * 0.7 + i * 0.29)) * (1 + 4 * life)
        y = 44 - life * 34
        r = 2.2 + 4.5 * life
        FI.puff(L, x, y, r, ramp=FI.STEAM, dissolve=max(0.0, life - 0.5) * 1.8, seed=20 + i)
    return L


# ------------------------------------------------------------------ the steam fog (full-screen overlay)
FOG_W, FOG_H = 640, 360                 # one screen of texels (1920x1080 at 3x); seamless both ways


def _tile_noise(w, h, cx, cy, seed):
    """Seamless value noise, cells cx by cy texels."""
    rnd = np.random.RandomState(seed)
    nx, ny = w // cx, h // cy
    g = rnd.rand(ny, nx)
    ys, xs = np.mgrid[0:h, 0:w]
    fx, fy = xs / float(cx), ys / float(cy)
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    x1, y1 = (x0 + 1) % nx, (y0 + 1) % ny
    x0, y0 = x0 % nx, y0 % ny
    a = g[y0, x0] * (1 - tx) + g[y0, x1] * tx
    b = g[y1, x0] * (1 - tx) + g[y1, x1] * tx
    return a * (1 - ty) + b * ty


def _fog_field(seed=13):
    """Banks of steam: big soft sheets stretched sideways, their edges curled by a second noise (domain
    warp), with finer wisps riding on them."""
    w, h = FOG_W, FOG_H
    warp_x = _tile_noise(w, h, 80, 60, seed + 1) - 0.5
    warp_y = _tile_noise(w, h, 64, 45, seed + 2) - 0.5
    base = 0.55 * _tile_noise(w, h, 160, 60, seed) + 0.3 * _tile_noise(w, h, 80, 30, seed + 3)
    ys, xs = np.mgrid[0:h, 0:w]
    wx = (xs + warp_x * 36).astype(int) % w
    wy = (ys + warp_y * 20).astype(int) % h
    fine = _tile_noise(w, h, 32, 12, seed + 4)
    ridge = 1 - np.abs(2 * _tile_noise(w, h, 64, 20, seed + 5) - 1)       # wispy ridges
    f = base[wy, wx] + 0.12 * fine[wy, wx] + 0.1 * ridge[wy, wx]
    f = (f - f.min()) / (f.max() - f.min())
    return f


_FOG = None
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def fog_screen(density):
    """640x360, seamless both ways, drawn over the floor, the hazards and Liam (under the player and the
    tells), scrolled slowly sideways. density 0 light wisps, 1 banks, 2 thick, 3 'really really hard to
    see' (attack 4). Banded alpha with ordered dither at each band edge (no smooth gradients)."""
    global _FOG
    if _FOG is None:
        _FOG = _fog_field()
    f = _FOG + (np.tile(BAYER4, (FOG_H // 4, FOG_W // 4)) - 0.5) * 0.045
    L = blank(FOG_W, FOG_H)
    bands = {0: ((0.62, 'π'), (0.72, 'ρ')),
             1: ((0.44, 'π'), (0.55, 'ρ'), (0.66, 'σ')),
             2: ((0.2, 'π'), (0.36, 'ρ'), (0.5, 'σ'), (0.64, 'τ')),
             3: ((0.0, 'ρ'), (0.3, 'σ'), (0.46, 'τ'), (0.6, 'υ'))}[density]
    for th, ch in bands:
        L[f >= th] = ch
    return L


def fog(density):
    """The 256x256 version (a crop of the screen fog, not seamless): kept for the first-pass mock code."""
    return fog_screen(min(3, density + (1 if density == 2 else 0)))[:256, :256]


# ================================================================== the red lunge triangle
TRI = 32


def _tri_mask(scale, angle_deg):
    X, Y = R.centres(TRI, TRI)
    a = math.radians(angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for (px, py) in ((-8.5, -10.0), (10.5, 0.0), (-8.5, 10.0)):
        px, py = px * scale, py * scale
        pts.append((16 + px * ca - py * sa, 16 + px * sa + py * ca))
    return R.poly_mask(pts, TRI, TRI), pts


def triangle_dir(k, angle_deg=0.0):
    """32x32, pivot (16, 16), pointing along angle_deg (0 = right, 90 = down), 6 frames: 0 a spark,
    1 pops in (overshoot), 2 settled, 3 pulse ring, 4 settled, 5 the 'now' flash as he lunges.
    The parry badge's reds, a white inner rim, the black keyline and a dark halo for the steam."""
    L = blank(TRI, TRI)
    if k == 0:
        for (x, y, ch) in ((16, 16, 'W'), (15, 16, 'ψ'), (17, 16, 'ψ'), (16, 15, 'ψ'), (16, 17, 'ψ'),
                           (14, 16, 'φ'), (18, 16, 'φ'), (16, 14, 'φ'), (16, 18, 'φ')):
            L[y, x] = ch
        return L
    scale = {1: 1.12, 2: 1.0, 3: 1.04, 4: 1.0, 5: 1.0}[k]
    m, pts = _tri_mask(scale, angle_deg)
    X, Y = R.centres(TRI, TRI)
    halo = m.copy()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        halo |= np.roll(np.roll(m, dx, axis=1), dy, axis=0)
    L[halo & ~m] = 'ω'
    # the fill splits along the triangle's own axis: the upper half lit
    a = math.radians(angle_deg)
    side = -(X - 16) * math.sin(a) + (Y - 16) * math.cos(a)
    lit = side < 0 if abs(math.cos(a)) >= abs(math.sin(a)) * 0.99 else (X - 16) * math.sin(a) < 0
    fill = np.where(lit, 'φ', 'χ')
    if k == 1:
        fill = np.where(lit, 'ψ', 'φ')
    if k == 5:
        fill = np.where(lit, 'ψ', 'φ')
    L[m] = fill[m]
    ol = R.outline_pixels(m, prune=True)
    inner = m & ~ol
    L[R.outline_pixels(inner, prune=True)] = 'W'
    L[ol] = '#'
    if k == 3:
        m2, _ = _tri_mask(1.3, angle_deg)
        o2 = R.outline_pixels(m2, prune=True) & (L == '.')
        L[o2] = 'φ'
    if k == 5:
        for (x, y) in ((4, 4), (27, 5), (4, 27), (28, 26), (16, 2), (2, 16)):
            L[y, x] = 'W'
    return L


def triangle(k):
    return triangle_dir(k, 0.0)


# ================================================================== water
def water_jet(k, n=6):
    """32x16 tile, seamless left-right, pointing RIGHT, n-frame loop: a hard jet - bright core, white
    streaks racing along it, its skin bulging as pulses travel down it, spray flicking off both edges."""
    L = blank(32, 16)
    X, Y = R.centres(32, 16)
    t = k / float(n)
    ph = (X / 32.0 - t) * TAU
    bulge = 0.9 * np.sin(ph * 2) + 0.5 * np.sin(ph * 3 + 1.1)
    half = 4.3 + bulge * 0.7
    cy = 8 + 0.4 * np.sin(ph * 1)
    d = np.abs(Y - cy)
    L[d <= half] = '%'
    L[d <= half - 1.0] = '='
    L[d <= half - 2.2] = '+'
    L[(d <= half - 3.2)] = 'l'
    L[(Y < cy) & (d <= half) & (d > half - 1.0)] = '+'           # the lit upper skin
    streak = (((X - t * 64) % 11) < 4) & (d <= 1.3)
    L[streak] = 'W'
    streak2 = (((X - t * 64 + 5) % 13) < 3) & (np.abs(Y - cy + 2.2) < 0.6)
    L[streak2 & (d <= half - 1)] = 'W'
    rnd = np.random.RandomState(7)
    for i in range(12):
        x0 = (rnd.randint(0, 32) - t * 32 * (0.5 + 0.5 * (i % 2))) % 32
        side = -1 if i % 2 else 1
        dist = 5 + ((k + i) % 3)
        y0 = 8 + side * dist
        plot(L, x0, y0, 'l' if (k + i) % 2 else 'W')
        plot(L, x0 + 1, y0 - side * 0.5, '+')
    return L


def _spray(L, ox, oy, ang, length, t, width=1, seed=0, ramp=('W', 'l', '+', '=')):
    """One spray streak from (ox, oy) along ang, curving down a little as it goes (gravity), bright at
    the root, beading into droplets at its tip."""
    n = int(length * 1.6) + 2
    for j in range(n):
        f = j / float(n - 1)
        d = f * length
        x = ox + math.cos(ang) * d
        y = oy + math.sin(ang) * d + (f ** 2) * length * 0.18
        if f > 0.7 and (j % 2):
            continue
        c = ramp[min(3, int(f * 4))]
        plot(L, x, y, c)
        if width > 1 and f < 0.5:
            plot(L, x - math.sin(ang), y + math.cos(ang), ramp[min(3, int(f * 4) + 1)])


def water_head(k, n=6):
    """40x40, pivot (10, 20) where the jet slams the player (the jet comes from the left): the water
    bursts into a crown of spray fanning forward round him, sheets and streaks racing out and beading
    into droplets that arc and fall (n-frame loop while he is carried)."""
    L = blank(40, 40)
    X, Y = R.centres(40, 40)
    t = k / float(n)
    rnd = np.random.RandomState(9)
    for i in range(13):
        base = -1.25 + 2.5 * i / 12.0
        life = (t + rnd.rand()) % 1.0
        ang = base + 0.1 * math.sin(TAU * (t + i * 0.3))
        ln = (8 + 14 * rnd.rand()) * (0.5 + 0.5 * life)
        ox = 10 + math.cos(ang) * 3
        oy = 20 + math.sin(ang) * 5
        _spray(L, ox, oy, ang, ln, t, width=2 if abs(base) < 0.9 else 1, seed=i)
    # droplets flung beyond, arcing down
    for i in range(12):
        life = (t + i / 12.0) % 1.0
        a = (rnd.rand() - 0.5) * 2.6
        v = 16 + 10 * rnd.rand()
        x = 12 + math.cos(a) * v * life
        y = 20 + math.sin(a) * v * life + 12 * life * life
        plot(L, x, y, 'W' if life < 0.35 else ('l' if life < 0.7 else '+'))
    # the white foam where it hits
    core = ((X - 10) / 4.5) ** 2 + ((Y - 20) / 7.0) ** 2 <= 1
    L[core] = np.where(((X - 9) / 3.2) ** 2 + ((Y - 19) / 5.0) ** 2 <= 1, 'W', 'l')[core]
    return L


def water_trail(k, n=4):
    """24x32, pivot (12, 31): streaks and droplets shed behind a player washed down the ring."""
    L = blank(24, 32)
    t = k / float(n)
    for i, x in enumerate((4, 8, 12, 16, 20)):
        off = (t * 12 + i * 5) % 12
        top = 2 + off
        ln = 7 + (i * 5) % 6
        for j in range(ln):
            y = top + j
            if y < 30:
                plot(L, x + (1 if (j // 3) % 2 else 0), y, 'l' if j > ln - 3 else ('+' if j % 3 else '='))
        plot(L, x - 1, top - 2, 'l')
        plot(L, x + 2, top - 4 + (k % 2), 'W')
    return L


def water_muzzle(k, n=5):
    """40x40, pivot (20, 20) on the staff's water gem, once: the gem bursts - a white flash, spray streaks
    fanning out all round and beading into droplets, the droplets falling away."""
    L = blank(40, 40)
    u = k / float(n - 1)
    X, Y = R.centres(40, 40)
    if k <= 1:
        rr = 3.2 + 2.4 * u
        core = ((X - 20) / rr) ** 2 + ((Y - 20) / rr) ** 2 <= 1
        L[core] = np.where(((X - 20) / (rr * 0.6)) ** 2 + ((Y - 20) / (rr * 0.6)) ** 2 <= 1, 'W', 'l')[core]
    rnd = np.random.RandomState(4)
    for i in range(14):
        ang = TAU * i / 14 + rnd.rand() * 0.3
        start = 3 + 9 * u
        ln = (4 + 8 * rnd.rand()) * (1.0 - 0.5 * u)
        ox, oy = 20 + math.cos(ang) * start, 20 + math.sin(ang) * start + u * u * 5
        if u < 0.95:
            _spray(L, ox, oy, ang, ln, 0.0, width=1, seed=i,
                   ramp=('W', 'l', '+', '=') if u < 0.5 else ('l', '+', '=', '%'))
    return L


def extinguish(k, n=8):
    """40x44, pivot (20, 40) = the player's feet, n frames once: water hits the burning player - the
    flames flinch and shrink, a hiss of steam bursts out where they meet and billows up round him, the
    last tongues gutter to embers that wink out, the steam tears into wisps and is gone."""
    L = blank(40, 44)
    u = k / float(n - 1)
    t = k / 8.0
    fd = FI.Field(40, 44)
    emb = []
    p = max(0.0, 1.0 - u * 1.9)
    if p > 0:
        for i, (bx, by) in enumerate(((11, 40), (16, 41), (24, 41), (29, 40), (10, 30), (30, 30), (13, 20), (27, 20))):
            FI.tongue(fd, bx, by, (t + i * 0.23) % 1.0, (5 + 7 * p) * (0.8 + 0.1 * (i % 3)), 1.0 + 1.2 * p,
                      seed=140 + i * 1.3, embers=emb, temp=0.4 + 0.5 * p, anchor=False)
        fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    # embers winking out after the flames
    for i, (x, y) in enumerate(((9, 36), (31, 35), (14, 24), (26, 22), (20, 40), (12, 30), (28, 29))):
        life = u * 1.4 - 0.25 - i * 0.05
        if 0 < life < 1:
            c = 'β' if life < 0.25 else ('δ' if life < 0.5 else ('ε' if life < 0.75 else 'ϖ'))
            plot(L, x + (i % 2 * 2 - 1) * life * 2, y - life * 5, c)
    # the steam: bursts out sideways first (the hiss), then billows up and tears apart
    if k >= 1:
        v = (k - 1) / float(n - 2)
        spots = ((8, 32), (32, 31), (20, 24), (12, 18), (28, 16), (20, 10))
        for i, (x, y) in enumerate(spots):
            born = i * 0.1
            if v < born:
                continue
            w = (v - born) / (1 - born)
            FI.puff(L, x + (x - 20) * 0.25 * w, y - w * 8, 2.6 + 3.6 * min(1.0, w * 1.6), ramp=FI.STEAM,
                    dissolve=max(0.0, w - 0.4) * 1.5, seed=150 + i)
    return L


# ================================================================== fire on the impaled player
def flame_overlay(k, n=8):
    """28x44, pivot (14, 41) = the player's feet (his body is about 11 x 25 texels: x 8.5-19.5, y 16-41),
    n-frame loop: sheets of flame licking up both his flanks and off his feet, a crown of tongues over
    his head, all flickering, tearing off and dying to embers and smoke. His middle stays clear so he
    reads through it."""
    L = blank(28, 44)
    t = k / float(n)
    fd = FI.Field(28, 44)
    emb = []
    spots = ((9.0, 39, 11, 2.3, -0.2), (8.6, 32, 12, 2.2, -0.25), (9.0, 25, 12, 2.2, -0.2), (10.0, 19, 11, 2.0, -0.15),
             (19.0, 39, 11, 2.3, 0.2), (19.4, 32, 12, 2.2, 0.25), (19.0, 25, 12, 2.2, 0.2), (18.0, 19, 11, 2.0, 0.15),
             (12.0, 17, 14, 2.3, -0.1), (14.5, 16, 16, 2.5, 0.0), (17.0, 17, 14, 2.3, 0.1),
             (11.5, 41, 8, 2.0, -0.1), (16.5, 41, 8, 2.0, 0.1))
    for i, (bx, by, H, r0, lean) in enumerate(spots):
        FI.tongue(fd, bx, by, (t + i * 0.29) % 1.0, H, r0, seed=160 + i * 1.7, rate=6, embers=emb,
                  ember_every=2, temp=0.66, anchor=False, lean=lean)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    return L


def column_edge(k, n=6):
    """12x48, seamless top-bottom, n-frame loop: flame billowing OUT of the right side of Bixby's fire
    column (lay it beside the stacked bixby_flyby_curtain; flip it for the left side), curling up and
    tearing off into embers."""
    H_ = 48
    L = blank(12, H_)
    t = k / float(n)
    big = blank(12, H_ * 3)
    fd = FI.Field(12, H_ * 3)
    emb = []
    for i, y in enumerate(range(3, H_ * 3, 12)):
        j = i % 4
        FI.tongue(fd, 0.0, y, (t + j * 0.31) % 1.0, 9.0 + (j % 2) * 2.0, 2.3, seed=170 + j * 1.3, rate=6,
                  up=(1.0, -0.25), curl=6.0, embers=emb, ember_every=2, temp=0.75, anchor=True)
    fd.render(big, fill=False)
    FI.draw_embers(big, emb, smoke_ramp=FI.SMOKE_THIN)
    L[:, :] = big[H_:H_ * 2, :]
    return L


def fire_hit(k, n=6):
    """56x32, pivot (28, 14) = the top of the impaled player's head, n-frame loop: where Bixby's column
    lands on him - the column's end bulges white-hot on his head and the fire sheets outward and down
    over his shoulders like water off a rock, the sheets curling back up into tongues at their ends and
    tearing off; embers flung."""
    L = blank(56, 32)
    t = k / float(n)
    fd = FI.Field(56, 32)
    emb = []
    pulse = 1.0 + 0.1 * math.sin(TAU * t * 2)
    for side in (-1, 1):
        for j, (H, r0, dy) in enumerate(((16, 2.6, 0.55), (13, 2.2, 0.8), (10, 1.9, 0.3))):
            FI.tongue(fd, 28 + side * 2.0, 13 + j, (t + j * 0.27 + (0.5 if side > 0 else 0.0)) % 1.0, H * pulse, r0,
                      seed=180 + j * 2 + side, rate=7, up=(side * 0.9, dy), curl=H * 0.75, embers=emb,
                      ember_every=2, temp=0.9, anchor=False, accel=1.5)
    fd.blob(28, 8, 4.0 * pulse, temp=1.0, stretch=1.6)
    fd.blob(28, 13, 4.6 * pulse, temp=1.0, stretch=0.6)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    return L


# ================================================================== the ignite spark and the summon gust
def ignite_spark(k, n=4):
    """16x16, pivot (8, 8), n-frame loop: the spark Liam's fire gem throws at each tornado's foot - a
    tumbling ball of flame (radial, so it needs no turning); the code leaves ember_trail behind it."""
    L = blank(16, 16)
    t = k / float(n)
    fd = FI.Field(16, 16)
    for i in range(5):
        a = TAU * (i / 5.0 + t)
        FI.tongue(fd, 8 + math.cos(a) * 1.5, 8 + math.sin(a) * 1.5, (t + i * 0.2) % 1.0, 4.5, 1.4,
                  seed=190 + i, up=(math.cos(a), math.sin(a)), temp=1.0, anchor=False, rate=5)
    fd.blob(8, 8, 2.8, temp=1.0, stretch=1.0)
    fd.render(L)
    return L


def ember_trail(k, n=4):
    """8x8, pivot (4, 4), once (n frames): what the spark leaves hanging in the air - a spark cooling to
    an ember and a wisp of smoke."""
    L = blank(8, 8)
    u = k / float(n - 1)
    c = 'α' if u < 0.2 else ('γ' if u < 0.45 else ('ε' if u < 0.75 else 'ϖ'))
    plot(L, 4, 4 - u * 2, c)
    if u < 0.4:
        plot(L, 5, 4 - u * 2, 'β')
        plot(L, 4, 5 - u * 2, 'δ')
    if u >= 0.75:
        plot(L, 5, 3 - u * 2, 'ϡ')
    return L


def gust_bolt(k, n=6):
    """40x24, pivot (30, 12) = its head, pointing RIGHT, n-frame loop: the gust Liam blows out to each
    tornado spot - a spinning ball of wind at the head (streaks wheeling round it) dragging a wake of
    wavering streaks that fray behind it."""
    L = blank(40, 24)
    t = k / float(n)
    hx, hy = 30, 12
    for i in range(3):                                   # the wake
        ph = TAU * (t + i / 3.0)
        for j in range(30):
            f = j / 29.0
            x = hx - 3 - f * 26
            y = hy + (i - 1) * (1.5 + 3 * f) + math.sin(ph + f * 6.0) * (0.6 + 2.2 * f)
            if f > 0.55 and (j + i) % 2:
                continue
            plot(L, x, y, 'W' if f < 0.2 else ('w' if f < 0.5 else ('v' if f < 0.8 else 'ν')))
    for ring, rr in enumerate((5.5, 3.5)):              # the spinning head
        for j in range(22):
            f = j / 21.0
            a = TAU * t * (2 + ring) + f * 4.4 + ring * 1.3
            plot(L, hx + math.cos(a) * rr, hy + math.sin(a) * rr * 0.8,
                 'W' if f < 0.35 else ('w' if f < 0.7 else 'v'))
    plot(L, hx, hy, 'W')
    return L


def blow_cone(k, n=6):
    """48x40, pivot (24, 2) = his lips, n frames once: the breath leaving him - curling streaks pouring
    down and out of his mouth, thick and bright near him, fraying at their ends, then trailing away."""
    L = blank(48, 40)
    u = k / float(n - 1)
    for i in range(5):
        a = math.radians(55 + i * 17.5)
        ln = (12 + 26 * min(1.0, u * 1.6)) * (0.8 + 0.2 * ((i * 5) % 3) / 2.0)
        tail_gone = max(0.0, (u - 0.6) * 2.5)
        for j in range(int(ln)):
            f = j / max(1.0, ln - 1)
            if f < 0.14 or f < tail_gone:
                continue
            wave = math.sin(f * 7.0 + u * 6 + i) * (0.5 + 2.0 * f)
            x = 24 + math.cos(a) * j + math.cos(a + 1.57) * wave
            y = 2 + math.sin(a) * j * 0.95 + math.sin(a + 1.57) * wave
            c = 'W' if f > 0.8 else ('w' if f > 0.35 else 'v')
            if f > 0.6 and j % 2:
                continue
            plot(L, x, y, c)
            if 0.2 < f < 0.5:
                plot(L, x + 1, y, 'v')
    return L


# ================================================================== the pull (the floor under a tornado)
SW, SH = 96, 40
SWIRL_PIVOT = (48, 20)


def pull_swirl(k, n=8, kind='water'):
    """96x40, pivot (48, 20) = the tornado's foot, n-frame loop, drawn on the floor under a tornado: the
    floor's water (or the spray on the ice, kind='ice') dragged round and in, in a flattened spiral
    (the floor's 0.36) - streaks racing inward, so the pull reads before it is felt."""
    L = blank(SW, SH)
    t = k / float(n)
    ramp = ('W', 'ϙ', 'ϛ', 'ϝ') if kind == 'water' else ('W', 'w', 'ν', 'ξ')
    arms = 5
    for i in range(arms):
        for j in range(60):
            f = j / 59.0                                   # 0 = inner end (the head), 1 = outer tail
            r = 4 + f * 40
            a = TAU * (i / float(arms) + t) + f * 3.0
            x = SWIRL_PIVOT[0] + r * math.cos(a)
            y = SWIRL_PIVOT[1] + r * 0.36 * math.sin(a)
            if f > 0.55 and j % 2:
                continue
            c = ramp[0] if f < 0.1 else (ramp[1] if f < 0.35 else (ramp[2] if f < 0.7 else ramp[3]))
            plot(L, x, y, c)
    return L


# ================================================================== CONTRACT PIECES (ADDENDUM3 E.4)
# steam tile alpha levels (white steam; the shader reads the ALPHA as density)
STEAM_TILE = {'Γ': (240, 244, 248, 89), 'Δ': (240, 244, 248, 128), 'Θ': (240, 244, 248, 166),
              'Λ': (242, 246, 250, 204), 'Ξ': (244, 247, 250, 242)}
R.PAL.update(STEAM_TILE)


def blow_gust(k, n=6):
    """liam_blow_gust: 64x48, pivot (32, 4) on his lips, n frames once (0.5 s): the breath leaving him -
    curling streaks pouring down and fanning out, thick and bright near him, their heads winding into
    little whirls (the tornados to be) as they spread, then the tails trail away."""
    L = blank(64, 48)
    u = k / float(n - 1)
    mx, my = 32, 4
    for i in range(7):
        a = math.radians(38 + i * 17.3)
        reach = (8 + 34 * min(1.0, u * 1.5)) * (0.8 + 0.2 * ((i * 5) % 3) / 2.0)
        tail_gone = max(0.0, (u - 0.55) * 2.2)
        ns = int(reach * 1.6) + 2
        for j in range(ns):
            f = j / float(ns - 1)
            if f < (0.1 if i == 3 else 0.22) or f < tail_gone:
                continue
            d = f * reach
            wave = math.sin(f * 6.0 + u * 5 + i * 1.3) * (0.4 + 1.8 * f)
            x = mx + math.cos(a) * d + math.cos(a + math.pi / 2) * wave
            y = my + math.sin(a) * d * 0.9 + math.sin(a + math.pi / 2) * wave
            if f > 0.55 and j % 2:
                continue
            plot(L, x, y, 'W' if f > 0.8 else ('w' if f > 0.4 else 'v'))
            if 0.15 < f < 0.45 and i % 2 == 0:
                plot(L, x + 1, y, 'v')
        if u > 0.3:
            hx, hy = mx + math.cos(a) * reach, my + math.sin(a) * reach * 0.9
            rr = 1.5 + 1.6 * min(1.0, (u - 0.3) * 2)
            for m in range(11):
                aa = m * 0.62 + u * 8 + i
                sh = 1 - m / 15.0
                plot(L, hx + math.cos(aa) * rr * sh, hy + math.sin(aa) * rr * 0.7 * sh, 'W' if m < 4 else 'w')
    return L


def fire_streak(k, n=6):
    """liam_fire_streak: 24x12 flying RIGHT, pivot (20, 6) = its head, n-frame loop (0.05): the spark
    Liam's fire gem throws at each tornado's base - a white-hot head, flame streaming back off it and
    tearing into embers behind."""
    L = blank(24, 12)
    t = k / float(n)
    fd = FI.Field(24, 12)
    emb = []
    for i in range(3):
        FI.tongue(fd, 19.0, 6 + (i - 1) * 1.3, (t + i * 0.33) % 1.0, 15 - i * 2.5, 2.1 - i * 0.35, seed=210 + i,
                  up=(-1.0, (i - 1) * 0.1), temp=0.9, anchor=False, rate=6, embers=emb, ember_every=2, accel=1.4)
    fd.blob(19.5, 6, 2.8, temp=1.0, stretch=0.9)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    return L


def wind_streak(row, k, n=4):
    """liam_wind_streak (optional; BixbyInferno FINAL_SUCTION's format): 24x24, pivot (12, 12), rows at 0,
    45 and 90 degrees (right, down-right, down), n-frame loop; each streak flies toward its bright head.
    It is the firestorm's hot pull, so a spark rides one of them."""
    L = blank(24, 24)
    t = k / float(n)
    ang = math.radians((0, 45, 90)[row])
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    for i in range(3):
        off = (i - 1) * 4.5
        prog = (t + i * 0.37) % 1.0
        head = -8 + prog * 17
        ln = 7 + 3 * ((i * 2) % 3)
        for j in range(ln):
            f = j / float(ln - 1)
            sd = head - j
            if abs(sd) > 11.5:
                continue
            wav = math.sin(sd * 0.6 + i) * 0.6
            x, y = 12 + ux * sd + px * (off + wav), 12 + uy * sd + py * (off + wav)
            if f > 0.6 and j % 2:
                continue
            plot(L, x, y, 'W' if f < 0.15 else ('w' if f < 0.5 else ('v' if f < 0.8 else 'ν')))
        if i == 1 and prog < 0.85:
            plot(L, 12 + ux * (head + 1) + px * off, 12 + uy * (head + 1) + py * off, 'β')
    return L


def melt_rim(k, n=4):
    """liam_melt_rim: 16x16, pivot (8, 8), n-frame loop (0.1): stamped round each melting circle where it
    lies over the flood - the ice edge going to slush: plates bobbing and shrinking in dark water,
    bubbles popping, a thread of steam rising off it."""
    L = blank(16, 16)
    t = k / float(n)
    X, Y = R.centres(16, 16)
    pool = ((X - 8) / 7.2) ** 2 + ((Y - 8.5) / 5.6) ** 2 <= 1
    L[pool] = '='
    L[pool & (((X - 7) / 5.0) ** 2 + ((Y - 7.5) / 3.6) ** 2 <= 1)] = '+'
    for i, (cx, cy, r) in enumerate(((4.5, 7.0, 2.4), (10.5, 6.0, 2.1), (7.5, 11.0, 2.2), (12.5, 10.5, 1.5),
                                     (3.5, 11.5, 1.4))):
        bob = 0.5 * math.sin(TAU * (t + i * 0.23))
        rr = r * (0.88 + 0.12 * math.cos(TAU * (t + i * 0.4)))
        m = ((X - cx) / rr) ** 2 + ((Y - cy - bob) / (rr * 0.72)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, cx, cy + bob, rr, rr * 0.72))
        L[m] = np.where(v > 0.72, 'W', np.where(v > 0.42, 'l', 'b'))[m]
    for i, (x, y) in enumerate(((8, 8), (6, 9), (11, 8), (9, 12))):
        ph = (t + i * 0.27) % 1.0
        if ph < 0.6:
            plot(L, x, y - ph * 1.5, 'l' if ph < 0.4 else 'W')
    for j in range(8):
        f = j / 7.0
        ph = (t + f * 0.4) % 1.0
        x = 9 + math.sin(j * 0.8 + t * TAU) * 1.2
        y = 6 - j * 0.9
        if y >= 0 and ph < 0.8:
            plot(L, x, y, FI.STEAM[min(3, int(f * 4))])
    return L


def steam_tile(layer=0):
    """liam_steam_tile: 128x128, seamless both ways; frame 0 = the shader's first layer (broad banks of
    steam), frame 1 = its second (long soft drifts, sampled at another speed so the two never line up).
    White steam whose ALPHA carries the density (the shader multiplies it by `density`): five alpha
    bands (0.35 .. 0.95) with an ordered dither on each edge, most of the tile 0.65 and up, so steam_max
    0.85 covers the arena 70-90 %."""
    w = h = 128
    if layer == 0:
        wx = _tile_noise(w, h, 64, 64, 41) - 0.5
        wy = _tile_noise(w, h, 64, 32, 42) - 0.5
        base = 0.62 * _tile_noise(w, h, 64, 32, 43) + 0.26 * _tile_noise(w, h, 32, 16, 44) + 0.12 * _tile_noise(
            w, h, 16, 8, 45)
        cuts = (0.0, 0.2, 0.34, 0.52, 0.72)
        sx, sy = 20, 10
    else:
        wx = _tile_noise(w, h, 64, 32, 46) - 0.5
        wy = _tile_noise(w, h, 32, 32, 47) - 0.5
        base = 0.6 * _tile_noise(w, h, 128, 16, 48) + 0.28 * _tile_noise(w, h, 64, 16, 49) + 0.12 * _tile_noise(
            w, h, 32, 8, 50)
        cuts = (0.0, 0.25, 0.42, 0.6, 0.78)
        sx, sy = 26, 6
    ys, xs = np.mgrid[0:h, 0:w]
    f = base[(ys + (wy * sy).astype(int)) % h, (xs + (wx * sx).astype(int)) % w]
    f = (f - f.min()) / (f.max() - f.min())
    f = f + (np.tile(BAYER4, (h // 4, w // 4)) - 0.5) * 0.05
    L = blank(w, h)
    for c, ch in zip(cuts, ('Γ', 'Δ', 'Θ', 'Λ', 'Ξ')):
        L[f >= c] = ch
    return L


def steam_wisp(k, n=8):
    """liam_steam_wisp: 16x32, pivot (8, 31) on the wet floor, n frames once (0.8 s): a thread of vapour
    lifts off the water, curls as it climbs, lets go of the floor, thins to dashes and is gone."""
    L = blank(16, 32)
    u = k / float(n - 1)
    top = 30 - (4 + 26 * min(1.0, u * 1.3))
    bottom = 31 - max(0.0, u - 0.35) * 34
    y = bottom
    j = 0
    while y > top and y > 0:
        f = (bottom - y) / max(1.0, bottom - top)
        x = 8 + math.sin(y * 0.33 + u * 4.0) * (0.8 + (31 - y) * 0.1) + u * 1.5
        age = min(1.0, u * 0.7 + f * 0.45)
        if not (age > 0.8 and j % 2):
            plot(L, x, y, FI.STEAM[min(3, int(age * 3.4))])
            if f < 0.75 and u < 0.8:
                plot(L, x + 1, y, FI.STEAM[min(3, int(age * 3.4))])
            if f < 0.35 and u < 0.5:
                plot(L, x - 1, y, FI.STEAM[min(3, int(age * 3.4) + 1)])
        y -= 1.0
        j += 1
    return L


def steam_puff(k, n=7):
    """liam_steam_puff: 48x48, pivot (24, 44) at his feet, n frames once (0.35 s): a poof of steam -
    billows burst out and up round the feet, roll over, and tear apart into scraps (plays for the vanish,
    the whiff and the teleports; `reverse` plays it backward)."""
    L = blank(48, 48)
    u = k / float(n - 1)
    grow = min(1.0, u * 2.2)
    diss = max(0.0, (u - 0.4) / 0.6)
    for i in range(7):
        a = math.pi + i * math.pi / 6.0
        dist = 4 + 13 * math.sqrt(u)
        x = 24 + math.cos(a) * dist * 1.15
        y = 42 + math.sin(a) * dist * 0.75 - u * 5
        r = (2.4 + 3.6 * grow) * (0.85 + 0.15 * ((i * 3) % 3))
        FI.puff(L, x, y, r, ramp=FI.STEAM, dissolve=diss, seed=230 + i)
    FI.puff(L, 24, 38 - u * 12, 3.5 + 4.5 * grow, ramp=FI.STEAM, dissolve=diss * 0.9, seed=237)
    return L


def lunge_wake(k, n=4):
    """liam_lunge_wake: 48x24 facing RIGHT, pivot (47, 12) on his back, n frames once (0.15 s): the steam
    he tears through, swept back behind him in streaks, and speed lines - fading from the far end."""
    L = blank(48, 24)
    u = k / float(n - 1)
    for i in range(7):
        yy = 12 + (i - 3) * 2.6 + (0.6 if i % 2 else -0.4)
        ln = 22 + 20 * (1 - abs(i - 3) / 3.0)
        start = 46 - (i % 2) * 2
        gone = u * ln * 0.9
        for j in range(int(ln)):
            f = j / max(1.0, ln - 1)
            if j < gone * 0.2 or f * ln > ln - gone:
                continue
            x = start - j
            y = yy + math.sin(j * 0.25 + i) * 0.4 * f * 3
            c = 'W' if f < 0.12 else ('λ' if f < 0.4 else ('μ' if f < 0.7 else 'ν'))
            if f > 0.55 and j % 2:
                continue
            plot(L, x, y, c)
    for i in range(3):
        x = 36 - i * 12 - u * 4
        FI.puff(L, x, 12 + (i - 1) * 4, 3.0 - i * 0.5 + u, ramp=FI.STEAM, dissolve=min(1.0, u * 1.3 + i * 0.2),
                seed=240 + i)
    return L


def sky_fire(k, n=6):
    """liam_sky_fire (optional; the default is bixby_flyby_curtain.png stacked): 32x48, stacks seamlessly,
    pivot (16, 0), n-frame loop (0.06): Bixby's breath pouring straight down - a white-hot core of streaks
    racing down, flame licking out of both edges and curling up, tearing off into embers."""
    H3 = 48 * 3
    t = k / float(n)
    X, Y = R.centres(32, H3)
    core = np.clip(1 - (np.abs(X - 16) / 12.5) ** 2, 0, 1)
    ph = (Y / 48.0 - t) * TAU                              # streaks race down one tile a loop
    streak = 0.5 + 0.5 * np.sin(ph * 2 + np.sin(X * 0.9) * 1.6 + X * 0.45)
    streak2 = 0.5 + 0.5 * np.sin(ph * 3 - X * 0.7 + 1.3)
    heat = 0.12 + 0.36 * core + 0.24 * streak * core + 0.08 * streak2        # mostly beta/gamma: it glows through
    ripple = 0.8 * np.sin(ph * 2 + 1.1) + 0.6 * np.sin(ph * 3 + X * 0.1)
    inside = np.abs(X - 16) <= 12.0 + ripple
    fd = FI.Field(32, H3)
    emb = []
    for i, y0 in enumerate(range(4, H3, 12)):
        j = i % 4
        side = -1 if i % 2 else 1
        FI.tongue(fd, 16 + side * 11.5, y0 + 6 * (j % 2), (t + j * 0.29) % 1.0, 7.5 + (j % 3), 1.9,
                  seed=250 + j * 2 + (side > 0), up=(side * 1.0, -0.2), curl=5.0, embers=emb, ember_every=2,
                  temp=0.75, anchor=False, rate=6)
    big = blank(32, H3)
    fd.render(big, base_inside=inside, base_heat=np.clip(heat, 0, 1), fill=False)
    FI.draw_embers(big, emb, smoke_ramp=FI.SMOKE_THIN)
    return big[48:96, :].copy()


def sky_fire_splash(k, n=6):
    """liam_sky_fire_splash: 48x32, pivot (24, 28) on the top of the impaled player's head, n-frame loop
    (0.06): where the column lands - the column's end bulges white-hot on his head and the fire splashes
    out in a crown, the sheets curling up into tongues that tear off; embers flung."""
    L = blank(48, 32)
    t = k / float(n)
    fd = FI.Field(48, 32)
    emb = []
    pulse = 1.0 + 0.1 * math.sin(TAU * t * 2)
    for side in (-1, 1):
        for j, (H, r0, dy) in enumerate(((15, 2.5, 0.5), (12, 2.1, 0.75), (9, 1.8, 0.25))):
            FI.tongue(fd, 24 + side * 2.0, 26 + j * 0.5, (t + j * 0.27 + (0.5 if side > 0 else 0.0)) % 1.0, H * pulse,
                      r0, seed=260 + j * 2 + side, rate=7, up=(side * 0.9, dy), curl=H * 0.75, embers=emb,
                      ember_every=2, temp=0.9, anchor=False, accel=1.5)
    fd.blob(24, 21, 3.8 * pulse, temp=1.0, stretch=1.7)
    fd.blob(24, 26, 4.4 * pulse, temp=1.0, stretch=0.6)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    return L


PLAYER_BOX = (6.5, 5.0, 17.5, 30.0)     # the player's body in the 24x32 cell (x0, y0, x1, y1), feet at (12, 30)


def player_flames(k, n=8):
    """liam_player_flames: 24x32, pivot (12, 30) = the player's feet, n-frame loop (0.06): flames licking
    up his flanks and off his shoulders and head, flickering, tearing off into embers and smoke. His
    middle stays clear: at most 60 % of his silhouette is ever covered."""
    L = blank(24, 32)
    t = k / float(n)
    fd = FI.Field(24, 32)
    emb = []
    spots = ((6.8, 29, 7, 1.7, -0.25), (6.4, 22, 8, 1.7, -0.3), (7.0, 14, 8, 1.6, -0.25),
             (17.2, 29, 7, 1.7, 0.25), (17.6, 22, 8, 1.7, 0.3), (17.0, 14, 8, 1.6, 0.25),
             (9.5, 7, 8, 1.7, -0.15), (14.5, 7, 8, 1.7, 0.15), (12.0, 6, 9, 1.8, 0.0))
    for i, (bx, by, H, r0, lean) in enumerate(spots):
        FI.tongue(fd, bx, by, (t + i * 0.29) % 1.0, H, r0, seed=270 + i * 1.7, rate=6, embers=emb, ember_every=2,
                  temp=0.72, anchor=False, lean=lean)
    fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    return L


def player_embers(k, n=8):
    """liam_player_embers: 24x32, pivot (12, 30), n-frame loop (0.08): when the sky fire stops, what is
    left on him - embers clinging to his edges pulsing and dimming, sparks lifting off and dying, and
    thin smoke curling up off his shoulders and head."""
    L = blank(24, 32)
    t = k / float(n)
    rnd = np.random.RandomState(280)
    for i in range(12):
        side = -1 if i % 2 else 1
        x = 12 + side * (5.0 + rnd.rand() * 1.5)
        y = 8 + rnd.rand() * 21
        pulse = 0.5 + 0.5 * math.sin(TAU * (t + rnd.rand()))
        plot(L, x, y, 'β' if pulse > 0.7 else ('γ' if pulse > 0.35 else 'δ'))
        if pulse > 0.8:
            plot(L, x, y - 1, 'δ')
    for i in range(4):
        life = (t + i / 4.0) % 1.0
        x = 12 + (i - 1.5) * 3.5 + math.sin(life * 5 + i) * 1.5
        y = 12 - life * 12
        c = 'β' if life < 0.25 else ('δ' if life < 0.5 else ('ε' if life < 0.75 else 'ϖ'))
        plot(L, x, y, c)
    for i, x0 in enumerate((8, 12, 16)):
        for j in range(9):
            ph = (t + i * 0.3 + j * 0.06) % 1.0
            x = x0 + math.sin(j * 0.7 + t * TAU + i) * (0.6 + j * 0.15)
            y = 6 - j * 0.9 + (i % 2)
            if y >= 0 and ph < 0.85 and (j + k) % 3 != 0:
                plot(L, x, y, FI.SMOKE_THIN[min(3, j // 3)])
    return L


def extinguish48(k, n=8):
    """liam_extinguish: 48x48, pivot (24, 40) = the player's feet, n frames once (0.5 s): the water hits
    him - the flames flinch and shrink, a hiss of steam bursts out round him and billows up, the embers
    are knocked off and die as they fall, the steam tears into wisps."""
    L = blank(48, 48)
    u = k / float(n - 1)
    t = k / 8.0
    fd = FI.Field(48, 48)
    emb = []
    p = max(0.0, 1.0 - u * 2.2)
    if p > 0:
        for i, (bx, by) in enumerate(((18.8, 39), (18.4, 32), (19, 24), (29.2, 39), (29.6, 32), (29, 24),
                                      (21.5, 17), (26.5, 17), (24, 16))):
            FI.tongue(fd, bx, by, (t + i * 0.23) % 1.0, (4 + 5 * p) * (0.85 + 0.1 * (i % 3)), 1.0 + 0.8 * p,
                      seed=290 + i * 1.3, embers=emb, temp=0.4 + 0.4 * p, anchor=False)
        fd.render(L)
    FI.draw_embers(L, emb, smoke_ramp=FI.SMOKE_THIN)
    # embers knocked off him, falling and dying on the way down
    rnd = np.random.RandomState(291)
    for i in range(9):
        x0 = 24 + (rnd.rand() - 0.5) * 16
        y0 = 16 + rnd.rand() * 20
        life = u * 1.4 - 0.12 - i * 0.04
        if 0 < life < 1:
            x = x0 + (x0 - 24) * 0.25 * life
            y = y0 + life * life * 16
            plot(L, x, y, 'β' if life < 0.25 else ('δ' if life < 0.5 else ('ε' if life < 0.75 else 'ϖ')))
    # the hiss: steam bursting out sideways first, then billowing up and tearing apart
    if k >= 1:
        v = (k - 1) / float(n - 2)
        for i, (x, y) in enumerate(((13, 34), (35, 33), (24, 26), (16, 20), (32, 18), (24, 11), (9, 26), (39, 25))):
            born = i * 0.07
            if v < born:
                continue
            w = (v - born) / (1 - born)
            FI.puff(L, x + (x - 24) * 0.3 * w, y - w * 8, 2.8 + 3.8 * min(1.0, w * 1.6), ramp=FI.STEAM,
                    dissolve=max(0.0, w - 0.4) * 1.5, seed=300 + i)
    return L


def water_jet16(k, n=6):
    """liam_water_jet: a 16x16 body tile, seamless along x, pivot (0, 8), n-frame loop (0.05), laid along
    the jet from the staff tip to the player: a hard jet with a bright core, white streaks racing along
    it, its skin bulging as pulses run down it, spray flicking off both edges."""
    L = blank(16, 16)
    X, Y = R.centres(16, 16)
    t = k / float(n)
    ph = (X / 16.0 - t) * TAU
    half = 4.4 + 0.8 * np.sin(ph) + 0.4 * np.sin(ph * 2 + 1.1)
    cy = 8 + 0.35 * np.sin(ph)
    d = np.abs(Y - cy)
    L[d <= half] = '%'
    L[d <= half - 1.0] = '='
    L[d <= half - 2.2] = '+'
    L[d <= half - 3.2] = 'l'
    L[(Y < cy) & (d <= half) & (d > half - 1.0)] = '+'
    L[(((X - t * 32) % 8) < 3) & (d <= 1.2)] = 'W'
    rnd = np.random.RandomState(7)
    for i in range(6):
        x0 = (rnd.randint(0, 16) - t * 16 * (1 + i % 2)) % 16
        side = -1 if i % 2 else 1
        plot(L, x0, 8 + side * (5.6 + (k + i) % 2), 'l' if (k + i) % 2 else 'W')
    return L


# ================================================================== the design table (for anchors.json)
DESIGN = {
    'tornado_form': dict(fn='tornado_form', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=6, times=[0.08] * 6,
                         loop=False, note='plays once where each gust lands; then tornado_air'),
    'tornado_air': dict(fn='tornado_air', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=8, times=[0.07] * 8, loop=True),
    'tornado_ignite': dict(fn='tornado_ignite', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=6,
                           times=[0.1, 0.12, 0.12, 0.12, 0.12, 0.14], loop=False,
                           note='frame 0 = the spark arrives at the foot; then tornado_fire'),
    'tornado_fire': dict(fn='tornado_fire', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=8, times=[0.07] * 8, loop=True),
    'tornado_spew': dict(fn='tornado_spew', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=5,
                         times=[0.1, 0.08, 0.08, 0.08, 0.08], loop=False,
                         note='every 1.5 s instead of the loop; spawn the quake ring on frame 1 (radius 20 texels '
                              '= 60 px at frame 3)'),
    'tornado_die': dict(fn='tornado_die', size=(TN.TW, TN.TH), pivot=TN.PIVOT, frames=6, times=[0.1] * 6, loop=False),
    'fire_ring': dict(fn='ring_sheet', size=(RW, RH), pivot=RING_PIVOT, frames=8, rows=7, times=[0.08] * 8, loop=True,
                      note='BixbyQuakeRingScript format: rows by screen tangent (RING_ROW_TANGENTS), rows 1-5 rise '
                           'to the right and flip where the ring falls; neighbours one frame apart'),
    'steam_puff': dict(fn='steam_puff', size=(24, 40), pivot=(12, 38), frames=8, times=[0.1] * 8, loop=False),
    'steam_wisp': dict(fn='wisp', size=(16, 40), pivot=(8, 39), frames=8, times=[0.1] * 8, loop=True),
    'steam_vent': dict(fn='steam_vent', size=(32, 48), pivot=(16, 46), frames=8, times=[0.09] * 8, loop=True),
    'fog_screen': dict(fn='fog_screen', size=(FOG_W, FOG_H), pivot=(0, 0), frames=4, loop=None,
                       note='4 densities (not an animation): scroll ~8 px/s sideways, crossfade upward'),
    'triangle': dict(fn='triangle_dir', size=(TRI, TRI), pivot=(16, 16), frames=6, rows=8,
                     times=[0.04, 0.05, 0.08, 0.08, 0.08, 0.06], loop=False,
                     note='rows = 8 directions from right, clockwise (0, 45 ... 315 degrees); hold 2-4 while '
                          'it waits, 5 on the lunge'),
    'water_jet': dict(fn='water_jet', size=(32, 16), pivot=(0, 8), frames=6, times=[0.05] * 6, loop=True,
                      note='tile along the jet, pointing right'),
    'water_head': dict(fn='water_head', size=(40, 40), pivot=(10, 20), frames=6, times=[0.06] * 6, loop=True),
    'water_trail': dict(fn='water_trail', size=(24, 32), pivot=(12, 31), frames=4, times=[0.06] * 4, loop=True),
    'water_muzzle': dict(fn='water_muzzle', size=(40, 40), pivot=(20, 20), frames=5, times=[0.05] * 5, loop=False),
    'extinguish': dict(fn='extinguish', size=(40, 44), pivot=(20, 40), frames=8, times=[0.07] * 8, loop=False),
    'flame_overlay': dict(fn='flame_overlay', size=(28, 44), pivot=(14, 41), frames=8, times=[0.07] * 8, loop=True),
    'column_edge': dict(fn='column_edge', size=(12, 48), pivot=(0, 0), frames=6, times=[0.07] * 6, loop=True,
                        note='seamless vertically; right edge of the column, flip for the left'),
    'fire_hit': dict(fn='fire_hit', size=(56, 32), pivot=(28, 14), frames=6, times=[0.06] * 6, loop=True),
    'ignite_spark': dict(fn='ignite_spark', size=(16, 16), pivot=(8, 8), frames=4, times=[0.05] * 4, loop=True),
    'ember_trail': dict(fn='ember_trail', size=(8, 8), pivot=(4, 4), frames=4, times=[0.06] * 4, loop=False),
    'gust_bolt': dict(fn='gust_bolt', size=(40, 24), pivot=(30, 12), frames=6, times=[0.05] * 6, loop=True),
    'blow_cone': dict(fn='blow_cone', size=(48, 40), pivot=(24, 2), frames=6, times=[0.06] * 6, loop=False),
    'pull_swirl': dict(fn='pull_swirl', size=(SW, SH), pivot=SWIRL_PIVOT, frames=8, rows=2, times=[0.07] * 8, loop=True,
                       note='row 0 water (fire phase), row 1 ice spray (air phase)'),
}
