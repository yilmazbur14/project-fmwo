"""Bakes VS-card lettering to pixel images, with Pixelify Sans's broken glyphs redrawn.

Why this exists: Pixelify Sans builds every capital from a rounded-rectangle ring
with segments cut away. Two of those cuts are wrong for our copy:

  B  the ring is notched on the RIGHT edge through the middle bar (glyph cols
     37-45, rows 28-35 of the 46x64 box), and the middle bar never touches the
     left stem. That notch sits exactly where a G's mouth goes, so BURAK reads
     GURAK and BIXBY reads GIXGY.
     Fix: fill the middle band edge to edge, which is the same ring-plus-crossbar
     construction the font uses for E.

  5  carries a right stem across rows 10-18, closing the top the way S does, so
     5 and S are near-identical and FIGHT 05 reads FIGHT OS.
     Fix: draw the font's own S and erase that upper-right stem. Identical
     metrics (both are 46x64 on a 58 advance), so spacing is untouched.

Everything else comes straight from the font. Patches are expressed as fractions
of the glyph box so they hold at any size.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "fonts", "PixelifySans.ttf")
FONT_PATH = os.path.normpath(FONT_PATH)
THRESH = 40                      # hard-edge cut; matches the approved mocks

# glyph box the font uses for capitals, measured at size 99
GW, GH = 46.0, 64.0
TL = (0.0, 0.0, 9 / GW, 9 / GH)          # top-left corner notch of the ring
BL = (0.0, 55 / GH, 9 / GW, 1.0)         # bottom-left corner notch
# (source glyph, [(x0,y0,x1,y1,'fill'|'erase'), ...]) in glyph-box fractions.
# Closing the ring's middle turns it into an 8, so B also needs its two left
# corners squared off - that squared left edge is the only thing separating B
# from 8 (and 5 from S) in a font this geometric.
PATCHES = {
    "B": ("B", [(0.0, 27 / GH, 1.0, 37 / GH, "fill"),
                TL + ("fill",), BL + ("fill",)]),
    "5": ("S", [(36 / GW, 10 / GH, 1.0, 19 / GH, "erase"),
                TL + ("fill",)]),
}

_fonts = {}


def _font(sz):
    if sz not in _fonts:
        _fonts[sz] = ImageFont.truetype(FONT_PATH, sz)
    return _fonts[sz]


GPAD = 6        # margin inside a single-glyph mask; its ink starts at (GPAD, GPAD)


def glyph(ch, sz):
    """Hard-edged mask for one character. Its ink always starts at (GPAD, GPAD)."""
    f = _font(sz)
    src, patches = PATCHES.get(ch, (ch, []))
    bb = f.getbbox(src)
    m = Image.new("L", (bb[2] - bb[0] + GPAD * 2, bb[3] - bb[1] + GPAD * 2), 0)
    ImageDraw.Draw(m).text((GPAD - bb[0], GPAD - bb[1]), src, font=f, fill=255)
    m = m.point(lambda v: 255 if v > THRESH else 0)
    if patches:
        box = m.getbbox()
        if box:
            gx0, gy0, gx1, gy1 = box
            gw, gh = gx1 - gx0, gy1 - gy0
            d = ImageDraw.Draw(m)
            for fx0, fy0, fx1, fy1, op in patches:
                d.rectangle([gx0 + round(fx0 * gw), gy0 + round(fy0 * gh),
                             gx0 + round(fx1 * gw) - 1, gy0 + round(fy1 * gh) - 1],
                            fill=255 if op == "fill" else 0)
    return m


def _line_mask(text, sz):
    """Lay the patched glyphs out on the font's own advances, so spacing matches
    what draw.text would have produced."""
    f = _font(sz)
    asc, desc = f.getmetrics()
    pad = 10
    out = Image.new("L", (int(f.getlength(text)) + pad * 2 + 12, asc + desc + pad * 2), 0)
    pen = 0.0
    for ch in text:
        if ch.strip():
            src = PATCHES.get(ch, (ch, []))[0]
            bb = f.getbbox(src)
            m = glyph(ch, sz)
            # draw.text would put this glyph's ink at (pen + bb[0], bb[1])
            out.paste(m, (pad + int(round(pen)) + bb[0] - GPAD, pad + bb[1] - GPAD), m)
        pen += f.getlength(ch)
    return out


def bake(text, sz, fill="#FFFFFF", outline="#000000", ol_w=None,
         shadow=None, shadow_col="#0B0A12", trim=True):
    """The approved treatment: hard white letters, black outline, hard drop shadow."""
    if ol_w is None:
        ol_w = max(1, round(sz / 30))
    if shadow is None:
        shadow = (0, max(3, round(sz / 16)))
    m = _line_mask(text, sz)
    pad = ol_w + max(abs(shadow[0]), abs(shadow[1])) + 2
    big = Image.new("L", (m.width + pad * 2, m.height + pad * 2), 0)
    big.paste(m, (pad, pad))
    grown = big.filter(ImageFilter.MaxFilter(ol_w * 2 + 1)) if ol_w else big
    out = Image.new("RGBA", big.size, (0, 0, 0, 0))
    if shadow != (0, 0):
        out.paste(_c(shadow_col), (shadow[0], shadow[1]), grown)
    out.paste(_c(outline), (0, 0), grown)
    out.paste(_c(fill), (0, 0), big)
    if trim:
        bb = out.split()[3].getbbox()
        if bb:
            out = out.crop(bb)
    return out


def _c(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
