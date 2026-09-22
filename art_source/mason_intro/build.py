"""python build.py  - write fry_trail.png (7 frames of 32x16) and the previews."""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fries  # noqa: E402

OUT = os.path.join(HERE, 'fry_trail.png')
MAT = '#7EA85B'          # arena_mat.png's commonest green, for the previews only


def strip():
    n = len(fries.FRAMES)
    im = Image.new('RGBA', (fries.FW * n, fries.FH), (0, 0, 0, 0))
    for i, (_, fn) in enumerate(fries.FRAMES):
        g = fn()
        for y in range(fries.FH):
            for x in range(fries.FW):
                im.putpixel((i * fries.FW + x, y), g[y][x])
    return im


def preview(im, scale, path, on_mat=True):
    """Previews sit on the mat's own green: these fries are only ever seen there
    and a checkerboard would flatter colours the arena will not."""
    z = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    pad = 4 * scale
    bg = Image.new('RGBA', (z.width + 2 * pad, z.height + 2 * pad),
                   fries.hex2rgba(MAT) if on_mat else (0, 0, 0, 0))
    bg.alpha_composite(z, (pad, pad))
    bg.convert('RGB' if on_mat else 'RGBA').save(path)
    return path


def main():
    im = strip()
    im.save(OUT)
    print('%-22s %dx%d, %d frames of %dx%d'
          % (os.path.basename(OUT), im.width, im.height,
             len(fries.FRAMES), fries.FW, fries.FH))
    for scale, name in ((3, 'fry_trail_3x.png'), (8, 'fry_trail_8x.png')):
        print('  ', preview(im, scale, os.path.join(HERE, name)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
