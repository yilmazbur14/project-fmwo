"""matt_glass_shadow.png: the shadow a falling shard casts on its landing spot. 1 frame of 20x8.
THE PIVOT IS THE FRAME CENTRE (10, 4). A solid #1B1638 ellipse, as the plan asks; the code scales it
0.3 -> 1.0 and fades it 0.15 -> 0.5 during the fall.
"""
import math

import mfx_pal as pal

FRAME_SIZE = (20, 8)
NOTE = '1 frame; pivot = frame centre (10,4)'


def frames():
    g = pal.blank(20, 8)
    for y in range(8):
        for x in range(20):
            if ((x + 0.5 - 10) / 10.0) ** 2 + ((y + 0.5 - 4) / 4.0) ** 2 <= 1.0:
                g[y][x] = 'S'
    return [pal.rows(g)]
