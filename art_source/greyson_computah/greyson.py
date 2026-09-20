"""Greyson - 96x96 frames, feet on row 95, scale 3, drawn facing right.

Human proportions after the beat-'em-up reference the user approved: about
4.3 heads tall, real legs, a lat-spread stance with daylight between each arm
and the torso, and muscle indicated with a handful of deliberate shapes - two
pec volumes, a sternum line, an ab groove with two ticks - rather than either
modelled anatomy or flat blobs.  Six-tone ramps, shaded smoothly across each
mass, the same production level as Computah.

Identity: long strawberry-blonde mane, thin gold wire glasses, two forehead
veins in pink skin tones, thin blonde moustache, fair skin, blue eyes, purple
trunks with a clean hem, white boots, a vein down each forearm.

Fists are squared-off blocks and every mark on one runs to its own edge: a
round skin shape with two marks in it reads as a face at 1x.

    python greyson.py <out_dir>        writes the five production sheets
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import (Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip,
                    Sub, polyline)

W = H = 96
AX = 47.0              # mirror axis (x' = 94 - x)
OUTLINE = "#000000"

PAL = {
    "skin":  ["#FFF2E2", "#FFDCBE", "#F6CCA8", "#DCA57C", "#B07E58", "#835438"],
    "rage":  ["#FFDCC2", "#FFB088", "#F08050", "#C85630", "#94381C", "#63220E"],
    "hair":  ["#FFE6BC", "#FFC77E", "#F2A94E", "#CE8436", "#A16224", "#6E4116"],
    "trunk": ["#DEB8FA", "#C08CEE", "#A063DC", "#7E42B8", "#5A288A", "#3A1660"],
    "boot":  ["#FFFFFF", "#F2F6FE", "#DCE2F0", "#BCC4DA", "#949CB8", "#6A7290"],
    "steel": ["#F2F8FF", "#D4E0EE", "#B8C6D6", "#94A4B8", "#6E7E94", "#4A5668"],
}

FACE_CH = {
    "K": OUTLINE, "E": "#FFFFFF", "B": "#4A6E9E", "o": "#3A0F16",
    "G": "#F0CC5E", "t": "#FFFFFF",
    "v": "#CE7A60", "V": "#FFD4BC",
    "S": ("skin", 0), "s": ("skin", 1), "n": ("skin", 2), "m": ("skin", 3),
    "w": ("skin", 4), "x": ("skin", 5),
    "H": ("hair", 0), "h": ("hair", 1), "g": ("hair", 2), "d": ("hair", 3),
}
RAGE_CH = dict(FACE_CH)
RAGE_CH.update({"S": ("rage", 0), "s": ("rage", 1), "n": ("rage", 2),
                "m": ("rage", 3), "w": ("rage", 4), "x": ("rage", 5),
                "B": "#FFFFFF", "E": "#FFE8C0",
                "v": "#C0392B", "V": "#FF8A6A"})

# 19 wide; local column 9 is the mirror axis (= x 47)
#         0    5   10   15
#         |    |    |    |
FACE = [
    "                   ",   # 0   y2   crown
    "                   ",   # 1
    "                   ",   # 2
    "                   ",   # 3
    "                   ",   # 4
    "       v   v       ",   # 5   y7   forehead veins
    "       v   v       ",   # 6
    "        v v        ",   # 7
    "                   ",   # 8
    "    ddd     ddd    ",   # 9   y11  brows
    "   GGGGG   GGGGG   ",   # 10  y12  lens top rim
    "   GEBEG G GEBEG   ",   # 11  y13  eyes + bridge
    "   GGGGG   GGGGG   ",   # 12  y14  lens bottom rim
    "                   ",   # 13
    "        w w        ",   # 14  y16  nostrils
    "                   ",   # 15
    "      ddddddd      ",   # 16  y18  thin moustache
    "       KKKKK       ",   # 17  y19  mouth
    "       KtttK       ",   # 18  y20
    "                   ",   # 19
    "                   ",   # 20
]
FACE_Y = 2
FACE_X = 38

_CLASS = {" ": "b", "K": "k", "E": "e", "B": "e", "G": "gl", "t": "t", "o": "o",
          "v": "vn", "V": "vn"}
for _c in "Ssnmwx":
    _CLASS[_c] = "sk"
for _c in "Hhgd":
    _CLASS[_c] = "hr"


def _scowl(face):
    """wind-up and combo: brows driven down into an angry V"""
    g = list(face)
    g[8] = "   dd         dd   "
    g[9] = "     dd     dd     "
    return g


def _hurt(face):
    """eyes screwed shut behind the lenses, mouth blown open"""
    g = list(face)
    g[11] = "   GKKKG G GKKKG   "
    g[17] = "      KKKKKKK      "
    g[18] = "      KoooooK      "
    g[19] = "       KKKKK       "
    return g


def _out(face):
    """lights out: eyes closed, jaw slack"""
    g = list(face)
    g[11] = "   GKKKG G GKKKG   "
    g[17] = "       KKKKK       "
    g[18] = "       KoooK       "
    return g


def _faces():
    return {"base": FACE, "scowl": _scowl(FACE), "hurt": _hurt(FACE),
            "out": _out(FACE)}


def check_faces():
    bad = []
    for name, rows in _faces().items():
        for j, row in enumerate(rows):
            if len(row) != 19:
                bad.append("%s row %d len %d" % (name, j, len(row)))
                continue
            for i in range(9):
                if _CLASS.get(row[i]) != _CLASS.get(row[18 - i]):
                    bad.append("%s row %d col %d/%d" % (name, j, i, 18 - i))
    return bad


# ---------------------------------------------------------------------------
def _mir(p):
    return (2 * AX - p[0], p[1])


def _arm(delt, u1, bice, f1, fist, ur=(7.6, 5.8), fr=(5.8, 4.8)):
    """an arm from its five landmarks; the upper arm starts at the delt"""
    return {"delt": delt,
            "uarm": ((delt[0], delt[1]), u1, ur[0], ur[1]),
            "bice": bice,
            "farm": (u1, f1, fr[0], fr[1]),
            "fist": fist}


def _mirror_arm(a):
    return {"delt": (2 * AX - a["delt"][0], a["delt"][1], a["delt"][2], a["delt"][3]),
            "uarm": (_mir(a["uarm"][0]), _mir(a["uarm"][1]), a["uarm"][2], a["uarm"][3]),
            "bice": (2 * AX - a["bice"][0], a["bice"][1], a["bice"][2], a["bice"][3]),
            "farm": (_mir(a["farm"][0]), _mir(a["farm"][1]), a["farm"][2], a["farm"][3]),
            "fist": (2 * AX - a["fist"][0], a["fist"][1], a["fist"][2], a["fist"][3])}


def _leg(hip, knee, ankle, boot, tr=(9.2, 6.0), cr=(6.2, 4.6)):
    return {"thigh": (hip, knee, tr[0], tr[1]), "calf": (knee, ankle, cr[0], cr[1]),
            "boot": boot}


def _mirror_leg(l):
    return {"thigh": (_mir(l["thigh"][0]), _mir(l["thigh"][1]), l["thigh"][2], l["thigh"][3]),
            "calf": (_mir(l["calf"][0]), _mir(l["calf"][1]), l["calf"][2], l["calf"][3]),
            "boot": (2 * AX - l["boot"][2], l["boot"][1], 2 * AX - l["boot"][0], l["boot"][3])}


def _lerp(a, b, t):
    """blend two rig values of the same shape"""
    if isinstance(a, (int, float)):
        return a + (b - a) * t
    if isinstance(a, dict):
        return {k: _lerp(a[k], b[k], t) for k in a}
    return type(a)(_lerp(x, y, t) for x, y in zip(a, b))


# ---------------------------------------------------------------------------
# the approved lat spread: arms out and down, elbow soft, fist held away
HERO_ARM = _arm((27.0, 34.0, 8.2, 7.6), (18.5, 48.0), (23.0, 40.0, 6.8, 6.2),
                (13.5, 61.0), (12.0, 66.0, 5.0, 4.6))
HERO_LEG = _leg((41.0, 58.0), (39.5, 77.0), (38.5, 87.0), (31.0, 84.0, 45.0, 95.0))

# chambered at the ribs, elbow flung back - the rear arm of every punch frame
CHAMBER_L = _arm((26.5, 34.5, 8.2, 7.7), (17.0, 45.0), (21.5, 39.0, 6.8, 6.2),
                 (24.0, 50.5), (27.0, 52.5, 5.4, 5.0), ur=(7.7, 6.0), fr=(6.0, 5.2))


def _base():
    return {
        "head": (AX, 13.5, 8.5, 11.0),
        "neck": ((AX, 23.0), (AX, 29.0), 4.2, 5.2),
        "trap": ((43.0, 26.0), (37.0, 33.0), 2.8, 5.5),
        "armL": HERO_ARM, "armR": _mirror_arm(HERO_ARM),
        "legL": HERO_LEG, "legR": _mirror_leg(HERO_LEG),
        "lean": 0.0, "body_dy": 0.0, "chest_ry": 0.0, "bulk": 1.0,
        "head_dx": 0.0, "head_dy": 0.0,
        "trunk_y": (54.0, 65.0), "fore": None, "chamber": (),
        "face": "base", "rage": False, "antenna": False,
    }


def _breathe(r, d):
    """lift the shoulders and swell the chest by d px; the hands stay put"""
    hx, hy, hrx, hry = r["head"]
    r["head"] = (hx, hy - d, hrx, hry)
    r["head_dy"] -= d
    n0, n1, a, b = r["neck"]
    r["neck"] = ((n0[0], n0[1] - d), (n1[0], n1[1] - d * 0.5), a, b)
    t0, t1, a, b = r["trap"]
    r["trap"] = ((t0[0], t0[1] - d), (t1[0], t1[1] - d * 0.6), a, b)
    r["chest_ry"] += d * 0.45
    for k in ("armL", "armR"):
        a = dict(r[k])
        dl = a["delt"]
        a["delt"] = (dl[0], dl[1] - d * 0.8, dl[2], dl[3])
        u = a["uarm"]
        a["uarm"] = ((u[0][0], u[0][1] - d * 0.8), (u[1][0], u[1][1] - d * 0.4), u[2], u[3])
        bc = a["bice"]
        a["bice"] = (bc[0], bc[1] - d * 0.6, bc[2], bc[3])
        f = a["farm"]
        a["farm"] = ((f[0][0], f[0][1] - d * 0.4), f[1], f[2], f[3])
        r[k] = a
    return r


def _sink(r, d, fwd=0.0):
    """drop everything above the hips by d px; fwd drops the head further"""
    hx, hy, hrx, hry = r["head"]
    r["head"] = (hx, hy + d + fwd, hrx, hry)
    r["head_dy"] += d + fwd
    n0, n1, a, b = r["neck"]
    r["neck"] = ((n0[0], n0[1] + d + fwd * 0.5), (n1[0], n1[1] + d), a, b)
    t0, t1, a, b = r["trap"]
    r["trap"] = ((t0[0], t0[1] + d), (t1[0], t1[1] + d), a, b)
    r["body_dy"] += d
    r["trunk_y"] = (r["trunk_y"][0] + d, r["trunk_y"][1] + d)
    return r


# ---------------------------------------------------------------------------
def _rig(pose):
    r = _base()

    # ---- idle: breathe --------------------------------------------------
    if pose == "hero":
        return r
    if pose.startswith("idle"):
        return _breathe(r, (0.0, 0.7, 1.4, 0.7)[int(pose[-1])])

    # ---- the combo ------------------------------------------------------
    if pose in ("windup", "combo_r", "combo_l", "combo_rlow", "snapback"):
        r["face"] = "scowl"
        r["legL"] = _leg((41.0, 58.0), (36.0, 77.0), (34.5, 87.0), (27.0, 84.0, 41.0, 95.0))
        r["legR"] = _leg((53.0, 58.0), (58.5, 77.0), (60.0, 87.0), (53.0, 84.0, 67.0, 95.0),
                         tr=(9.0, 5.8), cr=(6.0, 4.4))

    if pose == "windup":
        # the approved wind-up: rear fist chambered, lead fist up at the camera
        r["head"] = (AX + 2, 15.0, 8.5, 11.0)
        r["head_dx"], r["head_dy"] = 2.0, 1.5
        r["neck"] = ((AX + 2, 24.5), (AX + 1.5, 30.0), 4.3, 5.3)
        r["trap"] = ((44.0, 27.5), (37.5, 34.0), 2.8, 5.7)
        r["lean"] = 2.0
        r["armL"] = CHAMBER_L
        r["armR"] = _arm((67.5, 35.0, 8.0, 7.5), (64.0, 40.0), (67.0, 37.0, 5.2, 4.8),
                         (58.5, 42.0), (53.0, 43.0, 9.6, 9.2), ur=(7.6, 7.4), fr=(7.8, 8.4))
        r["fore"], r["chamber"] = "armR", ("armL",)

    if pose == "combo_r":
        # hit 1 and 5: the right fist snaps all the way out - bigger, nearer
        r["head"] = (AX + 3, 15.5, 8.5, 11.0)
        r["head_dx"], r["head_dy"] = 3.0, 2.0
        r["neck"] = ((AX + 3, 25.0), (AX + 2, 30.5), 4.3, 5.3)
        r["trap"] = ((45.0, 28.0), (38.0, 34.5), 2.8, 5.7)
        r["lean"] = 3.0
        r["armL"] = _arm((26.0, 35.0, 8.2, 7.7), (16.0, 45.0), (21.0, 39.5, 6.8, 6.2),
                         (23.5, 50.5), (26.5, 52.5, 5.4, 5.0), ur=(7.7, 6.0), fr=(6.0, 5.2))
        r["armR"] = _arm((68.5, 35.5, 8.2, 7.7), (64.5, 40.5), (68.0, 37.5, 5.2, 4.8),
                         (58.5, 42.5), (53.0, 43.0, 11.2, 10.6), ur=(7.8, 7.6), fr=(8.2, 9.0))
        r["fore"], r["chamber"] = "armR", ("armL",)

    if pose == "combo_l":
        # hits 2 and 4: the left fist out, the right drawn back
        r["head"] = (AX - 2.5, 15.5, 8.5, 11.0)
        r["head_dx"], r["head_dy"] = -2.5, 2.0
        r["neck"] = ((AX - 2.5, 25.0), (AX - 1.5, 30.5), 4.3, 5.3)
        r["trap"] = ((42.0, 28.0), (35.5, 34.5), 2.8, 5.7)
        r["lean"] = -2.5
        r["armL"] = _arm((25.5, 35.5, 8.2, 7.7), (29.5, 40.5), (26.0, 37.5, 5.2, 4.8),
                         (36.0, 44.5), (44.0, 46.0, 11.0, 10.4), ur=(7.8, 7.6), fr=(8.2, 9.0))
        r["armR"] = _arm((68.0, 35.0, 8.2, 7.7), (78.0, 45.0), (73.0, 39.5, 6.8, 6.2),
                         (70.5, 50.5), (67.5, 52.5, 5.4, 5.0), ur=(7.7, 6.0), fr=(6.0, 5.2))
        r["fore"], r["chamber"] = "armL", ("armR",)
        r["legL"] = _leg((41.0, 58.0), (35.5, 77.0), (34.0, 87.0), (26.5, 84.0, 40.5, 95.0))
        r["legR"] = _leg((53.0, 58.0), (58.0, 77.0), (59.5, 87.0), (52.5, 84.0, 66.5, 95.0),
                         tr=(9.0, 5.8), cr=(6.0, 4.4))

    if pose == "combo_rlow":
        # hit 3: the right fist again, dug in low with the knees bent
        r["head"] = (AX + 2.5, 17.5, 8.5, 11.0)
        r["head_dx"], r["head_dy"] = 2.5, 4.0
        r["neck"] = ((AX + 2.5, 27.0), (AX + 2, 32.0), 4.3, 5.3)
        r["trap"] = ((44.5, 30.0), (38.0, 36.0), 2.8, 5.7)
        r["lean"] = 2.5
        r["body_dy"] = 2.0
        r["trunk_y"] = (56.0, 67.0)
        r["armL"] = _arm((26.0, 37.0, 8.2, 7.7), (16.5, 47.0), (21.0, 41.5, 6.8, 6.2),
                         (24.0, 52.0), (27.0, 54.0, 5.4, 5.0), ur=(7.7, 6.0), fr=(6.0, 5.2))
        r["armR"] = _arm((68.0, 37.5, 8.2, 7.7), (64.0, 44.0), (67.5, 40.0, 5.2, 4.8),
                         (57.5, 47.5), (50.0, 49.0, 10.8, 10.2), ur=(7.8, 7.6), fr=(8.2, 8.8))
        r["fore"], r["chamber"] = "armR", ("armL",)
        r["legL"] = _leg((41.0, 60.0), (35.0, 78.0), (33.5, 87.0), (26.0, 84.0, 40.0, 95.0))
        r["legR"] = _leg((53.0, 60.0), (59.5, 78.0), (61.0, 87.0), (54.0, 84.0, 68.0, 95.0),
                         tr=(9.0, 5.8), cr=(6.0, 4.4))

    if pose == "snapback":
        # both fists back to the ribs, standing up out of the flurry
        r["head"] = (AX + 1, 14.0, 8.5, 11.0)
        r["head_dx"], r["head_dy"] = 1.0, 0.5
        r["neck"] = ((AX + 1, 23.5), (AX + 0.5, 29.5), 4.2, 5.2)
        r["lean"] = 1.0
        guard = _arm((26.5, 34.5, 8.2, 7.7), (17.0, 45.0), (21.5, 39.0, 6.8, 6.2),
                     (25.0, 49.5), (28.0, 51.5, 5.4, 5.0), ur=(7.7, 6.0), fr=(6.0, 5.2))
        r["armL"], r["armR"] = guard, _mirror_arm(guard)
        r["chamber"] = ("armL", "armR")
        r["legL"] = _leg((41.0, 58.0), (37.5, 77.0), (36.5, 87.0), (29.0, 84.0, 43.0, 95.0))
        r["legR"] = _mirror_leg(r["legL"])

    # ---- hit: flinch, recoil, hunch --------------------------------------
    if pose.startswith("hit"):
        return _hit(int(pose[-1]))

    # ---- defeat: stagger, knees, down -------------------------------------
    if pose.startswith("defeat"):
        return _defeat(int(pose[-1]))

    # ---- phase 2: he grows ------------------------------------------------
    if pose.startswith("p2_idle") or pose == "phase2":
        k = 0 if pose == "phase2" else int(pose[-1])
        return _breathe(_phase2(), (0.0, 1.0, 2.0, 1.0)[k])

    return r


# the flinch (0) and the hunch (2); frame 1 is drawn between them.  Frame 2 is
# also the pose the fight holds as "brink", so it is a real doubled-over hunch
# rather than a return to the idle.
_HIT_FLINCH = {
    "head": (AX - 3.0, 12.5, 8.5, 11.0), "head_dx": -3.0, "head_dy": -1.0,
    "neck": ((AX - 3.0, 22.0), (AX - 1.5, 28.5), 4.2, 5.2),
    "trap": ((40.0, 25.0), (34.0, 32.0), 2.8, 5.5),
    "lean": -3.0, "sink": 1.0,
    "armL": _arm((25.0, 32.0, 8.2, 7.6), (14.0, 38.0), (20.0, 34.5, 6.8, 6.2),
                 (9.5, 31.0), (9.0, 26.5, 5.0, 4.6)),
    "legL": _leg((41.0, 58.0), (38.0, 77.0), (37.0, 87.0), (29.5, 84.0, 43.5, 95.0)),
}
_HIT_HUNCH = {
    "head": (AX, 21.0, 8.5, 11.0), "head_dx": 0.0, "head_dy": 7.5,
    "neck": ((AX, 29.5), (AX, 33.0), 4.2, 5.2),
    "trap": ((43.0, 31.0), (36.0, 37.0), 2.8, 5.8),
    "lean": 0.0, "sink": 5.0,
    "armL": _arm((28.0, 39.0, 8.2, 7.6), (28.5, 54.0), (27.5, 45.5, 6.8, 6.2),
                 (33.5, 67.0), (36.0, 72.5, 5.0, 4.6)),
    "legL": _leg((41.0, 63.0), (37.5, 78.0), (37.5, 87.0), (29.5, 84.0, 43.5, 95.0)),
}


def _hit(k):
    r = _base()
    src = _lerp(_HIT_FLINCH, _HIT_HUNCH, (0.0, 0.5, 1.0)[k])
    for key in ("head", "head_dx", "head_dy", "neck", "trap", "lean"):
        r[key] = src[key]
    r["armL"] = src["armL"]
    r["armR"] = _mirror_arm(src["armL"])
    r["legL"] = src["legL"]
    r["legR"] = _mirror_leg(src["legL"])
    r["face"] = "hurt"
    s = src["sink"]
    r["body_dy"] = s
    r["trunk_y"] = (54.0 + s, 65.0 + s)
    r["chest_ry"] = (0.0, -1.2, -2.5)[k]   # bent forward, the chest foreshortens
    return r


_DEFEAT = [
    # sink, head drop, arm, leg
    (4.0, 0.0,
     _arm((26.0, 36.0, 8.2, 7.6), (16.5, 49.0), (22.0, 42.0, 6.8, 6.2),
          (12.5, 62.0), (11.5, 67.0, 5.0, 4.6)),
     _leg((41.0, 62.0), (36.5, 78.0), (35.5, 88.0), (27.5, 85.0, 41.5, 95.0))),
    (11.0, 2.0,
     _arm((27.0, 43.0, 8.2, 7.6), (19.0, 56.0), (23.5, 49.0, 6.8, 6.2),
          (15.5, 69.0), (14.5, 74.0, 5.0, 4.6)),
     _leg((41.0, 69.0), (34.5, 86.0), (32.0, 92.0), (24.0, 88.0, 38.0, 95.0),
          tr=(9.2, 6.2), cr=(5.8, 4.4))),
    (18.0, 4.0,
     _arm((27.5, 50.0, 8.2, 7.6), (20.5, 63.0), (24.5, 56.0, 6.8, 6.2),
          (17.5, 76.0), (16.5, 81.0, 5.0, 4.6)),
     _leg((41.0, 76.0), (35.0, 92.0), (30.0, 94.0), (21.0, 90.0, 35.0, 95.0),
          tr=(9.2, 6.6), cr=(5.2, 4.2))),
    (22.0, 7.0,
     _arm((28.5, 54.0, 8.0, 7.4), (22.0, 67.0), (25.5, 60.0, 6.6, 6.0),
          (19.5, 80.0), (18.5, 86.0, 5.0, 4.6)),
     _leg((41.5, 80.0), (35.5, 93.0), (29.5, 94.5), (19.5, 91.0, 33.5, 95.0),
          tr=(9.2, 6.8), cr=(5.0, 4.0))),
    (23.0, 8.0,
     _arm((28.5, 55.0, 8.0, 7.4), (22.0, 68.0), (25.5, 61.0, 6.6, 6.0),
          (19.5, 81.0), (18.5, 87.0, 5.0, 4.6)),
     _leg((41.5, 81.0), (35.5, 93.5), (29.5, 94.5), (19.5, 91.5, 33.5, 95.0),
          tr=(9.2, 6.8), cr=(5.0, 4.0))),
]


def _defeat(k):
    sink, drop, arm, leg = _DEFEAT[k]
    r = _base()
    r["face"] = "hurt" if k == 0 else "out"
    r["lean"] = (-1.5, -0.5, 0.0, 0.5, 0.5)[k]
    r["armL"], r["armR"] = arm, _mirror_arm(arm)
    r["legL"], r["legR"] = leg, _mirror_leg(leg)
    return _sink(r, sink, drop)


def _phase2():
    """Greyson after Computah dies.  The frame is 96 tall and he already fills
    it crown to boot, and the fight does not rescale the sprite - so he grows
    the only way the contract allows: wider, heavier, higher in the traps."""
    r = _base()
    r["rage"] = True
    r["antenna"] = True
    r["face"] = "scowl"
    r["bulk"] = 1.13
    r["head"] = (AX, 14.5, 8.5, 11.0)
    r["head_dy"] = 1.0
    r["neck"] = ((AX, 24.0), (AX, 30.0), 4.6, 5.8)
    r["trap"] = ((43.0, 26.5), (35.0, 34.0), 3.2, 6.8)
    arm = _arm((24.5, 34.0, 9.6, 8.8), (15.0, 48.0), (20.0, 40.0, 7.8, 7.0),
               (9.5, 61.0), (8.5, 66.0, 5.6, 5.2), ur=(8.8, 6.6), fr=(6.6, 5.4))
    r["armL"], r["armR"] = arm, _mirror_arm(arm)
    leg = _leg((40.5, 58.0), (37.5, 77.0), (36.0, 87.0), (28.0, 84.0, 43.0, 95.0),
               tr=(9.8, 6.4), cr=(6.6, 4.8))
    r["legL"], r["legR"] = leg, _mirror_leg(leg)
    return r


# ---------------------------------------------------------------------------
def _fist_shape(fist, kind):
    """A fist is a squared-off block, never a ball.

      front  thrust at the camera: wider than tall, knuckle row on top
      side   chambered at the ribs, seen thumb-side
      hang   at the end of a loose arm, fingers curled under
    """
    fx, fy, frx, fry = [float(v) for v in fist]
    if kind == "front":
        w, h, rr = frx * 1.08, fry * 0.78, 3.5
    elif kind == "side":
        w, h, rr = frx * 1.18, fry * 0.84, 2.6
    else:
        w, h, rr = frx * 0.92, fry * 1.04, 2.4
    return RoundRect(fx - w, fy - h, fx + w, fy + h, r=rr, round_r=4.0)


def _fist_kind(r, key):
    if key == r["fore"]:
        return "front"
    if key in r["chamber"]:
        return "side"
    return "hang"


# every layer below this is the torso (body 1, neck 2, pecs 3); arms start at 8
TORSO_TOP = 4


def _mass(c, shape, mat, prio, wrap=0.56, amb=0.10):
    c.add(shape, mat, prio=prio, wrap=wrap, amb=amb)


def build(pose="hero"):
    r = _rig(pose)
    skin = "rage" if r["rage"] else "skin"
    c = Canvas(W, H, PAL, OUTLINE)
    L, B, K = r["lean"], r["body_dy"], r["bulk"]
    hx, hy, hrx, hry = r["head"]
    ty0, ty1 = r["trunk_y"]
    ch = r["chest_ry"]

    # ---- torso: broad chest, hard taper to a narrow waist ---------------
    chest = Ellipse(AX + L * .7, 36 + B, 16.5 * K, 7.5 + ch)
    latL = Ellipse(AX - 11 * K + L * .7, 42 + B, 8.5 * K, 8.0)
    latR = Ellipse(AX + 11 * K + L * .7, 42 + B, 8.5 * K, 8.0)
    ribs = Ellipse(AX + L, 47 + B, 9.5 * K, 6.5)
    waist = Ellipse(AX + L, 53 + B, 6.5 * K, 5.5)
    hips = Ellipse(AX + L, 59 + B, 9.0 * K, 6.5)
    _mass(c, Union([chest, latL, latR, ribs, waist, hips], k=1.8), skin, 1)

    tp = r["trap"]
    neck = Union([Capsule(tp[0], tp[1], tp[2], tp[3]),
                  Capsule(_mir(tp[0]), _mir(tp[1]), tp[2], tp[3]),
                  Capsule(r["neck"][0], r["neck"][1], r["neck"][2], r["neck"][3])],
                 k=2.0)
    _mass(c, neck, skin, 2)

    # the chest's one bit of definition: two pec volumes
    for sx in (-1, 1):
        _mass(c, Ellipse(AX + sx * 6.5 * K + L * .7, 35.5 + B, 7.5 * K, max(3.0, 4.6 + ch)),
              skin, 3, wrap=0.62, amb=0.08)

    # ---- legs -----------------------------------------------------------
    legs = []
    for key in ("legL", "legR"):
        g = r[key]
        leg = Union([Capsule(g["thigh"][0], g["thigh"][1], g["thigh"][2], g["thigh"][3]),
                     Capsule(g["calf"][0], g["calf"][1], g["calf"][2], g["calf"][3])],
                    k=1.6)
        _mass(c, leg, skin, 4)
        legs.append(leg)

    # ---- trunks: one clean hem (ripped shorts are Danny's) --------------
    tx = AX - 14 * K + L
    trunk_poly = Poly([(tx, ty0 - 1), (2 * AX - tx, ty0 - 1),
                       (2 * AX - tx + 1, ty1), (tx - 1, ty1)], round_r=5)
    trunks = Clip(Union([hips] + legs, k=2.0), trunk_poly)
    _mass(c, trunks, "trunk", 5)

    for key in ("legL", "legR"):
        b = r[key]["boot"]
        _mass(c, RoundRect(b[0], b[1], b[2], b[3], r=3.0, round_r=5.0), "boot", 6)

    # ---- arms -----------------------------------------------------------
    order = ["armL", "armR"]
    if r["fore"]:
        order = [k for k in order if k != r["fore"]] + [r["fore"]]
    inked = []
    for i, key in enumerate(order):
        a = r[key]
        prio = 8 + i * 4
        upper = Union([Ellipse(*a["delt"]),
                       Capsule(a["uarm"][0], a["uarm"][1], a["uarm"][2], a["uarm"][3]),
                       Ellipse(*a["bice"])], k=2.2)
        _mass(c, upper, skin, prio)
        inked.append((upper, prio))
        kind = _fist_kind(r, key)
        if kind in ("front", "side"):
            fore = Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3])
            fist = _fist_shape(a["fist"], kind)
            _mass(c, fore, skin, prio + 1)
            _mass(c, fist, skin, prio + 2)
            inked += [(fore, prio + 1), (fist, prio + 2)]
        else:
            lower = Union([Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3]),
                           _fist_shape(a["fist"], "hang")], k=1.8)
            _mass(c, lower, skin, prio + 1)
            inked.append((lower, prio + 1))

    # ---- head + mane ----------------------------------------------------
    head = Union([Ellipse(hx, hy, hrx, hry),
                  Ellipse(hx, hy + 3.0, hrx - 1.4, hry - 2.4)], k=1.8)
    _mass(c, head, skin, 18, wrap=0.50, amb=0.16)
    crown, falls = _hair(hx, hy, hrx, hry)
    _mass(c, falls, "hair", 7, wrap=0.60, amb=0.10)
    _mass(c, crown, "hair", 20, wrap=0.60, amb=0.10)

    for shp, prio in inked:
        c.contour(shp, 1.3, color=OUTLINE, below_prio=prio)
    c.contour(head, 1.3, color=OUTLINE, below_prio=18)
    c.contour(trunks, 1.2, color=OUTLINE, below_prio=5)

    c.occlude(strength=2, reach=1)
    c.rim(1, mats=(skin, "hair", "trunk", "boot"))
    c.despeckle()
    _details(c, r, skin)
    if r["antenna"]:
        _antenna(c, r)
    face = _faces()[r["face"]]
    c.stamp(face, int(round(FACE_X + r["head_dx"])), int(round(FACE_Y + r["head_dy"])),
            RAGE_CH if r["rage"] else FACE_CH)
    if r["rage"]:
        tx0 = int(round(FACE_X + r["head_dx"])) + 4
        ty0f = int(round(FACE_Y + r["head_dy"])) + 13
        c.raw_px([(tx0, ty0f), (tx0, ty0f + 1)], "#9FE0FF")     # the one tear
    return c


def _hair(hx, hy, hrx, hry):
    face = Ellipse(hx, hy + 4.0, hrx - 1.8, hry - 2.0)
    frL = Poly([(hx - 11, hy - 8), (hx - 2.6, hy - 5.5), (hx - 4.0, hy - 0.5),
                (hx - 12, hy - 2.0)], round_r=2)
    frR = Poly([(hx + 11, hy - 8), (hx + 2.6, hy - 5.5), (hx + 4.0, hy - 0.5),
                (hx + 12, hy - 2.0)], round_r=2)
    hole = Sub(Sub(face, frL), frR)
    mass = Ellipse(hx, hy + 1.0, hrx + 2.0, hry + 3.2)
    fallL = Capsule((hx - hrx - 0.5, hy + 2), (hx - hrx - 2.0, hy + 20), 4.2, 3.4)
    fallR = Capsule((hx + hrx + 0.5, hy + 2), (hx + hrx + 2.0, hy + 20), 4.2, 3.4)
    return Sub(mass, hole), Union([fallL, fallR], k=1.0)


def _details(c, r, skin):
    """Simple but definite: a sternum line, the under-pec, an ab groove with
    two ticks, a waistband, soles, the fists and the forearm veins."""
    L, B, K = r["lean"], r["body_dy"], r["bulk"]
    ty0 = int(round(r["trunk_y"][0]))

    def P(pts):
        # Shift the ENDPOINTS, snap them, THEN rasterise.  Shifting an already
        # rasterised line by a half pixel and rounding each pixel collapses
        # neighbours onto one another (round-half-to-even) and leaves a dotted
        # line on every pose that leans or sinks by .5.
        snapped = [(int(math.floor(a + L + 0.5)), int(math.floor(b + B + 0.5)))
                   for a, b in pts]
        return polyline(snapped)

    torso = dict(below_prio=TORSO_TOP)
    c.shade_px(P([(AX, 33), (AX, 40)]), 2, skin, **torso)
    c.shade_px(P([(AX - 7 * K, 40), (AX - 2, 41)]), 2, skin, **torso)
    c.shade_px(P([(AX + 7 * K, 40), (AX + 2, 41)]), 2, skin, **torso)
    c.shade_px(P([(AX, 43), (AX, 52)]), 2, skin, **torso)
    for yy in (45, 49):
        c.shade_px(P([(AX - 4, yy), (AX + 4, yy)]), 2, skin, **torso)

    c.ink_px([(x, ty0 + 1) for x in range(20, 76)], OUTLINE, mats=("trunk",))

    for key in ("armL", "armR"):
        a = r[key]
        (ex, ey), (fx2, fy2) = a["farm"][0], a["farm"][1]
        c.shade_px(polyline([(ex + (fx2 - ex) * .3, ey + (fy2 - ey) * .3),
                             (ex + (fx2 - ex) * .8 - 1, ey + (fy2 - ey) * .8)]), 1, skin)
        _fist_marks(c, a["fist"], _fist_kind(r, key),
                    -1.0 if a["delt"][0] < AX else 1.0, skin)

    for key in ("legL", "legR"):
        b = r[key]["boot"]
        x0, x1, y1 = int(b[0]), int(b[2]), int(b[3])
        c.raw_px([(x, y1 - 2) for x in range(x0, x1 + 1)], OUTLINE)
        c.raw_px([(x, int(b[1]) + 2) for x in range(x0 + 1, x1)], OUTLINE)


def _fist_marks(c, fist, kind, sgn, skin):
    """Every mark on a fist runs out to the fist's own edge.  A mark that
    floats in the middle of a round skin shape is an eye."""
    fx, fy, frx, fry = [float(v) for v in fist]
    if kind == "front":
        w, h = frx * 1.08, fry * 0.78
        x0, x1 = int(round(fx - w)), int(round(fx + w))
        y0, y1 = int(round(fy - h)), int(round(fy + h))
        crease = int(round(y0 + (y1 - y0) * 0.58))
        for k in (1, 2, 3):
            gx = int(round(x0 + (x1 - x0) * k / 4.0))
            c.raw_px([(gx, y) for y in range(y0, crease)], OUTLINE)
        for k in range(4):
            kx = int(round(x0 + (x1 - x0) * (k + 0.5) / 4.0))
            c.shade_px([(kx, y0 + 1), (kx - 1, y0 + 1)], -2, skin)
        c.raw_px([(x, crease) for x in range(x0, x1 + 1)], OUTLINE)
        c.shade_px([(x, y) for x in range(x0 + 2, int(fx) + 3)
                    for y in range(crease + 1, crease + 3)], -1, skin)
    elif kind == "side":
        w, h = frx * 1.18, fry * 0.84
        x0, x1 = int(round(fx - w)), int(round(fx + w))
        y0, y1 = int(round(fy - h)), int(round(fy + h))
        front = x1 - 3 if sgn < 0 else x0 + 3
        c.raw_px([(front, y) for y in range(y0, y1 + 1)], OUTLINE)
        span = range(min(front, int(fx)), max(front, int(fx)) + 1)
        c.raw_px([(x, y0 + 2) for x in span], OUTLINE)
        c.shade_px([(x, y0 + 1) for x in span], -2, skin)
    else:
        w, h = frx * 0.92, fry * 1.04
        x0, x1 = int(round(fx - w)), int(round(fx + w))
        y1 = int(round(fy + h))
        for k in (1, 2, 3):
            gx = int(round(x0 + (x1 - x0) * k / 4.0))
            c.raw_px([(gx, y1), (gx, y1 - 1), (gx, y1 - 2)], OUTLINE)
        ex = x1 if sgn < 0 else x0
        step = -1 if sgn < 0 else 1
        c.raw_px([(ex, int(fy) - 1), (ex + step, int(fy)), (ex + 2 * step, int(fy))],
                 OUTLINE)


def _antenna(c, r):
    """Computah's snapped antenna, gripped in his screen-left fist"""
    fx, fy = r["armL"]["fist"][0], r["armL"]["fist"][1]
    rod = polyline([(fx + 1.5, fy + 4.0), (fx + 3.5, fy + 13.0), (fx + 4.5, fy + 21.0)])
    for (x, y) in rod:
        c.set_px([(x, y)], "steel", 2)
        c.set_px([(x + 1, y)], "steel", 4)
    bx, by = int(round(fx + 4.5)), int(round(fy + 23.0))
    c.raw_px([(bx, by), (bx + 1, by), (bx, by + 1), (bx + 1, by + 1)], "#C0392B")
    c.raw_px([(bx, by)], "#FF8A7A")


