"""matt_glass_land.png: a falling shard landing in the glass bed. 4 frames of 32x20 at 0.04 s, one strip.
THE PIVOT IS (16, 14): the landing point on the floor. The glass ramp, opaque, no keyline:
  f0  a white flash on the floor where the point strikes, its spike standing up out of it
  f1  bits hopping out left, right and up, hairline cracks running along the floor
  f2  the bits at the top of their hop and falling, the flash gone
  f3  the bits settled on the floor round it, a glint where it struck
"""
import mfx_glassbits as gb
import mfx_pal as pal

W, H = 32, 20
PX, PY = 16.0, 14.0
FRAME_SIZE = (32, 20)
NOTE = '4 frames at 0.04 s; pivot (16,14) on the landing point'
TIMES = [0.0, 0.04, 0.08, 0.12]
GRAV = 1100.0


def frame(f):
    g = pal.blank(W, H)
    t = TIMES[f]
    if f == 0:
        for x in range(9, 23):
            g[14][x] = 'W' if 12 <= x <= 19 else 'E'
        for x in range(11, 21):
            g[15][x] = 'I' if x in (11, 20) else 'E'
            g[13][x] = 'E' if 12 <= x <= 19 else 'I'
        for y in range(8, 14):
            g[y][15] = 'W'
            g[y][16] = 'E' if y < 12 else 'W'
        g[7][15] = 'E'
    if f in (1, 2, 3):
        # hairline cracks along the floor from the strike point
        for (dx, dy) in ((-3, 0), (-4, 0), (-5, 1), (-6, 1), (3, 0), (4, 0), (5, -1), (6, -1), (7, -1),
                         (-1, 1), (1, 1), (2, 2)):
            k = 'J' if f < 3 else 'K'
            g[14 + dy][16 + dx] = k
        if f == 3:
            g[13][16] = 'W'
            g[12][16] = 'E'
            g[13][15] = 'E'
            g[13][17] = 'E'
    for (vx, vy, size, spin) in gb.fragments(7, 8, 78.0, 1.0, 70, (1, 2, 2, 3), mirrored=True):
        if f == 0:
            continue
        x = PX + vx * t
        y = PY - 1 + vy * t + 0.5 * GRAV * t * t
        age = gb.GLASS_BY_AGE[min(4, f)]
        gb.put_bit(g, x, y, size, spin + f, age, floor_y=int(PY) + 1)
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
