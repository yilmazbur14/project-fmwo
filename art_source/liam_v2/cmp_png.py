import sys
from pngio import read_png
def norm(p):
    return p if p[3] != 0 else (0, 0, 0, 0)
a = read_png(sys.argv[1]); b = read_png(sys.argv[2])
print('sizes', a[:2], b[:2])
if a[:2] != b[:2]:
    print('SIZE MISMATCH'); sys.exit(1)
w, h = a[:2]
diff = [(x, y, a[2][y][x], b[2][y][x]) for y in range(h) for x in range(w) if norm(a[2][y][x]) != norm(b[2][y][x])]
print('differing pixels:', len(diff))
for d in diff[:10]:
    print(d)
al = sorted(set(p[3] for r in b[2] for p in r))
print('alpha values in second:', al)
