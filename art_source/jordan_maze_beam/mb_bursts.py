"""The beam's one-shot pieces: the corner burst, the impact and its floor shockwave, the charge and its
release, and their additive glows. Every piece is centred on its pivot (see each size below).

CORNER: 64 x 64, 6 frames, pivot (32, 32) on the corner. Drawn for the turn "running right, then down":
its splash goes to the outer corner, up-right. For any turn, outer = incoming - outgoing (unit
vectors): flip_h when outer.x < 0, flip_v when outer.y > 0.
"""
import math

import numpy as np

import mb_core as C

CW = 64
CORNER_FRAMES = 6


def _polar(w, h, cx, cy):
    ys, xs = np.mgrid[0:h, 0:w]
    dx = xs + 0.5 - cx
    dy = ys + 0.5 - cy
    return dx, dy, np.sqrt(dx * dx + dy * dy), np.arctan2(dy, dx)


def _ang_diff(a, b):
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return np.abs(d)


def _jag_ray(r, x0, y0, ang, length, spread=0.45, step=(2, 4)):
    """A jagged lightning ray from (x0, y0) along `ang`, kinking either side of it."""
    pts = [(x0, y0)]
    x, y = float(x0), float(y0)
    travelled = 0.0
    while travelled < length:
        st = float(r.integers(step[0], step[1] + 1))
        a = ang + float(r.uniform(-spread, spread)) * (1 if r.random() < 0.5 else -1)
        x += st * math.cos(a)
        y += st * math.sin(a)
        travelled += st
        pts.append((int(round(x)), int(round(y))))
    return pts


def _draw_bolt(g, pal, pts, halo_in_body=True, rim_out='m', tip='h'):
    h, w = g.shape
    m = C.blank(w, h)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        C.draw_line(m, xa, ya, xb, yb, 1)
    mb = m > 0
    ring = C.dilate(mb, 1) & ~mb
    inside = g > 0
    dark = np.isin(g, [pal[k] for k in ('c', 'm', 'v', 'd', 'r')])
    if halo_in_body:
        g[ring & inside & dark] = pal['s']
    g[ring & ~inside] = pal[rim_out]
    g[mb] = pal['k']
    tx, ty = pts[-1]
    if tip and 0 <= ty < h and 0 <= tx < w:
        g[ty, tx] = pal[tip]


def _bands(g, pal, I, table):
    for t, k in table:
        g[I > t] = pal[k]


# ----------------------------------------------------------------------------------------------- corner A

OUTER = -math.pi / 4          # the outer corner, up-right, in screen angles (y down)


def spike(g, pal, cx, cy, ang, length, width, keys=('s', 'h', 'w')):
    """A sharp triangular spike from (cx, cy) along `ang`: an outer colour, a hotter inner one and
    a white-hot spine."""
    h, w = g.shape
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    tipx, tipy = cx + ca * length, cy + sa * length
    for scale, key in ((1.0, keys[0]), (0.55, keys[1])):
        hw = width * scale / 2.0
        ln = length * (1.0 if scale == 1.0 else 0.8)
        poly = [(cx + nx * hw, cy + ny * hw), (cx + ca * ln, cy + sa * ln), (cx - nx * hw, cy - ny * hw)]
        m = C.polygon_mask(w, h, poly)
        g[m] = pal[key]
    for t in np.arange(0, length * 0.6, 0.5):
        x, y = int(math.floor(cx + ca * t)), int(math.floor(cy + sa * t))
        if 0 <= x < w and 0 <= y < h:
            g[y, x] = pal[keys[2]]


