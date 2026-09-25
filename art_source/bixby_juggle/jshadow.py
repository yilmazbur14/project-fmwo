"""Bixby's mat shadow while he is juggled: bixby_leap_shadow.png, 3 frames (low, mid, high) of solid
black, the fight setting the alpha (his other shadows use BixbyBeastArtLayout.SHADOW_ALPHA 0.38).

Why a new sheet rather than bixby_beast_shadow.png: that sheet is four flap phases of a level, wings-
spread hover at one height, all the same size, while a juggle picks its shadow frame by height
(MasonArtLayout.JUGGLE_SHADOW: frame = lift / step, 0 low .. 2 high) and needs it to shrink as he rises.
A tumbling body with its wings flailing has no steady footprint either, so these are plain ellipses, the
juggle convention Mason's and Eric's leap shadows set.

Same frame as his other shadows, so the coder can reuse their conventions: 192x48, centred on
BixbyBeastArtLayout.SHADOW_CENTRE (96, 25). Sized off his tumble: low is his body's width at the mat
(about as wide as his ground shadow, 150 texels), then smaller and flatter as he rises.
"""
from PIL import Image

SW, SH = 192, 48
CX, CY = 96, 25
# half-width, half-height per frame: low, mid, high
SIZES = ((75.0, 14.0), (60.0, 11.0), (45.0, 8.0))


def frame(rx, ry):
    im = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))
    px = im.load()
    for y in range(SH):
        for x in range(SW):
            if ((x + 0.5 - CX) / rx) ** 2 + ((y + 0.5 - CY) / ry) ** 2 <= 1.0:
                px[x, y] = (0, 0, 0, 255)
    return im


def frames():
    return [frame(*s) for s in SIZES]


def sheet():
    out = Image.new('RGBA', (SW * len(SIZES), SH), (0, 0, 0, 0))
    for i, f in enumerate(frames()):
        out.alpha_composite(f, (i * SW, 0))
    return out


def extents():
    out = []
    for f in frames():
        x0, y0, x1, y1 = f.getbbox()
        out.append('%dx%d at x %d..%d y %d..%d' % (x1 - x0, y1 - y0, x0, x1 - 1, y0, y1 - 1))
    return out
