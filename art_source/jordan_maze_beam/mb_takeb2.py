"""Take B, SOUL TORRENT, continued: the corner splash, the impact (a giant screaming face bursts out of
the blast and tears apart into fleeing souls), the floor shockwave, the break-up into rising souls,
the particles, the bone-ash scorch, the charge (souls spiralling into a skull-faced core) and the
release. Same sizes, frame counts and pivots as take A's.
"""
import math

import numpy as np

import mb_core as C
import mb_bursts as X
import mb_diss as D
import mb_charge as Q
import mb_takeb as TB

CW, IW, RW, RH, QW = X.CW, X.IW, X.RW, X.RH, Q.QW
OUTER = X.OUTER


def _stamp(g, pal, art, x0, y0, bone=('w', 'e', 'b', 'l'), eyes=None):
    """A soul drawn from one of mb_takeb's face grids, centred on (x0, y0), in the given bone ramp."""
    hh, ww = len(art), len(art[0])
    ox, oy = int(round(x0 - ww / 2.0)), int(round(y0 - hh / 2.0))
    h, w = g.shape
    for j in range(hh):
        for i in range(ww):
            ch = art[j][i]
            x, y = ox + i, oy + j
            if ch == '.' or not (0 <= x < w and 0 <= y < h):
                continue
            if ch == 'k':
                g[y, x] = pal['k']
                continue
            edge = (j == 0 or i in (0, ww - 1) or art[j - 1][i] == '.' or art[j][i - 1] == '.'
                    or (i + 1 < ww and art[j][i + 1] == '.') or (j + 1 < hh and art[j + 1][i] == '.'))
            g[y, x] = pal[bone[3] if edge else bone[0] if j <= 2 else bone[1] if j <= 5 else bone[2]]
    if eyes:
        for ex, ey in eyes:
            if 0 <= oy + ey < h and 0 <= ox + ex < w:
                g[oy + ey, ox + ex] = pal['r']


def _wisp(g, pal, x, y, ang, length, keys=('w', 'e', 'l', 'g')):
    """A fleeing soul: a 2x2 head and a tail trailing back along -ang, cooling along its length."""
    h, w = g.shape
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(int(length), -1, -1):
        px, py = int(round(x - ca * i)), int(round(y - sa * i))
        if 0 <= px < w and 0 <= py < h:
            u = i / max(length, 1)
            g[py, px] = pal[keys[1] if u < 0.35 else keys[2] if u < 0.7 else keys[3]]
    for dx in (0, 1):
        for dy in (0, 1):
            px, py = int(round(x)) + dx - 1, int(round(y)) + dy - 1
            if 0 <= px < w and 0 <= py < h:
                g[py, px] = pal[keys[0]]


def _smoke(g, pal, mask):
    """Smoke that shows on the pitch dark: dusk-purple masses, lit ash on their upper edge, black in
    their deepest middle."""
    h, w = g.shape
    m = mask & ((g == 0) | (g == pal['u']) | (g == pal['k']) | (g == pal['a']))
    g[m] = pal['u']
    up = np.zeros_like(m)
    up[1:, :] = m[:-1, :]
    top = m & ~up
    g[top] = pal['a']
    deep = m & ~C.dilate(~m, 2)
    g[deep] = pal['v']


# ----------------------------------------------------------------------------------------------- corner