def corner_a(pal, f, variant=0):
    """Take A: the beam slams into the turn: a white-hot star flash, a shock ring that breaks into
    crimson shards and flame thrown to the outer corner with black lightning, then smoke and embers."""
    g = C.blank(CW, CW)
    cx = cy = CW / 2.0
    dx, dy, d, a = _polar(CW, CW, cx, cy)
    r = C.rng('cornerA-%d-%d' % (variant, f))
    bias = np.cos(_ang_diff(a, OUTER))           # 1 toward the outer corner, -1 away
    pb = np.clip(bias, 0, 1)
    n = C.fbm_periodic(CW, CW, [(8, 8, 1.0), (4, 4, 0.5)], 511 + 7 * f + variant, period_x=CW)
    if f == 0:
        # the flash: long spikes along the two runs and out to the outer corner, short ones between
        for ang, ln, wd in ((0, 26, 9), (-math.pi / 2, 25, 9), (math.pi, 15, 7), (math.pi / 2, 16, 7),
                            (OUTER, 30, 11), (OUTER + math.pi, 11, 6), (OUTER + math.pi / 2, 13, 6),
                            (OUTER - math.pi / 2, 13, 6)):
            spike(g, pal, cx, cy, ang, ln, wd)
        _bands(g, pal, 1.0 - d / 9.5, ((0.0, 'h'), (0.3, 'w')))
    elif f == 1:
        # the shock ring, fat and white-hot on its front, and the fan of flame bursting through it
        fan = (d < 13 + 13 * pb ** 1.5 + 3 * n) & (pb > 0.2)
        g[fan] = pal['c']
        g[fan & (d < 10 + 9 * pb ** 1.5 + 2 * n)] = pal['s']
        _bands(g, pal, 1.0 - d / 8.5, ((0.0, 's'), (0.3, 'h'), (0.55, 'w')))
        ring = (d > 9.0) & (d < 12.0 + 1.5 * pb)
        g[ring] = pal['h']
        g[ring & (d > 11.0 + 1.5 * pb)] = pal['s']
        for k in range(3):
            ang = OUTER + float(r.uniform(-1.0, 1.0))
            _hot_bolt(g, pal, _jag_ray(r, int(cx + 12 * math.cos(ang)), int(cy + 12 * math.sin(ang)), ang, 12, 0.55))
    elif f == 2:
        fan = (d < 15 + 14 * pb ** 1.3 + 4 * n) & ((pb > 0.1) | (d < 14))
        g[fan] = pal['m']
        g[fan & (d < 13 + 11 * pb ** 1.3 + 3 * n)] = pal['c']
        g[fan & (d < 9 + 7 * pb ** 1.3 + 2 * n)] = pal['s']
        g[d < 6.5] = pal['c']
        g[d < 4.0] = pal['s']
        ring = (d > 15.0 + 2 * pb) & (d < 17.0 + 2 * pb) & (n > -0.35)
        g[ring] = pal['s']
        g[ring & (d < 16.0 + 2 * pb)] = pal['h']
        for k in range(4):
            ang = OUTER + float(r.uniform(-1.1, 1.1))
            _hot_bolt(g, pal, _jag_ray(r, int(cx + 6 * math.cos(ang)), int(cy + 6 * math.sin(ang)), ang, 22, 0.55))
    elif f == 3:
        # flame licks torn off toward the outer corner, holed through, the centre already out
        lick = (d < 11 + 14 * pb ** 1.3 + 3 * n) & (d > 6.0 + 3 * n) & (pb > 0.25) & (n > -0.15)
        g[lick] = pal['m']
        g[lick & (n > 0.2)] = pal['c']
        g[lick & (n > 0.45) & (d < 14 + 8 * pb)] = pal['s']
    elif f == 4:
        wisp = (d < 14 + 12 * pb + 3 * n) & (d > 10 + 3 * n) & (pb > 0.3) & (n > 0.25)
        g[wisp] = pal['v']
        g[wisp & (n > 0.45)] = pal['m']
    elif f == 5:
        wisp = (d < 16 + 12 * pb + 3 * n) & (d > 13 + 4 * n) & (pb > 0.4) & (n > 0.45)
        g[wisp] = pal['v']
    # sparks and embers flung to the outer corner, living through the burst
    er = C.rng('cornerA-embers-%d' % variant)
    for k in range(16):
        ang = OUTER + float(er.normal(0, 0.7))
        speed = float(er.uniform(4.0, 7.0))
        born = int(er.integers(0, 2))
        age = f - born
        if age < 0 or age > 4:
            continue
        dist = 8 + speed * age
        x = int(round(cx - 0.5 + dist * math.cos(ang)))
        y = int(round(cy - 0.5 + dist * math.sin(ang) + 0.5 * age * age))
        if 0 <= x < CW and 0 <= y < CW and g[y, x] in (0, pal['v']):
            g[y, x] = pal[['w', 'h', 'p', 's', 'r'][age]]
            if age <= 1 and x - 1 >= 0 and g[y, x - 1] == 0:
                g[y, x - 1] = pal['s']
    return g


