"""viewposes.py uppercut_poses tag scale NAME[:lift],... -> close-up of selected poses (grounded, R=0 unless
given as NAME:R), with the idle frame first. Crops to the used rows."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uplib import *
from pngio import write_png
import importlib
from paths import PROJ, work

mod = importlib.import_module(sys.argv[1])
tag = sys.argv[2]
S = int(sys.argv[3])
names = sys.argv[4].split(',')
sheet = from_png(PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png')


def std_frame(row, col):
    c = Canvas(48, 64)
    for y in range(32):
        for x in range(32):
            c.p[32 + y][8 + x] = sheet.p[row * 32 + y][col * 32 + x]
    return c


frames = [std_frame(3, 0)]
for n in names:
    R = 0
    if ':' in n:
        n, R = n.split(':')
        R = int(R)
    if hasattr(mod, 'render'):
        frames.append(mod.render(n, R))
    else:
        y0, rows = getattr(mod, n)
        c = Canvas(48, 64)
        c.stamp(rows, 8, 32 + y0 - R)
        frames.append(c)
s = strip(frames)
ys = [y for y in range(s.h) for x in range(s.w) if s.p[y][x]]
y0 = max(0, min(ys) - 2)
y1 = min(s.h, max(ys) + 3)
cr = Canvas(s.w, y1 - y0)
for y in range(y0, y1):
    cr.p[y - y0] = s.p[y][:]
W, H, px = zoom_rgba(cr, S, bg=(136, 180, 99), grid=(48, 64))
# ground line at y=61 edge
gy = (61 - y0) * S
if 0 <= gy < H:
    for i in range(W):
        if (i // S) % 2 == 0:
            px[gy][i] = (60, 90, 40, 255)
write_png(work('view_%s.png' % tag), W, H, px)
print('wrote', work('view_%s.png' % tag), W, H)