def corner_b(pal, f, variant=0):
    """Take B: the torrent slams the turn: a ghost-white flash, bone fire splashing to the outer corner
    with a screaming soul flung out of it, then wisps and black smoke."""
    g = C.blank(CW, CW)
    c = CW / 2.0
    dx, dy, d, a = X._polar(CW, CW, c, c)
    pb = np.clip(np.cos(X._ang_diff(a, OUTER)), 0, 1)
    n = C.fbm_periodic(CW, CW, [(8, 8, 1.0), (4, 4, 0.5)], 2011 + 7 * f + variant, period_x=CW)
    r = C.rng('cornerB-%d-%d' % (variant, f))
    ox, oy = math.cos(OUTER), math.sin(OUTER)
    if f == 0:
        for ang, ln, wd in ((0, 22, 8), (-math.pi / 2, 21, 8), (OUTER, 27, 10), (math.pi, 12, 6), (math.pi / 2, 12, 6)):
            X.spike(g, pal, c, c, ang, ln, wd, ('l', 'e', 'w'))
        X._bands(g, pal, 1.0 - d / 9.5, ((0.0, 'e'), (0.3, 'w')))
    elif f == 1:
        fan = (d < 12 + 13 * pb ** 1.5 + 3 * n) & (pb > 0.2)
        g[fan] = pal['l']
        g[fan & (d < 9 + 9 * pb ** 1.5 + 2 * n)] = pal['b']
        X._bands(g, pal, 1.0 - d / 8.5, ((0.0, 'b'), (0.3, 'e'), (0.55, 'w')))
        ring = (d > 9.0) & (d < 11.5 + 1.5 * pb)
        g[ring] = pal['e']
        _stamp(g, pal, TB.SOUL_SMALL_OPEN, c + ox * 15, c + oy * 15, eyes=[(1, 2), (7, 2)])
    elif f == 2:
        fan = (d < 15 + 13 * pb ** 1.3 + 4 * n) & ((pb > 0.15) | (d < 12)) & (n > -0.35)
        g[fan] = pal['g']
        g[fan & (d < 12 + 10 * pb ** 1.3 + 3 * n)] = pal['l']
        g[fan & (d < 8 + 6 * pb ** 1.3 + 2 * n)] = pal['b']
        _smoke(g, pal, (d < 6.5 + 2 * n) & (n > -0.2))
        for k in range(3):
            ang = OUTER + float(r.uniform(-0.9, 0.9))
            rr = 12 + 4 * k
            _wisp(g, pal, c + math.cos(ang) * rr, c + math.sin(ang) * rr, ang, 6)
        _stamp(g, pal, TB.SOUL_SMALL_SHUT, c + ox * 21, c + oy * 21, eyes=[(1, 2), (7, 2)])
    elif f == 3:
        lick = (d < 11 + 13 * pb ** 1.3 + 3 * n) & (d > 6.0 + 3 * n) & (pb > 0.25) & (n > -0.1)
        g[lick] = pal['a']
        g[lick & (n > 0.25)] = pal['g']
        _smoke(g, pal, (d < 9 + 3 * n) & (n > 0.0))
        for k in range(3):
            ang = OUTER + float(r.uniform(-1.0, 1.0))
            rr = 17 + 4 * k
            _wisp(g, pal, c + math.cos(ang) * rr, c + math.sin(ang) * rr, ang, 6, ('e', 'l', 'g', 'a'))
        _stamp(g, pal, TB.SOUL_SMALL_SHUT, c + ox * 26, c + oy * 26, bone=('b', 'l', 'g', 'a'))
    elif f == 4:
        _smoke(g, pal, (d < 13 + 10 * pb + 3 * n) & (d > 8 + 3 * n) & (n > 0.2))
        for k in range(2):
            ang = OUTER + float(r.uniform(-1.0, 1.0))
            rr = 22 + 4 * k
            _wisp(g, pal, c + math.cos(ang) * rr, c + math.sin(ang) * rr, ang, 5, ('l', 'g', 'a', 'u'))
    elif f == 5:
        _smoke(g, pal, (d < 15 + 10 * pb + 3 * n) & (d > 12 + 4 * n) & (n > 0.45))
    er = C.rng('cornerB-embers-%d' % variant)
    for k in range(14):
        ang = OUTER + float(er.normal(0, 0.7))
        speed = float(er.uniform(4.0, 7.0))
        born = int(er.integers(0, 2))
        age = f - born
        if age < 0 or age > 4:
            continue
        dist = 8 + speed * age
        x = int(round(c - 0.5 + dist * math.cos(ang)))
        y = int(round(c - 0.5 + dist * math.sin(ang) - 0.4 * age * age))
        if 0 <= x < CW and 0 <= y < CW and g[y, x] in (0, pal['u'], pal['k']):
            g[y, x] = pal[['w', 'e', 'b', 'l', 'g'][age]]
    return g


# ----------------------------------------------------------------------------------------------- impact