def _hot_bolt(g, pal, pts):
    """Black lightning: one texel of black with a red-hot halo where it crosses fire and a crimson
    rim where it crosses the dark, a white spark at its tip."""
    h, w = g.shape
    m = C.blank(w, h)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        C.draw_line(m, xa, ya, xb, yb, 1)
    mb = m > 0
    ring = C.dilate(mb, 1) & ~mb
    inside = g > 0
    hot = np.isin(g, [pal['w'], pal['h']])
    g[ring & inside & ~hot] = pal['s']
    g[ring & ~inside] = pal['c']
    g[mb] = pal['k']
    tx, ty = pts[-1]
    if 0 <= ty < h and 0 <= tx < w:
        g[ty, tx] = pal['w']


def corner_glow_a(gpal, f):
    g = C.blank(CW, CW)
    _, _, d, a = _polar(CW, CW, CW / 2.0, CW / 2.0)
    bias = np.cos(_ang_diff(a, OUTER))
    size = [22, 26, 26, 14, 0, 0][f]
    if size == 0:
        return g
    I = 1.0 - d / (size * (1 + 0.35 * np.clip(bias, 0, 1)))
    g[I > 0.0] = gpal['1']
    g[I > 0.35] = gpal['2']
    if f <= 2:
        g[I > 0.65] = gpal['3']
    return g


# ----------------------------------------------------------------------------------------------- impact A
# IMPACT: 112 x 112, 10 frames, pivot (56, 56) on the beam's end (the player's middle).
# RING: 128 x 48, 8 frames, pivot (64, 24) on the player's soles: a shockwave along the floor.

IW = 112
IMPACT_FRAMES = 10
RW, RH = 128, 48
RING_FRAMES = 8


def _radial_bolts(r, g, pal, cx, cy, count, r0, length, spread=0.5, drawer=None):
    for k in range(count):
        ang = 2 * math.pi * k / count + float(r.uniform(-0.25, 0.25))
        pts = _jag_ray(r, int(cx + r0 * math.cos(ang)), int(cy + r0 * math.sin(ang)), ang,
                       length * float(r.uniform(0.7, 1.15)), spread, (2, 5))
        (drawer or _hot_bolt)(g, pal, pts)
        if r.random() < 0.6 and len(pts) > 3:
            i = int(r.integers(1, len(pts) - 1))
            bx, by = pts[i]
            fork = _jag_ray(r, bx, by, ang + float(r.choice([-0.8, 0.8])), length * 0.35, spread, (2, 4))
            (drawer or _hot_bolt)(g, pal, fork)


