"""Jordan's kaiju mount, approval pass: shared base (scratch rig, never writes into the project).

Imports Jordan's live rigs READ-ONLY (art_source/jordan_anims -> jordan_v2 -> jordan_redesign ->
josh_redesign/lib), with bytecode writing off so nothing lands in their folders. Every module here is
named kj_* so nothing can shadow theirs.

Palette: Jordan's approved 40 keys (v2 palette, pallor skin) plus the kaiju's own keys, which are
characters Jordan's rig never uses.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.path.dirname(HERE)
OUT = os.path.join(SCRATCH, 'approval')
LOOK = os.path.join(SCRATCH, 'look')
PROJECT = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
ART = os.path.join(PROJECT, 'art_source')
ANIMS = os.path.join(ART, 'jordan_anims')
ASSETS_JORDAN = os.path.join(PROJECT, 'Assets', 'Characters', 'Jordan')
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'

if ANIMS not in sys.path:
    sys.path.append(ANIMS)

import janim_base as JB  # noqa: E402
import janim_heads as JH  # noqa: E402
import janim_box as JBX  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

for _m in (JB, JH, JBX):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(os.path.abspath(ANIMS)):
        raise ImportError('module clash: %s from %s' % (_m.__name__, _m.__file__))

lib = JB.lib
Canvas = lib.Canvas
amap, ellipse, fill, poly, rim, stroke, line = lib.amap, lib.ellipse, lib.fill, lib.poly, lib.rim, lib.stroke, lib.line
JORDAN_KEYS = set(JB.ALLOWED)


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# The kaiju's own colours. Ramps dark -> light; lit from the upper left like the cast.
KAIJU_PAL = {
    # hide: a dark slate-teal vinyl (charcoal with a cool cast, so it stands off the green mat)
    '#': hx('0B1416'), '%': hx('152829'), '&': hx('213D3F'), '@': hx('2F5454'), '+': hx('467570'),
    '=': hx('689A8F'), '~': hx('ACD6C9'),
    # belly scutes: muted sand
    'C': hx('5B5545'), 'E': hx('847A5E'), 'F': hx('AA9F7A'), 'H': hx('CEC39B'),
    # dorsal plates and claws: bone
    '4': hx('5E5B50'), '5': hx('8F8975'), '6': hx('BDB59B'), '7': hx('E6DEC4'),
    # the atomic glow
    '8': hx('1B3AB4'), 'I': hx('2D7BF0'), 'J': hx('5CC9FF'), 'K': hx('B8F1FF'), 'X': hx('FFFFFF'),
}
PAL = dict(JB.PAL)
for _k, _v in KAIJU_PAL.items():
    assert _k not in PAL, _k
    PAL[_k] = _v
KAIJU_KEYS = set(KAIJU_PAL)
GLOW_KEYS = set('8IJKX')


def render(px, w, h, pal=None):
    pal = pal or PAL
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    put = im.putpixel
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            put((x, y), pal[k])
    return im


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
    """gaps: body pixels touching transparency (holes in the keyline); lone: isolated specks;
    holes: transparent pixels boxed in on four sides; keys: unknown palette keys."""
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
    keys = sorted(set(px.values()) - set(PAL))
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


BG = (46, 49, 58, 255)
MAT = (136, 180, 99, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def look(im, name, s=4, bg=BG):
    os.makedirs(LOOK, exist_ok=True)
    p = os.path.join(LOOK, name)
    up(im, s, bg).save(p)
    return p
