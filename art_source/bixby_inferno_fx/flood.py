"""bixby_inferno_flood.png: the Inferno breath's fire, one seamless tile the code lays across the cone.

Frame 57x41 texels. The bed is the bottom 29 rows (12..40); rows 0..11 hold flame tips that rise over
the tile above (the code draws the tile below over it). Frames, in order:
  0-1  smoulder   the floor glowing before it catches (loops, faint then strong)
  2-3  ignite     the catch, played once
  4-7  burn       the fire (loops)
  8-10 die-down   played once, ending mostly clear

SEAMS. The flood script plays the looping phases with each tile one frame ahead of the one before it
(BixbyInfernoFloodScript._show_tiles), so a tile's neighbours show OTHER frames of the loop. For a seam to
hold between any two frames, the bed's background is the same in every frame of a loop and wraps both
ways, and no flame, glow or spark comes within SIDE_KEEP columns of the sides. The once-only phases show
one frame on every tile, so they only have to wrap onto themselves.
"""
import random

from firelib import periodic_noise, quantise, put, flame_set, paint_flame, halo, bounds

W, H = 57, 41
BED_TOP = 12          # first bed row
BED_H = H - BED_TOP   # 29
SIDE_KEEP = 1         # columns at each side a flame, glow or spark never reaches


def blank():
    return [['.'] * W for _ in range(H)]


def inside(x, y):
    return SIDE_KEEP <= x <= W - 1 - SIDE_KEEP


def check(shape, what):
    x0, x1, y0, y1 = bounds(shape)
    assert x0 >= SIDE_KEEP + 1 and x1 <= W - 2 - SIDE_KEEP, ('%s crosses a side' % what, x0, x1)
    assert y0 >= 0, ('%s leaves the top' % what, y0)


# ---------------------------------------------------------------- background

# Ember glow between the flames: dark blood lifting to ember in soft blobs taller than they are wide, with
# a few deep pockets. No term is constant down a column (ky = 0), or the two seam columns flames never
# cover would show as a straight line. Frequencies are whole cycles per tile, so it wraps.
EMBER_BG = periodic_noise(W, BED_H, [(3, 1, 1.0), (3, -1, 0.9), (5, 2, 0.45), (5, -2, 0.4), (8, 1, 0.3), (2, 3, 0.25)], seed=21)
BG_STEPS = [(0.0, 'q'), (0.14, 'r'), (0.6, 'n')]


def background(g, steps=BG_STEPS, lift=('q', 'r')):
    """The ember glow, the same in every frame. On the two columns each side that nothing else ever
    reaches, its deepest pockets are lifted one step (lift) so the seam doesn't read as a dark line."""
    for v in range(BED_H):
        for x in range(W):
            k = quantise(EMBER_BG[v][x], steps)
            if (x <= SIDE_KEEP or x >= W - 1 - SIDE_KEEP) and k == lift[0]:
                k = lift[1]
            g[BED_TOP + v][x] = k


# ---------------------------------------------------------------- burn

# Flames: centre column, root row, root width, height, tongues (dx, root dy, height, width, lean, sway).
# Listed back to front: the back row roots high in the bed and licks into the rows above it.
BURN_FLAMES = [
    # back row: four roots on a 14.25-texel pitch, so every gap, the seam's included, is about 5 wide;
    # their root rows are staggered so the tile's hot spots don't line up across the field
    (7, 26, 9, 18, [(0, 0, 16, 5, -0.8, 0.6), (2, -3, 8, 3, 1.6, 0.0)]),
    (21, 23, 9, 18, [(-1, 0, 16, 6, 0.8, -0.7), (3, -4, 9, 3, 2.2, 0.0)]),
    (36, 27, 9, 20, [(0, 0, 18, 6, -0.9, 0.7), (-2, -3, 9, 3, -2.0, 0.0)]),
    (50, 24, 9, 18, [(0, 0, 16, 5, 0.7, -0.6), (-2, -3, 8, 3, -1.6, 0.0)]),
    # front row: three roots on a 19-texel pitch, so every gap, the seam's included, is about 5 wide
    (9, 36, 14, 19, [(-1, 0, 16, 7, -1.0, 0.6), (4, -3, 10, 4, 2.2, -0.3)]),
    (28, 39, 15, 25, [(0, 0, 23, 7, 0.9, 0.9), (-5, -2, 11, 4, -2.4, 0.0), (5, -4, 12, 4, 2.2, -0.3)]),
    (47, 35, 13, 17, [(1, 0, 15, 6, -0.9, -0.6), (-4, -3, 9, 3, -2.0, 0.0)]),
]
# Per loop frame: tongue height scale and sway added, rotated per flame so no two flicker together.
FLICKER = [(1.0, 0.0), (1.22, 1.0), (0.78, 0.0), (1.12, -1.0)]


