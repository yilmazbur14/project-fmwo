"""Attack 1's water: the tsunami wave (liam_wave_*), its tell swell, collapse and parry splash.
No keyline anywhere (floor/FX precedent). The palette is shared with the flood (attack 2).

The wave covers the 282 x 120 texel hit band exactly; its front (the crest crashing toward the player)
is the band's bottom row. It is built from a body tile (94 x 80) and a crest strip (94 x 40, 3-frame
loop), both seamless left-right, three of each side by side: 3 x 94 = 282. It may be mirrored.
"""
import math

import numpy as np

import le_rig as R

# water ramp (dark -> foam). b, l, W are his; the rest are the water's own.
WATER = {
    '0': R.hx('14295a'),   # navy: the shadow in the curl
    '%': R.hx('1d4a8e'),   # deep
    '=': R.hx('2b6cc0'),   # mid
    '+': R.hx('4596e0'),   # light
    '~': R.hx('9fdcf7'),   # pale aqua (flow streaks, foam shadow)
}
R.PAL.update(WATER)
RAMP = '0%=+~lW'          # 7 steps, b is used for spray

TW, BODY_H, CREST_H = 94, 80, 40
WW, WH = 3 * TW, BODY_H + CREST_H


def pnoise(w, h, cell, seed, periodic_x=True, periodic_y=False):
    """Value noise, seamless across x (and y if asked)."""
    rnd = np.random.RandomState(seed)
    gw, gh = int(math.ceil(w / cell)), int(math.ceil(h / cell)) + 2
    g = rnd.rand(gh + 1, gw + 1)
    if periodic_x:
        g[:, gw] = g[:, 0]
    if periodic_y:
        g[gh, :] = g[0, :]
    ys, xs = np.mgrid[0:h, 0:w]
    fx, fy = xs * gw / w, ys / cell
    if periodic_y:
        fy = ys * gh / h
    x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    tx, ty = fx - x0, fy - y0
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
    b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
    return a * (1 - ty) + b * ty


def quant(v, ramp=RAMP):
    idx = np.clip((v * len(ramp)).astype(int), 0, len(ramp) - 1)
    return np.array(list(ramp))[idx]


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def dquant(v, ramp=RAMP):
    """Quantise with a 4x4 ordered dither between neighbouring tones (pixel-art gradients)."""
    h, w = v.shape
    t = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    f = v * (len(ramp) - 1)
    idx = np.floor(f + (t - 0.5) * 0.9 + 0.5).astype(int)
    idx = np.clip(idx, 0, len(ramp) - 1)
    return np.array(list(ramp))[idx]


def body_tile(seed=11):
    """94 x 80: the back of the wave. A frothy trailing edge at the top, then the long slope of water,
    deep at the back and brighter toward the crest, with short ripple dashes across the flow."""
    w, h = TW, BODY_H
    ys, xs = np.mgrid[0:h, 0:w]
    n1 = pnoise(w, h, 12, seed)
    n2 = pnoise(w, h, 4, seed + 1)
    u = ys / (h - 1)
    v = 0.16 + 0.30 * u + (n1 - 0.5) * 0.16
    cv = dquant(np.clip(v, 0, 0.99), RAMP[:5])
    # ripple dashes: short horizontal highlights, denser and brighter toward the crest
    rnd = np.random.RandomState(seed + 7)
    for _ in range(95):
        y = int(rnd.randint(10, h - 2))
        x = int(rnd.randint(0, w))
        L = int(rnd.randint(3, 9))
        uu = y / (h - 1)
        ch = '~' if uu > 0.62 and rnd.rand() < 0.5 else ('+' if uu > 0.25 else '=')
        for k in range(L):
            cv[y, (x + k) % w] = ch
        if uu > 0.5 and rnd.rand() < 0.4:
            cv[y + 1, (x + 1) % w] = '%' if ch != '~' else '+'
    # thin foam threads near the crest (short, pale, broken)
    for _ in range(26):
        y = int(rnd.randint(int(h * 0.55), h - 2))
        x = int(rnd.randint(0, w))
        for k in range(int(rnd.randint(4, 11))):
            if rnd.rand() < 0.8:
                cv[y, (x + k) % w] = 'l' if k % 3 else '~'
    # the trailing edge: rounded froth bumps
    e = 6 + (pnoise(w, 1, 16, seed + 6)[0] * 9 + np.sin(xs[0] / w * 2 * np.pi * 6) * 1.5).astype(int)
    for x in range(w):
        top = e[x]
        cv[:top, x] = '.'
        cv[top, x] = 'W'
        if top + 1 < h:
            cv[top + 1, x] = 'l' if n2[top + 1, x] > 0.35 else 'W'
        if top + 2 < h and n2[top + 2, x] > 0.6:
            cv[top + 2, x] = '~'
        if top - 3 >= 0 and n2[max(0, top - 3), x] > 0.8:
            cv[top - 3, x] = 'l'
    return cv


