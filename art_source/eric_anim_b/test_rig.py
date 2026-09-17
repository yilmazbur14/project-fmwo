import rig, lib, sword128
from pngio import write_png, read_png
f = rig.Frame128()
for k in rig.ORDER:
    f.put(k)
rig.use128()
sword128.arm(f.cv); sword128.blade(f.cv); sword128.hilt(f.cv); sword128.fist(f.cv)
px = f.rgba()
_, _, ap = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_sword.png')
diff = [(x, y) for y in range(128) for x in range(128) if tuple(px[y][x]) != tuple(ap[y][x])]
print('diff pixels vs approved:', len(diff), diff[:10])
