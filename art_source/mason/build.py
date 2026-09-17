import sys
from png import read_png
from zoom import write_png
import rig

APPROVED = r'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/mason.png'

def diff(a, b):
    out = []
    for y in range(64):
        for x in range(64):
            pa, pb = a[y][x], b[y][x]
            if (pa[3] > 0) != (pb[3] > 0) or (pa[3] > 0 and tuple(pa[:3]) != tuple(pb[:3])):
                out.append((x, y, pa, pb))
    return out

def checker(X, Y, f):
    c = 232 if ((X // f) + (Y // f)) % 2 == 0 else 208
    return (c, c, c, 255)

def zoom_grid(grid, f, path):
    Wd, Hd = 64 * f, 64 * f
    out = [[grid[Y // f][X // f] if grid[Y // f][X // f][3] else checker(X, Y, f)
            for X in range(Wd)] for Y in range(Hd)]
    write_png(path, Wd, Hd, out)

def strip(grids, f, path, gap=6, labels=None):
    n = len(grids)
    Wd = n * 64 * f + (n - 1) * gap; Hd = 64 * f
    out = [[(70, 70, 80, 255)] * Wd for _ in range(Hd)]
    out = [r[:] for r in out]
    for i, g in enumerate(grids):
        ox = i * (64 * f + gap)
        for Y in range(Hd):
            for X in range(64 * f):
                p = g[Y // f][X // f]
                out[Y][ox + X] = p if p[3] else checker(X, Y, f)
    write_png(path, Wd, Hd, out)

if __name__ == '__main__':
    g0 = rig.render({})
    _, _, ref = read_png(APPROVED)
    d = diff(g0, ref)
    print('frame 0 vs approved mason.png: %d differing pixels' % len(d))
    for item in d[:20]: print('   ', item)
    print('frozen thresholds:', {k: [round(v, 4) for v in vs] for k, vs in rig.TH.items()})
