"""Palette and canvas for Bixby's Hades-direction redesign.

Borrows the Josh redesign's toolkit (art_source/josh_redesign/lib.py) by import and never edits it:
its Canvas keylines every part it stamps; here only the palette and the frame size differ, so
BCanvas renders with this palette at 192x160.

Bixby's tricolour is carried through Hades' palette: his tan becomes ember/blood red, his black
saddle becomes a violet-rimmed charcoal, his white becomes bone.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Appended, not prepended: josh_redesign has its own rig.py and export.py, and this folder's must win.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
_JOSH = os.path.join(os.path.dirname(HERE), 'josh_redesign')
if _JOSH not in sys.path:
    sys.path.append(_JOSH)
import lib  # noqa: E402  (josh_redesign/lib.py, imported, not edited)
from lib import (amap, ellipse, fill, line, mirror, paint, poly, rect, rim, shift,  # noqa: E402,F401
                 stroke, dump, patch)

FW, FH = 192, 160          # frame size (BixbyBeastArtLayout.FRAME_SIZE)
AX = 95.5                  # symmetry axis: x mirrors to 191 - x
ANCHOR = (96, 151)         # feet / hover anchor


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour; ramps run dark -> light.
PAL = {
    'k': hx('000000'),                      # keyline, pure black as measured on bixby_beast.png
    # blood-red / ember fur: Bixby's tan, pushed into Hades' red
    'q': hx('2C0610'), 'r': hx('570C18'), 's': hx('87151F'), 't': hx('B42424'), 'u': hx('DE4E2C'),
    'v': hx('FF8C45'),                      # hot ember rim
    # charcoal saddle: Bixby's black, with Hades' violet rim light
    'a': hx('120D16'), 'b': hx('221A28'), 'c': hx('362A3E'), 'd': hx('4E3F5A'),
    'e': hx('7A5AAE'), 'f': hx('A98AE6'),
    # bone: Bixby's white
    'z': hx('74606E'), 'y': hx('B09A8E'), 'x': hx('E3D2BC'), 'w': hx('FFF6E6'),
    # gold: the collar spikes and studs
    'g': hx('5C360C'), 'G': hx('A66C1A'), 'o': hx('E0A632'), 'O': hx('FFE488'),
    # wine leather: the collars (the approved red collar, cooler than the fur so it separates)
    'l': hx('3E0A1E'), 'L': hx('6E1230'), 'm': hx('A4203E'), 'M': hx('D04A5A'),
    # mint: Hades' glowing eyes
    'h': hx('0F4A38'), 'i': hx('36C487'), 'j': hx('B6FFDC'),
    # tongue and fire
    'n': hx('9A2A10'), 'N': hx('E0561A'), 'p': hx('FF8C2E'), 'P': hx('FFC45A'), 'Y': hx('FFF2B0'),
    # steel: Liam's headband plate and band
    'S': hx('4A5563'), 'T': hx('7B8893'), 'U': hx('B3C0C9'), 'W': hx('EEF4F7'),
    # wing membrane: dark wine
    'A': hx('1E0C16'), 'B': hx('3A1424'), 'C': hx('5E1C30'),
}


class BCanvas(lib.Canvas):
    def __init__(self, w=FW, h=FH):
        super().__init__(w, h)

    def image(self):
        from PIL import Image
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        for (x, y), k in self.px.items():
            if 0 <= x < self.w and 0 <= y < self.h:
                im.putpixel((x, y), PAL[k])
        return im


def mir(part):
    """Mirror a part across the frame's axis (x -> 191 - x)."""
    return {(int(2 * AX) - x, y): k for (x, y), k in part.items()}


def both(part):
    """A part plus its mirror image."""
    out = dict(part)
    out.update(mir(part))
    return out


def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    px = [c for c in (flat() if flat else im.getdata()) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': round(100.0 * black / max(1, len(px)), 2)}
