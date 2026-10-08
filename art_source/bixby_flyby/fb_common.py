"""Shared setup for the Flyby art: paths, the rig on sys.path (read-only), the Inferno fire palette.

The rig in art_source/bixby_redesign/ is imported, never edited and never run: its modules keep their
names on sys.path (its pal.py must win over josh_redesign's, so it goes first). The Inferno palette
lives in a module that is also called pal.py, so it is loaded by path under its own name.

Frame conventions (Scripts/BixbyBeastArtLayout.gd and the plan's section 13):
  192x160 texels, anchor (96, 151), drawn facing right; the engine mirrors about the anchor column.
  On a pass the anchor sits at screen y 300, so texel row r is at y = 300 + 3 (r - 151).
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
RIG = os.path.join(ART, 'bixby_redesign')
INFERNO = os.path.join(ART, 'bixby_inferno_fx')
ASSETS = os.path.join(ROOT, 'Assets')
BIXBY_ASSETS = os.path.join(ASSETS, 'Characters', 'Bixby')
APPROVAL = os.path.join(HERE, 'approval')

if RIG in sys.path:
    sys.path.remove(RIG)
sys.path.insert(0, RIG)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
if ART not in sys.path:
    sys.path.append(ART)                    # imgdiff.py

import pal as RPAL  # noqa: E402  (the rig's palette + BCanvas; importing it also pulls josh_redesign/lib)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIRE_PAL = _load('inferno_pal', os.path.join(INFERNO, 'pal.py')).PAL

# The rig's palette plus the Inferno ramp's one colour it lacks: white-hot. Every other Inferno fire
# colour is already one of the rig's keys (n N p P Y t r q are the same hexes), checked in fire_keys().
PAL = dict(RPAL.PAL)
PAL['!'] = FIRE_PAL['W']                  # #FFFFFF, the fire's white-hot core

FW, FH = 192, 160
ANCHOR = (96, 151)
SCALE = 3
PASS_ANCHOR_Y = 300
FLOOR_ROW = 86                             # the ring floor's top edge (screen y 105)
LOWEST_ROW = 157                           # nothing is drawn below this row
EXIT_ROWS = (78, 112)                      # every mouth exit sits in these rows
CURTAIN_TEXELS = 32                        # the curtain band: 32 columns up to and including the lead exit


def fire_keys():
    """The rig keys whose colour is an Inferno fire colour (the fire may use exactly these plus '!')."""
    inv = {v: k for k, v in RPAL.PAL.items()}
    out = {}
    for fk, rgba in FIRE_PAL.items():
        if rgba in inv:
            out[fk] = inv[rgba]
    return out


def screen_y(row):
    return PASS_ANCHOR_Y + SCALE * (row - ANCHOR[1])


def image(px, w=FW, h=FH):
    """A {(x, y): key} dict as an RGBA image in the Flyby palette."""
    from PIL import Image
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    put = im.putpixel
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            put((x, y), PAL[k])
    return im


class Canvas(RPAL.BCanvas):
    """The rig's keylining canvas, rendering with the Flyby palette (the rig's plus white-hot)."""

    def image(self):
        return image(self.px, self.w, self.h)
