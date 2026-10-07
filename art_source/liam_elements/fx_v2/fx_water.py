"""FX v2 water (attack 1): the wave crest (a rolling curl with spray and churning foam), the body tile's shimmer, the
tell swell rising and trembling, the collapse bursting into arcing droplets, the parry splash, and a ripple overlay for
the flood. No keyline; the wave ramp (0 % = + ~ l W) plus his spray blue b, as shipped.

Every wave piece keeps its shipped cell: the crest 94x40 and the body 94x80 tile seamlessly left-right and stack into
the 94x120 band tile whose last row (the crest's row 39) is the band's front edge; the tell is 282x24 on the rope line,
the collapse 282x120 on the band, the splash 32x32 on (16, 20). The flood's six nested coverage frames are untouched:
the ripple is a separate 64x64 overlay drawn clipped to the water.
"""
import math
import sys

sys.dont_write_bytecode = True

import numpy as np

import fx_common as C

TW, BODY_H, CREST_H = 94, 80, 40
WW, WH = 3 * TW, BODY_H + CREST_H
NF = 12                         # the crest and the body loop together on WAVE_FRAME_TIME
FRAME_TIME = 0.06
RAMP = '0%=+~lW'


def _wrapdist(a, b, period):
    d = (a - b) % period
    return np.minimum(d, period - d)


# ------------------------------------------------------------------ the crest: 94 x 40, NF-frame loop
# Three barrels a tile, seen head-on as the wave rolls at the player: each is a dark tunnel under an arching lip, the lip
# plunging into a pile of whitewater between barrels. The barrels peel toward the rope end one barrel a loop; the lip's
# surface rolls forward, the whitewater tumbles forward and boils, and every plunge throws a fountain of spray up.
CURLS = 3
CURL_W = TW / CURLS
DRIFT = 1                      # barrels travelled a loop (toward -x, the rope end)


def crest_geometry(f):
    xs = np.arange(TW) + 0.5
    cx = (xs / CURL_W + DRIFT * f / NF) % 1.0
    s = np.sin(np.pi * cx)
    lip_top = np.round(13.0 - 6.4 * s ** 0.6).astype(int)             # the crown arches up over each barrel
    lip_bot = np.round(13.0 - 6.4 * s ** 0.6 + 5.6 + 3.8 * (1 - s)).astype(int)
    foam_top = np.round(25.4 - 4.2 * (1 - s) ** 1.6).astype(int)       # whitewater piles up where the lip lands
    return cx, s, lip_top, lip_bot, foam_top


def _foam(f, seed, w, h, y0=0):
    """Whitewater: bubbly clusters lit on top (W) with shade under them (~), tumbling forward a row a frame and
    boiling on the loop. y0 = the strip row its row 0 sits on."""
    P = 12
    base = C.vnoise((P, w), (4, 20), seed)
    fine = C.vnoise((P, w), (6, 47), seed + 2)
    boil = C.vnoise((NF, P, w), (3, 4, 20), seed + 1)
    ys = (np.arange(h)[:, None] + y0 - 1.0 * f) % P
    y0i = np.floor(ys).astype(int) % P
    t = ys - np.floor(ys)
    xs = np.arange(w)[None, :]

    def at(g):
        return g[y0i, xs] * (1 - t) + g[(y0i + 1) % P, xs] * t
    n = at(base) * 0.5 + at(boil[f]) * 0.3 + at(fine) * 0.2
    blob = n > 0.53
    under = np.zeros_like(blob)
    under[1:, :] = blob[:-1, :] & ~blob[1:, :]
    out = np.where(blob, 'W', 'l')
    out = np.where(under | (n < 0.37), '~', out)
    return out