def flame_shape(cx, by, w, h, tongues, f):
    scale, sway = FLICKER[f]
    tt = [(dx, dy, max(2, int(round(th * scale))), tw, lean, sw + sway) for dx, dy, th, tw, lean, sw in tongues]
    return flame_set(cx, by, w, int(round(h * scale)), tt, phase=0.25 * f), int(round(h * scale))


def burn_frame(t):
    g = blank()
    background(g)
    for i, (cx, by, w, h, tongues) in enumerate(BURN_FLAMES):
        f = (t + i) % 4
        shape, height = flame_shape(cx, by, w, h, tongues, f)
        check(shape, 'burn flame %d' % i)
        halo(g, shape, 'n', clip=inside)
        paint_flame(g, shape, by, height, white_depth=5)
    # sparks rising through the gaps, a few rows higher each frame
    rnd = random.Random(7)
    for j in range(5):
        x = rnd.randint(SIDE_KEEP + 1, W - 2 - SIDE_KEEP)
        y0 = rnd.randint(2, 30)
        y = (y0 - 5 * t) % 34
        if g[y][x] in '.qr':
            put(g, x, y, 'P' if j % 2 else 'Y')
    return g


# ---------------------------------------------------------------- smoulder

# The glowing pools sit where the burn's flames root, so the catch reads as these hot spots bursting.
POOLS = [(cx, by - 1, w) for cx, by, w, h, tt in BURN_FLAMES]
CRUST_STEPS = [(0.0, 'q'), (0.42, 'r'), (0.86, 'n')]


def interior(x):
    return SIDE_KEEP + 1 <= x <= W - 2 - SIDE_KEEP


def pool(g, cx, cy, w, level, swell):
    """An ember pool: a flat oval glowing from its centre. level 0..2 sets how hot its middle gets;
    swell grows it a little (the pulse)."""
    rx, ry = w / 2.0 - 1.5, max(1.6, w * 0.2)
    hot = [('n', 1.0), ('N', 0.72), ('p', 0.45), ('P', 0.22)][: 2 + level]
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d > 1.0 or not interior(x):
                continue
            k = None
            for key, lim in hot:
                if d <= lim * (1.15 if swell else 1.0):
                    k = key
            if k:
                put(g, x, y, k)


def crust(g, steps):
    """The floor before it catches or after it cools: the ember field darkened and mottled. No crack
    lines: any line network in a periodic field repeats on the tile grid and shows across the cone."""
    for v in range(BED_H):
        for x in range(W):
            g[BED_TOP + v][x] = quantise(EMBER_BG[v][x] * 0.8 + 0.1, steps)


# Scattered embers that twinkle between the two smoulder frames: (column, bed row), all off the seams.
EMBERS = [(5, 3), (13, 9), (17, 1), (25, 6), (31, 12), (33, 2), (42, 8), (47, 4), (53, 10), (11, 17), (40, 16),
          (23, 20), (3, 21), (51, 19), (30, 27), (15, 25), (45, 23)]


