import rig, frames
from zoom import write_png
W, H = 64 * len(frames.FRAMES), 64
sheet = [[(0, 0, 0, 0)] * W for _ in range(H)]; sheet = [r[:] for r in sheet]
for i, (name, pose) in enumerate(frames.FRAMES):
    g = rig.render(pose)
    for y in range(64):
        for x in range(64):
            sheet[y][i * 64 + x] = g[y][x]
write_png('mason_sheet_build.png', W, H, sheet)
print('wrote mason_sheet_build.png', W, 'x', H)
