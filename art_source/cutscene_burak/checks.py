"""Sanity checks on the strip: bottom row contact, edge clipping, alpha, size."""
import sys
from pngio import read_png
path = sys.argv[1] if len(sys.argv) > 1 else 'out/burak_cutscene_1x.png'
w, h, px = read_png(path)
n = w // 64
print('size', w, h, 'frames', n, 'alpha values', sorted({p[3] for r in px for p in r}))
for i in range(n):
    rows = [y for y in range(64) if any(px[y][i * 64 + x][3] for x in range(64))]
    cols = [x for x in range(64) if any(px[y][i * 64 + x][3] for y in range(64))]
    bottom = [x for x in range(64) if px[63][i * 64 + x][3]]
    print('f%02d top=%2d bottom=%2d height=%2d x=%2d..%2d  row63 px=%2d  edge=%s' % (
        i, rows[0], rows[-1], rows[-1] - rows[0] + 1, cols[0], cols[-1], len(bottom),
        'CLIP' if (cols[0] == 0 or cols[-1] == 63 or rows[0] == 0) else 'ok'))
