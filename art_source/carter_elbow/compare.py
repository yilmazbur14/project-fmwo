"""compare.py strip.png out.png scale -> Carter idle frame 0 + the 5 elbow frames on arena green"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png
CARTER = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/CarterAndJosh/carter.png'
strip, out, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
_, _, cp = read_png(CARTER)
w, h, sp = read_png(strip)
n = w // 64
frames = [[row[0:64] for row in cp]] + [[row[i * 64:(i + 1) * 64] for row in sp] for i in range(n)]
gap = 2 * s
W = len(frames) * 64 * s + (len(frames) + 1) * gap
H = 64 * s + 2 * gap
floor = (136, 180, 99, 255)
img = [[(90, 120, 66, 255)] * W for _ in range(H)]
for k, fr in enumerate(frames):
    ox = gap + k * (64 * s + gap)
    for Y in range(64 * s):
        for X in range(64 * s):
            p = fr[Y // s][X // s]
            img[gap + Y][ox + X] = p if p[3] == 255 else floor
write_png(out, W, H, img)
print('wrote', out, W, H)
