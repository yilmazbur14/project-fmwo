import sys
from lib import *
from pngio import read_png
src, x0, y0, w, h = sys.argv[1], *map(int, sys.argv[2:6])
_, _, px = read_png(src)
rev = {v: k for k, v in PALC.items()}
print('     ' + ''.join(str((x0 + i) // 10 % 10) for i in range(w)))
print('     ' + ''.join(str((x0 + i) % 10) for i in range(w)))
for y in range(y0, y0 + h):
    print('%3d  ' % y + ''.join('.' if px[y][x][3] == 0 else rev.get(tuple(px[y][x]), '?') for x in range(x0, x0 + w)))
