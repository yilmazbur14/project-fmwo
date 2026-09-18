"""Computah redesign - 64x64 frames, baseline row 63, meant for scale 3.

Kept from the old sprite: the bent antenna with a ball tip, the boxy head, the
red LED eyes, the wide toothy grin, the stubby segmented limbs, the cool grey
chassis.

Added: the BATTERY, because it is a fight mechanic.  Charge is readable three
ways at once - how many of the four chest cells are lit, what colour they are
(green -> amber -> red -> dead), and how bright the antenna ball and the eyes
glow.  Purple trim matches Greyson's trunks so the two read as one boss.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import (Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip,
                    polyline)

W = H = 64
AX = 31.5              # mirror axis: x' = 63 - x
OUTLINE = "#0C111A"

PAL = {
    "shell":  ["#F2F8FF", "#CEDCEA", "#A6B8CC", "#8091A8", "#5E6C82", "#3F4A5C"],
    "dark":   ["#6C7A8E", "#536174", "#3C4757", "#2A3341", "#1A212C"],
    "purple": ["#C892F2", "#A063DC", "#7C3BB4", "#592687", "#391555"],
    "glass":  ["#2B3444", "#222A38", "#1A202B", "#131821", "#0D1118"],
}

CHARGE = {
    #        lit cells, bright,      mid,       dark,      glow,      eye
    "full": (4, "#A9FFB4", "#4FE066", "#1F9A38", "#2A7A3C", "#FF4436"),
    "half": (2, "#FFE9A8", "#FFC33E", "#C9820F", "#7A5A18", "#E0392C"),
    "low":  (1, "#FFC0A6", "#FF6A4E", "#C32A1C", "#7A2418", "#C42C22"),
    "dead": (0, "#6E7A8C", "#4A5668", "#333D4C", "#232A36", "#5A2420"),
}

# --- face plate: 20 wide (x22..41), 13 tall (y19..31) ----------------------
VIS_W = 20
VISOR = [
    "vvvvvvvvvvvvvvvvvvvv",   # y19
    "VVVVVVVVVVVVVVVVVVVV",   # y20
    "VVVGGGGVVVVVVGGGGVVV",   # y21  eye bloom
    "VVVGRRGVVVVVVGRRGVVV",   # y22
    "VVVGRRGVVVVVVGRRGVVV",   # y23
    "VVVGRRGVVVVVVGRRGVVV",   # y24
    "VVVGGGGVVVVVVGGGGVVV",   # y25
    "VVVVVVVVVVVVVVVVVVVV",   # y26
    "VVMVVVVVVVVVVVVVVMVV",   # y27  grin corners hook up
    "VVMMMMMMMMMMMMMMMMVV",   # y28
    "VVMtMMtMMttMMtMMtMVV",   # y29  teeth
    "VVVMMMMMMMMMMMMMMVVV",   # y30
    "vvvvvvvvvvvvvvvvvvvv",   # y31
]
VIS_X, VIS_Y = 22, 19

_CLASS = {" ": "b", "v": "g", "V": "g", "G": "e", "R": "e", "M": "m", "t": "t"}


def _check():
    bad = []
    for j, row in enumerate(VISOR):
        if len(row) != VIS_W:
            bad.append("visor row %d len %d" % (j, len(row)))
            continue
        for i in range(VIS_W // 2):
            a, b = _CLASS.get(row[i]), _CLASS.get(row[VIS_W - 1 - i])
            if a != b:
                bad.append("visor row %d col %d/%d %r/%r"
                           % (j, i, VIS_W - 1 - i, row[i], row[VIS_W - 1 - i]))
    return bad


def _arm(up0, up1, lo1, hand, cap, r0=3.8, r1=3.2, r2=2.8):
    return {"up": (up0, up1, r0, r1), "lo": (up1, lo1, r1, r2),
            "hand": (hand[0], hand[1], 3.5, 3.1),
            "cap": (cap[0], cap[1], 5.0, 4.4)}


def _leg(p0, p1, foot):
    return {"leg": (p0, p1, 4.3, 3.4), "foot": foot}


def _bob(r, dy):
    """lift/drop everything above the hips; the feet stay on the ground"""
    if dy == 0:
        return r
    h = r["head"]
    r["head"] = (h[0], h[1] + dy, h[2], h[3] + 0)
    r["head"] = (h[0], h[1] + dy, h[2], h[3] + dy)
    r["ant"] = [(x, y + dy) for x, y in r["ant"]]
    b = r["ball"]
    r["ball"] = (b[0], b[1] + dy, b[2])
    n = r["neck"]
    r["neck"] = (n[0], n[1] + dy, n[2], n[3] + dy)
    r["torso"] = [(x, y + dy) for x, y in r["torso"][:2]] + r["torso"][2:]
    r["batt"] = (r["batt"][0], r["batt"][1] + dy * 0.6)
    for k in ("armL", "armR"):
        a = r[k]
        if a is None:
            continue
        r[k] = {"up": ((a["up"][0][0], a["up"][0][1] + dy),
                       (a["up"][1][0], a["up"][1][1] + dy * 0.7), a["up"][2], a["up"][3]),
                "lo": ((a["lo"][0][0], a["lo"][0][1] + dy * 0.7),
                       (a["lo"][1][0], a["lo"][1][1] + dy * 0.4), a["lo"][2], a["lo"][3]),
                "hand": (a["hand"][0], a["hand"][1] + dy * 0.3, a["hand"][2], a["hand"][3]),
                "cap": (a["cap"][0], a["cap"][1] + dy, a["cap"][2], a["cap"][3])}
    return r


def _mir(p):
    return (2 * AX - p[0], p[1])


# ---------------------------------------------------------------------------
def _rig(pose):
    if pose.startswith("idle"):
        k = int(pose[-1])
        r = _rig("hero")
        _bob(r, (0.0, -1.0, -2.0, -1.0)[k])
        if k == 2:
            r["eye_style"] = "blink"
        return r
    if pose.startswith("p2_idle"):
        k = int(pose[-1])
        r = _rig("phase2")
        _bob(r, (0.0, -1.0, -2.0, -1.0)[k])
        r["pulse"] = (0.0, 0.5, 1.0, 0.5)[k]
        return r
    if pose.startswith("run"):
        return _run(int(pose[-1]))
    if pose.startswith("drop"):
        return _drop(int(pose[-1]))
    if pose.startswith("hit"):
        return _hit(int(pose[-1]))
    if pose.startswith("die"):
        return _die(int(pose[-1]))
    r = {
        "head": (18.0, 19.0, 45.0, 40.0),
        "ant": [(30, 20), (32.5, 15.5), (36, 12.8)],
        "ball": (37.5, 11.6, 2.6),
        "neck": (28.0, 38.5, 35.0, 44.5),
        "torso": [(18.0, 43.5), (46.0, 43.5), (42.0, 56.0), (22.0, 56.0)],
        "batt": (31.5, 49.5),
        "batt_h": 5.0,
        "armL": {"up": ((16.0, 46.0), (12.5, 52.0), 3.8, 3.2),
                 "lo": ((12.5, 52.0), (11.2, 57.5), 3.2, 2.8),
                 "hand": (10.6, 59.8, 3.5, 3.1),
                 "cap": (16.4, 45.0, 5.0, 4.4)},
        "armR": None,
        "legL": {"leg": ((26.5, 54.5), (25.0, 59.5), 4.3, 3.4),
                 "foot": (19.0, 58.5, 29.5, 63.0)},
        "legR": None,
        "charge": "full",
        "tilt": 0,
        "smoke": False,
        "visor_dy": 0,
        "eye_style": "open",
        "pulse": 0.0,
        "spark": None,
        "streak": False,
    }

    if pose == "charge":
        r["streak"] = True
        # thrown forward mid-sprint, antenna whipped back, mitts reaching
        r["head"] = (20.0, 21.0, 47.0, 41.0)
        r["ant"] = [(31, 22), (26, 19), (20.5, 17)]
        r["ball"] = (18.6, 16.4, 2.6)
        r["neck"] = (29.0, 39.0, 36.0, 45.5)
        r["torso"] = [(19.0, 44.5), (46.0, 43.5), (42.0, 56.0), (21.0, 57.0)]
        r["batt"] = (32.5, 50.0)
        r["batt_h"] = 5.0
        r["charge"] = "half"
        r["visor_dy"] = 1
        r["eye_style"] = "angry"
        r["armL"] = {"up": ((17.0, 46.5), (9.5, 49.5), 3.8, 3.2),
                     "lo": ((9.5, 49.5), (7.0, 55.0), 3.2, 2.9),
                     "hand": (6.5, 57.5, 3.7, 3.3),
                     "cap": (17.2, 45.5, 5.0, 4.4)}
        r["armR"] = {"up": ((46.0, 45.5), (53.0, 49.5), 3.8, 3.2),
                     "lo": ((53.0, 49.5), (55.5, 55.5), 3.2, 2.9),
                     "hand": (56.0, 58.0, 3.7, 3.3),
                     "cap": (45.8, 44.5, 5.0, 4.4)}
        r["legL"] = {"leg": ((27.0, 54.5), (20.0, 59.5), 4.3, 3.4),
                     "foot": (13.5, 58.5, 24.0, 63.0)}
        r["legR"] = {"leg": ((38.0, 54.0), (43.5, 59.5), 4.3, 3.4),
                     "foot": (38.5, 58.5, 49.0, 63.0)}

    if pose == "dead":
        # battery flat: sat down where he stood, head lolled, limbs slack
        r["head"] = (20.0, 33.0, 44.0, 51.0)
        r["ant"] = [(28.5, 34.5), (22.5, 33.5), (17.5, 36.5)]
        r["ball"] = (16.0, 37.8, 2.6)
        r["neck"] = (29.0, 48.0, 35.0, 53.0)
        r["torso"] = [(21.0, 49.5), (42.0, 49.5), (46.0, 62.0), (17.0, 62.0)]
        r["batt"] = (31.5, 56.5)
        r["batt_h"] = 4.0
        r["charge"] = "dead"
        r["eye_style"] = "dead"
        r["visor_dy"] = 2
        r["smoke"] = True
        r["armL"] = {"up": ((21.0, 52.0), (13.5, 58.0), 3.4, 2.9),
                     "lo": ((13.5, 58.0), (9.5, 61.5), 2.9, 2.6),
                     "hand": (8.0, 62.4, 3.0, 2.5),
                     "cap": (21.5, 51.0, 4.2, 3.6)}
        r["legL"] = {"leg": ((27.0, 60.0), (21.0, 62.0), 3.8, 3.0),
                     "foot": (14.0, 61.0, 22.5, 63.0)}

    if pose == "phase2":
        # exploratory: Computah after Greyson dies - overclocked, core blown
        # open, no intention of ever stopping to recharge
        r["head"] = (18.0, 9.0, 45.0, 30.0)
        r["ant"] = [(31, 10), (31, 7.0), (31, 5.2)]
        r["ball"] = (31.5, 4.4, 3.0)
        r["neck"] = (28.0, 28.0, 35.0, 36.0)
        r["torso"] = [(17.5, 35.5), (46.5, 35.5), (43.5, 54.0), (20.5, 54.0)]
        r["batt"] = (31.5, 44.0)
        r["batt_h"] = 6.5
        r["charge"] = "over"
        r["eye_style"] = "over"
        r["armL"] = {"up": ((15.5, 38.0), (8.5, 46.0), 4.2, 3.5),
                     "lo": ((8.5, 46.0), (6.5, 56.0), 3.5, 2.9),
                     "hand": (5.8, 59.0, 3.8, 3.2),
                     "cap": (15.8, 37.0, 5.4, 4.8)}
        r["legL"] = {"leg": ((26.5, 52.0), (24.0, 59.0), 4.4, 3.5),
                     "foot": (18.0, 58.0, 29.5, 63.0)}

    for k, src in (("armR", "armL"), ("legR", "legL")):
        if r[k] is None:
            a = r[src]
            if src == "armL":
                r[k] = {"up": (_mir(a["up"][0]), _mir(a["up"][1]), a["up"][2], a["up"][3]),
                        "lo": (_mir(a["lo"][0]), _mir(a["lo"][1]), a["lo"][2], a["lo"][3]),
                        "hand": (2 * AX - a["hand"][0], a["hand"][1], a["hand"][2], a["hand"][3]),
                        "cap": (2 * AX - a["cap"][0], a["cap"][1], a["cap"][2], a["cap"][3])}
            else:
                r[k] = {"leg": (_mir(a["leg"][0]), _mir(a["leg"][1]), a["leg"][2], a["leg"][3]),
                        "foot": (2 * AX - a["foot"][2], a["foot"][1],
                                 2 * AX - a["foot"][0], a["foot"][3])}
    return r


# ---------------------------------------------------------------------------
_RUN_LEGS = [
    (_leg((27.0, 54.5), (19.0, 58.0), (12.0, 57.0, 23.0, 62.0)),
     _leg((38.0, 54.0), (45.0, 60.0), (40.0, 59.0, 51.0, 63.0))),
    (_leg((27.0, 54.5), (24.0, 58.5), (17.0, 57.5, 28.0, 62.5)),
     _leg((38.0, 54.0), (41.0, 59.5), (36.0, 58.5, 47.0, 63.0))),
    (_leg((27.0, 54.5), (22.0, 60.0), (15.0, 59.0, 26.0, 63.0)),
     _leg((38.0, 54.0), (47.0, 58.0), (42.0, 57.0, 53.0, 62.0))),
    (_leg((27.0, 54.5), (23.0, 59.0), (16.0, 58.0, 27.0, 63.0)),
     _leg((38.0, 54.0), (42.0, 58.5), (37.0, 57.5, 48.0, 62.5))),
]
_RUN_ARMS = [
    (_arm((17.0, 46.5), (9.5, 48.0), (7.0, 53.0), (6.5, 55.5), (17.2, 45.5)),
     _arm((46.0, 45.5), (52.0, 50.0), (54.0, 56.0), (54.5, 58.5), (45.8, 44.5))),
    (_arm((17.0, 46.0), (10.5, 49.0), (8.0, 54.5), (7.5, 57.0), (17.2, 45.0)),
     _arm((46.0, 46.0), (52.5, 49.0), (55.0, 54.5), (55.5, 57.0), (45.8, 45.0))),
    (_arm((17.0, 45.5), (11.0, 50.0), (9.0, 56.0), (8.5, 58.5), (17.2, 44.5)),
     _arm((46.0, 46.5), (53.5, 48.0), (56.0, 53.0), (56.5, 55.5), (45.8, 45.5))),
    (_arm((17.0, 46.0), (10.5, 49.5), (8.5, 55.0), (8.0, 57.5), (17.2, 45.0)),
     _arm((46.0, 46.0), (53.0, 49.0), (55.5, 54.5), (56.0, 57.0), (45.8, 45.0))),
]
_RUN_ANT = [
    ([(31, 22), (25, 19), (19.5, 17)], (17.6, 16.4)),
    ([(31, 21), (25.5, 17), (20.5, 14)], (18.6, 13.4)),
    ([(31, 22), (26, 19), (20.5, 17)], (18.6, 16.4)),
    ([(31, 21), (26.5, 18), (21.5, 15)], (19.6, 14.4)),
]


def _run(k):
    r = _rig("charge")
    r["streak"] = True
    r["eye_style"] = "angry"
    r["charge"] = "full"
    r["legL"], r["legR"] = _RUN_LEGS[k]
    r["armL"], r["armR"] = _RUN_ARMS[k]
    ant, ball = _RUN_ANT[k]
    r["ant"] = ant
    r["ball"] = (ball[0], ball[1], 2.6)
    _bob(r, (0.0, -2.0, 0.0, -2.0)[k])
    return r


def _drop(k):
    if k == 0:                       # faltering mid-stride, last red cell
        r = _run(2)
        r["charge"] = "low"
        r["eye_style"] = "dim"
        r["streak"] = False
        r["ant"] = [(31, 23), (26, 22), (21, 23)]
        r["ball"] = (19.4, 24.0, 2.6)
        _bob(r, 2.0)
        return r
    if k == 1:                       # knees gone, arms flung up, sparks
        r = _rig("charge")
        r["charge"] = "dead"
        r["eye_style"] = "dead"
        r["streak"] = False
        r["spark"] = "chest"
        r["ant"] = [(30, 26), (24, 27), (19, 30)]
        r["ball"] = (17.4, 31.2, 2.6)
        _bob(r, 5.0)
        r["armL"] = _arm((17.0, 48.0), (10.0, 43.0), (8.0, 37.0), (7.2, 34.5), (17.2, 47.0))
        r["armR"] = _arm((46.0, 47.0), (53.0, 42.0), (55.0, 36.0), (55.8, 33.5), (45.8, 46.0))
        r["legL"] = _leg((27.0, 57.0), (21.0, 62.0), (14.0, 60.0, 25.0, 63.0))
        r["legR"] = _leg((38.0, 57.0), (44.0, 62.0), (40.0, 60.0, 51.0, 63.0))
        return r
    r = _rig("dead")                 # 2,3,4 = landed + floor twitch
    if k == 3:
        _bob(r, -1.0)
        r["eye_style"] = "ember"
    if k == 4:
        r["ant"] = [(28.5, 35.5), (22.5, 35.0), (17.0, 37.5)]
        r["ball"] = (15.6, 38.8, 2.6)
    return r


def _hit(k):
    r = _rig("hero")
    r["eye_style"] = ("flash", "dim", "open")[k]
    r["spark"] = "head" if k == 0 else None
    tilt = (-4.0, -2.0, -0.5)[k]
    r["head"] = (18.0 + tilt, 19.0 - tilt * 0.4, 45.0 + tilt, 40.0 - tilt * 0.4)
    r["ant"] = [(30 + tilt, 20), (32.5 + tilt * 2.2, 15.5), (36 + tilt * 3.0, 13.5)]
    r["ball"] = (37.5 + tilt * 3.2, 12.4, 2.6)
    r["neck"] = (28.0 + tilt * .6, 38.5, 35.0 + tilt * .6, 44.5)
    r["torso"] = [(18.0 + tilt * .5, 43.5), (46.0 + tilt * .5, 43.5), (42.0, 56.0), (22.0, 56.0)]
    r["batt"] = (31.5 + tilt * .4, 49.5)
    sp = (5.0, 2.5, 0.8)[k]
    r["armL"] = _arm((16.0 - sp * .3, 46.0), (12.5 - sp, 50.0 - sp), (11.2 - sp * 1.3, 55.0 - sp * 1.4),
                     (10.6 - sp * 1.5, 57.4 - sp * 1.6), (16.4 - sp * .3, 45.0))
    r["armR"] = _arm((47.0 + sp * .3, 46.0), (50.5 + sp, 50.0 - sp), (51.8 + sp * 1.3, 55.0 - sp * 1.4),
                     (52.4 + sp * 1.5, 57.4 - sp * 1.6), (46.6 + sp * .3, 45.0))
    return r


def _die(k):
    if k < 2:
        r = _hit(0) if k == 0 else _hit(1)
        r["charge"] = "low" if k == 0 else "dead"
        r["eye_style"] = "flash" if k == 0 else "dim"
        r["spark"] = "chest"
        _bob(r, 1.0 + k * 3.0)
        return r
    r = _rig("dead")
    r["charge"] = "dead"
    r["eye_style"] = "dead"
    r["smoke"] = True
    if k == 2:
        _bob(r, -3.0)
        r["spark"] = "chest"
        r["smoke"] = False
    if k == 4:
        r["ant"] = [(28.5, 35.5), (22.5, 35.0), (17.0, 37.5)]
        r["ball"] = (15.6, 38.8, 2.6)
    return r


# ---------------------------------------------------------------------------
def build(pose="hero", charge=None):
    c = Canvas(W, H, PAL, OUTLINE)
    r = _rig(pose)
    ch = charge or r["charge"]
    over = ch == "over"
    cc = CHARGE.get(ch, CHARGE["full"])

    # ---- antenna -------------------------------------------------------
    for i in range(len(r["ant"]) - 1):
        a, b = r["ant"][i], r["ant"][i + 1]
        c.add(Capsule(a, b, 1.7 - i * 0.15, 1.5 - i * 0.15), "shell", prio=1)
    bx, by, br = r["ball"]
    c.add(Ellipse(bx, by, br, br), "shell", prio=2)

    # ---- torso ---------------------------------------------------------
    c.add(Poly(r["torso"], round_r=6.5), "shell", prio=3)
    nk = r["neck"]
    c.add(RoundRect(nk[0], nk[1], nk[2], nk[3], r=2.0, round_r=3.0), "shell", prio=2)

    # ---- limbs ---------------------------------------------------------
    for key in ("armL", "armR"):
        a = r[key]
        arm = Union([Capsule(a["up"][0], a["up"][1], a["up"][2], a["up"][3]),
                     Capsule(a["lo"][0], a["lo"][1], a["lo"][2], a["lo"][3])], k=1.2)
        c.add(arm, "shell", prio=4)
        c.add(Ellipse(*a["hand"]), "shell", prio=6)
        c.add(Ellipse(*a["cap"]), "purple", prio=7)
    for key in ("legL", "legR"):
        g = r[key]
        c.add(Capsule(g["leg"][0], g["leg"][1], g["leg"][2], g["leg"][3]), "shell", prio=4)
        f = g["foot"]
        c.add(RoundRect(f[0], f[1], f[2], f[3], r=2.0, round_r=3.0), "shell", prio=5)

    # ---- head ----------------------------------------------------------
    hd = r["head"]
    head = RoundRect(hd[0], hd[1], hd[2], hd[3], r=7.0, round_r=7.5)
    c.add(head, "shell", prio=8)
    # purple crown plate
    plate = Clip(head, Poly([(0, -50), (64, -50), (64, hd[1] + 4.5), (0, hd[1] + 4.5)]))
    c.add(plate, "purple", prio=9)
    # ear bolts
    c.add(Ellipse(hd[0] - 0.5, (hd[1] + hd[3]) / 2, 2.6, 3.2), "shell", prio=9)
    c.add(Ellipse(hd[2] + 0.5, (hd[1] + hd[3]) / 2, 2.6, 3.2), "shell", prio=9)

    # ---- detailing ------------------------------------------------------
    _panels(c, r, over)
    _battery(c, r, cc, over)
    _visor(c, r, cc, over)
    if r["smoke"]:
        _smoke(c, r)
    if r["spark"]:
        _sparks(c, r, r["spark"])
    if r["streak"]:
        _speed(c)
    if over:
        _overclock(c, r)

    c.occlude(strength=2, reach=1)
    c.rim(1, mats=("shell", "purple"))
    c.despeckle()
    return c


# ---------------------------------------------------------------------------
def _panels(c, r, over):
    t = r["torso"]
    top = (t[0][1] + t[1][1]) / 2
    left = min(t[0][0], t[3][0])
    right = max(t[1][0], t[2][0])
    c.shade_px([(x, int(top) + 2) for x in range(int(left) + 2, int(right) - 1)],
               2, "shell")
    c.shade_px([(x, int(top) + 1) for x in range(int(left) + 2, int(right) - 1)],
               -2, "shell")
    # rivets down the flanks
    for y in range(int(top) + 5, int(t[2][1]) - 2, 5):
        c.shade_px([(int(left) + 2, y), (int(right) - 2, y)], 2, "shell")
    # limb segment rings
    for key in ("armL", "armR"):
        a = r[key]
        ex, ey = a["lo"][0]
        c.shade_px([(int(ex) + dx, int(ey)) for dx in (-1, 0, 1)], 2, "shell")
        hx, hy = int(a["hand"][0]), int(a["hand"][1])
        c.shade_px([(hx - 1, hy + 1), (hx, hy + 1), (hx + 1, hy + 1)], 2, "shell")
        c.shade_px([(hx - 1, hy - 2), (hx, hy - 2)], -2, "shell")
    for key in ("legL", "legR"):
        g = r[key]
        kx, ky = g["leg"][1]
        c.shade_px([(int(kx) + dx, int(ky) - 1) for dx in (-2, -1, 0, 1, 2)], 2, "shell")
        f = g["foot"]
        fx0, fx1, fy1 = int(f[0]), int(f[2]), int(f[3])
        c.shade_px([(x, int(f[1]) + 1) for x in range(fx0 + 1, fx1)], 2, "shell")
        c.shade_px([(x, fy1 - 1) for x in range(fx0, fx1 + 1)], 3, "shell")
        c.shade_px([(x, fy1) for x in range(fx0, fx1 + 1)], 4, "shell")
        c.shade_px([(x, int(f[1]) + 2) for x in range(fx0 + 1, fx0 + 4)], -2, "shell")
    # neck rings
    nk = r["neck"]
    for y in (int(nk[1]) + 1, int(nk[3]) - 1):
        c.shade_px([(x, y) for x in range(int(nk[0]), int(nk[2]) + 1)], 2, "shell")


def _battery(c, r, cc, over):
    """Four cells + bezel + glow.  This is the charge read, and it has to be
    legible in one glance across the arena: the cell COUNT and the cell COLOUR
    both drop, and the antenna ball tracks both."""
    cx, cy = r["batt"]
    bh = r.get("batt_h", 7.0)
    half = 3 if bh >= 6.5 else 2            # cell half-height in rows
    lit, hi, mid, dk, glow, _eye = cc
    ix = int(cx - 7.5)                      # first cell column
    c.add(RoundRect(ix - 3, cy - bh, ix + 18, cy + bh, r=3.0, round_r=3.5),
          "purple", prio=10)
    c.add(RoundRect(ix - 1, cy - (half + 1.5), ix + 16, cy + (half + 1.5),
                    r=1.0, round_r=1.5), "glass", prio=11)
    if over:
        _blown_core(c, cx, cy, r.get("pulse", 0.0))
        return
    for i, off in enumerate((0, 4, 9, 13)):
        on = i < lit
        for x in range(ix + off, ix + off + 3):
            for y in range(int(cy) - half, int(cy) + half + 1):
                if on:
                    col = hi if y <= cy - 2 else (mid if y <= cy + 1 else dk)
                    if x == ix + off + 2 and y > cy - 2:
                        col = dk
                else:
                    col = "#323C4C" if y <= cy - 1 else "#242C38"
                c.raw_px([(x, y)], col)
    if lit:
        lo, hiy = int(cy) - half - 1, int(cy) + half + 1
        for x in range(ix - 1, ix + 17):
            c.raw_px([(x, lo), (x, hiy)], glow)
        for y in range(lo, hiy + 1):
            c.raw_px([(ix - 1, y), (ix + 16, y)], glow)
    bx, by, br = r["ball"]
    for dy in range(-int(br) - 1, int(br) + 2):
        for dx in range(-int(br) - 1, int(br) + 2):
            if dx * dx + dy * dy <= br * br:
                if lit:
                    col = hi if (dx <= 0 and dy <= 0) else mid
                else:
                    col = "#5A6577" if (dx <= 0 and dy <= 0) else "#3D4757"
                c.raw_px([(int(bx) + dx, int(by) + dy)], col)


def _blown_core(c, cx, cy, pulse=0.0):
    k = 1.0 + pulse * 0.16
    for y in range(int(cy) - 5, int(cy) + 6):
        for x in range(int(cx) - 9, int(cx) + 10):
            d = ((x - cx) / (8.0 * k)) ** 2 + ((y - cy) / (4.5 * k)) ** 2
            if d <= 1.0:
                col = "#FFFFFF" if d < 0.24 else ("#FFF0A0" if d < 0.52 else
                                                  ("#FFA83C" if d < 0.78 else "#C9521A"))
                c.raw_px([(x, y)], col)
    for k, (dx, dy) in enumerate(((-10, -5), (10, -5), (-10, 5), (10, 5))):
        c.raw_px([(int(cx) + dx, int(cy) + dy)], "#FFD06A")


def _visor(c, r, cc, over):
    eye = cc[5]
    style = r["eye_style"]
    chars = {
        "v": ("dark", 0), "V": ("glass", 1), "M": ("glass", 4), "t": "#D8E4F2",
        "G": _mix(eye, "#101820", 0.45), "R": eye,
    }
    if style == "dead":
        chars["G"] = "#2A2430"
        chars["R"] = "#5E2A26"
        chars["t"] = "#7E8A99"
    if style == "dim":
        chars["G"] = _mix(eye, "#101820", 0.72)
        chars["R"] = _mix(eye, "#101820", 0.45)
    if style == "ember":
        chars["G"] = "#3A2226"
        chars["R"] = "#B8392C"
        chars["t"] = "#7E8A99"
    if style == "flash":
        chars["G"] = "#FFD9A0"
        chars["R"] = "#FFFFFF"
        chars["t"] = "#FFFFFF"
    if style == "over":
        chars["G"] = "#FFB25A"
        chars["R"] = "#FFFFFF"
        chars["t"] = "#FFE9B0"
    grid = list(VISOR)
    if style == "angry":
        # hard scowl + a wide-open grab mouth
        grid[2] = "VVVVGGGVVVVVVGGGVVVV"
        grid[3] = "VVVVGRGVVVVVVGRGVVVV"
        grid[8] = "VVVVVMMMMMMMMMMVVVVV"
        grid[9] = "VVVVMtMMMMMMMMtMVVVV"
        grid[10] = "VVVVMMMMMMMMMMMMVVVV"
        grid[11] = "VVVVVMMMMMMMMMMVVVVV"
    if style in ("dead", "ember"):
        grid[8] = "VVVVVVVVVVVVVVVVVVVV"
        grid[9] = "VVVVVMMMMMMMMMVVVVVV"
        grid[10] = "VVVVVVMMMMMMMVVVVVVV"
        grid[11] = "VVVVVVVVVVVVVVVVVVVV"
    if style == "blink":
        grid[2] = "VVVVVVVVVVVVVVVVVVVV"
        grid[3] = "VVVGGGGVVVVVVGGGGVVV"
        grid[4] = "VVVGGGGVVVVVVGGGGVVV"
        grid[5] = "VVVVVVVVVVVVVVVVVVVV"
        grid[6] = "VVVVVVVVVVVVVVVVVVVV"
    if style == "flash":
        grid[8] = "VVMMVVVVVVVVVVVVMMVV"
        grid[9] = "VVMMMMMMMMMMMMMMMMVV"
        grid[10] = "VVMMMMMMMMMMMMMMMMVV"
        grid[11] = "VVVMMMMMMMMMMMMMMVVV"
    hd = r["head"]
    ox = int(round(hd[0] + (VIS_X - 18)))
    oy = int(round(hd[1] + (VIS_Y - 13))) + r["visor_dy"]
    c.stamp(grid, ox, oy, chars)


def _sparks(c, r, where):
    """electrical arcs - he is a machine coming apart"""
    if where == "head":
        hd = r["head"]
        ox, oy = int((hd[0] + hd[2]) / 2), int(hd[1]) - 1
        pts = [(-8, -2), (-6, -4), (-9, -5), (7, -2), (9, -4), (6, -5),
               (-2, -6), (2, -7)]
    else:
        cx, cy = r["batt"]
        ox, oy = int(cx), int(cy)
        pts = [(-13, -3), (-15, 0), (-12, 3), (13, -3), (15, 0), (12, 3),
               (-9, -8), (9, -8), (0, 9)]
    for i, (dx, dy) in enumerate(pts):
        c.raw_px([(ox + dx, oy + dy)], "#FFF6C8" if i % 2 else "#8CD8FF")


def _speed(c):
    """motion streaks trailing the sprint"""
    for (x0, x1, y, col) in ((4, 14, 22, "#6E7C90"), (1, 10, 27, "#8C9BB0"),
                             (3, 13, 33, "#9AA9BE"), (0, 9, 38, "#7E8CA0"),
                             (2, 11, 43, "#6E7C90")):
        c.raw_px([(x, y) for x in range(x0, x1)], col)
        c.raw_px([(x, y + 1) for x in range(x0 + 2, x1)], col)


def _smoke(c, r):
    """a couple of dying wisps curling off the crown"""
    hd = r["head"]
    x = int((hd[0] + hd[2]) / 2) + 5
    y = int(hd[1])
    puffs = [((0, -2), (1, -2), (0, -3), (1, -3), (2, -3)),
             ((2, -6), (3, -6), (4, -6), (2, -7), (3, -7), (4, -7), (3, -8)),
             ((1, -11), (2, -11), (3, -11), (2, -12))]
    cols = ("#6E7987", "#565F6E", "#414957")
    for blob, col in zip(puffs, cols):
        c.raw_px([(x + dx, y + dy) for dx, dy in blob], col)


def _overclock(c, r):
    """cracks in the chassis leaking light"""
    t = r["torso"]
    for pts in (
        [(22, 40), (25, 45), (23, 50), (26, 55)],
        [(41, 40), (38, 44), (40, 49), (37, 54)],
        [(29, 58), (31, 60)],
    ):
        seg = polyline(pts)
        for i, (x, y) in enumerate(seg):
            c.raw_px([(x, y)], "#FFC24A" if i % 3 else "#FFF0B0")
    hd = r["head"]
    for (x, y) in polyline([(int(hd[0]) + 3, int(hd[1]) + 6),
                            (int(hd[0]) + 6, int(hd[1]) + 11)]):
        c.raw_px([(x, y)], "#FFB84A")


def _mix(a, b, t):
    a = a.lstrip("#")
    b = b.lstrip("#")
    out = []
    for i in (0, 2, 4):
        av, bv = int(a[i:i + 2], 16), int(b[i:i + 2], 16)
        out.append(int(av * (1 - t) + bv * t))
    return "#%02x%02x%02x" % tuple(out)


SHEETS = {
    "computah_drop":        ["drop0", "drop1", "drop2", "drop3", "drop4"],
    "computah_hit":         ["hit0", "hit1", "hit2"],
    "computah_defeat":      ["die0", "die1", "die2", "die3", "die4"],
    "computah_phase2_idle": ["p2_idle0", "p2_idle1", "p2_idle2", "p2_idle3"],
}

# these two are emitted three times over - once per charge state - so the
# charge read costs the animation code a frame offset and no new art
CHARGE_SHEETS = {
    "computah_idle": ["idle0", "idle1", "idle2", "idle3"],
    "computah_run":  ["run0", "run1", "run2", "run3"],
}
CHARGE_ROWS = ("full", "half", "low")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    bad = _check()
    if bad:
        print("VISOR not symmetric:" + "".join(chr(10) + "  " + b for b in bad))
        sys.exit(1)
    from PIL import Image
    for name in ("hero", "charge", "dead", "phase2"):
        build(name).to_image().save(os.path.join(out, "computah_%s.png" % name))
    for st in ("full", "half", "low", "dead"):
        build("hero", charge=st).to_image().save(
            os.path.join(out, "computah_batt_%s.png" % st))
    for sheet, poses in SHEETS.items():
        ims = [build(p).to_image() for p in poses]
        strip = Image.new("RGBA", (W * len(ims), H), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.paste(im, (i * W, 0))
        strip.save(os.path.join(out, "%s.png" % sheet))
        print("%-24s %2d frames  %dx%d" % (sheet, len(ims), strip.width, strip.height))
    for sheet, poses in CHARGE_SHEETS.items():
        ims = []
        for st in CHARGE_ROWS:
            ims += [build(pp, charge=st).to_image() for pp in poses]
        strip = Image.new("RGBA", (W * len(ims), H), (0, 0, 0, 0))
        for i, im in enumerate(ims):
            strip.paste(im, (i * W, 0))
        strip.save(os.path.join(out, "%s.png" % sheet))
        print("%-24s %2d frames  %dx%d  (4 x full/half/low)"
              % (sheet, len(ims), strip.width, strip.height))
    print("ok")
