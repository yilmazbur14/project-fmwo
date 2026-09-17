"""crop+zoom: python cz.py src dst scale [x y w h] [bg]"""
import sys
from pngio import read_png, write_png, upscale
a = sys.argv
src, dst, s = a[1], a[2], int(a[3])
w, h, px = read_png(src)
if len(a) >= 8:
    x, y, cw, ch = map(int, a[4:8])
    px = [row[x:x+cw] for row in px[y:y+ch]]
    w, h = cw, ch
bg = a[8] if len(a) > 8 else 'checker'
if bg != 'checker':
    bg = tuple(int(bg[i:i+2], 16) for i in (0, 2, 4)) + (255,)
W, H, out = upscale(w, h, px, s, bg=bg)
write_png(dst, W, H, out)
print(dst, W, H)
