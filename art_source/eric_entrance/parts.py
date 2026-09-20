"""Body parts for Eric's entrance, cut from his own shipped frames.

The entrance needs him EMPTY-HANDED, and all 40 frames of eric_sheet_v2.png have
him holding the sword. The one empty-handed, front-facing pose in the project is
eric_bearhug_v2.png frame 8 - so that frame is the source for his head, beard,
pauldrons, chest, cape, belt and tassets, and for the hanging gauntlet arm.

It carries bear-hug FX (pale blue sparkles) that are not part of him, so
clean() drops any pixel whose colour is not in eric_sheet_v2's own 39-colour
palette. That is also the check: anything the cleaner removes was never his.

The legs are drawn rather than cut, because they have to animate. His legs are
short - the body runs about 74px from crown to sole, with the tassets covering
most of the thigh - so the walk reads through the body bob, the cape and the
sabatons stepping out from under the skirt.
"""
import os
from PIL import Image

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
CH = PROJ + "/Assets/Characters/Eric/"
SHEET = CH + "eric_sheet_v2.png"
BEARHUG = CH + "eric_bearhug_v2.png"
SHEET_BOX = (57, 40, 164, 192)          # frame 0, tight

# bear-hug frame 8, in its own 192x192 frame coordinates
BH_FRAME = 8
BODY_BOX = (77, 119, 180, 192)          # whole empty-handed upper body
ARM_BOX = (150, 152, 180, 192)          # his right arm, hanging, gauntlet fist

# Eric's palette (white plate / steel / hair / skin / cape / cross / gold)
PL_HI, PL_LT, PL, PL_MD, PL_SH, PL_DK = "#FFFFFF", "#EAF0F6", "#CDD7E2", "#A3B1C2", "#7A86A0", "#525A74"
ST_LT, ST, ST_MD, ST_DK = "#A3A8AE", "#7C8187", "#5C6067", "#41444B"
CP_HI, CP, CP_DK = "#8A1F38", "#5E142C", "#3C0C20"
GD_LT, GD, GD_DK = "#F2C457", "#C48A2C", "#8A5A1C"
BK = "#000000"


def sheet_palette():
    im = Image.open(SHEET).convert("RGBA").crop(SHEET_BOX)
    return {q[:3] for q in im.getdata() if q[3] > 128}


def frame(path, index, w, h):
    im = Image.open(path).convert("RGBA")
    return im.crop((index * w, 0, (index + 1) * w, h))


def clean(im, palette):
    """Drop every pixel whose colour is not in Eric's own sheet palette.
    This is what removes the bear-hug sparkles without hand-erasing them."""
    px = im.load()
    removed = 0
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a > 0 and (r, g, b) not in palette:
                px[x, y] = (0, 0, 0, 0)
                removed += 1
    return im, removed


def body():
    """Head, beard, pauldrons, chest, cape, belt, tassets - and ONE arm.

    The raised left arm is dropped: its column range is cut away so the walk can
    hang a mirrored copy of the right arm there instead."""
    pal = sheet_palette()
    f = frame(BEARHUG, BH_FRAME, 192, 192)
    im = f.crop(BODY_BOX)
    im, removed = clean(im, pal)
    # the raised arm and its open hand live left of the cape; clear that column
    px = im.load()
    for y in range(0, 46):
        for x in range(0, 26):
            px[x, y] = (0, 0, 0, 0)
    return im, removed


ANGRY_HEAD = (56, 75, 88, 110)      # eric_sheet_v2 frame 0, tight coords
HEAD_AT = (40, -2)                  # where it lands in the body part


def angry_head():
    """His idle face off the main sheet: narrow slit eyes, heavy angled brow.

    The bear-hug frame's face is neutral - wide white ovals with small pupils and
    a flat brow - which reads as startled. It is the wrong face for a menacing
    walk-in and it is why the first cut looked derpy. This is the same face the
    VS-card bust uses, at 1x."""
    im = Image.open(SHEET).convert("RGBA").crop(SHEET_BOX).crop(ANGRY_HEAD)
    return im


def arm():
    pal = sheet_palette()
    f = frame(BEARHUG, BH_FRAME, 192, 192)
    im = f.crop(ARM_BOX)
    im, _ = clean(im, pal)
    return im


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    pal = sheet_palette()
    b, removed = body()
    a = arm()
    print("sheet palette: %d colours" % len(pal))
    print("body %dx%d  (%d FX pixels removed)" % (b.width, b.height, removed))
    print("arm  %dx%d" % (a.width, a.height))
    o = Image.new("RGBA", (b.width + a.width * 2 + 40, max(b.height, a.height) + 10), (28, 26, 40, 255))
    o.alpha_composite(b, (5, 5))
    o.alpha_composite(a, (b.width + 15, 5))
    o.alpha_composite(a.transpose(Image.FLIP_LEFT_RIGHT), (b.width + a.width + 25, 5))
    o.resize((o.width * 4, o.height * 4), Image.NEAREST).convert("RGB").save(os.path.join(out, "_parts.png"))
