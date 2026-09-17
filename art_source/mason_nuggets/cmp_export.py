"""cmp_export.py exported.png reference.png fw -> per-frame pixel diff (transparent = any alpha-0 pixel)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png
a, b, fw = sys.argv[1], sys.argv[2], int(sys.argv[3])
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
print('exported %dx%d  reference %dx%d' % (wa, ha, wb, hb))
norm = lambda p: (0, 0, 0, 0) if p[3] == 0 else tuple(p)
total = 0
for f in range(max(wa, wb) // fw):
    d = 0
    for y in range(max(ha, hb)):
        for x in range(fw):
            X = f * fw + x
            p = norm(pa[y][X]) if (X < wa and y < ha) else None
            q = norm(pb[y][X]) if (X < wb and y < hb) else None
            if p != q:
                d += 1
    total += d
    print('  frame', f, 'diff px', d)
print('IDENTICAL' if total == 0 and (wa, ha) == (wb, hb) else 'DIFFERENT (%d px)' % total)
