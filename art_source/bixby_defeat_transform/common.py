"""Shared paths, palette and image helpers for the defeat and transformation sheets.

The approved redesign rig (art_source/bixby_redesign) is imported READ-ONLY: this folder only adds new
modules on top of its stable parts (pal, shapes, heads, body, wings, midmaps, sidemaps, frame).
Nothing here writes into Assets/ unless export.py is run with --write.
"""
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
REDESIGN = os.path.join(ART, 'bixby_redesign')
for p in (REDESIGN, ART, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image  # noqa: E402

import pal as RP  # noqa: E402  (bixby_redesign/pal.py)

BIXBY = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby')
LIAM = os.path.join(ROOT, 'Assets', 'Characters', 'Liam')
SCRATCH = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
           'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_redesign/defeat_transform/')
WORK = SCRATCH + 'work/'
ASEPRITE = r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe'

PAL = dict(RP.PAL)
BLACK = (0, 0, 0, 255)
CLEAR = (0, 0, 0, 0)

# The sheets as the game reads them (Scripts/BixbyBeastArtLayout.gd, Scripts/LiamEntranceLayout.gd).
BEAST_FW, BEAST_FH = 192, 160
BEAST_ANCHOR = (96, 151)
HOVER_HEIGHT = 40
TW, TH = 320, 256
T_ANCHOR = (160, 251)
# a 192x160 beast frame's top-left inside a 320x256 transformation frame, standing (lift 0)
BEAST_IN_T = (T_ANCHOR[0] - BEAST_ANCHOR[0], T_ANCHOR[1] - BEAST_ANCHOR[1])      # (64, 100)
DEFEAT_TIMES = [0.1, 0.3, 0.16, 0.14, 0.6, 0.34, 0.12, 0.12, 0.4, 1.0]
DEFEAT_LIAM_LANDS_FRAME = 8
TRANSFORM_TIMES = [0.26, 0.12, 0.22, 0.15, 0.15, 0.13, 0.2, 0.09, 0.09, 0.11, 0.15, 0.15, 0.15,
                   0.15, 0.22, 0.09, 0.09, 0.24, 0.12, 0.26, 0.09, 0.11, 0.2, 0.18, 0.18, 0.4]
AURA_FRAME_TIME = 0.09
SHOCKWAVE_FRAME_TIME = 0.06


def asset(name):
    return os.path.join(BIXBY, name)


def load(path):
    return Image.open(path).convert('RGBA')


def cells(im, fw, fh, cols=None, rows=None):
    """Split a sheet into frames, read left to right, top to bottom."""
    cols = cols or im.width // fw
    rows = rows or im.height // fh
    return [im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh)) for r in range(rows) for c in range(cols)]


def grid_sheet(frames, cols):
    fw, fh = frames[0].size
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGBA', (fw * cols, fh * rows), CLEAR)
    for i, f in enumerate(frames):
        out.paste(f, ((i % cols) * fw, (i // cols) * fh))
    return out


def rgba(k):
    """A palette key or a raw RGBA tuple."""
    return PAL[k] if isinstance(k, str) else k


def to_image(px, w, h, ox=0, oy=0):
    """A key dict {(x, y): key-or-rgba} drawn onto a w x h transparent image, shifted by (ox, oy)."""
    im = Image.new('RGBA', (w, h), CLEAR)
    put = im.putpixel
    for (x, y), k in px.items():
        X, Y = x + ox, y + oy
        if 0 <= X < w and 0 <= Y < h:
            put((X, Y), rgba(k))
    return im


INV = {v: k for k, v in PAL.items()}


def to_keys(im, ox=0, oy=0):
    """Image back to a key dict; colours outside the palette stay as RGBA tuples."""
    out = {}
    w, h = im.size
    data = im.load()
    for y in range(h):
        for x in range(w):
            c = data[x, y]
            if c[3]:
                out[(x + ox, y + oy)] = INV.get(c, c)
    return out


def over(dst, src, ox=0, oy=0):
    """Paste src over dst (both images); alpha is 0/255 so this is a plain overwrite of opaque pixels."""
    dst.alpha_composite(src, (ox, oy))
    return dst


def shift(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


def outer_edge(mask, diag=False):
    """Pixels just outside a mask (4-neighbour, or 8 with diag)."""
    ds = ((1, 0), (-1, 0), (0, 1), (0, -1))
    if diag:
        ds += ((1, 1), (1, -1), (-1, 1), (-1, -1))
    out = set()
    for (x, y) in mask:
        for dx, dy in ds:
            q = (x + dx, y + dy)
            if q not in mask:
                out.add(q)
    return out


def inner_edge(mask):
    out = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in mask:
                out.add((x, y))
                break
    return out


def measure(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    cnt = Counter(px)
    black = cnt.get(BLACK, 0)
    semi = sum(1 for c in px if c[3] < 255)
    return dict(opaque=len(px), colours=len(cnt), black=round(100.0 * black / max(1, len(px)), 2), semi=semi,
                bbox=im.getbbox())


def colours(im):
    flat = getattr(im, 'get_flattened_data', None)
    return set(c for c in (flat() if flat else im.getdata()) if c[3] > 0)


def on_bg(im, bg=(46, 49, 58, 255)):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def zoom_save(im, name, s=4, box=None, bg=(46, 49, 58, 255)):
    if box:
        im = im.crop(box)
    up(on_bg(im, bg), s).save(WORK + name)
    return WORK + name


class Rng:
    """A small deterministic generator (so every re-run draws the same sparks)."""

    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0xFFFFFFFF

    def __call__(self):
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def range(self, a, b):
        return a + (b - a) * self()

    def int(self, a, b):
        return int(a + (b - a + 1) * self()) if b > a else a
