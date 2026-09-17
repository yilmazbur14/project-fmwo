"""Checks: silhouette edge pixels must be K; flag isolated opaque pixels; count colours."""
import os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import load_rows
g = load_rows(os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'wip.txt'))
H, W = len(g), len(g[0])
bad_edge, isolated = [], []
for y in range(H):
    for x in range(W):
        c = g[y][x]
        if c == '.':
            continue
        nb = []
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + dx, y + dy
            nb.append(g[Y][X] if 0 <= X < W and 0 <= Y < H else '.')
        if '.' in nb and c != 'K':
            bad_edge.append((x, y, c))
        if all(n == '.' for n in nb):
            isolated.append((x, y, c))
print('non-K silhouette edge pixels:', len(bad_edge))
for b in bad_edge[:40]:
    print('  ', b)
print('isolated pixels:', isolated)
cnt = collections.Counter(c for r in g for c in r if c != '.')
print('colours used:', len(cnt), dict(cnt.most_common()))
