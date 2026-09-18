"""Greyson redesign - 96x96 frames, baseline row 95, meant for scale 3.

Kept from the old sprite + portrait: blonde crew-cut cap, blue eyes, the red
furrowed-brow marks on the forehead, blonde moustache, bronzed tan, purple
trunks, white wrestling boots, front-on bodybuilder stance.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import (Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip,
                    Sub, HalfPlane, polyline)

W = H = 96
AX = 47.0              # mirror axis (x' = 94 - x)
OUTLINE = "#150b11"

PAL = {
    "skin":   ["#FFEDC0", "#F9C587", "#E29B56", "#BD753A", "#8E4B26", "#5C2A1A"],
    "hair":   ["#FFF8C0", "#F6DE68", "#D6B833", "#A0871A", "#6A560E"],
    "trunk":  ["#D09CF6", "#A567E0", "#7F3DB8", "#5A278A", "#381356"],
    "boot":   ["#FFFFFF", "#E9EDF7", "#C4CADD", "#969DB6", "#5F6582"],
    "rage":   ["#FFC7A0", "#FF9668", "#EA6A42", "#BF4227", "#8B2718", "#5A140E"],
    "steel":  ["#E7EFF7", "#BDCCDA", "#93A6B9", "#6B7B90", "#4A5668", "#2C3442"],
}

FACE_CH = {
    "K": OUTLINE, "E": "#FFFFFF", "B": "#2F6BCC", "b": "#7FB6F5",
    "r": "#BE3427", "t": "#F7F3E6", "o": "#40121A", "p": "#8E3B45",
    "S": ("skin", 0), "s": ("skin", 1), "n": ("skin", 2), "m": ("skin", 3),
    "w": ("skin", 4), "x": ("skin", 5),
    "H": ("hair", 0), "h": ("hair", 1), "g": ("hair", 2), "d": ("hair", 3),
}
RAGE_CH = dict(FACE_CH)
RAGE_CH.update({"S": ("rage", 0), "s": ("rage", 1), "n": ("rage", 2),
                "m": ("rage", 3), "w": ("rage", 4), "x": ("rage", 5),
                "B": "#FFFFFF", "b": "#FFF0B0", "E": "#FFE8C0"})

# 27 wide; local column 13 is the mirror axis (= x 47).  Blank cells keep the
# procedural skull/hair shading underneath, so only the FEATURES are authored.
#         0    5   10   15   20   25
#         |    |    |    |    |    |
FACE = [
    "                           ",   # 0   rows 0-9 are the hair cap: left to
    "                           ",   # 1   the shader so the skull stays round
    "                           ",   # 2
    "                           ",   # 3
    "                           ",   # 4
    "                           ",   # 5
    "                           ",   # 6
    "                           ",   # 7
    "                           ",   # 8
    "                           ",   # 9
    "            rrr            ",   # 10  red furrow marks (from the portrait)
    "           rr rr           ",   # 11
    "          rr   rr          ",   # 12
    "   SdggSSSSSSSssnnnmggdw   ",   # 13  brow, outer end high
    "  nsSSgggddSSSsnddgggnmmw  ",   # 14  brow, inner end low = angry
    "  nsSKKKKKSsSSsnnKKKKKmmw  ",   # 15  lash line
    "  nsSEEBBESSSSsnnEBBEEmmw  ",   # 16  eyes
    "  nswEbBBEsSSsnnmEbBBEmmw  ",   # 17
    "  nsnwwwwnsSSsnmnwwwwnmmw  ",   # 18  lower lid + nose bridge
    "   sSSssnnnSSsnmnnmmmmww   ",   # 19  nose
    "   sSssnnnxnSsnmxmmmmwww   ",   # 20  nostrils
    "   sSsnnmmnnnnnmmmmmwwww   ",   # 21  philtrum
    "    SsngghHHhhhhhgggmww    ",   # 22  blonde moustache
    "    Ssngdooooooooodgmww    ",   # 23  moustache droop + mouth
    "    Ssnnmototttotomnmww    ",   # 24  gritted teeth
    "     snnmpppppppppmnmw     ",   # 25  lower lip
    "      nSSssnnnnmmmmww      ",   # 26  chin
    "        nSssnnnmmmw        ",   # 27
    "         nssnnnmmw         ",   # 28  jaw
]
FACE_Y = 1
FACE_X = 34


_CLASS = {}
for _c in " ":
    _CLASS[_c] = "blank"
for _c in "K":
    _CLASS[_c] = "ink"
for _c in "EBb":
    _CLASS[_c] = "eye"
for _c in "r":
    _CLASS[_c] = "red"
for _c in "t":
    _CLASS[_c] = "teeth"
for _c in "op":
    _CLASS[_c] = "mouth"
for _c in "Ssnmwx":
    _CLASS[_c] = "skin"
for _c in "Hhgd":
    _CLASS[_c] = "hair"


def _check_face():
    """Shading may be asymmetric (one light source) but the FORM may not."""
    bad = []
    for j, row in enumerate(FACE):
        if len(row) != 27:
            bad.append("row %d length %d" % (j, len(row)))
            continue
        for i in range(13):
            a, b = _CLASS.get(row[i]), _CLASS.get(row[26 - i])
            if a != b:
                bad.append("row %d col %d/%d %r/%r" % (j, i, 26 - i, row[i], row[26 - i]))
    return bad

# ---------------------------------------------------------------------------


def _mir(p):
    return (2 * AX - p[0], p[1])


def _mirror_arm(a):
    return {
        "delt": (2 * AX - a["delt"][0], a["delt"][1], a["delt"][2], a["delt"][3]),
        "uarm": (_mir(a["uarm"][0]), _mir(a["uarm"][1]), a["uarm"][2], a["uarm"][3]),
        "bice": (2 * AX - a["bice"][0], a["bice"][1], a["bice"][2], a["bice"][3]),
        "farm": (_mir(a["farm"][0]), _mir(a["farm"][1]), a["farm"][2], a["farm"][3]),
        "fist": (2 * AX - a["fist"][0], a["fist"][1], a["fist"][2], a["fist"][3]),
    }


def _mirror_leg(l):
    return {
        "thigh": (_mir(l["thigh"][0]), _mir(l["thigh"][1]), l["thigh"][2], l["thigh"][3]),
        "calf": (_mir(l["calf"][0]), _mir(l["calf"][1]), l["calf"][2], l["calf"][3]),
        "boot": (2 * AX - l["boot"][2], l["boot"][1], 2 * AX - l["boot"][0], l["boot"][3]),
    }


_DEFEAT_LEGS = [
    {"thigh": ((39.5, 69.0), (32.5, 82.0), 10.0, 7.6),
     "calf": ((32.5, 82.0), (31.0, 89.0), 7.4, 6.6), "boot": (23.0, 84.0, 39.0, 95.0)},
    {"thigh": ((39.5, 76.0), (29.0, 86.0), 9.8, 7.4),
     "calf": ((29.0, 86.0), (27.0, 92.0), 7.2, 6.4), "boot": (19.0, 88.0, 35.0, 95.0)},
    {"thigh": ((40.0, 82.0), (27.0, 90.0), 9.4, 7.2),
     "calf": ((27.0, 90.0), (25.0, 94.0), 7.0, 6.2), "boot": (16.0, 89.0, 32.0, 95.0)},
    {"thigh": ((40.5, 86.0), (26.0, 92.0), 9.0, 7.0),
     "calf": ((26.0, 92.0), (24.0, 95.0), 6.8, 6.0), "boot": (14.0, 90.0, 30.0, 95.0)},
    {"thigh": ((40.5, 86.5), (26.0, 92.5), 9.0, 7.0),
     "calf": ((26.0, 92.5), (24.0, 95.0), 6.8, 6.0), "boot": (14.0, 90.5, 30.0, 95.0)},
]

_DEFEAT_ARMS = [
    {"delt": (22.0, 44.0, 9.4, 8.8), "uarm": ((22.0, 44.0), (13.5, 56.0), 8.8, 7.0),
     "bice": (18.0, 49.0, 7.4, 6.6), "farm": ((13.5, 56.0), (11.0, 66.0), 7.0, 5.8),
     "fist": (10.0, 70.0, 6.6, 6.2)},
    {"delt": (23.0, 51.0, 9.2, 8.6), "uarm": ((23.0, 51.0), (14.0, 63.0), 8.6, 6.8),
     "bice": (19.0, 56.0, 7.2, 6.4), "farm": ((14.0, 63.0), (11.0, 75.0), 6.8, 5.8),
     "fist": (10.0, 79.0, 6.6, 6.2)},
    {"delt": (23.5, 57.0, 9.0, 8.4), "uarm": ((23.5, 57.0), (14.0, 69.0), 8.4, 6.6),
     "bice": (19.0, 62.0, 7.0, 6.2), "farm": ((14.0, 69.0), (10.0, 81.0), 6.6, 5.6),
     "fist": (8.5, 86.0, 6.4, 6.0)},
    {"delt": (24.0, 61.0, 8.8, 8.2), "uarm": ((24.0, 61.0), (14.0, 73.0), 8.2, 6.4),
     "bice": (19.5, 66.0, 6.8, 6.0), "farm": ((14.0, 73.0), (9.5, 85.0), 6.4, 5.4),
     "fist": (8.0, 90.0, 6.2, 5.8)},
    {"delt": (24.0, 62.0, 8.8, 8.2), "uarm": ((24.0, 62.0), (14.0, 74.0), 8.2, 6.4),
     "bice": (19.5, 67.0, 6.8, 6.0), "farm": ((14.0, 74.0), (9.5, 86.0), 6.4, 5.4),
     "fist": (8.0, 91.0, 6.2, 5.8)},
]


def _shift_arm(a, dx=0.0, dy=0.0, hand=True):
    hy = dy if hand else 0.0
    return {
        "delt": (a["delt"][0] + dx, a["delt"][1] + dy, a["delt"][2], a["delt"][3]),
        "uarm": ((a["uarm"][0][0] + dx, a["uarm"][0][1] + dy),
                 (a["uarm"][1][0] + dx, a["uarm"][1][1] + dy * 0.5),
                 a["uarm"][2], a["uarm"][3]),
        "bice": (a["bice"][0] + dx, a["bice"][1] + dy * 0.7, a["bice"][2], a["bice"][3]),
        "farm": ((a["farm"][0][0] + dx, a["farm"][0][1] + dy * 0.5),
                 (a["farm"][1][0] + dx, a["farm"][1][1] + hy), a["farm"][2], a["farm"][3]),
        "fist": (a["fist"][0] + dx, a["fist"][1] + hy, a["fist"][2], a["fist"][3]),
    }


def _shift_leg(l, dx=0.0, dy=0.0):
    return {
        "thigh": ((l["thigh"][0][0] + dx, l["thigh"][0][1] + dy),
                  (l["thigh"][1][0] + dx, l["thigh"][1][1] + dy * 0.4),
                  l["thigh"][2], l["thigh"][3]),
        "calf": ((l["calf"][0][0] + dx, l["calf"][0][1] + dy * 0.4),
                 l["calf"][1], l["calf"][2], l["calf"][3]),
        "boot": l["boot"],
    }


def _breathe(r, d):
    """lift the shoulders and swell the chest by d px; hands stay put"""
    hx, hy, hrx, hry = r["head"]
    r["head"] = (hx, hy - d, hrx, hry)
    r["head_dy"] -= d
    n0, n1, nr0, nr1 = r["neck"]
    r["neck"] = ((n0[0], n0[1] - d), (n1[0], n1[1] - d * 0.5), nr0, nr1)
    t0, t1, tr0, tr1 = r["trap"]
    r["trap"] = ((t0[0], t0[1] - d), (t1[0], t1[1] - d * 0.6), tr0, tr1)
    r["chest_ry"] = d * 0.55
    for k in ("armL", "armR"):
        r[k] = _shift_arm(r[k], 0, -d * 0.5, hand=False)
    return r


def _sink(r, d):
    """drop the whole upper body d px (crouch / kneel / collapse)"""
    hx, hy, hrx, hry = r["head"]
    r["head"] = (hx, hy + d, hrx, hry)
    r["head_dy"] += d
    n0, n1, nr0, nr1 = r["neck"]
    r["neck"] = ((n0[0], n0[1] + d), (n1[0], n1[1] + d), nr0, nr1)
    t0, t1, tr0, tr1 = r["trap"]
    r["trap"] = ((t0[0], t0[1] + d), (t1[0], t1[1] + d), tr0, tr1)
    r["body_dy"] = d
    r["trunk_y"] = (r["trunk_y"][0] + d, r["trunk_y"][1] + d)
    return r


def _rig(pose):
    # ---- derived loops -------------------------------------------------
    if pose.startswith("idle"):
        base = _rig("hero")
        return _breathe(base, (0.0, 1.0, 2.0, 1.0)[int(pose[-1])])
    if pose.startswith("p2_idle"):
        base = _rig("phase2")
        return _breathe(base, (0.0, 1.5, 3.0, 1.5)[int(pose[-1])])

    armL = {
        "delt": (23.5, 39.0, 9.2, 8.6),
        "uarm": ((23.5, 39.0), (17.0, 54.0), 8.6, 6.8),
        "bice": (20.0, 45.0, 7.2, 6.4),
        "farm": ((17.0, 54.0), (14.5, 66.5), 6.8, 5.8),
        "fist": (13.5, 71.0, 6.6, 6.2),
    }
    legL = {
        "thigh": ((39.5, 64.0), (36.0, 79.0), 10.0, 7.6),
        "calf": ((36.0, 79.0), (35.0, 86.0), 7.4, 6.6),
        "boot": (27.0, 80.0, 43.0, 95.0),
    }
    r = {
        "head": (AX, 15.5, 11.5, 14.5),
        "neck": ((AX, 26), (AX, 35), 6.8, 8.0),
        "trap": ((43, 31), (33.0, 41), 4.5, 9.4),
        "armL": armL, "armR": _mirror_arm(armL),
        "legL": legL, "legR": _mirror_leg(legL),
        "lean": 0.0, "head_dx": 0.0, "head_dy": 0.0,
        "trunk_y": (57, 70), "fore": None, "chamber": (),
        "scowl": False, "hair": "long", "body_dy": 0.0, "face": "base",
    }

    if pose == "windup":
        # coiled, not flexing: rear fist CHAMBERED tight at the ribs with the
        # elbow flung back, lead fist thrust at the camera, chin tucked,
        # weight braced on the back leg.
        r["head"] = (AX + 2.5, 18.5, 11.5, 14.5)
        r["head_dx"] = 2.0
        r["head_dy"] = 3.0
        r["scowl"] = True
        r["neck"] = ((AX + 2.5, 31), (AX + 1.5, 39), 7.2, 8.4)
        r["trap"] = ((44.5, 33), (32.5, 42), 4.8, 10.0)
        r["lean"] = 2.5
        r["armL"] = {
            "delt": (21.5, 41.0, 10.2, 9.6),
            "uarm": ((21.5, 41.0), (13.5, 49.5), 9.6, 8.0),
            "bice": (17.5, 44.5, 8.2, 7.6),
            "farm": ((13.5, 49.5), (21.0, 54.5), 8.0, 7.0),
            "fist": (23.5, 56.0, 7.0, 6.6),
        }
        r["armR"] = {
            "delt": (72.0, 42.0, 9.6, 9.0),
            "uarm": ((72.0, 42.0), (70.0, 48.0), 9.4, 9.2),
            "bice": (72.0, 44.0, 6.2, 5.8),
            "farm": ((70.0, 48.0), (66.0, 51.0), 9.6, 10.2),
            "fist": (63.5, 52.5, 10.8, 10.2),
        }
        r["fore"] = "armR"
        r["chamber"] = ("armL",)
        r["legL"] = {
            "thigh": ((39.5, 64.0), (31.0, 79.0), 10.2, 7.8),
            "calf": ((31.0, 79.0), (29.5, 86.0), 7.6, 6.8),
            "boot": (21.0, 80.0, 37.0, 95.0),
        }
        r["legR"] = {
            "thigh": ((55.0, 64.0), (62.0, 80.0), 9.8, 7.4),
            "calf": ((62.0, 80.0), (63.5, 86.0), 7.2, 6.4),
            "boot": (56.0, 80.0, 71.0, 95.0),
        }

    if pose == "phase2":
        r["head"] = (AX, 17.5, 11.5, 14.5)
        r["head_dy"] = 2.5
        r["neck"] = ((AX, 28), (AX, 37), 7.4, 8.6)
        r["trap"] = ((43, 32), (31.5, 42), 5.0, 10.2)
        r["armL"] = {
            "delt": (23.0, 40.0, 10.0, 9.4),
            "uarm": ((23.0, 40.0), (15.5, 55.0), 9.4, 7.6),
            "bice": (20.0, 46.0, 8.0, 7.4),
            "farm": ((15.5, 55.0), (17.5, 67.5), 7.6, 6.4),
            "fist": (18.0, 72.5, 7.2, 6.8),
        }
        r["armR"] = _mirror_arm(r["armL"])
        r["legL"] = {
            "thigh": ((39.5, 64.0), (34.5, 79.0), 10.4, 7.8),
            "calf": ((34.5, 79.0), (33.5, 86.0), 7.6, 6.8),
            "boot": (25.5, 80.0, 41.5, 95.0),
        }
        r["legR"] = _mirror_leg(r["legL"])

    # ---- five-hit combo -------------------------------------------------
    if pose in ("combo_r", "combo_l", "combo_rlow", "snapback"):
        r["scowl"] = True
        r["trunk_y"] = (57, 70)

    if pose == "combo_r":
        r["head"] = (AX + 3, 19.0, 11.5, 14.5)
        r["head_dx"] = 3.0
        r["head_dy"] = 3.5
        r["neck"] = ((AX + 3, 31), (AX + 2, 39), 7.2, 8.4)
        r["trap"] = ((45, 33), (33, 42), 4.8, 10.0)
        r["lean"] = 3.0
        r["armR"] = {
            "delt": (72.5, 42.5, 9.8, 9.2),
            "uarm": ((72.5, 42.5), (69.0, 49.0), 9.6, 9.4),
            "bice": (72.0, 45.0, 6.2, 5.8),
            "farm": ((69.0, 47.0), (60.0, 48.5), 10.0, 11.0),
            "fist": (53.0, 49.0, 13.0, 12.4),
        }
        r["armL"] = {
            "delt": (21.5, 41.0, 10.2, 9.6),
            "uarm": ((21.5, 41.0), (13.5, 49.5), 9.6, 8.0),
            "bice": (17.5, 44.5, 8.2, 7.6),
            "farm": ((13.5, 49.5), (21.0, 54.5), 8.0, 7.0),
            "fist": (23.5, 56.0, 7.0, 6.6),
        }
        r["fore"] = "armR"
        r["chamber"] = ("armL",)
        r["legL"] = {"thigh": ((39.5, 64.0), (30.0, 79.0), 10.2, 7.8),
                     "calf": ((30.0, 79.0), (28.5, 86.0), 7.6, 6.8),
                     "boot": (20.0, 80.0, 36.0, 95.0)}
        r["legR"] = {"thigh": ((55.0, 64.0), (63.0, 80.0), 9.8, 7.4),
                     "calf": ((63.0, 80.0), (64.5, 86.0), 7.2, 6.4),
                     "boot": (57.0, 80.0, 72.0, 95.0)}

    if pose == "combo_l":
        r["head"] = (AX - 2, 19.0, 11.5, 14.5)
        r["head_dx"] = -2.0
        r["head_dy"] = 3.5
        r["neck"] = ((AX - 2, 31), (AX - 1, 39), 7.2, 8.4)
        r["trap"] = ((41, 33), (29, 42), 4.8, 10.0)
        r["lean"] = -2.0
        r["armL"] = {
            "delt": (21.5, 42.5, 9.8, 9.2),
            "uarm": ((21.5, 42.5), (25.0, 49.0), 9.6, 9.4),
            "bice": (22.0, 45.0, 6.2, 5.8),
            "farm": ((25.0, 48.0), (35.0, 50.5), 10.0, 11.0),
            "fist": (44.0, 52.0, 12.6, 12.0),
        }
        r["armR"] = {
            "delt": (72.5, 41.0, 10.2, 9.6),
            "uarm": ((72.5, 41.0), (80.5, 49.5), 9.6, 8.0),
            "bice": (76.5, 44.5, 8.2, 7.6),
            "farm": ((80.5, 49.5), (73.0, 54.5), 8.0, 7.0),
            "fist": (70.5, 56.0, 7.0, 6.6),
        }
        r["fore"] = "armL"
        r["chamber"] = ("armR",)
        r["legL"] = {"thigh": ((39.5, 64.0), (31.5, 80.0), 9.8, 7.4),
                     "calf": ((31.5, 80.0), (30.0, 86.0), 7.2, 6.4),
                     "boot": (22.0, 80.0, 37.0, 95.0)}
        r["legR"] = {"thigh": ((55.0, 64.0), (64.0, 79.0), 10.2, 7.8),
                     "calf": ((64.0, 79.0), (65.5, 86.0), 7.6, 6.8),
                     "boot": (58.0, 80.0, 74.0, 95.0)}

    if pose == "combo_rlow":
        r["head"] = (AX + 2, 21.0, 11.5, 14.5)
        r["head_dx"] = 2.0
        r["head_dy"] = 5.5
        r["neck"] = ((AX + 2, 33), (AX + 1.5, 40), 7.2, 8.4)
        r["trap"] = ((44, 35), (32.5, 43), 4.8, 10.0)
        r["lean"] = 2.5
        r["body_dy"] = 1.5
        r["trunk_y"] = (58.5, 71.5)
        r["armR"] = {
            "delt": (72.0, 44.0, 9.8, 9.2),
            "uarm": ((72.0, 44.0), (68.0, 52.0), 9.6, 9.4),
            "bice": (71.0, 47.0, 6.2, 5.8),
            "farm": ((68.0, 51.0), (58.0, 53.5), 10.0, 10.8),
            "fist": (50.0, 55.0, 12.2, 11.6),
        }
        r["armL"] = {
            "delt": (21.5, 43.0, 10.2, 9.6),
            "uarm": ((21.5, 43.0), (14.0, 50.0), 9.6, 8.0),
            "bice": (17.5, 46.0, 8.2, 7.6),
            "farm": ((14.0, 50.0), (21.0, 52.5), 8.0, 7.0),
            "fist": (24.0, 53.5, 7.0, 6.6),
        }
        r["fore"] = "armR"
        r["chamber"] = ("armL",)
        r["legL"] = {"thigh": ((39.5, 65.5), (29.5, 80.0), 10.2, 7.8),
                     "calf": ((29.5, 80.0), (28.0, 86.0), 7.6, 6.8),
                     "boot": (19.5, 80.0, 35.5, 95.0)}
        r["legR"] = {"thigh": ((55.0, 65.5), (63.5, 80.0), 9.8, 7.4),
                     "calf": ((63.5, 80.0), (65.0, 86.0), 7.2, 6.4),
                     "boot": (57.5, 80.0, 72.5, 95.0)}

    if pose == "snapback":
        r["head"] = (AX + 1, 17.0, 11.5, 14.5)
        r["head_dx"] = 1.0
        r["head_dy"] = 1.5
        r["neck"] = ((AX + 1, 29), (AX + 1, 37), 7.0, 8.2)
        r["trap"] = ((44, 32), (33, 42), 4.8, 9.8)
        r["lean"] = 1.0
        r["armL"] = {
            "delt": (22.5, 40.0, 10.0, 9.4),
            "uarm": ((22.5, 40.0), (15.5, 48.0), 9.4, 7.8),
            "bice": (19.0, 44.0, 7.8, 7.2),
            "farm": ((15.5, 48.0), (23.0, 51.5), 7.8, 7.0),
            "fist": (25.5, 53.0, 7.2, 6.8),
        }
        r["armR"] = _mirror_arm(r["armL"])
        r["chamber"] = ("armL", "armR")
        r["legL"] = {"thigh": ((39.5, 64.0), (33.5, 79.0), 10.0, 7.6),
                     "calf": ((33.5, 79.0), (32.5, 86.0), 7.4, 6.6),
                     "boot": (24.5, 80.0, 40.5, 95.0)}
        r["legR"] = _mirror_leg(r["legL"])

    # ---- hit reaction ---------------------------------------------------
    if pose.startswith("hit"):
        k = int(pose[-1])
        r["face"] = "hurt" if k < 2 else "base"
        lean = (-3.5, -2.0, -0.8)[k]
        dy = (-2.0, -0.5, 0.0)[k]
        r["head"] = (AX + lean, 15.5 + dy, 11.5, 14.5)
        r["head_dx"] = lean
        r["head_dy"] = dy
        r["neck"] = ((AX + lean, 26 + dy), (AX + lean * .5, 35), 6.8, 8.0)
        r["trap"] = ((43 + lean, 31 + dy), (33 + lean, 41), 4.5, 9.4)
        r["lean"] = lean
        spread = (4.0, 2.5, 1.0)[k]
        rise = (13.0, 6.5, 2.0)[k]
        r["armL"] = {
            "delt": (23.5 - spread * .4, 39.0 - rise * .2, 9.2, 8.6),
            "uarm": ((23.5 - spread * .4, 39.0 - rise * .2),
                     (17.0 - spread, 54.0 - rise), 8.6, 6.8),
            "bice": (20.0 - spread * .7, 45.0 - rise * .5, 7.2, 6.4),
            "farm": ((17.0 - spread, 54.0 - rise),
                     (14.5 - spread * 1.2, 66.5 - rise * 1.6), 6.8, 5.8),
            "fist": (13.5 - spread * 1.3, 71.0 - rise * 1.9, 6.6, 6.2),
        }
        r["armR"] = _mirror_arm(r["armL"])
        sq = (5.0, 2.5, 1.0)[k]
        r["legL"] = {"thigh": ((39.5, 64.0 + sq), (35.0, 80.0), 10.0, 7.6),
                     "calf": ((35.0, 80.0), (34.0, 86.0), 7.4, 6.6),
                     "boot": (26.0, 80.0, 42.0, 95.0)}
        r["legR"] = _mirror_leg(r["legL"])
        _sink(r, sq * 0.6)

    # ---- defeat ---------------------------------------------------------
    if pose.startswith("defeat"):
        k = int(pose[-1])
        sink = (5.0, 12.0, 18.0, 22.0, 23.0)[k]
        r["face"] = "hurt" if k == 0 else ("out" if k >= 2 else "base")
        r["lean"] = (-2.0, -1.0, 0.0, 1.0, 1.0)[k]
        head_fwd = (0.0, 2.0, 5.0, 8.0, 9.0)[k]
        r["legL"] = _DEFEAT_LEGS[k]
        r["legR"] = _mirror_leg(_DEFEAT_LEGS[k])
        r["armL"] = _DEFEAT_ARMS[k]
        r["armR"] = _mirror_arm(_DEFEAT_ARMS[k])
        _sink(r, sink)
        hx, hy, hrx, hry = r["head"]
        r["head"] = (hx, hy + head_fwd, hrx, hry)
        r["head_dy"] += head_fwd
    return r


# ---------------------------------------------------------------------------
def build(pose="hero", hair=None):
    rage = pose == "phase2" or pose.startswith("p2_")
    mat = "rage" if rage else "skin"
    c = Canvas(W, H, PAL, OUTLINE)
    r = _rig(pose)
    if hair:
        r["hair"] = hair
    L = r["lean"]
    B = r["body_dy"]
    hx, hy, hrx, hry = r["head"]
    ty0, ty1 = r["trunk_y"]
    ch = r.get("chest_ry", 0.0)

    # ---- torso ---------------------------------------------------------
    chest = Ellipse(AX + L * .7, 41 + B, 20.5, 10.0 + ch)
    latL = Ellipse(AX - 13.0 + L * .7, 48 + B, 11.0, 11.0)
    latR = Ellipse(AX + 13.0 + L * .7, 48 + B, 11.0, 11.0)
    belly = Ellipse(AX + L, 55 + B, 11.8, 9.5)
    waist = Ellipse(AX + L, 61 + B, 9.8, 6.5)
    torso = Union([chest, latL, latR, belly, waist], k=2.4)
    c.add(torso, mat, prio=1)

    hips = Ellipse(AX + L, 66 + B, 14.5, 8.5)
    c.add(hips, mat, prio=1)

    tp = r["trap"]
    c.add(Capsule(tp[0], tp[1], tp[2], tp[3]), mat, prio=2)
    c.add(Capsule(_mir(tp[0]), _mir(tp[1]), tp[2], tp[3]), mat, prio=2)
    n = r["neck"]
    c.add(Capsule(n[0], n[1], n[2], n[3]), mat, prio=2)

    pecL = Ellipse(AX - 9.0 + L * .7, 41 + B, 10.2, 7.0 + ch)
    pecR = Ellipse(AX + 9.0 + L * .7, 41 + B, 10.2, 7.0 + ch)
    c.add(pecL, mat, prio=3)
    c.add(pecR, mat, prio=3)

    # ---- legs ----------------------------------------------------------
    legs = []
    for key in ("legL", "legR"):
        g = r[key]
        th = Capsule(g["thigh"][0], g["thigh"][1], g["thigh"][2], g["thigh"][3])
        c.add(th, mat, prio=2)
        c.add(Capsule(g["calf"][0], g["calf"][1], g["calf"][2], g["calf"][3]),
              mat, prio=2)
        legs.append(th)

    # ---- trunks --------------------------------------------------------
    tx = AX - 19 + L
    trunk_poly = Poly([
        (tx + 1, ty0 - 2), (2 * AX - tx - 1, ty0 - 2),
        (2 * AX - tx + 2, ty0 + 5), (2 * AX - tx + 2, ty1 + 2),
        (AX + 11, ty1 + 3), (AX + 8.0, ty1 - 2), (AX, ty1 + 1),
        (AX - 8.0, ty1 - 2), (AX - 11, ty1 + 3),
        (tx - 2, ty1 + 2), (tx - 2, ty0 + 5)], round_r=6)
    c.add(Clip(Union([hips] + legs, k=2.2), trunk_poly), "trunk", prio=4)

    # ---- boots ---------------------------------------------------------
    for key in ("legL", "legR"):
        b = r[key]["boot"]
        c.add(RoundRect(b[0], b[1], b[2], b[3], r=4.0, round_r=6.5), "boot", prio=5)

    # ---- arms ----------------------------------------------------------
    order = ["armL", "armR"]
    if r["fore"]:
        order = [k for k in order if k != r["fore"]] + [r["fore"]]
    for i, key in enumerate(order):
        a = r[key]
        p = 6 + i * 4
        c.add(Ellipse(*a["delt"]), mat, prio=p)
        c.add(Capsule(a["uarm"][0], a["uarm"][1], a["uarm"][2], a["uarm"][3]),
              mat, prio=p)
        c.add(Ellipse(*a["bice"]), mat, prio=p + 1)
        c.add(Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3]),
              mat, prio=p + 2)
        c.add(Ellipse(*a["fist"]), mat, prio=p + 3)

    # ---- head ----------------------------------------------------------
    c.add(Ellipse(hx, hy + 4.0, hrx - 2.0, hry - 3.0), mat, prio=16,
          wrap=0.55, amb=0.16)
    c.add(Ellipse(hx, hy, hrx, hry), mat, prio=16, wrap=0.55, amb=0.16)
    c.add(Ellipse(hx - hrx + 0.8, hy + 4.5, 2.8, 4.4), mat, prio=16)
    c.add(Ellipse(hx + hrx - 0.8, hy + 4.5, 2.8, 4.4), mat, prio=16)
    for shp in _hair(r["hair"], hx, hy, hrx, hry):
        c.add(shp, "hair", prio=18, wrap=0.60, amb=0.10)
    _strands(c, r["hair"], hx, hy, hrx, hry)

    # ---- separation between overlapping parts ---------------------------
    for key in order:
        a = r[key]
        c.contour(Ellipse(*a["delt"]), 1.3, 2, mats=(mat,))
        c.contour(Capsule(a["uarm"][0], a["uarm"][1], a["uarm"][2], a["uarm"][3]),
                  1.3, 2, mats=(mat,))
        c.contour(Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3]),
                  1.3, 2, mats=(mat,))
    if r["fore"]:
        a = r[r["fore"]]
        c.contour(Ellipse(a["fist"][0], a["fist"][1], a["fist"][2] + .4,
                          a["fist"][3] + .4), 1.6, 9, color=OUTLINE)
    for key in r["chamber"]:
        a = r[key]
        c.contour(Ellipse(a["fist"][0], a["fist"][1], a["fist"][2] + .3,
                          a["fist"][3] + .3), 1.4, 9, color=OUTLINE)
        c.contour(Capsule(a["farm"][0], a["farm"][1], a["farm"][2] + .3,
                          a["farm"][3] + .3), 1.3, 3, mats=(mat,))
    # jaw drops a shadow onto the neck and traps only, never onto the head
    c.contour(Ellipse(hx, hy + 2.0, hrx - 1.0, hry - 1.0), 1.4, 2, mats=(mat,),
              below_prio=16)

    _anatomy(c, r, L, mat, ty0, ty1, B)
    if rage:
        _rage_extras(c, r)

    face = FACE
    if r["face"] == "hurt":
        face = _hurt(FACE)
    elif r["face"] == "out":
        face = _out(FACE)
    elif r["scowl"]:
        face = _scowl(FACE)
    c.stamp(face, int(FACE_X + r["head_dx"]), int(FACE_Y + r["head_dy"]),
            RAGE_CH if rage else FACE_CH)

    c.occlude(strength=2, reach=2)
    c.rim(1, mats=(mat, "hair", "trunk", "boot"))
    c.despeckle()
    return c


# ---------------------------------------------------------------------------
def _hair(style, hx, hy, hrx, hry):
    """Two lengths for review.  Both use a parted fringe that points down over
    the temples and leaves the centre forehead bare, so the three red furrow
    marks stay readable - they are the thing that makes the face his."""
    if style == "crew":
        line = Poly([(hx - 22, hy - 26), (hx + 22, hy - 26), (hx + 22, hy - 2.0),
                     (hx + 11, hy - 3.0), (hx + 8, hy - 5.5), (hx + 4, hy - 4.5),
                     (hx, hy - 5.5), (hx - 4, hy - 4.5), (hx - 8, hy - 5.5),
                     (hx - 11, hy - 3.0), (hx - 22, hy - 2.0)], round_r=9)
        return [Clip(Ellipse(hx, hy, hrx + 0.5, hry + 0.4), line)]

    # the face opening, with a fringe biting back into it over each temple
    face = Ellipse(hx, hy + 5.0, hrx - 1.6, hry - 2.2)
    frL = Poly([(hx - 13, hy - 11), (hx - 3.5, hy - 7.5), (hx - 5.5, hy - 1.0),
                (hx - 14, hy - 3.0)], round_r=3)
    frR = Poly([(hx + 13, hy - 11), (hx + 3.5, hy - 7.5), (hx + 5.5, hy - 1.0),
                (hx + 14, hy - 3.0)], round_r=3)
    hole = Sub(Sub(face, frL), frR)

    if style == "mid":
        mass = Ellipse(hx, hy + 1.0, hrx + 2.2, hry + 3.6)
        jaw = HalfPlane(0, 1, -(hy + hry + 2.0))
        return [Sub(Clip(mass, jaw), hole)]

    # long: a wrestler's mane spilling over the traps onto the pecs
    mass = Ellipse(hx, hy + 1.5, hrx + 2.6, hry + 4.4)
    fallL = Capsule((hx - hrx - 1.0, hy - 1), (hx - hrx - 2.5, hy + 24), 5.4, 4.6)
    fallR = Capsule((hx + hrx + 1.0, hy - 1), (hx + hrx + 2.5, hy + 24), 5.4, 4.6)
    return [Sub(Union([mass, fallL, fallR], k=2.0), hole)]


def _strands(c, style, hx, hy, hrx, hry):
    """Darker strand grooves + a lit band on the crown.  Without these the
    hair reads as a helmet of flat colour at 3x."""
    if style == "crew":
        return
    long_ = style == "long"
    end = hy + (22 if long_ else 8)
    for dx, bend in ((-8.5, -2.5), (5.0, 1.5), (10.5, 3.0)):
        c.shade_px(polyline([(hx + dx, hy - hry + 4),
                             (hx + dx * 1.3, hy + 1),
                             (hx + dx * 1.45 + bend, end)]), 2, "hair")
    c.shade_px(polyline([(hx - 10, hy - 9), (hx - 4, hy - 12), (hx + 3, hy - 11)]),
               -2, "hair")
    c.shade_px(polyline([(hx - 12, hy - 5), (hx - 13, hy + 2)]), -1, "hair")
    if long_:
        for sgn in (-1, 1):
            c.shade_px(polyline([(hx + sgn * (hrx + 3.5), hy + 8),
                                 (hx + sgn * (hrx + 4.5), hy + 21)]), 2, "hair")


def _scowl(face):
    """heavier brow + narrowed eyes for the wind-up and the combo"""
    g = list(face)
    g[14] = "  nsddggdd       ddggddnmmw"
    g[15] = "  nsdKKKKKSsSSsnnKKKKKdmm  "
    return g


def _hurt(face):
    """eyes screwed shut, mouth blown open - the hit reaction"""
    g = list(face)
    g[16] = "  nsSKKKKKSSSSsnnKKKKKmmw  "
    g[17] = "  nswwwwwwsSSsnnmwwwwwmmw  "
    g[24] = "    Ssnnmtttttttttmnmww    "
    g[25] = "     snnmooooooooomnmw     "
    g[26] = "      nSsooooooommmww      "
    return g


def _out(face):
    """lights out: closed eyes, slack mouth - defeat hold"""
    g = list(face)
    g[16] = "  nsSKKKKKSSSSsnnKKKKKmmw  "
    g[17] = "  nswnnnnnsSSsnnmnnnnnmmw  "
    g[24] = "    Ssnnmooooooooomnmww    "
    return g


# ---------------------------------------------------------------------------
def _anatomy(c, r, L, mat, ty0, ty1, B=0.0):
    P = lambda pts: [(int(round(a + L)), int(round(b + B))) for a, b in pts]

    c.shade_px(P(polyline([(AX, 35), (AX, 48)])), 2, mat)
    c.shade_px(P(polyline([(AX - 18, 45), (AX - 11, 48), (AX - 3, 48)])), 2, mat)
    c.shade_px(P(polyline([(AX + 18, 45), (AX + 11, 48), (AX + 3, 48)])), 2, mat)
    c.shade_px(P(polyline([(AX - 14, 37), (AX - 5, 36)])), -1, mat)
    c.shade_px(P(polyline([(AX + 14, 37), (AX + 5, 36)])), -1, mat)
    c.shade_px(P(polyline([(AX - 12, 34), (AX - 4, 35)])), 1, mat)
    c.shade_px(P(polyline([(AX + 12, 34), (AX + 4, 35)])), 1, mat)

    c.shade_px(P(polyline([(AX, 49), (AX, 62)])), 2, mat)
    for yy, w in ((51, 7), (55, 7), (59, 5)):
        c.shade_px(P(polyline([(AX - w, yy), (AX + w, yy)])), 2, mat)
        c.shade_px(P(polyline([(AX - w + 1, yy - 1), (AX + w - 1, yy - 1)])), -1, mat)

    c.shade_px(P(polyline([(AX - 12, 51), (AX - 10, 57), (AX - 7, 62)])), 2, mat)
    c.shade_px(P(polyline([(AX + 12, 51), (AX + 10, 57), (AX + 7, 62)])), 2, mat)
    for i, yy in enumerate((45, 49, 53)):
        c.shade_px(P(polyline([(AX - 17 + i, yy), (AX - 13 + i, yy + 2)])), 2, mat)
        c.shade_px(P(polyline([(AX + 17 - i, yy), (AX + 13 - i, yy + 2)])), 2, mat)

    c.shade_px(P(polyline([(AX - 9, 29), (AX - 14, 35)])), 1, mat)
    c.shade_px(P(polyline([(AX + 9, 29), (AX + 14, 35)])), 1, mat)

    for key in ("armL", "armR"):
        a = r[key]
        dx, dy = a["delt"][0], a["delt"][1]
        s = -1 if dx < AX else 1
        c.shade_px(polyline([(dx - 4 * s, dy + 3), (dx + 4 * s, dy + 6)]), 2, mat)
        c.shade_px(polyline([(dx - 5 * s, dy - 1), (dx + 3 * s, dy + 1)]), 2, mat)
        bx, by = a["bice"][0], a["bice"][1]
        c.shade_px(polyline([(bx - 2 * s, by - 4), (bx - 3 * s, by + 2)]), -1, mat)
        e = a["farm"][0]
        c.shade_px(polyline([(e[0] - 3, e[1] + 1), (e[0] + 3, e[1] + 2)]), 2, mat)
        _fist(c, a["fist"], mat, fore=(key == r["fore"]))

    for key in ("legL", "legR"):
        g = r[key]
        kx, ky = g["thigh"][1]
        s = -1 if kx < AX else 1
        c.shade_px(polyline([(kx + 3 * s, ky - 12), (kx + 1 * s, ky - 3)]), 2, mat)
        c.shade_px(polyline([(kx - 4 * s, ky - 11), (kx - 3 * s, ky - 2)]), 2, mat)
        c.shade_px(polyline([(kx - 4, ky), (kx + 4, ky)]), 1, mat)

    for key in ("legL", "legR"):
        _boot(c, r[key]["boot"])

    c.shade_px([(x, ty0 - 1) for x in range(22, 74)], -1, "trunk")
    c.shade_px([(x, ty0 + 1) for x in range(22, 74)], 2, "trunk")
    # trunks cast onto the thighs
    c.shade_px([(x, ty1 + 1) for x in range(24, 72)], 2, mat)
    c.shade_px([(x, ty1 + 2) for x in range(26, 70)], 1, mat)
    c.shade_px(polyline([(AX - 12, ty0 + 4), (AX - 14, ty1)]), 2, "trunk")
    c.shade_px(polyline([(AX + 12, ty0 + 4), (AX + 14, ty1)]), 2, "trunk")
    c.shade_px(polyline([(AX, ty0 + 3), (AX, ty1 - 1)]), 2, "trunk")


def _fist(c, fist, mat, fore=False):
    """knuckle blocks + a wrapped thumb, so a fist never reads as a ball"""
    fx, fy, frx, fry = [float(v) for v in fist]
    ix, iy = int(round(fx)), int(round(fy))
    if fore:
        # thrown at the camera: four knuckles across the middle
        for k in range(-2, 2):
            gx = ix + int(round((k + 0.5) * frx * 0.46))
            c.shade_px([(gx, iy - 3), (gx, iy - 2), (gx, iy - 1), (gx, iy)], 2, mat)
        for k in range(-2, 2):
            hxp = ix + int(round(k * frx * 0.46)) + 1
            c.shade_px([(hxp, iy - 4), (hxp + 1, iy - 4)], -2, mat)
        c.shade_px(polyline([(ix - frx * .75, iy + 2), (ix, iy + 4),
                             (ix + frx * .55, iy + 3)]), 2, mat)
        c.shade_px(polyline([(ix - frx * .7, iy + 4), (ix - frx * .2, iy + 6)]), 2, mat)
        c.shade_px(polyline([(ix - frx * .45, iy - 6), (ix + frx * .3, iy - 6)]), -2, mat)
    else:
        for k in range(-1, 2):
            gx = ix + int(round(k * frx * 0.55))
            c.shade_px([(gx, iy - 1), (gx, iy), (gx, iy + 1)], 2, mat)
        c.shade_px(polyline([(ix - frx * .7, iy - 3), (ix + frx * .55, iy - 3)]), -1, mat)
        c.shade_px(polyline([(ix - frx * .55, iy + 3), (ix + frx * .45, iy + 3)]), 2, mat)
        s = 1 if fx < AX else -1
        c.shade_px(polyline([(ix + frx * .55 * s, iy - 1),
                             (ix + frx * .75 * s, iy + 2)]), 2, mat)


def _boot(c, b):
    """white wrestling boot: cuff, lace bars, dark sole"""
    x0, y0, x1, y1 = int(b[0]), int(b[1]), int(b[2]), int(b[3])
    cx = (x0 + x1) // 2
    c.shade_px([(x, y0 + 1) for x in range(x0, x1 + 1)], -2, "boot")
    c.shade_px([(x, y0 + 3) for x in range(x0, x1 + 1)], 3, "boot")
    for k, y in enumerate(range(y0 + 6, y1 - 4, 3)):
        w = 3 + k
        c.shade_px([(x, y) for x in range(cx - w, cx + w + 1)], 2, "boot")
    c.shade_px([(cx, y) for y in range(y0 + 5, y1 - 4)], 1, "boot")
    c.shade_px([(x, y) for x in range(x0, x0 + 2) for y in range(y0 + 4, y1 - 2)],
               1, "boot")
    c.shade_px([(x, y1 - 2) for x in range(x0 - 1, x1 + 2)], 2, "boot")
    c.shade_px([(x, y1 - 1) for x in range(x0 - 1, x1 + 2)], 4, "boot")
    c.shade_px([(x, y1) for x in range(x0 - 1, x1 + 2)], 4, "boot")


def _rage_extras(c, r):
    for key in ("armL", "armR"):
        a = r[key]
        fx, fy = a["farm"][0]
        tx, ty = a["farm"][1]
        c.shade_px(polyline([(fx + 1, fy + 3), (tx, ty - 6), (tx + 2, ty - 2)]),
                   -2, "rage")
    c.shade_px(polyline([(AX - 11, 40), (AX - 15, 45)]), -2, "rage")
    c.shade_px(polyline([(AX + 11, 40), (AX + 15, 45)]), -2, "rage")
    c.shade_px(polyline([(AX - 4, 30), (AX - 7, 34)]), -2, "rage")

    # Computah's snapped antenna clenched in his screen-left fist
    rod = polyline([(13, 76), (9, 84), (7, 90)])
    for (x, y) in rod:
        c.set_px([(x, y)], "steel", 1)
        c.set_px([(x + 1, y)], "steel", 3)
    c.raw_px([(6, 91), (7, 91), (6, 92), (7, 92)], "#B8322A")
    c.raw_px([(6, 91)], "#FF8A7A")
    # a single tear on his cheek
    c.raw_px([(int(AX) - 9, 28), (int(AX) - 9, 29)], "#9FE0FF")
    c.raw_px([(int(AX) - 9, 27)], "#E8F8FF")


SHEETS = {
    "greyson_idle":       ["idle0", "idle1", "idle2", "idle3"],
    "greyson_combo":      ["windup", "combo_r", "combo_l", "combo_rlow", "snapback"],
    "greyson_hit":        ["hit0", "hit1", "hit2"],
    "greyson_defeat":     ["defeat0", "defeat1", "defeat2", "defeat3", "defeat4"],
    "greyson_phase2_idle": ["p2_idle0", "p2_idle1", "p2_idle2", "p2_idle3"],
}

# fist centre of the punching hand, in frame pixels (x, y) - multiply by the
# sprite scale and add the sprite origin to place an impact burst
CONTACT = {"combo_r": (53, 49), "combo_l": (44, 52), "combo_rlow": (50, 55)}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    bad = _check_face()
    if bad:
        print("FACE not symmetric:\n  " + "\n  ".join(bad))
        sys.exit(1)
    from PIL import Image
    for name in ("hero", "windup", "phase2"):
        build(name).to_image().save(os.path.join(out, "greyson_%s.png" % name))
    for h in ("crew", "mid", "long"):
        build("hero", hair=h).to_image().save(
            os.path.join(out, "greyson_hair_%s.png" % h))
    for sheet, poses in SHEETS.items():
        ims = [build(p).to_image() for p in poses]
        strip = Image.new("RGBA", (W * len(ims), H), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.paste(im, (i * W, 0))
            im.save(os.path.join(out, "%s_f%d.png" % (sheet, i)))
        strip.save(os.path.join(out, "%s.png" % sheet))
        print("%-22s %d frames  %dx%d" % (sheet, len(ims), strip.width, strip.height))
    print("ok")
