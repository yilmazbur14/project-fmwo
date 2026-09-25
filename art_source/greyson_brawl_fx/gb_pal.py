"""Palette and grid helpers for Greyson's FINAL BRAWL effects (APPROVED 2026-09-24, see APPROVED.md).

House FX conventions, as Matt's effects (art_source/matt_fx/mfx_pal.py) set them: no keyline, hard
edges, no dither, and the only partial alpha is a few fixed steps. Nothing is rotated in the engine: a
chunk tumbles by swapping drawn frames, and every direction is its own frame.

Where every colour comes from (none is invented):
  dust / concrete  the house dust ramp, measured from Josh's shipped card_giant_impact plume and used by
                   Matt's stomp dust: #FBF7EE #EDE4D6 #C7BBAB #948779 #6B6157. Concrete IS that dust, so
                   the chunks are drawn in it, with #332B2B (measured from arena_ringside.png, its warm
                   near-black) for the crevices and the underside contact.
  steel            Greyson's own cool greys, measured from greyson_redesign.png: #D5D9EC #9DA1C0 #3F3F52
                   #2A2A38.
  rust (rebar)     Greyson's hair-shade browns, same sheet: #C27434 #8C4522.
  dodge gold       the shared dodge tell's ramp, measured from Assets/Effects/dodge_tell.png (Carter's
                   gold): #FFFCE0 #FFE45C #FFC21E #D68A12. The hook arrows are dodges, so they speak it.
  badge disc       Greyson's darkest trunk purple, #391555, doing what Matt's #332F68 disc does for his.
  ground shadow    solid black; the code supplies the translucency with modulate, as matt_glass_shadow.
"""
import os
import sys

from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
_MATT = os.path.abspath(os.path.join(_HERE, '..', 'matt_fx'))
sys.path.insert(0, _MATT)

import mfx_dustlib as dustlib            # noqa: E402  (the house dust puff, lit top-left)


def hx(s, a=255):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


PAL = {
    'k': hx('000000'),
    # dust / concrete, light to dark (the keys mfx_dustlib.puff writes)
    '1': hx('FBF7EE'), '2': hx('EDE4D6'), '3': hx('C7BBAB'), '4': hx('948779'), '5': hx('6B6157'),
    'c': hx('332B2B'),
    # dust in two alpha steps, for trails and thinning clouds: 176 (e f m) and 96 (n g h)
    'e': hx('EDE4D6', 176), 'f': hx('C7BBAB', 176), 'm': hx('948779', 176),
    'n': hx('EDE4D6', 96), 'g': hx('C7BBAB', 96), 'h': hx('948779', 96),
    # steel
    'S': hx('D5D9EC'), 'T': hx('9DA1C0'), 'U': hx('3F3F52'), 'V': hx('2A2A38'),
    # rust
    'R': hx('C27434'), 'Q': hx('8C4522'),
    # dodge gold, light to dark, and the disc
    'L': hx('FFFCE0'), 'H': hx('FFE45C'), 'G': hx('FFC21E'), 'D': hx('D68A12'), 'P': hx('391555'),
    'W': hx('FFFFFF'),
    # the answered glow: the gold tint in two alpha steps
    'i': hx('FFE45C', 176), 'j': hx('FFE45C', 96),
    # whoosh / impact whites in alpha steps
    'w': hx('FFFFFF', 176), 'x': hx('D5D9EC', 176), 'y': hx('D5D9EC', 96), 'z': hx('9DA1C0', 96),
}


def blank(w, h):
    return [['.'] * w for _ in range(h)]


def put(g, x, y, k):
    if 0 <= y < len(g) and 0 <= x < len(g[0]):
        g[y][x] = k


def rows(g):
    return [''.join(r) for r in g]


def to_image(frame):
    h, w = len(frame), len(frame[0])
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y, row in enumerate(frame):
        for x, k in enumerate(row):
            if k != '.':
                px[x, y] = PAL[k]
    return im


def strip(frames):
    fh, fw = len(frames[0]), len(frames[0][0])
    im = Image.new('RGBA', (fw * len(frames), fh), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        assert len(fr) == fh and all(len(r) == fw for r in fr), 'frame %d is not %dx%d' % (i, fw, fh)
        im.paste(to_image(fr), (i * fw, 0))
    return im


def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    return {'colours': len(set(px)), 'alphas': sorted(set(c[3] for c in px))}


DUST_KEYS = '12345'
# a dust key at an alpha step: 0 opaque, 1 = 176, 2 = 96
_THIN = {1: {'1': 'e', '2': 'e', '3': 'f', '4': 'm', '5': 'm'},
         2: {'1': 'n', '2': 'n', '3': 'g', '4': 'h', '5': 'h'}}


def puff(g, cx, cy, r, fade=0, thin=0):
    """the house dust puff (mfx_dustlib), drawn on its own grid and laid over `g` where `g` is clear or
    is dust, at an alpha step: thin 0 opaque, 1 at 176, 2 at 96"""
    h, w = len(g), len(g[0])
    tmp = blank(w, h)
    dustlib.puff(tmp, cx, cy, r, fade)
    for y in range(h):
        for x in range(w):
            k = tmp[y][x]
            if k == '.':
                continue
            if thin:
                k = _THIN[thin][k]
            if g[y][x] == '.' or g[y][x] in DUST_KEYS or g[y][x] in 'efmngh':
                g[y][x] = k


def poly_fill(g, pts, k):
    """even-odd scanline fill at texel centres"""
    h, w = len(g), len(g[0])
    n = len(pts)
    for y in range(h):
        cy = y + 0.5
        xs = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= cy < y1) or (y1 <= cy < y0):
                xs.append(x0 + (cy - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            for x in range(w):
                if xs[i] <= x + 0.5 < xs[i + 1]:
                    g[y][x] = k
