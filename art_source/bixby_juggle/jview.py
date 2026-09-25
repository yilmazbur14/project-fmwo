"""python jview.py [scale] [frame indices...]  - juggle frames in a grid with guides, into the scratchpad
only (jcommon.SCRATCH/work/). Guides: the frame edge (magenta), the feet row (cyan), the tumble centre
(yellow cross). Nothing is written anywhere else."""
import os
import sys

from PIL import Image, ImageDraw

import jcommon as C
import jposes
import jrot

OUT = os.path.join(C.SCRATCH, 'work')


def grid(frames, s=2, cols=4, guides=True, labels=None):
    rows = (len(frames) + cols - 1) // cols
    gap = 4
    W = cols * (C.W * s + gap)
    H = rows * (C.H * s + gap + (12 if labels else 0))
    out = Image.new('RGBA', (W, H), (24, 24, 30, 255))
    d = ImageDraw.Draw(out)
    for i, a in enumerate(frames):
        cx = (i % cols) * (C.W * s + gap)
        cy = (i // cols) * (C.H * s + gap + (12 if labels else 0))
        if labels:
            d.text((cx + 2, cy), labels[i], fill=(220, 220, 220, 255))
            cy += 12
        im = jrot.upscale(jrot.to_img(a), s)
        out.alpha_composite(im, (cx, cy))
        if guides:
            d.rectangle((cx, cy, cx + C.W * s - 1, cy + C.H * s - 1), outline=(170, 40, 170, 255))
            fy = cy + C.FEET[1] * s + s // 2
            d.line((cx, fy, cx + C.W * s - 1, fy), fill=(60, 220, 230, 160))
            tx, ty = cx + C.TUMBLE_CENTRE[0] * s, cy + C.TUMBLE_CENTRE[1] * s
            d.line((tx - 6, ty, tx + 6, ty), fill=(250, 230, 60, 255))
            d.line((tx, ty - 6, tx, ty + 6), fill=(250, 230, 60, 255))
    return out


def main():
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    want = [int(a) for a in sys.argv[2:]] or list(range(len(jposes.FRAMES)))
    frames = [jposes.FRAMES[i][1]() for i in want]
    labels = ['%d %s' % (i, jposes.FRAMES[i][0]) for i in want]
    os.makedirs(OUT, exist_ok=True)
    name = 'view_%s_%dx.png' % ('all' if len(want) == len(jposes.FRAMES) else '_'.join(map(str, want)), s)
    grid(frames, s, cols=min(4, len(frames)), labels=labels).save(os.path.join(OUT, name))
    print('wrote', os.path.join(OUT, name))


if __name__ == '__main__':
    main()
