"""matt_boom.png: Matt's sonic boom, flying down the lane. 5 frames of 72x40, one strip:
  frames 0-2   forming, picked by charge progress (0-1/3, 1/3-2/3, 2/3-1)
  frames 3-4   in flight, alternating at 0.05 s
THE PIVOT IS THE LEADING APEX (36, 30): the bottom point of the front arc's centre line, on the frame's
centre column. As a centred Sprite2D: offset (0, -10) texture px. The badge (matt_boom_arrow) sits on the
same point. Never flipped, never rotated: it only ever flies straight down.

Three concentric arcs, convex down, sharing a centre above like wavefronts leaving his mouth: the front
arc spans a 64-texel chord (texels 4..67) with a 14-texel sagitta; the two behind it are 6 and 12 texels
further up. In the approved roar-ring style: the front arc an #F2F3FF core between #4F4D96 edges with
#C4C9FA flanks where it steps; the middle arc fainter (#C4C9FA core); the last fainter still (edge only).
Each arc's horns taper to a point. While it charges the arcs grow in (front first); in flight they
flicker a texel in and out, with speed streaks trailing up behind. No keyline, no partial alpha.
"""
import math

import mfx_pal as pal

W, H = 72, 40
AX, AY = 36.0, 30.0                    # the pivot: the leading apex
FRAME_SIZE = (72, 40)
NOTE = '5 frames: f0-2 forming by charge, f3-4 flight flicker at 0.05 s; pivot (36,30), offset (0,-10)'

HALF_CHORD, SAG = 32.0, 14.0
R = (HALF_CHORD ** 2 + SAG ** 2) / (2 * SAG)          # 43.6
OY = AY - R                                            # the arcs' shared centre, above the frame
PHI = math.asin(HALF_CHORD / R)                        # the front arc's half-angle


def arc_key(dd, t, style):
    """The key at signed distance dd from an arc's centre line, t = |angle| / its half-angle (0..1).
    The band narrows toward the horns and the core gives out before the tip."""
    taper = 1.0 - 0.55 * t ** 2
    a = abs(dd)
    if style == 'front':
        core, flank, edge, ck = 0.75 * taper, 1.05 * taper, 1.85 * taper, 's'
        if t > 0.88:
            ck = 'r'
    elif style == 'middle':
        core, flank, edge, ck = 0.55 * taper, 0.55 * taper, 1.4 * taper, 'r'
        if t > 0.85:
            ck = 'm'
    else:
        core, flank, edge, ck = 0.0, 0.0, 0.95 * taper, 'm'
    if a <= core:
        return ck
    if a <= flank:
        return 'r'
    if a <= edge:
        return 'm'
    return None


def paint_arc(g, radius, extent, style):
    """An arc of the given radius round the shared centre, spanning +-extent radians about straight down."""
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - AX, y + 0.5 - OY
            d = math.hypot(dx, dy)
            ang = math.atan2(dx, dy)                   # 0 straight down, +- toward the sides
            t = abs(ang) / extent
            if t > 1.0:
                continue
            k = arc_key(d - radius, t, style)
            if k is None:
                continue
            cur = g[y][x]
            if cur == '.' or (cur == 'm' and k != 'm') or (cur == 'r' and k == 's'):
                g[y][x] = k


# Per frame: (radius offset, extent fraction, style) for each arc drawn, front arc first.
FRAMES_SPEC = [
    [(0.0, 0.42, 'front')],
    [(0.0, 0.72, 'front'), (-6.0, 0.5, 'middle')],
    [(0.0, 1.0, 'front'), (-6.0, 0.9, 'middle'), (-12.0, 0.75, 'back')],
    [(0.0, 1.0, 'front'), (-6.0, 0.92, 'middle'), (-12.0, 0.78, 'back')],
    [(0.0, 1.0, 'front'), (-5.0, 0.9, 'middle'), (-11.0, 0.74, 'back')],
]
# Speed streaks in flight: (x, top row, length, key), trailing up from the arcs.
STREAKS = {
    3: [(12, 6, 5, 'm'), (22, 2, 6, 'r'), (50, 2, 6, 'r'), (60, 6, 5, 'm'), (31, 0, 5, 'm'), (41, 1, 4, 'm')],
    4: [(9, 9, 4, 'm'), (18, 4, 6, 'm'), (26, 0, 6, 'r'), (46, 0, 6, 'r'), (54, 4, 6, 'm'), (63, 9, 4, 'm')],
}


def frame(i):
    g = pal.blank(W, H)
    for dr, ext, style in reversed(FRAMES_SPEC[i]):
        paint_arc(g, R + dr, PHI * ext, style)
    for x, top, length, k in STREAKS.get(i, []):
        for y in range(top, top + length):
            if 0 <= y < H and g[y][x] == '.':
                g[y][x] = k
    return pal.rows(g)


def frames():
    return [frame(i) for i in range(5)]
