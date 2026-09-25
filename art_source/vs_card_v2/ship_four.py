"""Ships the Computah, Mason, Danny and Liam & Bixby VS-card sets into Assets/UI/VsCard.

    python ship_four.py <backup_dir> <key> [<key> ...] --ship

  key         computah, mason, danny, liam (four.py builds each set; nothing else is shippable here)
  backup_dir  every file this run would overwrite is copied here first (PNG, .aseprite, .import)
  --ship      required; without it the script only builds into <backup_dir>/dry_run and reports

The same guarantees as ship.py (which ships Burak, Eric and Carter, and is left alone): every PNG is
written whole (a temp name, then os.replace), because the user's editor watches the folder; its
.aseprite is built from the finished PNG, round-tripped through the Aseprite CLI and compared with
imgdiff.pixel_diff, and a set with any round trip that differs ships nothing.

It also refuses to write any file that is not one of these four sets' own: band_right_<key>,
pose_<key>, name_<key>, epithet_<key>, badge_<key>, and the fight_NN and win_<rank> plates of these
four fights' numbers and ranks - never another artist's.
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, ".."))
import layout as LY                                                           # noqa: E402
import four as F                                                              # noqa: E402
from imgdiff import pixel_diff                                                # noqa: E402

ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
DEST = LY.SHIPPED                                     # Assets/UI/VsCard/


def allowed_names(key):
    row = F.card_row(key)
    names = {"band_right_%s.png" % key, "pose_%s.png" % key, "name_%s.png" % key,
             "epithet_%s.png" % key, "badge_%s.png" % key}
    if row["number"] > 0:
        names.add("fight_%02d.png" % row["number"])
    if row["rank"]:
        names.add("win_%s.png" % row["rank"].lstrip("@"))
    return names


def no_alpha_between(im):
    """STYLE.md: alpha is 0 or 255, nothing between."""
    return all(a in (0, 255) for a in im.getchannel("A").getdata())


def ase_roundtrip(png, work):
    ase = os.path.join(work, os.path.splitext(os.path.basename(png))[0] + ".aseprite")
    subprocess.run([ASE, "-b", png, "--save-as", ase], check=True, capture_output=True)
    back = os.path.join(work, "back_" + os.path.basename(png))
    subprocess.run([ASE, "-b", ase, "--save-as", back], check=True, capture_output=True)
    why = pixel_diff(Image.open(png).convert("RGBA"), Image.open(back).convert("RGBA"))
    return ase, why


def put(src, dst):
    """Copy whole: a temp name the editor ignores, then one atomic rename."""
    tmp = dst + ".shiptmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def main(backup, keys, ship):
    for k in keys:
        if k not in F.KEYS:
            raise SystemExit("not one of this script's sets: %r (shippable: %s)" % (k, F.KEYS))
    os.makedirs(backup, exist_ok=True)
    work = tempfile.mkdtemp(prefix="vs_ship4_")
    staged = []
    for k in keys:
        files = F.set_files(k)
        ok = allowed_names(k)
        for name, img in sorted(files.items()):
            if name not in ok:
                raise SystemExit("%s: %s is not this set's own file" % (k, name))
            if not no_alpha_between(img):
                raise SystemExit("%s: semi-alpha found" % name)
            png = os.path.join(work, name)
            img.save(png, optimize=False)
            ase, why = ase_roundtrip(png, work)
            if why is not None:
                raise SystemExit("%s: aseprite round trip differs: %s" % (name, why))
            staged.append((name, png, ase))
    if not ship:
        dry = os.path.join(backup, "dry_run")
        os.makedirs(dry, exist_ok=True)
        for name, png, ase in staged:
            shutil.copyfile(png, os.path.join(dry, name))
            shutil.copyfile(ase, os.path.join(dry, os.path.basename(ase)))
            print("%-26s built, .aseprite round trip OK" % name)
        print("dry run - nothing shipped; built into", dry)
        shutil.rmtree(work, ignore_errors=True)
        return
    for name, png, ase in staged:
        base = os.path.splitext(name)[0]
        for old in (name, base + ".aseprite", name + ".import"):
            p = os.path.join(DEST, old)
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(backup, old))
        put(png, os.path.join(DEST, name))
        put(ase, os.path.join(DEST, base + ".aseprite"))
        # prove what landed is what was checked
        why = pixel_diff(Image.open(os.path.join(DEST, name)).convert("RGBA"),
                         Image.open(png).convert("RGBA"))
        print("%-26s shipped, .aseprite round trip OK%s" % (name, "" if why is None else " - " + why))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        raise SystemExit(__doc__)
    main(args[0], args[1:], "--ship" in sys.argv)
