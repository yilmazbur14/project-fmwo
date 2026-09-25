"""Inspection helpers: python look.py head  |  python look.py frames  |  python look.py zoom f x0 y0 x1 y1 [s]"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402
import lib  # noqa: E402
from PIL import Image  # noqa: E402


def gridded(im, s, major=5):
    return lib.grid(im, s, major=major)


def crop_grid(px, x0, y0, x1, y1, s=12):
    im = kit.image(px).crop((x0, y0, x1 + 1, y1 + 1))
    return gridded(im, s)


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'head':
        import head
        c = kit.Canvas(96, 96)
        c.stamp(head.head(), outline=False)
        kit.save(crop_grid(c.px, 34, 6, 63, 42, 14), "head_14x.png")
        im = kit.image(c.px).crop((34, 6, 64, 43))
        kit.save(kit.row([kit.up(im, 3), kit.up(im, 6)]), 'head_3x_6x.png')
    elif what == 'frames':
        import jordan
        f0, f1 = jordan.frames()
        kit.save(kit.row([kit.up(f0, 5), kit.up(f1, 5)]), 'frames_5x.png')
        kit.save(kit.row([kit.up(f0, 3), kit.up(f1, 3)]), 'frames_3x.png')
        for i, f in enumerate((f0, f1)):
            print('frame', i, kit.stats(f), 'bbox', f.getbbox())
    elif what == 'zoom':
        import jordan
        fi = int(sys.argv[2])
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
        s = int(sys.argv[7]) if len(sys.argv) > 7 else 12
        px = jordan.build(fi).px
        kit.save(crop_grid(px, x0, y0, x1, y1, s), 'zoom_f%d_%d_%d.png' % (fi, x0, y0))
