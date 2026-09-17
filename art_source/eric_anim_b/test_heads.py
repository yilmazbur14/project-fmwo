from base import *
import headwarp
from pngio import blank, paste, crop

outs = []
h0 = arig.layers()['head']
outs.append(crop([[p for p in r] for r in h0], 22, 0, 52, 58))
for yaw, side in ((0, 1), (45, 1), (90, 1), (135, 1), (180, 1), (45, -1), (90, -1)):
    lib.W = lib.H = 96
    c = lib.Canvas()
    headwarp.render(c, yaw, side)
    outs.append(crop(c.rgba(), 22, 0, 52, 58))
out = blank(len(outs) * 54, 58, (40, 40, 40, 255))
for i, o in enumerate(outs):
    paste(out, rgba_on(o), i * 54, 0)
zoom(out, 7, '../t_heads_7x.png')
