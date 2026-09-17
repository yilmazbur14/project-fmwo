"""Append Mason frames 15-18 (Chicken Nugget Meteor Shower cast) to frames 0-14.
Frames 0-14 are copied pixel-for-pixel from the given sheet (its first 960 px: works on the
original 15-frame sheet or the current 19-frame one), never re-rendered.
usage: python build_sheet.py <mason_sheet.png> <out mason_sheet.png>"""
import sys
from png import read_png
from zoom import write_png
import nugget_cast as NC

src, dst = sys.argv[1], sys.argv[2]
w, h, old = read_png(src)
assert h == 64 and w in (960, 1216), (w, h)
BASE = 960                                  # frames 0-14
new = [NC.render_pose(p) for _, p in NC.FRAMES]
W = BASE + 64 * len(new)
sheet = [[(0, 0, 0, 0)] * W for _ in range(h)]
for y in range(h):
    for x in range(BASE):
        sheet[y][x] = tuple(old[y][x])
    for i, g in enumerate(new):
        for x in range(64):
            sheet[y][BASE + i * 64 + x] = tuple(g[y][x])
write_png(dst, W, h, sheet)
print('wrote', dst, W, h)
