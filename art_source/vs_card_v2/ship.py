"""Ships approved VS-card sets into Assets/UI/VsCard - the one script in this folder allowed to.

    python ship.py <backup_dir> <key> [<key> ...] --ship

  key         burak (band_left.png), eric (band_right_eric.png), carter, jordan, matt, josh
              (the last three are build_trio.set_for's sets), captain (CAPTAIN BURAK, boss 1:
              band_right_burak, name_burak, epithet_burak, badge_burak, win_member - files named
              for the "burak" key VsCardArtLayout will load him by; no fight plate, because
              fight_01.png already reads FIGHT 01), fight_NN (one FIGHT NN plate on its own, e.g.
              fight_09 for the ninth fight; plates are per number, so a renumber only ever needs
              the numbers that do not exist yet)
  backup_dir  every file this run would overwrite is copied here first (PNG, .aseprite, .import)
  --ship      required; without it the script only builds into <backup_dir>/dry_run and reports

Every PNG is written whole (temp name, then os.replace), because the user's editor watches the
folder. Its .aseprite is built from the finished PNG, round-tripped through the Aseprite CLI and
compared with imgdiff.pixel_diff; a PNG whose round trip differs is not shipped.

The card numbers and ranks each plate depends on (fight_NN, win_<rank>) are read out of
Scripts/VsCardArtLayout.gd at run time, so a plate always matches the table at the moment it
ships. The fight_NN plates are per number, not per boss (fight_01..08 all read their own number),
so a renumbering only changes which plate a card loads; a number with no plate yet gets one
with the fight_NN key.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, ".."))
import layout as LY                                                           # noqa: E402
import cards as CD                                                            # noqa: E402
import halves as HV                                                           # noqa: E402
import bands as BD                                                            # noqa: E402
from imgdiff import pixel_diff                                                # noqa: E402

ASE = r"C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe"
DEST = LY.SHIPPED                                     # Assets/UI/VsCard/
TABLE = LY.PROJ + "/Scripts/VsCardArtLayout.gd"
# the epithet and badge crop each boss ships with; the rest comes from the game's own table
EPITHET = {"eric": "THE WHITE KNIGHT", "carter": "THE DEMON"}
BADGE_CROP = {"carter": (18, 14, 46, 42)}


def table():
    """{key: {number, name, epithet, rank}} parsed from VsCardArtLayout.gd's CARDS."""
    src = open(TABLE, encoding="utf-8").read()
    block = src[src.index("const CARDS := {"):]
    block = block[:block.index("\n}\n")]
    out = {}
    for m in re.finditer(r'\t"(\w+)": \{(.*?)\n\t\}', block, re.S):
        body = m.group(2)
        grab = lambda k: re.search(r'"%s": ([^,\n]+),' % k, body).group(1).strip().strip('"')
        out[m.group(1)] = {"number": int(grab("number")), "name": grab("name"),
                           "epithet": grab("epithet"), "rank": grab("rank")}
    return out


def carter_like(key, pose_builder, place, portrait):
    """A boss's full set, named the way VsCardArtLayout loads it."""
    t = table()[key]
    b = BD.BANDS[key]
    pose = pose_builder()
    half = HV.right_half(pose, place, b["ramp"], b["accent"], b["mark"])
    plates = CD.baked_plates(t["name"], EPITHET[key], t["number"], t["rank"], portrait,
                             BADGE_CROP.get(key, (18, 6, 46, 34)))
    files = {"band_right_%s.png" % key: half, "name_%s.png" % key: plates["name"],
             "epithet_%s.png" % key: plates["epithet"],
             "fight_%02d.png" % t["number"]: plates["fight"]}
    if t["rank"]:
        files["win_%s.png" % t["rank"].lstrip("@")] = plates["win"]
        files["badge_%s.png" % key] = plates["badge"]
    return files


def sets(keys):
    if "captain" in keys and "jordan" in keys:
        # Captain Burak's rig and Jordan's v2 rig both bring modules named kit and head
        raise SystemExit("ship captain and jordan in separate runs: their rigs share module names")
    import build_mocks as BM
    ps = None
    files = {}
    for k in keys:
        if k in ("burak", "eric"):
            ps = ps or BM.poses()
            hs = BM.halves_for(ps)
            files.update({"band_left.png": hs["band_left"]} if k == "burak"
                         else {"band_right_eric.png": hs["band_right_eric"]})
        elif k == "carter":
            import pose_carter
            files.update(carter_like("carter", lambda: _crop(pose_carter.build("victory", False, "left")),
                                     BM.PLACE["carter"], "Carter/portrait.png"))
        elif k in ("jordan", "matt", "josh"):
            import build_trio
            files.update(build_trio.set_for(k)[0])
        elif k == "captain":
            import build_captain
            files.update(build_captain.set_for()[0])
        elif re.fullmatch(r"fight_\d\d", k):
            files[k + ".png"] = CD.fight_plate(int(k[6:]))
        else:
            raise SystemExit("no set defined for %r yet" % k)
    return files


def _crop(im):
    return im.crop(im.getbbox())


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
    os.makedirs(backup, exist_ok=True)
    work = tempfile.mkdtemp(prefix="vs_ship_")
    files = sets(keys)
    report = []
    staged = []
    for name, img in sorted(files.items()):
        png = os.path.join(work, name)
        img.save(png, optimize=False)
        ase, why = ase_roundtrip(png, work)
        if why is not None:
            raise SystemExit("%s: aseprite round trip differs: %s" % (name, why))
        staged.append((name, png, ase))
        report.append(name)
    if not ship:
        dry = os.path.join(backup, "dry_run")
        os.makedirs(dry, exist_ok=True)
        for name, png, ase in staged:
            shutil.copyfile(png, os.path.join(dry, name))
            shutil.copyfile(ase, os.path.join(dry, os.path.basename(ase)))
        print("dry run - nothing shipped; built into", dry)
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
