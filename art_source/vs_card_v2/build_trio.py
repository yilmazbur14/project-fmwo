"""Jordan's, Josh's and Matt's VS sets: halves, lettering and in-arena mock-ups, into a scratch folder.

    python build_trio.py <out_dir> <captures_dir> [key ...]

Card numbers and ranks come from Scripts/VsCardArtLayout.gd's CARDS (ship.table()), so the plates
always match the table. Epithets: the old art table's (vs_card/bosses.py) where it has one - THE
ADMIN, THE CARD SHARK - and a proposal for Matt, who is not in it: THE WALL OF SOUND.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout as LY                                                           # noqa: E402
import cards as CD                                                            # noqa: E402
import halves as HV                                                           # noqa: E402
import bands as BD                                                            # noqa: E402
import pxkit as P                                                             # noqa: E402
import pose_trio                                                              # noqa: E402
import ship                                                                   # noqa: E402

# top-left of each pose's canvas in the band: eyes on the shared line (row 58), the gesture clear of
# the VS and of the name plate
# Jordan is his approved v2 look (2026-09-24): pose_jordan_v2, built with the v2 rig, eyes on rows
# 58-59, the pop right of the seam, the raised arm clear of the VS, the box clear of the name plate.
# (pose_trio.jordan, the v1 taunt frame 2, was the card until then.)
PLACE = {"jordan": (326, 4), "josh": (365, 5), "matt": (330, -13)}


def _jordan_v2():
    import pose_jordan_v2                     # imported only when needed: it loads the v2 rig
    return pose_jordan_v2.pose()


POSE = {"jordan": _jordan_v2, "josh": pose_trio.josh, "matt": pose_trio.matt}
EPITHET = {"jordan": "THE ADMIN", "josh": "THE CARD SHARK", "matt": "THE WALL OF SOUND"}
PORTRAIT = {"jordan": ("Jordan/portrait.png", (18, 12, 46, 40)),
            "josh": ("Josh/portrait.png", (18, 16, 46, 44)),
            "matt": ("Matt/portrait.png", (18, 24, 46, 52))}


def set_for(key):
    t = ship.table()[key]
    b = BD.BANDS[key]
    pose = POSE[key]()
    half = HV.right_half(pose, PLACE[key], b["ramp"], b["accent"], b["mark"])
    portrait, crop = PORTRAIT[key]
    plates = CD.baked_plates(t["name"], EPITHET[key], t["number"], t["rank"], portrait, crop)
    files = {"band_right_%s.png" % key: half, "name_%s.png" % key: plates["name"],
             "epithet_%s.png" % key: plates["epithet"],
             "fight_%02d.png" % t["number"]: plates["fight"]}
    if t["rank"]:
        files["win_%s.png" % t["rank"].lstrip("@")] = plates["win"]
        files["badge_%s.png" % key] = plates["badge"]
    return files, plates, pose


def main(out, captures, keys):
    ship_refuse = os.path.normcase(os.path.abspath(os.path.join(LY.PROJ, "Assets")))
    if os.path.normcase(os.path.abspath(out)).startswith(ship_refuse):
        raise SystemExit("refusing to write into Assets")
    os.makedirs(out, exist_ok=True)
    from PIL import Image
    left = Image.open(LY.SHIPPED + "band_left.png").convert("RGBA")
    for k in keys:
        files, plates, pose = set_for(k)
        for name, im in files.items():
            im.save(os.path.join(out, name))
        P.save_zoom(pose, os.path.join(out, "pose_%s_3x.png" % k), 3)
        t = ship.table()[k]
        card = CD.card(CD.arena(k, captures), left, files["band_right_%s.png" % k], plates)
        card.convert("RGB").save(os.path.join(out, "card_%02d_%s_vs_burak.png" % (t["number"], k)))
        n = P.numbers(pose)
        print("%-7s pose %5.1f%% / %d colours   files: %s" % (k, n["black"], n["colours"],
                                                            ", ".join(sorted(files))))


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2:] or ["jordan", "josh", "matt"])
