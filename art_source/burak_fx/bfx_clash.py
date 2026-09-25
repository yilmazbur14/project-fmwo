"""burak_clash.png: the spark when the player parries Burak (his cutlass or his shot). 5 frames of 32x32 at
0.04 s, one strip. THE PIVOT IS THE FRAME CENTRE (16, 16): the point of the clash. Never flipped.
  f0  a white-hot cross of light
  f1  it twists into a bigger star, sparks leaving it
  f2  a ring of sparks flying out, the heart fading to gold
  f3  the sparks further out, cooling
  f4  the last sparks
Burak's gold (#FFF3B0 #F5D94E #E0AB35 #B07D22 #7A5216) round a #FFFCF4 heart, with his steel (#DCE3EE) in the
star's long arms: steel on steel. No keyline, opaque.
"""
import math

import bfx_pal as pal

W = H = 32
C = 16.0
FRAME_SIZE = (32, 32)
NOTE = '5 frames at 0.04 s; pivot = centre (16,16)'


def put(g, x, y, k):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = k


def star(g, rot, long_len, short_len, core_r, keys_long, keys_short):
    for y in range(H):
        for x in range(W):
            if math.hypot(x + 0.5 - C, y + 0.5 - C) <= core_r:
                g[y][x] = 'W'
    for i in range(8):
        a = math.radians(rot + 45 * i)
        length = long_len if i % 2 == 0 else short_len
        keys = keys_long if i % 2 == 0 else keys_short
        s = core_r - 0.5
        while s <= length:
            x = int(math.floor(C + math.cos(a) * s))
            y = int(math.floor(C + math.sin(a) * s))
            k = keys[min(len(keys) - 1, int((s / max(1.0, length)) * len(keys)))]
            if g[y][x] != 'W':
                put(g, x, y, k)
            s += 0.3


def sparks(g, radius, keys, n=10, rot=10):
    for i in range(n):
        a = math.radians(rot + 360.0 * i / n)
        r = radius * (1.0 if i % 2 == 0 else 0.8)
        x = int(math.floor(C + math.cos(a) * r))
        y = int(math.floor(C + math.sin(a) * r))
        put(g, x, y, keys[0])
        # a short tail pointing back at the clash
        put(g, int(math.floor(C + math.cos(a) * (r - 1.2))), int(math.floor(C + math.sin(a) * (r - 1.2))), keys[1])


def frame(f):
    g = pal.blank(W, H)
    if f == 0:
        star(g, 0, 11, 5, 2.2, 'WSQY', 'QY')
    elif f == 1:
        star(g, 45, 14, 7, 2.6, 'WQYG', 'YG')
        sparks(g, 9, 'YG', n=8, rot=22)
    elif f == 2:
        star(g, 22.5, 8, 4, 1.4, 'QYG', 'Gg')
        sparks(g, 12, 'YG', n=10)
    elif f == 3:
        sparks(g, 14, 'Gg', n=10, rot=14)
        put(g, 15, 15, 'G'); put(g, 16, 16, 'G')
    elif f == 4:
        sparks(g, 15, 'gh', n=8, rot=30)
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(5)]
