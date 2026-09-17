"""Sanity checks before export: alpha, palette, feet on the bottom row, frame margins."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from jlib import PAL, W, H
from pngio import read_png

NAMES = {v[:3]: k for k, v in PAL.items()}


def audit(path):
    w, h, px = read_png(path)
    alphas = sorted({p[3] for row in px for p in row})
    cols = Counter('#%02X%02X%02X' % p[:3] for row in px for p in row if p[3])
    solid = [(x, y) for y in range(h) for x in range(w) if px[y][x][3]]
    xs = [p[0] for p in solid]
    ys = [p[1] for p in solid]
    stray = [k for k in cols if tuple(int(k[i:i + 2], 16) for i in (1, 3, 5)) not in NAMES]
    print('--', os.path.basename(path), '%dx%d' % (w, h))
    print('   alphas', alphas, '(must be [0, 255])' if alphas != [0, 255] else 'OK')
    print('   colours', len(cols), '| x %d..%d  y %d..%d' % (min(xs), max(xs), min(ys), max(ys)))
    if stray:
        print('   *** STRAY COLOURS', stray)
    return cols


if __name__ == '__main__':
    OUT = sys.argv[1]
    total = Counter()
    for f in sys.argv[2:]:
        total.update(audit(os.path.join(OUT, f)))
    print('\ncombined palette (%d colours):' % len(total))
    for k, v in total.most_common():
        print('   %s %6d  %s' % (k, v, NAMES.get(tuple(int(k[i:i + 2], 16) for i in (1, 3, 5)), '?')))
