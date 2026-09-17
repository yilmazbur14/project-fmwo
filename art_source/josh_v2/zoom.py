"""usage: zoom.py in.png out.png scale [x y w h] [frame_grid_w]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, checker_bg

src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, pix = read_png(src)
if len(sys.argv) >= 8:
    x0, y0, cw, ch = map(int, sys.argv[4:8])
    pix = [row[x0:x0 + cw] for row in pix[y0:y0 + ch]]
    w, h = cw, ch
pix = checker_bg(w, h, pix, cell=4, c1=(190, 196, 204, 255), c2=(160, 168, 178, 255))
W2, H2, out = scale(w, h, pix, s)
if len(sys.argv) >= 9:
    fw = int(sys.argv[8])
    for y in range(H2):
        for x in range(0, W2, fw * s):
            out[y][x] = (255, 0, 255, 255)
write_png(dst, W2, H2, out)
print(w, h, '->', W2, H2)