def _giant_face(g, pal, c, stretch, melt, red):
    """The screaming face in the blast, cut as holes in the white fire: angular sockets glaring under
    an angry brow with red embers deep in them, a pear-shaped nose, and a dislocated jaw hanging
    open in a scream, lined with teeth. `stretch` drags the jaw further down, `melt` drips the
    sockets."""
    h, w = g.shape
    for sx in (-1, 1):
        sock = [(c + sx * 20.0, c - 13.0), (c + sx * 5.5, c - 8.5), (c + sx * 4.8, c - 2.5 + melt),
                (c + sx * 9.5, c + 1.0 + melt * 1.5), (c + sx * 16.0, c - 1.0 + melt), (c + sx * 20.5, c - 6.5)]
        m = C.polygon_mask(w, h, sock)
        g[m] = pal['k']
        # the brow's edge over it catches the fire's light, the socket's floor falls into shadow
        brow = C.dilate(m, 1) & ~m
        ys, xs = np.nonzero(brow)
        for y, x in zip(ys, xs):
            if g[y, x] not in (pal['k'],) and y < c - 3:
                g[y, x] = pal['l']
        if red:
            ex, ey = int(c + sx * 10.5 - (1 if sx > 0 else 0)), int(c - 6 + melt * 0.5)
            for ddx, ddy in ((-1, 0), (2, 0), (0, -1), (1, -1), (0, 2), (1, 2)):
                if m[ey + ddy, ex + ddx]:
                    g[ey + ddy, ex + ddx] = pal['c']
            for ddx, ddy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                g[ey + ddy, ex + ddx] = pal['r']
    nose = [(c, c + 1.0), (c + 3.4, c + 6.5), (c + 2.2, c + 9.2), (c, c + 8.0), (c - 2.2, c + 9.2), (c - 3.4, c + 6.5)]
    g[C.polygon_mask(w, h, nose)] = pal['k']
    # cheekbones: shadow slashing down from under the sockets
    for sx in (-1, 1):
        for t in range(7):
            x, y = int(c + sx * (17 - t * 0.6)), int(c + 3 + t)
            if g[y, x] not in (pal['k'],):
                g[y, x] = pal['l']
    top, bot = c + 12.0, c + 30.0 + stretch
    mouth = [(c - 9.5, top), (c + 9.5, top), (c + 11.0, top + 6), (c + 8.0, bot - 3), (c, bot), (c - 8.0, bot - 3),
             (c - 11.0, top + 6)]
    mm = C.polygon_mask(w, h, mouth)
    g[mm] = pal['k']
    # teeth: a row hanging from the upper jaw, a sparser row standing on the lower
    for tx in range(int(c - 8), int(c + 9), 2):
        col = [y for y in range(int(top - 1), int(top + 8)) if mm[y, tx]]
        if col:
            for k, y in enumerate(col[:3]):
                g[y, tx] = pal['e'] if k < 2 else pal['b']
    for tx in range(int(c - 6), int(c + 7), 3):
        col = [y for y in range(int(bot - 10), int(bot + 1)) if 0 <= y < h and mm[y, tx]]
        if col:
            for y in col[-2:]:
                g[y, tx] = pal['b']


