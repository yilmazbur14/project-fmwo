"""burak_muzzle.png: the flintlock's muzzle flash and powder smoke. 15 frames of 48x48 at 0.04 s, one strip:
  frames 0-4     firing right (0 degrees)
  frames 5-9     firing down-right (45 degrees)
  frames 10-14   firing down (90 degrees: the approved shot frame fires down)
Pick the direction that matches the pistol in the body frame; flip_h for a leftward shot. NEVER flip_v:
the smoke always rises.
THE PIVOT IS THE FRAME CENTRE (24, 24): the muzzle. No offset under flip_h.
  f0  the flash: a white-hot star at the muzzle, a jagged cone of gold flame forward, two short side jets
  f1  the flame shrinking, the first puff of smoke
  f2  the smoke billowing forward, a last spark
  f3  the smoke drifting on and rising, greying
  f4  wisps
Burak's colours: the approved shot's baked flash (#FFF3B0 #F5D94E #E0AB35 #B07D22) and smoke (#FFFCF4
#E8E1D3 #C3B9A9, greying to #A6AFC1). No keyline, opaque.
"""
import math
import random

import bfx_pal as pal

W = H = 48
C = 24.0
FRAME_SIZE = (48, 48)
NOTE = '15 frames: 0/45/90 deg x 5 at 0.04 s; pivot = centre (24,24), the muzzle; flip_h only'
DIRS = (0.0, 45.0, 90.0)
SMOKE = ['W', 'w', 'c', 's', 'i']


def put(g, x, y, k):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = k


def flame(g, theta, length, width, seed):
    """A jagged cone of flame forward from the muzzle, hottest at its root."""
    t = math.radians(theta)
    d = (math.cos(t), math.sin(t))
    n = (-d[1], d[0])
    rnd = random.Random(seed)
    jag = [rnd.uniform(0.7, 1.15) for _ in range(9)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - C, y + 0.5 - C
            u = px * d[0] + py * d[1]
            v = px * n[0] + py * n[1]
            if u < -1.5 or u > length:
                continue
            a = math.atan2(v, max(0.3, u))
            j = jag[int((a + 1.0) * 4) % 9]
            half = width * (1.0 - (max(0.0, u) / length) ** 1.4) * j + 1.2 * max(0.0, 1.0 - max(0.0, u) / 3.0)
            if abs(v) > half:
                continue
            q = (u / length) + abs(v) / max(1.0, half) * 0.35
            k = 'W' if q < 0.18 else ('Q' if q < 0.4 else ('Y' if q < 0.62 else ('G' if q < 0.85 else 'g')))
            g[y][x] = k
    # two short side jets
    for side in (1, -1):
        for s in range(1, int(length * 0.35)):
            x = int(math.floor(C + d[0] * 1.5 + n[0] * side * s))
            y = int(math.floor(C + d[1] * 1.5 + n[1] * side * s))
            put(g, x, y, 'Y' if s < 3 else 'G')


def puff(g, cx, cy, r, dark):
    for y in range(max(0, int(cy - r) - 1), min(H, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(W, int(cx + r) + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            hl = math.hypot(dx + 0.3 * r, dy + 0.35 * r)
            i = dark - 1 if hl < 0.5 * r else (dark + 1 if (d > r - 1.2 and dx + dy > 0) else dark)
            if g[y][x] == '.':
                g[y][x] = SMOKE[max(0, min(len(SMOKE) - 1, i))]


# Smoke per frame: (forward distance, rise, radius, darkness) for each puff.
PUFFS = {
    1: [(4, 0, 4.0, 1)],
    2: [(8, -1, 5.6, 1), (3, -3, 4.2, 1), (12, 1, 3.8, 2)],
    3: [(10, -5, 6.0, 2), (4, -7, 4.6, 2), (14, -3, 4.0, 2)],
    4: [(11, -10, 4.8, 3), (5, -12, 3.6, 3), (15, -8, 3.0, 3)],
}


def frame(theta, f):
    g = pal.blank(W, H)
    t = math.radians(theta)
    d = (math.cos(t), math.sin(t))
    for (fwd, rise, r, dark) in PUFFS.get(f, []):
        puff(g, C + d[0] * fwd, C + d[1] * fwd + rise, r, dark)
    if f == 0:
        flame(g, theta, 15.0, 5.0, 1)
        for (x, y) in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)):
            put(g, int(C) + x, int(C) + y, 'W')
    elif f == 1:
        flame(g, theta, 9.0, 3.2, 2)
    elif f == 2:
        put(g, int(C + d[0] * 2), int(C + d[1] * 2), 'Y')
    return pal.rows(g)


def frames():
    return [frame(t, f) for t in DIRS for f in range(5)]
