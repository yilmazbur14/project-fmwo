"""python zoom.py in.png out.png scale [x0 y0 w h] ; transparent -> checker grey"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, px = read_png(src)
if len(sys.argv) > 4:
    x0, y0, cw, ch = map(int, sys.argv[4:8])
    px = [r[x0:x0+cw] for r in px[y0:y0+ch]]; w, h = cw, ch
out = []
for y in range(h):
    row = []
    for x in range(w):
        p = px[y][x]
        if p[3] == 0:
            c = (150,160,170,255) if ((x//4 + y//4) % 2) else (125,135,145,255)
            p = c
        row.extend([tuple(p[:3])+(255,)] * s)
    for _ in range(s): out.append(row)
write_png(dst, w*s, h*s, out)
print(w, h)
