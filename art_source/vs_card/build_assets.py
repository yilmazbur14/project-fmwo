"""Builds the shippable VS-card assets and prints the placement contract.

  python build_assets.py <out_dir> [boss_key ...]

Layout is authored at 640x360 and scaled 3x, matching the rest of the game's
full-screen art. Lettering is baked at final screen resolution and drawn at
scale 1, which is what Godot already does with Labels under the project's
canvas_items stretch at a 1920x1080 base.

Output is deterministic: no randomness, no timestamps, so two runs give
byte-identical PNGs.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from card import (NW, NH, SCALE, band_halves, backdrop, mask_from_poly, up, hx)
from pxlib import outline
import textart, bosses
import bust_burak

PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"

# ---- the one layout table everything derives from (native 640x360 units) ----
BH, BY = 132, 122                 # band height and top edge
ST, SB = 350, 290                 # diagonal split: x at the band's top / bottom
BX, BY_B = 86, 14                 # Burak bust origin inside the band
EX, EY_B = 404, 14                # boss bust origin inside the band
LETTER_TOP, LETTER_BOT = BY - 30, BY + BH + 30     # letterbox inner edges
SEAM_MID = ST + (SB - ST) * 0.5 + 6                # x the VS centres on
VS_SIZE, NAME_SIZE, SMALL_SIZE = 200, 99, 33
BADGE_AT = (NW - 58, BY + BH + 42)


def busts_for(boss_key):
    import importlib
    b = bust_burak.build(); outline(b)
    e = importlib.import_module("bust_" + boss_key).build(); outline(e)
    return b, e


def badge(boss, idx=2):
    ring = Image.open(PROJ + "/Assets/UI/Screens/rank_slot.png").convert("RGBA").crop((idx * 40, 0, idx * 40 + 40, 40))
    por = Image.open(PROJ + "/Assets/Characters/" + boss["portrait"]).convert("RGBA").crop((18, 6, 46, 34))
    out = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    out.alpha_composite(por, (6, 6))
    out.alpha_composite(ring, (0, 0))
    return out


def save(img, path):
    img.save(path, optimize=False)
    return path


# ---- the two FX pieces the slam frame needs, so the coder isn't guessing ----
BURST_R = 480          # canvas is 2*BURST_R square, spokes centred


def seam_flash(accent_unused=None):
    """White flare along the diagonal, native 640x132, drawn over both halves."""
    from PIL import ImageDraw
    im = Image.new("RGBA", (NW, BH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for o in range(-3, 4):
        d.line([(ST + o, 0), (SB + o, BH)], fill=hx("#FFFFFF"), width=2)
    return im


def vs_burst():
    """Radial spokes + ring, screen resolution, centred on the VS."""
    import math
    from PIL import ImageDraw
    im = Image.new("RGBA", (BURST_R * 2, BURST_R * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = BURST_R
    for k in range(20):
        a = k * (math.pi * 2 / 20) + 0.14
        r0, r1 = 150, 150 + (330 if k % 2 == 0 else 200)
        d.line([(c + math.cos(a) * r0, c + math.sin(a) * r0),
                (c + math.cos(a) * r1, c + math.sin(a) * r1)], fill=hx("#FFFFFF"), width=7)
    d.ellipse([c - 168, c - 168, c + 168, c + 168], outline=hx("#FFFFFF"), width=9)
    return im


def build(boss, out_dir, shared=True):
    k = boss["key"]
    os.makedirs(out_dir, exist_ok=True)
    burak, boss_bust = busts_for(k)
    L, R = band_halves(NW, BH, ST, SB, burak, boss_bust, BX, BY_B, EX, EY_B,
                       ramp_b=boss["ramp"], accent=boss["accent"], mark=boss["mark"],
                       ramp_a=bosses.BURAK_RAMP, stripe=bosses.BURAK_STRIPE)
    made = {}
    if shared:
        made["band_left"] = save(L, os.path.join(out_dir, "band_left.png"))
        made["vs"] = save(textart.bake("VS", VS_SIZE), os.path.join(out_dir, "vs.png"))
        made["bust_burak"] = save(burak, os.path.join(out_dir, "bust_burak.png"))
        made["seam_flash"] = save(seam_flash(), os.path.join(out_dir, "seam_flash.png"))
        made["vs_burst"] = save(vs_burst(), os.path.join(out_dir, "vs_burst.png"))
    made["band_right"] = save(R, os.path.join(out_dir, "band_right_%s.png" % k))
    made["bust"] = save(boss_bust, os.path.join(out_dir, "bust_%s.png" % k))
    if len(boss["name"]) == 1:
        made["name"] = save(textart.bake(boss["name"][0], boss["name_size"]),
                            os.path.join(out_dir, "name_%s.png" % k))
    else:
        for i, line in enumerate(boss["name"]):
            made["name_%s" % "ab"[i]] = save(textart.bake(line, boss["name_size"]),
                                             os.path.join(out_dir, "name_%s_%s.png" % (k, "ab"[i])))
    made["epithet"] = save(textart.bake(boss["epithet"], SMALL_SIZE, fill="#CDD7E2"),
                           os.path.join(out_dir, "epithet_%s.png" % k))
    made["fight"] = save(textart.bake("FIGHT %02d" % boss["fight"], SMALL_SIZE, fill="#9BADB7"),
                         os.path.join(out_dir, "fight_%02d.png" % boss["fight"]))
    wtext = ("WIN " + boss["rank"]) if boss["rank"] else "THE INVITE"
    wkey = boss["rank"].lstrip("@") or "invite"
    made["win"] = save(textart.bake(wtext, SMALL_SIZE, fill="#F2C457"),
                       os.path.join(out_dir, "win_%s.png" % wkey))
    made["badge"] = save(badge(boss), os.path.join(out_dir, "badge_%s.png" % k))
    return made


def placements(boss, out_dir):
    """Top-left placement of every baked image in the 1920x1080 canvas."""
    k = boss["key"]
    g = lambda n: Image.open(os.path.join(out_dir, n))
    P = {}
    P["band_left.png"] = (0, BY * SCALE, "scale 3")
    P["band_right_%s.png" % k] = (0, BY * SCALE, "scale 3")
    vs = g("vs.png")
    P["vs.png"] = (int(SEAM_MID * SCALE - vs.width / 2), int((BY + BH / 2) * SCALE - vs.height / 2), "scale 1")
    rx, by = int(NW * 0.93) * SCALE, (BY + BH - 14) * SCALE
    names = ["name_%s.png" % k] if len(boss["name"]) == 1 else             ["name_%s_%s.png" % (k, c) for c in "ab"[:len(boss["name"])]]
    yy = by
    for n in reversed(names):
        nm = g(n)
        yy -= nm.height
        P[n] = (rx - nm.width, yy, "scale 1")
        yy -= 6
    P["fight_%02d.png" % boss["fight"]] = (18 * SCALE, (BY - 64) * SCALE, "scale 1")
    P["epithet_%s.png" % k] = (18 * SCALE, (BY + BH + 46) * SCALE, "scale 1")
    wkey = boss["rank"].lstrip("@") or "invite"
    wn = g("win_%s.png" % wkey)
    P["win_%s.png" % wkey] = ((NW - 68) * SCALE - wn.width, (BY + BH + 54) * SCALE, "scale 1")
    P["badge_%s.png" % k] = (BADGE_AT[0] * SCALE, BADGE_AT[1] * SCALE, "scale 3")
    return P


def compose_check(boss, out_dir):
    """Rebuild the card purely from the shipped files, to prove the contract."""
    img = up(backdrop(0.22))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, NW * SCALE, LETTER_TOP * SCALE], fill=hx("#15131F"))
    d.rectangle([0, LETTER_BOT * SCALE, NW * SCALE, NH * SCALE], fill=hx("#15131F"))
    d.rectangle([0, LETTER_TOP * SCALE, NW * SCALE, LETTER_TOP * SCALE + 2], fill=hx("#3F3F74"))
    d.rectangle([0, LETTER_BOT * SCALE, NW * SCALE, LETTER_BOT * SCALE + 2], fill=hx("#3F3F74"))
    for name, (x, y, sc) in placements(boss, out_dir).items():
        im = Image.open(os.path.join(out_dir, name)).convert("RGBA")
        if sc == "scale 3":
            im = up(im)
        img.alpha_composite(im, (x, y))
    return img


if __name__ == "__main__":
    out = sys.argv[1]
    keys = sys.argv[2:] or [b["key"] for b in bosses.card_roster()]
    for i, k in enumerate(keys):
        b = bosses.by_key(k)
        made = build(b, out, shared=(i == 0))
        for n, p in sorted(made.items()):
            im = Image.open(p)
            print("%-14s %-28s %dx%d" % (n, os.path.basename(p), im.width, im.height))
        print()
        for n, (x, y, sc) in sorted(placements(b, out).items()):
            print("   %-26s at (%4d,%4d)  %s" % (n, x, y, sc))
