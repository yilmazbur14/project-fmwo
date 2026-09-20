"""Boss nameplate and emblem art.

Imports vs_card.textart, so the HUD nameplate is literally the same lettering
bake as the VS cards - Pixelify Sans, hard-edge threshold at 40, and the B/5
glyph repairs. Without those repairs BIXBY renders as GIXGY and FIGHT 05 as
FIGHT OS, because the font builds its capitals from a rounded-rect ring and two
of its cuts are wrong.

Emblems come from vs_card.emblems and the roster from vs_card.bosses, so a boss
cannot drift between its card and its health bar.
"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))          # art_source/, so vs_card is a package
from PIL import Image
from barlib import *
from vs_card import textart, bosses, emblems

NAME_MAX_W, NAME_MAX_H = 66, 10     # 72 let '& COMPUTAH' touch the plate border
PLATE_TALL_H = 26                                   # pairs need two lines


def fit_size(text, max_w=NAME_MAX_W, max_h=NAME_MAX_H, lo=7, hi=20):
    """Largest Pixelify size whose baked ink fits the plate's name slot."""
    best = lo
    for s in range(hi, lo - 1, -1):
        im = textart.bake(text, s, ol_w=0, shadow=(0, 0))
        if im.width <= max_w and im.height <= max_h:
            best = s
            break
    return best


def name_art(text, max_w=NAME_MAX_W):
    """Baked at native HUD scale - export_all writes the 3x companion."""
    s = fit_size(text, max_w)
    return textart.bake(text, s, fill="#FFFFFF", ol_w=0, shadow=(0, 0)), s


def emblem(key, size=EMBLEM):
    """vs_card's emblem, re-centred into a square slot.

    emblem(name, w, h) places its shape at (0.80w, h/2) with half-size 0.40h, so
    asking for a 30x15 box puts a 12x12 emblem at (18,1)..(30,13) - crop that."""
    from PIL import ImageDraw
    b = bosses.by_key(key)
    shape, col, _ = b["mark"]
    box_w, box_h = 30, int(round(size / 0.8))
    im = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for pts in emblems.emblem(shape, box_w, box_h):
        d.polygon([tuple(p) for p in pts], fill=rgba(col))
    cx, arm = int(box_w * 0.80), int(box_h * 0.40)
    out = im.crop((cx - arm, box_h // 2 - arm, cx + arm, box_h // 2 + arm))
    return out.resize((size, size), Image.NEAREST) if out.size != (size, size) else out


def plate(tall=False):
    """Shared plate: brass chrome, a recessed name panel, emblem slot at left.

    Deliberately NOT per-boss - identity comes from the emblem dropped in the
    slot and from a code-side modulate on the hairlines, not from 10 plates."""
    h = PLATE_TALL_H if tall else PLATE_H
    im = canvas(PLATE_W, h)
    brass_box(im, 0, 0, PLATE_W - 1, h - 1)
    well_box(im, 16, 3, PLATE_W - 4, h - 4)
    rect(im, 2, 2, 2 + EMBLEM + 1, 2 + EMBLEM + 1, KEY)      # emblem slot
    rect(im, 3, 3, 3 + EMBLEM - 1, 3 + EMBLEM - 1, WELL)
    hline(im, 17, PLATE_W - 5, 4, BRASS_HI, 120)             # accent hairlines
    hline(im, 17, PLATE_W - 5, h - 5, BRASS_HI, 70)
    stud(im, 1, h - 5)
    stud(im, PLATE_W - 5, 1)
    return im


def plate_lines(key):
    """Name lines for a plate. Pairs stack two, which is why they need the tall
    plate: GREYSON & COMPUTAH is far too wide for a 72px slot on one line."""
    b = bosses.by_key(key)
    return list(b["name"])


if __name__ == "__main__":
    for b in bosses.BOSSES:
        for line in b["name"]:
            im, s = name_art(line)
            print("%-10s %-20s size %2d  %dx%d" % (b["key"], line, s, im.width, im.height))
