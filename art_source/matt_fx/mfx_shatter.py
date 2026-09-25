"""matt_glass_shatter.png: the player crashing into the glass bed. 6 frames of 80x56 at 0.05 s, one strip.
THE PIVOT IS (40, 44): on the player's feet. The glass ramp, opaque, no keyline:
  f0  a blinding flash across the floor at their feet, spikes of glass shooting up round them
  f1  a fountain of shards bursting up and out, the flash fading
  f2  the shards high and spreading, turning as they fly, cracks spidering across the floor
  f3  the shards at the top of their flight
  f4  raining back down, smaller and darker
  f5  settled round the feet, a couple of glints
"""
import math

import mfx_glassbits as gb
import mfx_pal as pal

W, H = 80, 56
PX, PY = 40.0, 44.0
FRAME_SIZE = (80, 56)
NOTE = '6 frames at 0.05 s; pivot (40,44) on the feet'
TIMES = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
GRAV = 520.0


def flash(g, rx, ry, keys):
    for y in range(H):
        for x in range(W):
            d = ((x + 0.5 - PX) / rx) ** 2 + ((y + 0.5 - PY) / ry) ** 2
            if d <= 1.0:
                g[y][x] = keys[0] if d < 0.35 else (keys[1] if d < 0.75 else keys[2])


def spike(g, x0, height, lean):
    for i in range(height):
        x = int(round(x0 + lean * i))
        y = int(PY) - i
        w = 2 if i < height - 3 else 1
        for dx in range(w):
            if 0 <= x + dx < W and 0 <= y < H:
                g[y][x + dx] = 'W' if dx == 0 else ('K' if i < height - 3 else 'E')


def cracks(g, f):
    rays = [(-1, 0.1, 22), (1, -0.05, 24), (-1, -0.25, 14), (1, 0.3, 15), (-0.4, 1, 8), (0.5, 1, 9)]
    for (dx, dy, n) in rays:
        length = min(n, 6 + 6 * (f - 1))
        for s in range(3, length):
            x = int(round(PX + dx * s))
            y = int(round(PY + 1 + dy * s * 0.35))
            if 0 <= x < W and 0 <= y < H and g[y][x] == '.':
                g[y][x] = 'J' if f < 4 else 'K'


def frame(f):
    g = pal.blank(W, H)
    t = TIMES[f]
    if f == 0:
        flash(g, 20, 4.5, 'WEI')
        for (x0, h, lean) in ((33, 10, -0.35), (37, 14, -0.12), (42, 13, 0.1), (46, 9, 0.35), (29, 6, -0.6),
                              (50, 7, 0.55)):
            spike(g, x0, h, lean)
    elif f == 1:
        flash(g, 16, 3.0, 'EIJ')
    if f >= 2:
        cracks(g, f)
    if f >= 1:
        for (vx, vy, size, spin) in gb.fragments(11, 26, 175.0, 1.0, 62, (3, 4, 4, 5, 5, 6, 2), mirrored=True):
            x = PX + vx * t
            y = PY - 3 + vy * t + 0.5 * GRAV * t * t
            age = gb.GLASS_BY_AGE[min(4, max(0, f - 1))]
            if f == 5:
                age = 'J' if spin % 2 else 'K'
            gb.put_bit(g, x, y, size if f < 4 else max(1, size - 1), spin + f, age, floor_y=int(PY) + 2)
    if f == 5:
        for (x, y) in ((33, 45), (48, 44), (40, 46)):
            g[y][x] = 'W'
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(6)]
