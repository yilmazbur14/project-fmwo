import sys
from pngio import *
src, dst, s, f0, f1 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
fw = int(sys.argv[6]) if len(sys.argv) > 6 else 64
w, h, px = read_png(src)
cw, ch, c = crop(w, h, px, f0*fw, 0, (f1-f0)*fw, h)
c = checker_bg(cw, ch, c, cell=4)
# separators
for y in range(ch):
    for k in range(1, f1-f0):
        c[y][k*fw] = (255, 0, 255, 255)
w2, h2, p2 = scale(cw, ch, c, s)
write_png(dst, w2, h2, p2)
print(dst, w2, h2)
