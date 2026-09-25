"""The Peach tee (10.webp): a red tee with black-trimmed collar and sleeves and a big princess graphic
on the front: yellow hair, gold crown with a red jewel, big blue eyes, a pink dress collar with a
blue brooch, the dress pink running across the bottom of the shirt. A little scruffy: the collar
stretched and sagging off-centre, the hem rumpled, a stain on the chest and a smudge on the pink.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import amap, fill, poly, stroke  # noqa: E402

# Where the collar trim runs (x -> y): stretched, so it sags lowest right of centre and wobbles.
COLLAR = {44: 40, 45: 41, 46: 42, 47: 42, 48: 43, 49: 43, 50: 44, 51: 44, 52: 43, 53: 42, 54: 41, 55: 40}

# The print, by hand. '.' keeps the shirt under it.
PRINT = [
    # x: 43-47 48-52 53-57        y
    "....k Ykoko k....",          # 45  crown prongs
    "..kkO YOROo okk..",          # 46  crown band, red jewel
    ".kYOk kkkkk koOk.",          # 47  crown base on the hair
    "kYOOO OOOOO OoOok",          # 48  hair
    "kYOkk kkkkk kkOok",          # 49  fringe line
    "kOOkf ffff ffkOok",          # 50  forehead
    "kOOkk kfffk kkOok",          # 51  lash lines
    "kOofB xfffB xfoGk",          # 52  big blue eyes
    "kOofD BfffD BfoGk",          # 53
    "koOfQ fffff QfoGk",          # 54  blush
    "koOkf ffPff fkoGk",          # 55  mouth
    "kGoOk fffff kOoGk",          # 56  chin
    "kGoOo kkkkk ooGk.",          # 57  jaw
    "kGkQP PPoPP Pqk Gk",         # 58  dress collar under her hair
    "kkQPP PoBoP PPqkk",          # 59  blue brooch in a gold ring
]

# The shirt's outline: shoulders wide, a slight taper at the waist, the hem rumpled.
OUTLINE = [(37, 44), (42, 40.5), (44, 40), (55, 40), (60, 42.5), (59.5, 50), (58.5, 57), (59.5, 66),
           (57, 67), (53, 66.5), (48, 67), (43, 66.5), (39.5, 66), (40.5, 57), (39.5, 50)]


def body_shape():
    part = fill(poly(OUTLINE), 'R')
    # the neck opening above the collar trim
    for x, yc in COLLAR.items():
        for y in range(36, yc):
            part.pop((x, y), None)
    return part


def _span(part, y):
    xs = [x for (x, yy) in part if yy == y]
    return (min(xs), max(xs)) if xs else (0, 0)


def shirt():
    part = body_shape()
    # Turn the cloth like a cylinder lit from the upper left: a lit near edge, a lit plane on the
    # near pec, a broad shadow down the far side, the darkest tone right at the far edge.
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):
        lo, hi = _span(part, y)
        t = (x - lo) / max(1, hi - lo)
        ramp = pink if y >= 60 else red
        k = ramp['base']
        if t <= 0.07:
            k = ramp['lit']
        elif t >= 0.94:
            k = ramp['deep']
        elif t >= 0.74:
            k = ramp['shade']
        elif y < 60 and 0.1 <= t <= 0.26 and 44 <= y <= 50:
            k = ramp['lit']
        part[(x, y)] = k
    # armpit shadows under the sleeves
    for (x, y) in list(part):
        if 47 <= y <= 52 and (x <= 41 or x >= 58):
            part[(x, y)] = 'v' if x >= 58 else 'V'
    # collar trim, stretched out
    for x, yc in COLLAR.items():
        part[(x, yc)] = '1'
    # where the dress pink meets the red at the sides, a seam line
    for (x, y) in list(part):
        if y == 60 and (x <= 42 or x >= 57):
            part[(x, y)] = 'k'
    # the print
    rows = [r.replace(' ', '') for r in PRINT]
    for q, k in amap(rows, 43, 45).items():
        if q in part:
            part[q] = k
    # folds: dragged toward the hand on his hip, and the rumpled hem
    stroke(part, [(58, 53), (56, 55)], 'v', only='V')
    stroke(part, [(57, 61), (53, 63)], 'q', only='P')
    stroke(part, [(49, 61), (45, 63)], 'q', only='P')
    stroke(part, [(55, 65), (52, 66)], 'q', only='P')
    stroke(part, [(44, 64), (46, 64)], 'Q', only='P')
    # scruff: a stain on the chest, a smudge on the pink
    for q in ((54, 43), (55, 43), (55, 44)):                  # a drip just off the collar
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for q in ((52, 63), (53, 63), (53, 64)):
        if q in part:
            part[q] = 'c'
    return part
