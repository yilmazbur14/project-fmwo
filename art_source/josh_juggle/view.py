"""python view.py [scale] [frame indices...]  - frames as a grid on a dark ground, frame borders and
the feet row marked, written to the scratch preview folder (never into Assets)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import poses as PZ                # noqa: E402
import jparts as P                # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SCRATCH = os.environ.get('JUGGLE_PREVIEW', os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project',
    r'a7fc2846-afef-472d-979b-e17143793a0f\scratchpad\juggle\josh'))


def image(px):
    im = Image.new('RGBA', (PZ.W, PZ.H), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < PZ.W and 0 <= y < PZ.H:
            im.putpixel((x, y), P.PAL[k])
    return im


def grid(frames, s=4, cols=4, names=None):
    rows = (len(frames) + cols - 1) // cols
    cw, ch = PZ.W * s + 6, PZ.H * s + 18
    out = Image.new('RGBA', (cols * cw, rows * ch), (24, 25, 31, 255))
    d = ImageDraw.Draw(out)
    for i, px in enumerate(frames):
        ox, oy = (i % cols) * cw, (i // cols) * ch
        cell = Image.new('RGBA', (PZ.W, PZ.H), (46, 49, 58, 255))
        cell.alpha_composite(image(px))
        big = cell.resize((PZ.W * s, PZ.H * s), Image.NEAREST)
        out.alpha_composite(big, (ox, oy + 14))
        d.rectangle((ox, oy + 14, ox + PZ.W * s - 1, oy + 14 + PZ.H * s - 1), outline=(120, 60, 140, 255))
        d.line((ox, oy + 14 + PZ.FEET[1] * s, ox + PZ.W * s - 1, oy + 14 + PZ.FEET[1] * s),
               fill=(60, 200, 210, 255))
        d.text((ox + 4, oy + 1), '%d %s' % (i, names[i] if names else ''), fill=(220, 220, 230, 255))
    return out


if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    want = [int(a) for a in sys.argv[2:]] or list(range(len(PZ.FRAMES)))
    frames = [PZ.FRAMES[i][1]() for i in want]
    os.makedirs(SCRATCH, exist_ok=True)
    path = os.path.join(SCRATCH, 'wip_%dx.png' % s)
    grid(frames, s, cols=min(4, len(frames)), names=[PZ.FRAMES[i][0] for i in want]).save(path)
    print('wrote', path)
