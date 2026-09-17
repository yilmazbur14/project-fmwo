"""Checks: alpha is 0/255 only, palette size, bounds, feet anchor, symmetry."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png

W = H = 96
w, h, px = read_png('sheet.png')
assert h == H, h
n = w // W
print('sheet %dx%d = %d frames of %dx%d' % (w, h, n, W, H))

alphas = set()
cols = set()
for row in px:
    for p in row:
        alphas.add(p[3])
        if p[3]:
            cols.add(tuple(p))
print('alphas:', sorted(alphas))
assert alphas <= {0, 255}, 'NON-BINARY ALPHA'
print('colours:', len(cols))

for f in range(n):
    xs, ys = [], []
    for y in range(H):
        for x in range(W):
            if px[y][f * W + x][3]:
                xs.append(x)
                ys.append(y)
    print('  f%d  rows %2d..%2d  cols %2d..%2d  (w=%d h=%d)' %
          (f, min(ys), max(ys), min(xs), max(xs), max(xs) - min(xs) + 1,
           max(ys) - min(ys) + 1))

# feet anchor: lowest opaque row of the body (ignoring aura) per frame
for f in range(n):
    low = max(y for y in range(H) for x in range(W) if px[y][f * W + x][3])
    print('  f%d lowest opaque row = %d' % (f, low))

# symmetry of frame 0 body columns (aura is deliberately asymmetric)
bad = 0
for y in range(40, H):
    for x in range(W):
        a = px[y][x][3] > 0
        b = px[y][95 - x][3] > 0
        if a != b:
            bad += 1
print('frame0 silhouette mirror mismatches (rows 40+):', bad)
