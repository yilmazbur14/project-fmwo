"""python verify.py generated.png exported.png -> pixel diff + alpha audit"""
import sys
from collections import Counter
from pngio import read_png
a, b = sys.argv[1], sys.argv[2]
wa, ha, pa = read_png(a)
wb, hb, pb = read_png(b)
print('sizes', (wa, ha), (wb, hb))
assert (wa, ha) == (wb, hb)
norm = lambda p: (0, 0, 0, 0) if p[3] == 0 else p
d = [(x, y, pa[y][x], pb[y][x]) for y in range(ha) for x in range(wa) if norm(pa[y][x]) != norm(pb[y][x])]
print('differing pixels:', len(d), d[:5])
alphas = Counter(p[3] for r in pb for p in r)
print('exported alpha values:', sorted(alphas))
cols = Counter('%02x%02x%02x' % p[:3] for r in pb for p in r if p[3])
print('exported colours:', len(cols))