def crest_strip(frame, seed=21):
    """94 x 40, 3-frame loop: the crest. From the top: the face rising and brightening, the rounded white
    lip, the curls rolling under it (a thin dark tube with scalloped edges), and the ragged spray where it
    crashes on the band's bottom row. Curls travel a third of their spacing per frame, so 0-1-2 loops."""
    w, h = TW, CREST_H
    ys, xs = np.mgrid[0:h, 0:w]
    ph = frame / 3.0
    n = pnoise(w, h, 3, seed + frame)
    curl_w = w / 3.0                                   # three curls per tile
    cx = (xs / curl_w + ph) % 1.0                      # 0..1 across each curl
    arch = np.sin(np.pi * cx)                          # 0 at the curl ends, 1 mid-curl
    lip_top = (10 - 3 * arch).astype(int)              # the lip bulges up mid-curl
    lip_bot = (21 + 3 * arch).astype(int)              # and hangs lower mid-curl
    tube_bot = (27 + 2 * arch + np.where(cx < 0.12, -3, 0)).astype(int)
    cv = np.full((h, w), '.', dtype='<U1')
    face = ys < lip_top
    v = 0.42 + 0.35 * ys / 10 + (n - 0.5) * 0.18
    cv[face] = dquant(np.clip(v, 0, 0.99), RAMP[:6])[face]
    lip = (ys >= lip_top) & (ys < lip_bot)
    rel = (ys - lip_top) / np.maximum(1, lip_bot - lip_top)
    lipc = np.where(rel < 0.5, 'W', np.where(rel < 0.78, 'l', '~'))
    # the curl's lit rim on the left of each curl, shadow on the right
    lipc = np.where((rel > 0.45) & (cx > 0.7), '~', lipc)
    lipc = np.where((n > 0.78) & (rel > 0.25) & (rel < 0.6), 'l', lipc)
    cv[lip] = lipc[lip]
    tube = (ys >= lip_bot) & (ys < tube_bot)
    tc = np.where(ys - lip_bot < 1, '0', np.where(n > 0.58, '%', '0'))
    tc = np.where((cx < 0.25) & (ys - lip_bot > 1), '=', tc)          # light through the curl's end
    cv[tube] = tc[tube]
    crash = ys >= tube_bot
    cr = np.where(n > 0.5, 'W', 'l')
    cr = np.where((ys == tube_bot) & (n < 0.4), '~', cr)
    cv[crash] = cr[crash]
    # ragged front: the last two rows chew in and out, with spray flecks just above the lip
    for x in range(w):
        if n[h - 1, x] < 0.22:
            cv[h - 1, x] = '~'
        if n[h - 2, x] > 0.85:
            cv[h - 2, x] = 'l'
    for (x0, y0) in ((6, 7), (19, 5), (37, 6), (52, 4), (68, 6), (83, 5)):
        xx = int(x0 + ph * curl_w) % w
        for (dx, dy, ch) in ((0, 0, 'W'), (1, 0, 'l'), (0, -2, 'l'), (-1, 1, '~')):
            X_, Y_ = (xx + dx) % w, y0 + dy
            if 0 <= Y_ < h:
                cv[Y_, X_] = ch
    return cv


def full_wave(frame=0):
    out = R.blank(WW, WH)
    b = body_tile()
    c = crest_strip(frame)
    for i in range(3):
        R.composite(out, b, i * TW, 0)
        R.composite(out, c, i * TW, BODY_H)
    return out


