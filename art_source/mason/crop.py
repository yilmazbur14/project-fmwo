"""python crop.py out.png scale x0 y0 x1 y1 frame [frame...] - side-by-side crops"""
import sys
import rig, frames
from zoom import write_png
out = sys.argv[1]; f = int(sys.argv[2]); x0, y0, x1, y1 = map(int, sys.argv[3:7])
ids = [int(a) for a in sys.argv[7:]]
w, h = (x1 - x0) * f, (y1 - y0) * f; gap = 8
W = len(ids) * w + (len(ids) - 1) * gap
img = [[(70, 70, 80, 255)] * W for _ in range(h)]; img = [r[:] for r in img]
for k, i in enumerate(ids):
    g = rig.render(frames.FRAMES[i][1]); ox = k * (w + gap)
    for Y in range(h):
        for X in range(w):
            p = g[y0 + Y // f][x0 + X // f]
            img[Y][ox + X] = p if p[3] else ((232,) * 3 + (255,) if ((X // f) + (Y // f)) % 2 == 0 else (208,) * 3 + (255,))
write_png(out, W, h, img); print('wrote', out, W, h)
