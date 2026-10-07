"""The charge at Greyson's raised cannon and the release as he throws it down.

CHARGE: 80 x 80 texels, 12 frames = three stages of 4-frame loops (0-3 small, 4-7 building, 8-11
full), pivot (40, 40) on the spirit pose's muzzle. Dark energy streams in from all round and dies
into a pulsing core while arcs crackle round it.
RELEASE: 80 x 80, 6 frames once, pivot (40, 40) on the throw pose's muzzle. Drawn firing DOWN (+y),
the way the beam's first run leaves him (his muzzle to the goal is always near straight down).
"""
import math

import numpy as np

import mb_core as C
import mb_bursts as X

QW = 80
STAGE_FRAMES = 4
CHARGE_FRAMES = 12
RELEASE_FRAMES = 6


def _tendrils(g, pal, f, stage, variant, count, r_out, r_in):
    """Dark energy dragged in: smooth black tendrils spiralling into the halo, crimson on their
    outer edge, fading to maroon at the tail; each slides a quarter of the way in a frame, looping
    in 4."""
    c = QW / 2.0
    r = C.rng('chargeA-tendrils-%d-%d' % (stage, variant))
    for k in range(count):
        ang = 2 * math.pi * k / count + float(r.uniform(-0.3, 0.3))
        phase = float(r.uniform(0, 1))
        t = (phase + f * 0.25) % 1.0
        head = r_out - (r_out - r_in) * t
        length = 9 + 7 * (1 - t)
        core = C.blank(QW, QW)
        tail = C.blank(QW, QW)
        outer = C.blank(QW, QW)
        prev = None
        for i in range(int(length) + 1):
            rr = head + i
            a = ang + 1.1 * (rr - r_in) / (r_out - r_in)
            pt = (c + rr * math.cos(a), c + rr * math.sin(a))
            # the outer side of the curl: further round the spiral's direction of travel
            o = (c + (rr + 1.0) * math.cos(a + 0.05), c + (rr + 1.0) * math.sin(a + 0.05))
            if prev is not None:
                tgt = core if i < length * 0.6 else tail
                C.draw_line(tgt, int(prev[0]), int(prev[1]), int(pt[0]), int(pt[1]), 1)
                if i < length * 0.6:
                    C.put(outer, o[0], o[1], 1)
            prev = pt
        mc, mt, mo = core > 0, tail > 0, outer > 0
        g[mo & (g == 0)] = pal['c']
        g[mt & (g == 0)] = pal['m']
        g[mc & ((g == 0) | (g == pal['c']) | (g == pal['m']))] = pal['k']


def _streaks(g, pal, f, stage, variant, keys, count, r_out, r_in, speed):
    """Dark energy pulled in: streaks along the radius that slide inwards a quarter of their run
    each frame, looping in 4, brightening as they near the core."""
    c = QW / 2.0
    r = C.rng('chargeA-streaks-%d-%d' % (stage, variant))
    for k in range(count):
        ang = 2 * math.pi * k / count + float(r.uniform(-0.2, 0.2))
        curl = float(r.uniform(0.15, 0.35))              # they spiral in a little
        phase = float(r.uniform(0, 1))
        t = (phase + f * speed) % 1.0                   # 0 at the rim, 1 at the core
        head = r_out - (r_out - r_in) * t
        length = 5 + 7 * (1 - t)
        for i in range(int(length)):
            rr = head + i
            if rr > r_out:
                break
            a = ang + curl * (rr - r_in) / (r_out - r_in)
            x = int(math.floor(c + rr * math.cos(a)))
            y = int(math.floor(c + rr * math.sin(a)))
            if 0 <= x < QW and 0 <= y < QW and g[y, x] == 0:
                u = i / max(length, 1)
                g[y, x] = pal[keys[0] if u < 0.25 else keys[1] if u < 0.6 else keys[2]]


def charge_a(pal, f, variant=0):
    """Take A: frame f of 12, three stages of 4. Dark crimson energy streams in and dies into a
    white-hot core ringed red-hot, pulsing; black lightning crackles round it, wider each stage."""
    stage, k = divmod(f, STAGE_FRAMES)
    g = C.blank(QW, QW)
    c = QW / 2.0
    dx, dy, d, a = X._polar(QW, QW, c, c)
    r = C.rng('chargeA-%d-%d' % (variant, f))
    pulse = [0.0, 0.8, 1.4, 0.6][k]
    core = [3.0, 5.0, 7.0][stage] + pulse
    # the halo round the core
    n = C.fbm_periodic(QW, QW, [(10, 10, 1.0)], 931 + f, period_x=QW)
    halo_r = core * [2.2, 2.3, 2.4][stage]
    halo = halo_r + 1.5 * n
    g[d < halo] = pal['m']
    g[d < halo * 0.78] = pal['c']
    g[d < core + 1.5] = pal['s']
    g[d < core] = pal['h']
    g[d < core - 1.4] = pal['w']
    # dark tendrils spiralling in from the dark, black with crimson edges, and hot streaks between
    _tendrils(g, pal, k, stage, variant, [5, 7, 9][stage], [26, 32, 38][stage], halo_r * 0.95)
    _streaks(g, pal, k, stage, variant, ('h', 's', 'c'), [10, 14, 18][stage], [30, 34, 38][stage],
             halo_r * 0.9, 0.25)
    # black lightning crackling round the core, reaching further each stage
    for b in range([2, 3, 5][stage]):
        ang = float(r.uniform(0, 2 * math.pi))
        r0 = core + 1
        pts = X._jag_ray(r, int(c + r0 * math.cos(ang)), int(c + r0 * math.sin(ang)), ang,
                         [7, 11, 16][stage], 0.7, (2, 3))
        X._hot_bolt(g, pal, pts)
    # sparks spat off the halo
    for s in range([3, 5, 8][stage]):
        ang = float(r.uniform(0, 2 * math.pi))
        rr = halo_r + float(r.uniform(1, 6))
        x, y = int(c + rr * math.cos(ang)), int(c + rr * math.sin(ang))
        if 0 <= x < QW and 0 <= y < QW and g[y, x] == 0:
            g[y, x] = pal['h' if s % 2 else 'p']
    return g


