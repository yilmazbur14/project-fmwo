import sys
from lib import *
BG = (120, 160, 120, 255)
def view_txt(paths, out, s=8, pad=2):
    grids = []
    for p in paths:
        x0, y0, rows = load_txt(p)
        grids.append((x0, y0, rows))
    W = sum(len(r[2][0]) for r in grids) + pad * (len(grids) - 1)
    H = max(len(r[2]) for r in grids)
    img = [[(40, 40, 40, 255)] * (W * s) for _ in range(H * s)]
    ox = 0
    for x0, y0, rows in grids:
        for j, r in enumerate(rows):
            for i, c in enumerate(r):
                col = PAL[c] + (255,) if c in PAL else BG
                for yy in range(s):
                    for xx in range(s):
                        img[j * s + yy][(ox + i) * s + xx] = col
        ox += len(rows[0]) + pad
    write_png(out, W * s, H * s, img)
if __name__ == '__main__':
    s = int(sys.argv[1]); out = sys.argv[2]
    view_txt(sys.argv[3:], out, s)
