"""usage: lineup.py out.png scale bg(checker|dark|light) src1[:x:y:w:h] src2 ...
Places 64x64 frames (or crops) side by side with a 4px gap, nearest-neighbour upscaled."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, scale, checker_bg

out, s, bg = sys.argv[1], int(sys.argv[2]), sys.argv[3]
tiles = []
for spec in sys.argv[4:]:
    parts = spec.split('|')
    path = parts[0]
    w, h, px = read_png(path)
    if len(parts) == 5:
        x0, y0, cw, ch = map(int, parts[1:])
        px = [row[x0:x0 + cw] for row in px[y0:y0 + ch]]
        w, h = cw, ch
    tiles.append((w, h, px))
gap = 4
TW = sum(t[0] for t in tiles) + gap * (len(tiles) + 1)
TH = max(t[1] for t in tiles) + gap * 2
canvas = [[(0, 0, 0, 0)] * TW for _ in range(TH)]
x = gap
for (w, h, px) in tiles:
    oy = gap + (TH - 2 * gap - h)
    for yy in range(h):
        for xx in range(w):
            canvas[oy + yy][x + xx] = px[yy][xx]
    x += w + gap
if bg == 'checker':
    canvas = checker_bg(TW, TH, canvas, cell=4, c1=(190, 196, 204, 255), c2=(160, 168, 178, 255))
else:
    col = {'dark': (52, 48, 62, 255), 'light': (214, 206, 190, 255), 'arena': (94, 84, 76, 255)}[bg]
    canvas = [[p if p[3] == 255 else col for p in row] for row in canvas]
W2, H2, big = scale(TW, TH, canvas, s)
write_png(out, W2, H2, big)
print(TW, TH, '->', W2, H2)
