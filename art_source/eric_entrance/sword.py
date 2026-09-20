"""The sword buried in the mat for the entrance - the one he pulls out.

eric_sword_planted_v2.png is the pose a THROWN blade lands in: about 107 texels
of blade standing proud of the mat, which is correct for a sword that has just
come down point-first and is why it reads as a grey pillar. That asset is
approved and doing its own job in the fight; this is a separate one.

Here the blade is sunk so only the last stretch shows, putting the grip at a
height a man can reach down and take.

HOW TALL IT IS ALLOWED TO BE.  A 40-frame sweep of eric_sheet_v2 measured every
gripping hand: the minimum anywhere is 19 texels above his feet, and the
waist-height poses that suit a planted hilt - frames 0, 24, 25 and 26 - sit at
22 to 25.  (An earlier note here claimed 3 texels.  That was a sabaton, not a
hand, and it drove a whole plan toward burying this deeper.  It is wrong.)

So the reach constraint binds only the GRIP, not the whole sword, and a long
grip decouples the two: the crossguard sits 17 above the mat with a real length
of blade below it, the grip runs from there up to 40, and his hand closes on its
bottom third at 22-25 - which is how you actually take a greatsword out of the
ground.  Above-ground total is 46 texels, about 62% of his 74-texel body.  The
first version showed 34 and read as a hydrant at ring distance; a later attempt
fixed that by widening the blade and read as an anvil.  Width was the mistake.
Narrow and tall is what says "sword" in silhouette.

Palette is sampled from eric_sword_planted_v2.png so the two read as the same
steel; nothing here is invented.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vs_card"))
from collections import Counter
from PIL import Image
from pxlib import canvas, poly, plate, seam, px, hx, black_ratio

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
SRC = PROJ + "/Assets/Characters/Eric/eric_sword_planted_v2.png"

W, H = 64, 56
CONTACT = (32, 46)              # the texel the blade enters the mat on
GRIP_CENTRE = (32, 23)          # what his hand closes on - 23 above the contact

ST_HI, ST_LT, ST, ST_MD, ST_SH, ST_DK = "#D4D8DC", "#A3A8AE", "#7C8187", "#5C6067", "#41444B", "#2B2D33"
WD_LT, WD, WD_DK = "#9C6038", "#74432A", "#4E2C1C"
DIRT_LT, DIRT, DIRT_DK = "#74432A", "#4E2C1C", "#331C12"
BK = "#000000"


def source_palette():
    im = Image.open(SRC).convert("RGBA")
    return Counter(q[:3] for q in im.getdata() if q[3] > 128)


SOCKET_W, SOCKET_H = 64, 20
SOCKET_CONTACT = (32, 8)


def build(with_sword=True, w=None, h=None, contact=None):
    """with_sword=False gives the socket left behind after the pull: the same
    mound and crack set, with a dark slot where the blade stood."""
    im = canvas(w or W, h or H)
    cx, gy = contact or CONTACT

    # --- disturbed mat: mound around the entry, then cracks running out ----
    plate(im, [(cx - 17, gy - 2), (cx + 17, gy - 2), (cx + 20, gy + 3), (cx + 14, gy + 6),
               (cx - 14, gy + 6), (cx - 20, gy + 3)], DIRT, hi=DIRT_LT, sh=DIRT_DK)
    poly(im, [(cx - 11, gy - 1), (cx + 11, gy - 1), (cx + 9, gy + 2), (cx - 9, gy + 2)], DIRT_DK)
    for x0, y0, x1, y1 in ((cx - 19, gy + 4, cx - 29, gy + 7), (cx - 22, gy + 2, cx - 31, gy + 1),
                           (cx + 19, gy + 4, cx + 29, gy + 6), (cx + 21, gy + 1, cx + 30, gy - 1),
                           (cx - 8, gy + 6, cx - 13, gy + 10), (cx + 9, gy + 6, cx + 15, gy + 9)):
        seam(im, [(x0, y0), (x1, y1)], BK)
    for sx, sy in ((cx - 25, gy + 5), (cx + 26, gy + 3), (cx - 14, gy + 9), (cx + 17, gy + 8)):
        px(im, [(sx, sy), (sx + 1, sy)], DIRT_DK)

    if not with_sword:
        # the slot the blade stood in, still open
        plate(im, [(cx - 6, gy - 5), (cx + 6, gy - 5), (cx + 5, gy + 1), (cx - 5, gy + 1)],
              DIRT_DK, hi=DIRT, sh=DIRT_DK)
        poly(im, [(cx - 4, gy - 4), (cx + 4, gy - 4), (cx + 3, gy), (cx - 3, gy)], BK)
        return im

    # --- blade: only the last stretch shows, widening as it leaves the mat --
    plate(im, [(cx - 6, gy - 17), (cx + 6, gy - 17), (cx + 5, gy + 1), (cx - 5, gy + 1)],
          ST, hi=ST_LT, sh=ST_DK)
    poly(im, [(cx + 2, gy - 17), (cx + 5, gy - 17), (cx + 4, gy + 1), (cx + 1, gy + 1)], ST_MD)
    seam(im, [(cx - 2, gy - 16), (cx - 2, gy - 1)], ST_LT)
    px(im, [(cx - 4, gy - 14), (cx + 3, gy - 10), (cx - 4, gy - 6)], ST_HI)

    # --- crossguard --------------------------------------------------------
    plate(im, [(cx - 13, gy - 22), (cx + 13, gy - 22), (cx + 14, gy - 19), (cx + 10, gy - 17),
               (cx - 10, gy - 17), (cx - 14, gy - 19)], ST, hi=ST_LT, sh=ST_DK)
    poly(im, [(cx - 12, gy - 21), (cx + 5, gy - 21), (cx + 5, gy - 20), (cx - 12, gy - 20)], ST_HI)
    poly(im, [(cx + 6, gy - 21), (cx + 13, gy - 21), (cx + 13, gy - 19), (cx + 6, gy - 19)], ST_MD)

    # --- grip: wrapped leather, the part his hand closes on ----------------
    plate(im, [(cx - 3, gy - 40), (cx + 3, gy - 40), (cx + 3, gy - 21), (cx - 3, gy - 21)],
          WD, hi=WD_LT, sh=WD_DK)
    for y in range(gy - 38, gy - 21, 3):
        seam(im, [(cx - 3, y), (cx + 2, y + 1)], WD_DK)
    px(im, [(cx - 2, gy - 37), (cx - 2, gy - 33), (cx - 2, gy - 29), (cx - 2, gy - 25)], WD_LT)

    # --- pommel ------------------------------------------------------------
    plate(im, [(cx - 5, gy - 46), (cx + 5, gy - 46), (cx + 6, gy - 43), (cx + 3, gy - 39),
               (cx - 3, gy - 39), (cx - 6, gy - 43)], ST, hi=ST_LT, sh=ST_DK)
    px(im, [(cx - 3, gy - 45), (cx - 2, gy - 45), (cx - 1, gy - 45)], ST_HI)
    return im


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    im = build()
    src = source_palette()
    mine = {q[:3] for q in im.convert("RGBA").getdata() if q[3] > 128}
    k, o, pct = black_ratio(im)
    print("buried sword %dx%d   contact %s   grip centre %s" % (W, H, CONTACT, GRIP_CENTRE))
    print("  above ground: %d texels   grip grabbable at %d above the contact"
          % (46, CONTACT[1] - GRIP_CENTRE[1]))
    print("  black %.1f%%   %d colours   not in eric_sword_planted_v2: %s"
          % (pct, len(mine), sorted("#%02X%02X%02X" % c for c in mine - set(src)) or "none"))
    im.save(os.path.join(out, "eric_sword_entrance_planted.png"), optimize=False)
    sock = build(False, SOCKET_W, SOCKET_H, SOCKET_CONTACT)
    sock.save(os.path.join(out, "eric_sword_socket.png"), optimize=False)
    print("socket %dx%d  contact %s" % (SOCKET_W, SOCKET_H, SOCKET_CONTACT))
    sb = Image.new("RGBA", (SOCKET_W, SOCKET_H), (96, 128, 76, 255))
    sb.alpha_composite(sock)
    sb.resize((SOCKET_W * 8, SOCKET_H * 8), Image.NEAREST).convert("RGB").save(
        os.path.join(out, "_socket.png"))
    bg = Image.new("RGBA", (W, H), (96, 128, 76, 255))
    bg.alpha_composite(im)
    bg.resize((W * 8, H * 8), Image.NEAREST).convert("RGB").save(os.path.join(out, "_buried_sword.png"))
