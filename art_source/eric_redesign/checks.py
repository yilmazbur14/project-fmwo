import sys
from pngio import *
from collections import Counter
FL = (136, 180, 99, 255)
imgs = {}
for v in ('sword', 'hammer'):
    w, h, px = read_png(sys.argv[1].replace('VAR', v) if len(sys.argv) > 1 else f'wip_{v}.png')
    imgs[v] = px
    alphas = Counter(p[3] for r in px for p in r)
    cols = Counter(p for r in px for p in r if p[3])
    print(v, w, h, 'alpha:', dict(alphas), 'colours:', len(cols))
    # isolated pixels (no opaque 8-neighbours)
    iso = []
    for y in range(h):
        for x in range(w):
            if px[y][x][3] == 0:
                continue
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h and px[y + dy][x + dx][3]:
                        n += 1
            if n <= 1:
                iso.append((x, y))
    print('  isolated/near-isolated opaque pixels:', iso)
    # non-black pixels touching transparency (silhouette must be outlined)
    leak = []
    for y in range(h):
        for x in range(w):
            p = px[y][x]
            if p[3] and p[:3] != (0, 0, 0):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and px[yy][xx][3] == 0:
                        leak.append((x, y))
                        break
    print('  coloured pixels touching transparency (outline gaps):', len(leak), leak[:40])
    # bbox + edge contact
    xs = [x for y in range(h) for x in range(w) if px[y][x][3]]
    ys = [y for y in range(h) for x in range(w) if px[y][x][3]]
    print('  bbox', min(xs), min(ys), max(xs), max(ys))
# diff
d = [(x, y) for y in range(96) for x in range(96) if imgs['sword'][y][x] != imgs['hammer'][y][x]]
print('diff pixels', len(d))
dm = blank(96, 96, (0, 0, 0, 0))
for y in range(96):
    for x in range(96):
        p = imgs['sword'][y][x]
        dm[y][x] = ((255, 0, 255, 255) if imgs['sword'][y][x] != imgs['hammer'][y][x] else ((p[0] // 3 + 120, p[1] // 3 + 120, p[2] // 3 + 120, 255) if p[3] else FL))
z = scale(dm, 5)
write_png('diffmask_5x.png', len(z[0]), len(z), z)
