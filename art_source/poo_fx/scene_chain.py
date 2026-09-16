"""Chain-reaction mock at game scale: explosion frames centred on bomb node positions."""
import sys
import fxpng
from scene_mock import ASSETS, FLOOR, frame_of, blit, new_canvas

bomb_path, explo_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
cw, ch = 1020, 330
cv = new_canvas(cw, ch)
_, _, mason = fxpng.read_png(ASSETS + 'Characters/Mason/mason.png')
_, _, player = fxpng.read_png(ASSETS + 'Characters/MainPlayer/MainC Top Down.png')
_, _, bombs = fxpng.read_png(bomb_path)
_, _, ex = fxpng.read_png(explo_path)
y = 200
xs = [80, 205, 330, 455, 580, 705, 830]
# oldest detonation on the left: F4, F3, F2, F1, F0, then armed bombs
stages = ['e4', 'e3', 'e2', 'e1', 'e0', 'b0', 'b1']
for x, st in zip(xs, stages):
    if st[0] == 'b':
        blit(cv, cw, ch, frame_of(bombs, 32, 32, int(st[1])), 32, 32, 3, x, y)
    else:
        blit(cv, cw, ch, frame_of(ex, 48, 48, int(st[1])), 48, 48, 3, x, y)
blit(cv, cw, ch, mason, 64, 64, 3, 945, 170)
blit(cv, cw, ch, player, 32, 32, 2, 400, 45)
fxpng.write_png(out, cw, ch, cv)
