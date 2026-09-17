"""Composite the crowd strip at 3x into an arena render, behind the rope/posts/UI.
usage: python mockup.py strip.png render.png frame out.png"""
import sys
from pngio import read_png, write_png
strip_p, render_p, fi, out_p = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
sw, sh, strip = read_png(strip_p)
rw, rh, rend = read_png(render_p)
OLD_TAN = (217, 160, 102, 255)
BLACK = (0, 0, 0, 255)
SIDE_GREEN = (113, 152, 79, 255)   # ColorRect2/3: drawn BEFORE the crowd sprite
H = 125
def near(x, y, pred, r):
    for yy in range(max(0, y - r), min(rh, y + r + 1)):
        for xx in range(max(0, x - r), min(rw, x + r + 1)):
            if pred(rend[yy][xx]):
                return True
    return False
white = lambda p: p[0] > 240 and p[1] > 240 and p[2] > 240
redbar = lambda p: p[0] > 180 and p[1] < 60 and p[2] < 60
brass = lambda p: p in ((138, 111, 48, 255), (209, 175, 97, 255))
out = [list(r) for r in rend]
for y in range(H):
    for x in range(rw):
        p = rend[y][x]
        fg = p not in (OLD_TAN, BLACK, SIDE_GREEN)
        if p == BLACK:
            if 109 <= x <= 1809 and 93 <= y <= 114:
                fg = True                                   # rope outline
            elif 700 <= x <= 1220 and 30 <= y <= 100 and (near(x, y, white, 2) or near(x, y, redbar, 1)):
                fg = True                                   # boss name / bar outline
            elif (80 <= x <= 140 or 1770 <= x <= 1840) and 65 <= y <= 125 and near(x, y, brass, 2):
                fg = True                                   # post outline
        if fg:
            continue
        c = strip[y // 3][fi * 640 + x // 3] if y < 120 else (0, 0, 0, 0)
        if c[3]:
            out[y][x] = c
        else:
            out[y][x] = SIDE_GREEN if p == SIDE_GREEN else BLACK
write_png(out_p, rw, rh, out)
print('wrote', out_p)
