"""Each fight's band identity: the ramp of the boss's half, the two hairlines on the seam, the ghosted
emblem behind the pose. Eric's is the shipped set, unchanged. The rest are proposals.

A band has to do one job the pose cannot: give the figure a ground to stand out from. So each ramp
is picked AGAINST its boss's own colours - never the colour of their biggest mass, so the figure
does not sink into it.

    ramp     five steps, darkest first (the order card.banded() reads)
    accent   the two hairlines along the seam, dark then light
    mark     (emblem, colour, alpha) for emblems.emblem()
    against  the boss's biggest colour masses, which the ramp was chosen to stand clear of

    python bands.py <out.png>       a swatch sheet of every band (scratch only; refuses Assets)
"""
BANDS = {
    # SHIPPED, unchanged: steel to white, the red cross, gold on the seam.
    "eric": dict(ramp=["#525A74", "#7A86A0", "#A3B1C2", "#CDD7E2", "#EAF0F6"],
                 accent=("#C48A2C", "#F2C457"), mark=("cross", "#B0242A", 52),
                 against="white plate, orange beard"),
    # His gi is navy and his aura is red, so the band is neither: a bruise purple into black, the
    # Satsui no Hado dark, which leaves the red spikes and the white 天 the brightest things on the
    # card. The seam in his aura's red; the demon mark ghosted behind him. (The game's stand-in is
    # red - see "carter_red" - and his spikes sink into it.)
    "carter": dict(ramp=["#0C0612", "#1C0A22", "#34103A", "#561A52", "#7E2A66"],
                   accent=("#8A1F38", "#FF4A3C"), mark=("demon", "#FF4A3C", 40),
                   against="navy gi, red aura"),
    "carter_red": dict(ramp=["#140A0A", "#3C0C20", "#6E1F22", "#AC3232", "#D95763"],
                       accent=("#8A1F38", "#E2402F"), mark=("demon", "#E2402F", 52),
                       against="(the stand-in, for comparison)"),
    # A purple-and-white robot on the game's own cyan ramp for him, with his battery's green on the
    # seam and the bolt.
    "computah": dict(ramp=["#0B1620", "#12304A", "#1F5C8A", "#35A6D8", "#A9E4FF"],
                     accent=("#1F9A38", "#4FE066"), mark=("bolt", "#4FE066", 48),
                     against="purple and white armour"),
    # A tan nugget in a yellow hood: not gold (the game's stand-in), the bucket's red, with the
    # bucket's white stripe on the seam.
    "mason": dict(ramp=["#240A0C", "#4E1216", "#7E1C20", "#B42A2A", "#E0483C"],
                  accent=("#EAF0F6", "#FFFFFF"), mark=("star", "#FFFFFF", 40),
                  against="tan nugget, yellow hood"),
    # A cream coat, a maroon hat, a navy vest: card-table felt, with gold on the seam and the spade.
    "josh": dict(ramp=["#081A10", "#0F3320", "#1A5234", "#28744A", "#3E9A64"],
                 accent=("#C48A2C", "#F2C457"), mark=("spade", "#0B0A12", 60),
                 against="cream coat, maroon hat, navy vest"),
    # Lavender, gold and navy hair: a charcoal amp stack, gold on the seam. No ghosted emblem: his
    # pose carries his own sound rings (matt.png frame 1's), and a second set would fight them.
    "matt": dict(ramp=["#0C0C12", "#18182A", "#262642", "#36365E", "#4C4C82"],
                 accent=("#C48A2C", "#F2C457"), mark=("rings", "#CBDBFC", 0),
                 against="lavender shirt, gold collar, navy hair"),
    # Tan, a pale blue cap and mawashi, a red ruff: a night indigo for the sleeping giant, the moon.
    "danny": dict(ramp=["#0A0C1E", "#141A3A", "#1F2A5C", "#2E3E82", "#4A5CA8"],
                  accent=("#C48A2C", "#F2C457"), mark=("moon", "#F2C457", 44),
                  against="tan skin, pale blue cap and mawashi"),
    # A red beast and a brown jacket: the game's own ember ramp, the throne's crown, bone white on
    # the seam.
    "liam": dict(ramp=["#1A1016", "#4A1C08", "#7A3010", "#DF6C22", "#FFB45E"],
                 accent=("#9A8F80", "#EDE4D6"), mark=("crown", "#F2C457", 50),
                 against="red beast, brown jacket, blue jeans"),
    # Red and pink: the game's own admin blue for the final fight, the shield, gold on the seam.
    "jordan": dict(ramp=["#0B0A12", "#222034", "#3F3F74", "#5B6EE1", "#CBDBFC"],
                   accent=("#C48A2C", "#F2C457"), mark=("shield", "#FFFFFF", 40),
                   against="red tee, pink Peach print, blue jeans"),
    # CAPTAIN BURAK (boss 1; the key VsCardArtLayout will load him by). A crimson greatcoat and a
    # black tricorn: the open sea, a teal that is the coat's complement and sits between Josh's felt
    # green and Computah's blue. The seam in his own gold (burak_boss/kit.py G, O - the pair his boss
    # bar uses). His Jolly Roger (emblems.GRIDS, the HUD's mark) is named but ghosted at alpha 0: the
    # emblem box sits right behind his head and raised gun, and the fragment left showing was noise.
    "burak": dict(ramp=["#06181A", "#0C3033", "#144C50", "#1E6A6E", "#2E8C8E"],
                  accent=("#B07D22", "#F5D94E"), mark=("jolly_roger", "#F5D94E", 0),
                  against="crimson greatcoat, black tricorn, gold trim"),
}


def swatches(out):
    """Every boss's half of the band, empty, side by side - the colour decisions on one sheet."""
    import os
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import halves as HV
    import layout as LY
    from PIL import Image
    sys.path.insert(1, os.path.join(here, "..", "vs_card"))
    import textart
    keys = [k for k in BANDS if k != "carter_red"]
    rows = []
    for k in keys:
        b = BANDS[k]
        empty = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        half = HV.right_half(empty, (0, 0), b["ramp"], b["accent"], b["mark"])
        crop = half.crop((LY.SPLIT_BOTTOM - 8, 0, LY.BAND_W, LY.BAND_H))
        rows.append((k, crop))
    w = rows[0][1].width * 2
    h = sum(r.height * 2 + 44 for _, r in rows)
    sheet = Image.new("RGBA", (w + 20, h + 20), (10, 9, 16, 255))
    y = 10
    for k, r in rows:
        sheet.alpha_composite(textart.bake(k.upper(), 33, fill="#F2C457"), (10, y))
        sheet.alpha_composite(r.resize((r.width * 2, r.height * 2), Image.NEAREST), (10, y + 40))
        y += r.height * 2 + 44
    sheet.convert("RGB").save(out)


if __name__ == "__main__":
    import os
    import sys
    out = sys.argv[1]
    proj_assets = os.path.normcase(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..",
                                                                "Assets")))
    if os.path.normcase(os.path.abspath(out)).startswith(proj_assets):
        raise SystemExit("refusing to write into Assets")
    swatches(out)
