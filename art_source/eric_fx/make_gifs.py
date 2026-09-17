import math
from pngio import read_png, write_png, scale
from gifio import write_gif
import mockup

FLOOR = (136, 180, 99, 255)

A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
def load(p):
    return read_png(A + p)[2]

def fr(px, fw, i):
    return [row[i * fw:(i + 1) * fw] for row in px]

def canvas(w, h):
    return [[FLOOR] * w for _ in range(h)]

def paste(dst, src, ox, oy):
    for y, row in enumerate(src):
        for x, p in enumerate(row):
            if p[3] and 0 <= oy + y < len(dst) and 0 <= ox + x < len(dst[0]):
                dst[oy + y][ox + x] = p

thrown = load('eric_thrown_sword.png')
planted = load('eric_sword_planted.png')
impact = load('eric_quake_impact.png')

# 1) spinning sword, 4x, 60 ms per frame
frames = []
for i in range(8):
    c = canvas(96, 96); paste(c, fr(thrown, 96, i), 0, 0)
    frames.append(scale(c, 4))
print('spin', write_gif('gif_thrown_sword_spin.gif', frames, [6] * 8))

# 2) sword lands, then the quake impact plays at the sword's ground contact, 4x
frames = []; delays = []
for i in range(2):                                   # landing + settled
    c = canvas(160, 100); paste(c, fr(planted, 64, i), 80 - 32, 82 - 80)
    frames.append(scale(c, 4)); delays.append(10 if i == 0 else 40)
for i in range(6):
    c = canvas(160, 100)
    paste(c, fr(impact, 160, i), 0, 82 - 66)
    paste(c, fr(planted, 64, 1), 80 - 32, 82 - 80)
    frames.append(scale(c, 4)); delays.append(8)
delays[-1] = 60
print('impact', write_gif('gif_quake_impact.gif', frames, delays))

# 3) impact sheet alone (no sword), 4x
frames = []
for i in range(6):
    c = canvas(160, 80); paste(c, fr(impact, 160, i), 0, 0)
    frames.append(scale(c, 4))
print('impact_only', write_gif('gif_quake_impact_only.gif', frames, [8, 8, 8, 8, 8, 50]))

# 4) shockwave ring expanding with the segment frames cycling, 3x
seg = load('eric_quake_segment.png')
frames = []
NW = NH = 280
for t in range(16):
    r = 34 + t * 6.5
    out = [[FLOOR] * (NW * 3) for _ in range(NH * 3)]
    n = max(8, math.ceil(2 * math.pi * r / 28))
    for j in range(n):
        a = 2 * math.pi * j / n
        mockup.draw(out, fr(seg, 32, t % 4), 140 + r * math.cos(a), 140 + r * math.sin(a), 16, 16, a + math.pi / 2)
    mockup.draw(out, fr(planted, 64, 1), 140, 140, 32.5, 80.5)
    frames.append(out)
print('ring', write_gif('gif_quake_ring.gif', frames, [7] * 16))
