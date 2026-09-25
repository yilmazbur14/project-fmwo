"""The cone's right edge as the code will build it: flood tiles clipped below the slanted edge line,
edge pieces laid along the line on top, every looping piece one frame ahead of the last. Over the mat."""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import edge  # noqa: E402
import flood  # noqa: E402
import pal  # noqa: E402
from tiletest import MAT  # noqa: E402


def render(flood_loop, edge_loop, w=192, h=120, line_at=(0, 18), step=0, scale=3, alpha=1.0, mat=True):
    """w x h texels. The edge line passes through texel line_at and falls 7 rows per 15 columns."""
    lx, ly = line_at

    def cone_row(x):          # first row inside the cone at column x
        return ly + (2 * edge.RISE * (x - lx) + edge.RUN) // (2 * edge.RUN)

    fl = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    tiles = [pal.to_image(f) for f in flood_loop]
    i = 0
    for r in range(-1, h // 29 + 2):
        for c in range(0, w // 57 + 2):
            im = tiles[(step + i) % len(tiles)]
            fl.alpha_composite(im, (c * 57, r * 29 - 12)) if r * 29 - 12 >= 0 else _paste_clip(fl, im, c * 57, r * 29 - 12)
            i += 1
    px = fl.load()
    for y in range(h):
        for x in range(w):
            if y < cone_row(x):
                px[x, y] = (0, 0, 0, 0)
    pieces = [pal.to_image(f) for f in edge_loop]
    k = 0
    x0 = lx - ((lx) // edge.W + 1) * edge.W
    while x0 < w:
        y0 = cone_row(x0) - edge.LINE_Y0
        _paste_clip(fl, pieces[(step + k) % len(pieces)], x0, y0)
        x0 += edge.W
        k += 1
    if alpha < 1.0:
        fl.putalpha(fl.getchannel('A').point(lambda v: int(v * alpha)))
    if mat:
        m = Image.open(MAT).convert('RGBA')
        bg = Image.new('RGBA', (w, h))
        for yy in range(0, h, m.height):
            for xx in range(0, w, m.width):
                bg.paste(m, (xx, yy))
        bg.alpha_composite(fl)
        fl = bg
    return fl.resize((w * scale, h * scale), Image.NEAREST)


def _paste_clip(dst, im, x, y):
    """alpha_composite that tolerates negative offsets."""
    sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height:
        return
    part = im.crop((sx, sy, im.width, im.height))
    dst.alpha_composite(part, (max(0, x), max(0, y)))


if __name__ == '__main__':
    from view import save
    fr = flood.frames()
    er = edge.frames()
    which = sys.argv[1:] or ['burn']
    loops = {'smoulder': (fr[0:2], er[0:2], 1.0), 'faint': (fr[0:2], er[0:2], 0.45), 'burn': (fr[4:8], er[4:8], 1.0)}
    for name in which:
        if name in loops:
            a, b, al = loops[name]
            print(save(render(a, b, alpha=al), 'cone_edge_%s_x3.png' % name))
        elif name.startswith('f'):
            i = int(name[1:])
            print(save(render([fr[i]], [er[i]]), 'cone_edge_%s_x3.png' % name))
