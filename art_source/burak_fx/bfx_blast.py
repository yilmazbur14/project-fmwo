"""burak_blast.png: a powder keg going up. 8 frames of 160x128 at 0.05 s, one strip.
THE PIVOT IS (80, 104): the barrel's floor point (its burak_barrel pivot). As a centred Sprite2D, offset
(0, -40). Never flipped. Pair it with burak_blast_screen for the whole-arena flash.

  f0  DETONATION: a white-hot ball over the whole keg (it covers the 48x56 keg, so hide the keg on this
      frame), long rays, a flash across the floor
  f1  the fireball swells: white core, Burak's gold, crimson rim; the floor shockwave ring leaves
  f2  the fireball at full size, black-powder smoke boiling out at its edge, splinters flying
  f3  the fire sinking into a rising cloud of black-powder smoke, the ring far out and thinning
  f4  a smoke column with fire still inside it, embers
  f5  the fire out, the smoke lightening
  f6  the smoke breaking into puffs
  f7  the last wisps
His colours (burak_boss.png): the gold ramp and smoke whites for the fire's heart, the coat's crimsons for
its rim, the iron greys for the black-powder smoke, and one derived step, #DC7742 (the exact midpoint of
his gold #E0AB35 and crimson #D8434F), where the fire turns from gold to red. Hard edges, no dither, opaque.
"""
import math
import random

import bfx_pal as pal

W, H = 160, 128
PX, PY = 80.0, 104.0
FRAME_SIZE = (160, 128)
NOTE = '8 frames at 0.05 s; pivot (80,104) on the keg\'s floor point, offset (0,-40)'
LOCAL = {'r': (0xDC, 0x77, 0x42, 255)}              # derived: midpoint of #E0AB35 and #D8434F

FIRE = ['W', 'Q', 'Y', 'G', 'r', '2', '3', '5']      # hot to cool
SMOKE = ['w', 'c', 's', 'i', 'I', 'j', 'k', 'K']     # light to dark


def lump(theta, seed, amt):
    """An irregular edge: a few random frequencies with random weights, plus flame tongues licking out at
    a handful of random angles."""
    rnd = random.Random(seed)
    s = 0.0
    for _ in range(5):
        k = rnd.choice((3, 4, 6, 7, 9, 11))
        s += rnd.uniform(0.15, 0.45) * math.sin(k * theta + rnd.uniform(0, 6.28))
    tongues = 0.0
    for _ in range(6):
        c = rnd.uniform(-math.pi, math.pi)
        w = rnd.uniform(0.12, 0.22)
        d = abs((theta - c + math.pi) % (2 * math.pi) - math.pi)
        if d < w:
            tongues = max(tongues, rnd.uniform(0.18, 0.32) * (1.0 - d / w))
    return 1.0 + amt * s + tongues


def fireball(g, cx, cy, R, seed, core_cut, squash=0.92, lump_floor=0.0):
    """A lumpy ball of fire: bands by normalized radius, hottest at the heart. lump_floor stops the edge's
    dips from biting in past that fraction of R (f0 uses it to cover the whole keg)."""
    for y in range(max(0, int(cy - R * 1.4)), min(H, int(cy + R * 1.4) + 1)):
        for x in range(max(0, int(cx - R * 1.4)), min(W, int(cx + R * 1.4) + 1)):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) / squash
            th = math.atan2(dy, dx)
            edge = R * max(lump_floor, lump(th, seed, 0.16))
            d = math.hypot(dx, dy)
            if d > edge:
                continue
            q = d / edge
            # the heat sits a little high and left: the light comes off the top of the ball
            q = q + 0.12 * (dy / max(1.0, R)) + 0.05 * (dx / max(1.0, R))
            i = int(max(0.0, min(0.999, (q - core_cut) / (1.0 - core_cut) if q > core_cut else 0.0)) * (len(FIRE) - 1) + 0.5)
            if q <= core_cut:
                i = 0
            g[y][x] = FIRE[max(0, min(len(FIRE) - 1, i))]