def smoulder_frame(t):
    g = blank()
    crust(g, CRUST_STEPS)
    for i, (x, v) in enumerate(EMBERS):
        if (i + t) % 2 == 0:
            put(g, x, BED_TOP + v, 'N' if i % 3 else 'p')
        else:
            put(g, x, BED_TOP + v, 'n')
    for i, (cx, cy, w) in enumerate(POOLS):
        swell = (i + t) % 2 == 0
        pool(g, cx, cy, w, (2 if swell else 1) - (1 if w < 10 else 0), swell)
    # tiny licks off the big pools, swapping between the two frames
    for i, (cx, cy, w) in enumerate(POOLS):
        if (i + t) % 2 == 0 and w >= 10:
            h = 3 + (i % 3)
            for j in range(h):
                put(g, cx + (1 if (j > h // 2 and i % 2) else 0), int(cy) - 2 - j, 'N' if j < h - 1 else 'n')
            put(g, cx, int(cy) - 2, 'p')
    # a few sparks drifting up over the tile above
    rnd = random.Random(40 + t)
    for j in range(3):
        put(g, rnd.randint(SIDE_KEEP + 2, W - 3 - SIDE_KEEP), rnd.randint(1, 11), 'N' if j else 'p')
    return g


# ---------------------------------------------------------------- ignite

def ignite_frame(t):
    """t 0: the pools flash and the flames sprout; t 1: they overshoot, taller and hotter than the burn."""
    g = blank()
    background(g, steps=[(0.0, 'r'), (0.3, 'n'), (0.75, 'N')], lift=('r', 'r'))
    scale = 0.45 if t == 0 else 1.2
    for i, (cx, by, w, h, tongues) in enumerate(BURN_FLAMES):
        tt = [(dx, dy, max(2, int(round(th * scale))), tw, lean, sw) for dx, dy, th, tw, lean, sw in tongues]
        height = int(round(h * scale))
        shape = flame_set(cx, by, w, height, tt, phase=0.1)
        shape = {(x, y) for (x, y) in shape if y >= 0}
        check(shape, 'ignite flame %d' % i)
        halo(g, shape, 'N', over=('r', 'n'), clip=inside)
        paint_flame(g, shape, by, height, bands=('p', 'P', 'Y', 'W'), white_depth=2)
    rnd = random.Random(90 + t)
    for j in range(8 if t else 5):
        x = rnd.randint(SIDE_KEEP + 2, W - 3 - SIDE_KEEP)
        y = rnd.randint(0, 20)
        if g[y][x] in '.qrn':
            put(g, x, y, 'Y' if j % 2 else 'P')
    return g


# ---------------------------------------------------------------- die-down

def puff(g, x, y, r):
    """A smoke puff like the fire trail's: a cloud of three bumps, lit from the upper left. Warm greys
    from the redesign's bone ramp (outline z, body y, highlight x): smoke lit by the fire under it."""
    body = set()
    for bx, by, br in ((x, y, r), (x - r + 1, y + 1, r - 1), (x + r - 1, y + 1, r - 1)):
        br = max(1, br)
        for yy in range(by - br, by + br + 1):
            for xx in range(bx - br, bx + br + 1):
                if (xx - bx) ** 2 + (yy - by) ** 2 <= br * br + br * 0.6:
                    body.add((xx, yy))
    for (xx, yy) in body:
        if not interior(xx) or yy < 0:
            continue
        edge = any(n not in body for n in ((xx - 1, yy), (xx + 1, yy), (xx, yy - 1), (xx, yy + 1)))
        lit = (xx - x) + (yy - y) < -r * 0.6
        put(g, xx, yy, 'z' if edge else ('x' if lit else 'y'))


def die_frame(t):
    """t 0: the flames sink and redden; t 1: embers in cooling ash, smoke leaving; t 2: mostly clear."""
    g = blank()
    if t == 0:
        background(g, steps=[(0.0, 'q'), (0.25, 'r'), (0.8, 'n')])
        for i, (cx, by, w, h, tongues) in enumerate(BURN_FLAMES):
            tt = [(dx, dy, max(2, int(round(th * 0.55))), max(2, tw - 1), lean, sw) for dx, dy, th, tw, lean, sw in tongues]
            height = int(round(h * 0.55))
            shape = flame_set(cx, by, w - 2, height, tt, phase=0.6)
            check(shape, 'die flame %d' % i)
            halo(g, shape, 'n', clip=inside)
            paint_flame(g, shape, by, height, bands=('n', 'N', 'p', 'P'), white=None)
        return g
    if t == 1:
        # the crust again, cooling: charcoal ash in the deep pockets, the pools down to embers, and the
        # front row's pools sending up smoke
        crust(g, [(0.0, 'c'), (0.14, 'q'), (0.5, 'r')])
        for i, (x, v) in enumerate(EMBERS):
            if i % 2:
                put(g, x, BED_TOP + v, 'n')
        for i, (cx, cy, w) in enumerate(POOLS):
            pool(g, cx, cy, w, 0, False)
        # smoke floating up off the back row's pools, clear of the bed like the trail's puffs
        for i, (cx, cy, w) in enumerate(POOLS[:4]):
            if i % 2 == 0:
                puff(g, cx + 1, 5, 2)
            else:
                puff(g, cx - 1, 8, 2)
        return g
    # t == 2: mostly clear. Ash flecks and a last ember at each big pool; the smoke has lifted and thinned
    for v in range(BED_H):
        for x in range(W):
            if not interior(x):
                continue
            e = EMBER_BG[v][x]
            if e > 0.8 and (x * 7 + v * 3) % 5 == 0:
                g[BED_TOP + v][x] = 'r'
            elif e < 0.12 and (x + v) % 3 == 0:
                g[BED_TOP + v][x] = 'c'
    for i, (cx, cy, w) in enumerate(POOLS):
        if w >= 10:
            put(g, cx, int(cy), 'N')
            put(g, cx + 1, int(cy), 'n')
            put(g, cx - 2, int(cy) - 1, 'n')
    # the smoke has lifted and thinned to wisps
    for i, (cx, cy, w) in enumerate(POOLS[:4]):
        x0, y0 = cx + (2 if i % 2 else 0), (2 if i % 2 == 0 else 4)
        for j, (dx, dy) in enumerate(((0, 0), (1, -1), (2, -1), (3, -2))):
            put(g, x0 + dx, y0 + dy, 'z' if j in (0, 3) else 'y')
    return g


def frames():
    return ([smoulder_frame(t) for t in range(2)] + [ignite_frame(t) for t in range(2)]
            + [burn_frame(t) for t in range(4)] + [die_frame(t) for t in range(3)])
