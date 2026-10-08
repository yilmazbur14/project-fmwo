"""The beam's end: its dissipation along the line, the particles the code emits, and the floor scorch.

DISSIPATION: the body's 96 x 32 strip on the same Line2D, 8 frames played once: the beam breaks up
along its whole length (tileable, like the body).
PARTICLES, separate sheets for rising embers and smoke the code emits along the line (they rise up
the screen whichever way the line runs): EMBER 8 x 8 x 6 frames, SMOKE 16 x 16 x 6 frames, each
played once over its life, pivot at the centre.
SCORCH: 96 x 16 x 4 frames (hot, cooling, cooler, char), a strip on a Line2D laid on the floor line
under the route (the soles line, not lifted), held until the lights are up.
"""
import math

import numpy as np

import mb_core as C
import mb_body as B

W, H, CY = B.W, B.H, B.CY
DISS_FRAMES = 8
EMBER = 8
EMBER_FRAMES = 6
SMOKE = 16
SMOKE_FRAMES = 6
SW, SH = 96, 16
SCORCH_FRAMES = 4


def _fragments(seed, frac, half):
    """Half-width per column of the beam's surviving fragments: lens-shaped cinders, tapering at
    their ends, fewer, shorter and thinner as frac drops (1 = the whole beam)."""
    out = np.zeros(W)
    if frac >= 1.0:
        out[:] = half
        return out
    r = C.rng('frag-%s' % seed)
    starts = sorted(int(v) for v in r.integers(0, W, 11))
    for x0 in starts:
        L = max(2, int(round(int(r.integers(5, 13)) * frac / 0.8)))
        hmul = float(r.uniform(0.6, 1.0))
        for i in range(L):
            t = (i + 0.5) / L
            out[(x0 + i) % W] = max(out[(x0 + i) % W], half * hmul * math.sin(math.pi * t) ** 0.7)
    return out


# How each of take A's colours cools, frame by frame, as the beam breaks up.
COOL_A = [
    {'w': 'h', 'h': 's', 's': 'c', 'c': 'm', 'm': 'v', 'v': 'v', 'k': 'v', 'r': 'c', 'd': 'm', 'p': 's'},
    {'w': 's', 'h': 'c', 's': 'c', 'c': 'm', 'm': 'v', 'v': 'v', 'k': 'v', 'r': 'm', 'd': 'm', 'p': 'c'},
    {'w': 'c', 'h': 'm', 's': 'm', 'c': 'm', 'm': 'v', 'v': 'v', 'k': 'v', 'r': 'm', 'd': 'v', 'p': 'm'},
    {'w': 'm', 'h': 'm', 's': 'm', 'c': 'v', 'm': 'v', 'v': 'v', 'k': 'v', 'r': 'v', 'd': 'v', 'p': 'm'},
    {'w': 'm', 'h': 'v', 's': 'v', 'c': 'v', 'm': 'v', 'v': 'v', 'k': 'v', 'r': 'v', 'd': 'v', 'p': 'v'},
]


def dissipate_a(pal, f, variant=0):
    """Take A: the core gutters out, the beam snaps into cinders that shrink and cool while black
    smoke puffs up along the line and embers scatter off it and die."""
    g = C.blank(W, H)
    base = B._profile_a(pal, 0, variant)
    ys = np.arange(H)[:, None] + 0.5
    ady = np.abs(ys - CY) * np.ones((1, W))
    n = C.fbm_periodic(W, H, [(12, 4, 1.0), (6, 2, 0.5)], 801 + variant)
    half = [9.0, 7.5, 5.5, 3.6, 2.2, 0.0, 0.0, 0.0][f]
    frac = [1.0, 0.8, 0.62, 0.45, 0.3, 0.0, 0.0, 0.0][f]
    hw = np.roll(_fragments('A%d' % variant, frac, half), 2 * f)
    erode = n > [-2.0, -0.45, -0.25, -0.1, 0.05, 2, 2, 2][f]
    body = (ady <= hw[None, :] + 0.9 * n * (hw[None, :] > 0)) & (hw[None, :] > 0) & erode
    if f < len(COOL_A):
        inv = {i: k for k, i in pal.idx.items()}
        for y in range(H):
            for x in range(W):
                if body[y, x] and base[y, x]:
                    g[y, x] = pal[COOL_A[f].get(inv[int(base[y, x])], 'v')]
    # smoke puffing up along the line: blobs that swell, drift off the line and thin out
    sr = C.rng('dissA-smoke-%d' % variant)
    xs_ = np.arange(W)[None, :] + 0.5
    for k in range(9):
        x0 = float(sr.integers(0, W))
        side = -1 if k % 2 else 1
        born = int(sr.integers(0, 3))
        age = f - born
        if age < 0:
            continue
        rad = 2.0 + 1.3 * age
        cy = CY + side * (1.0 + 1.6 * age)
        dxw = (xs_ - x0 + W / 2) % W - W / 2
        blob = (dxw / (rad * 1.4)) ** 2 + ((ys - cy) / rad) ** 2 < 1.0
        thin = n > [-2, -2, -0.5, -0.25, -0.05, 0.1, 0.25, 0.4][f] + 0.08 * age
        puff = blob & thin & (g == 0)
        g[puff] = pal['v']
        lit = puff & ((ys - cy) * side < -rad * 0.35) & (age < 4)
        g[lit] = pal['m']
    # embers thrown off both sides of the line, cooling and dying
    er = C.rng('dissA-embers-%d' % variant)
    for k in range(30):
        x0 = float(er.integers(0, W))
        side = -1 if k % 2 else 1
        born = int(er.integers(0, 4))
        life = int(er.integers(3, 6))
        age = f - born
        if age < 0 or age >= life:
            continue
        drift = float(er.uniform(-1.2, 1.2))
        x = int(round(x0 + drift * age)) % W
        y = int(round(CY - 0.5 + side * (1.5 + float(er.uniform(1.4, 2.6)) * (age + 1))))
        if 0 <= y < H:
            g[y, x] = pal[['h', 'p', 's', 'r', 'c', 'm'][min(age, 5)]]
    return g


