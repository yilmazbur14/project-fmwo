"""Jordan redesign v2 (thin, frail, greasy): shared base.

Imports the approved redesign rig (art_source/jordan_redesign) READ-ONLY and builds on it: the face
rows, the Peach print, the shoes, the collector box, the fist, the pop cloud and star are the
approved rig's own maps, used as they are. What v2 redraws is the body (a skeletal, gangly frame in a
baggy tee) and the hair (greasy, stringy, clumped). Bytecode writing is off so importing the rig
leaves no __pycache__ behind in its folder.

Every module here is named jv2_*, so none can shadow (or be shadowed by) the rig's kit / head / torso
/ jordan / previews, josh_redesign's lib / export, or jordan_anims' janim_*.

Coordinates are the rig's BUILD coordinates; a finished frame is shifted by the rig's ANCHOR_SHIFT
(-1 in x) so the body centres on column 48, with the soles on row 95. Nothing here writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'jordan_redesign')
JOSH = os.path.join(ART, 'josh_redesign')
ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')
APPROVED_PNG = os.path.join(ASSETS, 'jordan_redesign.png')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

for _p in (RIG, ART):
    if _p not in sys.path:
        sys.path.append(_p)

import kit            # noqa: E402  the rig's palette and renderer
import lib            # noqa: E402  josh_redesign/lib.py, via kit's own path setup
import jordan         # noqa: E402  the rig's parts and the two approved frames
import head as rig_head    # noqa: E402
import torso as rig_torso  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == os.path.normcase(os.path.abspath(folder))


for _m, _d in ((kit, RIG), (jordan, RIG), (rig_head, RIG), (rig_torso, RIG), (lib, JOSH)):
    if not _same_dir(_m, _d):
        raise ImportError('%s was imported from %s, expected %s: a module-name clash' % (_m.__name__, _m.__file__, _d))

from lib import (Canvas, amap, dump, ellipse, fill, line, paint, patch, poly, rect, rim, stroke)  # noqa: E402,F401

W = H = 96
ANCHOR_SHIFT = jordan.ANCHOR_SHIFT          # -1: build x -> frame x

# The approved sheet's 40 colours, as palette keys. Nothing else may appear in a frame.
ALLOWED = set('01239ABDGNOPQRSTVWYabcdefghijklmnopqsvwx')
assert len(ALLOWED) == 40


#PALETTE

def hx(s):
    return kit.hx(s)


# The skin ramp, same five steps and the lip, pushed toward a sickly pallor: paler and less
# saturated, the lights a touch sallow (yellower), the shadows greyer and cooler, so he reads
# unwell while staying in his light-olive family. JV2_PALLOR=0 renders the approved skin instead.
PALLOR_SKIN = {
    'a': hx('4E3A33'), 'b': hx('7D6353'), 'c': hx('AA9173'), 'd': hx('CDB694'), 'e': hx('E7D8B6'),
    'p': hx('9A6558'),
}
PALLOR = os.environ.get('JV2_PALLOR', '1') != '0'

APPROVED_PAL = dict(kit.PAL)
PAL = dict(kit.PAL)
if PALLOR:
    PAL.update(PALLOR_SKIN)


#PART HELPERS

def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rows_of(rows):
    return [r.replace(' ', '') for r in rows]


def capsule(p0, p1, r0, r1):
    return kit.capsule(p0, p1, r0, r1)


def span(pixels, y):
    xs = [x for (x, yy) in pixels if yy == y]
    return (min(xs), max(xs)) if xs else None


def vspan(pixels, x):
    ys = [y for (xx, y) in pixels if xx == x]
    return (min(ys), max(ys)) if ys else None


def finish(px):
    """Build coordinates -> frame coordinates (the rig's anchor shift), clipped to the frame."""
    out = {}
    for (x, y), k in px.items():
        q = (x + ANCHOR_SHIFT, y)
        if 0 <= q[0] < W and 0 <= q[1] < H:
            out[q] = k
    return out


def image(px, w=W, h=H, pal=None):
    """Render keys with v2's palette (or `pal`, e.g. APPROVED_PAL to see the approved skin)."""
    pal = pal or PAL
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), pal[k])
    return im


#MEASURING

def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def audit(px, fx=()):
    """Problems a frame must not ship with:
      gaps   body-colour pixels touching transparency (a hole in the keyline)
      lone   pixels with no neighbour at all (stray specks)
      holes  transparent pixels boxed in on four sides (pinholes: the floor showing through)
      keys   palette keys outside the approved 40
    `fx` lists pixels that are effects (glints) and so float free by design."""
    fx = set(fx)
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if k != 'k' and any(q not in px for q in n4):
            gaps.append((x, y, k))
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            lone.append((x, y, k))
    x0, y0, x1, y1 = bbox(px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                holes.append((x, y))
    keys = sorted(set(px.values()) - ALLOWED)
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


#PREVIEW HELPERS (images only; callers decide where they go)

BG = kit.BG
DARK = (10, 10, 12, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def grid(im, s, major=5):
    return lib.grid(im, s, major=major)


def row(ims, gap=8, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def label(im, text, pad=18, col=(220, 220, 228, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=col)
    return out