def impact_b(pal, f, variant=0):
    """Take B: the skull lands and bursts: a white-out, then the blast of bone fire forms a giant
    screaming face that stretches, melts and tears apart into souls fleeing in every direction,
    leaving black smoke and ash."""
    g = C.blank(IW, IW)
    c = IW / 2.0
    dx, dy, d, a = X._polar(IW, IW, c, c)
    r = C.rng('impactB-%d-%d' % (variant, f))
    n = C.fbm_periodic(IW, IW, [(14, 14, 1.0), (7, 7, 0.5)], 2111 + 3 * f + variant, period_x=IW)
    spiky = 1.0 + 0.16 * np.cos(a * 7 + f) + 0.10 * n
    if f == 0:
        for k in range(10):
            ang = 2 * math.pi * k / 10 + (0.15 if k % 2 else 0)
            X.spike(g, pal, c, c, ang, 42 if k % 2 == 0 else 28, 9 if k % 2 == 0 else 6, ('l', 'e', 'w'))
        X._bands(g, pal, 1.0 - d / 18.0, ((0.0, 'b'), (0.2, 'e'), (0.4, 'w')))
    elif f == 1:
        g[d < 27 * spiky] = pal['l']
        g[d < 23 * spiky] = pal['b']
        g[d < 18 * spiky] = pal['e']
        g[d < 13] = pal['w']
    elif f in (2, 3):
        R = 33 if f == 2 else 37
        cran = ((dx / (R * 0.95)) ** 2 + ((dy + 6) / (R * 0.82)) ** 2) < 1.0 + 0.12 * n
        chin = R * 0.95 + (0 if f == 2 else 3)
        jaw = ((dx / (R * 0.46)) ** 2 + ((dy - chin * 0.45) / (chin * 0.58)) ** 2 < 1.0 + 0.1 * n) & (dy > 0)
        skull = cran | jaw
        g[skull & (d > R * 0.55)] = pal['l']
        g[skull & (d <= R * 0.78 + 3 * n)] = pal['b']
        g[skull & (d <= R * 0.6 + 3 * n)] = pal['e']
        g[skull & (d <= R * 0.38)] = pal['w']
        flames = (~skull) & (d < R + 6 + 5 * np.clip(-dy / R, 0, 1) * (1 + n)) & (n > -0.2)
        g[flames] = pal['g']
        g[flames & (n > 0.3)] = pal['l']
        _giant_face(g, pal, c, stretch=0.0 if f == 2 else 3.0, melt=0.0 if f == 2 else 2.5, red=True)
        if f == 3:
            _smoke(g, pal, (d > R + 2 + 3 * n) & (d < R + 7 + 3 * n) & (n > -0.1))
    elif f in (4, 5, 6):
        age = f - 4
        R = 40 + 4 * age
        fire = (d < R * 0.75 * spiky) & (d > 8 + 10 * age + 4 * n) & (n > -0.3 + 0.2 * age)
        g[fire] = pal[['b', 'l', 'g'][age]]
        g[fire & (n > 0.3)] = pal[['e', 'b', 'l'][age]]
        _smoke(g, pal, (d > R * 0.6 + 3 * n) & (d < R + 4 * n) & (n > -0.3 + 0.15 * age))
        wr = C.rng('impactB-wisps-%d' % variant)
        for k in range(9):
            ang = 2 * math.pi * k / 9 + float(wr.uniform(-0.2, 0.2))
            rr = 20 + 9 * age + float(wr.uniform(0, 4))
            x, y = c + math.cos(ang) * rr, c + math.sin(ang) * rr
            if k % 3 == 0 and age < 2:
                _stamp(g, pal, TB.SOUL_SMALL_OPEN, x, y, bone=[('w', 'e', 'b', 'l'), ('e', 'b', 'l', 'g')][age],
                       eyes=[(1, 2), (7, 2)] if age == 0 else None)
            else:
                keys = [('w', 'e', 'l', 'g'), ('e', 'b', 'l', 'g'), ('b', 'l', 'g', 'a')][age]
                _wisp(g, pal, x, y, ang, 7 + 2 * age, keys)
    elif f == 7:
        _smoke(g, pal, (d < 46 * spiky) & (d > 20 + 6 * n) & (n > -0.15))
        g[(d < 46 * spiky) & (d > 20 + 6 * n) & (n > 0.4)] = pal['a']
    elif f == 8:
        _smoke(g, pal, (d < 49 * spiky) & (d > 30 + 6 * n) & (n > 0.1))
    er = C.rng('impactB-embers-%d' % variant)
    for k in range(30):
        ang = float(er.uniform(0, 2 * math.pi))
        speed = float(er.uniform(4.0, 7.5))
        born = int(er.integers(1, 5))
        age = f - born
        if age < 0 or age > 4:
            continue
        dist = 14 + speed * (age + 1)
        x = int(round(c - 0.5 + dist * math.cos(ang)))
        y = int(round(c - 0.5 + dist * math.sin(ang) - 0.5 * age * age))
        if 0 <= x < IW and 0 <= y < IW and g[y, x] in (0, pal['k'], pal['u']):
            g[y, x] = pal[['w', 'e', 'b', 'l', 'g'][age]]
    return g


