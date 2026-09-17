"""8x view of one frame region with a 10px coordinate grid on transparent pixels, and a text dump."""
import sys
from frames import *
BG = (120, 160, 120, 255); BG2 = (105, 145, 105, 255)
name = sys.argv[1]
x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(',')]
s = int(sys.argv[3]) if len(sys.argv) > 3 else 8
g = dict(FRAMES)[name]()
w, h = x1 - x0, y1 - y0
img = []
for j in range(h * s):
    y = y0 + j // s
    row = []
    for i in range(w * s):
        x = x0 + i // s
        c = g[y][x]
        if c in PAL:
            row.append(PAL[c] + (255,))
        else:
            row.append(BG2 if (x % 10 == 0 or y % 10 == 0) else BG)
    img.append(row)
write_png('i8_%s.png' % name, w * s, h * s, img)
save_txt('cur_%s.txt' % name, g, x0, y0, x1, y1)
if '-q' not in sys.argv:
    print(open('cur_%s.txt' % name).read())
