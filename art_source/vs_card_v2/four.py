"""The VS-card sets for Computah, Mason, Danny and Liam & Bixby: where each pose stands in its half,
the epithet and badge each ships with, and every file of a set, named the way VsCardArtLayout loads
them. Read-only: this module builds images in memory and writes nothing. mock_four.py previews the
sets into a scratch folder; ship_four.py is the only script that puts them in Assets.

The card numbers, names and ranks come from the game's own tables at run time - the fight number and
the rank from Scripts/VsCardArtLayout.gd's CARDS, and for Danny, who has no CARDS row yet, the rank
from Scripts/GameProgress.gd's BOSSES - so a renumbering never bakes a stale plate.
"""
import os
import re
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "vs_card"))
import layout as LY                                                           # noqa: E402
import cards as CD                                                            # noqa: E402
import halves as HV                                                           # noqa: E402
import bands as BD                                                            # noqa: E402
import textart                                                                # noqa: E402  (read-only)

KEYS = ["computah", "mason", "danny", "liam"]
TABLE = LY.PROJ + "/Scripts/VsCardArtLayout.gd"
PROGRESS = LY.PROJ + "/Scripts/GameProgress.gd"

# vs_card/bosses.py's canon epithets (approved 2026-09-20). Computah had none of his own - his row
# there is bar-only, from when he shared Greyson's card as "THE LIFTER AND THE MACHINE" - so his is
# that epithet's half that was his. PROPOSED, flagged for approval.
EPITHET = {
    "computah": "THE MACHINE",
    "mason": "THE SHITPOSTER",
    "danny": "THE SLEEPING GIANT",
    "liam": "THE THRONE AND THE BEAST",
}
# the dialogue portrait each badge crops, and the 28 x 28 window that holds the face
BADGE = {
    "computah": ("Computah/portrait.png", (18, 12, 46, 40)),
    "mason": ("Mason/portrait.png", (15, 19, 43, 47)),
    "danny": ("Danny/portrait.png", (18, 14, 46, 42)),
    "liam": ("Liam/portrait.png", (18, 12, 46, 40)),
}
# two-line names (vs_card/bosses.py: LIAM & BIXBY is 55 px on two lines)
NAME_LINES = {"liam": (["LIAM", "& BIXBY"], 55)}
NAME_GAP = 6
# where each pose's top-left goes in the band (texels), with every eye on band row 58 +- 2
PLACE = {
    "computah": (306, 14),
    "mason": (372, 23),
    "danny": (340, 27),
    "liam": (360, -10),
}


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


def progress_rank(name):
    """A fight's rank from GameProgress.BOSSES, for a boss the card table has no row for yet."""
    src = open(PROGRESS, encoding="utf-8").read()
    m = re.search(r'"name": "%s", "rank": "([^"]*)"' % re.escape(name), src)
    return m.group(1) if m else ""


def card_row(key):
    t = table()
    if key in t:
        return t[key]
    if key == "danny":
        return {"number": 0, "name": "DANNY", "epithet": "", "rank": progress_rank("DANNY")}
    raise KeyError(key)


def pose(key):
    if key == "computah":
        import pose_computah as M
    elif key == "mason":
        import pose_mason as M
    elif key == "danny":
        import pose_danny as M
    elif key == "liam":
        import pose_liam as M
    else:
        raise KeyError(key)
    return M.build()


def name_plate(key, name):
    if key not in NAME_LINES:
        return textart.bake(name, 99)
    lines, size = NAME_LINES[key]
    plates = [textart.bake(t, size) for t in lines]
    w = max(p.width for p in plates)
    h = sum(p.height for p in plates) + NAME_GAP * (len(plates) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for p in plates:
        out.alpha_composite(p, (w - p.width, y))           # right-aligned, as the plate hangs
        y += p.height + NAME_GAP
    return out


def half(key, pose_img=None):
    b = BD.BANDS[key]
    p = pose_img if pose_img is not None else pose(key)
    return HV.right_half(p, PLACE[key], b["ramp"], b["accent"], b["mark"])


def set_files(key, pose_img=None):
    """{file name: image} for one boss's full set."""
    row = card_row(key)
    p = pose_img if pose_img is not None else pose(key)
    portrait, crop = BADGE[key]
    files = {
        "band_right_%s.png" % key: half(key, p),
        "pose_%s.png" % key: p,
        "name_%s.png" % key: name_plate(key, row["name"]),
        "epithet_%s.png" % key: textart.bake(EPITHET[key], 33, fill="#CDD7E2"),
    }
    if row["number"] > 0:
        files["fight_%02d.png" % row["number"]] = textart.bake("FIGHT %02d" % row["number"], 33,
                                                               fill="#9BADB7")
    if row["rank"]:
        files["win_%s.png" % row["rank"].lstrip("@")] = textart.bake("WIN " + row["rank"], 33,
                                                                     fill="#F2C457")
        files["badge_%s.png" % key] = CD.badge(portrait, crop)
    return files


def plates_for_card(key, files):
    """The files as compose.frame() takes them."""
    row = card_row(key)
    get = lambda pre: next((im for n, im in files.items() if n.startswith(pre)), None)
    return {"name": files["name_%s.png" % key], "epithet": files["epithet_%s.png" % key],
            "fight": get("fight_"), "win": get("win_"), "badge": get("badge_"),
            "vs": Image.open(LY.SHIPPED + "vs.png").convert("RGBA")}
