"""bixby_fireball_impact.png: a fireball hitting the floor. 5 frames of 48x40 texels, 0.06 s each (0.3 s).

GROUND CONTACT: texel (24, 28), the point between texels (23..24, 27..28): the landing spot. For a centred
Sprite2D that is an offset of (0, -8) texels. The ring the fire spreads in reaches the full 44x22 hit oval
around it on frame 2 (x 2..45, y 17..38).

  0  the ball bursts on the floor: a white-hot splash and rays
  1  a dome of fire, a ring of flame running out along the floor
  2  the dome breaks into rising tongues; the ring at the hit oval's size
  3  the fire thins and reddens over the scorch it has left
  4  smoke lifting off the scorch, a last few flames

Frames 3 and 4 lie on bixby_fire_scorch.png's own frame-0 pixels (its 34x14 oval, re-centred on the
contact), so the switch to the scorch sprite afterwards doesn't pop.
"""
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pal  # noqa: E402
from firelib import rings, put, close_holes, flame_set, paint_flame, stamp, FLAME_S, FLAME_M, FLAME_L  # noqa: E402

W, H = 48, 40
CX, CY = 24.0, 28.0
SCORCH = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/bixby_fire_scorch.png'
# bixby_fire_scorch.png's own colours, carried as they are so the hand-off matches texel for texel
SCORCH_KEYS = {(0x12, 0x10, 0x16): 'a', (0x26, 0x22, 0x2C): 'b', (0x3A, 0x35, 0x42): 'c', (0x5C, 0x58, 0x68): 'd',
               (0x6E, 0x1E, 0x22): '1', (0xDF, 0x71, 0x26): '2', (0xF5, 0x8A, 0x38): '3'}
EXTRA = {'1': pal.hx('6E1E22'), '2': pal.hx('DF7126'), '3': pal.hx('F58A38')}


def blank():
    return [['.'] * W for _ in range(H)]


def ellipse(cx, cy, rx, ry):
    return {(x, y) for y in range(H) for x in range(W)
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0}


def scorch_layer(g):
    """bixby_fire_scorch.png frame 0, its oval centre (20, 31) moved onto the contact (24, 28)."""
    im = Image.open(SCORCH).convert('RGBA').crop((0, 0, 40, 40))
    for y in range(40):
        for x in range(40):
            p = im.getpixel((x, y))
            if p[3]:
                put(g, x + 4, y - 3, SCORCH_KEYS[p[:3]])


def paint_rings(g, shape, keys):
    for (x, y), d in rings(shape).items():
        put(g, x, y, keys[min(d, len(keys) - 1)])


def ring_flames(g, rx, ry, n, sizes, cool=0, phase=0.0, half=None):
    """Hand-drawn flames standing on an oval around the contact: the fire running out along the floor.
    half: 'back' (upper arc only) or 'front' (lower arc only), so a dome can sit between them."""
    for i in range(n):
        a = 2 * math.pi * (i + phase) / n
        if half == 'back' and math.sin(a) > 0.05:
            continue
        if half == 'front' and math.sin(a) <= 0.05:
            continue
        x = int(round(CX - 0.5 + rx * math.cos(a)))
        y = int(round(CY - 0.5 + ry * math.sin(a)))
        stamp(g, sizes[i % len(sizes)], x, y, cool=cool, mirror=bool(i % 2))


