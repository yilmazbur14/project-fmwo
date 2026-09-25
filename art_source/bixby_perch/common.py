"""Shared setup for the perch set: imports the approved redesign rig READ-ONLY (never edits it), the
frame size, the rope row, and inspection helpers that write only into this set's scratch folder.

The rig lives in art_source/bixby_redesign (see its README): the approved parts (pal, shapes, heads,
body, wings, midmaps, sidemaps, frame) and the redesign artist's posable modules (rig_body, rig_wings,
rig_heads, rig_faces, rig_faces2). Its view.save() and rig_fire.stream() write into the redesign
artist's own scratch folder, so nothing here calls them.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RIG = os.path.join(ART, 'bixby_redesign')
for p in (RIG, ART):
    if p not in sys.path:
        sys.path.insert(0, p)

from PIL import Image  # noqa: E402

import pal  # noqa: E402,F401
import shapes  # noqa: E402,F401
import heads  # noqa: E402,F401
import body  # noqa: E402,F401
import midmaps  # noqa: E402,F401
import sidemaps  # noqa: E402,F401
import frame as rigframe  # noqa: E402,F401
import rig_body as RB  # noqa: E402,F401
import rig_wings as RW  # noqa: E402,F401
import rig_heads as RH  # noqa: E402,F401
import rig_faces as RF  # noqa: E402,F401
import rig_faces2 as F2  # noqa: E402,F401
from pal import PAL, BCanvas  # noqa: E402,F401

ROOT = os.path.dirname(ART)
SCRATCH = ('C:/Users/theyi/AppData/Local/Temp/claude/C--Users-theyi-OneDrive-Documents-new-game-project/'
           'a7fc2846-afef-472d-979b-e17143793a0f/scratchpad/bixby_perch/')

# Frames are 192x160, top-aligned around the usual anchor, like every beast sheet.
FW, FH = 192, 160
ANCHOR = (96, 151)
AX = 95.5                # symmetry axis: a pixel at x mirrors to 191 - x
# The texel row the arena's top rope crosses (it lands on screen y 100). The rope band on screen is black
# 93-99, white 100-106, black 107-113, so at 3x it hides rows ROPE-2 .. ROPE+3 completely, and a third
# of ROPE-3 and two thirds of ROPE+4.
ROPE = 36
HEADROOM = 33            # nothing above row ROPE - HEADROOM
TOP_ROW = ROPE - HEADROOM
# The top rope's doorway (screen x 852..1067) in frame columns, with him centred on screen x 960: the
# rope is only there at columns <= DOOR[0] - 1 and >= DOOR[1].
DOOR = (60, 132)
BG = (46, 49, 58, 255)


def canvas(h=FH):
    return BCanvas(FW, h)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def save(im, name, s=4, bg=BG, crop=None):
    if crop:
        im = im.crop(crop)
    os.makedirs(SCRATCH, exist_ok=True)
    up(on_bg(im, bg), s).save(SCRATCH + name)
    return SCRATCH + name
