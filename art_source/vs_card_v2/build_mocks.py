"""Builds the VS-card pose pass for approval: the poses, the new band halves, the lettering Carter's
card needs, the two full in-game mock-ups and the old/new comparison - into a scratch folder.

    python build_mocks.py <out_dir> <captures_dir> [--aseprite]

out_dir       where everything goes. REQUIRED, and refused if it is inside the project's Assets:
              this is an approval pass; nothing here ships until the user says so.
captures_dir  shoot_arena.gd's stills: <key>_arena_t0.png (the live arena before the card shows)
              and eric_hold.png (the game's own render of the shipped Eric card).
--aseprite    also save a .aseprite beside every PNG (Aseprite CLI), and prove each round trip.

Deterministic: no randomness, no timestamps.
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, ".."))
import layout as LY                                                           # noqa: E402
import compose as CO                                                          # noqa: E402
import cards as CD                                                            # noqa: E402
import halves as HV                                                           # noqa: E402
import bands as BD                                                            # noqa: E402
import pxkit as P                                                             # noqa: E402
import pose_burak                                                             # noqa: E402
import pose_eric                                                              # noqa: E402
import pose_carter                                                            # noqa: E402

ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"

# where each pose sits in its half (band texels, top-left of the pose's own canvas): every eye on
# band row 56-60, the shared eye line (STYLE.md)
PLACE = {"burak": (0, 0), "eric": (296, -2), "carter": (352, -12)}


def refuse_assets(path):
    a = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(os.path.abspath(os.path.join(LY.PROJ, "Assets")))
    if a == b or a.startswith(b + os.sep):
        raise SystemExit("refusing to write into Assets: %s" % path)


def poses():
    burak = pose_burak.build()
    eric = pose_eric.build()
    eric = eric.crop(eric.getbbox())
    carter = pose_carter.build("victory", False, "left")
    carter = carter.crop(carter.getbbox())
    return {"burak": burak, "eric": eric, "carter": carter}


def halves_for(ps):
    L = HV.left_half(ps["burak"], PLACE["burak"])
    e, c = BD.BANDS["eric"], BD.BANDS["carter"]
    return {
        "band_left": L,
        "band_right_eric": HV.right_half(ps["eric"], PLACE["eric"], e["ramp"], e["accent"], e["mark"]),
        "band_right_carter": HV.right_half(ps["carter"], PLACE["carter"], c["ramp"], c["accent"],
                                           c["mark"]),
    }


def carter_plates():
    # FIGHT 05 and @moderator are the game's own (VsCardArtLayout.CARDS), THE DEMON is the canon
    # epithet (vs_card/bosses.py, approved 2026-09-20); the badge is build_assets.badge() on his
    # dialogue portrait, cropped to his eyes and beard.
    return CD.baked_plates("CARTER", "THE DEMON", 5, "@moderator", "Carter/portrait.png",
                           (18, 14, 46, 42))


def label(img, text, xy, size=40):
    from textart import bake
    plate = bake(text, 33, fill="#F2C457")
    img.alpha_composite(plate, xy)


def comparison(old, new):
    """The two Eric cards side by side at half size, and the two bands stacked at full size."""
    half = (960, 540)
    a, b = old.resize(half, Image.LANCZOS), new.resize(half, Image.LANCZOS)
    side = Image.new("RGBA", (1920 + 24, 540 + 60), (10, 9, 16, 255))
    side.alpha_composite(a, (0, 60))
    side.alpha_composite(b, (984, 60))
    label(side, "SHIPPED", (12, 12))
    label(side, "PROPOSED", (996, 12))
    band = (0, 270, 1920, 858)
    stack = Image.new("RGBA", (1920, (band[3] - band[1]) * 2 + 120), (10, 9, 16, 255))
    stack.alpha_composite(old.crop(band), (0, 60))
    stack.alpha_composite(new.crop(band), (0, 60 + band[3] - band[1] + 60))
    label(stack, "SHIPPED", (24, 12))
    label(stack, "PROPOSED", (24, band[3] - band[1] + 72))
    return side, stack


def contact(ps, out):
    """The three poses side by side at 3x, the size the card draws them, on the night backdrop."""
    pad = 12
    w = sum(p.width for p in ps.values()) + pad * (len(ps) + 1)
    h = max(p.height for p in ps.values()) + pad * 2
    sheet = Image.new("RGBA", (w, h), (34, 32, 52, 255))
    x = pad
    for p in ps.values():
        sheet.alpha_composite(p, (x, pad))
        x += p.width + pad
    sheet.resize((w * 3, h * 3), Image.NEAREST).save(out)


def ase(png):
    """Save a .aseprite beside the PNG and prove the round trip is lossless (imgdiff)."""
    import tempfile
    from imgdiff import pixel_diff
    dst = os.path.splitext(png)[0] + ".aseprite"
    subprocess.run([ASE, "-b", png, "--save-as", dst], check=True, capture_output=True)
    with tempfile.TemporaryDirectory() as td:
        back = os.path.join(td, "back.png")
        subprocess.run([ASE, "-b", dst, "--save-as", back], check=True, capture_output=True)
        why = pixel_diff(Image.open(png).convert("RGBA"), Image.open(back).convert("RGBA"))
    return dst, why


def main(out, captures, with_ase):
    refuse_assets(out)
    os.makedirs(out, exist_ok=True)
    made = []

    def save(img, name):
        p = os.path.join(out, name)
        img.save(p, optimize=False)
        made.append(p)
        return p

    ps = poses()
    for k, im in ps.items():
        save(im, "pose_%s.png" % k)
    hs = halves_for(ps)
    for k, im in hs.items():
        save(im, "%s.png" % k)
    plates = carter_plates()
    for k in ("name", "epithet", "fight", "win", "badge"):
        save(plates[k], {"name": "name_carter.png", "epithet": "epithet_carter.png",
                         "fight": "fight_05.png", "win": "win_moderator.png",
                         "badge": "badge_carter.png"}[k])

    arena = lambda key: CD.arena(key, captures)
    eric_card = CD.card(arena("eric"), hs["band_left"], hs["band_right_eric"], CO.shipped_eric_plates())
    carter_card = CD.card(arena("carter"), hs["band_left"], hs["band_right_carter"], plates)
    save(eric_card.convert("RGB"), "card_01_eric_vs_burak.png")
    save(carter_card.convert("RGB"), "card_05_carter_vs_burak.png")

    old = Image.open(os.path.join(captures, "eric_hold.png")).convert("RGBA")
    side, stack = comparison(old, eric_card)
    save(side.convert("RGB"), "compare_eric_old_new.png")
    save(stack.convert("RGB"), "compare_eric_bands_fullres.png")
    contact(ps, os.path.join(out, "poses_3x.png"))

    print("%-10s %8s %8s" % ("pose", "black%", "colours"))
    for k, im in ps.items():
        n = P.numbers(im)
        print("%-10s %7.1f%% %8d" % (k, n["black"], n["colours"]))
    if with_ase:
        for p in made:
            if os.path.basename(p).startswith(("card_", "compare_")):
                continue
            dst, why = ase(p)
            print("%-34s -> %s" % (os.path.basename(p), "round trip OK" if why is None else why))
    return made


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        raise SystemExit(__doc__)
    main(args[0], args[1], "--aseprite" in sys.argv)
