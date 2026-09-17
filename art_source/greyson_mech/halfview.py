import sys, rig, sheet
from pngio import *
idxs = [int(a) for a in sys.argv[1].split(',')]
x0, x1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 50)
s = 8
FR = sheet.frames()
w = x1 - x0
cv = blank(len(idxs) * (w * s + 8) + 8, 96 * s + 16, (70, 90, 76, 255))
for n, i in enumerate(idxs):
    im = rig.render(FR[i])
    paste(cv, scale(crop(im, x0, 0, w, 96), s, sheet.BG), 8 + n * (w * s + 8), 8)
write_png('half_' + '_'.join(map(str, idxs)) + '.png', len(cv[0]), len(cv), cv)