# ---------------------------------------------------------------------------
SHEETS = {
    "greyson_idle":        ["idle0", "idle1", "idle2", "idle3"],
    "greyson_combo":       ["windup", "combo_r", "combo_l", "combo_rlow", "snapback"],
    "greyson_hit":         ["hit0", "hit1", "hit2"],
    "greyson_defeat":      ["defeat0", "defeat1", "defeat2", "defeat3", "defeat4"],
    "greyson_phase2_idle": ["p2_idle0", "p2_idle1", "p2_idle2", "p2_idle3"],
}

# The punching fist's centre on each combo sheet frame, in texels.  These are
# read off the rig, never typed twice: fist_point() is the source of truth and
# the fight's COMBO_FIST_POINTS must match it.
COMBO_FRAMES = {1: "combo_r", 2: "combo_l", 3: "combo_rlow"}


def fist_point(pose):
    r = _rig(pose)
    f = r[r["fore"]]["fist"]
    return (int(round(f[0])), int(round(f[1])))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    bad = check_faces()
    if bad:
        print("faces not symmetric:" + "".join(chr(10) + "  " + x for x in bad))
        sys.exit(1)
    from PIL import Image
    for name in ("hero", "windup", "phase2"):
        build(name).to_image().save(os.path.join(out, "greyson_%s.png" % name))
    for sheet, poses in SHEETS.items():
        ims = [build(p).to_image() for p in poses]
        strip = Image.new("RGBA", (W * len(ims), H), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.paste(im, (i * W, 0))
        strip.save(os.path.join(out, "%s.png" % sheet))
        print("%-22s %d frames  %dx%d" % (sheet, len(ims), strip.width, strip.height))
    for frame, pose in sorted(COMBO_FRAMES.items()):
        print("combo frame %d (%s) fist = %s" % (frame, pose, fist_point(pose)))
    print("ok")
