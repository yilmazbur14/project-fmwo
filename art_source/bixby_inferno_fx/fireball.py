"""bixby_fireball.png: the Inferno's fireballs. 2 rows x 4 frames of 16x24 texels.

Row 1 is a ball FALLING: the ball low in the frame, its hot face leading (down), its flame trail streaming
up behind it. Row 0 is the same ball RISING, drawn by flipping row 1 top to bottom, so the leading face and
the trail swap ends together. The 4 frames flicker the trail and roll the core (0.06 s each).

  ball centre  row 1 (falling): (8, 17)    row 0 (rising): (8, 7)     (texels from the frame's top-left
  corner; the ball fills columns 2-13 and rows 11-22, or 1-12 when rising). A centred Sprite2D puts the
  ball on its node with offset (0, -5) falling and (0, +5) rising.
  The trail points straight up in row 1 and straight down in row 0: code that tilts the rising ball along
  its velocity rotates about the ball centre by (angle of velocity + 90 degrees).

The redesign's throat ramp, dark-blood rim ('r') outermost, white-hot core; no black keyline, like the
rest of his fire.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from firelib import rings, put, close_holes  # noqa: E402

W, H = 16, 24
BALL = (8.0, 17.0)     # falling row: centre of the ball (x between columns 7 and 8)
R = 5.6


def disc(cx, cy, r):
    return {(x, y) for y in range(H) for x in range(W) if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


# Trail tongues, per frame: (root dx from the ball centre, length above the ball's top, root half-width,
# sway at the tip). Narrower than the ball and spaced apart, so the tail splits into flames.
TRAIL = [
    [(-3.0, 7, 2.1, -1.0), (0.0, 11, 2.7, 0.5), (3.2, 6, 2.0, 1.2)],
    [(-3.2, 9, 2.1, -1.4), (0.2, 9, 2.7, -0.5), (3.0, 8, 2.1, 0.8)],
    [(-2.6, 6, 2.0, -0.6), (0.4, 12, 2.8, 1.0), (3.4, 6, 1.9, 1.4)],
    [(-3.3, 8, 2.2, -1.2), (-0.2, 10, 2.6, -0.9), (2.8, 7, 2.1, 0.6)],
]
SPARKS = [[(3, 2), (12, 5)], [(4, 0), (11, 3)], [(2, 4), (13, 1)], [(5, 1), (10, 0)]]


def falling(f):
    g = [['.'] * W for _ in range(H)]
    bx, by = BALL
    ball = disc(bx, by, R)
    trail = set()
    top = by - R + 2.5
    for dx, length, hw, sway in TRAIL[f]:
        for i in range(int(length) + 1):
            s = i / length
            half = hw * (1.0 - s) ** 0.6
            c = bx + dx + sway * s * s
            y = int(math.floor(top - i))
            if half < 0.5:
                trail.add((int(math.floor(c)), y))
                continue
            for x in range(int(math.floor(c - half + 0.5)), int(math.floor(c + half - 0.5)) + 1):
                trail.add((x, y))
    shape = close_holes({(x, y) for (x, y) in ball | trail if 0 <= x < W and 0 <= y < H})
    depth = rings(shape)
    # the hot point sits toward the leading (bottom) face and rolls a texel with the frame
    hx = bx + (0.5 if f in (1, 2) else -0.5)
    hy = by + 1.2
    for (x, y), d in depth.items():
        if d == 0:
            k = 'r'
        elif (x, y) in ball:
            dd = math.hypot(x + 0.5 - hx, (y + 0.5 - hy) * 1.1)
            k = 'W' if dd < 1.7 else 'Y' if dd < 2.9 else 'P' if dd < 4.0 else 'p' if dd < 4.9 else 'N'
        else:
            up = (by - R) - y
            k = 'p' if (d >= 2 or (d >= 1 and up < 3)) and up < 6 else ('N' if up < 10 else 'n')
        put(g, x, y, k)
    for (x, y) in SPARKS[f]:
        if g[y][x] == '.':
            put(g, x, y, 'P' if (x + y + f) % 2 else 'Y')
    return g


def rising(f):
    return [row[:] for row in reversed(falling(f))]


def frames():
    """Rows: [rising x4], [falling x4]."""
    return [[rising(f) for f in range(4)], [falling(f) for f in range(4)]]
