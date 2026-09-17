import sys
from lib import *
BG = (120, 160, 120, 255)
def view(paths, out, s, x0, y0, x1, y1, pad=2):
    grids = [load_seg(p) for p in paths]
    w, h = x1 - x0, y1 - y0
    W = len(grids) * w + pad * (len(grids) - 1)
    img = [[(40, 40, 40, 255)] * (W * s) for _ in range(h * s)]
    for k, g in enumerate(grids):
        ox = k * (w + pad)
        for j in range(h):
            for i in range(w):
                c = g[y0 + j][x0 + i]
                col = PAL[c] + (255,) if c in PAL else BG
                for yy in range(s):
                    r = img[j * s + yy]
                    for xx in range(s):
                        r[(ox + i) * s + xx] = col
    write_png(out, W * s, h * s, img)
if __name__ == '__main__':
    s = int(sys.argv[1]); x0, y0, x1, y1 = [int(v) for v in sys.argv[2].split(',')]
    view(sys.argv[4:], sys.argv[3], s, x0, y0, x1, y1)