def ring_b(pal, f, variant=0):
    """Take B: a ghost-white shockwave racing out along the floor, cooling to ash as it breaks up,
    black smoke rolling behind it."""
    g = C.blank(RW, RH)
    d, a, rad, th, n = X._ring_shape(f, variant, 2211)
    band = (d > rad - th) & (d < rad + 0.6)
    keep = band & (n > [-2, -2, -0.7, -0.5, -0.3, -0.15, 0.0, 0.12][f])
    cols = [('w', 'e', 'b'), ('w', 'e', 'b'), ('e', 'b', 'l'), ('e', 'b', 'l'), ('b', 'l', 'g'),
            ('l', 'g', 'a'), ('g', 'a', 'u'), ('a', 'u', 'u')][f]
    g[keep] = pal[cols[2]]
    g[keep & (d > rad - th * 0.66)] = pal[cols[1]]
    g[keep & (d > rad - th * 0.30)] = pal[cols[0]]
    if 1 <= f <= 5:
        smoke = (d < rad - th) & (d > rad - th - 8) & (n > 0.2)
        g[smoke & (g == 0)] = pal['k']
        g[smoke & C.dilate(~smoke, 1) & (g == pal['k'])] = pal['u']
    if f == 0:
        g[d < 5] = pal['w']
    r = C.rng('ringB-sparks-%d' % variant)
    for k in range(18):
        ang = float(r.uniform(0, math.pi))
        born = int(r.integers(0, 4))
        age = f - born
        if age < 0 or age > 3:
            continue
        rr = [10, 18, 26, 34, 42, 49, 56, 62][born] + 3 * age
        x = int(round(RW / 2.0 - 0.5 + rr * math.cos(ang)))
        y = int(round(RH / 2.0 - 0.5 + rr * math.sin(ang) / 2.7 - 2.0 * age))
        if 0 <= x < RW and 0 <= y < RH and g[y, x] == 0:
            g[y, x] = pal[['w', 'e', 'b', 'l'][age]]
    return g


# ----------------------------------------------------------------------------------------------- break-up

W, H, CY = D.W, D.H, D.CY

COOL_B = [
    {'w': 'e', 'e': 'b', 'b': 'l', 'l': 'g', 'g': 'a', 'a': 'u', 'u': 'u', 'k': 'k', 'r': 'c', 'c': 'd', 'd': 'u', 'v': 'u'},
    {'w': 'b', 'e': 'l', 'b': 'l', 'l': 'g', 'g': 'a', 'a': 'u', 'u': 'u', 'k': 'k', 'r': 'c', 'c': 'd', 'd': 'u', 'v': 'u'},
    {'w': 'l', 'e': 'g', 'b': 'g', 'l': 'a', 'g': 'a', 'a': 'u', 'u': 'u', 'k': 'k', 'r': 'd', 'c': 'd', 'd': 'u', 'v': 'u'},
    {'w': 'g', 'e': 'a', 'b': 'a', 'l': 'u', 'g': 'u', 'a': 'u', 'u': 'u', 'k': 'u', 'r': 'u', 'c': 'u', 'd': 'u', 'v': 'u'},
]


