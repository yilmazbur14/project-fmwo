"""CAPTAIN BURAK's VS set - boss 1, the tutorial fight, Burak vs Burak - into a scratch folder.

    python build_captain.py <out_dir> <arena_png> [face ...]

  face       shot (the wink and grin, frame 1's) or idle (the smirk, frame 0's); default both
  arena_png  a t = 0 still of an arena for the mock's backdrop (his own fight scene does not exist
             yet, so any fight's capture stands in: it only shows, dimmed, above and below the band)

His VsCardArtLayout.gd entry does not exist yet either (a coder adds CARDS["burak"] and renumbers
the table), so his number, name and rank come from Scripts/GameProgress.gd's first BOSSES row -
"BURAK", @member - and he is FIGHT 01. The files are named the way VsCardArtLayout loads a key
("burak"): band_right_burak, name_burak, epithet_burak, badge_burak, and win_member for his rank.
No fight plate: fight_01.png already reads FIGHT 01, byte for byte what this would bake.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import layout as LY                                                           # noqa: E402
import cards as CD                                                            # noqa: E402
import halves as HV                                                           # noqa: E402
import bands as BD                                                            # noqa: E402
import pxkit as P                                                             # noqa: E402
import pose_captain                                                           # noqa: E402

KEY = "burak"
NAME, NUMBER, RANK = "BURAK", 1, "@member"      # GameProgress.gd BOSSES[0]; FIGHT 01 once renumbered
EPITHET = "THE CAPTAIN"                         # proposed: with the plate's BURAK it names him
# the cocky smirk (frame 0's face) - the brief's, and it keeps Josh's the only wink on the cards;
# "shot" swaps in frame 1's wink-and-grin with the ting
FACE = "idle"
# top-left of the pose's 192 x 192 canvas in the band: his eyes (sprite row 33) on rows 58-59, the
# blade's tip clear of the VS, the gun's bell clear of the name plate
PLACE = (355, -8)
# the badge: his smirk off the idle frame of his sheet (he has no dialogue portrait), eyes to chin
PORTRAIT = ("BurakBoss/burak_boss.png", (34, 20, 62, 48))


def entry():
    """His row: CARDS["burak"] once a coder adds it to VsCardArtLayout.gd, GameProgress's until then."""
    import ship
    t = ship.table().get(KEY)
    if t:
        return t["name"], t["number"], t["rank"]
    return NAME, NUMBER, RANK


def set_for(face=FACE, band=None, place=PLACE, epithet=EPITHET):
    b = band or BD.BANDS[KEY]
    pose = pose_captain.pose(face=face)
    half = HV.right_half(pose, place, b["ramp"], b["accent"], b["mark"])
    name, number, rank = entry()
    portrait, crop = PORTRAIT
    plates = CD.baked_plates(name, epithet, number, rank, portrait, crop)
    files = {"band_right_%s.png" % KEY: half, "name_%s.png" % KEY: plates["name"],
             "epithet_%s.png" % KEY: plates["epithet"],
             "win_%s.png" % rank.lstrip("@"): plates["win"], "badge_%s.png" % KEY: plates["badge"]}
    return files, plates, pose


def main(out, arena_png, faces):
    refuse = os.path.normcase(os.path.abspath(os.path.join(LY.PROJ, "Assets")))
    if os.path.normcase(os.path.abspath(out)).startswith(refuse):
        raise SystemExit("refusing to write into Assets")
    os.makedirs(out, exist_ok=True)
    from PIL import Image
    left = Image.open(LY.SHIPPED + "band_left.png").convert("RGBA")
    arena = Image.open(arena_png).convert("RGBA")
    for face in faces:
        files, plates, pose = set_for(face)
        sub = os.path.join(out, face)
        os.makedirs(sub, exist_ok=True)
        for name, im in files.items():
            im.save(os.path.join(sub, name))
        P.save_zoom(pose, os.path.join(sub, "pose_burak_3x.png"), 3)
        card = CD.card(arena, left, files["band_right_%s.png" % KEY], plates)
        card.convert("RGB").save(os.path.join(sub, "card_%02d_captain_burak_vs_burak.png" % entry()[1]))
        n = P.numbers(pose)
        print("%-5s pose %5.1f%% / %d colours   files: %s" % (face, n["black"], n["colours"],
                                                          ", ".join(sorted(files))))


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[0], args[1], args[2:] or ["idle", "shot"])
