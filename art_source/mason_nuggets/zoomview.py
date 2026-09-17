"""zoom.py in.png out.png scale [bg r,g,b] [fw] -> nearest-neighbour upscale; optional frame separators"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
bg = tuple(int(v) for v in sys.argv[4].split(',')) + (255,) if len(sys.argv) > 4 else (255, 0, 255, 255)
fw = int(sys.argv[5]) if len(sys.argv) > 5 else 0
w, h, px = read_png(src)
out = []
for y in range(h):
    row = []
    for x in range(w):
        p = px[y][x]
        if p[3] == 0:
            p = bg
        elif p[3] < 255:
            k = p[3] / 255
            p = tuple(int(p[i] * k + bg[i] * (1 - k)) for i in range(3)) + (255,)
        row.extend([p] * s)
    for _ in range(s):
        out.append(list(row))
if fw:
    for y in range(h * s):
        for f in range(1, w // fw):
            out[y][f * fw * s] = (255, 255, 255, 255)
write_png(dst, w * s, h * s, out)
print('wrote', dst, w * s, h * s)
