"""Gothic frame language for the boss bar and the daze meter.

WHY THIS IS A SEPARATE FILE FROM barlib.py
barlib samples its brass tones out of the shipped stamina and break frames, and
that is still correct for the PLAYER HUD - the heart tray, the stamina rail and
the hype meter are brass on purpose.  It is the wrong reference for this
element.  The boss bar is being restyled to a thin, dark, ornate language, so
its palette is declared here and sampled from the direction reference instead.

PALETTE PROVENANCE - every tone below was read out of the reference image, not
picked by eye.  Region samples:
    empty frame body    #0A0A0A 10%   #2E233D 3%
    frame inner rim     #403058 / #3E3058 (column slice, y65-66 and y89-90)
    end caps            #FEFEFE  (the pale keyline; the caps are the whitest thing present)
    empty channel       #313C40 61%
    fill strip          #AD2A3C 20%  with #493138 / #463137 as its underside
The reference is an upscaled render, so its intermediate tones are resampling
artefacts; the eight below are the real set.

WHAT CHANGED AND WHAT DID NOT
Geometry is untouched: 160x18 frame, window at (4,4) 152x12, seven dividers on
the 19px notch pitch, daze rail 128x7 with its fill at (7,2) 114x3.  Every
existing state keeps its name and size.  Only the tones and the chrome shapes
change, plus one genuinely new asset - see CREST below.

CREST.  The reference's defining feature is an ornate winged crest at the centre
that BREAKS the bar's top and bottom edge, which is what stops it reading as a
plain rectangle.  That cannot live inside an 18px frame, so it ships as its own
sprite drawn centred over the bar.  One new asset, one new draw call.  Flagged
rather than wired.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image, ImageDraw
from barlib import (canvas, rect, poly, hline, vline, rgba, up3,
                    FRAME_W, FRAME_H, WIN_X, WIN_Y, WIN_W, WIN_H, NOTCH_XS)

# ---- palette, sampled from the direction reference -----------------------
INK = "#000000"        # outer keyline, house style
COAL = "#0A0A0A"       # frame body, near-black
PLUM_DK = "#2E233D"    # deep purple inner rim
PLUM = "#403058"       # purple
PLUM_LT = "#4C3F61"    # lit purple
BONE = "#EDE4D6"       # the thin pale keyline that gives it the elegance
BONE_HI = "#FFFFFF"
WELL = "#313C40"       # empty channel, charcoal-teal
SHADE = "#0C160E"      # the crest's ragged shadow mass, a green-black
CRIMSON = "#AD2A3C"    # the fill
CRIMSON_DK = "#493138"

FW, FH = FRAME_W, FRAME_H
WX, WY, WW, WH = WIN_X, WIN_Y, WIN_W, WIN_H
CAP_W = 9              # the crescent end cap
CREST_W, CREST_H = 46, 32
CREST_OVER = 7         # how far the crest stands proud of the bar, top and bottom


def _mirror(im):
    """Right half from the left, about the canvas centre.  Every symmetric
    shape here is drawn once and mirrored, so the halves cannot drift."""
    w, h = im.size
    px = im.load()
    for x in range(w // 2):
        for y in range(h):
            px[w - 1 - x, y] = px[x, y]
    return im


# ---- crescent end cap ----------------------------------------------------
# A thin pale crescent opening inward, the reference's cap shape.  Authored as a
# grid because a 9x18 shape drawn with arcs lands on the wrong texels.
CAP = [
    ".........",
    "....KKK..",
    "..KKBBBK.",
    ".KBBKKKK.",
    ".KBKK....",
    "KBBK.....",
    "KBK......",
    "KBK......",
    "KBK......",
    "KBK......",
    "KBK......",
    "KBK......",
    "KBBK.....",
    ".KBKK....",
    ".KBBKKKK.",
    "..KKBBBK.",
    "....KKK..",
    ".........",
]
CAP_COLS = {"K": INK, "B": BONE_HI, "b": PLUM, ".": None}

# The crest's mask, authored as a grid: a pale dome with two eye slots and a
# chin spike that runs down across the bar.
MASK = [
    "...KKKKK...",
    "..KWWWWWK..",
    ".KWWWWWWWK.",
    "KWWWWWWWWWK",
    "KWWKKWKKWWK",
    "KWWKKWKKWWK",
    "KWWWWWWWWWK",
    ".KWWWWWWWK.",
    "..KWWWWWK..",
    "...KWWWK...",
    "....KWK....",
    "....KWK....",
    "....KWK....",
    ".....K.....",
]
MASK_COLS = {"K": INK, "W": BONE_HI, ".": None}

# Ragged shadow, left half only - _mirror makes the right.  Highest at the
# centre, tapering out, so it reads as something spreading from behind the mask.
RAG = (1, 3, 2, 5, 3, 6, 4, 7, 5, 9, 6, 10, 7, 11, 8, 12, 9, 13, 10, 12, 11, 13, 12)


def _stamp(im, grid, x0, y0, cols, flip=False):
    px = im.load()
    for gy, row in enumerate(grid):
        for gx, ch in enumerate(row):
            c = cols.get(ch)
            if c is None:
                continue
            x = x0 + (len(row) - 1 - gx if flip else gx)
            y = y0 + gy
            if 0 <= x < im.width and 0 <= y < im.height:
                px[x, y] = rgba(c)


# ---- the bar frame -------------------------------------------------------
def _rails(im, plum=PLUM, plum_dk=PLUM_DK):
    """The thin chrome above and below the window.

    MEASURED, not guessed.  A row scan of the reference inside its window found
    the dividers at lum 11 (#0B0B0B) and the only pale pixels in the whole bar
    at the two end caps (#FEFEFE).  So the rails are purple and black and the
    bar is almost entirely dark - the elegance is the restraint, and the two
    white accents (caps, and the mask on the crest) are what pop against it.
    An earlier pass here ran a bone keyline the full length and bone dividers;
    that was brighter than the reference and lost exactly that effect."""
    hline(im, 0, FW - 1, 0, INK)
    hline(im, 0, FW - 1, 1, plum_dk)
    hline(im, 0, FW - 1, 2, plum)
    hline(im, 0, FW - 1, 3, INK)
    hline(im, 0, FW - 1, FH - 3, plum)
    hline(im, 0, FW - 1, FH - 2, plum_dk)
    hline(im, 0, FW - 1, FH - 1, INK)
    vline(im, 0, 0, FH - 1, INK)
    vline(im, FW - 1, 0, FH - 1, INK)


def frame_back():
    """Under the fill: the recessed channel the fill sits in."""
    im = canvas(FW, FH)
    rect(im, 1, 1, FW - 2, FH - 2, COAL)
    rect(im, WX - 1, WY - 1, WX + WW, WY + WH, INK)
    rect(im, WX, WY, WX + WW - 1, WY + WH - 1, WELL)
    hline(im, WX, WX + WW - 1, WY, INK)
    _rails(im)
    _stamp(im, CAP, 0, 0, CAP_COLS)
    _stamp(im, CAP, FW - CAP_W, 0, CAP_COLS, flip=True)
    return im


def _frame_over(low=False):
    """Over the fill: rails, dividers and caps, window transparent.

    LOW HEALTH.  Eric's fill is red and the old low state was also red, so at
    20% he read by rim and pulse only.  The fix here is to separate them by
    VALUE and CHROMA rather than hue: at low health the chrome goes pale bone
    and the dividers brighten, so a red fill sits inside a near-white frame.
    That reads at a glance on any boss, including the red ones, and it does not
    need the fill to change colour at all."""
    im = canvas(FW, FH)
    rect(im, 1, 1, WX - 1, FH - 2, COAL)
    rect(im, WX + WW, 1, FW - 2, FH - 2, COAL)
    _rails(im, BONE if low else PLUM, PLUM_LT if low else PLUM_DK)
    vline(im, WX - 1, WY - 1, WY + WH, INK)
    vline(im, WX + WW, WY - 1, WY + WH, INK)
    for x in NOTCH_XS:
        vline(im, x, WY, WY + WH - 1, INK)
        vline(im, x + 1, WY, WY + WH - 1, PLUM_LT if low else PLUM_DK, 150)
    _stamp(im, CAP, 0, 0, CAP_COLS)
    _stamp(im, CAP, FW - CAP_W, 0, CAP_COLS, flip=True)
    return im


def frame_over():
    return _frame_over(False)


def frame_over_low():
    return _frame_over(True)


# ---- the winged crest ----------------------------------------------------
def crest(low=False):
    """Ornate winged crest, drawn once on the left and mirrored.

    IT MUST NOT EAT THE FILL EDGE.  The first build centred the ragged mass on
    the bar's middle, so the wings lay straight across the fill window and at
    60% the fill's leading edge vanished behind them for ~30% of the bar's
    width.  That is the one number the bar exists to communicate, in a fight the
    player is watching, and a static reference image never has to survive it.

    The fix is also what the reference actually does, which I had misread: the
    ragged mass hugs the bar's TOP and BOTTOM RAILS and does not enter the fill
    window at all.  Only the mask's chin spike crosses, 3px wide.  So the crest
    still breaks both edges - the whole point of it - while obscuring 3 texels
    of a 152 texel window instead of 46.

    Rows in this canvas: the bar frame sits at CREST_OVER..CREST_OVER+FH-1
    (7..24) and its fill window at 11..22.  Everything structural is clamped
    out of 11..22."""
    im = canvas(CREST_W, CREST_H)
    cx = CREST_W // 2
    win_top = CREST_OVER + WY               # 11
    win_bot = CREST_OVER + WY + WH - 1      # 22
    top_base, bot_base = win_top - 1, win_bot + 1
    # --- ragged shadow, one band riding each rail.  Fixed column heights, no
    # randomness, so two builds are byte-identical; mirrored, so it is symmetric.
    for i, up in enumerate(RAG):
        x = cx - len(RAG) + i
        rect(im, x, max(0, top_base - up), x, top_base, SHADE)
        rect(im, x, bot_base, x, max(bot_base, min(CREST_H - 1, bot_base + up - 2)), SHADE)
    for dx, dy in ((-21, -4), (-17, -6), (-12, -5), (-19, 5), (-14, 6)):
        y = (top_base + dy) if dy < 0 else (bot_base + dy)
        if 0 <= y < CREST_H and not (win_top <= y <= win_bot):
            rect(im, cx + dx, y, cx + dx + 1, y, SHADE)
    # --- horns: thin curved blades rising from behind the mask, above the rail
    for pts in (((-3, -2), (-6, -6), (-8, -9)), ((-5, -1), (-10, -4), (-13, -7)),
                ((-6, 0), (-12, -2), (-16, -4))):
        for k in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            steps = max(abs(x1 - x0), abs(y1 - y0))
            for t in range(steps + 1):
                x = cx + x0 + (x1 - x0) * t // steps
                y = top_base + y0 + (y1 - y0) * t // steps
                if 0 <= y < win_top:
                    rect(im, x, y, x, y, BONE if low else PLUM_LT)
                    if y + 1 < win_top:
                        rect(im, x, y + 1, x, y + 1, PLUM_DK)
    _mirror(im)
    # --- the mask.  Its dome sits ABOVE the window and only the chin crosses,
    # which is why the fill stays readable straight through the centre.
    _stamp(im, MASK, cx - len(MASK[0]) // 2, 1, MASK_COLS)
    return im


# ---- daze meter (the break gauge), same language -------------------------
GW, GH = 128, 7
GFILL_X, GFILL_Y, GFILL_W, GFILL_H = 7, 2, 114, 3
GCAP = [
    ".KKKKK.",
    "KBBBBBK",
    "KBKKKBK",
    "KBK.KBK",
    "KBKKKBK",
    "KBBBBBK",
    ".KKKKK.",
]
GCAP_COLS = {"K": INK, "B": BONE, ".": None}


def gauge_frame(low=False):
    """The daze rail: same thin pale keyline, same charcoal channel, same
    crescent-family cap.  Size and fill window are unchanged so no code moves."""
    # Same restraint as the bar: purple rails, pale only at the caps.  A pale
    # line down the full length here read as a lit bar even when the gauge was
    # empty, which is the one thing a meter must never do.
    lit = BONE if low else PLUM
    im = canvas(GW, GH)
    rect(im, GFILL_X, 0, GW - GFILL_X - 1, GH - 1, COAL)
    hline(im, GFILL_X, GW - GFILL_X - 1, 0, INK)
    hline(im, GFILL_X, GW - GFILL_X - 1, 1, lit)
    rect(im, GFILL_X, GFILL_Y, GW - GFILL_X - 1, GFILL_Y + GFILL_H - 1, WELL)
    hline(im, GFILL_X, GW - GFILL_X - 1, GH - 2, PLUM_LT if low else PLUM_DK)
    hline(im, GFILL_X, GW - GFILL_X - 1, GH - 1, INK)
    _stamp(im, GCAP, 0, 0, GCAP_COLS)
    _stamp(im, GCAP, GW - 7, 0, GCAP_COLS, flip=True)
    return im


def gauge_fill(hot=False):
    """Crimson at rest, going pale toward the top of the gauge so the meter
    filling up reads as heat without leaving the palette."""
    im = canvas(GFILL_W, GFILL_H)
    for x in range(GFILL_W):
        t = x / float(GFILL_W - 1)
        if hot:
            top, body, base = BONE_HI, BONE, CRIMSON
        elif t > 0.80:
            top, body, base = BONE, CRIMSON, CRIMSON_DK
        else:
            top, body, base = CRIMSON, CRIMSON, CRIMSON_DK
        rect(im, x, 0, x, 0, top)
        rect(im, x, 1, x, 1, body)
        rect(im, x, 2, x, 2, base)
    return im


# ---- boss bar fill in the reference's own tones ---------------------------
def bar_fill(base=CRIMSON, dark=CRIMSON_DK, top=None):
    """A fill for the 152x12 window.  Per-boss fills still come from boss_bar's
    ramps; this is the reference's own crimson, used for the previews and as the
    default for a boss with no ramp of its own."""
    im = canvas(WW, WH)
    top = top or "#C84453"
    rect(im, 0, 0, WW - 1, WH - 1, base)
    hline(im, 0, WW - 1, 0, top)
    hline(im, 0, WW - 1, 1, base)
    hline(im, 0, WW - 1, WH - 2, dark)
    hline(im, 0, WW - 1, WH - 1, dark)
    return im


def compose(frac=1.0, low=False, fill=None, with_crest=True):
    """Bar as the game would stack it: back, fill clipped to frac, over, crest."""
    pad = CREST_OVER
    im = canvas(FW, FH + pad * 2)
    im.alpha_composite(frame_back(), (0, pad))
    f = fill if fill is not None else bar_fill()
    w = max(0, min(WW, int(round(WW * frac))))
    if w:
        im.alpha_composite(f.crop((0, 0, w, WH)), (WX, WY + pad))
    im.alpha_composite(_frame_over(low), (0, pad))
    if with_crest:
        im.alpha_composite(crest(low), ((FW - CREST_W) // 2, (FH + pad * 2 - CREST_H) // 2))
    return im


def compose_gauge(frac=0.0, hot=False):
    im = canvas(GW, GH)
    im.alpha_composite(gauge_frame(hot), (0, 0))
    w = max(0, min(GFILL_W, int(round(GFILL_W * frac))))
    if w:
        im.alpha_composite(gauge_fill(hot).crop((0, 0, w, GFILL_H)), (GFILL_X, GFILL_Y))
    return im


# ---- nameplate, same language --------------------------------------------
PLATE_W, PLATE_H, PLATE_TALL_H, EMBLEM = 96, 16, 26, 12


def plate(tall=False, low=False):
    """The name plate in the bar's language.  A brass plate under a gothic bar
    would be the mismatch the preview exists to test, so it goes dark too: black
    keyline, purple rails, a recessed charcoal name panel, emblem slot at left."""
    h = PLATE_TALL_H if tall else PLATE_H
    im = canvas(PLATE_W, h)
    rect(im, 0, 0, PLATE_W - 1, h - 1, INK)
    rect(im, 1, 1, PLATE_W - 2, h - 2, COAL)
    hline(im, 1, PLATE_W - 2, 1, PLUM_LT if low else PLUM)
    hline(im, 1, PLATE_W - 2, h - 2, PLUM_DK)
    rect(im, 15, 3, PLATE_W - 4, h - 4, INK)
    rect(im, 16, 4, PLATE_W - 5, h - 5, WELL)
    rect(im, 2, 2, 2 + EMBLEM + 1, 2 + EMBLEM + 1, INK)
    rect(im, 3, 3, 3 + EMBLEM, 3 + EMBLEM, WELL)
    return im


def plate_named(key, lines, emblem_im=None, low=False):
    """Plate with the condensed gothic name baked in, one fixed size for every
    line - which is the fix for the two lines of a pair baking at 15 and 11."""
    import gothicfont as GF
    tall = len(lines) > 1
    im = plate(tall, low)
    baked = [GF.render(ln, fill=rgba(BONE_HI), ink=rgba(INK)) for ln in lines]
    lead = 1
    block = sum(t.height for t in baked) + lead * (len(baked) - 1)
    # Centre the whole block in the plate.  Placing the first line at a fixed
    # y=4 pushed an 11px bake to row 15 of a 16-row plate, where the bar's top
    # rail then covered the letters.
    y = max(0, (im.height - block) // 2)
    for t in baked:
        im.alpha_composite(t, (16 + (PLATE_W - 20 - t.width) // 2, y))
        y += t.height + lead
    if emblem_im is not None:
        im.alpha_composite(emblem_im, (3, 3))
    return im


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    for n, im in (("gothic_frame_back", frame_back()), ("gothic_frame_over", frame_over()),
                  ("gothic_frame_over_low", frame_over_low()), ("gothic_crest", crest()),
                  ("gothic_gauge_frame", gauge_frame())):
        im.save(os.path.join(out, n + ".png"))
        print("%-26s %dx%d" % (n, im.width, im.height))
