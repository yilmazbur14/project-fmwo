"""python grid.py strip.png out.png scale cols [y0 h] : lay out 64px frames of a strip in a grid with a ground line"""
import sys
from pngio import read_png, write_png
src, dst, s, cols = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
y0 = int(sys.argv[5]) if len(sys.argv) > 5 else 0
hh = int(sys.argv[6]) if len(sys.argv) > 6 else 64
w, h, px = read_png(src)
n = w // 64
rows_ = (n + cols - 1) // cols
G = 2
TW, TH = cols * (64 * s + G), rows_ * (hh * s + G)
img = [[(30, 30, 36, 255)] * TW for _ in range(TH)]
for i in range(n):
    ox, oy = (i % cols) * (64 * s + G), (i // cols) * (hh * s + G)
    for y in range(hh):
        for x in range(64):
            p = px[y0 + y][i * 64 + x]
            if p[3] == 0:
                p = (150, 158, 170, 255) if ((x // 4 + (y0 + y) // 4) % 2) else (132, 140, 152, 255)
                if (y0 + y) == 63:
                    p = (200, 120, 120, 255)
                if x in (30,):
                    p = tuple(min(255, c + 25) for c in p[:3]) + (255,)
            for yy in range(s):
                row = img[oy + y * s + yy]
                for xx in range(s):
                    row[ox + x * s + xx] = p
write_png(dst, TW, TH, img)
print(TW, TH)