def dissipate_b(pal, f, variant=0):
    """Take B: the torrent comes apart: the stream thins and snaps into ragged wisps, the souls tear
    free of it and flee off the line, fading, and black smoke and bone ash are all that's left."""
    g = C.blank(W, H)
    base = TB._profile_b(pal, 0, variant)
    ys = np.arange(H)[:, None] + 0.5
    ady = np.abs(ys - CY) * np.ones((1, W))
    n = C.fbm_periodic(W, H, [(12, 4, 1.0), (6, 2, 0.5)], 2301 + variant)
    half = [8.0, 6.5, 4.8, 3.0, 0.0, 0.0, 0.0, 0.0][f]
    frac = [1.0, 0.8, 0.6, 0.42, 0.0, 0.0, 0.0, 0.0][f]
    hw = np.roll(D._fragments('B%d' % variant, frac, half), 2 * f)
    erode = n > [-2.0, -0.3, -0.1, 0.05, 2, 2, 2, 2][f]
    body = (ady <= hw[None, :] + 0.9 * n * (hw[None, :] > 0)) & (hw[None, :] > 0) & erode
    if f < len(COOL_B):
        inv = {i: k for k, i in pal.idx.items()}
        for y in range(H):
            for x in range(W):
                if body[y, x] and base[y, x]:
                    g[y, x] = pal[COOL_B[f].get(inv[int(base[y, x])], 'u')]
    # the souls tearing free: the torrent's three, fleeing up and down off the line, fading
    for k, (x_at, kind, side) in enumerate(((4, 'big', -1), (40, 'small', 1), (66, 'mid', -1))):
        if f >= 6:
            break
        shut, opened, eyes_x, eye_y = TB.SOULS[kind]
        art = opened if f % 2 == 0 else shut
        hh, ww = len(art), len(art[0])
        cx = (x_at + ww / 2.0 + 2 * f) % W
        cy = CY + side * (2 + 3.2 * f)
        bone = [('w', 'e', 'b', 'l'), ('e', 'b', 'l', 'g'), ('b', 'l', 'g', 'a'), ('l', 'g', 'a', 'u'),
                ('g', 'a', 'u', 'u'), ('a', 'u', 'u', 'u')][f]
        eyes = [(ex, eye_y) for ex in eyes_x] if f < 3 else None
        tmp = C.blank(W, H)
        _stamp(tmp, pal, art, W / 2.0, cy, bone=bone, eyes=eyes)
        tmp = np.roll(tmp, int(round(cx - W / 2.0)), axis=1)
        g[tmp > 0] = tmp[tmp > 0]
        # its tail, streaming back towards the line
        for i in range(1, 8 + f):
            tx = int(round(cx - 3 - i * 0.6)) % W
            ty = int(round(cy - side * (hh / 2.0 + i * 0.7)))
            if 0 <= ty < H and g[ty, tx] == 0:
                g[ty, tx] = pal[bone[3] if i > 3 else bone[2]]
    # black smoke puffing off the line
    sr = C.rng('dissB-smoke-%d' % variant)
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
        _smoke(g, pal, puff)
    # bone ash scattering off both sides
    er = C.rng('dissB-ash-%d' % variant)
    for k in range(30):
        x0 = float(er.integers(0, W))
        side = -1 if k % 2 else 1
        born = int(er.integers(0, 4))
        life = int(er.integers(3, 6))
        age = f - born
        if age < 0 or age >= life:
            continue
        x = int(round(x0 + float(er.uniform(-1.2, 1.2)) * age)) % W
        y = int(round(CY - 0.5 + side * (1.5 + float(er.uniform(1.4, 2.6)) * (age + 1))))
        if 0 <= y < H and g[y, x] in (0, pal['u']):
            g[y, x] = pal[['w', 'e', 'b', 'l', 'g', 'a'][min(age, 5)]]
    return g


def ember_b(pal, f):
    """One soul-wisp rising: a bright head, its tail below it, fading to ash."""
    g = C.blank(D.EMBER, D.EMBER)
    shapes = [
        [(3, 2, 'w'), (4, 2, 'w'), (3, 3, 'w'), (4, 3, 'e'), (3, 4, 'e'), (4, 5, 'b'), (3, 6, 'l')],
        [(3, 2, 'e'), (4, 2, 'e'), (3, 3, 'e'), (4, 3, 'b'), (4, 4, 'l'), (3, 5, 'g')],
        [(3, 2, 'b'), (4, 3, 'b'), (3, 3, 'l'), (4, 4, 'g')],
        [(3, 2, 'l'), (3, 3, 'g'), (4, 4, 'a')],
        [(3, 2, 'g'), (4, 3, 'a')],
        [(3, 2, 'a')],
    ]
    for x, y, k in shapes[f]:
        g[y, x] = pal[k]
    return g


def smoke_b(pal, f):
    """One puff of black smoke rimmed ash, swelling and thinning to nothing."""
    g = C.blank(D.SMOKE, D.SMOKE)
    c = D.SMOKE / 2.0
    ys, xs = np.mgrid[0:D.SMOKE, 0:D.SMOKE]
    n = C.fbm_periodic(D.SMOKE, D.SMOKE, [(4, 4, 1.0)], 2381, period_x=D.SMOKE)
    rad = [2.5, 3.5, 4.5, 5.5, 6.3, 7.0][f]
    blob = ((xs + 0.5 - c) / (rad * 1.1)) ** 2 + ((ys + 0.5 - c) / rad) ** 2 + 0.25 * n < 1.0
    thin = n > [-2, -2, -0.4, -0.2, 0.05, 0.25][f]
    m = blob & thin
    _smoke(g, pal, m)
    if f >= 3:
        g[m & (g == pal['a'])] = pal['u']
    return g


