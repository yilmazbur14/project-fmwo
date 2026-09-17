import sys, math
sys.path.insert(0, '..')
from pngio import read_png, write_png, scale
from gifio import write_gif
import mockup
A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
FLOOR = (136, 180, 99, 255)
SC = 3
def load(n): return read_png(A + n)[2]
def fr(px, fw, i): return [r[i * fw:(i + 1) * fw] for r in px]
eric = load('eric_redesign_sword.png'); thrown = load('eric_thrown_sword.png'); planted = load('eric_sword_planted.png')
impact = load('eric_quake_impact.png'); seg = load('eric_quake_segment.png')

NW, NH = 560, 320
out = [[FLOOR] * (NW * SC) for _ in range(NH * SC)]
rcx, rcy, R, n = 405, 178, 110, 25
for i in range(n):
    a = 2 * math.pi * i / n
    mockup.draw(out, fr(seg, 32, 1), rcx + R * math.cos(a), rcy + R * math.sin(a), 16, 16, a + math.pi / 2)
mockup.draw(out, fr(impact, 160, 2), rcx, rcy, 80.5, 66.5)
mockup.draw(out, fr(planted, 64, 1), rcx, rcy, 31.5, 112.5)
mockup.draw(out, fr(eric, 128, 0), 80, 200, 64, 64)
mockup.draw(out, fr(thrown, 128, 1), 205, 105, 64, 64)
write_png('mockup2_3x.png', NW * SC, NH * SC, out)

# spin GIF (4x, 50 ms) and a landing GIF (planted impact -> settled over the approved impact sheet)
frames = []
for i in range(8):
    c = [[FLOOR] * 128 for _ in range(128)]
    f = fr(thrown, 128, i)
    for y in range(128):
        for x in range(128):
            if f[y][x][3]: c[y][x] = f[y][x]
    frames.append(scale(c, 3))
print('spin', write_gif('gif2_thrown_sword_spin.gif', frames, [5] * 8))
frames = []; delays = []
def comp(imp_i, pl_i):
    c = [[FLOOR] * 160 for _ in range(150)]
    if imp_i is not None:
        f = fr(impact, 160, imp_i)
        for y in range(80):
            for x in range(160):
                if f[y][x][3]: c[y + 132 - 66][x] = f[y][x]
    f = fr(planted, 64, pl_i)
    for y in range(128):
        for x in range(64):
            if f[y][x][3]: c[y + 132 - 112][x + 80 - 31] = f[y][x]
    return scale(c, 3)
frames.append(comp(None, 0)); delays.append(10)
frames.append(comp(None, 1)); delays.append(40)
for i in range(6):
    frames.append(comp(i, 1)); delays.append(8 if i < 5 else 60)
print('impact', write_gif('gif2_planted_impact.gif', frames, delays))
