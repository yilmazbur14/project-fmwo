"""pixel-exact compare of a deliverable PNG with its Aseprite round-trip export.
python rtcheck.py a.png b.png   (transparent pixels compare equal regardless of rgb)"""
import sys
from pngio import read_png
a, b = sys.argv[1], sys.argv[2]
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
if (wa, ha) != (wb, hb):
    print('SIZE MISMATCH', (wa, ha), (wb, hb)); sys.exit(1)
diff = 0
first = None
for y in range(ha):
    for x in range(wa):
        p, q = pa[y][x], pb[y][x]
        if p[3] == 0 and q[3] == 0:
            continue
        if p != q:
            diff += 1
            if first is None:
                first = (x, y, p, q)
print('%s vs %s: %dx%d, %d differing pixels%s' % (a.split('/')[-1], b.split('/')[-1], wa, ha, diff, '' if not first else ' first=%s' % (first,)))
