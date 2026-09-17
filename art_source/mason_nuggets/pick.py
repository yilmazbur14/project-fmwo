"""pick.py sheet.png out.png fw fh scale idx,idx,..  -> selected frames side by side, zoomed, with 1px grid lines every 8px"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png
src, dst = sys.argv[1], sys.argv[2]
fw, fh, s = int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
idxs = [int(v) for v in sys.argv[6].split(',')]
bg = tuple(int(v) for v in sys.argv[7].split(',')) + (255,) if len(sys.argv) > 7 else (136, 180, 99, 255)
grid = len(sys.argv) <= 8 or sys.argv[8] != 'nogrid'
w, h, px = read_png(src)
cols = w // fw
gap = 6
W = len(idxs) * (fw * s + gap) - gap
H = fh * s
out = [[(40, 40, 40, 255)] * W for _ in range(H)]
for k, i in enumerate(idxs):
    fx, fy = (i % cols) * fw, (i // cols) * fh
    ox = k * (fw * s + gap)
    for y in range(fh):
        for x in range(fw):
            p = px[fy + y][fx + x]
            if p[3] == 0:
                q = bg
            elif p[3] < 255:
                a = p[3] / 255
                q = tuple(int(p[j] * a + bg[j] * (1 - a)) for j in range(3)) + (255,)
            else:
                q = p
            for yy in range(s):
                for xx in range(s):
                    c = q
                    if grid and s >= 6 and ((xx == 0 and x % 8 == 0) or (yy == 0 and y % 8 == 0)):
                        c = tuple(max(0, v - 40) for v in q[:3]) + (255,)
                    out[y * s + yy][ox + x * s + xx] = c
write_png(dst, W, H, out)
print('wrote', dst, W, H)
