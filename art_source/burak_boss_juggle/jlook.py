"""Inspection for the juggle. Writes ONLY to BURAK_JWIP (default: a burak_juggle_wip folder in the
system temp dir), never into Assets/ or the repo.

    python jlook.py grid [s]              all 12 frames in two rows at scale s (default 3)
    python jlook.py zoom F x0 y0 x1 y1 [s]  a gridded crop of frame F
    python jlook.py dump F x0 y0 x1 y1      the keys of a region of frame F
"""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jkit as J  # noqa: E402
import jposes  # noqa: E402
import kit  # noqa: E402
from PIL import Image  # noqa: E402

WIP = os.environ.get('BURAK_JWIP', os.path.join(tempfile.gettempdir(), 'burak_juggle_wip'))


def save(im, name):
    os.makedirs(WIP, exist_ok=True)
    p = os.path.join(WIP, name)
    im.save(p)
    print('wrote', p)


def frame_im(i):
    return kit.image(jposes.FRAMES[i][1](), J.FW, J.FH)


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'grid':
        s = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        ims = [kit.label(kit.up(frame_im(i), s), '%d %s' % (i, jposes.FRAMES[i][0])) for i in range(12)]
        top, bot = kit.row(ims[:6], gap=6), kit.row(ims[6:], gap=6)
        out = Image.new('RGBA', (max(top.width, bot.width), top.height + bot.height + 6), (10, 10, 12, 255))
        out.paste(top, (0, 0))
        out.paste(bot, (0, top.height + 6))
        save(out, 'grid_%dx.png' % s)
    elif what == 'zoom':
        fi = int(sys.argv[2])
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
        s = int(sys.argv[7]) if len(sys.argv) > 7 else 8
        save(kit.grid(frame_im(fi).crop((x0, y0, x1 + 1, y1 + 1)), s, x0, y0), 'zoom_f%d_%d_%d.png' % (fi, x0, y0))
    elif what == 'dump':
        fi = int(sys.argv[2])
        x0, y0, x1, y1 = map(int, sys.argv[3:7])
        print(kit.dump(jposes.FRAMES[fi][1](), x0, y0, x1, y1))