def scorch_b(pal, f, variant=0):
    """Take B: the path burnt into the floor: a charred band, a seam of bone-white soul fire through it
    that gutters to grey ash."""
    g = C.blank(D.SW, D.SH)
    char, inner = D._char_band(2401 + variant)
    g[char] = pal[['a', 'u', 'u', 'v'][f]]
    g[inner] = pal['k']
    m = D._cracks('scorchB-%d' % variant, D.SH / 2.0)
    hot = [('w', 'e'), ('e', 'b'), ('b', 'l'), ('g', 'a')][f]
    g[m] = pal[hot[1]]
    every3 = np.zeros((D.SH, D.SW), bool)
    every3[:, ::3] = True
    g[m & every3] = pal[hot[0]]
    return g


# ----------------------------------------------------------------------------------------------- charge

def charge_b(pal, f, variant=0):
    """Take B: frame f of 12, three stages of 4: souls spiral in out of the dark and into a ball of
    ghost fire; at full charge a skull face grins out of it, eyes red."""
    stage, k = divmod(f, Q.STAGE_FRAMES)
    g = C.blank(QW, QW)
    c = QW / 2.0
    dx, dy, d, a = X._polar(QW, QW, c, c)
    r = C.rng('chargeB-%d-%d' % (variant, f))
    pulse = [0.0, 0.8, 1.4, 0.6][k]
    core = [3.2, 5.2, 7.4][stage] + pulse
    n = C.fbm_periodic(QW, QW, [(10, 10, 1.0)], 2431 + f, period_x=QW)
    halo_r = core * [2.0, 2.1, 2.2][stage]
    halo = halo_r + 1.5 * n
    _smoke(g, pal, (d < halo + 3.5) & (d > halo - 0.5) & (n > -0.1))
    g[d < halo] = pal['g']
    g[d < halo * 0.8] = pal['l']
    g[d < core + 1.5] = pal['b']
    g[d < core] = pal['e']
    g[d < core - 1.4] = pal['w']
    # ghost fire spiralling in: pale streaks curling round into the halo, bright at their heads
    wr = C.rng('chargeB-souls-%d-%d' % (stage, variant))
    count = [6, 9, 12][stage]
    for s_ in range(count):
        ang0 = 2 * math.pi * s_ / count + float(wr.uniform(-0.3, 0.3))
        t = (float(wr.uniform(0, 1)) + k * 0.25) % 1.0
        r_out, r_in = [26, 32, 38][stage], halo_r
        head = r_out - (r_out - r_in) * t
        length = 8 + 7 * (1 - t)
        prev = None
        for i in range(int(length) + 1):
            rr = head + i
            a_ = ang0 + 1.1 * (rr - r_in) / (r_out - r_in)
            pt = (c + rr * math.cos(a_), c + rr * math.sin(a_))
            if prev is not None:
                u = i / max(length, 1)
                key = 'e' if u < 0.2 else 'l' if u < 0.55 else 'g' if u < 0.8 else 'a'
                for x_, y_ in C.line_points(prev[0], prev[1], pt[0], pt[1]):
                    if 0 <= x_ < QW and 0 <= y_ < QW and g[y_, x_] in (0, pal['u'], pal['v'], pal['a']):
                        g[y_, x_] = pal[key]
            prev = pt
    # at full charge a demon skull glares out of the core: sockets slanting down to the nose, red
    # embers in them, a grin of teeth
    if stage == 2:
        holes = [
            ".kkk...kkk.",
            "..kkk.kkk..",
            "...kk.kk...",
            ".....k.....",
            "...........",
            "..kkkkkkk..",
            "..k.k.k.k..",
        ] if k % 2 == 0 else [
            ".kkk...kkk.",
            "..kkk.kkk..",
            "...kk.kk...",
            ".....k.....",
            "..kkkkkkk..",
            "..k.k.k.k..",
            "..kkkkkkk..",
        ]
        ox, oy = int(c - 5.5), int(c - 3.5)
        for j, row in enumerate(holes):
            for i, ch in enumerate(row):
                if ch == 'k':
                    g[oy + j, ox + i] = pal['k']
        for ex, ey in ((2, 1), (8, 1)):
            g[oy + ey, ox + ex] = pal['r']
        g[oy, ox + 1] = pal['c']
        g[oy, ox + 9] = pal['c']
    return g


