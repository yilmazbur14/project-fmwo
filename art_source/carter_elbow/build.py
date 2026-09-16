"""build.py -> reads frame0..4.txt, writes carter_elbowdrop_wip.png (320x64) + review views"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from puppet import *
from pngio import read_png, write_png

gs = []
for i in range(5):
    g = text_to_grid(open(os.path.join(HERE, 'frame%d.txt' % i)).read())
    assert len(g) == 64 and all(len(r) == 64 for r in g), ('bad size', i, len(g), [len(r) for r in g if len(r) != 64][:3])
    bad = set(ch for r in g for ch in r if ch not in PAL)
    assert not bad, ('unknown chars', i, bad)
    # edge check
    for y in range(64):
        for x in range(64):
            if g[y][x] != '.' and (x in (0, 63) or y in (0, 63)):
                print('WARN frame', i, 'pixel on frame edge', x, y)
    gs.append(g)
out = os.path.join(HERE, 'carter_elbowdrop_wip.png')
write_strip(out, gs)
print('wrote', out)
