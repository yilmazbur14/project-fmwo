"""Greyson on HUMAN proportions - design-pass prototype.

Rebuilt against the beat-'em-up reference: ~4.3 heads tall, real legs, the
classic lat-spread stance with daylight between each arm and the torso, and
muscle indicated with a handful of deliberate shapes rather than either
modelled anatomy or flat blobs.

Everything already approved about him is carried over: long strawberry-blonde
mane, thin gold wire glasses, forehead veins in pink skin tones, thin blonde
moustache, fair skin, blue eyes, purple trunks, white boots, forearm veins,
and the steroid V - wide shoulders, narrow waist.

Only `hero` and `windup` exist here.  The other poses get re-rigged onto these
proportions once the figure is approved.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import (Canvas, Ellipse, Capsule, Poly, RoundRect, Union, Clip,
                    Sub, HalfPlane, polyline)

W = H = 96
AX = 47.0
OUTLINE = "#000000"

PAL = {
    "skin":  ["#FFF2E2", "#FFDCBE", "#F6CCA8", "#DCA57C", "#B07E58", "#835438"],
    "hair":  ["#FFE6BC", "#FFC77E", "#F2A94E", "#CE8436", "#A16224", "#6E4116"],
    "trunk": ["#DEB8FA", "#C08CEE", "#A063DC", "#7E42B8", "#5A288A", "#3A1660"],
    "boot":  ["#FFFFFF", "#F2F6FE", "#DCE2F0", "#BCC4DA", "#949CB8", "#6A7290"],
}

FACE_CH = {
    "K": OUTLINE, "E": "#FFFFFF", "B": "#4A6E9E",
    "G": "#F0CC5E", "t": "#FFFFFF",
    "v": "#CE7A60", "V": "#FFD4BC",
    "S": ("skin", 0), "s": ("skin", 1), "n": ("skin", 2), "m": ("skin", 3),
    "w": ("skin", 4), "x": ("skin", 5),
    "H": ("hair", 0), "h": ("hair", 1), "g": ("hair", 2), "d": ("hair", 3),
}

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

_CLASS = {" ": "b", "K": "k", "E": "e", "B": "e", "G": "gl", "t": "t",
          "v": "vn", "V": "vn"}
for _c in "Ssnmwx":
    _CLASS[_c] = "sk"
for _c in "Hhgd":
    _CLASS[_c] = "hr"


def check_face():
    bad = []
    for j, row in enumerate(FACE):
        if len(row) != 19:
            bad.append("row %d len %d" % (j, len(row)))
            continue
        for i in range(9):
            if _CLASS.get(row[i]) != _CLASS.get(row[18 - i]):
                bad.append("row %d col %d/%d" % (j, i, 18 - i))
    return bad


def _mir(p):
    return (2 * AX - p[0], p[1])


def _mirror_arm(a):
    return {"delt": (2 * AX - a["delt"][0], a["delt"][1], a["delt"][2], a["delt"][3]),
            "uarm": (_mir(a["uarm"][0]), _mir(a["uarm"][1]), a["uarm"][2], a["uarm"][3]),
            "bice": (2 * AX - a["bice"][0], a["bice"][1], a["bice"][2], a["bice"][3]),
            "farm": (_mir(a["farm"][0]), _mir(a["farm"][1]), a["farm"][2], a["farm"][3]),
            "fist": (2 * AX - a["fist"][0], a["fist"][1], a["fist"][2], a["fist"][3])}


def _mirror_leg(l):
    return {"thigh": (_mir(l["thigh"][0]), _mir(l["thigh"][1]), l["thigh"][2], l["thigh"][3]),
            "calf": (_mir(l["calf"][0]), _mir(l["calf"][1]), l["calf"][2], l["calf"][3]),
            "boot": (2 * AX - l["boot"][2], l["boot"][1], 2 * AX - l["boot"][0], l["boot"][3])}


# ---------------------------------------------------------------------------
def _rig(pose):
    armL = {                       # lat spread: out, down, elbow bent
        "delt": (27.0, 34.0, 8.0, 7.5),
        "uarm": ((27.0, 34.0), (18.0, 48.0), 7.5, 5.8),
        "bice": (23.0, 40.0, 6.6, 6.0),
        "farm": ((18.0, 48.0), (19.0, 62.0), 5.8, 4.8),
        "fist": (20.0, 67.0, 5.0, 4.6),
    }
    legL = {
        "thigh": ((41.0, 58.0), (39.5, 78.0), 7.2, 5.2),
        "calf": ((39.5, 78.0), (38.5, 89.0), 5.2, 4.2),
        "boot": (31.0, 86.0, 45.0, 95.0),
    }
    r = {
        "head": (AX, 13.5, 8.5, 11.0),
        "neck": ((AX, 23), (AX, 29), 4.2, 5.2),
        "trap": ((43, 26), (37, 33), 2.8, 5.5),
        "armL": armL, "armR": _mirror_arm(armL),
        "legL": legL, "legR": _mirror_leg(legL),
        "lean": 0.0, "head_dx": 0.0, "head_dy": 0.0,
        "trunk_y": (54, 65), "fore": None, "chamber": (),
    }

    if pose == "windup":
        r["head"] = (AX + 2, 15.0, 8.5, 11.0)
        r["head_dx"] = 2.0
        r["head_dy"] = 1.5
        r["neck"] = ((AX + 2, 24.5), (AX + 1.5, 30), 4.3, 5.3)
        r["trap"] = ((44, 27.5), (37.5, 34), 2.8, 5.7)
        r["lean"] = 2.0
        # rear fist chambered tight at the ribs, elbow flung back
        r["armL"] = {
            "delt": (26.5, 34.5, 8.2, 7.7),
            "uarm": ((26.5, 34.5), (17.0, 45.0), 7.7, 6.0),
            "bice": (21.5, 39.0, 6.8, 6.2),
            "farm": ((17.0, 45.0), (24.0, 50.5), 6.0, 5.2),
            "fist": (27.0, 52.5, 5.4, 5.0),
        }
        # lead fist thrust at the camera, foreshortened
        r["armR"] = {
            "delt": (67.5, 35.0, 8.0, 7.5),
            "uarm": ((67.5, 35.0), (64.0, 40.0), 7.6, 7.4),
            "bice": (67.0, 37.0, 5.2, 4.8),
            "farm": ((64.0, 40.0), (58.5, 42.0), 7.8, 8.4),
            "fist": (53.0, 43.0, 9.6, 9.2),
        }
        r["fore"] = "armR"
        r["chamber"] = ("armL",)
        r["legL"] = {"thigh": ((41.0, 58.0), (36.0, 78.0), 7.2, 5.2),
                     "calf": ((36.0, 78.0), (34.5, 89.0), 5.2, 4.2),
                     "boot": (27.0, 86.0, 41.0, 95.0)}
        r["legR"] = {"thigh": ((53.0, 58.0), (58.5, 78.0), 7.0, 5.0),
                     "calf": ((58.5, 78.0), (60.0, 89.0), 5.0, 4.0),
                     "boot": (53.0, 86.0, 67.0, 95.0)}
    return r


# ---------------------------------------------------------------------------
def _mass(c, shape, mat, prio, wrap=0.56, amb=0.10):
    c.add(shape, mat, prio=prio, wrap=wrap, amb=amb)


def build(pose="hero"):
    c = Canvas(W, H, PAL, OUTLINE)
    r = _rig(pose)
    L = r["lean"]
    hx, hy, hrx, hry = r["head"]
    ty0, ty1 = r["trunk_y"]

    # ---- torso: broad chest, hard taper to a narrow waist ---------------
    chest = Ellipse(AX + L * .7, 36, 16.5, 7.5)
    latL = Ellipse(AX - 11 + L * .7, 42, 8.5, 8.0)
    latR = Ellipse(AX + 11 + L * .7, 42, 8.5, 8.0)
    ribs = Ellipse(AX + L, 47, 9.5, 6.5)
    waist = Ellipse(AX + L, 53, 6.5, 5.5)
    hips = Ellipse(AX + L, 59, 9.0, 6.5)
    torso = Union([chest, latL, latR, ribs, waist, hips], k=1.8)
    _mass(c, torso, "skin", 1)

    tp = r["trap"]
    neck = Union([Capsule(tp[0], tp[1], tp[2], tp[3]),
                  Capsule(_mir(tp[0]), _mir(tp[1]), tp[2], tp[3]),
                  Capsule(r["neck"][0], r["neck"][1], r["neck"][2], r["neck"][3])],
                 k=2.0)
    _mass(c, neck, "skin", 2)

    # the one bit of definition: two pec shapes, shaded as their own volumes
    pecL = Ellipse(AX - 6.5 + L * .7, 35.5, 7.5, 4.6)
    pecR = Ellipse(AX + 6.5 + L * .7, 35.5, 7.5, 4.6)
    _mass(c, pecL, "skin", 3, wrap=0.62, amb=0.08)
    _mass(c, pecR, "skin", 3, wrap=0.62, amb=0.08)

    # ---- legs -----------------------------------------------------------
    legs = []
    for key in ("legL", "legR"):
        g = r[key]
        leg = Union([Capsule(g["thigh"][0], g["thigh"][1], g["thigh"][2], g["thigh"][3]),
                     Capsule(g["calf"][0], g["calf"][1], g["calf"][2], g["calf"][3])],
                    k=1.6)
        _mass(c, leg, "skin", 4)
        legs.append(leg)

    # ---- trunks ---------------------------------------------------------
    tx = AX - 13 + L
    trunk_poly = Poly([(tx, ty0 - 1), (2 * AX - tx, ty0 - 1),
                       (2 * AX - tx + 1, ty0 + 4), (2 * AX - tx + 1, ty1 + 2),
                       (AX + 7, ty1 + 3), (AX + 4.5, ty1 - 1), (AX, ty1 + 1),
                       (AX - 4.5, ty1 - 1), (AX - 7, ty1 + 3),
                       (tx - 1, ty1 + 2), (tx - 1, ty0 + 4)], round_r=5)
    _mass(c, Clip(Union([hips] + legs, k=2.0), trunk_poly), "trunk", 5)

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
        _mass(c, upper, "skin", prio)
        inked.append((upper, prio))
        if key in (r["fore"],) + tuple(r["chamber"]):
            fore = Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3])
            fist = Ellipse(*a["fist"])
            _mass(c, fore, "skin", prio + 1)
            _mass(c, fist, "skin", prio + 2)
            inked += [(fore, prio + 1), (fist, prio + 2)]
        else:
            lower = Union([Capsule(a["farm"][0], a["farm"][1], a["farm"][2], a["farm"][3]),
                           Ellipse(*a["fist"])], k=1.8)
            _mass(c, lower, "skin", prio + 1)
            inked.append((lower, prio + 1))

    # ---- head + mane ----------------------------------------------------
    head = Union([Ellipse(hx, hy, hrx, hry),
                  Ellipse(hx, hy + 3.0, hrx - 1.4, hry - 2.4)], k=1.8)
    _mass(c, head, "skin", 18, wrap=0.50, amb=0.16)
    crown, falls = _hair(hx, hy, hrx, hry)
    _mass(c, falls, "hair", 7, wrap=0.60, amb=0.10)
    _mass(c, crown, "hair", 20, wrap=0.60, amb=0.10)

    for shp, prio in inked:
        c.contour(shp, 1.3, color=OUTLINE, below_prio=prio)
    c.contour(head, 1.3, color=OUTLINE, below_prio=18)

    c.occlude(strength=2, reach=1)
    c.rim(1, mats=("skin", "hair", "trunk", "boot"))
    c.despeckle()
    _details(c, r, L, ty0, ty1)
    c.stamp(FACE, int(FACE_X + r["head_dx"]), int(FACE_Y + r["head_dy"]), FACE_CH)
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


def _details(c, r, L, ty0, ty1):
    """Simple but definite: a sternum line, two ab ticks, a waistband, soles,
    knuckles and the forearm veins.  Nothing else."""
    ty0, ty1 = int(round(ty0)), int(round(ty1))
    P = lambda pts: [(a + L, b) for a, b in pts]

    c.shade_px(P(polyline([(AX, 33), (AX, 40)])), 2, "skin")          # sternum
    c.shade_px(P(polyline([(AX - 7, 40), (AX - 2, 41)])), 2, "skin")  # under-pec
    c.shade_px(P(polyline([(AX + 7, 40), (AX + 2, 41)])), 2, "skin")
    c.shade_px(P(polyline([(AX, 43), (AX, 52)])), 2, "skin")          # ab groove
    for yy in (45, 49):                                               # two ticks
        c.shade_px(P(polyline([(AX - 4, yy), (AX + 4, yy)])), 2, "skin")

    c.ink_px([(x, ty0 + 1) for x in range(26, 70)], OUTLINE, mats=("trunk",))

    for key in ("armL", "armR"):
        a = r[key]
        (ex, ey), (fx2, fy2) = a["farm"][0], a["farm"][1]
        c.shade_px(polyline([(ex + (fx2 - ex) * .3, ey + (fy2 - ey) * .3),
                             (ex + (fx2 - ex) * .8 - 1, ey + (fy2 - ey) * .8)]),
                   1, "skin")
        fx, fy, frx, fry = [float(v) for v in a["fist"]]
        big = frx > 7.0
        for k in range(-1, 2 if big else 1):
            gx = int(round(fx + (k + (0.5 if big else 0.0)) * frx * 0.5))
            c.raw_px([(gx, int(fy) - 1), (gx, int(fy)), (gx, int(fy) + 1)], OUTLINE)

    for key in ("legL", "legR"):
        b = r[key]["boot"]
        x0, x1, y1 = int(b[0]), int(b[2]), int(b[3])
        c.raw_px([(x, y1 - 2) for x in range(x0, x1 + 1)], OUTLINE)
        c.raw_px([(x, int(b[1]) + 2) for x in range(x0 + 1, x1)], OUTLINE)


CONTACT = {"windup": None}   # filled in below from the rig


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    bad = check_face()
    if bad:
        print("FACE not symmetric:" + "".join(chr(10) + "  " + b for b in bad))
        sys.exit(1)
    for name in ("hero", "windup"):
        im = build(name).to_image()
        im.save(os.path.join(out, "v2_%s.png" % name))
        bb = im.getbbox()
        print("%-8s bbox=%s  %dx%d  feet row %d" % (name, bb, bb[2] - bb[0],
                                                    bb[3] - bb[1], bb[3] - 1))
    r = _rig("windup")
    f = r[r["fore"]]["fist"]
    print("lead fist centre (windup) = (%g, %g)" % (f[0], f[1]))
    hd = _rig("hero")["head"]
    print("head %.0f px tall -> figure is %.1f heads" % (hd[3] * 2, 94.0 / (hd[3] * 2)))
