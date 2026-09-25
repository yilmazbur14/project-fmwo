"""Zoomed previews for the Inferno FX rig. Writes only into the scratchpad view folder.

  python view.py <png> <scale> [out_name] [--grid W H] [--bg RRGGBB] [--crop x0 y0 x1 y1]

A checkerboard (or a flat --bg) sits under transparent pixels so the silhouette reads, and --grid draws
the frame boundaries so sheets can be checked frame by frame.
"""
import os
import sys

from PIL import Image, ImageDraw

SCRATCH = r'C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_inferno_fx/view'


def checker(w, h, cell=8, a=(58, 58, 66, 255), b=(78, 78, 88, 255)):
    im = Image.new('RGBA', (w, h), a)
    d = ImageDraw.Draw(im)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if (x // cell + y // cell) % 2:
                d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=b)
    return im


def zoom(im, scale, grid=None, bg=None):
    im = im.convert('RGBA')
    big = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    base = Image.new('RGBA', big.size, bg) if bg else checker(big.width, big.height, max(4, scale * 2))
    base.alpha_composite(big)
    if grid:
        d = ImageDraw.Draw(base)
        gw, gh = grid
        for x in range(0, im.width + 1, gw):
            d.line([(x * scale, 0), (x * scale, big.height)], fill=(0, 255, 255, 255))
        for y in range(0, im.height + 1, gh):
            d.line([(0, y * scale), (big.width, y * scale)], fill=(0, 255, 255, 255))
    return base


def save(im, name):
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, name)
    im.save(path)
    return path


def main(argv):
    src, scale = argv[0], int(argv[1])
    name = argv[2] if len(argv) > 2 and not argv[2].startswith('--') else os.path.basename(src).replace('.png', '_x%d.png' % scale)
    grid = bg = crop = None
    if '--grid' in argv:
        i = argv.index('--grid')
        grid = (int(argv[i + 1]), int(argv[i + 2]))
    if '--bg' in argv:
        s = argv[argv.index('--bg') + 1]
        bg = (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
    if '--crop' in argv:
        i = argv.index('--crop')
        crop = tuple(int(v) for v in argv[i + 1:i + 5])
    im = Image.open(src)
    if crop:
        im = im.crop(crop)
    print(save(zoom(im, scale, grid, bg), name))


if __name__ == '__main__':
    main(sys.argv[1:])
