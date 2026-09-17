import sys
from png import read_png
a_path, b_path = sys.argv[1], sys.argv[2]
wa, ha, a = read_png(a_path); wb, hb, b = read_png(b_path)
print('%s: %dx%d   %s: %dx%d' % (a_path.split('/')[-1], wa, ha, b_path.split('/')[-1], wb, hb))
assert (wa, ha) == (wb, hb) == (960, 64), 'wrong dimensions'
bad = [(x, y) for y in range(64) for x in range(960)
       if (a[y][x][3] > 0) != (b[y][x][3] > 0) or (a[y][x][3] and tuple(a[y][x][:4]) != tuple(b[y][x][:4]))]
print('differing pixels:', len(bad), bad[:10])
_, _, ref = read_png(r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason.png')
d0 = sum(1 for y in range(64) for x in range(64)
         if (a[y][x][3] > 0) != (ref[y][x][3] > 0) or (a[y][x][3] and tuple(a[y][x][:3]) != tuple(ref[y][x][:3])))
print('frame 0 region vs approved mason.png:', d0, 'differing pixels')
for i in range(15):
    ys = [y for y in range(64) for x in range(64) if a[y][i * 64 + x][3]]
    xs = [x for y in range(64) for x in range(64) if a[y][i * 64 + x][3]]
    print('  frame %2d: x %2d-%2d  y %2d-%2d' % (i, min(xs), max(xs), min(ys), max(ys)))
print('PASS' if not bad and d0 == 0 else 'FAIL')
