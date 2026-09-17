import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'a_prop'))
sys.path.insert(1, HERE)
import rig2 as R
from pngio import read_png, write_png, scale

fr = R.base_idle()
px = fr.rgba()
_, _, ap = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_v2.png')
d = sum(1 for y in range(192) for x in range(256) if tuple(px[y][x]) != tuple(ap[y][x]))
print('rig2.base_idle vs eric_redesign_v2.png diff:', d)
L = R.layers()
for n in R.ORDER:
    img = L[n]
    xs = [x for y in range(96) for x in range(96) if img[y][x][3]]
    ys = [y for y in range(96) for x in range(96) if img[y][x][3]]
    print('%-10s x %2d..%2d y %2d..%2d' % (n, min(xs), max(xs), min(ys), max(ys)))
