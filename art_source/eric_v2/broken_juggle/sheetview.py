"""Review helper: side-by-side zoomed crops of rendered key frames.

    python sheetview.py <dir> <out.png> <scale> <x> <y> <w> <h> name [name ...]
"""
import os
import sys
from PIL import Image, ImageDraw

BG = (96, 110, 96, 255)


def main():
    d, out, s = sys.argv[1], sys.argv[2], int(sys.argv[3])
    x, y, w, h = map(int, sys.argv[4:8])
    names = sys.argv[8:]
    pad = 6
    W = len(names) * (w * s + pad) + pad
    H = h * s + 2 * pad + 14
    c = Image.new('RGBA', (W, H), (30, 30, 30, 255))
    dr = ImageDraw.Draw(c)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(d, n + '.png')).convert('RGBA').crop((x, y, x + w, y + h))
        bg = Image.new('RGBA', im.size, BG)
        bg.alpha_composite(im)
        X = pad + i * (w * s + pad)
        c.paste(bg.resize((w * s, h * s), Image.NEAREST), (X, pad + 14))
        dr.text((X + 2, 2), n, fill=(255, 255, 0, 255))
    c.save(out)
    print(out, c.size)


if __name__ == '__main__':
    main()
