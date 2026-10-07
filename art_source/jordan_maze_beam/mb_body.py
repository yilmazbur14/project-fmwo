"""The beam's body and its dissipation: seamless, horizontally tileable strips for a Line2D.

BODY: W x H = 96 x 32 texels a frame, 8 frames, the content flowing +x (towards the player: the
Line2D runs from the muzzle) by FLOW = 12 texels a frame, so frame 8 would be frame 0 again and any
two tiles side by side meet without a seam. The line's centre is the texture's middle (between rows
15 and 16). Vertically near-symmetric, because a Line2D turns its texture upside down on runs going
left. GLOW: 96 x 48, the same centre (between rows 23 and 24), additive, under the body.
"""
import math

import numpy as np

import mb_core as C

W, H = 96, 32
GH = 48
FRAMES = 8
FLOW = W // FRAMES          # 12 texels a frame
CY = 16.0                   # the centre line, between rows 15 and 16


def _poly(g, pts, c, wrap=True):
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        C.draw_line(g, xa, ya, xb, yb, c, wrap_x=wrap)


def _smooth(seed, harmonics, amp=1.0):
    return C.noise1_periodic(W, W, harmonics, seed) * amp


def _band(ad, edges):
    """The band a texel `ad` rows off the centre is in, given the band edges (ascending)."""
    for i, e in enumerate(edges):
        if ad <= e:
            return i
    return len(edges)


def _sawtooth(seed, lo_len, hi_len, lo_h, hi_h):
    """Swept-back spikes along the rim, periodic in W: each tooth's tip at its back (-x), its long
    slope running forward (+x), so the rim reads as torn back by the beam's speed."""
    r = C.rng('saw-%s' % seed)
    out = np.zeros(W)
    x = 0
    teeth = []
    while x < W:
        L = int(r.integers(lo_len, hi_len + 1))
        teeth.append((x, min(L, W - x), float(r.uniform(lo_h, hi_h))))
        x += L
    for x0, L, h in teeth:
        for i in range(L):
            out[(x0 + i) % W] = h * (1.0 - i / max(L, 1)) ** 1.6
    return out


def _jag(r, x0, length, y0, lo, hi, big=3):
    """An irregular lightning path: runs of 1-5 texels, kinks of 1-2 and now and then a jump."""
    pts = [(x0, y0)]
    x, y = x0, y0
    while x < x0 + length:
        x += int(r.choice([1, 1, 2, 2, 3, 5]))
        step = int(r.choice([-1, 1, -2, 2, -1, 1, big, -big]))
        y = int(np.clip(y + step, lo, hi))
        pts.append((x, y))
    return pts


# ----------------------------------------------------------------------------------------------- take A

HELIX_PERIOD = 48           # two twists a tile
HELIX_AMP = 8.5


def _profile_a(pal, f, variant):
    """Four bold bands (white core, red-hot, crimson, maroon) whose edges interlock in tongues, then
    black thorns swept back off the rim."""
    s = FLOW * f
    v = variant * 100

    def flow(seed, harmonics, amp):
        return np.roll(_smooth(seed + v, harmonics, amp), s)

    fl = C.rng('bodyA-flicker-%d-%d' % (variant, f))
    sides = {}
    for side, o in (('t', 0), ('b', 10)):
        core = 2.6 + flow(1 + o, (2, 3, 5), 0.7)
        hot = core + 2.2 + flow(2 + o, (3, 4, 7), 1.3)
        mid = hot + 3.4 + flow(3 + o, (2, 5, 8), 1.6)
        rim = mid + 2.0 + flow(4 + o, (3, 6), 0.8)
        thorn = np.roll(_sawtooth('A%s%d' % (side, variant), 4, 11, 1.5, 5.0), s)
        thorn = thorn + fl.integers(-1, 2, W) * 0.7 * (thorn > 1.0)
        sides[side] = (core, hot, mid, rim, thorn)
    g = C.blank(W, H)
    for x in range(W):
        for y in range(H):
            d = CY - (y + 0.5)
            core, hot, mid, rim, thorn = sides['t' if d > 0 else 'b']
            ad = abs(d)
            if ad <= core[x]:
                k = 'w'
            elif ad <= core[x] + 0.9:
                k = 'h'
            elif ad <= hot[x]:
                k = 's'
            elif ad <= mid[x]:
                k = 'c'
            elif ad <= rim[x]:
                k = 'm'
            elif ad <= rim[x] + max(0.0, thorn[x]):
                k = 'v'
            else:
                continue
            g[y, x] = pal[k]
    return g


def _helix(f, variant, strand):
    """One strand of the black-lightning coil: a flowing twist, two a tile, its reach swelling and
    shrinking, made jagged and re-jagged every frame so it crackles as it drills forward. Returns
    the polyline and, per point, whether that part passes in front of the core."""
    s = FLOW * f
    r = C.rng('helixA-%d-%d-%d' % (variant, strand, f))
    phase0 = 0.0 if strand == 0 else math.pi
    pts, front = [], []
    x = 0
    while x <= W:
        u = x - s
        ph = 2 * math.pi * u / HELIX_PERIOD + phase0 + 0.55 * math.sin(2 * math.pi * u / W)
        amp = HELIX_AMP + 1.6 * math.sin(2 * math.pi * u / W + 1.3 * strand)
        jag = float(r.choice([-2, -1, -1, 0, 0, 1, 1, 2]))
        pts.append((x, int(round(CY - 0.5 + amp * math.sin(ph) + jag))))
        front.append(math.cos(ph) > 0)
        x += int(r.choice([2, 3, 3, 4]))
    pts.append((W, pts[0][1]))
    front.append(front[0])
    return pts, front