def ember_a(pal, f):
    """One ember rising: white-hot with a short tail below it, cooling to an ash fleck."""
    g = C.blank(EMBER, EMBER)
    shapes = [
        [(3, 3, 'w'), (4, 3, 'h'), (3, 4, 'h'), (4, 4, 's'), (3, 5, 's'), (3, 6, 'c')],
        [(3, 3, 'h'), (4, 3, 'p'), (3, 4, 's'), (3, 5, 'c')],
        [(3, 3, 'p'), (3, 4, 's'), (3, 5, 'm')],
        [(3, 3, 's'), (3, 4, 'c')],
        [(3, 3, 'r'), (4, 4, 'm')],
        [(3, 3, 'm')],
    ]
    for x, y, k in shapes[f]:
        g[y, x] = pal[k]
    return g


def smoke_a(pal, f):
    """One puff of black smoke lit crimson from below, swelling and thinning to nothing."""
    g = C.blank(SMOKE, SMOKE)
    c = SMOKE / 2.0
    ys, xs = np.mgrid[0:SMOKE, 0:SMOKE]
    n = C.fbm_periodic(SMOKE, SMOKE, [(4, 4, 1.0)], 881, period_x=SMOKE)
    rad = [2.5, 3.5, 4.5, 5.5, 6.3, 7.0][f]
    blob = ((xs + 0.5 - c) / (rad * 1.1)) ** 2 + ((ys + 0.5 - c) / rad) ** 2 + 0.25 * n < 1.0
    thin = n > [-2, -2, -0.4, -0.2, 0.05, 0.25][f]
    m = blob & thin
    g[m] = pal['v']
    lit = m & (ys + 0.5 > c + rad * 0.3)
    if f < 3:
        g[lit] = pal['m']
    if f == 0:
        g[int(c), int(c)] = pal['c']
    return g


def _cracks(seed, cy):
    """A jagged burn seam wandering along the band, with short branches off it."""
    r = C.rng(seed)
    crack = C.blank(SW, SH)
    y = int(cy)
    pts = [(0, y)]
    x = 0
    while x < SW:
        x += int(r.choice([2, 3, 3, 4, 5]))
        y = int(np.clip(y + r.choice([-1, 0, 1, 1, -1]), cy - 2, cy + 1))
        pts.append((x, y))
    pts[-1] = (SW, pts[0][1])
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        C.draw_line(crack, xa, ya, xb, yb, 1, wrap_x=True)
    for k in range(6):
        i = int(r.integers(1, len(pts) - 1))
        bx, by = pts[i]
        sgn = -1 if k % 2 else 1
        ex = bx + int(r.choice([-3, -2, 2, 3]))
        ey = by + sgn * int(r.integers(2, 4))
        C.draw_line(crack, bx, by, ex, ey, 1, wrap_x=True)
    return crack > 0


def _char_band(seed):
    cy = SH / 2.0
    ys = np.arange(SH)[:, None] + 0.5
    edge_t = 4.2 + C.noise1_periodic(SW, SW, (3, 5, 9, 13), seed) * 1.6
    edge_b = 4.2 + C.noise1_periodic(SW, SW, (3, 5, 9, 13), seed + 6) * 1.6
    dy = ys - cy
    char = ((dy < 0) & (-dy <= edge_t[None, :])) | ((dy >= 0) & (dy <= edge_b[None, :]))
    inner = ((dy < 0) & (-dy <= edge_t[None, :] - 1.5)) | ((dy >= 0) & (dy <= edge_b[None, :] - 1.5))
    return char, inner


def scorch_a(pal, f, variant=0):
    """Take A: the path burnt into the floor: a charred band with a ragged, smouldering edge, jagged
    cracks through it glowing white-hot, then cooling out to char."""
    g = C.blank(SW, SH)
    char, inner = _char_band(901 + variant)
    g[char] = pal[['m', 'm', 'v', 'v'][f]]
    g[inner] = pal['k']
    m = _cracks('scorchA-%d' % variant, SH / 2.0)
    hot = [('h', 's'), ('s', 'r'), ('r', 'c'), ('d', 'm')][f]
    g[m] = pal[hot[1]]
    every3 = np.zeros((SH, SW), bool)
    every3[:, ::3] = True
    g[m & every3] = pal[hot[0]]
    return g