def puff(g, cx, cy, r, dark, lit_bias=0.55):
    """A round smoke puff lit from the top left: dark is the index of its body shade in SMOKE."""
    for y in range(max(0, int(cy - r) - 1), min(H, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(W, int(cx + r) + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            # a round highlight toward the top left, a shaded rim toward the bottom right
            hl = math.hypot(dx + 0.32 * r, dy + 0.36 * r)
            if hl < 0.42 * r:
                i = dark - 2
            elif hl < 0.72 * r:
                i = dark - 1
            elif d > r - 1.6 and (dx + dy) > 0:
                i = dark + 1
            else:
                i = dark
            g[y][x] = SMOKE[max(0, min(len(SMOKE) - 1, i))]


def cloud(g, cx, cy, R, n, seed, dark, spread=1.0):
    """A billow: a ring of puffs round a filled heart of puffs, drawn back to front."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.3, 0.3)
        rr = R * rnd.uniform(0.35, 0.8) * spread
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.8, R * rnd.uniform(0.32, 0.5)))
    for i in range(max(2, n // 3)):
        pts.append((cx + rnd.uniform(-0.25, 0.25) * R, cy + rnd.uniform(-0.2, 0.2) * R, R * rnd.uniform(0.4, 0.55)))
    # back to front: the lower puffs overlap the upper ones
    for (x, y, r) in sorted(pts, key=lambda p: p[1]):
        puff(g, x, y, r, dark)


def ring(g, rx, ry, core, keys, dash=None, seed=0):
    """The shockwave across the floor round the pivot: an ellipse band, keys inner to outer."""
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - PX, (y + 0.5 - PY) * rx / ry
            d = math.hypot(dx, dy) - rx
            if abs(d) > core:
                continue
            if dash:
                a = (math.atan2(dy, dx) / (2 * math.pi)) % 1.0
                if (a * dash[0]) % 1.0 > dash[1]:
                    continue
            if g[y][x] != '.':
                continue
            i = int((d + core) / (2 * core) * len(keys))
            g[y][x] = keys[max(0, min(len(keys) - 1, i))]


def rays(g, cx, cy, n, r0, r1, seed, keys='QY'):
    rnd = random.Random(seed)
    for i in range(n):
        a = 2 * math.pi * i / n + rnd.uniform(-0.12, 0.12)
        length = r1 * rnd.uniform(0.7, 1.0)
        s = r0
        while s < length:
            x = int(cx + math.cos(a) * s)
            y = int(cy + math.sin(a) * s * 0.85)
            if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
                g[y][x] = keys[0] if s < length * 0.6 else keys[1]
            s += 0.5


def debris(g, t, seed, n=14):
    """Splinters and hoop scraps flung out and falling."""
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(rnd.uniform(-170, -10))
        v = rnd.uniform(110, 210)
        x = PX + math.cos(a) * v * t
        y = PY - 12 + math.sin(a) * v * t + 0.5 * 380 * t * t
        k = rnd.choice('ODnki')
        for (dx, dy) in ((0, 0), (1, 0)) if i % 3 else ((0, 0), (0, 1)):
            xx, yy = int(x) + dx, int(y) + dy
            if 0 <= xx < W and 0 <= yy < H and g[yy][xx] not in 'WQY':     # never dirt on the white heart
                g[yy][xx] = k


def embers(g, t, seed, n=12, keys='YG'):
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(rnd.uniform(-160, -20))
        v = rnd.uniform(60, 150)
        x = PX + math.cos(a) * v * t
        y = PY - 30 + math.sin(a) * v * t + 0.5 * 120 * t * t
        xx, yy = int(x), int(y)
        if 0 <= xx < W and 0 <= yy < H:
            g[yy][xx] = keys[i % len(keys)]


def ground_flash(g, rx, ry, keys):
    for y in range(H):
        for x in range(W):
            d = ((x + 0.5 - PX) / rx) ** 2 + ((y + 0.5 - PY) / ry) ** 2
            if d <= 1.0 and g[y][x] == '.':
                g[y][x] = keys[0] if d < 0.3 else (keys[1] if d < 0.7 else keys[2])


def frame(f):
    g = pal.blank(W, H)
    cy = PY - 18
    if f == 0:
        # the detonation is a white-hot ball over the whole 48x56 keg (centred on its body, a little
        # upright like the keg, its dips floored), so the keg can be hidden on this frame
        ground_flash(g, 50, 10, 'QYG')
        fireball(g, PX, PY - 26, 25, 1, 0.6, squash=1.1, lump_floor=0.88)
        rays(g, PX, PY - 26, 16, 25, 64, 2)
    elif f == 1:
        ring(g, 52, 13, 2.2, 'GYQY')
        cloud(g, PX, cy - 6, 36, 10, 3, 5)
        fireball(g, PX, cy - 4, 34, 4, 0.34)
        rays(g, PX, cy - 4, 12, 33, 54, 5, keys='YG')
    elif f == 2:
        ring(g, 68, 17, 1.8, 'GYG')
        cloud(g, PX, cy - 10, 50, 13, 6, 5)
        fireball(g, PX, cy - 9, 44, 7, 0.22)
        debris(g, 0.07, 8, n=20)
    elif f == 3:
        ring(g, 78, 21, 1.3, 'csc', dash=(34, 0.8))
        cloud(g, PX, cy - 16, 52, 14, 9, 5)
        cloud(g, PX, cy - 40, 30, 8, 21, 5)
        fireball(g, PX, cy - 14, 32, 10, 0.1)
        debris(g, 0.12, 8, n=20)
        embers(g, 0.1, 11)
    elif f == 4:
        cloud(g, PX, cy - 22, 50, 13, 12, 5)
        cloud(g, PX, cy - 48, 32, 8, 13, 5)
        fireball(g, PX, cy - 20, 18, 14, 0.0)
        debris(g, 0.17, 8, n=20)
        embers(g, 0.16, 11, n=16)
    elif f == 5:
        cloud(g, PX, cy - 28, 48, 13, 15, 4)
        cloud(g, PX, cy - 54, 30, 8, 16, 4)
        embers(g, 0.22, 17, n=14, keys='GY')
    elif f == 6:
        cloud(g, PX, cy - 34, 44, 12, 18, 3, spread=1.15)
        cloud(g, PX, cy - 60, 26, 7, 22, 3)
        embers(g, 0.28, 19, n=8, keys='Gg')
    elif f == 7:
        cloud(g, PX, cy - 42, 36, 10, 20, 2, spread=1.35)
    return pal.Frame(pal.rows(g), LOCAL)


def frames():
    return [frame(f) for f in range(8)]
