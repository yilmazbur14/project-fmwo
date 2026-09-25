"""Jordan's juggle sheet: shared base. Jordan v2 (approved 2026-09-24): thin, frail and greasy.

Builds on the approved v2 rig (art_source/jordan_v2, jv2_*: the stick body, the sack of a tee, the
greasy hair, the pallor skin) and the redesign rig it builds on (art_source/jordan_redesign), both
imported READ-ONLY with bytecode writing off. The few pieces of his fight rig the juggle uses (its
expression rows, its hand, its box placement, its sheet writer) are frozen in jj_snap, because that
rig (art_source/jordan_anims) is being reworked and must not change the juggle under it. Every module
here is named jj_* so none can shadow (or be shadowed by) theirs. Nothing here imports Matt's juggle
rig: both rigs share josh_redesign/lib.py, and Matt's palette hook would clash.

v2 keeps the approved face, the Peach print, the sneakers and the box as they were, and v2's palette
is the approved 40 keys with the skin keys (a-e and the lip) re-coloured to the pallor ramp, so a
figure is still a key map and renders with jv2_base.PAL.

Two coordinate spaces:

  BUILD  the redesign rig's own coordinates (jordan.build): 96x96, the soles on row 95, light
         upper left. The finished rig frames shift x by ANCHOR_SHIFT (-1) so the body centres on
         column 48. Jordan is always BUILT here, upright, in the rig's own parts.
  FRAME  one juggle frame, 192x144 (the house's 2x wide, 1.5x tall). His feet stand on (96, 143)
         on the ground frames: build (x, y) -> frame (x - 1 + 48, y + 48).

A figure is a key map {(x, y): palette key}; keys are his approved 40 (jv2_base.ALLOWED).
Nothing here writes into Assets/.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
V2_DIR = os.path.join(ART, 'jordan_v2')
if V2_DIR not in sys.path:
    sys.path.insert(0, V2_DIR)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from PIL import Image         # noqa: E402

import jv2_base as V2B        # noqa: E402  the v2 rig: palette, audit (sets up the redesign rig)
import jv2_body as V2        # noqa: E402  its body parts
import jv2_head as V2H       # noqa: E402  its hair on the approved face
import jj_snap as S           # noqa: E402  the frozen fight-rig pieces

for _m in (V2B, V2, V2H):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(V2_DIR):
        raise ImportError('%s came from %s, not the v2 rig' % (_m.__name__, _m.__file__))
if os.path.normcase(os.path.dirname(os.path.abspath(S.__file__))) != os.path.normcase(HERE):
    raise ImportError('jj_snap came from %s' % S.__file__)
if any(m.startswith('janim_') for m in sys.modules):
    raise ImportError('the juggle must not import the fight rig (janim_*)')

jordan = S.jordan
kit = S.kit
lib = S.lib
PAL = V2B.PAL                 # v2: the approved keys, the skin keys re-coloured to the pallor ramp
ALLOWED = S.ALLOWED
APPROVED_V2 = os.path.join(os.path.dirname(ART), 'Assets', 'Characters', 'Jordan',
                           'jordan_redesign_v2.png')
pixel_diff = S.pixel_diff

ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan')
SCRATCH = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad', 'juggle', 'jordan')

W, H = 192, 144
FEET = (96, 143)
BUILD_TO_FRAME = (FEET[0] - 48 + S.ANCHOR_SHIFT, FEET[1] - 95)     # (47, 48)

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

# His key light, toward the light: the rig lights the left edge of every volume (rim -1, 0) and
# the top edge of the limbs (rim 0, -1): from the upper left.
LIGHT = (-math.sqrt(0.5), -math.sqrt(0.5))


def rot2(v, deg):
    """Rotate a 2D vector clockwise on screen (y down) by deg."""
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def image(px, w=W, h=H):
    return V2B.image(px, w, h)


def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(px):
    n = len(px)
    black = sum(1 for k in px.values() if k == 'k')
    return {'opaque': n, 'colours': len(set(px.values())), 'black': black / max(1, n)}


def strip(frames, w=W, h=H):
    out = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f if isinstance(f, Image.Image) else image(f, w, h), (w * i, 0))
    return out


def approved_sheet():
    return Image.open(APPROVED_V2).convert('RGBA')


def approved_colours():
    """Every colour on the approved jordan_redesign_v2.png: the 40."""
    return {c for c in flat(approved_sheet()) if c[3]}
