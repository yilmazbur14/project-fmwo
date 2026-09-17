"""Whole-attack preview GIF (approval aid only): Eric's new frames in order, a stand-in planted sword
(cut from his own downed frames) and a rough leap arc + shadow the code would supply."""
import math, os
from build import *
from gifio import write_gif

grids = build_grids()
F = {n: g for n, g in zip(ORDER, grids)}
IDLE = to_chars(ref_frames()[21])
W, H, S = 270, 150, 2
BGc = (120, 160, 120, 255)
SHADOW = (80, 110, 80, 255)
ex0, ex1, ey = 138, 4, 14
sword_tl = (ex1 + 34, ey + 73)


def canvas():
    return [[BGc] * W for _ in range(H)]


def blit(img, g, ox, oy):
    for y in range(FS):
        for x in range(FS):
            c = g[y][x]
            if c in PAL:
                X, Y = ox + x, oy + y
                if 0 <= X < W and 0 <= Y < H:
                    img[Y][X] = PAL[c] + (255,)


def sword(img):
    for j, r in enumerate(SW_PLANT.rows):
        for i, c in enumerate(r):
            if c in PAL:
                img[sword_tl[1] + j][sword_tl[0] + i] = PAL[c] + (255,)


def shadow(img, cx, cy, rx=13, ry=3.5):
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if 0 <= x < W and 0 <= y < H and ((x + .5 - cx) / rx) ** 2 + ((y + .5 - cy) / ry) ** 2 <= 1:
                img[y][x] = SHADOW


seq = []  # (grid, ms, ex, ey_offset, sword_visible, shadow_t)
seq.append((IDLE, 500, ex0, 0, False, None))
seq += [(F['throw_windup_0'], 120, ex0, 0, False, None), (F['throw_windup_1'], 320, ex0, 0, False, None),
        (F['throw_release_0'], 70, ex0, 0, False, None), (F['throw_release_1'], 220, ex0, 0, False, None)]
seq += [(F['empty_wait_0'], 260, ex0, 0, False, None), (F['empty_wait_1'], 260, ex0, 0, True, None),
        (F['empty_wait_0'], 260, ex0, 0, True, None), (F['empty_wait_1'], 260, ex0, 0, True, None)]
seq += [(F['leap_0'], 200, ex0, 0, True, None), (F['leap_1'], 80, ex0, 0, True, 0.0)]
for t, name in [(0.18, 'leap_2'), (0.36, 'leap_2'), (0.54, 'leap_2'), (0.72, 'leap_3'), (0.88, 'leap_3')]:
    seq.append((F[name], 60, int(round(ex0 + (ex1 - ex0) * t)), -int(round(46 * math.sin(math.pi * t))), True, t))
seq += [(F['slam_0'], 90, ex1, 0, False, None), (F['slam_1'], 70, ex1, 0, False, None),
        (F['slam_2'], 380, ex1, 0, False, None), (F['recover_0'], 180, ex1, 0, False, None),
        (F['recover_1'], 160, ex1, 0, False, None), (IDLE, 600, ex1, 0, False, None)]

frames, delays = [], []
for g, ms, ex, dy, sw, sh in seq:
    img = canvas()
    if sw:
        sword(img)
    if sh is not None:
        shadow(img, ex + 61, ey + 122)
    blit(img, g, ex, ey + dy)
    frames.append(scale(img, S))
    delays.append(max(2, round(ms / 10)))
print(write_gif(os.path.join(OUT, 'gif_full_sequence_preview.gif'), frames, delays), 'bytes')
