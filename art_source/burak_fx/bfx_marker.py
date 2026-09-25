"""burak_barrel_marker.png: where a thrown keg will land, sized to the 2x keg's footprint. 4 frames of 64x32,
looping at 0.1 s, one strip.
THE PIVOT IS THE FRAME CENTRE (32, 16): the landing point. Never flipped.
A crimson target reticle lying on the floor (an ellipse ring and four ticks) round the keg's footprint (its
base is 28 texels across), pulsing in and brightening as the keg comes down. Burak's coat crimsons (#D95763
#D8434F #B02436 #7E162B) with a gold centre pip (#F5D94E #E0AB35 #B07D22): crimson on the green mat is the
strongest warning the palette has. No keyline, opaque. Drawn natively: the first draft's measures (32x16)
times S = 2.0; the ring, ticks and pip thicken with S.
"""
import math

import bfx_pal as pal

S = 2.0
W, H = int(32 * S + 0.5), int(16 * S + 0.5)
CX, CY = W / 2.0, H / 2.0
FRAME_SIZE = (W, H)
NOTE = '4 frames of %dx%d looping at 0.1 s; pivot = centre (%d,%d), the landing point' % (W, H, CX, CY)
SQUASH = 0.42
CORE_W = 0.5 * S            # half-width of the ring's bright core
EDGE_W = 0.97 * S           # how far out its dark outer edge reaches

SPEC = [(13.5, '3', '5'), (12.5, '2', '3'), (11.5, '1', '2'), (12.5, '2', '3')]   # radius (x S), core, edge


def rnd(v):
    return int(math.floor(v + 0.5))


def frame(f):
    g = pal.blank(W, H)
    r0, core, edge = SPEC[f]
    rx = r0 * S
    ry = rx * SQUASH
    pts = [(CX + rx * math.cos(2 * math.pi * i / 800), CY + ry * math.sin(2 * math.pi * i / 800))
           for i in range(800)]
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5, y + 0.5
            if abs(((px - CX) / rx) ** 2 + ((py - CY) / ry) ** 2 - 1.0) > 0.6:
                continue
            d = min(math.hypot(px - a, py - b) for (a, b) in pts)
            inside = ((px - CX) / rx) ** 2 + ((py - CY) / ry) ** 2 < 1.0
            if d <= CORE_W:
                g[y][x] = core
            elif d <= EDGE_W and not inside:
                g[y][x] = edge
    # four ticks pointing in at the ring, and a gold pip on the landing point
    tick_h, tick_v, tick_w = rnd(1.5 * S), rnd(1.4 * S), max(2, rnd(1.25 * S))   # f0's widest ring still fits
    cxi, cyi = int(CX), int(CY)
    for side in (-1, 1):
        x_edge = CX + side * (rx + EDGE_W)                  # the ring's outer edge on this side
        for i in range(tick_h):
            x = int(math.floor(x_edge + side * (i + 0.5)))
            for w in range(tick_w):
                y = cyi - tick_w // 2 + w
                if 0 <= x < W and 0 <= y < H:
                    g[y][x] = core
        y_edge = CY + side * (ry + EDGE_W)
        for i in range(tick_v):
            y = int(math.floor(y_edge + side * (i + 0.5)))
            for w in range(tick_w):
                x = cxi - tick_w // 2 + w
                if 0 <= x < W and 0 <= y < H:
                    g[y][x] = core
    pip = max(2, rnd(S))                                  # a pip pip x pip texels, lit top left
    x0, y0 = cxi - pip // 2, cyi - pip // 2
    for y in range(pip):
        for x in range(pip):
            g[y0 + y][x0 + x] = 'Y' if y < pip / 2.0 else 'G'
    g[y0][x0 - 1] = 'G'
    g[y0 + pip - 1][x0 + pip] = 'g'
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
