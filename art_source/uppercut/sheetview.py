"""sheetview.py out.png scale bg item1.png item2.png ... -> row of zoomed images with gaps"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
out, s = sys.argv[1], int(sys.argv[2])
bg = tuple(int(v) for v in sys.argv[3].split(',')) + (255,)
items = [read_png(p) for p in sys.argv[4:]]
gap = 16
W = sum(w * s for w, h, px in items) + gap * (len(items) + 1)
H = max(h * s for w, h, px in items) + gap * 2
canvas = [[(40, 40, 48, 255)] * W for _ in range(H)]
x0 = gap
for w, h, px in items:
    for Y in range(h * s):
        for X in range(w * s):
            p = px[Y // s][X // s]
            if p[3] == 0:
                p = bg
            canvas[gap + Y][x0 + X] = p
    x0 += w * s + gap
write_png(out, W, H, canvas)
print('wrote', out, W, H)
