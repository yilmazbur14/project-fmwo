"""Jordan's finale cutscene pieces: shared base.

The Jordan frames are drawn in his approved v2 look (thin, frail, greasy: art_source/jordan_v2,
approved 2026-09-24), on the approved redesign rig (art_source/jordan_redesign) and the fight
animation rig (art_source/jordan_anims). All three are imported READ-ONLY: nothing here edits them,
and bytecode writing is switched off so importing them leaves no __pycache__ in their folders.

Every module in this folder is named jfc_*, so none of them can shadow (or be shadowed by) the
redesign rig's kit / head / torso / jordan, v2's jv2_*, the fight rig's janim_* or josh_redesign's lib.
The imports below are checked against the folders they must come from.

Jordan's frames are 96x96 like every sheet of his, rendered through v2's palette (the approved 40
keys, pallor skin). The player pieces are drawn in the player's own 7 colours at his 32x32 scale.
Nothing in this module writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
RIG = os.path.join(ART, 'jordan_redesign')
V2 = os.path.join(ART, 'jordan_v2')
ANIMS = os.path.join(ART, 'jordan_anims')
JOSH = os.path.join(ART, 'josh_redesign')
JORDAN_ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')
PLAYER_SHEET = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

for _p in (RIG, ART, V2, ANIMS):
    if _p not in sys.path:
        sys.path.append(_p)

import kit            # noqa: E402  the redesign rig's palette
import lib            # noqa: E402  josh_redesign/lib.py: Canvas, shapes, rim, amap
import jordan         # noqa: E402  the redesign rig: sneakers, fist, box, star
import head as rig_head    # noqa: E402  the approved face rows
import torso as rig_torso  # noqa: E402  the Peach print
import jv2_base       # noqa: E402  v2's palette (pallor skin)
import jv2_body       # noqa: E402  v2's thin body in the baggy tee
import jv2_head       # noqa: E402  v2's greasy hair
import jv2_frames     # noqa: E402  v2's two approved frames
import janim_heads    # noqa: E402  the fight rig's expressions over the approved face
from imgdiff import pixel_diff  # noqa: E402,F401
from PIL import Image, ImageDraw  # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == os.path.normcase(os.path.abspath(folder))


for _m, _d in ((kit, RIG), (jordan, RIG), (rig_head, RIG), (rig_torso, RIG), (lib, JOSH),
               (jv2_base, V2), (jv2_body, V2), (jv2_head, V2), (jv2_frames, V2), (janim_heads, ANIMS)):
    if not _same_dir(_m, _d):
        raise ImportError('%s was imported from %s, expected %s: a module-name clash' % (_m.__name__, _m.__file__, _d))

from kit import capsule  # noqa: E402,F401
from lib import (Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, stroke, dump, patch)  # noqa: E402,F401

W = H = 96                         # the approved rig's frame (his fight sheets)
FW = FH = 128                      # jordan_seated's frame (the coordinator's contract)
ANCHOR = (64, 127)                 # the chair's floor contact (front caster), his y-sort point
# The seated frames are composed straight in 128-frame pixels. Parts taken from the approved rig
# (built for its 96 frame) are moved by OFF, so the approved pixels keep their exact shapes.
OFF = (16, 32)
PAL = jv2_base.PAL                 # v2's palette: the approved 40 keys, the skin turned to pallor
ANCHOR_SHIFT = jordan.ANCHOR_SHIFT  # -1: the rigs' build x -> frame x
V2B, V2H, V2F, HD = jv2_body, jv2_head, jv2_frames, janim_heads

# The approved sheets' 40 colours, as palette keys. Nothing else may appear in a Jordan frame.
ALLOWED = set('01239ABDGNOPQRSTVWYabcdefghijklmnopqsvwx')
assert len(ALLOWED) == 40


#PART HELPERS

def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rows_of(rows):
    return [r.replace(' ', '') for r in rows]


def mirror(part, axis2):
    """Mirror a part about x = axis2 / 2 (axis2 = 2 * the axis, so half-pixel axes stay integer)."""
    return {(axis2 - x, y): k for (x, y), k in part.items()}


def span(pixels, y):
    xs = [x for (x, yy) in pixels if yy == y]
    return (min(xs), max(xs)) if xs else None


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def close_gaps(part):
    """Keyline any transparent spot a coloured pixel of `part` touches (4-neighbours), in place."""
    add = set()
    for (x, y), k in part.items():
        if k == 'k':
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in part:
                add.add(q)
    for q in add:
        part[q] = 'k'
    return part


def limb(segments, knobs=(), base='d', lit='e', shade='c'):
    """A thin limb, the way v2 draws his arms: capsules unioned into one shape, bony knobs at the
    joints, lit from the upper left, a shadow line along its underside. SKINNY since 2026-09-28, as the
    v2 rig (jv2_body.limb): callers pass the fitted build's radii and ARM_THIN comes off each segment's,
    KNOB_THIN off each knob's (only Jordan's arms are built with this)."""
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= capsule(p0, p1, max(V2B.MIN_R, r0 - V2B.ARM_THIN), max(V2B.MIN_R, r1 - V2B.ARM_THIN))
    for (cx, cy, r) in knobs:
        r = max(V2B.MIN_KNOB, r - V2B.KNOB_THIN)
        shape |= ellipse(cx, cy, r, r)
    part = fill(shape, base)
    rim(part, lit, -1, 0)
    rim(part, lit, 0, -1, only=base)
    rim(part, shade, 1, 0)
    rim(part, shade, 0, 1, only=base)
    return part


#RENDERING AND MEASURING

def image(px, w=FW, h=FH, pal=None):
    pal = pal or PAL
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), pal[k])
    return im


def stats(im):
    data = list(im.get_flattened_data())
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def audit(px, fx=(), allowed=ALLOWED, keyline='k'):
    """Problems a Jordan frame must not ship with (the fight rig's own checks):
      gaps   body-colour pixels touching transparency (a hole in the keyline)
      lone   pixels with no neighbour at all (stray specks)
      holes  transparent pixels boxed in on four sides (pinholes)
      keys   palette keys outside the approved 40
    `fx` lists pixels that are effects (steam, sparkles, speed lines): they float free by design."""
    fx = set(fx)
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if k != keyline and any(q not in px for q in n4):
            gaps.append((x, y, k))
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            lone.append((x, y, k))
    if px:
        x0, y0, x1, y1 = bbox(px)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                    holes.append((x, y))
    keys = sorted(set(px.values()) - set(allowed))
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


#PREVIEW HELPERS (images only; callers decide where they go)

BG = (46, 49, 58, 255)
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


#A SMALL 3D HELPER (used only to place things consistently across the turn; every part it
#produces is a template the frame builders shade and keyline like the rest of the rig)

# Oblique projection: verticals keep their full length, like every standing sprite in the game,
# and depth (toward the back of the room) climbs the screen at half rate, so the floor and the seat
# read as seen from above. World: x east (screen right), y north (away from the camera), z up.
KY = 0.5


def project(p, ox, oy):
    x, y, z = p
    return (ox + x, oy - z - KY * y)


def yaw_rot(p, deg):
    """Turn a chair-local point (x right, y forward, z up) so the chair faces `deg` clockwise from
    north (0 = facing away from the camera, 90 = facing screen-right, 180 = facing the camera)."""
    x, y, z = p
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    # local forward (0,1) -> (sin t, cos t); local right (1,0) -> (cos t, -sin t)
    return (x * c + y * s, -x * s + y * c, z)
