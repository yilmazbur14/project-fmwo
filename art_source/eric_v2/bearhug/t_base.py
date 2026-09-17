"""check: the rig bh2 resolves still reproduces the approved v2 idle exactly"""
import bh2
from bh2 import R
from pngio import read_png
px = R.base_idle().rgba()
w, h, ap = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_v2.png')
d = sum(1 for y in range(h) for x in range(w) if (px[y][x] if px[y][x][3] else (0, 0, 0, 0)) != (ap[y][x] if ap[y][x][3] else (0, 0, 0, 0)))
print('rig:', bh2.RIG_DIR, '| base_idle vs eric_redesign_v2.png diff px:', d)
