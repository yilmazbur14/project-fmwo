"""python mj_view.py [scale] [frame indices...]  - the juggle frames as a grid in the scratchpad,
with the frame edge (magenta), the feet row and column (cyan) and the air pivot (yellow) marked.
Writes only into the scratchpad (mj_base.SCRATCH)."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mj_base as J  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

GUIDE = (170, 40, 170, 255)
FEET = (60, 220, 230, 255)
PIV = (240, 220, 40, 255)


def grid(frames, names, f=4, cols=4, marks=True, bg=None):
    w, h = J.W * f, J.H * f
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (cols * w, rows * h), (34, 34, 44, 255))
    for i, (px, name) in enumerate(zip(frames, names)):
        cell = Image.new('RGBA', (J.W, J.H))
        c = cell.load()
        for y in range(J.H):
            for x in range(J.W):
                if bg:
                    c[x, y] = bg
                else:
                    v = 62 if (x + y) % 2 == 0 else 50
                    c[x, y] = (v, v, v, 255)
        cell.alpha_composite(J.image(px))
        big = cell.resize((w, h), Image.NEAREST)
        d = ImageDraw.Draw(big)
        if marks:
            d.rectangle([0, 0, w - 1, h - 1], outline=GUIDE)
            d.line([0, J.FEET[1] * f + f - 1, w, J.FEET[1] * f + f - 1], fill=FEET)
            d.line([J.FEET[0] * f, h - 3 * f, J.FEET[0] * f, h], fill=FEET)
        d.text((4, 2), '%d %s' % (i, name), fill=(255, 255, 255, 255))
        out.paste(big, ((i % cols) * w, (i // cols) * h))
    return out


def main():
    import mj_poses as MP
    import mj_build as MB
    f = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    want = [int(a) for a in sys.argv[2:]] or list(range(len(MP.FRAMES)))
    built = [MB.frame(i) for i in want]
    im = grid([b.px for b in built], [b.name for b in built], f)
    os.makedirs(J.SCRATCH, exist_ok=True)
    p = os.path.join(J.SCRATCH, 'view_%dx.png' % f)
    im.save(p)
    print('wrote', p, im.size)


if __name__ == '__main__':
    main()