def tell_swell(k):
    """3 frames, 282 x 24: the swell humping up behind the top rope before a wave rolls in."""
    w, h = WW, 24
    out = R.blank(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    n = pnoise(w, h, 5, 31 + k)
    height = (8, 14, 20)[k]
    top = h - height + (np.sin(2 * math.pi * (xs / TW * 3)) * 1.5).astype(int)
    body = ys >= top
    rel = (ys - top) / max(1, height)
    v = 0.65 - 0.35 * rel + (n - 0.5) * 0.25
    cv = quant(np.clip(v, 0, 0.99))
    cv = np.where((ys - top) < 2, np.where(n > 0.4, 'W', 'l'), cv)
    out[body] = cv[body]
    return out


def collapse(k, seed=41):
    """3 frames, 282 x 120: the wave (after the round's first hit) slumping into foam and spreading
    thin - it is what floods the ring. 0 the crest breaks; 1 a sheet of foam with holes; 2 last foam."""
    base = full_wave(0)
    ys, xs = np.mgrid[0:WH, 0:WW]
    n = pnoise(WW, WH, 6, seed + k)
    n2 = pnoise(WW, WH, 3, seed + 10 + k)
    out = base.copy()
    if k == 0:
        # the lip crumbles into foam and the body pales
        foam = (ys > BODY_H - 6) & (n > 0.35)
        out[foam] = np.where(n2[foam] > 0.5, 'W', 'l')
        paler = (out == '0') | (out == '%')
        out[paler] = '='
        holes = (n < 0.18) & (ys < BODY_H - 20)
        out[holes] = '.'
    elif k == 1:
        v = 0.55 + (n - 0.5) * 0.6
        out = quant(np.clip(v, 0.28, 0.99))
        out[(n2 > 0.62)] = 'W'
        out[(n < 0.32)] = '.'
        out[ys < 10 + (n[0] * 8).astype(int)[None, :].repeat(WH, 0)] = '.'
    else:
        out = R.blank(WW, WH)
        patch = (n > 0.62)
        out[patch] = np.where(n2[patch] > 0.6, 'W', np.where(n2[patch] > 0.4, 'l', '~'))
    return out


DROP = [".W.", "WWl", "l~+", ".+."]          # a flung droplet (head up)
DROP_S = ["W.", "l+"]


def splash(k):
    """4 frames, 32 x 32, pivot (16, 20): a parried wave bursting against the player's guard.
    0 the burst (white star of spray); 1 a crown of water thrown up and out; 2 the crown breaking into
    flung droplets; 3 droplets falling and a ring of foam on the floor."""
    w = h = 32
    out = R.blank(w, h)
    X, Y = R.centres(w, h)
    cx, cy = 16.0, 20.0
    if k == 0:
        core = ((X - cx) / 6) ** 2 + ((Y - cy) / 4.5) ** 2 <= 1
        out[core] = 'W'
        for a_ in range(0, 360, 30):
            r0, r1 = 5, 10 if a_ % 60 == 0 else 8
            for rr in np.linspace(r0, r1, 8):
                x = int(cx + math.cos(math.radians(a_)) * rr * 1.1)
                y = int(cy + math.sin(math.radians(a_)) * rr * 0.8)
                if 0 <= x < w and 0 <= y < h:
                    out[y, x] = 'W' if rr < r1 - 2 else 'l'
        rim = (((X - cx) / 7.5) ** 2 + ((Y - cy) / 5.5) ** 2 <= 1) & ~core
        out[rim & (out == '.')] = '~'
    elif k == 1:
        crown = (((X - cx) / 11) ** 2 + ((Y - cy) / 5) ** 2 <= 1) & (((X - cx) / 7) ** 2 + ((Y - cy) / 3) ** 2 > 1)
        out[crown] = np.where(Y[crown] < cy, 'W', 'l')
        for (x, y) in ((7, 9), (12, 5), (19, 5), (24, 9), (4, 14), (27, 14)):
            R.blk(out, x - 1, y - 1, DROP)
        pool = ((X - cx) / 9) ** 2 + ((Y - cy - 1) / 3) ** 2 <= 1
        out[pool & (out == '.')] = '+'
    elif k == 2:
        ring = (((X - cx) / 13) ** 2 + ((Y - cy - 1) / 5) ** 2 <= 1) & (((X - cx) / 10.5) ** 2 + ((Y - cy - 1) / 3.6) ** 2 > 1)
        out[ring] = np.where(Y[ring] < cy, 'l', '~')
        for (x, y) in ((4, 6), (10, 2), (21, 2), (27, 6), (1, 12), (30, 12), (15, 1)):
            R.blk(out, x - 1, y - 1, DROP if (x + y) % 2 else DROP_S)
    else:
        ring = (((X - cx) / 15) ** 2 + ((Y - cy - 2) / 5.5) ** 2 <= 1) & (((X - cx) / 13.5) ** 2 + ((Y - cy - 2) / 4.5) ** 2 > 1)
        out[ring] = '~'
        for (x, y) in ((3, 13), (8, 8), (23, 8), (28, 13), (15, 6), (12, 27), (20, 28)):
            R.blk(out, x - 1, y - 1, DROP_S)
    return out


EDGE_W = 10
EDGE_AT = 6          # the wave's inner edge falls on this column of the cap


def wave_edge():
    """10 x 120 (optional piece): a frothy cap for the wave's inner (seam) end so the half-width band
    does not end in a ruler-straight cut. Columns 0..5 overlap the wave's last texels (foam), 6..9 hold
    spray beyond it. Drawn at the left wave's right end; mirror it for the right wave."""
    h = WH
    cv = R.blank(EDGE_W, h)
    n = pnoise(EDGE_W, h, 5, 61, periodic_x=False)
    for y in range(8, h):
        depth = 3 + int(n[y, 0] * 4)                     # foam bite into the wave's edge
        for x in range(EDGE_AT - depth, EDGE_AT):
            cv[y, x] = 'W' if x > EDGE_AT - 3 else ('l' if n[y, x] > 0.4 else '~')
        if n[y, 3] > 0.7 and y % 3 == 0:
            cv[y, EDGE_AT] = 'l'
            cv[y, EDGE_AT + 1] = 'W' if n[y, 5] > 0.8 else '~'
        if n[y, 6] > 0.82 and y % 5 == 1:
            cv[y, EDGE_AT + 3] = 'l'
    # the crest's end curls round: the lip's white runs out past the edge a little
    for y in range(BODY_H + 12, BODY_H + 24):
        cv[y, EDGE_AT] = 'W'
        if y % 2:
            cv[y, EDGE_AT + 1] = 'l'
    return cv
