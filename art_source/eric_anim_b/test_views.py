from base import *
import views
import sys


def compose(yaw, side=1):
    V, L = views.build(yaw, side)
    fr = arig.Frame()
    for name in views.order(yaw, side):
        img = [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in L[name]]
        fr.put(img)
    return fr.rgba()


fr = arig.Frame()
body(fr, skip=('armL_back', 'armR_back', 'armR_front'))
imgs = [fr.rgba()]
for yaw, side in ((45, -1), (90, -1), (135, -1), (180, 1), (135, 1), (90, 1), (45, 1), (0, 1)):
    imgs.append(compose(yaw, side))
strip(imgs, 3, '../t_turnaround_3x.png')
from pngio import blank, paste
out = blank(4 * 100, 100, (40, 40, 40, 255))
for k, i in enumerate([7, 6, 5, 4]):
    paste(out, rgba_on(crop(imgs[i], 14, 28, 100, 100)), k * 100, 0)
zoom(out, 5, '../t_turn_right_5x.png')
