"""matt_stomp_dust.png: the dust Matt's slam throws up. 6 frames of 96x40 at 0.05 s, one strip.
THE PIVOT IS (48, 30): the slam foot on the floor. The dust ramp measured from the shipped Josh card plume
(#FBF7EE #EDE4D6 #C7BBAB #948779 #6B6157), without its keyline (Matt's effects carry none):
  f0  a flat burst along the floor at the foot
  f1-3  puffs rolling out left and right along the floor and billowing up, largest at f3
  f4-5  thinning, a step darker, breaking up at the ends
"""
import mfx_dustlib as dl
import mfx_pal as pal

W, H = 96, 40
PX, PY = 48.0, 30.0
FRAME_SIZE = (96, 40)
NOTE = '6 frames at 0.05 s; pivot (48,30) on the slam foot'

# Per frame: puffs as (x offset, y offset, radius); mirrored left and right (with small differences).
PUFFS = [
    [(0, 0, 4.5), (6, 1, 3.5), (11, 1.5, 2.5)],
    [(3, -1, 5.0), (11, 0, 4.5), (18, 1, 3.5), (0, -3, 3.5)],
    [(6, -3, 6.0), (15, -1, 5.5), (24, 0, 4.5), (31, 1, 3.0), (0, -6, 4.0)],
    [(8, -5, 6.5), (19, -3, 6.5), (29, -1, 5.5), (37, 0, 4.0), (1, -8, 4.5)],
    [(10, -7, 5.5), (22, -5, 5.5), (32, -3, 4.5), (40, -1, 3.0)],
    [(12, -9, 3.5), (24, -7, 3.5), (34, -5, 3.0), (42, -3, 2.0)],
]
FADE = [0, 0, 0, 0, 1, 2]


def frame(f):
    g = pal.blank(W, H)
    if f == 0:
        # the flat burst: a wide low sheet of dust at the foot
        for y in range(int(PY) - 2, int(PY) + 3):
            for x in range(W):
                dx = abs(x + 0.5 - PX)
                half = 16 - 3 * abs(y + 0.5 - PY)
                if dx <= half:
                    g[y][x] = '1' if y < PY - 0.5 else ('2' if y < PY + 1.5 else '4')
    for (ox, oy, r) in PUFFS[f]:
        for sx, jitter in ((1, 0.0), (-1, 0.6)):
            dl.puff(g, PX + sx * (ox + jitter), PY + oy + (0.4 if sx < 0 else 0.0), r, FADE[f])
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(6)]
