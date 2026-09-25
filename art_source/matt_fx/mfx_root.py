"""matt_root.png: the sound shackle round the player's feet while Matt holds them in the lane. 5 frames of
40x20, one strip:
  frames 0-2   the clamp, 0.05 s each: a wide ring on the floor snaps in tight round the feet, two bars
               locking at its sides on the last frame (release plays these backwards)
  frames 3-4   the hold, looping at 0.15 s: the tight ring pulses, echoes rippling out from it
THE PIVOT IS (20, 12): on the player's feet (the ring's centre on the floor). A floor effect: FloorLayer or
just under the player. The approved roar-ring style (#F2F3FF core, #C4C9FA flanks, #4F4D96 edge) as a flat
ellipse, its front arc a texel thicker than its back so it reads as lying on the floor; no keyline.
"""
import math

import mfx_pal as pal

W, H = 40, 20
CX, CY = 20.0, 12.0
FRAME_SIZE = (40, 20)
NOTE = '5 frames: f0-2 clamp at 0.05 s, f3-4 loop at 0.15 s; pivot (20,12) on the feet'
SQUASH = 0.36
RANK = {'.': 0, 'm': 1, 'r': 2, 's': 3}


def put(g, x, y, k):
    if 0 <= x < W and 0 <= y < H and RANK[k] >= RANK[g[y][x]]:
        g[y][x] = k


def curve(rx, n=480):
    ry = rx * SQUASH
    return [(CX + rx * math.cos(2 * math.pi * i / n), CY + ry * math.sin(2 * math.pi * i / n), i / n) for i in range(n)]


def floor_ring(g, rx, core, flank, edge, ck='s', dash=None):
    """A flat ellipse ring on the floor, banded by the true distance to its curve, so it stays one even
    screen thickness all the way round; the front (lower) arc is a little thicker."""
    pts = curve(rx)
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            best, bt = 1e9, 0.0
            for (cx, cy, t) in pts:
                d = (px - cx) ** 2 + (py - cy) ** 2
                if d < best:
                    best, bt = d, t
            d = math.sqrt(best)
            front = 1.0 + 0.3 * max(0.0, math.sin(2 * math.pi * bt))
            if dash and (bt * dash[0]) % 1.0 > dash[1]:
                continue
            dd = d / front
            k = ck if dd <= core else ('r' if dd <= flank else ('m' if dd <= edge else None))
            if k:
                put(g, x, y, k)


def bars(g, rx):
    """The shackle's clasps: a short upright bar rising from each end of the ring, edged on its outside."""
    for sx in (-1, 1):
        x = int(math.floor(CX + sx * rx - (0.5 if sx > 0 else -0.5)))
        for y in range(int(CY) - 4, int(CY)):
            put(g, x, y, 's' if y >= CY - 3 else 'r')
            put(g, x + sx, y, 'm')
        put(g, x, int(CY) - 5, 'm')


def frame(f):
    g = pal.blank(W, H)
    if f == 0:
        floor_ring(g, 17.5, 0.6, 0.95, 1.65)
    elif f == 1:
        floor_ring(g, 13.0, 0.6, 0.95, 1.65)
        floor_ring(g, 17.5, 0.0, 0.0, 0.7, ck='m', dash=(14, 0.55))
    elif f == 2:
        floor_ring(g, 9.5, 0.7, 1.05, 1.8)
        bars(g, 9.5)
    elif f == 3:
        floor_ring(g, 9.5, 0.7, 1.05, 1.8)
        floor_ring(g, 13.5, 0.4, 0.4, 1.0, ck='r', dash=(16, 0.6))
        bars(g, 9.5)
    elif f == 4:
        floor_ring(g, 9.5, 0.55, 0.9, 1.6)
        floor_ring(g, 16.5, 0.0, 0.0, 0.7, ck='m', dash=(18, 0.5))
        bars(g, 9.5)
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(5)]
