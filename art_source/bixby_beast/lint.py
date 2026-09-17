"""Lint a PNG: alpha values, colours not in palette, isolated opaque pixels."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png
from pal import PALC

path = sys.argv[1]
w, h, px = read_png(path)
pal = set(PALC.values())
alphas = set()
off = {}
iso = []
for y in range(h):
    for x in range(w):
        p = tuple(px[y][x])
        alphas.add(p[3])
        if p[3] == 0:
            continue
        if p not in pal:
            off[p] = off.get(p, 0) + 1
        n = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if (dx or dy) and 0 <= x + dx < w and 0 <= y + dy < h and px[y + dy][x + dx][3]:
                    n += 1
        if n == 0:
            iso.append((x, y, '#%02x%02x%02x' % p[:3]))
cols = {tuple(px[y][x]) for y in range(h) for x in range(w) if px[y][x][3]}
print(os.path.basename(path), w, 'x', h, 'colours:', len(cols), 'alphas:', sorted(alphas))
print('  off-palette:', off if off else 'none')
print('  isolated pixels:', len(iso), iso[:30])
