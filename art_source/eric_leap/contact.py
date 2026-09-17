import sys
from pngio import *
BG = (120, 160, 120, 255)
w, h, px = read_png(sys.argv[1])
s = int(sys.argv[2]); per = int(sys.argv[3]); y0, y1 = int(sys.argv[4]), int(sys.argv[5])
out = sys.argv[6]
n = w // 128
rows = (n + per - 1) // per
fh = (y1 - y0) * s
W = per * (128 * s + 4)
H = rows * (fh + 4)
img = [[(40, 40, 40, 255)] * W for _ in range(H)]
for i in range(n):
    r, c = divmod(i, per)
    ox, oy = c * (128 * s + 4), r * (fh + 4)
    for y in range(y0, y1):
        for x in range(128):
            p = px[y][x + 128 * i]
            col = p if p[3] == 255 else BG
            if x % 16 == 0 and y % 16 == 0 and p[3] == 0:
                col = (100, 140, 100, 255)
            for yy in range(s):
                for xx in range(s):
                    img[oy + (y - y0) * s + yy][ox + x * s + xx] = col
write_png(out, W, H, img)