def body_a(pal, f, variant=0):
    """Take A, Hellbolt: a searing white core in a crimson corona torn back into black thorns by its
    speed, with a double helix of black lightning coiled round it and drilling towards the player,
    forks breaking out into the glow, and embers that live and die off the rim. Frame f of FRAMES."""
    s = FLOW * f
    g = _profile_a(pal, f, variant)
    body = g > 0

    # flowing streaks: red-hot dashes in the crimson, dark matter in the maroon
    sr = C.rng('bodyA-streaks-%d' % variant)
    for k in range(24):
        x0 = int(sr.integers(0, W))
        up = k % 2 == 0
        off = float(sr.uniform(5.5, 11.5))
        y = int(math.floor(CY - off)) if up else int(math.floor(CY + off))
        length = int(sr.integers(4, 14))
        for i in range(length):
            x = (x0 + s + i) % W
            here = g[y, x]
            if here == pal['c']:
                g[y, x] = pal['r'] if k % 3 else pal['d']
            elif here == pal['m']:
                g[y, x] = pal['d'] if k % 2 else pal['v']

    # the coil: two strands of black lightning wound round the core, each crossing in front of it on
    # half its twist (black, a red-hot halo) and behind it on the other (hidden by the core, dim in
    # the corona)
    for strand in (0, 1):
        pts, front = _helix(f, variant, strand)
        back = C.blank(W, H)
        fore = C.blank(W, H)
        for i in range(len(pts) - 1):
            (xa, ya), (xb, yb) = pts[i], pts[i + 1]
            C.draw_line(fore if front[i] else back, xa, ya, xb, yb, 1, wrap_x=True)
        hidden = (g == pal['w']) | (g == pal['h'])
        mb = (back > 0) & ~hidden & body
        g[mb & (g == pal['s'])] = pal['c']
        g[mb & (g == pal['c'])] = pal['m']
        g[mb & ((g == pal['m']) | (g == pal['v']))] = pal['k']
        mf = fore > 0
        ring = C.dilate_wrap(mf, 1) & ~mf & body
        dark = (g == pal['c']) | (g == pal['d']) | (g == pal['m']) | (g == pal['v']) | (g == pal['r'])
        g[ring & dark] = pal['s']
        g[mf] = pal['k']

    r = C.rng('bodyA-bolts-%d-%d' % (variant, f))
    # forks breaking off the helix out through the rim into the glow
    for b in range(3):
        up = r.random() < 0.5
        x0 = int(r.integers(0, W))
        col = np.nonzero(body[:, x0])[0]
        if len(col) == 0:
            continue
        y0 = int(CY - 6) if up else int(CY + 5)
        pts = [(x0, y0)]
        x, y = x0, y0
        for j in range(int(r.integers(3, 6))):
            x += int(r.choice([-1, 1, 2, 2, 3]))
            y += (-1 if up else 1) * int(r.integers(1, 3))
            pts.append((x, int(np.clip(y, 0, H - 1))))
        _black_bolt(g, pal, pts, body)

    # embers that live and die: born at the rim, thrown out and left behind, cooling as they go
    er = C.rng('bodyA-embers-%d' % variant)
    for e in range(14):
        born = int(er.integers(0, FRAMES))
        life = int(er.integers(3, 5))
        age = (f - born) % FRAMES
        if age >= life:
            continue
        up = e % 2 == 0
        x_birth = int(er.integers(0, W))
        x = (x_birth + FLOW * born + (FLOW - 5) * age) % W
        edge = CY - 12 if up else CY + 12
        y = int(round(edge + (-1 if up else 1) * (0.5 + 1.2 * age)))
        if 0 <= y < H and g[y, x] == 0:
            g[y, x] = pal[['h', 'p', 's', 'r'][min(age, 3)]]
            if age == 0 and x > 0 and g[y, x - 1] == 0:
                g[y, x - 1] = pal['s']
    return g


def _black_bolt(g, pal, pts, body, spark=True):
    """Black lightning: black inside the beam with a red-hot halo on its dark bands (black on the
    white core needs none); outside it, black with a maroon rim, so it reads as a silhouette on the
    glow and still shows without it."""
    bolt = C.blank(W, H)
    _poly(bolt, pts, 1)
    m = bolt > 0
    ring = C.dilate_wrap(m, 1) & ~m
    dark = (g == pal['c']) | (g == pal['d']) | (g == pal['m']) | (g == pal['v']) | (g == pal['r'])
    g[ring & body & dark] = pal['s']
    g[ring & ~body & (g == 0)] = pal['m']
    g[m] = pal['k']
    if spark:
        tx, ty = pts[-1]
        if 0 <= ty < H:
            g[ty, tx % W] = pal['h']


def glow_a(gpal, f, variant=0):
    """The additive haze under take A's body: GH rows, three steps, breathing with the flow."""
    s = FLOW * f
    n = np.roll(C.fbm_periodic(W, GH, [(24, 6, 1.0), (12, 3, 0.5)], 91 + variant), s, axis=1)
    ys = np.arange(GH)[:, None] + 0.5
    ady = np.abs(ys - GH / 2.0)
    I = 1.0 - ady / 23.0 + 0.10 * n + 0.03 * math.sin(f * math.pi / 2)
    g = C.blank(W, GH)
    g[I > 0.08] = gpal['1']
    g[I > 0.30] = gpal['2']
    g[I > 0.46] = gpal['3']
    return g
