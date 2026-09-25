"""bixby_inferno_edge.png: the fire along the cone's slanted RIGHT edge (the code flips it for the left).

Frame 30x48 texels, 11 frames in the flood's order (smoulder 0-1, ignite 2-3, burn 4-7, die-down 8-10).

GEOMETRY. Drawn for the code's cone: half-angle 65 degrees from vertical, so the right edge runs down to
the right 25 degrees below horizontal. tan(25) = 0.4663 is taken as 7/15 (0.4667): a 30-texel piece drops
exactly 14 rows, so the stair pattern repeats piece to piece, and across the whole 570-texel floor it
drifts from a true 25-degree line by under a quarter of a texel.
  - The edge line enters a frame at texel (0, 22) and leaves at (30, 36): LINE_Y0 + round(x * 7 / 15).
    Its steps run 2 texels wide, with one 3 wide every 15 columns.
  - PIVOT (0, 22): put it on the cone's edge line. Pieces tile along the edge at +(30, 14) texels =
    +(90, 42) px, the first with its pivot on the apex.
  - Above the line is outside the cone (the safe corner): flame tongues lick up and outward there.
  - Below the line is the cone: a root band 3-5 texels deep covers the flood's clipped edge and fades into
    it, so the clip line never shows.
  - Flipped for the left edge, the pivot is (30, 22) (the frame's top-right side, 22 down), the line leaves
    at (0, 36), and pieces tile at (-90, +42) px.

SEAMS. Pieces meet at their left and right columns, and the looping phases play neighbours on different
frames (as the flood does). So the root band on columns 0-1 and 28-29 is the same in every frame of a
loop, and no tongue, glow or spark comes within 2 columns of the sides.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from firelib import periodic_noise, quantise, put, flame_set, paint_flame, halo, bounds  # noqa: E402

W, H = 30, 48
LINE_Y0 = 22
RISE, RUN = 7, 15       # the slope, 7 rows down per 15 across
KEEP = 2


def line_y(x):
    """The edge line's row at column x (the first row inside the cone): LINE_Y0 + round(x * 7 / 15)."""
    return LINE_Y0 + (2 * RISE * x + RUN) // (2 * RUN)


def blank():
    return [['.'] * W for _ in range(H)]


def interior(x):
    return KEEP <= x <= W - 1 - KEEP


def check(shape, what):
    x0, x1, y0, y1 = bounds(shape)
    assert x0 >= KEEP and x1 <= W - 1 - KEEP, ('%s crosses a side' % what, x0, x1)
    assert y0 >= 0 and y1 < H, ('%s leaves the frame' % what, y0, y1)


# How deep the root band reaches below the line, per column: a wavy lower edge, period 32 so it wraps.
DEPTH = periodic_noise(W, 1, [(1, 0, 1.0), (3, 0, 0.5), (5, 0, 0.3)], seed=5)[0]


def band(g, keys, depth_lo, depth_hi, static=True):
    """The root band: keys[d] at d texels below the line, d < depth(x). keys run hot (at the line) to cool."""
    for x in range(W):
        depth = int(round(depth_lo + (depth_hi - depth_lo) * DEPTH[x]))
        for d in range(depth):
            k = keys[min(d, len(keys) - 1)]
            put(g, x, line_y(x) + d, k)


# Tongues rooted on the line: root column, root width, height above the line, lean (texels, + is outward
# = right), tongues [(dx, root dy, height, width, lean, sway)] measured from the root blob.
BURN_TONGUES = [
    (6, 9, 15, 1.4, [(0, 0, 14, 5, 1.4, 0.5), (-2, -3, 7, 3, -1.2, 0.0)]),
    (12, 10, 19, 1.8, [(0, 0, 18, 6, 1.8, -0.6), (3, -4, 8, 3, 2.4, 0.0)]),
    (18, 8, 14, 1.2, [(0, 0, 13, 5, 1.2, 0.4), (-2, -3, 6, 2, -1.0, 0.0)]),
    (24, 7, 11, 0.6, [(0, 0, 10, 4, 0.6, -0.4)]),
]
FLICKER = [(1.0, 0.0), (1.2, 0.6), (0.8, 0.0), (1.1, -0.6)]


