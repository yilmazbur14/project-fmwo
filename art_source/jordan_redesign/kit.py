"""Jordan's redesign kit: his palette, a renderer for it, and the preview helpers.

Built on art_source/josh_redesign/lib.py (imported, never edited): its Canvas keylines every part it
stamps, and its shapes / rim / stroke / amap / dump / patch do the drawing. lib.Canvas.image() reads
lib.PAL, so this module renders with its own palette instead.

Nothing here writes into Assets/. Previews go to the session scratchpad (or WIP if given).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Appended, not prepended: josh_redesign has its own export.py etc., which must never shadow ours.
for _p in (os.path.join(HERE, '..', 'josh_redesign'), os.path.join(HERE, '..')):
    if _p not in sys.path:
        sys.path.append(_p)
import lib  # noqa: E402
from lib import Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, shift, stroke  # noqa: E402,F401
from PIL import Image  # noqa: E402

W = H = 96
WIP = os.environ.get('JORDAN_WIP', os.path.join(HERE, 'wip'))


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour; ramps run dark -> light.
PAL = {
    'k': hx('000000'),                                   # keyline, pure black like Mason / Josh
    # skin: light olive (12.webp), lit from the upper left like the rest of the cast
    'a': hx('573A2B'), 'b': hx('876046'), 'c': hx('B58A63'), 'd': hx('D5AD85'), 'e': hx('ECCDA5'),
    'p': hx('A8604F'),                                   # lip
    # hair and beard: dark brown
    'h': hx('1A110D'), 'i': hx('2B1C15'), 'j': hx('432D21'), 'l': hx('5F412E'), 'm': hx('7F5B3E'),
    'A': hx('A27B57'),                                   # greasy sheen on the quiff
    'W': hx('F3EEE4'),                                   # eye white, teeth
    # jersey red (the Peach tee's red, kept as a colour)
    'v': hx('4C0D1A'), 'V': hx('8C1B2D'), 'R': hx('C9293F'), 'T': hx('EC5A5B'), 'U': hx('FF9C8C'),
    # pink trim, wristband, pop cloud
    'q': hx('B04A78'), 'P': hx('EE7FAE'), 'Q': hx('FFC3DB'),
    # denim
    'n': hx('141A31'), 'N': hx('222F55'), 's': hx('33467B'), 'S': hx('4A62A0'),
    # sneakers: charcoal uppers, white soles
    '1': hx('2C2F39'), '2': hx('4C505D'), '3': hx('7B8090'), '9': hx('BAB6AC'), '0': hx('F2EFE7'),
    # gold: the chase-edition box, the star
    'g': hx('7A5216'), 'G': hx('B07D22'), 'o': hx('E0AB35'), 'O': hx('F5D94E'), 'Y': hx('FFF3B0'),
    # box window plastic
    'w': hx('86A9C2'), 'x': hx('CFE4EE'),
    # figure colours (the plumber in the box, the print)
    'B': hx('2F55B5'), 'D': hx('1C2F73'),                # overalls / hedgehog blue
    'L': hx('5A64E8'), 'M': hx('3A3F9E'),                # mascot blurple
    'u': hx('8A55CC'), 'y': hx('5A3291'),                # gamer purple
    'z': hx('5BD1E6'),                                   # gamer headset cyan
    # the princess print on his tee (10.webp): pale face; hair and crown use the gold ramp
    'f': hx('FBE3CC'),
}


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1, as a pixel set."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PAL[k])
    return im


def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    px = [c for c in data if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': black / max(1, len(px))}


BG = (46, 49, 58, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def row(ims, gap=8, bg=(10, 10, 12, 255)):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def save(im, name):
    os.makedirs(WIP, exist_ok=True)
    p = os.path.join(WIP, name)
    im.save(p)
    return p
