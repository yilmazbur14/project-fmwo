"""Preview GIFs for every new animation (written next to the work folder)."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from compose import *

DEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'previews')
os.makedirs(DEST, exist_ok=True)
PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/'

mason = Sheet(os.path.join(OUT, 'mason_sheet.png'), 64, 64)
meteor = Sheet(os.path.join(OUT, 'nugget_meteor.png'), 48, 64)
target = Sheet(os.path.join(OUT, 'nugget_target.png'), 48, 26)
impact = Sheet(os.path.join(OUT, 'nugget_impact.png'), 64, 48)
et2 = Sheet(os.path.join(OUT, 'elbow_target_v2.png'), 76, 76)
ei2 = Sheet(os.path.join(OUT, 'elbow_impact_v2.png'), 104, 104)
et1 = Sheet(PROJ + 'elbow_target.png', 48, 48)
ei1 = Sheet(PROJ + 'elbow_impact.png', 64, 64)

V = (-math.sin(math.radians(20)), math.cos(math.radians(20)))


def simple(sheet, idx, delays, s, pad, name):
    frames = []
    for i in idx:
        c = Canvas((sheet.fw + 2 * pad) * s, (sheet.fh + 2 * pad) * s)
        if i is not None:
            c.blit(sheet.frame(i), pad * s, pad * s, s)
        frames.append(c)
    gif(os.path.join(DEST, name), frames, delays)


# 1. Mason cast: idle -> pull -> hoist -> heave -> hold/shout
simple(mason, [0, 15, 16, 17, 18], [45, 30, 35, 18, 110], 4, 4, 'mason_nugget_cast.gif')
# 2. meteor loop
simple(meteor, [0, 1, 2, 3], [8, 8, 8, 8], 4, 4, 'nugget_meteor_loop.gif')
# 3. marker: grow then pulse
simple(target, [0, 1, 2, 3, 2, 3, 2, 3], [22, 22, 12, 12, 12, 12, 12, 12], 4, 4, 'nugget_target.gif')
# 4. impact (then a beat of empty floor)
simple(impact, [0, 1, 2, 3, 4, None], [6, 7, 7, 8, 12, 40], 4, 3, 'nugget_impact.gif')
# 5. v2 Carter effects, as the scene plays them (pulse 0.15s per frame, burst 0.1s per frame)
simple(et2, [0, 1], [15, 15], 3, 4, 'elbow_target_v2.gif')
simple(ei2, [0, 1, 2, 3, None], [10, 10, 10, 10, 40], 3, 3, 'elbow_impact_v2.gif')

# 6. one full meteor at game scale: marker grows, nugget falls along the 20 degree line, impact
S = 3
W, H = 420, 540
M = (170, 420)                       # marker / impact centre (screen px)
seq = []
delays = []


def frame_with(tgt=None, met=None, imp=None):
    c = Canvas(W, H)
    if tgt is not None:
        c.place(target.frame(tgt), M[0], M[1], S)
    if imp is not None:
        c.place(impact.frame(imp), M[0], M[1], S)
    if met is not None:
        f, d = met
        nx, ny = M[0] - V[0] * d, M[1] - V[1] * d
        c.place(meteor.frame(f), nx, ny, S, anchor=(16.5, 48.0))
    return c


seq.append(frame_with(tgt=0)); delays.append(20)
seq.append(frame_with(tgt=1)); delays.append(20)
for k, d in enumerate([520, 430, 340, 250, 160, 75]):
    seq.append(frame_with(tgt=2 + (k % 2), met=(k % 4, d))); delays.append(7)
for i in range(5):
    seq.append(frame_with(imp=i)); delays.append((6, 7, 7, 8, 12)[i])
seq.append(frame_with()); delays.append(45)
gif(os.path.join(DEST, 'nugget_shower_sequence_3x.gif'), seq, delays)

# 7. Carter old vs new, side by side at game scale
S = 3
W, H = 1040, 420
frames = []
for t in range(4):
    c = Canvas(W, H)
    c.place(et1.frame(t % 2), 180, 110, S)
    c.place(et2.frame(t % 2), 700, 110, S)
    c.place(ei1.frame(t), 180, 300, S)
    c.place(ei2.frame(t), 700, 300, S)
    text(c, 20, 10, 4, 'OLD')
    text(c, 470, 10, 4, 'NEW 1.6X')
    frames.append(c)
gif(os.path.join(DEST, 'elbow_old_vs_v2_3x.gif'), frames, [12, 12, 12, 12])
