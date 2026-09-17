"""Final build: strip + in-context mockups (PNG) + animated GIFs of the arena top band."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import crowd
from pngio import read_png, write_png
from gifio import write_gif

OUT = os.path.join(HERE, 'final')
os.makedirs(OUT, exist_ok=True)
RENDER = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
          'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/wiring/round2/eric/frame00000089.png')

figures, frames = crowd.render()
strip_path = os.path.join(OUT, 'crowd_v2.png')
crowd.write_strip(frames, strip_path)
sw, sh, strip = read_png(strip_path)
print('strip', sw, sh)

rw, rh, rend = read_png(RENDER)
OLD_TAN = (217, 160, 102, 255)
BLACK = (0, 0, 0, 255)
SIDE_GREEN = (113, 152, 79, 255)   # ColorRect2/3 are drawn BEFORE the crowd sprite
BAND = 125


def near(x, y, pred, r):
    for yy in range(max(0, y - r), min(rh, y + r + 1)):
        for xx in range(max(0, x - r), min(rw, x + r + 1)):
            if pred(rend[yy][xx]):
                return True
    return False


white = lambda p: p[0] > 240 and p[1] > 240 and p[2] > 240
redbar = lambda p: p[0] > 180 and p[1] < 60 and p[2] < 60
brass = lambda p: p in ((138, 111, 48, 255), (209, 175, 97, 255))

# which render pixels in the top band sit IN FRONT of the crowd (rope, posts, floor, HUD)?
front = [[False] * rw for _ in range(BAND)]
for y in range(BAND):
    for x in range(rw):
        p = rend[y][x]
        fg = p not in (OLD_TAN, BLACK, SIDE_GREEN)
        if p == BLACK:
            if 109 <= x <= 1809 and 93 <= y <= 114:
                fg = True
            elif 700 <= x <= 1220 and 30 <= y <= 100 and (near(x, y, white, 2) or near(x, y, redbar, 1)):
                fg = True
            elif (80 <= x <= 140 or 1770 <= x <= 1840) and 65 <= y <= 125 and near(x, y, brass, 2):
                fg = True
        front[y][x] = fg


def band_for(fi):
    out = []
    for y in range(BAND):
        row = []
        for x in range(rw):
            p = rend[y][x]
            if front[y][x]:
                row.append(p)
                continue
            c = strip[y // 3][fi * 640 + x // 3] if y < 120 else (0, 0, 0, 0)
            row.append(c if c[3] else (SIDE_GREEN if p == SIDE_GREEN else BLACK))
        out.append(row)
    return out


bands = [band_for(i) for i in range(crowd.NF)]
for i, name in ((0, 'idle'), (3, 'cheer')):
    full = [list(r) for r in rend]
    full[:BAND] = bands[i]
    write_png(os.path.join(OUT, f'mockup_{name}_frame{i}.png'), rw, rh, full)
    write_png(os.path.join(OUT, f'mockup_{name}_topband.png'), rw, BAND, bands[i])
    print('mockup', name)

GIF_H = 135
def gif_frame(i):
    return [row for row in bands[i]] + [list(r) for r in rend[BAND:GIF_H]]

idle = [gif_frame(i) for i in (0, 1, 2)]
cheer = [gif_frame(i) for i in (3, 4)]
write_gif(os.path.join(OUT, 'mockup_idle.gif'), idle, [35, 35, 35])
write_gif(os.path.join(OUT, 'mockup_cheer.gif'), cheer, [15, 15])
seq, delays = [], []
for _ in range(3):
    seq += idle; delays += [35, 35, 35]
for _ in range(6):
    seq += cheer; delays += [15, 15]
write_gif(os.path.join(OUT, 'mockup_idle_then_cheer.gif'), seq, delays)
print('gifs done')
