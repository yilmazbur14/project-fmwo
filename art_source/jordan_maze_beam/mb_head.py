"""The beam's racing head, drawn facing right; the code rotates it to the run it is on.

HEAD: 64 x 48 texels a frame, 6 frames looping. ATTACH (the line's end, where the body strip runs
in from the left) at texel (34, 24): the centre line is between rows 23 and 24, like the body's
between 15 and 16. The front reaches to x = 63, the smear trails back to x = 0 over the body.
"""
import math

import numpy as np

import mb_core as C

HW, HH = 64, 48
HEAD_FRAMES = 6
ATTACH = (34, 24)
HCY = 24.0


def _field_comet(f, variant, nucleus_x=44.0, radius=12.5, tail_len=44.0, stretch=1.0):
    """Intensity of a comet facing right: a nucleus and a tapering, dimming tail of smear."""
    ys, xs = np.mgrid[0:HH, 0:HW]
    px, py = xs + 0.5, ys + 0.5
    dy = py - HCY
    dx = px - nucleus_x
    # the nucleus: a disc, a little squashed front to back (it is moving fast)
    dn = np.sqrt((dx / (radius * 1.05)) ** 2 + (dy / radius) ** 2)
    i_n = 1.0 - dn
    # the tail: half-height tapering back from the nucleus
    back = np.clip((nucleus_x - px) / tail_len, 0.0, 1.0)
    half = radius * (1.0 - back) ** 0.75 * stretch + 0.01
    i_t = (1.0 - np.abs(dy) / half) * (1.0 - back) ** 0.55
    i_t[px > nucleus_x] = -1
    streak = C.fbm_periodic(HW, HH, [(16, 2, 1.0), (8, 1, 0.5)], 301 + variant, period_x=HW)
    streak = np.roll(streak, 5 * f, axis=1)
    I = np.maximum(i_n, i_t) + 0.16 * streak * (px < nucleus_x + 4)
    return I, dx, dy


def _teardrop(front_x, back_x, half_h, sharp=1.8):
    """Intensity of a teardrop pointing right: 1 on its axis, 0 at its edge."""
    ys, xs = np.mgrid[0:HH, 0:HW]
    px, py = xs + 0.5, ys + 0.5
    u = (px - back_x) / (front_x - back_x)          # 0 at the back, 1 at the tip
    inside_u = (u >= 0) & (u <= 1)
    # half-height: round at the back, a point at the front
    prof = np.where(u < 0.35, np.sqrt(np.clip(1 - ((0.35 - u) / 0.35) ** 2, 0, 1)),
                    np.clip(1 - (u - 0.35) / 0.65, 0, 1) ** (1 / sharp))
    hh = half_h * np.clip(prof, 0, 1) + 1e-6
    return np.where(inside_u, 1.0 - np.abs(py - HCY) / hh, -1.0)