def crest_strip(f, seed=21):
    w, h = TW, CREST_H
    cv = C.blank(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, s, lip_top, lip_bot, tube_bot = crest_geometry(f)
    LT, LB, TB = lip_top[None, :], lip_bot[None, :], tube_bot[None, :]
    CX = np.repeat(cx[None, :], h, 0)
    n_face = C.vnoise((NF, h, w), (3, 8, 20), seed)[f]
    n_fine = C.vnoise((NF, h, w), (3, 16, 47), seed + 5)[f]

    # the top of the wave, drawn up into the lip: dithered blues brightening toward it, flow lines running in
    face = ys < LT
    v = 0.44 + 0.30 * ys / np.maximum(1, LT) + (n_face - 0.5) * 0.16
    cv[face] = C.dquant(np.clip(v, 0, 0.99), RAMP[:6])[face]
    rnd = np.random.RandomState(seed + 9)
    for i in range(14):
        x0, ln = rnd.randint(0, w), rnd.randint(3, 7)
        y = (rnd.randint(0, 12) + f) % 12
        for k in range(ln):
            X = (x0 + k) % w
            if y < lip_top[X] - 1:
                cv[y, X] = '~' if y > 3 else '+'

    # the lip: lit crown, rounded front, shaded underside; its surface rolls forward a third of a row a frame
    lip = (ys >= LT) & (ys < LB)
    rl = (ys - LT) / np.maximum(1, LB - LT)
    band = ((ys - LT) - f / 3.0) % 4.0 < 1.0
    lc = np.where(rl < 0.30, 'W', np.where(rl < 0.76, 'l', '~'))
    lc = np.where((rl >= 0.30) & (rl < 0.76) & band & (n_fine > 0.35), 'W', lc)
    lc = np.where((rl >= 0.76) & band & (n_fine > 0.3), 'l', lc)
    lc = np.where((rl < 0.30) & band & (n_fine < 0.3), 'l', lc)
    cv[lip] = lc[lip]
    # its outline where it meets the face: a bright rim along the crown
    for x in range(w):
        if lip_top[x] - 1 >= 0 and n_fine[lip_top[x] - 1, x] > 0.55:
            cv[lip_top[x] - 1, x] = 'l'

    # the barrel: a dark tunnel under the arch; its back wall glows low in the middle where light comes through the
    # lip, and the water line at its foot catches the light
    tube = (ys >= LB) & (ys < TB)
    d = (ys - LB) / np.maximum(1, TB - LB)
    S = np.repeat(s[None, :], h, 0)
    tc = np.where(d < 0.34, '0', np.where(n_fine > 0.55, '0', '%'))
    tc = np.where((d >= 0.50) & (S > 0.30), np.where(n_fine > 0.5, '%', '='), tc)
    core = (d >= 0.62) & (S > 0.62)
    tc = np.where(core, np.where(n_fine > 0.62, '+', '='), tc)
    tc = np.where(core & (S > 0.9) & (d > 0.7), '+', tc)
    cv[tube] = tc[tube]
    for x in range(w):                                   # the water line at the barrel's foot
        y = tube_bot[x] - 1
        if lip_bot[x] < y and s[x] > 0.2:
            cv[y, x] = '~' if (x + f) % 5 else 'l'
    # the lip's edge pouring into the barrel: two thin runnels a barrel that stretch and snap back
    for c in range(CURLS):
        for j, off in enumerate((0.34, 0.63)):
            xx = int(((c + off - DRIFT * f / NF) * CURL_W)) % w
            ln = (f + j * 4 + c * 5) % 6
            for k in range(min(ln, 4)):
                y = lip_bot[xx] + k
                if y < tube_bot[xx] - 2:
                    cv[y, xx] = 'l' if k < ln - 1 else '~'

    # the whitewater: bubbly foam tumbling forward from the barrel's foot to the front edge
    foam = _foam(f, seed + 3, w, h)
    crash = ys >= TB
    cv[crash] = foam[crash]
    rim = (ys == TB) & (CX > 0.12) & (CX < 0.88)
    cv[rim] = np.where(n_fine[rim] > 0.4, 'W', 'l')
    for x in range(w):
        if cv[h - 1, x] == '.':
            cv[h - 1, x] = '~'

    # spray: each plunge point (a valley between barrels, moving with the peel) throws a fountain of droplets up over
    # the face, a mist puff blooming at its foot; flecks blow back off every crown
    DROPS = 10
    for c in range(CURLS):
        valley = (c - DRIFT * f / NF) * CURL_W
        for j in range(DROPS):
            born = (j * NF) // DROPS
            age = (f - born + c * 4) % NF
            if age > 5:
                continue
            vx = (-1.4, 1.2, -0.6, 1.7, 0.2, -1.1, 0.8, -1.8, 1.5, -0.2)[j]
            vy = (-4.9, -5.3, -5.4, -4.6, -5.2, -4.8, -4.3, -4.1, -4.7, -5.5)[j]
            x = valley + vx * age - DRIFT * CURL_W / NF * 0.3 * age
            y = 12.5 + vy * age + 0.72 * age * age
            if age > 0 and y > 12.5:
                continue
            head = 'W' if age < 4 else 'l'
            if age <= 4:
                vyt = vy + 1.44 * age
                C.plot(cv, x - vx * 0.4, y - vyt * 0.4, 'l' if age < 3 else '~', wrap_x=True)
            C.plot(cv, x, y, head, wrap_x=True)
            if age == 1 and j % 3 == 0:
                C.plot(cv, x + 1, y, 'W', wrap_x=True)
        k = (f + c * 4) % 6
        r = 1.8 + k * 0.7
        for dx in range(-5, 6):
            for dy in range(-3, 2):
                inside = (dx / r) ** 2 + (dy / (r * 0.6)) ** 2 <= 1
                if inside and (dx * 3 + dy * 5 + k) % 4 != 0:
                    C.plot(cv, valley + dx, 11.5 + dy - k * 0.8, 'W' if k < 2 else ('l' if k < 4 else '~'),
                           wrap_x=True, under=set('=+~%0'))
        for j in range(2):
            crown = valley + CURL_W * (0.32 + 0.36 * j)
            age = (f + j * 3 + c * 2) % 6
            if age < 4:
                X = int(math.floor(crown - age * (0.5 if j else -0.5))) % w
                y = lip_top[X] - 1 - age
                if y >= 0:
                    C.plot(cv, X, y, 'l' if age < 2 else '~', wrap_x=True)
                    if age == 0:
                        C.plot(cv, X + 1, y, 'W', wrap_x=True)
    return cv


# ------------------------------------------------------------------ the body tile: 94 x 80, a subtle NF-frame shimmer
def body_tile(f, seed=11):
    w, h = TW, BODY_H
    ys, xs = np.mgrid[0:h, 0:w]
    n1 = C.vnoise((h, w), (7, 8), seed, periodic=(False, True))
    n2 = C.vnoise((NF, h, w), (2, 20, 24), seed + 1)[f]
    u = ys / (h - 1)
    v = 0.16 + 0.30 * u + (n1 - 0.5) * 0.16
    cv = C.dquant(np.clip(v, 0, 0.99), RAMP[:5])
    rnd = np.random.RandomState(seed + 7)
    # ripple dashes: each one lives across the loop - it swells, slides a row toward the crest and thins away
    for i in range(190):
        y0 = int(rnd.randint(10, h - 3))
        x0 = int(rnd.randint(0, w))
        L = int(rnd.randint(3, 9))
        born = int(rnd.randint(0, NF))
        life = int(rnd.randint(4, 7))
        age = (f - born) % NF
        if age >= life:
            continue
        uu = y0 / (h - 1)
        grow = min(age + 1, life - age)
        ln = max(1, min(L, 1 + grow * 2))
        y = y0 + (1 if age >= life // 2 else 0)
        ch = '~' if uu > 0.62 and (i % 2) else ('+' if uu > 0.25 else '=')
        xs0 = x0 + (L - ln) // 2
        for k in range(ln):
            cv[y, (xs0 + k) % w] = ch
        if uu > 0.5 and (i % 5 == 0) and ln > 2:
            cv[min(h - 1, y + 1), (xs0 + 1) % w] = '%' if ch != '~' else '+'
    # foam threads near the crest drift down a row every other frame
    for i in range(26):
        y0 = int(rnd.randint(int(h * 0.56), h - 3))
        x0 = int(rnd.randint(0, w))
        L = int(rnd.randint(4, 11))
        y = min(h - 1, y0 + ((f + i) % NF) // 4)
        for k in range(L):
            if (k + f + i) % 5 != 4:
                cv[y, (x0 + k) % w] = 'l' if k % 3 else '~'
    # glints: a sparkle for two frames here and there
    for i in range(7):
        born = (i * 3) % NF
        age = (f - born) % NF
        if age > 1:
            continue
        x, y = int(rnd.randint(0, w)), int(rnd.randint(24, h - 4))
        cv[y, x] = 'W'
        if age == 0:
            cv[y, (x + 1) % w] = 'l'
            cv[y, (x - 1) % w] = 'l'
    # the trailing edge: rounded froth bumps that bob as the back of the wave runs on
    base = 6 + (C.vnoise((w,), (6,), seed + 6)[None, :] * 9)[0]
    wob = np.sin(2 * np.pi * (np.arange(w) / w * 6 + f / NF)) * 1.2
    e = np.round(base + np.sin(np.arange(w) / w * 2 * np.pi * 6) * 1.5 + wob * 0.6).astype(int)
    e = np.minimum(e, 14)                          # never deeper than the shipped edge: the band stays covered
    for x in range(w):
        top = e[x]
        cv[:top, x] = '.'
        cv[top, x] = 'W'
        if top + 1 < h:
            cv[top + 1, x] = 'l' if n2[top + 1, x] > 0.35 else 'W'
        if top + 2 < h and n2[top + 2, x] > 0.62:
            cv[top + 2, x] = '~'
    # spray flecks lifting off the trailing froth
    for i in range(5):
        born = (i * 5 + 1) % NF
        age = (f - born) % NF
        if age > 3:
            continue
        x = (int(rnd.randint(0, w)) + age) % w
        y = e[x] - 2 - age
        if y >= 0:
            cv[y, x] = 'l' if age < 2 else '~'
    return cv


def full_wave(f):
    out = C.blank(WW, WH)
    b = body_tile(f)
    c = crest_strip(f)
    for i in range(3):
        C.R.composite(out, b, i * TW, 0)
        C.R.composite(out, c, i * TW, BODY_H)
    return out


# ------------------------------------------------------------------ the tell: 282 x 24 on the rope line
TELL_FRAMES = 8
TELL_RISE = 5                   # 0..4 rise, 5..7 tremble (at the default 0.45 s tell, 0.06 s a frame shows 0..7 once)
TELL_H = (5, 9, 13, 17, 20, 21, 20, 21)


def tell_swell(k, seed=31):
    """The swell humping up behind the top rope before a wave rolls in: it rises over frames 0-4, its crest curling
    into small lips, then trembles at full height with spray flicking off (5-7). Bottom row = the rope line."""
    w, h = WW, 24
    out = C.blank(w, h)
    ys, xs = np.mgrid[0:h, 0:w]
    height = TELL_H[k]
    trem = 0 if k < TELL_RISE else (1 if k % 2 else -1)
    hump = np.sin(2 * np.pi * (xs / CURL_W + 0.035 * trem))                # three humps a tile, like the barrels
    rough = C.vnoise((TELL_FRAMES, h, w), (4, 3, 60), seed, periodic=(True, False, False))[k]
    top = h - height - np.round(hump * (1.0 + 0.8 * min(1.0, k / 4.0)) - (rough[0][None, :] - 0.5) * 2).astype(int)
    body = ys >= top
    rel = (ys - top) / max(1, height)
    n = C.vnoise((TELL_FRAMES, h, w), (4, 6, 70), seed + 1, periodic=(True, False, False))[k]
    v = 0.66 - 0.40 * rel + (n - 0.5) * 0.22
    cv = C.dquant(np.clip(v, 0, 0.99), RAMP[1:6])
    out[body] = cv[body]
    # the crest: a foam cap, a lit lip on each hump and a shaded underside once it has risen
    cap = body & ((ys - top) < 2)
    out[cap] = np.where(n[cap] > 0.42, 'W', 'l')
    if k >= 2:
        under = body & ((ys - top) == 2) & (hump > 0.1)
        out[under] = np.where(n[under] > 0.5, '~', 'l')
    if k >= 3:
        hollow = body & ((ys - top) == 3) & (hump > 0.35)
        out[hollow] = '%' if k < TELL_RISE else '0'
        if k >= TELL_RISE:
            hollow2 = body & ((ys - top) == 4) & (hump > 0.6)
            out[hollow2] = '%'
    # spray flicked off the crest once it stands (and a first few as it rises)
    rnd = np.random.RandomState(seed + 7)
    for i in range(70):
        x0 = rnd.randint(0, w)
        born = rnd.randint(0, TELL_FRAMES)
        age = k - born
        if age < 0 or age > 2 or k < 2:
            continue
        y0 = top[0, x0] - 1
        y = y0 - (1 + age * 2) + (age * age) // 2
        x = x0 + (age if i % 2 else -age)
        if 0 <= y < h:
            C.plot(out, x, y, 'W' if age == 0 else ('l' if age == 1 else '~'))
            if age == 0 and y + 1 < h:
                C.plot(out, x, y + 1, 'l')
    return out


# ------------------------------------------------------------------ the collapse: 282 x 120 over wave_collapse_time
COLLAPSE_FRAMES = 8
CREST_LINE = BODY_H + 12        # where the lip stood: the burst goes up from here


def _droplet(cv, x, y, vx, vy, age):
    """A flung droplet: a bright head and a short trail pointing back along its flight."""
    sp = math.hypot(vx, vy) or 1.0
    tx, ty = -vx / sp, -vy / sp
    C.plot(cv, x, y, 'W')
    C.plot(cv, x + tx, y + ty, 'l')
    if sp > 3.5:
        C.plot(cv, x + 2 * tx, y + 2 * ty, '~')


def _ring(cv, x, y, r, ch):
    C.arc(cv, x, y, r, max(1.0, r * 0.45), 0, 360, ch)


def _plume(cv, xc, base, width, height, lean=0.0, torn=0.0, seed=0):
    """A jet of spray standing up off the crest line: a round, bubbly head (a lit ball of water, W where the light
    catches it, ~ under its rim) on a neck that spreads into a foot of foam, droplets breaking off its sides.
    torn 0..1: the head has torn away into blobs and only the lower part of the neck still stands."""
    rnd = np.random.RandomState(seed)
    h, w = cv.shape
    hr = max(2.0, width * 0.6)
    top = base - height
    hx, hy = xc + lean * height * 0.22, top + hr
    wob = rnd.rand(24)
    # the neck, from the head's centre down to the foot
    cut = top + height * torn
    for y in range(int(math.floor(hy)), int(base) + 1):
        if y < cut:
            continue
        u = (y - hy) / max(1.0, base - hy)                      # 0 under the head, 1 at the foot
        half = width * (0.42 + 0.32 * u * u) + (wob[int(y) % 24] - 0.5) * 1.4
        x0 = hx + (xc - hx) * u
        for x in range(int(math.floor(x0 - half)), int(math.ceil(x0 + half)) + 1):
            rel = (x + 0.5 - (x0 - half)) / max(1.0, 2 * half)
            if rel < 0 or rel > 1:
                continue
            ch = 'W' if rel < 0.34 else ('~' if rel > 0.74 else 'l')
            if (y + int(x)) % 7 == 0 and 0.3 < rel < 0.7:
                ch = 'W'                                        # water rising up the jet
            C.plot(cv, x, y, ch)
    if torn > 0:
        # the head torn into round blobs flung out and up
        for j in range(3):
            bx = hx + (j - 1) * width * (0.55 + torn * 0.8)
            by = hy - torn * (4 + 3 * j) + (j % 2) * 3
            r = max(1.2, hr * (0.62 - 0.1 * j))
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    d = (dx / r) ** 2 + (dy / r) ** 2
                    if d <= 1:
                        C.plot(cv, bx + dx, by + dy, 'W' if dx + dy < 0 else ('~' if d > 0.5 and dx + dy > 1 else 'l'))
        return
    # the head: a bubbly ball, lit from the top-left
    X, Y = C.R.centres(w, h)
    ang = np.arctan2(Y - hy, X - hx)
    rim = hr * (1.0 + 0.16 * np.sin(ang * 3 + wob[0] * 6) + 0.1 * np.sin(ang * 5 + wob[1] * 6))
    m = np.hypot(X - hx, (Y - hy) * 1.05) <= rim
    v = C.R.lambert(C.R.sphere_normal(X, Y, hx, hy, hr, hr))
    cv[m] = np.where(v > 0.62, 'W', np.where(v > 0.28, 'l', '~'))[m]
    # droplets breaking off its sides
    for j in range(2):
        side = -1 if j == 0 else 1
        dx = side * (hr + 1.5 + wob[2 + j] * 1.5)
        dy = -hr * 0.3 - wob[4 + j] * 2
        C.plot(cv, hx + dx, hy + dy, 'W')
        C.plot(cv, hx + dx - side * 0.8, hy + dy + 1, 'l')


def collapse(k, seed=41):
    """The wave (after the round's first hit) bursting harmlessly: 0 the barrels cave in, the back of the wave drains
    forward and a crown of spray bursts up off the crest line; 1 the crown towers over a low sheet of water; 2 it tears
    into droplets arcing out; 3-4 droplets rain down and land in rings as the water flattens into foam; 5-7 the rings
    and the last foam fade. It is what floods the ring, and it stays inside its 282 x 120 band."""
    w, h = WW, WH
    ys, xs = np.mgrid[0:h, 0:w]
    n = C.vnoise((h, w), (10, 30), seed, periodic=(False, False))
    n2 = C.vnoise((h, w), (24, 70), seed + 10, periodic=(False, False))
    edge = (C.vnoise((w,), (24,), seed + 2, periodic=(False,)) * 8).astype(int)[None, :]
    out = C.blank(w, h)
    crest_y = BODY_H + 14
    if k == 0:
        base = full_wave(0)
        keep = ys >= 30 + edge
        out[keep] = base[keep]
        cap = keep & (ys < 33 + edge)
        out[cap] = np.where(n2[cap] > 0.4, 'W', 'l')
        crest = ys >= BODY_H + 2
        out[crest] = np.where(n2[crest] > 0.5, 'W', np.where(n2[crest] > 0.33, 'l', '~'))
        out[(out == '0')] = '%'
    elif k <= 4:
        top = (60, 72, 82, 90)[k - 1] + edge
        thin = (0.12, 0.34, 0.5, 0.62)[k - 1]
        keep = (ys >= top) & (n > thin)
        water = np.where(n2 > 0.6, 'W', np.where(n2 > 0.42, 'l', np.where(n2 > 0.3, '~', '+')))
        if k == 1:
            water = np.where(n2 < 0.36, '=', water)
            water = np.where((ys < top + 2), 'W', water)
        out[keep] = water[keep]
        blob = keep & (out == 'W')
        below = np.zeros_like(blob)
        below[1:, :] = blob[:-1, :] & ~blob[1:, :] & keep[1:, :]
        out[below] = '~'
    else:
        thr = (0.7, 0.78, 0.86)[k - 5]
        patch = (n > thr) & (ys > 92)
        out[patch] = np.where(n2[patch] > 0.5, 'W', 'l')
        rim = np.zeros_like(patch)
        rim[1:, :] = patch[:-1, :] & ~patch[1:, :]
        out[rim] = '~'

    # the crown: separate plumes standing up off the crest line, towering, then tearing into droplets
    rnd = np.random.RandomState(seed + 3)
    x = 4.0
    plumes = []
    while x < w - 4:
        width = rnd.uniform(4.5, 9.5)
        tall = rnd.uniform(0.62, 1.0) * (1.08 - 0.05 * (width - 4.5))
        plumes.append((x + width / 2, width, tall, rnd.uniform(-0.7, 0.7), rnd.randint(0, 9999)))
        x += width + rnd.uniform(3, 8)
    if k <= 2:
        for (xc, width, tall, lean, sd) in plumes:
            _plume(out, xc, crest_y, width * (1.0, 1.0, 0.85)[k], (38, 64, 62)[k] * tall, lean,
                   torn=(0.0, 0.0, 0.62)[k], seed=sd)
    # droplets torn off the plume caps, arcing out and raining down onto the floor, where they land in rings
    rnd = np.random.RandomState(seed + 5)
    for (xc, width, tall, lean, sd) in plumes:
        for j in range(6):
            born = 1 + (j % 2)
            height = 66 * tall
            x0 = xc + rnd.uniform(-width / 2, width / 2)
            y0 = crest_y - height * rnd.uniform(0.6, 1.0)
            vx = rnd.uniform(-3.0, 3.0) + lean
            vy = rnd.uniform(-5.5, -1.5)
            g = 3.4
            floor_y = rnd.uniform(60, 116)
            a = k - born
            if a < 0:
                continue
            x = x0 + vx * a
            y = y0 + vy * a + 0.5 * g * a * a
            if y >= floor_y:
                t_land = (-vy + math.sqrt(max(0.0, vy * vy + 2 * g * (floor_y - y0)))) / g
                since = a - t_land
                if since < 3.0:
                    _ring(out, x0 + vx * t_land, floor_y, 1.4 + since * 1.5,
                          'W' if since < 1 else ('l' if since < 2 else '~'))
                continue
            if 0 <= y < h:
                _droplet(out, x, y, vx, vy + g * a, a)
                if j % 3 == 0:
                    C.plot(out, x + 1, y, 'W')
    return out


# ------------------------------------------------------------------ the parry splash: 32 x 32, pivot (16, 20)
SPLASH_FRAMES = 7
SPLASH_TIMES = [0.03, 0.03, 0.04, 0.04, 0.04, 0.04, 0.04]      # 0.26 s: the shipped splash's length
SPLASH_PIVOT = (16, 20)


def splash(k):
    """A parried wave bursting against the player's guard: 0 the impact flash; 1 a crown of water jets rising off a
    ring; 2 the jets at their height, tips breaking; 3-4 droplets arcing out and falling; 5 they land in tiny rings as
    the big ring thins; 6 the last ripples."""
    w = h = 32
    cv = C.blank(w, h)
    cx, cy = SPLASH_PIVOT
    X, Y = C.R.centres(w, h)
    if k == 0:
        core = ((X - cx) / 5.0) ** 2 + ((Y - cy) / 3.6) ** 2 <= 1
        rim = (((X - cx) / 6.6) ** 2 + ((Y - cy) / 4.8) ** 2 <= 1) & ~core
        cv[rim] = '~'
        cv[core] = 'W'
        for a in range(0, 360, 30):
            r1 = 11 if a % 60 == 0 else 8
            for r in np.linspace(5, r1, 10):
                x = cx + math.cos(math.radians(a)) * r * 1.15
                y = cy + math.sin(math.radians(a)) * r * 0.8
                C.plot(cv, x, y, 'W' if r < r1 - 2.5 else 'l')
        return cv
    ring_r = (0, 8.0, 10.0, 11.5, 12.5, 13.5, 14.5)[k]
    ring_y = cy + 1
    if k <= 4:
        pool = ((X - cx) / (ring_r - 1.5)) ** 2 + ((Y - ring_y) / ((ring_r - 1.5) * 0.36)) ** 2 <= 1
        if k <= 2:
            cv[pool] = '+'
        C.arc(cv, cx, ring_y, ring_r, ring_r * 0.38, 0, 360, 'W' if k <= 2 else 'l',
              gaps=(lambda u: k >= 3 and (int(u * 40) % 5 == 0)))
        C.arc(cv, cx, ring_y + 1, ring_r, ring_r * 0.38, 20, 160, '~')
    else:
        C.arc(cv, cx, ring_y, ring_r, ring_r * 0.38, 0, 360, '~', gaps=(lambda u: int(u * 30) % (2 if k == 5 else 3) == 0))
    # the crown's jets: rising off the ring's back half, their tips breaking into droplets
    jets = [(-7, 0.8), (-4.5, 1.0), (-1.5, 1.15), (1.5, 1.1), (4.5, 1.0), (7, 0.75)]
    if k in (1, 2):
        for (dx, tall) in jets:
            hgt = (0, 6.5, 10.0)[k] * tall
            base = ring_y - 1 + abs(dx) * 0.12
            for i in range(int(hgt) + 1):
                y = base - i
                ch = 'W' if i > hgt - 2.5 else ('l' if (i + int(dx)) % 3 else 'W')
                C.plot(cv, cx + dx * (1 + 0.04 * i), y, ch)
                if i < hgt * 0.5 and abs(dx) > 3:
                    C.plot(cv, cx + dx * (1 + 0.04 * i) + (1 if dx > 0 else -1), y, '~')
            if k == 2:
                C.plot(cv, cx + dx * 1.5, base - hgt - 1.5, 'W')
    # droplets thrown off the jet tips from frame 2
    for j, (dx, tall) in enumerate(jets):
        for m in range(2):
            a = k - 2
            if a < 0:
                continue
            x0 = cx + dx * 1.4
            y0 = ring_y - 1 - 10.0 * tall
            vx = dx * (0.42 + 0.18 * m)
            vy = -1.2 + 0.9 * m
            g = 1.5
            x = x0 + vx * a
            y = y0 + vy * a + 0.5 * g * a * a
            floor_y = ring_y + 1 + (j % 3)
            if y >= floor_y:
                t_land = (-vy + math.sqrt(max(0.0, vy * vy + 2 * g * (floor_y - y0)))) / g
                since = a - t_land
                if since < 2.0:
                    lx = x0 + vx * t_land
                    C.plot(cv, lx - 1, floor_y, 'l' if since < 1 else '~')
                    C.plot(cv, lx + 1, floor_y, 'l' if since < 1 else '~')
                    if since < 1:
                        C.plot(cv, lx, floor_y - 1, 'W')
                continue
            C.plot(cv, x, y, 'W')
            sp = math.hypot(vx, vy + g * a) or 1.0
            C.plot(cv, x - vx / sp, y - (vy + g * a) / sp, 'l')
    return cv


# ------------------------------------------------------------------ the flood's ripple overlay: 64 x 64 tile
RIPPLE_FRAMES = 12
RIPPLE_TIME = 0.1
T64 = 64


def flood_ripple(k, seed=61):
    """Drawn over the flood and clipped to its water (a code hook): rings spreading from three spots a tile on
    staggered beats and glints drifting across, so the standing water never sits dead still. Seamless on all four
    edges and looping; only the flood's own shine and rim keys (^ and "), so it is as semi-transparent as the water."""
    cv = C.blank(T64, T64)
    rings = [(13.5, 17.5, 0), (45.5, 38.5, 4), (25.5, 53.5, 8)]
    for (x0, y0, born) in rings:
        age = (k - born) % RIPPLE_FRAMES
        if age > 6:
            continue
        r = 1.5 + age * 1.6
        ch = '^' if age < 3 else '"'
        C.arc(cv, x0, y0, r, max(1.0, r * 0.42), 0, 360, ch, wrap_x=True, wrap_y=True,
              gaps=(lambda u, age=age: age >= 4 and int(u * 24) % (2 if age >= 5 else 3) == 0))
        if age <= 1:
            C.plot(cv, x0, y0, '^', wrap_x=True, wrap_y=True)
    rnd = np.random.RandomState(seed)
    for i in range(14):
        x0, y0 = rnd.randint(0, T64), rnd.randint(0, T64)
        born = rnd.randint(0, RIPPLE_FRAMES)
        age = (k - born) % RIPPLE_FRAMES
        if age > 5:
            continue
        ln = (2, 3, 4, 4, 3, 2)[age]
        x = x0 + age // 2
        for j in range(ln):
            C.plot(cv, x + j, y0, '^' if 1 <= age <= 3 else '"', wrap_x=True, wrap_y=True)
    return cv
