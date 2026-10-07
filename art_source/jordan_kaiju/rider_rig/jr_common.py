"""Jordan's kaiju-fight sheets (the rider and the mat poses): shared base. SCRATCH ONLY.

Everything here imports Jordan's rigs from a COPY in this folder (vendor/art_source/...: jordan_anims,
jordan_v2, jordan_redesign, josh_redesign/lib.py, imgdiff.py, copied 2026-10-04 with their sha256 in
vendor_sha256.txt), never the live art_source. The copy's Assets folder (vendor/Assets/...) holds
read-only copies of the approved PNGs it checks against, so every path the rigs compute resolves inside
this scratch folder: nothing here can reach the live Assets tree. Bytecode writing is off.

Modules here are named jr_*, so none shadows the rigs' janim_* / jv2_* / kit / lib / jordan / head.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RIDER = os.path.dirname(HERE)                         # scratchpad/jordan_kaiju/rider
KAIJU = os.path.dirname(RIDER)                        # scratchpad/jordan_kaiju
VENDOR = os.path.join(HERE, 'vendor')
VART = os.path.join(VENDOR, 'art_source')
ANIMS = os.path.join(VART, 'jordan_anims')
LIVE_PROJECT = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
LIVE_JORDAN = os.path.join(LIVE_PROJECT, 'Assets', 'Characters', 'Jordan')     # READ ONLY
APPROVAL = os.path.join(KAIJU, 'approval')
LOOK = os.path.join(RIDER, 'look')
ASEPRITE = r'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'

if ANIMS not in sys.path:
    sys.path.insert(0, ANIMS)

import janim_base as JB   # noqa: E402
import janim_heads as JH  # noqa: E402
import janim_box as JBX   # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402


def _inside(path, root):
    p, r = os.path.normcase(os.path.realpath(path)), os.path.normcase(os.path.realpath(root))
    return p == r or p.startswith(r + os.sep)


for _m in (JB, JH, JBX, JB.kit, JB.lib, JB.jordan, JB.jv2_base, JB.jv2_body, JB.jv2_head, JB.jv2_frames):
    if not _inside(_m.__file__, VENDOR):
        raise ImportError('%s came from %s, not the scratch copy' % (_m.__name__, _m.__file__))
if not _inside(JB.ASSETS, VENDOR):
    raise ImportError('the rig copy points its Assets at %s' % JB.ASSETS)

lib = JB.lib
Canvas = lib.Canvas
amap, ellipse, fill, poly, rim, stroke, line = lib.amap, lib.ellipse, lib.fill, lib.poly, lib.rim, lib.stroke, lib.line
V = JB.V2B
PAL = JB.PAL
ALLOWED = JB.ALLOWED
FX_KEYS = JB.FX_KEYS
pixel_diff = JB.pixel_diff
W = H = 96


def guard_out(path):
    """Every file this rig writes goes through here: it must land inside the rider scratch folder."""
    if not _inside(path, RIDER):
        raise SystemExit('refusing to write %s: outside %s' % (path, RIDER))
    if _inside(path, os.path.join(LIVE_PROJECT, 'Assets')):
        raise SystemExit('refusing to write into the live Assets: %s' % path)
    return path


def render(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PAL[k])
    return im


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(im):
    data = flat(im)
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


BG = (46, 49, 58, 255)
MAT = (136, 180, 99, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def look(im, name, s=6, bg=BG):
    os.makedirs(LOOK, exist_ok=True)
    p = guard_out(os.path.join(LOOK, name))
    up(im, s, bg).save(p)
    return p


def live_sheet(name):
    return Image.open(os.path.join(LIVE_JORDAN, name + '.png')).convert('RGBA')


def approved_colours():
    """The approved v2 sheet's 40 colours (read from the live jordan_redesign_v2.png)."""
    return {c for c in flat(live_sheet('jordan_redesign_v2')) if c[3]}
