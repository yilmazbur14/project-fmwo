"""matt_fury_puff.png: the small puff at each of Matt's furious stomps. 4 frames of 32x16 at 0.04 s.
THE PIVOT IS (16, 12): the stomping foot on the floor. The same dust ramp as matt_stomp_dust, no keyline:
a low burst, two puffs rolling out each side, then thinning away.
"""
import mfx_dustlib as dl
import mfx_pal as pal

W, H = 32, 16
PX, PY = 16.0, 12.0
FRAME_SIZE = (32, 16)
NOTE = '4 frames at 0.04 s; pivot (16,12) on the foot'
PUFFS = [
    [(0, 0, 3.0), (4, 0.5, 2.2)],
    [(3, -1, 3.2), (8, 0, 2.6)],
    [(5, -2, 3.2), (11, -1, 2.6)],
    [(7, -3, 2.4), (13, -2, 1.8)],
]
FADE = [0, 0, 1, 2]


def frame(f):
    g = pal.blank(W, H)
    for (ox, oy, r) in PUFFS[f]:
        for sx in (1, -1):
            dl.puff(g, PX + sx * ox, PY + oy, r, FADE[f])
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
