import sys
from lib import *
import frames as FR
def main(idx, out, y0=0, y1=48, s=5, cols=3):
    fr = FR.build_frames()
    sel = [fr[i] for i in idx]
    hh = y1 - y0
    gap = 3
    rows = (len(sel) + cols - 1) // cols
    Wt = cols * 64 + (cols + 1) * gap
    Ht = rows * hh + (rows + 1) * gap
    bg = (58, 64, 84, 255)
    img = [[(20, 20, 26, 255)] * Wt for _ in range(Ht)]
    for k, (name, dur, cv) in enumerate(sel):
        r, c = divmod(k, cols)
        ox = gap + c * (64 + gap); oy = gap + r * (hh + gap)
        rgba = to_rgba(cv)
        for y in range(y0, y1):
            for x in range(64):
                p = rgba[y][x]
                img[oy + y - y0][ox + x] = p if p[3] == 255 else bg
    w2, h2, big = scale(Wt, Ht, img, s)
    write_png(out, w2, h2, big)
if __name__ == '__main__':
    idx = [int(v) for v in sys.argv[1].split(',')]
    main(idx, sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
