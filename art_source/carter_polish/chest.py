"""The chest showing between the lapels of the open gi, drawn by hand, and the prayer beads over it.

Kept from the approved sheet: the gi is open from the collar to the belt and shows the pecs and the
abs; the beads hang in a U over them. Changed: the approved chest was rows of 1px strokes in five
skin tones (it read as stripes), and the beads were 13 small overlapping balls on a black cord (it
read as a tangle). Here the pecs are two lit plates with a dark crescent under each, the sternum a
groove, the abs a clean 2x3 grid lit on top; the beads are 9 round 4px beads, evenly spaced.

The lapel keyline is part of this map (x 38 / 57 down most of the chest) and the jacket polygon in
frame0 stops one pixel short of it, so cloth and skin meet on one clean line.
"""
import math
from lib import amap

X0, Y0 = 38, 51

CHEST = [
    # x: 38-42 43-47 48-52 53-57       y
    "__kvv vvvvv vvvvv vvk__",        # 51  under the chin (mostly hidden by the beard)
    "_kttu vwwww wwwwv uuvk_",        # 52  the beard's shadow across the top of the chest
    "ktsst tuvvw wvutu uuuvk",        # 53
    "ktsss ttuuv vuttu uuuvk",        # 54
    "ktsst ttuuv vutuu uuvvk",        # 55
    "ktttt tuuuv vuuuu uvvvk",        # 56
    "kuttu uuuvv vuuuu vvvwk",        # 57
    "kuuvv vvvww wwvvv vvwwk",        # 58  bottom of the pecs
    "kuvww wwwwv vwwww wvvwk",        # 59  crescent under each pec
    "kuutt ttuuv vttuu uuvvk",        # 60  top pair of abs, lit on top
    "kuutu uuuvw wuuuu uvvvk",        # 61
    "kuvvv vvvvw wvvvv vvwvk",        # 62  groove
    "kuutt tuuuw wtuuu uvvvk",        # 63  middle pair
    "_kutu uuuvw wuuuu vvvk_",        # 64
    "_kvvv vvvvw wvvvv vwvk_",        # 65  groove
    "_kutt uuuvw wtuuu vvvk_",        # 66  bottom pair, into the belt
    "_kuuu uuvvw wvuuv vwwk_",        # 67
]


def chest():
    return amap(CHEST, X0, Y0, skip='_')


# ------------------------------------------------------------------ beads

# A bead is 4x4 inside its keyline, lit from the upper left: highlight, body, shadow, core shadow.
BEAD = [
    ".kkkk.",
    "kGGHHk",
    "kGHHIk",
    "kHHIJk",
    "kHIJJk",
    ".kkkk.",
]


def bead_centres(n=7, ax=11.5, ay=9.0, top=50.0):
    """n beads at equal spacing ALONG a U from collar to collar (equal angle bunched them at the
    ends), lowest at the sternum under the pecs."""
    pts = []
    steps = 2000
    for i in range(steps + 1):
        th = -math.pi / 2 + math.pi * i / steps
        pts.append((47.5 + ax * math.sin(th), top + ay * math.cos(th)))
    acc = [0.0]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.hypot(x1 - x0, y1 - y0))
    total = acc[-1]
    out = []
    j = 0
    for i in range(n):
        target = total * i / (n - 1)
        while j < len(acc) - 1 and acc[j] < target:
            j += 1
        out.append(pts[j])
    return out


def beads():
    """Stamped in order from the ends to the middle so each lower bead overlaps the one above it."""
    parts = []
    cs = bead_centres()
    order = sorted(range(len(cs)), key=lambda i: cs[i][1])
    for i in order:
        cx, cy = cs[i]
        x0 = int(round(cx - 2.5))
        y0 = int(round(cy - 2.5))
        parts.append(amap(BEAD, x0, y0))
    return parts
