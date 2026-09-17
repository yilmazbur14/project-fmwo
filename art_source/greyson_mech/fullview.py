import sys, rig, sheet
from pngio import *
idxs = [int(a) for a in sys.argv[1].split(',')]
s = int(sys.argv[2]) if len(sys.argv) > 2 else 8
FR = sheet.frames()
cv = blank(len(idxs) * (96 * s + 8) + 8, 96 * s + 16, (70, 90, 76, 255))
for n, i in enumerate(idxs):
    paste(cv, scale(rig.render(FR[i]), s, sheet.BG), 8 + n * (96 * s + 8), 8)
write_png('full_' + '_'.join(map(str, idxs)) + '.png', len(cv[0]), len(cv), cv)
