"""Matt's juggle sheet: shared base.

Builds on the fight rig (art_source/matt_fight, mf_*), which builds on the intro rig
(art_source/matt_intro, mi_*), which builds on the approved rig (art_source/matt). All three are
imported READ-ONLY with bytecode writing off, so importing leaves nothing behind in their folders.
Every module here is named mj_* so none can shadow (or be shadowed by) theirs.

Two coordinate spaces:

  LOCAL  the rig's own 96x96 frame: feet on row 95, column 48 the mirror axis, light upper left.
         Matt is always BUILT here, upright, exactly as the approved sheets build him.
  FRAME  one juggle frame, 192x144 (the house's 2x wide, 1.5x tall, as Mason 64->128x96 and
         Eric 128->256x192). His feet stand on (96, 143) on the ground frames.

A figure is a key map {(x, y): palette key}; keys are Matt's approved 41 (pal.PAL). Nothing here
writes into Assets/.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
FIGHT = os.path.join(ART, 'matt_fight')
if FIGHT not in sys.path:
    sys.path.insert(0, FIGHT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mf_base as MF                 # noqa: E402  (sets up the intro rig and the approved rig)
from mf_base import B, A, G, F, H as HANDS, L, PZ   # noqa: E402,F401
import mf_faces as FF                # noqa: E402,F401
import mf_recover as MR              # noqa: E402,F401
from PIL import Image                # noqa: E402

matt = B.matt
sh = B.sh
details = B.details
rig_face = B.rig_face
pal = B.pal
PAL = B.PAL
ALLOWED = B.ALLOWED
DARKER, LIGHTER = B.DARKER, B.LIGHTER
pixel_diff = B.pixel_diff

for _m in (MF, FF, MR):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(FIGHT):
        raise ImportError('%s came from %s, not the fight rig' % (_m.__name__, _m.__file__))

ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Matt')
SCRATCH = os.path.join(
    r'C:\Users\theyi\AppData\Local\Temp\claude\C--Users-theyi-OneDrive-Documents-new-game-project'
    r'\a7fc2846-afef-472d-979b-e17143793a0f\scratchpad', 'juggle', 'matt')

# ------------------------------------------------------------------------------ the juggle frame
W, H = 192, 144
FEET = (96, 143)
LOCAL_TO_FRAME = (FEET[0] - 48, FEET[1] - 95)     # an upright, grounded figure: local + (48, 48)

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

# ------------------------------------------------------------------------------ the light
# The rig's key light (shading.LIGHT3), toward the light: left, up and out of the screen. Every
# surface in the juggle frame is lit from here, whatever way the body is turned.
LIGHT3 = tuple(sh.LIGHT3)
# The hair's two 2D lights, as matt.hair writes them: the spikes' (matt.LIGHT) and the dome's
# (its `lit = -(u * 0.75 + v * 0.65)`).
SPIKE_LIGHT = tuple(matt.LIGHT)
DOME_LIGHT = (-0.75, -0.65)


def rot2(v, deg):
    """Rotate a 2D vector clockwise on screen (y down) by deg."""
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def local_light3(theta):
    """The light, in the body's own frame, that lands upper left once the body is turned theta
    clockwise: R(-theta) applied to the screen light. z (toward the viewer) is unchanged."""
    x, y = rot2(LIGHT3[:2], -theta)
    return (x, y, LIGHT3[2])


# ------------------------------------------------------------------------------ key maps
def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    put = im.putpixel
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            put((x, y), PAL[k])
    return im


def from_image(im):
    """An RGBA image back to keys (every opaque colour must be one of the 41)."""
    inv = {v[:3]: k for k, v in PAL.items()}
    im = im.convert('RGBA')
    out = {}
    for y in range(im.height):
        for x in range(im.width):
            p = im.getpixel((x, y))
            if p[3]:
                out[(x, y)] = inv[p[:3]]
    return out


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


def approved_colours():
    """Every colour on the approved matt.png: the 41."""
    return {c for c in flat(B.approved_sheet()) if c[3]}
