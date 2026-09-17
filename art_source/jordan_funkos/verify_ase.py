"""Compare an Aseprite-exported horizontal strip with the delivered PNG sheet (pixel exact, alpha 0/255)."""
import sys
from lib import *
name = sys.argv[1]
w1, h1, a = read_png(WIP + 'verify_%s.png' % name)
w2, h2, b = read_png(OUT_ASSETS + '%s.png' % name)
print(name, 'aseprite export', (w1, h1), 'png', (w2, h2))
assert (w1, h1) == (w2, h2), 'size mismatch'
diff = 0
for y in range(h1):
    for x in range(w1):
        p, q = a[y][x], b[y][x]
        if p[3] == 0 and q[3] == 0:
            continue
        if p != q:
            diff += 1
alphas = set(p[3] for r in a for p in r)
print('pixel diffs:', diff, 'alphas in export:', sorted(alphas))
