"""Builds the review images for the Greyson & Computah design pass.

    python previews.py <wip_dir> <out_dir>

<wip_dir> holds the per-pose PNGs produced by greyson.py / computah.py.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

BG = (58, 58, 70)
BG2 = (48, 48, 58)
INK = (232, 236, 245)
DIM = (150, 158, 175)
PROJ = "C:/Users/theyi/OneDrive/Documents/new-game-project"


def font(sz):
    for p in ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def nn(im, z):
    return im.resize((im.width * z, im.height * z), Image.NEAREST)


def frames(path, fw, fh):
    im = Image.open(path).convert("RGBA")
    return [im.crop((i * fw, 0, i * fw + fw, fh)) for i in range(im.width // fw)]


def plate(w, h, checker=False):
    im = Image.new("RGB", (w, h), BG)
    if checker:
        d = ImageDraw.Draw(im)
        for y in range(0, h, 16):
            for x in range(0, w, 16):
                if ((x // 16) + (y // 16)) % 2:
                    d.rectangle([x, y, x + 15, y + 15], fill=BG2)
    return im


# ---------------------------------------------------------------------------
def contact_sheet(wip, out):
    z = 6
    cells = [
        ("greyson_hero.png", 96, "GREYSON - idle, hair A (mid)", "96x96, feet row 95"),
        ("greyson_hair_long.png", 96, "GREYSON - idle, hair B (long)", "same pose, mane"),
        ("greyson_windup.png", 96, "GREYSON - punch wind-up", "rear fist chambered, lead fist at camera"),
        ("greyson_phase2.png", 96, "GREYSON - phase 2 (concept)", "lost Computah: rage, holds the antenna"),
        ("computah_hero.png", 64, "COMPUTAH - idle / hero", "64x64, feet row 63, battery FULL"),
        ("computah_charge.png", 64, "COMPUTAH - charging", "battery HALF"),
        ("computah_dead.png", 64, "COMPUTAH - battery dead", "the punish window"),
        ("computah_phase2.png", 64, "COMPUTAH - phase 2 (concept)", "lost Greyson: overclocked, core blown"),
    ]
    cw, chh = 96 * z + 40, 96 * z + 74
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    im = plate(cw * cols, chh * rows + 96, checker=True)
    d = ImageDraw.Draw(im)
    d.text((22, 16), "GREYSON & COMPUTAH - design pass, every pose at 6x",
           font=font(26), fill=INK)
    for i, (fn, size, title, sub) in enumerate(cells):
        cx = (i % cols) * cw
        cy = (i // cols) * chh + 54
        sp = nn(Image.open(os.path.join(wip, fn)).convert("RGBA"), z)
        px = cx + (cw - sp.width) // 2
        py = cy + 30 + (96 * z - sp.height)
        im.paste(sp, (px, py), sp)
        d.text((cx + 20, cy + 4), title, font=font(19), fill=INK)
        d.text((cx + 20, cy + 96 * z + 36), sub, font=font(16), fill=DIM)
        d.rectangle([cx + 12, cy + 26, cx + cw - 14, cy + 96 * z + 30],
                    outline=(88, 92, 108))
    im.save(os.path.join(out, "contact_sheet_6x.png"))
    print("contact_sheet_6x.png", im.size)


# ---------------------------------------------------------------------------
def before_after(wip, out):
    """Old sprite next to the new design at the SAME on-screen scale.

    Both bosses render at scale 3 in game, so comparing at a single zoom is an
    honest like-for-like: Greyson's frame grew 64 -> 96, so he really is taller
    on screen; Computah's frame is unchanged, so only the art moved."""
    z = 5
    rows = [
        ("GREYSON",
         (PROJ + "/Assets/Characters/Greyson/greyson.png", 64, 1),
         (os.path.join(wip, "greyson_hero.png"), 96, 0),
         "old: 64x64 frame, scale 3  ->  189 px tall on screen",
         "new: 96x96 frame, scale 3  ->  285 px tall on screen"),
        ("COMPUTAH",
         (PROJ + "/Assets/Characters/Computah/computah.png", 64, 0),
         (os.path.join(wip, "computah_hero.png"), 64, 0),
         "old: 64x64 frame, scale 3  ->  174 px tall on screen",
         "new: 64x64 frame, scale 3  ->  168 px tall on screen"),
    ]
    panel_h = 96 * z + 120
    im = plate(96 * z * 2 + 200, panel_h * 2 + 60, checker=True)
    d = ImageDraw.Draw(im)
    d.text((22, 16), "OLD vs NEW - same on-screen scale", font=font(26), fill=INK)
    for r, (name, old, new, oc, nc) in enumerate(rows):
        top = 60 + r * panel_h
        for col, (src, fw, idx, cap) in enumerate(
                ((old[0], old[1], old[2], oc), (new[0], new[1], new[2], nc))):
            fr = frames(src, fw, fw)[idx]
            sp = nn(fr, z)
            x = 60 + col * (96 * z + 90)
            base = top + 40 + 96 * z
            im.paste(sp, (x + (96 * z - sp.width) // 2, base - sp.height), sp)
            d.line([x - 10, base + 1, x + 96 * z + 10, base + 1], fill=(120, 126, 142))
            d.text((x + 96, top + 8), ("BEFORE" if col == 0 else "AFTER"),
                   font=font(21), fill=INK if col else DIM)
            d.text((x, base + 12), cap, font=font(15), fill=DIM)
        d.text((22, top + 8), name, font=font(21), fill=INK)
    im.save(os.path.join(out, "before_after.png"))
    print("before_after.png", im.size)


# ---------------------------------------------------------------------------
def battery_closeup(wip, out):
    z = 12
    states = [("computah_batt_full.png", "FULL", "4 green cells - fresh off the charger"),
              ("computah_batt_half.png", "HALF", "2 amber cells - hurry up"),
              ("computah_batt_low.png", "LOW", "1 red cell - about to drop"),
              ("computah_batt_dead.png", "DEAD", "0 cells, grey - punish window open")]
    # crop the chest window + a little chassis around it
    box = (16, 34, 48, 56)
    cw = (box[2] - box[0]) * z + 48
    im = plate(cw * len(states), (box[3] - box[1]) * z + 400, checker=True)
    d = ImageDraw.Draw(im)
    d.text((22, 16), "COMPUTAH - battery indicator at 12x", font=font(26), fill=INK)
    d.text((22, 50), "charge reads three ways at once: cell COUNT, cell COLOUR, "
                     "and the antenna ball", font=font(17), fill=DIM)
    for i, (fn, label, sub) in enumerate(states):
        src = Image.open(os.path.join(wip, fn)).convert("RGBA")
        chest = nn(src.crop(box), z)
        x = i * cw + 24
        im.paste(chest, (x, 96), chest)
        d.text((x, 96 + chest.height + 14), label, font=font(24), fill=INK)
        d.text((x, 96 + chest.height + 46), sub, font=font(15), fill=DIM)
        whole = nn(src, 3)
        im.paste(whole, (x + (chest.width - whole.width) // 2,
                         96 + chest.height + 76), whole)
    im.save(os.path.join(out, "battery_states.png"))
    print("battery_states.png", im.size)


def hair_options(wip, out):
    """A/B for the user to pick: mid-length vs a full mane."""
    z = 7
    opts = [("greyson_hero.png", "A - MID LENGTH",
             "covers the ears, ends at the jaw"),
            ("greyson_hair_long.png", "B - LONG (mane)",
             "falls over the traps onto the pecs")]
    im = plate(96 * z * 2 + 200, 96 * z + 460, checker=True)
    d = ImageDraw.Draw(im)
    d.text((22, 16), "GREYSON - pick a hair length", font=font(26), fill=INK)
    d.text((22, 50), "both keep the blonde, the blue eyes, the moustache and "
                     "the three red forehead furrows", font=font(17), fill=DIM)
    for i, (fn, label, sub) in enumerate(opts):
        src = Image.open(os.path.join(wip, fn)).convert("RGBA")
        sp = nn(src, z)
        x = 60 + i * (96 * z + 80)
        im.paste(sp, (x, 96), sp)
        d.text((x, 96 + sp.height + 16), label, font=font(24), fill=INK)
        d.text((x, 96 + sp.height + 48), sub, font=font(16), fill=DIM)
        head = nn(src.crop((30, 0, 66, 40)), 4)
        im.paste(head, (x + sp.width - head.width, 96 + sp.height + 80), head)
    im.save(os.path.join(out, "hair_options.png"))
    print("hair_options.png", im.size)


def cast_lineup(wip, out):
    """Where the two land against the rest of the cast at real game scale."""
    z = 4
    items = [
        (PROJ + "/Assets/Characters/MainPlayer/player_4dir_sheet.png", 32, 32, 0,
         2, "PLAYER", "32x32 @2x"),
        (os.path.join(wip, "computah_hero.png"), 64, 64, 0, 3, "COMPUTAH (new)", "64x64 @3x"),
        (PROJ + "/Assets/Characters/Carter/carter_idle.png", 96, 96, 0, 3,
         "CARTER", "96x96 @3x - the bar"),
        (os.path.join(wip, "greyson_hero.png"), 96, 96, 0, 3, "GREYSON (new)", "96x96 @3x"),
    ]
    tallest = 96 * 3 * z // 3
    im = plate(300 * len(items), 96 * z + 240, checker=True)
    d = ImageDraw.Draw(im)
    d.text((22, 16), "CAST LINE-UP at true game scale", font=font(26), fill=INK)
    d.text((22, 50), "every sprite drawn at its own in-game scale, then zoomed "
                     "x%d together" % z, font=font(17), fill=DIM)
    base = 96 * z + 130
    d.line([0, base + 1, im.width, base + 1], fill=(120, 126, 142))
    for i, (src, fw, fh, idx, gs, name, cap) in enumerate(items):
        fr = frames(src, fw, fh)[idx]
        bb = fr.getbbox()
        fr = fr.crop((0, 0, fw, fh))
        sp = nn(fr, max(1, gs * z // 3))
        x = i * 300 + 150 - sp.width // 2
        im.paste(sp, (x, base - sp.height), sp)
        d.text((i * 300 + 24, base + 14), name, font=font(20), fill=INK)
        d.text((i * 300 + 24, base + 42), cap, font=font(15), fill=DIM)
        h = (bb[3] - bb[1]) * gs if bb else 0
        d.text((i * 300 + 24, base + 66), "%d px tall on screen" % h,
               font=font(15), fill=DIM)
    im.save(os.path.join(out, "cast_lineup.png"))
    print("cast_lineup.png", im.size)


if __name__ == "__main__":
    wip, out = sys.argv[1], sys.argv[2]
    contact_sheet(wip, out)
    before_after(wip, out)
    battery_closeup(wip, out)
    cast_lineup(wip, out)
    hair_options(wip, out)
