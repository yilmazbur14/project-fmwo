"""python preview.py <first> <last> [scale] [outname]  - render a frame range as a strip"""
import sys, importlib
import rig, frames
from build import strip, zoom_grid

a = int(sys.argv[1]); b = int(sys.argv[2])
f = int(sys.argv[3]) if len(sys.argv) > 3 else 6
name = sys.argv[4] if len(sys.argv) > 4 else 'strip_%d_%d.png' % (a, b)
grids = []
for i in range(a, b + 1):
    label, pose = frames.FRAMES[i]
    g = rig.render(pose)
    grids.append(g)
    ys = [y for y in range(64) for x in range(64) if g[y][x][3]]
    xs = [x for y in range(64) for x in range(64) if g[y][x][3]]
    print('f%02d %-8s bbox x %2d-%2d  y %2d-%2d' % (i, label, min(xs), max(xs), min(ys), max(ys)))
strip(grids, f, name)
print('wrote', name)
