import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'a_prop'))
sys.path.insert(1, HERE)
import rig2 as R
import lib
import head2
from pngio import write_png, scale, blank, paste, crop

FL = (136, 180, 99, 255)
outs = [crop(R.layers()['head'], 28, 16, 40, 48)]
for yaw, side in ((45, 1), (90, 1), (135, 1), (180, 1), (45, -1), (90, -1)):
    lib.W = lib.H = 96
    c = lib.Canvas()
    head2.render(c, yaw, side)
    outs.append(crop(c.rgba(), 28, 16, 40, 48))
out = blank(len(outs) * 42, 48, (40, 40, 40, 255))
for i, o in enumerate(outs):
    paste(out, [[p if p[3] else FL for p in r] for r in o], i * 42, 0)
z = scale(out, 10)
write_png('../v2_heads_10x.png', len(z[0]), len(z), z)
