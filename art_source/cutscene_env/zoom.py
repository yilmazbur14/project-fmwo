import sys
from pngio import read_png, write_png, upscale
# usage: zoom.py in out scale [x y w h]
src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, pix = read_png(src)
if len(sys.argv) > 4:
    x0, y0, cw, ch = map(int, sys.argv[4:8])
    pix = [row[x0:x0+cw] for row in pix[y0:y0+ch]]
    w, h = cw, ch
W, H, out = upscale(w, h, pix, s, bg='checker')
write_png(dst, W, H, out)
print(W, H)
