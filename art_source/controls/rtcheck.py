import sys
from pngio import read_png
def norm(px):
    # treat all fully-transparent pixels as identical regardless of stored rgb
    return [[(0, 0, 0, 0) if p[3] == 0 else p for p in row] for row in px]
a, b = sys.argv[1], sys.argv[2]
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
assert (wa, ha) == (wb, hb), ('size', (wa, ha), (wb, hb))
pa, pb = norm(pa), norm(pb)
diff = [(x, y, pa[y][x], pb[y][x]) for y in range(ha) for x in range(wa) if pa[y][x] != pb[y][x]]
print('%s vs %s: %dx%d, %d differing pixels' % (a.split('/')[-1], b.split('/')[-1], wa, ha, len(diff)))
for d in diff[:10]:
    print('  ', d)
sys.exit(1 if diff else 0)
