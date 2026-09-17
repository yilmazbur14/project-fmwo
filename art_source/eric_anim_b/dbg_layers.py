from base import *
import views
from pngio import blank, paste
names = ['torso', 'paul_r', 'paul_l', 'tassets', 'flap', 'buckle', 'belt']
rows = []
for yaw in (45, 90):
    V, L = views.build(yaw, 1)
    for n in names:
        rows.append([[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in L[n]])
out = blank(7 * 98, 2 * 98, (40, 40, 40, 255))
for i, im in enumerate(rows):
    paste(out, rgba_on(im), (i % 7) * 98, (i // 7) * 98)
zoom(out, 3, '../dbg_layers_3x.png')
