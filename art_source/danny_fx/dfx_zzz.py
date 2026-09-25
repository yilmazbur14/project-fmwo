"""danny_sleep_z.png: Z's rising off Danny while he sleeps. 8 frames of 40x56, looping at 0.12 s, one strip.
THE PIVOT IS (6, 52): where the Z's come from. Put it at his head (by the sleep bubble on his sleeping frames);
they drift up and to the right. flip_h with him if he faces the other way.
Three Z's always in the air, a third of a loop apart, each growing as it rises and thinning out at the top
in stepped alpha (255, then 176, then 96). His beanie's pale blues (Q P, shaded L and B at their lower edges
so they hold on his skin and on the mat). No keyline.
"""
import math

import dfx_pal as pal

W, H = 40, 56
PX, PY = 6.0, 52.0
FRAME_SIZE = (W, H)
NOTE = '8 frames of 40x56 looping at 0.12 s; pivot (6,52) = where the Zs rise from (his head); flip_h with him'
# stepped-alpha versions of the Z keys (frame-local)
FADE = {176: {'a': 'F0F5FF', 'b': 'CBDBFC', 'c': '97ABEF', 'd': '5B6EE1'},
        96: {'e': 'F0F5FF', 'f': 'CBDBFC', 'g': '97ABEF', 'h': '5B6EE1'}}


def glyph(size):
    """A Z `size` texels square with strokes 1 (size < 7) or 2 texels thick: top bar, diagonal, bottom bar.
    Keys: Q lit top edges, P body, L lower edges, B the underside of the bottom bar."""
    t = 1 if size < 7 else 2
    g = [['.'] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            top = y < t
            bot = y >= size - t
            dia = abs((size - 1 - x) - y * (size - 1) / (size - 1)) < t * 0.75 + 0.2
            if top or bot or dia:
                g[y][x] = 'P'
    for y in range(size):
        for x in range(size):
            if g[y][x] != 'P':
                continue
            if y == 0 or (y > 0 and g[y - 1][x] == '.'):
                g[y][x] = 'Q'
            elif y == size - 1:
                g[y][x] = 'B'
            elif y + 1 < size and g[y + 1][x] == '.':
                g[y][x] = 'L'
    return g


def frame(f):
    g = pal.blank(W, H)
    local = {}
    for lvl, keys in FADE.items():
        local.update({k: pal.hx(v, lvl) for k, v in keys.items()})
    for n in range(3):
        u = ((f + n * 8 / 3.0) % 8) / 8.0                  # 0 at the head .. 1 at the top of its rise
        size = int(round(5 + 5 * u))
        x0 = PX + 2 + 18 * u + 2.0 * math.sin(u * 6.28 + n)
        y0 = PY - 6 - 34 * u
        gl = glyph(size)
        fade = 0 if u < 0.62 else (176 if u < 0.84 else 96)
        remap = {} if not fade else dict(zip('QPLB', FADE[fade].keys()))
        for yy in range(size):
            for xx in range(size):
                k = gl[yy][xx]
                if k == '.':
                    continue
                x, y = int(x0 + xx), int(y0 - size + yy)
                if 0 <= x < W and 0 <= y < H:
                    g[y][x] = remap.get(k, k)
    return pal.Frame(pal.rows(g), local)


def frames():
    return [frame(f) for f in range(8)]
