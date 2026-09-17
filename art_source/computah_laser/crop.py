import sys
from pngio import *
src, x0, y0, x1, y1, s, dst = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
w, h, px = read_png(src)
rows = [px[y][x0:x1] for y in range(y0, y1)]
W, H, up = upscale(x1 - x0, y1 - y0, rows, s)
write_png(dst, W, H, up)
