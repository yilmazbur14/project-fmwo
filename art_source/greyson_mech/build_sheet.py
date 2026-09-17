import rig, sheet, pickle
from pngio import *
FR = sheet.frames()
assert len(FR) == 23, len(FR)
imgs = [rig.render(P) for P in FR]
pickle.dump(imgs, open('frames.pkl', 'wb'))
# raw sheet
sheetpx = [[(0, 0, 0, 0)] * (96 * 23) for _ in range(96)]
for i, im in enumerate(imgs):
    for y in range(96):
        for x in range(96):
            p = im[y][x]
            sheetpx[y][x + 96 * i] = p if p[3] else (0, 0, 0, 0)
write_png('greyson_mech_sheet.png', 96 * 23, 96, sheetpx)
# 3x review strip in two rows with labels-free gutters
S = 3
rows = [list(range(0, 12)), list(range(12, 23))]
Wt = 12 * (96 * S + 6) + 6
cv = blank(Wt, 2 * (96 * S + 6) + 6, (70, 90, 76, 255))
for r, idxs in enumerate(rows):
    for n, i in enumerate(idxs):
        paste(cv, scale(imgs[i], S, sheet.BG), 6 + n * (96 * S + 6), 6 + r * (96 * S + 6))
write_png('greyson_mech_sheet_3x.png', len(cv[0]), len(cv), cv)
print('ok')
