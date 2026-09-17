"""crop.py in.png out.png x y w h [scale]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
src, dst = sys.argv[1], sys.argv[2]
x0, y0, w, h = [int(v) for v in sys.argv[3:7]]
s = int(sys.argv[7]) if len(sys.argv) > 7 else 1
W, H, px = read_png(src)
out = []
for y in range(y0, y0 + h):
    row = []
    for x in range(x0, x0 + w):
        row.extend([px[y][x]] * s)
    for _ in range(s):
        out.append(list(row))
write_png(dst, w * s, h * s, out)
print('wrote', dst)
