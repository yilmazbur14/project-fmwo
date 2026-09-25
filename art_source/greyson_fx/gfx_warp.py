"""Greyson's teleport, out and in: a violet warp in the cannon's paint (Computah's tech carries him). Two sheets,
6 frames of 96x140 each, at 0.05 s, once:
  greyson_teleport_out  f0 a beam of white-hot light stands up over him (show his sprite under it on f0 only),
                        f1 the beam at full width with a ring on the floor (hide his sprite from f1), f2 it
                        narrows and sheds pixel squares, f3 a thin line and the squares streaming up, f4 the line
                        gone, the squares thinning, f5 the last few (stepped alpha)
  greyson_teleport_in   the reverse: squares falling in and gathering (f0-1), a thin line (f2), the beam opening
                        over him at full width (f3: show his sprite from f3), fading off him (f4), a ring and a
                        glint on the floor (f5)
PIVOT: his feet on the floor (48, 126), like his body sheets' feet. Never flipped.
The cannon's violets (V v U u X) with white-hot hearts (W w). No keyline; the beam's flanks in stepped alpha.
"""
import math
import random

import gfx_pal as pal

W, H = 96, 140
PX, PY = 48.0, 126.0
TALL = 100.0                    # the beam's height: over his 86 texels


def beam(g, half, bright=True, top=TALL):
    """A vertical beam over his feet, `half` texels wide either side, white-hot in the middle."""
    for y in range(max(0, int(PY - top)), int(PY) + 1):
        t = (PY - y) / top
        taper = 1.0 - 0.35 * t * t - 0.5 * max(0.0, t - 0.8) * 5
        hw = half * taper
        for x in range(int(PX - hw) - 1, int(PX + hw) + 2):
            d = abs(x + 0.5 - PX) / max(0.6, hw)
            if d > 1.0 or not (0 <= x < W):
                continue
            if d < 0.4:
                k = 'W' if bright else 'V'
            elif d < 0.7:
                k = 'V' if bright else 'v'
            else:
                k = '5' if bright else '6'                  # the flanks, in stepped alpha
            if t > 0.9:
                k = '7' if k in 'WV5' else '8'              # its top dissolves
            elif t > 0.78:
                k = '5' if k in 'WV' else ('6' if k == 'v' else k)
            g[y][x] = k


def floor_ring(g, rx, keys='VU'):
    ry = rx * 0.34
    for i in range(int(2 * math.pi * rx * 2)):
        a = 2 * math.pi * i / int(2 * math.pi * rx * 2)
        x, y = int(PX + rx * math.cos(a)), int(PY + ry * math.sin(a))
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = keys[0] if math.sin(a) < 0 else keys[1]


def squares(g, t, rising=True, fade=0):
    """Pixel squares shed by the beam: 2x2 and 1x1, rising (or falling in) along it."""
    rnd = random.Random(17)
    for i in range(26):
        x0 = PX + rnd.uniform(-14, 14)
        y0 = PY - rnd.uniform(4, TALL)
        v = rnd.uniform(60, 140)
        drift = rnd.uniform(-10, 10)
        if rising:
            x, y = x0 + drift * t, y0 - v * t
        else:
            x, y = x0 + drift * (1 - t), y0 - v * (1 - t)
        s = 2 if i % 3 else 1
        if y < 1 or y > H - 3:
            continue                                       # risen out of view: gone, never cut at the edge
        k = ['W', 'V', 'v'][i % 3]
        if fade:
            k = {'W': '7', 'V': '7', 'v': '8'}[k] if fade == 2 else {'W': '5', 'V': '5', 'v': '6'}[k]
        for dx in range(s):
            for dy in range(s):
                pal.put(g, int(x) + dx, int(y) + dy, k)


LOCAL = {'5': pal.hx('C892F2', 168), '6': pal.hx('A063DC', 168), '7': pal.hx('C892F2', 96), '8': pal.hx('A063DC', 96)}


def out_frame(f):
    g = pal.blank(W, H)
    if f == 0:
        floor_ring(g, 18, 'Vv')
        beam(g, 12, True)
    elif f == 1:
        floor_ring(g, 26, 'WV')
        beam(g, 18, True)
    elif f == 2:
        floor_ring(g, 22, 'Vv')
        beam(g, 7, True)
        squares(g, 0.05)
    elif f == 3:
        floor_ring(g, 16, 'vU')
        beam(g, 1.6, True)
        squares(g, 0.15)
    elif f == 4:
        floor_ring(g, 10, 'vU')
        squares(g, 0.28, fade=1)
    else:
        squares(g, 0.42, fade=2)
    return pal.Frame(pal.rows(g), LOCAL)


def in_frame(f):
    g = pal.blank(W, H)
    if f == 0:
        squares(g, 0.55, rising=False, fade=1)
    elif f == 1:
        squares(g, 0.8, rising=False)
        floor_ring(g, 8, 'vU')
    elif f == 2:
        beam(g, 1.6, True)
        squares(g, 0.95, rising=False)
        floor_ring(g, 14, 'Vv')
    elif f == 3:
        beam(g, 18, True)
        floor_ring(g, 26, 'WV')
    elif f == 4:
        beam(g, 12, False)
        floor_ring(g, 30, 'Vv')
    else:
        floor_ring(g, 32, 'vU')
        for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, -2), (0, 2)):
            pal.put(g, int(PX + 20) + dx, int(PY - 70) + dy, 'W' if abs(dx) + abs(dy) < 2 else 'V')
    return pal.Frame(pal.rows(g), LOCAL)


def out_frames():
    return [out_frame(f) for f in range(6)]


def in_frames():
    return [in_frame(f) for f in range(6)]


SHEETS = {'greyson_teleport_out': (out_frames, (W, H)), 'greyson_teleport_in': (in_frames, (W, H))}
