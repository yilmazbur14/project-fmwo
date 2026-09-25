"""Pixel helpers for the pose pass: integer upscales that stay pixel art, re-rimming, palette locks
and the numbers every pose is held to.

The upscale is Scale2x (EPX), not NEAREST. NEAREST turns every 1-texel step of a curve into a
2x2 stair, which is the blocky look the old busts had; Scale2x rounds those steps back into
single-texel ones using only colours already in the sprite, and keeps a 1-texel keyline 2 texels
thick, so the black weight the sprite has survives the enlargement.
"""
import os
import sys
from collections import Counter

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", ".."))
CHARS = PROJ.replace("\\", "/") + "/Assets/Characters/"
CLEAR = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)


def load(path, box=None):
    im = Image.open(CHARS + path).convert("RGBA")
    return im.crop(box) if box else im


def rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgba(h):
    return rgb(h) + (255,)


def hexc(c):
    return "#%02X%02X%02X" % tuple(c[:3])


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def norm(im):
    """Binary alpha, and every transparent pixel the same (0,0,0,0) so Scale2x compares cleanly."""
    im = im.convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            px[x, y] = CLEAR if p[3] < 128 else (p[0], p[1], p[2], 255)
    return im


def scale2x(im):
    """EPX. Only colours already present; edges stay hard; 1-texel stairs stay 1-texel stairs."""
    im = norm(im)
    w, h = im.size
    src = im.load()
    out = Image.new("RGBA", (w * 2, h * 2), CLEAR)
    dst = out.load()

    def at(x, y):
        if 0 <= x < w and 0 <= y < h:
            return src[x, y]
        return CLEAR

    for y in range(h):
        for x in range(w):
            p = src[x, y]
            a, b, c, d = at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            e0 = a if (c == a and c != d and a != b) else p
            e1 = b if (a == b and a != c and b != d) else p
            e2 = c if (d == c and d != b and c != a) else p
            e3 = d if (b == d and b != a and d != c) else p
            dst[2 * x, 2 * y] = e0
            dst[2 * x + 1, 2 * y] = e1
            dst[2 * x, 2 * y + 1] = e2
            dst[2 * x + 1, 2 * y + 1] = e3
    return out


def nearest(im, k):
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


def palette(im):
    return sorted({hexc(q) for q in im.getdata() if q[3] > 128})


def ratio(im, key=(0, 0, 0)):
    px = im.load()
    op = hit = 0
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] > 128:
                op += 1
                if p[:3] == tuple(key):
                    hit += 1
    return 100.0 * hit / op if op else 0.0, hit, op


def numbers(im, key=(0, 0, 0)):
    pct, hit, op = ratio(im, key)
    return {"black": pct, "colours": len(palette(im)), "opaque": op}


def lock(im, allowed):
    """Snap every opaque pixel to the nearest allowed colour (perceptual weights)."""
    cols = [rgb(c) if isinstance(c, str) else tuple(c[:3]) for c in allowed]
    cache = {}
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            k = (r, g, b)
            v = cache.get(k)
            if v is None:
                v = min(cols, key=lambda c: (c[0] - r) ** 2 * 3 + (c[1] - g) ** 2 * 6 + (c[2] - b) ** 2)
                cache[k] = v
            px[x, y] = v + (255,)
    return im


def outline(im, color=BLACK):
    """1px keyline in the transparent pixels 4-adjacent to opaque ones."""
    w, h = im.size
    a = im.load()
    add = []
    for y in range(h):
        for x in range(w):
            if a[x, y][3] > 128:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and a[nx, ny][3] > 128:
                    add.append((x, y))
                    break
    for p in add:
        a[p] = color
    return im


def paste(dst, src, at):
    dst.alpha_composite(src, (int(at[0]), int(at[1])))
    return dst


def save_zoom(im, path, f=4, bg=(34, 32, 52, 255)):
    b = Image.new("RGBA", im.size, bg)
    b.alpha_composite(im)
    b.resize((im.width * f, im.height * f), Image.NEAREST).save(path)
