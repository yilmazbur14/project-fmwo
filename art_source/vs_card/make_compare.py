"""Comparison sheets: the shipped sprite beside the new bust, at the SAME zoom.

Both render at 3x in game, so showing them at one common zoom is the honest
check - if the pixels are the same size and the bust still looks smoother or
more tonal than the sprite, the bust is wrong.

  python make_compare.py <out_dir> [key ...]
"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from pxlib import outline
import textart

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"
CH = PROJ + "/Assets/Characters/"
ZOOM = 5
BG = (34, 32, 52, 255)

# key -> [(sheet, crop-box or None), ...] of the shipped frames to sit alongside
SHIPPED = {
    "burak":   [("MainPlayer/player_4dir_sheet.png", (0, 64, 32, 96)),
                ("MainPlayer/player_4dir_sheet.png", (0, 0, 32, 32))],
    "eric":    [("Eric/eric_sheet_v2.png", (57, 40, 164, 192))],
    "greyson": [("Greyson/greyson_idle.png", (0, 0, 64, 96)),
                ("Computah/computah_idle.png", (0, 0, 64, 64))],
    "mason":   [("Mason/mason.png", None)],
    "josh":    [("Josh/josh_idle.png", (0, 0, 64, 80))],
    "danny":   [("Danny/Sumo/danny_sumo_idle.png", (0, 0, 176, 144))],
    "carter":  [("Carter/carter_akuma.png", (0, 0, 96, 96))],
    "liam":    [("Bixby/bixby_beast.png", (0, 0, 192, 160)),
                ("Liam/liam.png", None)],
    "jordan":  [("Jordan/jordan_redesign_v2.png", (0, 0, 96, 96))],     # v2 idle, the bust's source
}


def load(p, box):
    im = Image.open(CH + p).convert("RGBA")
    if box:
        im = im.crop(box)
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def sheet(key):
    bust = importlib.import_module("bust_" + key).build()
    outline(bust)
    tiles = [load(p, b) for p, b in SHIPPED[key]] + [bust]
    labels = ["SHIPPED SPRITE"] * len(SHIPPED[key]) + ["NEW VS BUST"]
    zt = [t.resize((t.width * ZOOM, t.height * ZOOM), Image.NEAREST) for t in tiles]
    lab = [textart.bake(s, 33, fill="#9BADB7", ol_w=1, shadow=(0, 2)) for s in labels]
    pad, gap = 20, 28
    W = sum(max(z.width, l.width) for z, l in zip(zt, lab)) + gap * (len(zt) - 1) + pad * 2
    HH = max(z.height for z in zt) + max(l.height for l in lab) + 14 + pad * 2
    out = Image.new("RGBA", (W, HH), (18, 17, 24, 255))
    x, rowh = pad, max(zz.height for zz in zt)
    for z, l in zip(zt, lab):
        col = max(z.width, l.width)
        zx, zy = x + (col - z.width) // 2, pad + (rowh - z.height) // 2
        out.alpha_composite(Image.new("RGBA", z.size, BG), (zx, zy))
        out.alpha_composite(z, (zx, zy))
        out.alpha_composite(l, (x + (col - l.width) // 2, pad + rowh + 12))
        x += col + gap
    return out


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k in (sys.argv[2:] or list(SHIPPED)):
        p = os.path.join(out, "compare_%s.png" % k)
        sheet(k).convert("RGB").save(p)
        print(p)
