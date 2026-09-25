"""Jordan v2's body: skeletal and gangly, in clothes that hang off him.

  - stick arms and legs with bony elbows and knees, knock-kneed;
  - a slump: a thin neck craning forward, the head pushed forward and sunk down into narrow, sloped
    shoulders;
  - the Peach tee (the approved print, as it is) hanging off him like a sack: drooping sleeves far
    wider than the arms in them (one bunched at the shoulder in the fist-pump), a stretched collar
    gaping round the neck, soft folds, a long rumpled hem;
  - dark jeans loose on thin legs, bunched in stacks at the ankles over the (approved) sneakers.

Everything is placed in the rig's build coordinates, like art_source/jordan_redesign/jordan.py.
Parts are dicts {(x, y): key}; lists of (part, outline) pairs are stamped back to front.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jv2_base as B  # noqa: E402
from jv2_base import amap, capsule, ellipse, fill, poly, rim, span, stroke  # noqa: E402

J = B.jordan          # the approved rig: shoes, box, fist, pop cloud, star
T = B.rig_torso       # the approved rig: the Peach print


#LEGS

# thin legs: each thigh tapers to a bony knee that bulges inward (knock-kneed), then a thin shin
NEAR_LEG = [(41, 66), (46.5, 66), (46.6, 71), (46.8, 74.6), (48, 77.2), (47.6, 79.4), (45.4, 82.6),
            (44.6, 87.5), (40.6, 87.5), (41, 83.6), (42.4, 79.6), (42.2, 77.2), (42.8, 74.6), (41.8, 71)]
FAR_LEG = [(51.6, 66), (57, 66), (56.4, 71), (55, 74.6), (55.6, 77.2), (55.4, 79.4), (57, 83.5), (57.4, 87.5),
           (53.2, 87.5), (52.8, 83.6), (50.4, 79.6), (49.8, 77.2), (50.8, 74.6), (51.2, 71)]
HIPS = [(40.6, 64), (57.4, 64), (57.2, 69), (53, 70.4), (50, 71.5), (47, 70.4), (41.2, 69)]
# the hems stacked on the shoes: loose denim bunching round thin ankles
NEAR_HEM = [(39.2, 84.2), (45.6, 84.2), (46.2, 88.5), (38.8, 88.5)]
FAR_HEM = [(52.4, 84.2), (58.2, 84.2), (58.8, 88.5), (52.2, 88.5)]


def legs():
    near = B.poly(NEAR_LEG) | B.poly(NEAR_HEM)
    far = B.poly(FAR_LEG) | B.poly(FAR_HEM)
    hips = B.poly(HIPS)
    jeans = fill(near | far | hips, 'N')
    for (x, y) in list(jeans):
        if (x, y) in near and y >= 70:
            lo, hi = span(near, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x == hi else 'N'))
        elif (x, y) in far and y >= 70:
            lo, hi = span(far, y)
            k = 's' if x == lo + 1 else ('n' if x in (lo, hi) else 'N')
        else:
            lo, hi = span(jeans, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        jeans[(x, y)] = k
    stroke(jeans, [(50, 66), (50, 71)], 'n')                          # the fly, under the hem
    # knees: bony caps the cloth catches on, and the fold behind each
    for q in ((46, 76), (47, 77), (46, 77), (47, 78)):     # the kneecaps poke through the denim
        if q in jeans:
            jeans[q] = 's'
    for q in ((51, 76), (50, 77), (51, 77), (51, 78)):
        if q in jeans:
            jeans[q] = 's'
    stroke(jeans, [(44, 80), (46, 81)], 'n', only='N')
    stroke(jeans, [(53, 80), (55, 81)], 'n', only='N')
    # slack cloth: a long diagonal drag down each shin
    stroke(jeans, [(43, 73), (45, 75)], 'n', only='N')
    stroke(jeans, [(53, 72), (54, 74)], 'n', only='N')
    # the stacks at the ankles
    stroke(jeans, [(40, 85), (42, 86), (45, 85)], 'n', only='NsS')
    stroke(jeans, [(40, 87), (43, 87), (45, 86)], 's', only='N')
    stroke(jeans, [(53, 85), (55, 86), (58, 85)], 'n', only='Ns')
    stroke(jeans, [(54, 87), (57, 87)], 's', only='N')
    return jeans


def shoes():
    """The approved sneakers, with one keyline pixel added: the near toe cap's lit edge touched the
    background at (47, 92) (a gap in the approved art too); (47, 91) closes it."""
    far, near = J.shoes()
    near = dict(near)
    near[(47, 91)] = 'k'
    return [far, near]


#NECK, CHEST AND SHIRT

def neck(dx):
    """A thin neck craning up and forward from the collar to under the jaw, and the skin the
    stretched collar shows round its base, as one part so no keyline cuts across the base of the
    neck. `dx` = the head's x offset: the neck leans with the head. The Adam's apple bumps out on its
    front edge."""
    o = dx - 3
    col = B.poly([(47.2 + o * 0.3, 46), (50.8 + o * 0.3, 46), (52.2 + o, 43), (54.2 + o, 40.5),
                  (54.6 + o, 37), (50.2 + o, 37), (50.2 + o, 40.5), (48.4 + o * 0.5, 43)])
    skin = B.poly([(43.4, 43), (56, 43), (55, 44.8), (51.6, 46.4), (48, 46.4), (44.4, 44.8)])
    n = fill(skin, 'c')
    column = fill(col, 'c')                            # the neck turns like a thin cylinder
    rim(column, 'd', -1, 0)
    rim(column, 'b', 1, 0)
    n.update(column)
    for (x, y) in list(n):
        if y <= 39:
            n[(x, y)] = 'b'                            # the jaw's shadow on the neck
        elif y == 40 and (x + 1, y) not in n:
            n[(x, y)] = 'b'
    ax = int(round(53.5 + o))                          # the Adam's apple
    n[(ax, 41)] = 'd'                                 # a 1px bump; the stamp keylines round it
    n[(ax, 42)] = 'b'
    # the neck's shadow falls on the chest to its right, down into the stretched collar
    for (x, y) in list(n):
        if (x, y) not in column and y >= 43 and (x - 1, y) in column:
            n[(x, y)] = 'b'
    return n


# where the collar trim runs (x -> y): stretched out, sagging off-centre, gaping
COLLAR = {43: 43, 44: 44, 45: 44, 46: 45, 47: 45, 48: 46, 49: 46, 50: 46, 51: 46, 52: 45, 53: 45,
          54: 44, 55: 44, 56: 43}

# the tee's body: narrow sloped shoulders, a straight sack-like hang, a long rumpled hem
TORSO = [(38.8, 49.4), (41.6, 45.6), (44.4, 43.4), (55.6, 43.4), (58, 45), (60, 48.4), (60.4, 54),
         (61, 62), (61.8, 69.6), (59.4, 71.2), (56.6, 70.2), (53, 71.4), (49.6, 70.4), (46, 71.4),
         (42.6, 70.4), (37.8, 71.4), (38.2, 62), (39.2, 54)]
PRINT_AT = (42, 47)            # the approved print's top-left (it sat at (43, 45) on the old tee)
BAND_Y = PRINT_AT[1] + 15      # the princess's dress pink runs from here to the hem


def shirt(frame=0):
    part = fill(B.poly(TORSO), 'R')
    for x, yc in COLLAR.items():                       # the neck opening above the trim
        for y in range(40, yc):
            part.pop((x, y), None)
    red = {'lit': 'T', 'base': 'R', 'shade': 'V', 'deep': 'v'}
    pink = {'lit': 'Q', 'base': 'P', 'shade': 'q', 'deep': 'q'}
    for (x, y) in list(part):
        lo, hi = span(part, y)
        t = (x - lo) / max(1, hi - lo)
        ramp = pink if y >= BAND_Y else red
        k = ramp['base']
        if t <= 0.06:
            k = ramp['lit']
        elif t >= 0.95:
            k = ramp['deep']
        elif t >= 0.76:
            k = ramp['shade']
        elif y < BAND_Y and 0.1 <= t <= 0.24 and 46 <= y <= 52:
            k = ramp['lit']
        part[(x, y)] = k
    for x, yc in COLLAR.items():                       # the collar trim, stretched out
        if (x, yc) in part:
            part[(x, yc)] = '1'
    for (x, y) in list(part):                          # the seam where the red meets the pink
        if y == BAND_Y and (x <= 41 or x >= 58):
            part[(x, y)] = 'k'
    rows = B.rows_of(T.PRINT)
    for q, k in amap(rows, *PRINT_AT).items():
        if q in part:
            part[q] = k
    # drape: the cloth hangs straight down off the narrow shoulders like a sack, so the folds are
    # long verticals, each ending in a scallop of the rumpled hem
    stroke(part, [(40, 54), (40, 60), (41, 64)], 'V', only='RT')
    stroke(part, [(59, 50), (59, 56), (58, 60)], 'v', only='V')
    # soft folds in the pink, curved and uneven so no two ever line up into a shape
    def fold(pts, key='q', only='PQ'):
        for q in pts:
            if part.get(q) in only:
                part[q] = key
    if frame == 0:
        # his hand pinches the tee at the hip: one long pull fold sweeps from the grip down across
        # the pink, a shorter one under it
        fold(((42, 64), (43, 65), (44, 65), (45, 66), (46, 67), (46, 68), (47, 69)))
        fold(((43, 64), (44, 64), (46, 66)), 'Q', 'P')
        fold(((42, 67), (43, 68), (43, 69)))
        fold(((51, 65), (51, 66), (50, 67), (50, 68)))
        fold(((52, 66), (51, 67)), 'Q', 'P')
    else:
        # hanging straight: two soft verticals of different lengths
        fold(((44, 64), (44, 65), (45, 66), (45, 67), (45, 68), (44, 69)))
        fold(((43, 65), (44, 66), (44, 67)), 'Q', 'P')
        fold(((50, 66), (50, 67), (51, 68), (51, 69)))
        fold(((49, 67), (50, 68)), 'Q', 'P')
    # scruff: the drip off the collar, the smudge on the pink
    for q in ((55, 46), (56, 46), (56, 47)):
        if part.get(q) in ('R', 'T', 'V'):
            part[q] = 'b'
    for q in ((54, 66), (55, 66), (55, 67)):
        if q in part:
            part[q] = 'c'
    return part


# dandruff fallen on his shoulders: white flakes, a couple of greyer ones
DANDRUFF = {(41, 48): 'W', (44, 45): '9', (57, 46): 'W', (38, 51): '9', (59, 49): 'W', (42, 46): 'W'}


def dandruff(px):
    for q, k in DANDRUFF.items():
        if px.get(q) in ('R', 'T', 'V', 'v'):
            px[q] = k


#ARMS

def limb(segments, knobs=(), base='d', lit='e', shade='c'):
    """A thin arm: capsules unioned into one shape, bony knobs at the joints, lit from the upper
    left, a shadow line along its underside."""
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= capsule(p0, p1, r0, r1)
    for (cx, cy, r) in knobs:
        shape |= ellipse(cx, cy, r, r)
    part = fill(shape, base)
    rim(part, lit, -1, 0)
    rim(part, lit, 0, -1, only=base)
    rim(part, shade, 1, 0)
    rim(part, shade, 0, 1, only=base)
    return part


def sleeve(pts, hem, lit=True):
    """A baggy T-shirt sleeve: red, lit on the side toward the light, the dark red of its underside,
    the trim along its hem."""
    s = fill(poly(pts), 'R')
    rim(s, 'T' if lit else 'R', -1, 0)
    rim(s, 'V', 1, 0)
    rim(s, 'v', 0, 1, only='RV')
    stroke(s, [(int(round(x)), int(round(y))) for (x, y) in hem], '1')
    return s


def near_arm_hip():
    """His right arm: a stick out of a drooping sleeve that reaches almost to the elbow, the elbow a
    sharp point, the hand on his hip."""
    arm = limb([((40.6, 49.2), (32.4, 57.2), 1.55, 1.45), ((32.4, 57.2), (38.2, 63.2), 1.45, 1.3)],
               knobs=((32.4, 57.4, 1.9),))
    sl = sleeve([(44.2, 43.4), (41.4, 44.6), (38.6, 47.2), (35.4, 51.6), (33.6, 54.0), (37.6, 57.8),
                 (41.2, 55.2), (42.6, 51.6), (43.4, 47.6)], [(34, 54), (37, 57)])
    hand = amap([
        # x: 36-42
        "..kkk..",     # 60
        ".kdedk.",     # 61  bony knuckles on the hip
        "kcdddck",     # 62
        "kbdccbk",     # 63
        ".kbcbk.",     # 64  fingers pinching the tee
        "..kbk..",     # 65
        "...k...",     # 66
    ], 36, 60)
    return [(arm, True), (sl, True), (hand, False)]


def far_arm_box():
    """His left arm holding the box up beside his face: the upper arm lost in a drooping sleeve, a
    stick forearm rising in front of it to the box."""
    upper = limb([((57.8, 48.5), (62.8, 56.6), 1.5, 1.4)], knobs=((62.8, 56.6, 1.8),),
                 base='c', lit='d', shade='b')
    fore = limb([((62.8, 56.6), (64.4, 49.8), 1.4, 1.25)], knobs=((62.8, 56.8, 1.8),),
                base='c', lit='d', shade='b')
    sl = sleeve([(55.6, 43.4), (58.4, 44.8), (60.8, 47.4), (62.6, 50.6), (63.2, 52.6), (59.4, 55.6),
                 (57.8, 52.4), (57, 48)], [(59, 55), (62, 53)], lit=False)
    return [(upper, True), (sl, True), (fore, True)]


FAR_HAND_BOX = [
    # x: 61-66
    ".kkkk.",      # 44
    "kdeddk",      # 45  fingers wrapped over the base's front corner
    "kddddk",      # 46
    "kcddck",      # 47
    ".kccbk",      # 48
    "..kbk.",      # 49  a thin wrist
]


def raised_sleeve(arm):
    """The sleeve fallen back to the shoulder, bunched round the top of the raised arm. Its opening
    faces up the arm: the back rim behind the arm, the dark inside of the sleeve either side of it,
    the front rim across it; below that the bunched sleeve, a fold pulled toward the armpit."""
    part = fill(poly([(34.6, 43.6), (44.6, 43.6), (45, 46.4), (43.4, 49.2), (40.2, 50.4), (36.6, 49.4),
                      (34.8, 46.6)]), 'R')
    rim(part, 'T', -1, 0)
    rim(part, 'V', 1, 0)
    rim(part, 'v', 0, 1, only='RV')
    stroke(part, [(37, 45), (40, 48), (41, 49)], 'V', only='R')
    for y, (lo, hi), key in ((41, (36, 43), '1'), (42, (35, 44), 'v')):
        xs = [x for (x, yy) in arm if yy == y]
        a0, a1 = (min(xs) - 1, max(xs) + 1) if xs else (99, -99)      # the arm and its keyline
        for x in range(lo, hi + 1):
            if x < a0 or x > a1:
                part[(x, y)] = key
    for x in range(35, 45):
        part[(x, 43)] = '1'
    return part


def raised_arm():
    """The fist-pump: a stick arm punched up out of the sleeve bunched at the shoulder, a bony elbow,
    the pink wristband hanging loose on the thin wrist."""
    arm = limb([((40.8, 47.5), (35.4, 34.6), 1.6, 1.5), ((35.4, 34.6), (31.4, 22.5), 1.5, 1.3)],
               knobs=((35.4, 34.8, 1.9),))
    sl = raised_sleeve(arm)
    band = amap([
        # x: 28-34
        "kkkkkkk",     # 22
        "kQPPPqk",     # 23  loose on him now
        "kQPPqqk",     # 24
        "kkkkkkk",     # 25
    ], 28, 22)
    fist = J.raised_arm()[2][0]                    # the approved fist, straight from the rig
    # the arm runs on through the opening, between the dark of the sleeve's inside either side of it
    through = {q: k for q, k in arm.items() if q[1] in (41, 42)}
    return [(arm, True), (sl, True), (through, False), (band, False), (fist, False)]


def far_arm_box_low():
    """Frame 1: his left arm hanging out of the drooping sleeve, swung a little clear of the tee so the
    stick of it shows, the box's weight on it."""
    arm = limb([((57.8, 48.5), (62.6, 56.4), 1.5, 1.4), ((62.6, 56.4), (63.8, 63), 1.4, 1.3)],
               knobs=((62.6, 56.6, 1.7),), base='c', lit='d', shade='b')
    sl = sleeve([(55.6, 43.4), (58.4, 44.8), (60.8, 47.6), (62.4, 51.2), (63, 53.8), (58.8, 55.4),
                 (57.4, 51), (57, 47)], [(59, 55), (62, 54)], lit=False)
    return [(arm, True), (sl, True)]


# the approved hooked fingers, redrawn at the top so the thin wrist runs into the hand instead of
# stopping at a keyline across it
LOW_HAND = [
    # x: 61-66
    "..kdk.",      # 63  the wrist
    ".kcddk",      # 64
    "kcdddk",      # 65  fingers hooked over the box's top edge
    "kbccdk",      # 66
    ".kkkk.",      # 67
]
