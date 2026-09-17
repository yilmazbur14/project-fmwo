import sys
from pngio import read_png, write_png, upscale
src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
bg = sys.argv[4] if len(sys.argv) > 4 else 'checker'
if bg != 'checker':
    bg = tuple(int(bg[i:i+2], 16) for i in (0, 2, 4)) + (255,)
w, h, px = read_png(src)
W, H, out = upscale(w, h, px, s, bg=bg)
write_png(dst, W, H, out)
print("zoomed", src, w, h, "->", dst, W, H)
