"""The arena mockup: both poses composited into the real Jordan arena capture (1920x1080, the live
HUD and the player as the game draws them), at the game's 3x, with the health-bar block outlined.
Writes only into the scratch approval folder."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

CAP = os.path.join(K.SCRATCH, 'cap')
SCALE = 3
HUD_BLOCK = (680, 36, 1240, 180)          # the boss health-bar block (the architect's numbers)
RING = (124, 145, 1796, 932)


def place(frame_im, top_left, base=None):
    base = base.copy() if base is not None else Image.open(os.path.join(CAP, 'arena_player.png')).convert('RGBA')
    big = frame_im.resize((frame_im.width * SCALE, frame_im.height * SCALE), Image.NEAREST)
    base.alpha_composite(big, top_left)
    return base


def ground_shadow(base, cx, cy, rx, ry):
    """A flat dark ellipse under the feet, as the game's separate shadow sprites do (mock only)."""
    sh = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(30, 50, 25, 110))
    out = base.copy()
    out.alpha_composite(sh)
    return out


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def annotate(im, marks, label=None):
    d = ImageDraw.Draw(im)
    f = _font(18)
    x0, y0, x1, y1 = HUD_BLOCK
    for i in range(0, 3):
        d.rectangle((x0 - i, y0 - i, x1 + i, y1 + i), outline=(255, 60, 200, 255))
    d.text((x0 + 4, y1 + 6), 'boss bar block (x 680-1240, y 36-180)', fill=(255, 60, 200, 255), font=f,
           stroke_width=2, stroke_fill=(0, 0, 0, 255))
    for (x, y, txt, col) in marks:
        d.line((x - 10, y, x + 10, y), fill=(0, 0, 0, 255), width=4)
        d.line((x, y - 10, x, y + 10), fill=(0, 0, 0, 255), width=4)
        d.line((x - 9, y, x + 9, y), fill=col, width=2)
        d.line((x, y - 9, x, y + 9), fill=col, width=2)
        d.text((x + 12, y - 9), txt, fill=col, font=f, stroke_width=2, stroke_fill=(0, 0, 0, 255))
    if label:
        d.text((360, 1040), label, fill=(255, 255, 255, 255), font=_font(22), stroke_width=2,
               stroke_fill=(0, 0, 0, 255))
    return im
