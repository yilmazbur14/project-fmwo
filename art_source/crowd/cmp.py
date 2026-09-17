import sys
from pngio import read_png
wa, ha, a = read_png(sys.argv[1]); wb, hb, b = read_png(sys.argv[2])
print('sizes', (wa, ha), (wb, hb))
if (wa, ha) != (wb, hb):
    sys.exit(1)
def norm(p):  # fully transparent pixels compare equal regardless of RGB
    return (0, 0, 0, 0) if p[3] == 0 else p
diff = [(x, y, a[y][x], b[y][x]) for y in range(ha) for x in range(wa) if norm(a[y][x]) != norm(b[y][x])]
print('differing pixels', len(diff), diff[:8])
per = {}
for x, y, _, _ in diff:
    per[x // 640] = per.get(x // 640, 0) + 1
print('by frame', per)
