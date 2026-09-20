"""Frame language for the HUD bars, SAMPLED from the shipped art.

The keyline, well and brass tones below are not chosen here - they are read out
of Assets/UI/stamina_bar_frame.png and break_gauge_frame.png at generation time
and classified by luminance. If someone re-authors those frames, this generator
picks the change up (or asserts) instead of quietly drifting away from them.

Geometry constants come from the build plan; everything is native px, and
export_all writes the _3x companions with NEAREST.
"""
import os
from collections import Counter
from PIL import Image, ImageDraw

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
UI = PROJ + "/Assets/UI/"

# ---- geometry (native px) ------------------------------------------------
FRAME_W, FRAME_H = 160, 18
WIN_X, WIN_Y, WIN_W, WIN_H = 4, 4, 152, 12
NOTCH_XS = [4 + 19 * k for k in range(1, 8)]        # 23 42 61 80 99 118 137
PLATE_W, PLATE_H = 96, 16
EMBLEM = 12
GHOST_W = 3
SPARK_W, SPARK_H = 24, 20
TRAY_W, TRAY_H = 88, 22
HEART_W, HEART_H = 18, 16
BREAK_W, BREAK_H = 30, 28
HEART_SLOTS = [8, 34, 60]                            # native x, pitch 26


def _hex(c):
    return "#%02X%02X%02X" % c[:3]


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def sample_frame_palette():
    """Lift the shared frame tones out of the two shipped frames."""
    seen = Counter()
    for n in ("stamina_bar_frame.png", "break_gauge_frame.png"):
        im = Image.open(UI + n).convert("RGBA")
        for q in im.getdata():
            if q[3] > 128:
                seen[q[:3]] += 1
    cols = list(seen)
    # keyline: the darkest thing present, and it must be pure black
    key = min(cols, key=_lum)
    assert key == (0, 0, 0), "expected a pure black keyline, got %s" % (_hex(key),)
    # the well is the dark blue-violet body; its rim is the lighter indigo
    blues = [c for c in cols if c[2] > c[1] and _lum(c) < 90 and c != key]
    blues.sort(key=_lum)
    well, well_rim = blues[0], blues[-1]
    # Brass: warm tones (r > b), ordered dark -> bright. Weighted by pixel count
    # first - both frames carry a few stray warm accents (a skin tone, a brown)
    # that are structurally irrelevant, and taking them turns the frame muddy.
    total = sum(seen.values())
    warm = [c for c in cols if c[0] > c[2] + 20 and seen[c] >= total * 0.015]
    brass = sorted(warm, key=_lum)
    assert len(brass) >= 4, "expected at least four brass tones, got %d" % len(brass)
    p = dict(
        KEY=_hex(key), WELL=_hex(well), WELL_RIM=_hex(well_rim),
        BRASS_DK=_hex(brass[0]), BRASS=_hex(brass[1]),
        BRASS_LT=_hex(brass[2]), BRASS_HI=_hex(brass[-1]),
        GLINT="#FFFFFF",
    )
    return p


PAL = sample_frame_palette()
KEY, WELL, WELL_RIM = PAL["KEY"], PAL["WELL"], PAL["WELL_RIM"]
BRASS_DK, BRASS, BRASS_LT, BRASS_HI = PAL["BRASS_DK"], PAL["BRASS"], PAL["BRASS_LT"], PAL["BRASS_HI"]
GLINT = PAL["GLINT"]
# hot variants for the low-health rim, kept in the DB32 family the rest uses
HOT_DK, HOT, HOT_LT, HOT_HI = "#6E1F22", "#AC3232", "#D95763", "#FBF236"
BONE, BONE_DK = "#EDE4D6", "#C7BBAB"
CYAN, CYAN_LT = "#5FCDE4", "#CBDBFC"


def rgba(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def canvas(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def rect(im, x0, y0, x1, y1, col, a=255):
    ImageDraw.Draw(im).rectangle([x0, y0, x1, y1], fill=rgba(col, a))


def poly(im, pts, col, a=255):
    ImageDraw.Draw(im).polygon([tuple(p) for p in pts], fill=rgba(col, a))


def hline(im, x0, x1, y, col, a=255):
    rect(im, x0, y, x1, y, col, a)


def vline(im, x, y0, y1, col, a=255):
    rect(im, x, y0, x, y1, col, a)


def stud(im, x, y, w=4, h=4):
    """The little brass corner stud the stamina and break frames both carry."""
    rect(im, x, y, x + w - 1, y + h - 1, BRASS)
    rect(im, x, y, x + w - 1, y, BRASS_LT)
    rect(im, x, y + h - 1, x + w - 1, y + h - 1, BRASS_DK)
    rect(im, x + 1, y + 1, x + 1, y + 1, BRASS_HI)


def brass_box(im, x0, y0, x1, y1):
    """Outer keyline, lit top, brass body, dark underside - the shared chrome."""
    rect(im, x0, y0, x1, y1, KEY)
    rect(im, x0 + 1, y0 + 1, x1 - 1, y1 - 1, BRASS)
    hline(im, x0 + 1, x1 - 1, y0 + 1, BRASS_HI)
    hline(im, x0 + 1, x1 - 1, y0 + 2, BRASS_LT)
    hline(im, x0 + 1, x1 - 1, y1 - 1, BRASS_DK)
    vline(im, x0 + 1, y0 + 1, y1 - 1, BRASS_LT)
    vline(im, x1 - 1, y0 + 1, y1 - 1, BRASS_DK)


def well_box(im, x0, y0, x1, y1):
    """The recessed dark well the fills sit in."""
    rect(im, x0, y0, x1, y1, WELL_RIM)
    rect(im, x0 + 1, y0 + 1, x1 - 1, y1 - 1, WELL)
    hline(im, x0 + 1, x1 - 1, y0 + 1, KEY)


def ramp_fill(w, h, ramp, sheen=True, pitch=19):
    """A bar fill from a boss's 5-step ramp: lit top line, body, dark underside.
    Faint bands on the notch pitch tie the fill to the frame's 7 notches."""
    r0, r1, r2, r3, r4 = ramp
    im = canvas(w, h)
    bands = [(0, 0, r3), (1, 1, r4), (2, 5, r3), (6, 9, r2), (10, 10, r1), (11, h - 1, r0)]
    for a, b, c in bands:
        if a < h:
            rect(im, 0, a, w - 1, min(b, h - 1), c)
    if sheen:
        for x in range(0, w, pitch):
            rect(im, x, 2, x + 1, h - 3, r3)
            rect(im, x + 1, 2, x + 1, h - 3, r2)
    return im


def tint(im, col, amount):
    """Blend every opaque pixel toward col. Used for the hot fills."""
    t = rgba(col)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            px[x, y] = (int(r + (t[0] - r) * amount), int(g + (t[1] - g) * amount),
                        int(b + (t[2] - b) * amount), a)
    return im


def up3(im):
    return im.resize((im.width * 3, im.height * 3), Image.NEAREST)


if __name__ == "__main__":
    for k, v in sorted(PAL.items()):
        print("%-9s %s" % (k, v))
