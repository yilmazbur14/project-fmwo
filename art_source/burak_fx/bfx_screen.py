"""burak_blast_screen.png: the whole-arena flash and concussion that goes with every keg blast. 5 frames of
640x360 texels (1920x1080 px at 3x: the whole screen), one strip, 0.05 s each.
THE PIVOT IS THE TOP-LEFT (0, 0): draw it on a screen-space CanvasLayer at (0, 0), scale 3, over the arena
and under the HUD. It is position-independent on purpose: the kegs go up all over the ring, so the screen
effect lights and shakes the WHOLE arena wherever the keg was, while burak_blast (with its floor
shockwave) marks the keg itself.
  f0  a gold-white flash over the whole arena (#FFF3B0 at alpha 208)
  f1  the flash falling off (alpha 144); black-powder smoke bursts in at all four edges
  f2  the flash at alpha 80; the concussion smoke billows further in; ash begins to fall
  f3  the flash at alpha 32; the smoke thinning back to the edges; ash falling across the screen
  f4  the last of the smoke at the edges, the ash settling
Burak's colours (burak_boss.png): his hot gold for the flash, the iron greys for the smoke and ash; stepped
alpha only (the four flash steps, three smoke steps), hard edges, no dither.
"""
import math
import random

import bfx_pal as pal

W, H = 640, 360
FRAME_SIZE = (640, 360)
NOTE = '5 frames at 0.05 s; 640x360 = the whole screen at 3x; top-left pivot, screen space'

FLASH_ALPHA = [208, 144, 80, 32, 0]
SMOKE_ALPHA = [0, 176, 176, 112, 56]
SMOKE_REACH = [0, 22, 34, 28, 18]              # how far in from the edges the concussion billows


def keys(f):
    k = {}
    if FLASH_ALPHA[f]:
        k['@'] = (0xFF, 0xF3, 0xB0, FLASH_ALPHA[f])
    a = SMOKE_ALPHA[f]
    if a:
        k['a'] = (0x35, 0x35, 0x47, a)          # smoke body (#353547)
        k['b'] = (0x6D, 0x75, 0x89, a)          # its lit side (#6D7589)
        k['d'] = (0x23, 0x23, 0x2F, a)          # its shade (#23232F)
        k['e'] = (0xA6, 0xAF, 0xC1, a)          # ash, light (#A6AFC1)
    return k


def edge_puffs(f):
    """Puffs centred just outside the four edges, reaching SMOKE_REACH[f] texels in."""
    rnd = random.Random(40)                  # the same billows every frame, so they grow and thin in place
    reach = SMOKE_REACH[f]
    out = []
    for layer, (step, size) in enumerate(((30, 1.0), (19, 0.55))):
        for x in range(-10, W + 20, step):
            for y0, sgn in ((0, 1), (H, -1)):
                push = rnd.uniform(0.45, 1.6)            # how far this billow reaches in, relative
                r = size * (reach * push + 8)
                out.append((x + rnd.uniform(-9, 9), y0 + sgn * (reach * push - r + 2), r))
        for y in range(-10, H + 20, step):
            for x0, sgn in ((0, 1), (W, -1)):
                push = rnd.uniform(0.45, 1.6)
                r = size * (reach * push + 8)
                out.append((x0 + sgn * (reach * push - r + 2), y + rnd.uniform(-9, 9), r))
    return out


def ash(f):
    rnd = random.Random(7)
    pts = []
    for i in range(140):
        x = rnd.uniform(0, W)
        y0 = rnd.uniform(-40, H)
        y = y0 + (f - 1) * rnd.uniform(6, 14)
        pts.append((int(x), int(y), rnd.random() < 0.35))
    return pts


def frame(f):
    g = pal.blank(W, H)
    if FLASH_ALPHA[f]:
        for y in range(H):
            g[y] = ['@'] * W
    if SMOKE_ALPHA[f]:
        for (cx, cy, r) in edge_puffs(f):
            for y in range(max(0, int(cy - r)), min(H, int(cy + r) + 1)):
                for x in range(max(0, int(cx - r)), min(W, int(cx + r) + 1)):
                    dx, dy = x + 0.5 - cx, y + 0.5 - cy
                    d = math.hypot(dx, dy)
                    if d > r:
                        continue
                    hl = math.hypot(dx + 0.3 * r, dy + 0.34 * r)
                    g[y][x] = 'b' if hl < 0.5 * r else ('d' if (d > r - 2 and dx + dy > 0) else 'a')
        if f >= 2:
            for (x, y, light) in ash(f):
                if 0 <= x < W and 0 <= y < H:
                    g[y][x] = 'e' if light else 'd'
    return pal.Frame(pal.rows(g), keys(f))


def frames():
    return [frame(f) for f in range(5)]