def rays(g, n, r0, r1, keys, seed):
    """Splash rays, only up and out along the floor: none go down into it."""
    rnd = random.Random(seed)
    for i in range(n):
        a = math.pi + math.pi * (i + 0.5) / n          # from pointing left, over the top, to pointing right
        L = r1 * (0.7 + 0.5 * rnd.random())
        for j in range(int(L - r0)):
            r = r0 + j
            x = int(round(CX - 0.5 + r * math.cos(a)))
            y = int(round(CY - 2.5 + r * math.sin(a) * 0.75))
            put(g, x, y, keys[min(len(keys) - 1, j * len(keys) // max(1, int(L - r0)))])


def sparks(g, pts, keys='PY'):
    for i, (x, y) in enumerate(pts):
        if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
            put(g, x, y, keys[i % len(keys)])


def puff(g, x, y, r):
    body = {(px, py) for py in range(y - r - 1, y + r + 2) for px in range(x - r - 1, x + r + 2)
            if (px - x) ** 2 + (py - y) ** 2 <= r * r + r * 0.6}
    for (px, py), d in rings(body).items():
        lit = (px - x) + (py - y) < -r * 0.6
        put(g, px, py, 'z' if d == 0 else ('x' if lit else 'y'))


def frame0():
    g = blank()
    rays(g, 9, 5, 16, ['Y', 'P', 'p', 'N'], seed=3)
    splash = ellipse(CX, CY - 1.0, 11.0, 4.0) | ellipse(CX, CY - 3.5, 6.5, 5.0)
    paint_rings(g, close_holes(splash), ['r', 'N', 'p', 'P', 'Y', 'W', 'W'])
    sparks(g, [(10, 12), (37, 14), (16, 6), (31, 7), (5, 24), (43, 23)])
    return g


def frame1():
    g = blank()
    ring_flames(g, 17.0, 8.0, 12, [FLAME_M, FLAME_S], half='back')
    dome = ellipse(CX, CY - 5.0, 12.5, 10.0)
    dome = {(x, y) for (x, y) in dome if y <= CY + 1} | ellipse(CX, CY - 0.5, 12.5, 4.0)
    for dx, h in ((-6, 6), (0, 9), (6, 6)):
        dome |= flame_set(int(CX + dx), int(CY - 10), 8, h, [(0, 0, h, 5, 0.0, 0.5 if dx > 0 else -0.5)])
    paint_rings(g, close_holes(dome), ['r', 'N', 'p', 'P', 'Y', 'Y', 'W'])
    ring_flames(g, 17.0, 8.0, 12, [FLAME_M, FLAME_S], half='front')
    sparks(g, [(6, 10), (41, 8), (12, 3), (35, 2), (3, 18), (45, 17), (20, 1)])
    return g


def frame2():
    g = blank()
    ring_flames(g, 20.0, 9.5, 14, [FLAME_L, FLAME_M], phase=0.5, half='back')
    body = ellipse(CX, CY - 3.0, 10.5, 6.0)
    for dx, h, w, lean in ((-7, 11, 9, -1.4), (0, 16, 10, 0.4), (7, 12, 9, 1.4)):
        body |= flame_set(int(CX + dx), int(CY - 2), w, h, [(0, 0, h, w - 1, lean, 0.5)])
    body = {(x, y) for (x, y) in body if 0 <= y < H}
    paint_flame(g, close_holes(body), int(CY), 24, bands=('r', 'N', 'p', 'P', 'Y'), white='W', white_depth=4)
    ring_flames(g, 20.0, 9.5, 14, [FLAME_L, FLAME_M], phase=0.5, half='front')
    sparks(g, [(4, 6), (44, 5), (13, 1), (36, 0), (1, 14), (46, 12), (24, 0), (19, 3)])
    return g


def frame3():
    g = blank()
    scorch_layer(g)
    ring_flames(g, 17.0, 6.5, 9, [FLAME_M, FLAME_S], cool=1, phase=0.25)
    body = set()
    for dx, h, w, lean in ((-6, 8, 8, -1.0), (0, 12, 9, -0.4), (6, 9, 8, 0.9)):
        body |= flame_set(int(CX + dx), int(CY), w, h, [(0, 0, h, w - 1, lean, 0.6)])
    paint_flame(g, close_holes(body), int(CY), 16, bands=('r', 'n', 'N', 'p', 'P'), white=None)
    puff(g, 14, 9, 2)
    puff(g, 33, 6, 2)
    sparks(g, [(8, 4), (40, 3), (22, 1), (3, 12), (45, 10)], keys='pN')
    return g


def frame4():
    g = blank()
    scorch_layer(g)
    for i, (dx, t) in enumerate(((-7, FLAME_S), (1, FLAME_M), (8, FLAME_S))):
        stamp(g, t, int(CX + dx), int(CY) + 1, cool=1, mirror=bool(i % 2))
    puff(g, 14, 12, 3)
    puff(g, 31, 8, 3)
    puff(g, 22, 3, 2)
    sparks(g, [(7, 10), (41, 12), (37, 1)], keys='Nn')
    return g


def frames():
    return [frame0(), frame1(), frame2(), frame3(), frame4()]


def image(frames_):
    """The sheet as an image; the scorch's three old ember colours are drawn with their own values."""
    saved = dict(pal.PAL)
    pal.PAL.update(EXTRA)
    try:
        return pal.sheet([frames_])
    finally:
        pal.PAL.clear()
        pal.PAL.update(saved)
