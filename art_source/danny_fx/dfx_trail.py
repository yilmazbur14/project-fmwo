"""danny_headbutt_trail.png: the speed trail behind Danny's Sumo Headbutt torpedo. 4 frames of 160x96, looping at
0.04 s, one strip. Drawn for a torpedo flying RIGHT (the body sheet's side view): flip_h with the body for a
flight to the left. Horizontal only, never rotated.
THE PIVOT IS (156, 48): the front of the trail, where it tucks under the back of his body. Put it on the rear
of his body box, level with its middle, and draw it BEHIND the body.
White-hot speed lines streaming back off him (W Q P, cooling to his pale blues L M at their tails), thickest
and brightest nearest him, scrolling back each frame, inside an air cone (two long curved wake lines closing
on him). No keyline, opaque.
"""
import math
import random

import dfx_pal as pal

W, H = 160, 96
PX, PY = 156.0, 48.0
FRAME_SIZE = (W, H)
NOTE = '4 frames of 160x96 looping at 0.04 s, flying right (flip_h for left); pivot (156,48) = the back of his body box'

# streaks: (y offset from the middle, length, thickness, phase): the longest and thickest near the middle
STREAKS = [(-34, 70, 2, 0.1), (-27, 100, 2, 0.6), (-20, 125, 3, 0.3), (-12, 145, 4, 0.8), (-4, 152, 4, 0.45),
           (4, 150, 4, 0.2), (12, 140, 4, 0.7), (20, 118, 3, 0.4), (27, 95, 2, 0.9), (34, 68, 2, 0.55),
           (-40, 42, 1, 0.5), (40, 40, 1, 0.0), (-16, 60, 1, 0.15), (16, 58, 1, 0.65)]


def frame(f):
    g = pal.blank(W, H)
    rnd = random.Random(f * 13 + 5)
    # the air cone: two wake lines curving back from his body, opening behind him
    for side in (-1, 1):
        for i in range(140):
            x = PX - 8 - i
            y = PY + side * (26 + 18 * (i / 140.0) ** 0.8)
            if (i + f * 9) % 24 < 15 and 0 <= int(y) < H and 0 <= x < W:
                g[int(y)][int(x)] = 'P' if i < 60 else 'L'
    # speed lines: each a few long dashes of its own lengths, thick at their front ends and thinning to their
    # tails, scrolling back 16 texels a frame over a 64-texel period (so 4 frames loop seamlessly)
    for n, (dy, L, t, ph) in enumerate(STREAKS):
        L = min(L, PX - 4 - 4)                           # every line ends inside the frame
        lr = random.Random(n * 31 + 7)
        dashes = []
        pos = lr.uniform(0, 20)
        while pos < 64:
            ln = lr.uniform(22, 44)
            dashes.append((pos, ln))
            pos += ln + lr.uniform(8, 18)
        for (d0, ln) in dashes:
            for rep in range(-1, 4):
                front = d0 + rep * 64 + f * 16 + ph * 64          # distance behind the body of the dash's front
                for i in range(int(ln)):
                    dist = front + i
                    if dist < 0 or dist > L:
                        continue
                    x = int(PX - 4 - dist)
                    k = 'W' if dist < L * 0.3 else ('Q' if dist < L * 0.55 else ('P' if dist < L * 0.8 else 'L'))
                    thick = max(1, int(round(t * (1.0 - 0.7 * i / ln))))
                    for j in range(thick):
                        y = int(PY + dy + j - thick // 2)
                        if 0 <= x < W and 0 <= y < H:
                            g[y][x] = k
    # a few loose flecks torn off the wake
    for _ in range(8):
        x = rnd.randint(20, 120)
        y = rnd.randint(14, 82)
        if g[y][x] == '.':
            g[y][x] = 'P'
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(4)]
