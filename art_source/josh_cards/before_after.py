"""Before/after sheet for the polish pass: old strip on top, new strip underneath, at 6x.

Usage: python before_after.py <old_dir> <new_dir> <out_png> <anim> [<anim> ...]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import W, H
from pngio import read_png, write_png
from mockup import label

BG = (40, 38, 52, 255)
LINE = (92, 88, 112, 255)


def row(img, px, w, h, n, x0, y0, f):
    for i in range(n):
        for y in range(H * f):
            for x in range(W * f):
                p = px[y // f][i * W + x // f]
                if p[3]:
                    img[y0 + y][x0 + i * (W * f + 8) + x] = p[:3] + (255,)
        for yy in range(y0 - 1, y0 + H * f + 1):
            for xx in (x0 + i * (W * f + 8) - 1, x0 + i * (W * f + 8) + W * f):
                if 0 <= yy < len(img) and 0 <= xx < len(img[0]):
                    img[yy][xx] = LINE


if __name__ == '__main__':
    old_dir, new_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    names = sys.argv[4:]
    f = 6
    blocks = []
    for n in names:
        ow, oh, opx = read_png(os.path.join(old_dir, n + '.png'))
        nw, nh, npx = read_png(os.path.join(new_dir, n + '.png'))
        blocks.append((n, ow // W, opx, npx))
    cols = max(b[1] for b in blocks)
    TW = 150 + cols * (W * f + 8) + 20
    TH = 60 + sum(2 * (H * f + 30) + 26 for b in blocks) + 10
    img = [[BG] * TW for _ in range(TH)]
    label(img, 14, 18, 'JOSH POLISH PASS  BEFORE ABOVE  AFTER BELOW', sc=4)
    y = 60
    for (n, cnt, opx, npx) in blocks:
        label(img, 14, y + H * f // 2, n.replace('josh_', '').upper(), sc=3)
        label(img, 100, y + 6, 'OLD', sc=3, col=(220, 130, 130, 255))
        row(img, opx, 0, 0, cnt, 150, y, f)
        y += H * f + 30
        label(img, 100, y + 6, 'NEW', sc=3, col=(150, 220, 150, 255))
        row(img, npx, 0, 0, cnt, 150, y, f)
        y += H * f + 30 + 26
    write_png(out, TW, TH, img)
    print('wrote', os.path.basename(out), TW, 'x', TH)
