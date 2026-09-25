"""matt_yell_rings.png: the sound rings of Matt's yell (and the intro roar's visual-only rings). 7 frames of
200x200, one strip:
  frames 0-5   the front ring at radius 20, 37, 54, 71, 83, 90 texels (60 -> 270 px at 3x), 0.03 s each
  frame 6      the fade, 0.06 s: both rings break up into dashes
THE PIVOT IS THE FRAME CENTRE (100, 100): put it on his mouth texel. The rings are circles round it, so the
drawn front matches the hitbox (radius 60 -> 270 px, hurt band +-15 px): the ring's band spans the front
radius +-2 texels (+-6 px), inside the hurt band.

The style is the approved roar's baked rings (matt.png frame 1), measured: a band 3-4 texels thick, an
#F2F3FF core 1-2 texels wide between #4F4D96 edges, with #C4C9FA flanks where the band steps on its curve.
Behind the front ring (12 texels in) runs a fainter second ring: an #C4C9FA core, thinner, same edge. The
first frame's front is a texel thicker, the burst leaving his mouth. No partial alpha; the fade is the
rings breaking into dashes, not a dissolve.
"""
import math

import mfx_pal as pal

W = H = 200
CX = CY = 100.0
FRAME_SIZE = (200, 200)
NOTE = '7 frames: front radius 20/37/54/71/83/90 texels at 0.03 s, then f6 the fade at 0.06 s'
FRONT = [20, 37, 54, 71, 83, 90]
BEHIND = 12


def band_key(dd, core, flank, edge, core_key):
    """The ring's key at a signed distance dd (texels) from its radius, or None outside it."""
    a = abs(dd)
    if a <= core:
        return core_key
    if a <= flank:
        return 'r'
    if a <= edge:
        return 'm'
    return None


def ring(g, radius, core_key, core, flank, edge, dash=None):
    """Paint one ring into g. dash=(count, fraction on, phase) breaks it into dashes."""
    r_out = radius + edge + 1
    x0, x1 = int(CX - r_out) - 1, int(CX + r_out) + 2
    for y in range(max(0, x0), min(H, x1)):
        for x in range(max(0, x0), min(W, x1)):
            dx, dy = x + 0.5 - CX, y + 0.5 - CY
            d = math.hypot(dx, dy)
            k = band_key(d - radius, core, flank, edge, core_key)
            if k is None:
                continue
            if dash:
                n, on, ph = dash
                a = (math.atan2(dy, dx) / (2 * math.pi) + ph) % 1.0
                if (a * n) % 1.0 > on:
                    continue
            if g[y][x] == '.' or (g[y][x] == 'm' and k != 'm'):
                g[y][x] = k


def frame(i):
    g = pal.blank(W, H)
    if i < 6:
        r = FRONT[i]
        if r - BEHIND > 4:
            ring(g, r - BEHIND, 'r', 0.55, 0.55, 1.45)          # the fainter second ring
        thick = 1.25 if i == 0 else 0.0
        ring(g, r, 's', 0.75 + thick, 1.05 + thick, 1.85 + thick)
    else:
        r = FRONT[-1] + 2
        ring(g, r - BEHIND, 'm', 0.55, 0.55, 1.2, dash=(18, 0.35, 0.02))
        ring(g, r, 'r', 0.75, 0.75, 1.6, dash=(24, 0.55, 0.0))
    return pal.rows(g)


def frames():
    return [frame(i) for i in range(7)]
