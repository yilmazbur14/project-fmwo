"""Builds the three VS-card layout variants at 1920x1080."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from card import *
from pxlib import hx, outline
import bust_burak, bust_eric

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"


def busts():
    b = bust_burak.build(); outline(b)
    e = bust_eric.build(); outline(e)
    return b, e


def seam_x(split_top, split_bot, h, y):
    return split_top + (split_bot - split_top) * (y / float(h))


def avatar_ring(idx=2):
    """Eric's dialogue portrait dropped into the ladder's rank ring - the one
    place the existing 64x64 bust is still exactly the right tool."""
    ring = Image.open(PROJ + "/Assets/UI/Screens/rank_slot.png").convert("RGBA").crop((idx * 40, 0, idx * 40 + 40, 40))
    por = Image.open(PROJ + "/Assets/Characters/Eric/portrait.png").convert("RGBA").crop((18, 6, 46, 34))
    out = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    out.alpha_composite(por, (6, 6))
    out.alpha_composite(ring, (0, 0))
    return out


# =====================================================================  A
def variant_a(b, e):
    """Platinum-faithful: one 5:1 banner across a darkened arena."""
    bg = backdrop(0.30)
    BH, BY, ST, SB = 132, 114, 350, 290
    band = build_band(NW, BH, ST, SB, b, e, bx=86, by=14, ex=404, ey=14)
    bg.alpha_composite(band, (0, BY))
    img = up(bg)

    vy = BH // 2
    vx = seam_x(ST, SB, BH, vy) + 6
    put_text(img, (int(vx) * SCALE, (BY + vy) * SCALE), "VS", 200, anchor="cc")
    rx = int(NW * 0.93) * SCALE
    put_text(img, (rx, (BY + BH - 14) * SCALE), "ERIC", 99, anchor="rb")
    put_text(img, (rx, (BY + BH - 14) * SCALE - 108, ), "@regular", 33, anchor="rb", fill="#F2C457")
    return img


# =====================================================================  B
def variant_b(b, e):
    """Full-bleed clash. Busts shown here as a 2x upscale of the 116x120 art -
    the final would want them redrawn at ~232x240 so the pixel size still
    matches the 3x the rest of the game renders at."""
    b2 = b.resize((b.width * 2, b.height * 2), Image.NEAREST)
    e2 = e.resize((e.width * 2, e.height * 2), Image.NEAREST)
    ST, SB = 372, 268
    card = build_band(NW, NH, ST, SB, b2, e2, bx=6, by=116, ex=392, ey=116)
    img = up(card)

    vx = seam_x(ST, SB, NH, 150) + 8
    put_text(img, (int(vx) * SCALE, 150 * SCALE), "VS", 300, anchor="cc")
    yb = int(NH * 0.975) * SCALE
    put_text(img, (int(NW * 0.94) * SCALE, yb), "ERIC", 132, anchor="rb")
    put_text(img, (int(NW * 0.94) * SCALE, yb - 146), "@regular", 55, anchor="rb", fill="#F2C457")
    put_text(img, (int(NW * 0.19) * SCALE, yb), "BURAK", 99, anchor="lb")
    put_text(img, (int(NW * 0.19) * SCALE, yb - 110), "@everyone", 33, anchor="lb", fill="#9BADB7")
    return img


# =====================================================================  C
def variant_c(b, e):
    """The band, wrapped in the game's own Discord-ladder furniture."""
    bg = backdrop(0.22)
    d = ImageDraw.Draw(bg)
    BH, BY, ST, SB = 132, 122, 350, 290
    d.rectangle([0, 0, NW, BY - 30], fill=hx("#15131F"))
    d.rectangle([0, BY + BH + 30, NW, NH], fill=hx("#15131F"))
    d.line([(0, BY - 30), (NW, BY - 30)], fill=hx("#3F3F74"))
    d.line([(0, BY + BH + 30), (NW, BY + BH + 30)], fill=hx("#3F3F74"))

    band = build_band(NW, BH, ST, SB, b, e, bx=86, by=14, ex=404, ey=14)
    bg.alpha_composite(band, (0, BY))
    bg.alpha_composite(avatar_ring(2), (NW - 58, BY + BH + 42))
    img = up(bg)

    vy = BH // 2
    vx = seam_x(ST, SB, BH, vy) + 6
    put_text(img, (int(vx) * SCALE, (BY + vy) * SCALE), "VS", 200, anchor="cc")
    rx = int(NW * 0.93) * SCALE
    put_text(img, (rx, (BY + BH - 14) * SCALE), "ERIC", 99, anchor="rb")
    put_text(img, (18 * SCALE, (BY - 64) * SCALE), "FIGHT 01", 33, anchor="lt", fill="#9BADB7")
    put_text(img, (18 * SCALE, (BY + BH + 46) * SCALE), "THE WHITE KNIGHT", 33, anchor="lt", fill="#CDD7E2")
    put_text(img, ((NW - 68) * SCALE, (BY + BH + 54) * SCALE), "WIN  @regular", 33, anchor="rt", fill="#F2C457")
    return img


if __name__ == "__main__":
    b, e = busts()
    for name, fn in (("A_band", variant_a), ("B_fullscreen", variant_b), ("C_ladder", variant_c)):
        img = fn(b, e)
        p = os.path.join(OUT, "vs_card_%s.png" % name)
        img.convert("RGB").save(p)
        print(p, img.size)
