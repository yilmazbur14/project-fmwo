"""Greyson's fight art: the shared base.

Imports the APPROVED rig (art_source/greyson_redesign, the design of record since 2026-09-24)
READ-ONLY and builds on it. Nothing in this folder edits the rig's files. On import it proves the
rig still draws the shipped approved sprite (Assets/Characters/Greyson/greyson_redesign.png)
pixel for pixel, and refuses to run if it does not, so fight art can never drift from the design
the user approved.

Every module here is named gf_*, so none can shadow (or be shadowed by) the rig's gr_* modules.
Coordinates are the rig's own: 112x112 frames, feet on row 111, column 56 the anchor and mirror
axis (x' = 112 - x), light from the upper left. Nothing in this module writes files.
"""
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'greyson_redesign')
ROOT = os.path.dirname(ART)
ASSETS_GREYSON = os.path.join(ROOT, 'Assets', 'Characters', 'Greyson')
APPROVED_PNG = os.path.join(ASSETS_GREYSON, 'greyson_redesign.png')

for _p in (ART, RIG, HERE):
    while _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, ART)          # art_source, for imgdiff
sys.path.insert(0, RIG)          # the approved rig
sys.path.insert(0, HERE)         # this folder first; its names never clash (gf_*)

import gr_kit as K      # noqa: E402
import gr_muscle as M   # noqa: E402
import gr_fig           # noqa: E402
import gr_face          # noqa: E402
import gr_arms          # noqa: E402
import gr_hands         # noqa: E402
import gr_boots         # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image   # noqa: E402


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == \
        os.path.normcase(os.path.abspath(folder))


for _m in (K, M, gr_fig, gr_face, gr_arms, gr_hands, gr_boots):
    if not _same_dir(_m, RIG):
        raise ImportError('%s came from %s, not the approved rig %s' % (_m.__name__, _m.__file__, RIG))

W = H = 112
AX = K.AX
FEET_ROW = 111

# ------------------------------------------------------------------------------------ palette
# The approved 28 colours, plus what the fight adds. Computah's cannon is painted in the SAME
# purple ramp as Greyson's trunks (A-E: C892F2 A063DC 7C3BB4 592687 391555), so the cannon adds
# only its two bore darks. Its own keyline (#0C111A) is NOT carried over: on Greyson the cannon
# sits inside his pure-black keyline, like everything else he wears. The barbell reuses them too:
# the iron plate is the bore's slate, the bar is the boots' chrome whites.
FIGHT_KEYS = {
    'z': K.hx('1A212C'),     # the cannon's bore, deep (Computah's own)
    'Z': K.hx('3C4757'),     # the cannon's bore, slate (Computah's own); the plate's face
}
for _k, _v in FIGHT_KEYS.items():
    assert _k not in K.PAL, _k
    K.PAL[_k] = _v           # in memory only; the rig's files are untouched
K.RAMPS.setdefault('bore', 'Zz')
K.DARKER['Z'], K.DARKER['z'] = 'z', 'z'
K.LIGHTER['z'], K.LIGHTER['Z'] = 'Z', 'Z'
ALLOWED = set(K.PAL)


# ------------------------------------------------------------------------------------ guard

def approved_sheet():
    return Image.open(APPROVED_PNG).convert('RGBA')


def check_rig():
    """The rig must still draw the approved frames exactly (after the palette extension too)."""
    sheet = approved_sheet()
    for i, pose in enumerate(('idle', 'flex')):
        d = pixel_diff(gr_fig.build(pose).image(), sheet.crop((112 * i, 0, 112 * i + 112, 112)))
        if d:
            raise SystemExit('the approved rig no longer reproduces approved frame %d (%s): %s'
                             % (i, pose, d))


check_rig()


# ------------------------------------------------------------------------------------ helpers

def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def mirror(part):
    return {(AX - x, y): k for (x, y), k in part.items()}


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), K.PAL[k])
    return im


def audit(px, fx=()):
    """gr_kit.audit with the fight palette as the allowed keys."""
    a = K.audit(px, fx)
    a['keys'] = sorted(set(px.values()) - ALLOWED)
    return a


def strip(frames, w=W, h=H):
    out = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.alpha_composite(f if isinstance(f, Image.Image) else image(f, w, h), (w * i, 0))
    return out
