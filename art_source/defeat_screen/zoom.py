"""usage: python zoom.py in.png out.png scale [x y w h]"""
import sys
from pngio import read_png, write_png, upscale
a = sys.argv
w, h, p = read_png(a[1])
s = int(a[3])
if len(a) > 4:
    x, y, cw, ch = map(int, a[4:8])
    p = [row[x:x+cw] for row in p[y:y+ch]]
    w, h = cw, ch
W, H, o = upscale(w, h, p, s, bg='checker')
write_png(a[2], W, H, o)
print(a[2], W, H)
