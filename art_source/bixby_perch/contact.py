"""Contact sheets of the 16 frames (scratch only).

    python contact.py            # all frames at 2x, and each on the arena at game scale
    python contact.py 4 5 6      # just these frames, at 4x
"""
import sys

from PIL import Image, ImageDraw

import sheet
import stage
from common import SCRATCH, on_bg, up, FW

LABELS = []
for name, n in sheet.NAMES:
    for i in range(n):
        LABELS.append('%s %d' % (name, i))


def grid(ims, s=2, cols=8, rows_px=200, name='contact_2x.png'):
    cells = [up(on_bg(im.crop((0, 0, FW, rows_px))), s) for im in ims]
    w, h = cells[0].size
    nrows = (len(cells) + cols - 1) // cols
    out = Image.new('RGBA', (cols * (w + 6), nrows * (h + 22)), (14, 13, 18, 255))
    d = ImageDraw.Draw(out)
    for i, c in enumerate(cells):
        x, y = (i % cols) * (w + 6), (i // cols) * (h + 22)
        out.alpha_composite(c, (x, y + 18))
        d.text((x + 4, y + 3), '%d  %s' % (i, LABELS[i]), fill=(230, 230, 230, 255))
    out.save(SCRATCH + name)
    return out


def stages(ims, idx, name='contact_stage.png', w=600, h=620, cols=4):
    cells = []
    for i in idx:
        sc = stage.scene(ims[i], hud=False, with_player=False)
        cells.append(stage.crop_around(sc, w, h))
    nrows = (len(cells) + cols - 1) // cols
    out = Image.new('RGBA', (cols * (w + 6), nrows * (h + 22)), (14, 13, 18, 255))
    d = ImageDraw.Draw(out)
    for j, c in enumerate(cells):
        x, y = (j % cols) * (w + 6), (j // cols) * (h + 22)
        out.alpha_composite(c, (x, y + 18))
        d.text((x + 4, y + 3), '%d  %s' % (idx[j], LABELS[idx[j]]), fill=(230, 230, 230, 255))
    out.save(SCRATCH + name)
    return out


if __name__ == '__main__':
    ims = sheet.frames()
    args = [int(a) for a in sys.argv[1:]]
    if args:
        for i in args:
            up(on_bg(ims[i].crop((0, 0, FW, 200))), 4).save(SCRATCH + 'frame_%02d_4x.png' % i)
    else:
        grid(ims)
        stages(ims, list(range(0, 8)), 'contact_stage_a.png')
        stages(ims, list(range(8, 16)), 'contact_stage_b.png')
