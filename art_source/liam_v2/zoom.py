import sys
from pngio import *
src, dst, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
w, h, px = read_png(src)
print(src, w, h)
px = checker_bg(w, h, px, cell=4)
w2, h2, px2 = scale(w, h, px, s)
write_png(dst, w2, h2, px2)