def tongues(g, spec, f_of, scale_all=1.0, bands=('N', 'p', 'P', 'Y'), white='W', white_depth=3, halo_key='n'):
    for i, (rx, w, h, lean, tt) in enumerate(spec):
        f = f_of(i)
        sc, sw = FLICKER[f]
        sc *= scale_all
        base = line_y(rx) + 3
        t2 = [(dx, dy, max(2, int(round(th * sc))), tw, ln, s + sw) for dx, dy, th, tw, ln, s in tt]
        height = max(2, int(round(h * sc)))
        shape = flame_set(rx, base, w, height, t2, phase=0.3 * f)
        check(shape, 'edge tongue %d' % i)
        if halo_key:
            halo(g, shape, halo_key, over=('.', 'q', 'r'), clip=lambda x, y: interior(x))
        paint_flame(g, shape, base, height, bands=bands, white=white, white_depth=white_depth)


def burn_frame(t):
    g = blank()
    band(g, ['N', 'N', 'n', 'n', 'r'], 3, 5)
    tongues(g, BURN_TONGUES, lambda i: (t + i) % 4)
    rnd = random.Random(12)
    for j in range(3):
        x = rnd.randint(KEEP + 1, W - 2 - KEEP)
        y = (rnd.randint(0, 14) - 4 * t) % 15 + max(0, line_y(x) - 24)
        if g[y][x] == '.' and y < line_y(x) - 2:
            put(g, x, y, 'P' if j % 2 else 'Y')
    return g


def smoulder_frame(t):
    """The boundary glowing: a hot seam along the line over the dark crust, embers twinkling on it."""
    g = blank()
    band(g, ['N', 'n', 'r', 'r', 'q', 'q', 'r', 'r'], 6, 9)
    for x in range(KEEP, W - KEEP):
        if (x + t) % 4 == 0:
            put(g, x, line_y(x), 'p')
            put(g, x, line_y(x) + 1, 'N')
        if (x * 3 + t) % 7 == 0:
            put(g, x, line_y(x) + 2, 'n')
    for i, x in enumerate((6, 13, 20, 25)):
        if (i + t) % 2 == 0:
            put(g, x, line_y(x) - 1, 'N')
            put(g, x, line_y(x) - 2 - (i % 2), 'n')
    return g


def ignite_frame(t):
    g = blank()
    band(g, ['P', 'p', 'N', 'n', 'n'], 3, 5)
    tongues(g, BURN_TONGUES, lambda i: 0, scale_all=0.5 if t == 0 else 1.25,
            bands=('p', 'P', 'Y', 'W'), white_depth=2, halo_key='N')
    return g


def die_frame(t):
    g = blank()
    if t == 0:
        band(g, ['N', 'n', 'n', 'r', 'r'], 3, 5)
        tongues(g, BURN_TONGUES, lambda i: 2, scale_all=0.55, bands=('n', 'N', 'p', 'P'), white=None)
    elif t == 1:
        band(g, ['n', 'r', 'q', 'q', 'c', 'q'], 4, 7)
        for i, x in enumerate((7, 19)):
            put(g, x, line_y(x), 'N')
            put(g, x + 1, line_y(x), 'n')
        for x, y in ((11, 12), (22, 19)):
            for (dx, dy, k) in ((0, 0, 'z'), (1, 0, 'y'), (2, 0, 'z'), (1, -1, 'z'), (0, 1, 'z'), (1, 1, 'z')):
                put(g, x + dx, y + dy, k)
    else:
        for x in range(KEEP, W - KEEP):
            if x % 4 == 1:
                put(g, x, line_y(x), 'r')
            if x % 6 == 3:
                put(g, x, line_y(x) + 1, 'c')
        put(g, 13, line_y(13), 'n')
        for (x, y) in ((12, 9), (13, 8), (14, 8), (24, 15), (25, 14)):
            put(g, x, y, 'z' if (x + y) % 2 else 'y')
    return g


def frames():
    return ([smoulder_frame(t) for t in range(2)] + [ignite_frame(t) for t in range(2)]
            + [burn_frame(t) for t in range(4)] + [die_frame(t) for t in range(3)])
