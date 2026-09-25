"""Previews the Computah, Mason, Danny and Liam & Bixby VS sets into a scratch folder: each set's
files, the whole card at its hold over the fight's arena, and a 3x view of each half.

    python mock_four.py <out_dir> <captures_dir> [key ...]

out_dir       REQUIRED, and refused if it is inside the project's Assets. This script never ships;
              ship_four.py does.
captures_dir  shoot_arena.gd's stills: <key>_arena_t0.png, the live arena before the card shows.
              A fight with no still of its own is drawn over the first still the folder has.

Burak's half is the shipped Assets/UI/VsCard/band_left.png, read, never written.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as LY                                                           # noqa: E402
import compose as CO                                                          # noqa: E402
import four as F                                                              # noqa: E402
import pxkit as P                                                             # noqa: E402


def refuse_assets(path):
    a = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(os.path.abspath(os.path.join(LY.PROJ, "Assets")))
    if a == b or a.startswith(b + os.sep):
        raise SystemExit("refusing to write into Assets: %s" % path)


def arena(captures, key):
    p = os.path.join(captures, "%s_arena_t0.png" % key)
    if not os.path.exists(p):
        stills = sorted(f for f in os.listdir(captures) if f.endswith("_arena_t0.png"))
        if not stills:
            raise SystemExit("no arena still in %s" % captures)
        p = os.path.join(captures, stills[0])
    return Image.open(p).convert("RGBA")


def main(out, captures, keys):
    refuse_assets(out)
    os.makedirs(out, exist_ok=True)
    left = Image.open(LY.SHIPPED + "band_left.png").convert("RGBA")
    for key in keys:
        files = F.set_files(key)
        d = os.path.join(out, key)
        os.makedirs(d, exist_ok=True)
        for name, im in files.items():
            im.save(os.path.join(d, name), optimize=False)
        right = files["band_right_%s.png" % key]
        card = CO.frame(arena(captures, key), left, right, F.plates_for_card(key, files),
                        half_at=LY.HALF_AT)
        card.convert("RGB").save(os.path.join(out, "card_%s.png" % key))
        band = card.crop((0, LY.BAND_AT[1] - 30, 1920, LY.BAND_AT[1] + LY.BAND_H * 3 + 30))
        band.convert("RGB").save(os.path.join(out, "band_%s.png" % key))
        n = P.numbers(files["pose_%s.png" % key],
                      (0x0C, 0x11, 0x1A) if key == "computah" else (0, 0, 0))
        print("%-9s pose %s  keyline %.1f%%  colours %d  -> %s" % (
            key, files["pose_%s.png" % key].size, n["black"], n["colours"], sorted(files)))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        raise SystemExit(__doc__)
    main(args[0], args[1], args[2:] or F.KEYS)
