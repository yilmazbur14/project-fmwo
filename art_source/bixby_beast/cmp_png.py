"""Pixel-compare two PNGs (treating all alpha-0 pixels as equal)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png

a, b = sys.argv[1], sys.argv[2]
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
if (wa, ha) != (wb, hb):
    print('SIZE MISMATCH', (wa, ha), (wb, hb))
    sys.exit(1)
diff = 0
first = []
for y in range(ha):
    for x in range(wa):
        p, q = tuple(pa[y][x]), tuple(pb[y][x])
        if p[3] == 0 and q[3] == 0:
            continue
        if p != q:
            diff += 1
            if len(first) < 5:
                first.append((x, y, p, q))
print(os.path.basename(a), 'vs', os.path.basename(b), '->', 'IDENTICAL' if diff == 0 else '%d differing pixels %s' % (diff, first))
