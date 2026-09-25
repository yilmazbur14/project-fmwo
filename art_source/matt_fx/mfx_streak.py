"""matt_mystic_streak.png (optional): the faint dark streak a Mystic bolt casts on the floor. 6 frames of
40x40, one strip, laid out exactly like matt_mystic_bolt.png:
  frames 0-1   heading 22.5 degrees
  frames 2-3   heading 45 degrees
  frames 4-5   heading 67.5 degrees
2 frames per heading, alternating at the bolt's 0.05 s. Same flips as the bolt.

SAME FRAME SIZE AND PIVOTS AS THE BOLT: the pivot is the bolt's core texel for that heading (22.5: (29,23),
45: (27,27), 67.5: (23,29)), so the bolt's offset table serves both. Put it on FloorLayer at the bolt's
position + (0, 24) px, modulate 0.3, as the plan says.

Solid #000000, as the project's other ground shadows are (bixby_beast_shadow*.png); the modulate makes it
faint. The shape is the bolt's footprint simplified: a blunt wedge under the head, 4 texels wide,
tapering along the trail to a 1-texel tail about 24 texels behind; the tail wavers between the two frames.
"""
import math

import mfx_bolt as bolt
import mfx_pal as pal

W = H = 40
FRAME_SIZE = (40, 40)
NOTE = '6 frames: 22.5 deg f0-1, 45 deg f2-3, 67.5 deg f4-5; alternate at 0.05 s'

U_FRONT, U_BACK = 3.2, -24.0


def half_width(u, f):
    if u > 0.0:
        return 2.1 * math.sqrt(max(0.0, 1.0 - (u / U_FRONT) ** 2))        # a blunt, rounded front
    s = u / U_BACK                                                        # 0 at the core .. 1 at the tail
    wob = 0.3 * math.sin(2 * math.pi * s * 2.0 + (0.0 if f == 0 else math.pi)) * s
    return max(0.0, 2.1 - 1.6 * s ** 0.8 + wob)


def frame(theta, f):
    core = bolt.CORE[theta]
    g = pal.blank(W, H)
    for y in range(H):
        for x in range(W):
            u, v = bolt.uv(x, y, core, theta)
            if U_BACK <= u <= U_FRONT and abs(v) <= half_width(u, f):
                g[y][x] = 'k'
    return pal.rows(g)


def frames():
    by = {t: [frame(t, f) for f in range(2)] for t in (22.5, 45.0)}
    by[67.5] = [pal.transpose(fr) for fr in by[22.5]]
    return by[22.5] + by[45.0] + by[67.5]
