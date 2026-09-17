from base2 import *
import views2

imgs = []
fr = R.Frame()
R.compose(fr, skip=('armR_front',))
imgs.append(fr.rgba())
for yaw, side in ((45, -1), (90, -1), (135, -1), (180, 1), (135, 1), (90, 1), (45, 1)):
    V, L = views2.build(yaw, side)
    fr = R.Frame()
    for name in views2.order(yaw, side):
        fr.put96(layer_rgba(L[name]))
    imgs.append(fr.rgba())
crops = [crop(im, 72, 104, 112, 88) for im in imgs]
out = blank(len(crops) * 116, 88, (40, 40, 40, 255))
for i, c in enumerate(crops):
    paste(out, rgba_on(c), i * 116, 0)
z = scale(out, 4)
write_png('../v2_turnaround_4x.png', len(z[0]), len(z), z)