def release_b(pal, f, variant=0):
    """Take B: the throw: a ghost-white flash, a cone of bone fire screaming down, souls spat out of
    it, a ring, and smoke curling off the muzzle."""
    g = C.blank(QW, QW)
    c = QW / 2.0
    dx, dy, d, a = X._polar(QW, QW, c, c)
    r = C.rng('releaseB-%d-%d' % (variant, f))
    down = math.pi / 2
    pb = np.clip(np.cos(X._ang_diff(a, down)), 0, 1)
    n = C.fbm_periodic(QW, QW, [(10, 10, 1.0), (5, 5, 0.5)], 2451 + f + variant, period_x=QW)
    if f == 0:
        for ang, ln, wd in ((down, 32, 12), (down - 0.5, 20, 7), (down + 0.5, 20, 7), (0, 14, 6),
                            (math.pi, 14, 6), (-down, 10, 5)):
            X.spike(g, pal, c, c, ang, ln, wd, ('l', 'e', 'w'))
        X._bands(g, pal, 1.0 - d / 10.0, ((0.0, 'e'), (0.3, 'w')))
    elif f == 1:
        cone = (d < 10 + 18 * pb ** 2 + 3 * n) & (pb > 0.35)
        g[cone] = pal['l']
        g[cone & (d < 8 + 14 * pb ** 2 + 2 * n)] = pal['b']
        g[cone & (d < 5 + 9 * pb ** 3)] = pal['e']
        X._bands(g, pal, 1.0 - d / 9.0, ((0.0, 'b'), (0.3, 'e'), (0.55, 'w')))
        g[(d > 11) & (d < 13.5)] = pal['e']
    elif f == 2:
        cone = (d < 12 + 16 * pb ** 2 + 4 * n) & ((pb > 0.3) | (d < 10)) & (n > -0.35)
        g[cone] = pal['g']
        g[cone & (d < 10 + 13 * pb ** 2 + 3 * n)] = pal['l']
        g[cone & (d < 7 + 7 * pb ** 2)] = pal['b']
        g[d < 5] = pal['e']
        ring = (d > 17) & (d < 19.5) & (n > -0.3)
        g[ring] = pal['b']
        for k in range(3):
            ang = down + float(r.uniform(-1.0, 1.0))
            rr = 14 + 4 * k
            _wisp(g, pal, c + math.cos(ang) * rr, c + math.sin(ang) * rr, ang, 6)
    elif f == 3:
        g[(d > 20) & (d < 22) & (n > 0.1)] = pal['g']
        g[(d < 4) & (n > -0.2)] = pal['l']
        for k in range(3):
            ang = down + float(r.uniform(-1.1, 1.1))
            rr = 20 + 4 * k
            _wisp(g, pal, c + math.cos(ang) * rr, c + math.sin(ang) * rr, ang, 6, ('e', 'l', 'g', 'a'))
    elif f == 4:
        _smoke(g, pal, (d < 12 + 12 * pb + 3 * n) & (d > 8 + 3 * n) & (n > 0.45))
    return g


def impact_glow_b(gpal, f):
    """Take B's afterglow goes out faster than A's: a grey haze left behind reads as a hole."""
    g = C.blank(IW, IW)
    _, _, d, _ = X._polar(IW, IW, IW / 2.0, IW / 2.0)
    size = [50, 56, 58, 54, 40, 24, 0, 0, 0, 0][f]
    if size == 0:
        return g
    n = C.fbm_periodic(IW, IW, [(14, 14, 1.0)], 2671 + f, period_x=IW)
    I = 1.0 - d / size + 0.08 * n
    g[I > 0.0] = gpal['1']
    if f <= 4:
        g[I > 0.35] = gpal['2']
    if f <= 3:
        g[I > 0.65] = gpal['3']
    return g
