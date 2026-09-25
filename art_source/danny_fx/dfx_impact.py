"""danny_slam_impact.png: Danny's butt slam hitting the canvas. 6 frames of 192x72 at 0.05 s, one strip.
THE PIVOT IS (96, 52): the point his rear lands on (the same point as danny_slam_target's centre). Never flipped.
  f0  IMPACT: a white-hot flash flattened on the floor under him, the canvas splitting in a star of cracks
  f1  a ring of dust bursting out low along the floor, chips of mat thrown up
  f2  the dust ring rolling out and rising, the chips at the top of their flight
  f3  the dust thinning and greying, the chips falling
  f4  the last dust drifting, the cracks left
  f5  the cracks alone (hold it while the quake rings roll out, then fade it)
Dust in his cool whites and grey-blue (W Q P g N), the cracks in the mat's own greens (K k n m), the flash
white with his pale blues. No keyline; the dust thins out in stepped alpha (168 on f3, 96 on f4). The dust
ring reaches about rx 88 texels (264 px) either side of the pivot.
"""
import math
import random

import dfx_pal as pal
import dfx_floor as fl

W, H = 192, 72
PX, PY = 96.0, 52.0
FRAME_SIZE = (W, H)
NOTE = '6 frames of 192x72 at 0.05 s; pivot (96,52) = where his rear lands; f5 = the cracks alone (hold, fade)'
FLAT = 0.24                    # how much the floor flattens a ring's height against its width here

CRACKS = [(-18, 30, 0.8), (8, 34, 0.9), (32, 38, 1.0), (60, 33, 0.9), (95, 30, 0.8), (128, 34, 0.9), (152, 38, 1.0),
          (180, 33, 0.9), (205, 30, 0.8), (240, 36, 1.0), (270, 30, 0.8), (305, 34, 0.9), (335, 38, 1.0)]


def cracks(g, grow):
    """A star of cracks from the impact point, `grow` of their full length: two texels wide near the centre,
    a few forking once."""
    rnd = random.Random(21)
    for n, (ang, L, w) in enumerate(CRACKS):
        a = math.radians(ang)
        ln = L * grow * w
        x1 = PX + math.cos(a) * ln
        y1 = PY + math.sin(a) * ln * 0.3
        pts = fl.zigzag(PX + math.cos(a) * 3, PY + math.sin(a) * 1, x1, y1, seed=n, jag=1.3)
        inner = pts[:max(2, len(pts) * 2 // 5)]
        fl.crack(g, pts)
        fl.crack(g, inner, wide=True)
        if grow > 0.6 and n % 4 == 0:
            m = pts[len(pts) // 2]
            b = a + rnd.choice((-0.5, 0.5))
            fl.crack(g, fl.zigzag(m[0], m[1], m[0] + math.cos(b) * ln * 0.3, m[1] + math.sin(b) * ln * 0.3 * 0.3,
                                  seed=n + 40, jag=0.9), lip=False)


def dust_ring(g, rx, rise, shade, rmin, rmax, count=22, seed=3):
    """A ring of flattened dust billows on the floor round the impact, rising `rise` texels, `shade` 0 fresh
    .. 2 grey; the front of the ring's billows are the biggest. Back to front, so the front overlaps."""
    rnd = random.Random(seed)
    puffs = []
    for i in range(count):
        a = 2 * math.pi * i / count + rnd.uniform(-0.1, 0.1)
        front = 0.5 + 0.5 * math.sin(a)                      # 1 at the front of the ring, 0 at its back
        r = rnd.uniform(rmin, rmax) * (0.8 + 0.35 * front)
        x = PX + math.cos(a) * rx * rnd.uniform(0.94, 1.04)
        y = PY + math.sin(a) * rx * FLAT - rise * rnd.uniform(0.5, 1.0) - r * 0.3
        puffs.append((y, x, r))
    for (y, x, r) in sorted(puffs):
        fl.puff(g, x, y, r, shade, squash=0.72)


def flash(g, rx, ry):
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - PX) / rx, (y + 0.5 - PY) / ry)
            if d <= 1.0:
                g[y][x] = 'W' if d < 0.55 else ('Q' if d < 0.8 else 'P')


def chips(g, t):
    rnd = random.Random(8)
    for i in range(14):
        a = math.radians(rnd.uniform(-165, -15))
        v = rnd.uniform(90, 170)
        x = PX + math.cos(a) * v * t * 1.7
        y = min(PY + 3, PY - 6 + math.sin(a) * v * t + 0.5 * 700 * t * t)
        fl.chip(g, x, y, big=True)


def frame(f):
    g = pal.blank(W, H)
    local = {}
    if f == 0:
        cracks(g, 0.55)
        flash(g, 34, 9)
        for (dx, r) in ((-22, 7), (20, 7), (-8, 8), (9, 6)):
            fl.puff(g, PX + dx, PY - 3, r, 0, squash=0.72)
    elif f == 1:
        cracks(g, 0.9)
        chips(g, 0.05)
        dust_ring(g, 40, 5, 0, 6.0, 8.5)
        fl.puff(g, PX, PY - 7, 11, 0, squash=0.8)
    elif f == 2:
        cracks(g, 1.0)
        chips(g, 0.10)
        dust_ring(g, 60, 9, 0, 7.0, 10.0)
        fl.puff(g, PX - 6, PY - 14, 10, 1, squash=0.8)
        fl.puff(g, PX + 7, PY - 12, 9, 1, squash=0.8)
    elif f == 3:
        cracks(g, 1.0)
        chips(g, 0.15)
        dust_ring(g, 70, 12, 1, 7.5, 11.0)
        fl.puff(g, PX, PY - 20, 11, 2, squash=0.8)
        local = fl.dust_alpha(g, 168)
    elif f == 4:
        cracks(g, 1.0)
        chips(g, 0.20)
        dust_ring(g, 76, 14, 2, 8.0, 11.0, count=16)
        local = fl.dust_alpha(g, 96)
    else:
        cracks(g, 1.0)
    return pal.Frame(pal.rows(g), local)


def frames():
    return [frame(f) for f in range(6)]