def impact_a(pal, f, variant=0):
    """Take A: the beam lands: a white-out star, a fireball that black lightning cracks open from
    the inside out, a white shock ring, then the fire breaking into black smoke and embers."""
    g = C.blank(IW, IW)
    c = IW / 2.0
    dx, dy, d, a = _polar(IW, IW, c, c)
    r = C.rng('impactA-%d-%d' % (variant, f))
    n = C.fbm_periodic(IW, IW, [(14, 14, 1.0), (7, 7, 0.5)], 611 + 3 * f + variant, period_x=IW)
    spiky = 1.0 + 0.18 * np.cos(a * 9 + f) + 0.10 * n
    if f == 0:
        for k in range(12):
            ang = 2 * math.pi * k / 12 + (0.13 if k % 2 else 0)
            spike(g, pal, c, c, ang, 44 if k % 3 == 0 else 30, 8 if k % 3 == 0 else 5)
        _bands(g, pal, 1.0 - d / 18.0, ((0.0, 's'), (0.18, 'h'), (0.35, 'w')))
    elif f == 1:
        fire = d < 25 * spiky
        g[fire] = pal['c']
        g[d < 21 * spiky] = pal['s']
        g[d < 17 * spiky] = pal['h']
        g[d < 13] = pal['w']
        _radial_bolts(r, g, pal, c, c, 8, 6, 38)
    elif f == 2:
        g[d < 33 * spiky] = pal['m']
        g[d < 29 * spiky] = pal['c']
        g[d < 22 * spiky] = pal['s']
        g[d < 15 * spiky] = pal['h']
        g[d < 10] = pal['w']
        ring = (d > 36) & (d < 39.5)
        g[ring] = pal['h']
        g[ring & (d > 38)] = pal['s']
        _radial_bolts(r, g, pal, c, c, 9, 8, 48)
    elif f == 3:
        g[d < 37 * spiky] = pal['m']
        g[d < 32 * spiky] = pal['c']
        g[d < 22 * spiky] = pal['s']
        g[d < 11 * spiky] = pal['h']
        g[d < 6] = pal['w']
        ring = (d > 44) & (d < 46.5) & (n > -0.3)
        g[ring] = pal['s']
        g[ring & (d < 45.2)] = pal['h']
        _radial_bolts(r, g, pal, c, c, 7, 14, 40)
    elif f == 4:
        smoke = d < 40 * spiky
        g[smoke] = pal['v']
        g[smoke & (d < 34 * spiky) & (n > -0.35)] = pal['m']
        g[(d < 27 * spiky) & (n > -0.2)] = pal['c']
        g[(d < 15 * spiky) & (n > -0.1)] = pal['s']
        g[d < 5] = pal['h']
        ring = (d > 50) & (d < 52) & (n > 0.0)
        g[ring] = pal['c']
        _radial_bolts(r, g, pal, c, c, 5, 20, 26)
    elif f == 5:
        smoke = (d < 43 * spiky) & (d > 6 + 4 * n)
        g[smoke] = pal['v']
        g[smoke & (d < 34 * spiky) & (n > -0.1)] = pal['m']
        g[smoke & (d < 24 * spiky) & (n > 0.05)] = pal['c']
        g[(d < 12) & (n > 0.0)] = pal['s']
    elif f == 6:
        smoke = (d < 45 * spiky) & (d > 12 + 5 * n) & (n > -0.4)
        g[smoke] = pal['v']
        g[smoke & (n > 0.15)] = pal['m']
        g[(d < 20) & (d > 8) & (n > 0.25)] = pal['c']
    elif f == 7:
        smoke = (d < 47 * spiky) & (d > 20 + 6 * n) & (n > -0.2)
        g[smoke] = pal['v']
        g[smoke & (n > 0.35)] = pal['m']
    elif f == 8:
        smoke = (d < 49 * spiky) & (d > 30 + 6 * n) & (n > 0.05)
        g[smoke] = pal['v']
    # embers flung out, living 4 frames each
    er = C.rng('impactA-embers-%d' % variant)
    for k in range(34):
        ang = float(er.uniform(0, 2 * math.pi))
        speed = float(er.uniform(4.0, 7.5))
        born = int(er.integers(1, 5))
        age = f - born
        if age < 0 or age > 4:
            continue
        dist = 14 + speed * (age + 1)
        x = int(round(c - 0.5 + dist * math.cos(ang)))
        y = int(round(c - 0.5 + dist * math.sin(ang) + 0.7 * age * age))
        if 0 <= x < IW and 0 <= y < IW and g[y, x] in (0, pal['v'], pal['m']):
            g[y, x] = pal[['w', 'h', 'p', 's', 'r'][age]]
    return g


