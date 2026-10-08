"""Preview helpers (scratch only)."""
from PIL import Image

BG = (120, 140, 120, 255)


def to_img(g):
    h, w = len(g), len(g[0])
    im = Image.new('RGBA', (w, h))
    im.putdata([tuple(p) for row in g for p in row])
    return im


def zoom(im, f, bg=BG, grid=0):
    b = Image.new('RGBA', im.size, bg)
    b.alpha_composite(im)
    z = b.resize((im.width * f, im.height * f), Image.NEAREST)
    if grid:
        px = z.load()
        for y in range(z.height):
            for x in range(z.width):
                if (x % (grid * f) == 0) or (y % (grid * f) == 0):
                    r, g_, b_, a = px[x, y]
                    px[x, y] = (max(0, r - 40), max(0, g_ - 40), max(0, b_ - 40), 255)
    return z


def strip(imgs, gap=4, bg=(70, 70, 80, 255)):
    w = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    h = max(i.height for i in imgs)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in imgs:
        out.alpha_composite(i, (x, 0))
        x += i.width + gap
    return out
