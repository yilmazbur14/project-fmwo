"""view_final.py out.png scale [idx,...]  (-1 = idle frame 0 from the shipped sheet)"""
import sys
import rig, frames, nugget_cast as NC
from zoom import write_png
out, s = sys.argv[1], int(sys.argv[2])
idx = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else [-1, 0, 1, 2, 3]
grids = []
for i in idx:
    grids.append(rig.render(frames.FRAMES[0][1]) if i < 0 else NC.render_pose(NC.FRAMES[i][1]))
bg = (136, 180, 99, 255)
gap = 8
W = len(grids) * (64 * s + gap) - gap
img = [[(40, 40, 40, 255)] * W for _ in range(64 * s)]
for k, g in enumerate(grids):
    ox = k * (64 * s + gap)
    for y in range(64 * s):
        row = g[y // s]
        for x in range(64 * s):
            p = row[x // s]
            img[y][ox + x] = p if p[3] else bg
write_png(out, W, 64 * s, img)
print('wrote', out)