def head_a(pal, f, variant=0):
    """Take A, Hellbolt: the coil's two strands of black lightning converge into a serrated black
    spearhead rimmed white-hot, a white-hot heart behind it, a crescent bow shock torn through the
    dark ahead of it, and its red-hot coma swept back into flame spikes and smear."""
    r = C.rng('headA-%d-%d' % (variant, f))
    ys, xs = np.mgrid[0:HH, 0:HW]
    px, py = xs + 0.5, ys + 0.5
    dy = py - HCY
    # the coma and its tail of smear
    I_coma = _teardrop(58.0, 20.0, 12.5, 1.5)
    tail = np.clip((32.0 - px) / 32.0, 0, 1)
    I_tail = (1.0 - np.abs(dy) / (10.0 * (1 - tail) + 0.5)) * (1 - tail) ** 0.6 - 0.04
    I_tail[px > 32] = -1
    streak = np.roll(C.fbm_periodic(HW, HH, [(16, 2, 1.0), (8, 1, 0.5)], 301 + variant, period_x=HW), 6 * f, axis=1)
    I = np.maximum(I_coma, I_tail) + 0.14 * streak * (px < 44)
    g = C.blank(HW, HH)
    for t, k in ((0.0, 'm'), (0.22, 'c'), (0.50, 's')):
        g[I > t] = pal[k]
    # the white-hot heart: the core swelling into a long diamond behind the blade
    heart = _teardrop(50.0, 26.0, 5.5, 1.1)
    g[heart > 0.0] = pal['h']
    g[heart > 0.25] = pal['w']
    # swept-back flame spikes off the coma, three a side, flickering
    for sgn in (-1, 1):
        for k, (bx, bl, hl) in enumerate(((49, 9, 8), (40, 11, 10), (30, 10, 7))):
            jitter = int(r.integers(-1, 2))
            root_y = HCY + sgn * (7.5 if k == 0 else 9.0)
            tip = (bx - bl - 4 + jitter, HCY + sgn * (hl + 7 + jitter))
            m = C.polygon_mask(HW, HH, [(bx + 2, root_y), tip, (bx - bl, root_y - sgn * 1.0)])
            g[m & ((g == 0) | (g == pal['m']))] = pal['c']
            core = C.polygon_mask(HW, HH, [(bx, root_y), (tip[0] + 3, tip[1] - sgn * 2.5),
                                           (bx - bl + 2, root_y - sgn * 0.5)])
            g[core & (g == pal['c'])] = pal['s']
            g[C.dilate(m, 1) & ~m & (g == 0)] = pal['m']
    # the spearhead: a serrated black blade, rimmed white-hot at its point, red-hot behind
    tip_x = 60.0
    blade = [(44.0, HCY - 5.5), (48.0, HCY - 4.0), (50.0, HCY - 6.5), (53.5, HCY - 3.5), (55.5, HCY - 4.5),
             (tip_x, HCY), (55.5, HCY + 4.5), (53.5, HCY + 3.5), (50.0, HCY + 6.5), (48.0, HCY + 4.0),
             (44.0, HCY + 5.5), (46.5, HCY)]
    bm = C.polygon_mask(HW, HH, blade)
    rim = C.dilate(bm, 1) & ~bm
    front = rim & (px > 51.0)
    g[rim] = pal['s']
    g[front] = pal['h']
    g[bm] = pal['k']
    # a hairline of red-hot splitting the blade along its axis, flickering
    if f % 2 == 0:
        for x in range(47, 57):
            if bm[int(HCY) - (x % 2), x]:
                g[int(HCY) - (x % 2), x] = pal['c']
    # the coil's two strands, converging from the body into the blade's barbs
    for sgn in (-1, 1):
        x, y = 0, int(HCY + sgn * (7 + r.integers(-1, 2)))
        pts = [(x, y)]
        target = (45, int(HCY + sgn * 5))
        while x < target[0] - 3:
            x += int(r.choice([2, 3, 4]))
            want = y + (target[1] - y) * 0.35
            y = int(round(want + r.choice([-2, -1, 0, 1, 2])))
            pts.append((x, y))
        pts.append(target)
        _bolt(g, pal, pts, spark=False)
    # the bow shock: a crescent a gap ahead of the point, pulsing out and in
    gap = [0.0, 1.0, 2.0, 1.0, 0.0, 1.0][f % 6]
    shock_x = 61.5 + gap - 2.0
    arc = (np.abs(px - (shock_x + 1.6 - 0.07 * dy ** 2)) < 0.9) & (np.abs(dy) < 13.5) & ~bm & ~rim
    g[arc & (np.abs(dy) >= 3.0)] = pal['s']
    g[arc & (np.abs(dy) < 6.0) & (np.abs(dy) >= 3.0)] = pal['h']
    g[arc & (np.abs(dy) >= 10)] = pal['c']
    # smear lines trailing off the coma
    for k in range(14):
        y = int(HCY + r.normal(0, 6.5))
        if not 0 <= y < HH:
            continue
        x1 = int(r.integers(16, 34))
        length = int(r.integers(8, 24))
        for i in range(length):
            x = x1 - i
            if x < 0:
                break
            if g[y, x] in (0, pal['m']):
                fade = i / max(length, 1)
                g[y, x] = pal['s'] if fade < 0.25 else (pal['c'] if fade < 0.6 else pal['m'])
    # black lightning spat ahead of the point
    for b in range(2):
        sgn = -1 if (b + f) % 2 else 1
        x, y = 59, int(HCY + sgn * 2)
        pts = [(x, y)]
        for j in range(int(r.integers(2, 4))):
            x += int(r.choice([1, 1, 2]))
            y += sgn * int(r.integers(1, 4))
            pts.append((min(x, HW - 1), int(np.clip(y, 0, HH - 1))))
        _bolt(g, pal, pts)
    # sparks thrown back off the spikes
    for k in range(6):
        x = int(r.integers(12, 48))
        y = int(HCY + (1 if k % 2 else -1) * r.integers(14, 23))
        if 0 <= y < HH and g[y, x] == 0:
            g[y, x] = pal['h' if k % 3 == 0 else 'p']
    return g


def _bolt(g, pal, pts, spark=True):
    m = C.blank(HW, HH)
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        C.draw_line(m, xa, ya, xb, yb, 1)
    mb = m > 0
    ring = C.dilate(mb, 1) & ~mb
    inside = g > 0
    dark = (g == pal['c']) | (g == pal['m']) | (g == pal['v']) | (g == pal['d'])
    g[ring & inside & dark] = pal['s']
    g[ring & ~inside] = pal['m']
    g[mb] = pal['k']
    tx, ty = pts[-1]
    if spark and 0 <= ty < HH and 0 <= tx < HW:
        g[ty, tx] = pal['h']


def head_glow_a(gpal, f):
    ys, xs = np.mgrid[0:HH, 0:HW]
    d = np.sqrt(((xs + 0.5 - 44) / 22.0) ** 2 + ((ys + 0.5 - HCY) / 20.0) ** 2)
    tail = (xs + 0.5 < 44) & (np.abs(ys + 0.5 - HCY) < 14 * (xs + 0.5) / 44.0)
    pulse = 0.05 * math.sin(f * math.pi / 3)
    g = C.blank(HW, HH)
    g[(d < 1.0 + pulse) | tail] = gpal['1']
    g[(d < 0.72 + pulse)] = gpal['2']
    g[(d < 0.45 + pulse)] = gpal['3']
    return g
