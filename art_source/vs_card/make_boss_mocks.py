"""Mocked ladder cards (layout C) for every boss, for review before finalising.

  python make_boss_mocks.py <out_dir> [key ...]
"""
import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from card import NW, NH, SCALE, band_halves, backdrop, up, hx
from pxlib import outline
import textart, bosses
import bust_burak

BH, BY, ST, SB = 132, 122, 350, 290
BX, BY_B, EX, EY_B = 86, 14, 404, 14
SEAM_MID = ST + (SB - ST) * 0.5 + 6
PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"


def boss_bust(key):
    m = importlib.import_module("bust_" + key)
    im = m.build()
    outline(im)
    return im


def badge(boss, idx=2):
    ring = Image.open(PROJ + "/Assets/UI/Screens/rank_slot.png").convert("RGBA").crop((idx * 40, 0, idx * 40 + 40, 40))
    src = Image.open(PROJ + "/Assets/Characters/" + boss["portrait"]).convert("RGBA")
    bb = src.getbbox()
    src = src.crop(bb) if bb else src
    s = max(src.width, src.height)
    pad = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pad.alpha_composite(src, ((s - src.width) // 2, (s - src.height) // 2))
    pad = pad.resize((28, 28), Image.NEAREST)
    out = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    out.alpha_composite(pad, (6, 6))
    out.alpha_composite(ring, (0, 0))
    return out


def card(boss):
    burak = bust_burak.build(); outline(burak)
    L, R = band_halves(NW, BH, ST, SB, burak, boss_bust(boss["key"]), BX, BY_B, EX, EY_B,
                       ramp_b=boss["ramp"], accent=boss["accent"], mark=boss["mark"],
                       ramp_a=bosses.BURAK_RAMP, stripe=bosses.BURAK_STRIPE)
    bg = backdrop(0.22)
    d = ImageDraw.Draw(bg)
    d.rectangle([0, 0, NW, BY - 30], fill=hx("#15131F"))
    d.rectangle([0, BY + BH + 30, NW, NH], fill=hx("#15131F"))
    d.line([(0, BY - 30), (NW, BY - 30)], fill=hx("#3F3F74"))
    d.line([(0, BY + BH + 30), (NW, BY + BH + 30)], fill=hx("#3F3F74"))
    bg.alpha_composite(L, (0, BY))
    bg.alpha_composite(R, (0, BY))
    bg.alpha_composite(badge(boss), (NW - 58, BY + BH + 42))
    img = up(bg)

    def put(im, x, y):
        img.alpha_composite(im, (x, y))

    vs = textart.bake("VS", 200)
    put(vs, int(SEAM_MID * SCALE - vs.width / 2), int((BY + BH / 2) * SCALE - vs.height / 2))

    # name plate: right-aligned, stacked upward from a fixed baseline
    rx, by = int(NW * 0.93) * SCALE, (BY + BH - 14) * SCALE
    lines = [textart.bake(t, boss["name_size"]) for t in boss["name"]]
    y = by
    for im in reversed(lines):
        y -= im.height
        put(im, rx - im.width, y)
        y -= 6

    put(textart.bake("FIGHT %02d" % boss["fight"], 33, fill="#9BADB7"), 18 * SCALE, (BY - 64) * SCALE)
    put(textart.bake(boss["epithet"], 33, fill="#CDD7E2"), 18 * SCALE, (BY + BH + 46) * SCALE)
    win = textart.bake("WIN " + boss["rank"], 33, fill="#F2C457") if boss["rank"] \
        else textart.bake("THE INVITE", 33, fill="#F2C457")
    put(win, (NW - 68) * SCALE - win.width, (BY + BH + 54) * SCALE)
    return img


if __name__ == "__main__":
    out = sys.argv[1]
    keys = sys.argv[2:] or [b["key"] for b in bosses.card_roster()]
    os.makedirs(out, exist_ok=True)
    for k in keys:
        b = bosses.by_key(k)
        p = os.path.join(out, "card_%02d_%s.png" % (b["fight"], k))
        card(b).convert("RGB").save(p)
        print(p)
