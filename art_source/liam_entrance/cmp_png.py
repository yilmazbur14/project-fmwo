"""cmp_png.py A B : pixel-exact comparison of two PNGs (alpha-0 pixels compare equal regardless of RGB)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png

a, b = sys.argv[1], sys.argv[2]
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
if (wa, ha) != (wb, hb):
    print('SIZE MISMATCH', (wa, ha), (wb, hb))
    sys.exit(1)
diff = 0
first = None
for y in range(ha):
    for x in range(wa):
        p, q = tuple(pa[y][x]), tuple(pb[y][x])
        if p[3] == 0 and q[3] == 0:
            continue
        if p != q:
            diff += 1
            first = first or (x, y, p, q)
print('%s vs %s: %dx%d, %d differing pixels%s' % (os.path.basename(a), os.path.basename(b), wa, ha, diff,
                                                  '' if not first else ' first=%s' % (first,)))
sys.exit(1 if diff else 0)