def impact_glow_a(gpal, f):
    g = C.blank(IW, IW)
    _, _, d, _ = _polar(IW, IW, IW / 2.0, IW / 2.0)
    size = [50, 56, 58, 54, 46, 34, 20, 0, 0, 0][f]
    if size == 0:
        return g
    n = C.fbm_periodic(IW, IW, [(14, 14, 1.0)], 671 + f, period_x=IW)
    I = 1.0 - d / size + 0.08 * n
    g[I > 0.0] = gpal['1']
    if f <= 6:
        g[I > 0.35] = gpal['2']
    if f <= 4:
        g[I > 0.65] = gpal['3']
    return g


def _ring_shape(f, variant, seed):
    cx, cy = RW / 2.0, RH / 2.0
    ys, xs = np.mgrid[0:RH, 0:RW]
    ex = (xs + 0.5 - cx)
    ey = (ys + 0.5 - cy) * 2.7
    d = np.sqrt(ex * ex + ey * ey)
    a = np.arctan2(ey, ex)
    rad = [10, 18, 26, 34, 42, 49, 56, 62][f]
    th0 = [4.0, 4.5, 4.2, 3.8, 3.2, 2.7, 2.2, 1.8][f]
    front = 0.5 + 0.5 * np.sin(a)            # the near half (lower on screen) is thicker
    # thickness in texels whichever way the band runs: d is stretched 2.7x vertically
    th = th0 * (0.45 + front) * (1.0 + 1.7 * np.abs(np.sin(a)))
    n = C.fbm_periodic(RW, RH, [(16, 6, 1.0), (8, 3, 0.5)], seed + f + variant, period_x=RW)
    return d, a, rad, th, n


def ring_a(pal, f, variant=0):
    """Take A: the shockwave racing out along the floor round the player's feet: a flat ellipse,
    its near side thicker, white-hot at first and cooling to crimson as it breaks up, sparks kicked
    off its front."""
    g = C.blank(RW, RH)
    d, a, rad, th, n = _ring_shape(f, variant, 711)
    band = (d > rad - th) & (d < rad + 0.6)
    keep = band & (n > [-2, -2, -0.7, -0.5, -0.3, -0.15, 0.0, 0.12][f])
    cols = [('w', 'h', 's'), ('w', 'h', 's'), ('h', 's', 'c'), ('h', 's', 'c'), ('s', 'c', 'm'),
            ('s', 'c', 'm'), ('c', 'm', 'v'), ('c', 'm', 'v')][f]
    g[keep] = pal[cols[2]]
    g[keep & (d > rad - th * 0.66)] = pal[cols[1]]
    g[keep & (d > rad - th * 0.30)] = pal[cols[0]]
    # the floor inside it scorched and glowing for the first frames
    if f <= 3:
        inner = (d < rad - th) & (n > [-2, -0.2, 0.1, 0.3][f])
        g[inner] = pal[['s', 'c', 'm', 'v'][f]]
    if f == 0:
        g[d < 5] = pal['w']
    # sparks kicked up off the front
    r = C.rng('ringA-sparks-%d' % variant)
    for k in range(18):
        ang = float(r.uniform(0, math.pi))            # the near half
        born = int(r.integers(0, 4))
        age = f - born
        if age < 0 or age > 3:
            continue
        rr = [10, 18, 26, 34, 42, 49, 56, 62][born] + 3 * age
        x = int(round(RW / 2.0 - 0.5 + rr * math.cos(ang)))
        y = int(round(RH / 2.0 - 0.5 + rr * math.sin(ang) / 2.7 - 2.0 * age + 0.5 * age * age))
        if 0 <= x < RW and 0 <= y < RH and g[y, x] == 0:
            g[y, x] = pal[['h', 'p', 's', 'c'][age]]
    return g
