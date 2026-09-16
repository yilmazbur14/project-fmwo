"""view.py src out fw fh cols scale [frames comma list] [bg]
Lay frames of a horizontal strip into a grid, upscale, write png for viewing."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png

src, out = sys.argv[1], sys.argv[2]
fw, fh, cols, s = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
w, h, pix = read_png(src)
nframes = w // fw
frames = list(range(nframes))
if len(sys.argv) > 7 and sys.argv[7] != 'all':
    frames = [int(v) for v in sys.argv[7].split(',')]
bgmode = sys.argv[8] if len(sys.argv) > 8 else 'checker'
rows = (len(frames) + cols - 1) // cols
gap = 4
W = cols * fw * s + (cols + 1) * gap
H = rows * fh * s + (rows + 1) * gap
img = [[(255, 0, 255, 255)] * W for _ in range(H)]
for k, f in enumerate(frames):
    cx = gap + (k % cols) * (fw * s + gap)
    cy = gap + (k // cols) * (fh * s + gap)
    for Y in range(fh * s):
        y = Y // s
        for X in range(fw * s):
            x = X // s
            p = pix[y][f * fw + x]
            if p[3] < 255:
                if bgmode == 'checker':
                    c = 205 if (((X // s) // 4 + (y // 4)) % 2 == 0) else 180
                    base = (c, c, c)
                elif bgmode == 'dark':
                    base = (60, 52, 44)
                elif bgmode == 'floor':
                    base = (136, 180, 99)
                else:
                    base = (205, 205, 205)
                a = p[3] / 255.0
                p = tuple(int(p[i] * a + base[i] * (1 - a)) for i in range(3)) + (255,)
            img[cy + Y][cx + X] = p
write_png(out, W, H, img)
print('wrote', out, W, H)
