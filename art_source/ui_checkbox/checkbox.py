"""The INVINCIBLE toggle's checkbox icons, for the main menu's boss-select panel (MainMenuScript.gd).

Godot's default CheckBox icons are what the toggle shows today, because ui_theme.tres has none. The
unchecked one is a half-transparent dark grey that vanishes on the panel, and the checked one is a
smooth, anti-aliased box. These replace both.

THE GRID. Everything is drawn on the toggle's own text grid. Its label is Pixelify Sans at 22 px
(BOSS_SELECT_FONT_SIZE), which is 2 screen px per font pixel. Caps are 7 font pixels tall (14 px),
and strokes are 1 font pixel wide. So each grid below is authored at 1 texel = 1 font pixel and
shipped at 2x (NEAREST, the project's canvas filter). The box is 9 font pixels, one proud of the
caps above and below, so it reads as a control rather than one more letter, and it centres on the
28 px row the same way the caps do (y 843-860 around caps at 845-858).

THE COLOURS are the panel's own, from MainMenuScript's styles:
    L  #E0E6ED  the toggle's and the fights' text colour (font_color 0.88, 0.9, 0.93)
    D  #242429  a fight button's fill (0.14, 0.14, 0.17)
    S  #17171C  a pressed button's fill (0.09, 0.09, 0.11): the well's shaded top and left
    G  #6B707A  disabled text (0.42, 0.44, 0.48), for the disabled pair
    g  #17171A  a disabled button's fill (0.09, 0.09, 0.10)

Unchecked is an outlined well in the text colour. Checked is the same box lit, with a dark tick
two font pixels thick. A light tick inside the dark well was tried and rejected: with no room for
a margin, it runs into the outline and turns to mush. The cap-height 7-pixel box was tried too, and
read as a glyph rather than a control.

    python checkbox.py <out_dir>                   build every icon into out_dir (refuses Assets/)
    python checkbox.py <out_dir> --ship <backup>   also ship them into Assets/UI, each with its
                                                   .aseprite, backing up anything replaced first
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, "..", ".."))
ASSETS_UI = os.path.join(PROJ, "Assets", "UI")
ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
SCALE = 2                               # screen px per font pixel at 22 px

PAL = {
    "L": (0xE0, 0xE6, 0xED, 255),
    "D": (0x24, 0x24, 0x29, 255),
    "S": (0x17, 0x17, 0x1C, 255),
    "G": (0x6B, 0x70, 0x7A, 255),
    "g": (0x17, 0x17, 0x1A, 255),
    ".": (0, 0, 0, 0),
}

OFF = [
    "LLLLLLLLL",
    "LSSSSSSSL",
    "LSDDDDDDL",
    "LSDDDDDDL",
    "LSDDDDDDL",
    "LSDDDDDDL",
    "LSDDDDDDL",
    "LSDDDDDDL",
    "LLLLLLLLL",
]
ON = [
    "LLLLLLLLL",
    "LLLLLLLLL",
    "LLLLLLLDL",
    "LLLLLLDDL",
    "LDLLLDDLL",
    "LDDLDDLLL",
    "LLDDDLLLL",
    "LLLDLLLLL",
    "LLLLLLLLL",
]
DISABLED = {"L": "G", "D": "g", "S": "g"}

# file -> (grid, remap, the CheckBox theme icon it is for)
ICONS = {
    "checkbox_off_2x.png": (OFF, None, "unchecked"),
    "checkbox_on_2x.png": (ON, None, "checked"),
    "checkbox_off_disabled_2x.png": (OFF, DISABLED, "unchecked_disabled"),
    "checkbox_on_disabled_2x.png": (ON, DISABLED, "checked_disabled"),
}


def image(rows, remap=None, scale=SCALE):
    h, w = len(rows), len(rows[0])
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for y, row in enumerate(rows):
        assert len(row) == w, (row, w)
        for x, k in enumerate(row):
            im.putpixel((x, y), PAL[(remap or {}).get(k, k)])
    return im.resize((w * scale, h * scale), Image.NEAREST)


def build(out):
    os.makedirs(out, exist_ok=True)
    made = {}
    for name, (rows, remap, _slot) in ICONS.items():
        im = image(rows, remap)
        im.save(os.path.join(out, name), optimize=False)
        made[name] = im
    return made


def ase_roundtrip(png, work):
    sys.path.insert(0, os.path.join(HERE, ".."))
    from imgdiff import pixel_diff
    ase = os.path.join(work, os.path.splitext(os.path.basename(png))[0] + ".aseprite")
    subprocess.run([ASE, "-b", png, "--save-as", ase], check=True, capture_output=True)
    back = os.path.join(work, "back_" + os.path.basename(png))
    subprocess.run([ASE, "-b", ase, "--save-as", back], check=True, capture_output=True)
    return ase, pixel_diff(Image.open(png).convert("RGBA"), Image.open(back).convert("RGBA"))


def ship(built_dir, backup):
    """Copy the built icons into Assets/UI whole (temp name, then one rename), each with a .aseprite
    whose round trip is pixel-identical, after backing up anything they replace."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    from imgdiff import pixel_diff
    os.makedirs(backup, exist_ok=True)
    work = tempfile.mkdtemp(prefix="checkbox_ship_")
    staged = []
    for name in ICONS:
        png = os.path.join(built_dir, name)
        ase, why = ase_roundtrip(png, work)
        if why is not None:
            raise SystemExit("%s: aseprite round trip differs: %s" % (name, why))
        staged.append((name, png, ase))
    for name, png, ase in staged:
        base = os.path.splitext(name)[0]
        for old in (name, base + ".aseprite", name + ".import"):
            p = os.path.join(ASSETS_UI, old)
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(backup, old))
        for src, dst in ((png, os.path.join(ASSETS_UI, name)), (ase, os.path.join(ASSETS_UI, base + ".aseprite"))):
            shutil.copyfile(src, dst + ".shiptmp")
            os.replace(dst + ".shiptmp", dst)
        why = pixel_diff(Image.open(os.path.join(ASSETS_UI, name)).convert("RGBA"), Image.open(png).convert("RGBA"))
        print("%-30s shipped for CheckBox %-18s .aseprite round trip OK%s"
              % (name, ICONS[name][2], "" if why is None else " - " + why))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0]
    if os.path.normcase(os.path.abspath(out)).startswith(os.path.normcase(os.path.abspath(ASSETS_UI))):
        raise SystemExit("refusing to build previews into Assets/; use --ship")
    for name, im in build(out).items():
        print("%-30s %s  for CheckBox %s" % (name, im.size, ICONS[name][2]))
    if "--ship" in sys.argv:
        if len(args) < 2:
            raise SystemExit("--ship needs a backup folder")
        ship(out, args[1])
