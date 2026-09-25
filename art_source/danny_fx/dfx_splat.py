"""danny_worm_splat.png: the glob landing and spreading into a puddle. 5 frames of 100x52 at 0.05 s, one strip,
the same frame and pivot as danny_worm_puddle, so the puddle's loop takes over from its last frame.
THE PIVOT IS THE FRAME CENTRE (50, 26): where the glob lands, the puddle's centre on the floor. Never flipped.
  f0  the glob bursts flat on the mat: a squashed disc of slime with a crown of drops flung out round it
  f1  the splash spreading into a ragged star of slime, drops flying out, worms thrown up
  f2  the slime running out to nearly the puddle's size, drops landing round it, the worms landing in it
  f3  settling to the puddle's edge (the trigger ellipse)
  f4  the puddle's first frame (danny_worm_puddle f0), pixel for pixel: switch to the puddle loop after it
Drawn for the puddle at rx 43, ry 17 texels (the user's playtest, 2026-09-24, about 1.6x the first one).
"""
import math
import random

import dfx_pal as pal
import dfx_worms as wm
import dfx_puddle as pud

W, H = pud.W, pud.H
CX, CY = pud.CX, pud.CY
FRAME_SIZE = (W, H)
NOTE = '5 frames of 100x52 at 0.05 s; pivot = centre (50,26) on the floor; f4 = danny_worm_puddle f0'
# the first puddle's stages were drawn at rx 27, ry 10.5; the splash grows with the puddle
KX, KY = pud.RX / 27.0, pud.RY / 10.5

# per frame: (body rx, ry, spike length as a fraction, drop ring radius as a fraction, drops shown, worms)
STAGES = [(10.0 * KX, 4.2 * KY, 0.9, 1.5, 14, 'up'), (19.0 * KX, 7.2 * KY, 0.55, 1.45, 14, 'air'),
          (25.0 * KX, 9.7 * KY, 0.2, 1.18, 10, 'in'), (pud.RX, pud.RY, 0.0, 1.06, 0, 'in')]
N_DROPS = 14
# worms thrown up out of the burst (f0) and flying out (f1): (x0, y0, x1, y1 relative to the centre, phase)
THROWN_UP = [(-6, -8, -1, -11, 0.0), (1, -12, 6, -9, 1.3), (-10, -5, -7, -8, 2.1), (7, -6, 11, -8, 3.0),
             (-15, -9, -11, -12, 4.2), (13, -11, 17, -9, 5.1)]
THROWN_OUT = [(-18, -17, -12, -19, 0.4), (6, -21, 12, -19, 1.6), (-29, -11, -25, -14, 2.6), (22, -12, 27, -14, 3.3),
              (-4, -24, 1, -22, 4.4), (32, -6, 37, -8, 5.5)]


def splash_mask(rx, ry, spike, seed):
    """A splat: an ellipse with thin spikes of slime running out from it."""
    rnd = random.Random(seed)
    spikes = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.6, 1.0), rnd.uniform(0.10, 0.18)) for _ in range(12)]
    m = set()
    for y in range(H):
        for x in range(W):
            dx, dy = (x + 0.5 - CX) / rx, (y + 0.5 - CY) / ry
            r = math.hypot(dx, dy)
            th = math.atan2(dy, dx)
            e = 1.0 + 0.06 * math.sin(5 * th + seed)
            for (a, s, w) in spikes:
                dd = abs((th - a + math.pi) % (2 * math.pi) - math.pi)
                if dd < w:
                    e = max(e, 1.0 + spike * s * (1.0 - dd / w))
            if r <= e:
                m.add((x, y))
    return m


def ellipse_mask(rx, ry):
    return {(x, y) for y in range(H) for x in range(W) if ((x + 0.5 - CX) / rx) ** 2 + ((y + 0.5 - CY) / ry) ** 2 <= 1.0}


def frame(f):
    if f == 4:
        return pud.frame(0)
    g = pal.blank(W, H)
    rx, ry, spike, ring, ndrops, worms = STAGES[f]
    if f == 3:
        # settled: the puddle's own body and drops, so f4 takes over cleanly
        mask = pud.body_mask() | pud.drops_mask()
    elif f == 2:
        # the slime running out, nearly the puddle's size, its last spikes still reaching
        mask = ellipse_mask(rx, ry) | splash_mask(rx, ry, spike, seed=5)
    else:
        mask = splash_mask(rx, ry, spike, seed=5)
    rnd = random.Random(9)
    for i in range(N_DROPS):
        a = 2 * math.pi * i / N_DROPS + rnd.uniform(-0.15, 0.15)
        dr = ring * rnd.uniform(0.95, 1.1)
        if i >= ndrops:
            continue
        ox, oy = CX + rx * dr * math.cos(a), CY + ry * dr * math.sin(a) - (4.0 if f == 0 else 0.0) * max(0.0, -math.sin(a))
        size = 2.0 if f < 2 else 1.6
        for y in range(int(oy) - 3, int(oy) + 4):
            for x in range(int(ox) - 3, int(ox) + 4):
                if ((x + 0.5 - ox) / size) ** 2 + ((y + 0.5 - oy) / (size * 0.8)) ** 2 <= 1.0 and 0 <= x < W and 0 <= y < H:
                    mask.add((x, y))
    wm.stain(g, mask)
    wm.gloss(g, [(int(CX - rx * 0.55), int(CY - ry * 0.55)), (int(CX - rx * 0.5), int(CY - ry * 0.62)),
                 (int(CX - rx * 0.44), int(CY - ry * 0.62))])
    body = {(x, y) for (x, y) in mask if math.hypot((x + 0.5 - CX) / rx, (y + 0.5 - CY) / ry) < 0.86}
    if worms in ('up', 'air'):
        # the worms thrown up out of the burst, short and curled, above it; then flying out
        for (x0, y0, x1, y1, p) in (THROWN_UP if worms == 'up' else THROWN_OUT):
            wm.worm(g, wm.wiggle(CX + x0, CY + y0, CX + x1, CY + y1, 1.0 if worms == 'up' else 1.2, 1.0, p, n=16),
                    width=2.3, saddle=-1, glint_every=0)
    else:
        scale = rx / pud.RX
        for (x0, y0, x1, y1, amp, waves, p, w, sad) in pud.WORMS:
            pts = wm.wiggle(CX + x0 * scale, CY + y0 * scale, CX + x1 * scale, CY + y1 * scale, amp, waves, p - 1.0)
            wm.worm(g, pts, width=w, clip=body, saddle=sad)
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(5)]
