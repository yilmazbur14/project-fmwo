"""python jj_view.py [scale] [--upright] [frame indices...]  - the juggle frames as a grid in the
scratchpad, frame edge magenta, feet row and column cyan. --upright shows every pose unturned and
standing on the mat, to check how it is put together. Writes only into the scratchpad."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jj_base as J  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def grid(frames, names, f=4, cols=4, bg=None):
    w, h = J.W * f, J.H * f
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (cols * w, rows * h), (34, 34, 44, 255))
    for i, (px, name) in enumerate(zip(frames, names)):
        cell = Image.new('RGBA', (J.W, J.H))
        c = cell.load()
        for y in range(J.H):
            for x in range(J.W):
                v = 62 if (x + y) % 2 == 0 else 50
                c[x, y] = bg or (v, v, v, 255)
        cell.alpha_composite(J.image(px))
        big = cell.resize((w, h), Image.NEAREST)
        d = ImageDraw.Draw(big)
        d.rectangle([0, 0, w - 1, h - 1], outline=(170, 40, 170, 255))
        d.line([0, J.FEET[1] * f + f - 1, w, J.FEET[1] * f + f - 1], fill=(60, 220, 230, 255))
        d.line([J.FEET[0] * f, h - 3 * f, J.FEET[0] * f, h], fill=(60, 220, 230, 255))
        d.text((4, 2), '%d %s' % (i, name), fill=(255, 255, 255, 255))
        out.paste(big, ((i % cols) * w, (i // cols) * h))
    return out


def main():
    import jj_poses as MP
    import jj_build as MB
    args = sys.argv[1:]
    upright = '--upright' in args
    args = [a for a in args if a != '--upright']
    f = int(args[0]) if args else 4
    want = [int(a) for a in args[1:]] or list(range(len(MP.FRAMES)))
    frames, names = [], []
    for i in want:
        if upright:
            spec = MP.FRAMES[i]()
            spec.theta, spec.ground, spec.flatten, spec.seat, spec.lift = 0, True, 1.0, None, 0
            px, _ = MP.render(spec)
            frames.append(px)
            names.append(spec.name + ' (upright)')
        else:
            b = MB.frame(i)
            frames.append(b.px)
            names.append(b.name)
    im = grid(frames, names, f)
    os.makedirs(J.SCRATCH, exist_ok=True)
    p = os.path.join(J.SCRATCH, 'work', 'view_%dx%s.png' % (f, '_upright' if upright else ''))
    im.save(p)
    print('wrote', p, im.size)


if __name__ == '__main__':
    main()