def charge_glow_a(gpal, f):
    stage, k = divmod(f, STAGE_FRAMES)
    g = C.blank(QW, QW)
    _, _, d, _ = X._polar(QW, QW, QW / 2.0, QW / 2.0)
    size = [16, 24, 32][stage] + [0, 2, 3, 1][k]
    I = 1.0 - d / size
    g[I > 0.0] = gpal['1']
    g[I > 0.4] = gpal['2']
    g[I > 0.7] = gpal['3']
    return g


def release_a(pal, f, variant=0):
    """Take A: the throw: a white-hot muzzle flash with a cone of fire blasting down, black
    lightning ripping out of it, then a ring and smoke curling off the muzzle."""
    g = C.blank(QW, QW)
    c = QW / 2.0
    dx, dy, d, a = X._polar(QW, QW, c, c)
    r = C.rng('releaseA-%d-%d' % (variant, f))
    down = math.pi / 2
    bias = np.cos(X._ang_diff(a, down))
    pb = np.clip(bias, 0, 1)
    n = C.fbm_periodic(QW, QW, [(10, 10, 1.0), (5, 5, 0.5)], 951 + f + variant, period_x=QW)
    if f == 0:
        for ang, ln, wd in ((down, 34, 12), (down - 0.5, 22, 7), (down + 0.5, 22, 7), (0, 16, 6),
                            (math.pi, 16, 6), (-down, 12, 5), (-down - 0.8, 10, 4), (-down + 0.8, 10, 4)):
            X.spike(g, pal, c, c, ang, ln, wd)
        X._bands(g, pal, 1.0 - d / 10.0, ((0.0, 'h'), (0.3, 'w')))
    elif f == 1:
        cone = (d < 10 + 18 * pb ** 2 + 3 * n) & (pb > 0.35)
        g[cone] = pal['c']
        g[cone & (d < 9 + 18 * pb ** 2 + 2 * n)] = pal['s']
        g[cone & (d < 6 + 12 * pb ** 3)] = pal['h']
        X._bands(g, pal, 1.0 - d / 9.0, ((0.0, 's'), (0.3, 'h'), (0.55, 'w')))
        ring = (d > 11) & (d < 13.5)
        g[ring] = pal['h']
        for b in range(4):
            ang = down + float(r.uniform(-1.3, 1.3))
            X._hot_bolt(g, pal, X._jag_ray(r, int(c + 8 * math.cos(ang)), int(c + 8 * math.sin(ang)), ang, 18, 0.55))
    elif f == 2:
        cone = (d < 12 + 16 * pb ** 2 + 4 * n) & ((pb > 0.3) | (d < 10)) & (n > -0.35)
        g[cone] = pal['m']
        g[cone & (d < 10 + 13 * pb ** 2 + 3 * n)] = pal['c']
        g[cone & (d < 8 + 8 * pb ** 2)] = pal['s']
        g[d < 5] = pal['h']
        ring = (d > 17) & (d < 19.5) & (n > -0.3)
        g[ring] = pal['s']
        g[ring & (d < 18.3)] = pal['h']
        for b in range(3):
            ang = down + float(r.uniform(-1.4, 1.4))
            X._hot_bolt(g, pal, X._jag_ray(r, int(c + 6 * math.cos(ang)), int(c + 6 * math.sin(ang)), ang, 22, 0.55))
    elif f == 3:
        wisp = (d < 10 + 12 * pb + 3 * n) & (d > 5 + 2 * n) & (n > 0.0)
        g[wisp] = pal['m']
        g[wisp & (n > 0.35)] = pal['c']
        ring = (d > 20) & (d < 22) & (n > 0.1)
        g[ring] = pal['c']
    elif f == 4:
        wisp = (d < 12 + 12 * pb + 3 * n) & (d > 8 + 3 * n) & (n > 0.3)
        g[wisp] = pal['v']
        g[wisp & (n > 0.5)] = pal['m']
    er = C.rng('releaseA-embers-%d' % variant)
    for k in range(16):
        ang = down + float(er.normal(0, 0.9))
        speed = float(er.uniform(4.0, 7.0))
        age = f - 1
        if age < 0 or age > 4:
            continue
        dist = 8 + speed * age
        x = int(round(c - 0.5 + dist * math.cos(ang)))
        y = int(round(c - 0.5 + dist * math.sin(ang)))
        if 0 <= x < QW and 0 <= y < QW and g[y, x] in (0, pal['v']):
            g[y, x] = pal[['h', 'p', 's', 'r', 'c'][age]]
    return g


def release_glow_a(gpal, f):
    g = C.blank(QW, QW)
    _, _, d, a = X._polar(QW, QW, QW / 2.0, QW / 2.0)
    pb = np.clip(np.cos(X._ang_diff(a, math.pi / 2)), 0, 1)
    size = [28, 30, 24, 14, 0, 0][f]
    if size == 0:
        return g
    I = 1.0 - d / (size * (1 + 0.4 * pb))
    g[I > 0.0] = gpal['1']
    g[I > 0.4] = gpal['2']
    if f <= 2:
        g[I > 0.7] = gpal['3']
    return g
