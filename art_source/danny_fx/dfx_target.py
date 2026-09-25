"""danny_slam_target.png: where Danny's butt slam will land, his tracking shadow growing as he drops. 6 frames
of 144x32, one strip.
THE PIVOT IS THE FRAME CENTRE (72, 16): the point his rear lands on. Never flipped.
  f0 .. f5   the shadow at 45%, 56%, 67%, 78%, 89% and 100% of his seated footprint (132x22 texels, the size
             of danny_leap_shadow's largest), darker as it grows, ringed by a warning reticle in his collar
             reds (r R q) with four ticks and a gold pip (Y G) on the spot. Show the frame by how far he has
             come down: f0 while he hovers and tracks (loop f0-f1 at 0.1 s there, a pulse), f5 on the frame
             before he lands.
The shadow is his navy (#222034) in stepped alpha (outer 96, inner 144 on f0-2; 120 and 168 on f3-5, once
he is close); the reticle is opaque. No keyline.
"""
import math

import dfx_pal as pal

W, H = 144, 32
CX, CY = 72.0, 16.0
RX, RY = 66.0, 11.0
FRAME_SIZE = (W, H)
NOTE = '6 frames of 144x32 by fall height (f0 hovering, loop f0-f1 at 0.1 s; f5 just before he lands); pivot = centre (72,16)'
SIZES = [0.45, 0.56, 0.67, 0.78, 0.89, 1.0]
ALPHA = [(96, 144)] * 3 + [(120, 168)] * 3        # two steps inside each frame, darker once he is close


def frame(f):
    g = pal.blank(W, H)
    s = SIZES[f]
    rx, ry = RX * s, RY * s
    a_out, a_in = ALPHA[f]
    local = {'z': pal.hx('222034', a_out), 'Z': pal.hx('222034', a_in)}
    for y in range(H):
        for x in range(W):
            d = math.hypot((x + 0.5 - CX) / rx, (y + 0.5 - CY) / ry)
            if d <= 1.0:
                g[y][x] = 'Z' if d <= 0.72 else 'z'
    # the reticle: an even ring on the shadow's rim (true distance to the ellipse), dashed by arc length
    # (dashes about 7 texels, gaps about 3), lit on its upper left, its outer edge darker
    n = 900
    pts = [(CX + rx * math.cos(2 * math.pi * i / n), CY + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]
    arc = [0.0]
    for i in range(1, n):
        arc.append(arc[-1] + math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]))
    total = arc[-1] + math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])
    period = total / round(total / 10.0)
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            if abs(math.hypot((px - CX) / rx, (py - CY) / ry) - 1.0) > 3.0 / min(rx, ry * 2.2):
                continue
            j = min(range(n), key=lambda i: (pts[i][0] - px) ** 2 + (pts[i][1] - py) ** 2)
            d = math.hypot(pts[j][0] - px, pts[j][1] - py)
            inside = ((px - CX) / rx) ** 2 + ((py - CY) / ry) ** 2 < 1.0
            if d > (0.8 if inside else 1.3):
                continue
            if (arc[j] % period) > period * 0.7:
                continue
            lit = (-(px - CX) / rx - (py - CY) / ry) > 0.25
            g[y][x] = ('r' if lit else 'R') if (inside or d < 0.5) else 'q'
    # ticks pointing in at the ring: 3 long at the ends, 2 at the top and bottom
    for i in range(3):
        for w in (0, 1):
            pal.put(g, int(CX - rx) - 2 - i, int(CY) - 1 + w, 'R')
            pal.put(g, int(math.ceil(CX + rx)) + 1 + i, int(CY) - 1 + w, 'R')
    for i in range(2):
        for w in (0, 1):
            pal.put(g, int(CX) - 1 + w, int(CY - ry) - 2 - i, 'R')
            pal.put(g, int(CX) - 1 + w, int(math.ceil(CY + ry)) + 1 + i, 'R')
    # the gold pip on the spot
    for (x, y, k) in ((71, 15, 'Y'), (72, 15, 'Y'), (71, 16, 'G'), (72, 16, 'G'), (70, 15, 'G'), (73, 16, 'h')):
        g[y][x] = k
    return pal.Frame(pal.rows(g), local)


def frames():
    return [frame(f) for f in range(6)]
