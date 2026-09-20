"""Shared method for the VS-card busts: crop from the sprite, scale, re-rim, detail.

This is the pass that finally made Eric read as himself. Two hand-drawn attempts
missed because I was re-drawing a 28px head at 42px and losing the character in
the rescale. The fix was to stop drawing the base at all:

  1. crop the character's OWN pixels around their centreline
  2. scale by an INTEGER factor chosen so the figure fills a 116x120 bust
  3. rim_light(): a ONE-pixel lit edge wherever a material meets its keyline and
     a one-pixel dark edge underneath. An Nx upscale has Nx-wide edges; re-rimming
     at 1px is detail that cannot exist at source scale, and it is the same
     top-lit / dark-underside language the sprites are built from.
  4. hand detail the source has no room for
  5. lock() to the source's own palette (plus any tones deliberately added)

measure() prints black% and colour count against the source sheet on every
build. That number is the check - it is what caught the first two attempts.
"""
import os
from collections import Counter
from PIL import Image

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
CH = PROJ + "/Assets/Characters/"
W, H = 116, 120


def _rgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _hex(c):
    return "#%02X%02X%02X" % c[:3]


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def frame(path, box=None):
    """One source frame, cropped tight to its ink."""
    im = Image.open(CH + path).convert("RGBA")
    if box:
        im = im.crop(box)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def raw(path, box=None):
    im = Image.open(CH + path).convert("RGBA")
    return im.crop(box) if box else im


def palette_of(im):
    return sorted({_hex(q) for q in im.getdata() if q[3] > 128})


def keyline_of(im):
    """The darkest colour carrying real area - not every sprite uses pure black
    (Computah's keyline is #0C111A), so the black check has to ask the sheet."""
    c = Counter(q[:3] for q in im.getdata() if q[3] > 128)
    tot = sum(c.values())
    dark = [k for k in c if _lum(k) < 40 and c[k] >= tot * 0.02]
    return _hex(min(dark, key=_lum)) if dark else "#000000"


def key_ratio(im, key="#000000"):
    k = _rgb(key)
    px = im.load()
    op = hit = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 128:
                op += 1
                if (r, g, b) == k:
                    hit += 1
    return hit, op, (100.0 * hit / op if op else 0.0)


def place(dst, src, crop, scale, at):
    """Crop a region of a source frame, scale it by an integer, paste it in."""
    piece = src.crop(crop)
    piece = piece.resize((piece.width * scale, piece.height * scale), Image.NEAREST)
    dst.alpha_composite(piece, at)
    return dst


def bust_from(src, crop, scale, at=(0, 0)):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return place(im, src, crop, scale, at)


def rim_light(im, group, hi, sh):
    """1px lit edge where a material meets its keyline, 1px dark edge under it."""
    g = {_rgb(c) for c in group}
    if not g:
        return
    px = im.load()
    hi_rgb, sh_rgb = _rgb(hi), _rgb(sh)
    todo = []
    for y in range(im.height):
        for x in range(im.width):
            r, gg, b, a = px[x, y]
            if a < 128 or (r, gg, b) not in g:
                continue
            up = px[x, y - 1] if y > 0 else (0, 0, 0, 0)
            dn = px[x, y + 1] if y < im.height - 1 else (0, 0, 0, 0)
            if up[3] < 128 or up[:3] not in g:
                todo.append((x, y, hi_rgb))
            elif dn[3] < 128 or dn[:3] not in g:
                todo.append((x, y, sh_rgb))
    for x, y, c in todo:
        px[x, y] = (c[0], c[1], c[2], 255)


def rim_all(im, groups):
    """Re-rim every material. Each group is sorted by luminance here, so the
    caller does not have to remember which palette lists run light-first."""
    for grp in groups:
        g = sorted(set(grp), key=lambda c: _lum(_rgb(c)))
        if len(g) >= 2:
            rim_light(im, g, g[-1], g[0])


def lock(im, allowed):
    cols = [_rgb(c) for c in allowed]
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
            px[x, y] = (v[0], v[1], v[2], 255)
    return im


def measure(name, bust, src):
    """Print the bust's keyline ratio and colour count against its source."""
    key = keyline_of(src)
    _, _, spct = key_ratio(src, key)
    scols = len(palette_of(src))
    _, _, bpct = key_ratio(bust, key)
    bcols = len(palette_of(bust))
    note = "" if key == "#000000" else "  (keyline %s, this sheet has no pure black)" % key
    print("%-9s bust %5.1f%% / %2d colours   sprite %5.1f%% / %2d%s"
          % (name, bpct, bcols, spct, scols, note))
    return bpct, bcols, spct, scols
