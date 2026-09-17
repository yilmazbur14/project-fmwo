"""view3x.py out.png -> frames at true 3x on the mat, with idle and hit for comparison"""
import sys
import rig, frames, nugget_cast as NC
from zoom import write_png
S = 3
seq = [('idle', rig.render(frames.FRAMES[0][1]))] + [(n, NC.render_pose(p)) for n, p in NC.FRAMES] + [('hit', rig.render(frames.FRAMES[12][1]))]
bg = (136, 180, 99, 255)
gap = 24
W = len(seq) * (64 * S + gap) + gap
H = 64 * S + 2 * gap
img = [[bg] * W for _ in range(H)]
for k, (n, g) in enumerate(seq):
    ox = gap + k * (64 * S + gap)
    for y in range(64 * S):
        for x in range(64 * S):
            p = g[y // S][x // S]
            if p[3]:
                img[gap + y][ox + x] = p
write_png(sys.argv[1], W, H, img)
print('wrote', sys.argv[1], W, H)
