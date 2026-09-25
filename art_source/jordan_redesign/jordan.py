"""Jordan, redesigned: the initial sprite for approval. 2 frames of 96x96, feet on row 95, x = 48 the
anchor column, facing screen-right in three-quarter view.

  frame 0  idle: slouched and cocky, a hand on his hip, a gold chase-edition boxed figure held up
           beside his face
  frame 1  the signature fist-pump from 10.webp: his right fist punched skyward with the pink
           wristband, a pink pop with a gold star bursting off it (the funko summon's own pop), the
           boxed figure tucked at his hip

Build order is back to front. Every part is keylined as it is stamped, so a part laid over another
cuts its own black line into it; that is where the interior separations come from.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import (Canvas, amap, capsule, ellipse, fill, image, line, paint, poly, rect, rim,  # noqa: E402,F401
                 stroke)
import head as headmod  # noqa: E402
import torso  # noqa: E402


#LOWER BODY

NEAR_LEG = [(38.5, 66), (48.5, 66), (48, 72), (47.5, 78), (46.5, 88), (39.5, 88), (39.5, 79), (38.5, 72)]
FAR_LEG = [(51, 66), (59, 66), (60, 71), (61.5, 78), (60.5, 83), (60.5, 88), (54, 88), (54, 83), (54.5, 78),
           (52.5, 72)]
HIPS = [(38.5, 64), (59, 64), (59.5, 70), (54, 71), (50.5, 72.5), (47, 71), (39, 70.5)]


def legs():
    """Dark jeans as one part: the near (screen-left) leg locked and taking the weight, the far one
    relaxed with its knee bent forward, parting below the crotch."""
    near, far, hips = poly(NEAR_LEG), poly(FAR_LEG), poly(HIPS)
    jeans = fill(near | far | hips, 'N')

    def span(pixels, y):
        xs = [x for (x, yy) in pixels if yy == y]
        return (min(xs), max(xs)) if xs else None

    for (x, y) in list(jeans):
        if (x, y) in near and (y >= 70 or x <= 46):
            lo, hi = span(near, y)
            if x == lo:
                k = 'S'
            elif x == lo + 1:
                k = 's'
            elif x == hi:
                k = 'n'
            else:
                k = 'N'
        elif (x, y) in far and y >= 70:
            lo, hi = span(far, y)
            t = (x - lo) / max(1, hi - lo)
            if x == lo or x == hi:
                k = 'n'
            elif 0.25 <= t <= 0.45:
                k = 's'                                       # the front of the thigh and shin
            else:
                k = 'N'
        else:
            lo, hi = span(jeans, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        jeans[(x, y)] = k
    stroke(jeans, [(50, 66), (50, 71)], 'n')                  # fly / crotch seam
    stroke(jeans, [(51, 70), (53, 72)], 'n')                  # far thigh in the near thigh's shadow
    for q in ((42, 76), (42, 77), (43, 77), (42, 78)):        # near knee
        jeans[q] = 's'
    stroke(jeans, [(44, 71), (46, 69)], 's', only='N')        # thigh fold
    stroke(jeans, [(45, 79), (46, 80)], 'n', only='N')        # back of the near knee
    stroke(jeans, [(41, 84), (43, 83), (46, 85)], 'n', only='Nsn')  # stacked hems
    stroke(jeans, [(41, 86), (44, 86)], 's', only='N')
    stroke(jeans, [(57, 79), (59, 80)], 'n', only='Ns')       # crease behind the far knee
    stroke(jeans, [(55, 84), (57, 83), (60, 85)], 'n', only='Ns')
    stroke(jeans, [(56, 86), (58, 86)], 's', only='N')
    return [jeans]


# Black sneakers (10.webp), toes to the right: charcoal uppers, a lit edge, white midsoles.
SHOE_NEAR = [
    # x: 37-41 42-46 47-51        y
    "..... ..... .....",          # 88  (the jeans hem covers the top)
    "k2111 kk... .....",          # 89
    "k2111 10k.. .....",          # 90  laces
    "k2111 110kk .....",          # 91
    "k2111 11122 3k...",          # 92  toe box
    "k0091 11111 22k..",          # 93  midsole rises at the heel
    "k0000 00000 009k.",          # 94
    ".kkkk kkkkk kkkk.",          # 95
]
SHOE_FAR = [
    # x: 51-55 56-60 61-64        y
    "..... ..... ....",           # 88
    "k2111 1kk.. ....",           # 89
    "k1111 110k. ....",           # 90
    "k1111 1110k k...",           # 91
    "k1111 11112 2k..",           # 92
    "k0911 11111 12k.",           # 93
    "k0000 00000 009k",           # 94
    ".kkkk kkkkk kkk.",           # 95
]


def shoes():
    near = amap([r.replace(' ', '') for r in SHOE_NEAR], 37, 88)
    far = amap([r.replace(' ', '') for r in SHOE_FAR], 51, 88)
    return [far, near]


def neck():
    n = fill(poly([(46, 33), (53, 33), (53, 43), (46, 43)]), 'c')
    rim(n, 'd', -1, 0)
    rim(n, 'b', 1, 0)
    for x in range(46, 54):                                   # the beard's shadow
        n[(x, 38)] = 'b'
        n[(x, 39)] = 'b' if x > 47 else 'c'
    return n


#ARMS

def sleeve(pts, hem, lit=True):
    """A T-shirt sleeve: red, lit on one side, with the black-trimmed hem along `hem`."""
    s = fill(poly(pts), 'R')
    rim(s, 'T' if lit else 'R', -1, 0)
    rim(s, 'V', 1, 0)
    stroke(s, hem, '1')
    return s


def arm(segments, base='d', lit='e', shade='c', crease=()):
    """One arm from capsules unioned into a single shape, lit from the upper left."""
    shape = set()
    for (p0, p1, r0, r1) in segments:
        shape |= capsule(p0, p1, r0, r1)
    part = fill(shape, base)
    rim(part, lit, -1, 0)
    rim(part, lit, 0, -1, only=base)
    rim(part, shade, 1, 0)
    rim(part, shade, 0, 1, only=base)
    for q in crease:
        if q in part:
            part[q] = 'b'
    return part


def near_arm_hip():
    """His right arm: sleeve to mid-bicep, elbow out, hand on the hip."""
    limb = arm([((38, 47), (30.5, 55.5), 2.7, 2.2), ((30.5, 55.5), (38.5, 61.5), 2.2, 1.9)],
               crease=((32, 56), (33, 57)))
    sl = sleeve([(37, 43), (42, 42), (42.5, 48), (38, 51), (34.5, 49.5), (35, 46)], [(35, 49), (38, 51)])
    hand = amap([
        # x: 37-43
        "..kkkk.",     # 58
        ".kddedk",     # 59  back of the hand on the hip, knuckles up
        "kcdddck",     # 60
        "kcddcck",     # 61
        "kbccbk.",     # 62  fingers round the hip
        ".kbbk..",     # 63
        "..kk...",     # 64
    ], 37, 58)
    return [(limb, True), (hand, False), (sl, True)]


def far_arm_box():
    """His left arm, bent up, holding the boxed figure beside his face (on the shadow side)."""
    limb = arm([((59.5, 46), (63, 55), 2.6, 2.3), ((63, 55), (64, 47), 2.2, 2.0)],
               base='c', lit='d', shade='b', crease=((62, 53),))
    for (x, y) in list(limb):                 # the forearm turns toward the light
        if y <= 53 and x >= 62 and limb[(x, y)] == 'c':
            limb[(x, y)] = 'd'
    sl = sleeve([(56, 42), (61, 43), (63.5, 49), (59, 51), (57, 48)], [(59, 51), (63, 49)], lit=False)
    return [(limb, True), (sl, True)]


# The chase edition: a gold window box. The header is the plumber's cap (red, gold star); the window
# shows the figure itself: red starred cap, dot eyes, moustache, blue overalls.
BOX = [
    # x: 61-65 66-70 71-75       y
    ".kkkk kkkkk kkkk.",         # 25
    "kTRRR RRORR RRVvk",         # 26  header: the star's point
    "kTRRR ROOOR RRVvk",         # 27
    "kTRRO OOYOO ORVvk",         # 28  arms
    "kTRRR OOOOO RRVvk",         # 29
    "kTRRR OOROO RRVvk",         # 30  legs
    "kkkkk kkkkk kkkkk",         # 31
    "kYkxx wwwww wwkGk",         # 32  window, a glint at its corner
    "kYkxw kkkkk wwkGk",         # 33  the figure's cap
    "kYkwk RRORR kwkGk",         # 34
    "kYkwk RRRRR RkkGk",         # 35  brim out to the right
    "kokwk kkkkk kwkGk",         # 36
    "kokwk dkdkd kwkGk",         # 37  dot eyes
    "kokwk jjjjd kwkGk",         # 38  moustache
    "kokww kBOBk wwkGk",         # 39  overalls, a gold button
    "kokww kBBBk wwkGk",         # 40
    "kokww klklk wxkGk",         # 41  shoes
    "kokww wwwwx xxkGk",         # 42
    "kkkkk kkkkk kkkkk",         # 43
    "kOOoo ooooo oGGgk",         # 44  base
    ".kkkk kkkkk kkkk.",         # 45
]


def box_part(dx=0, dy=0):
    rows = [r.replace(' ', '') for r in BOX]
    return amap(rows, 61 + dx, 25 + dy)


FAR_HAND_BOX = [
    # x: 59-64
    ".kkkk.",      # 42
    "kdeddk",      # 43  fingers wrapped over the base's front corner
    "kddddk",      # 44
    "kcddck",      # 45
    "kbccbk",      # 46
    ".kbbk.",      # 47
]


#FRAME 1: THE FIST-PUMP

def raised_arm():
    """His right arm punched straight up, the sleeve fallen back to the shoulder, a pink wristband."""
    limb = arm([((38.5, 44), (33, 32), 3.1, 2.7), ((33, 32), (31, 21), 2.7, 2.4)])
    sl = sleeve([(34.5, 44), (39, 40), (43, 43), (42, 48), (36, 48)], [(35, 43), (39, 41)])
    band = amap([
        # x: 31-38
        "kkkkkkkk",    # 22
        "kQPPPPqk",    # 23  pink wristband (10.webp)
        "kQPPPqqk",    # 24
        "kkkkkkkk",    # 25
    ], 27, 22)
    fist = amap([
        # x: 30-38
        ".kkkkkkk.",   # 11
        "kebebdbdk",   # 12  four curled fingers, palm out
        "kebdbdbck",   # 13
        "kdbdbdbck",   # 14
        "kddddddck",   # 15
        "kkkkkdcbk",   # 16  the thumb laid across the first two
        "keeedkcbk",   # 17
        ".kddckbk.",   # 18
        "..kkkkk..",   # 19
        "..kdddk..",   # 20  wrist
        "..kdcck..",   # 21
    ], 27, 11)
    return [(limb, True), (band, False), (fist, False), (sl, True)]


# The pop off the fist: the summon's own pink cloud and gold star (funko_spawn_pop.png).
STAR = [
    # x: 30-38
    "....k....",   # 0
    "...kYk...",   # 1
    "kkkkYOkkk",   # 2
    "kYYYYOOok",   # 3
    ".kOYOOok.",   # 4
    "..kOOOk..",   # 5
    ".kOokOok.",   # 6
    ".kok.kok.",   # 7
    ".kk...kk.",   # 8
]
GLINTS = {}
for (gx, gy) in ((20, 2), (43, 4), (21, 13)):
    GLINTS[(gx, gy)] = 'W'
    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        GLINTS[(gx + ddx, gy + ddy)] = 'Q'


# Puffs spaced about two radii apart, so the cloud's edge keeps real scallops: three across the
# top (the star over the middle one), one each side, three underneath. (cx, cy, r)
PUFFS = [(26.5, 5.0, 2.6), (31, 4.0, 3.0), (35.5, 5.0, 2.6), (23, 7.5, 2.2), (39, 7.5, 2.2),
         (26.5, 9.0, 2.2), (31, 9.3, 2.0), (35.5, 9.0, 2.2)]


def pop_cloud():
    """One pink puff cloud behind the star (the summon's pop), keylined as a single shape."""
    shape = ellipse(31, 7, 6.5, 2.8)
    for (cx, cy, r) in PUFFS:
        shape |= ellipse(cx, cy, r, r)
    p = fill(shape, 'P')
    rim(p, 'Q', -1, 0)
    rim(p, 'Q', 0, -1)
    rim(p, 'q', 1, 0)
    rim(p, 'q', 0, 1, only='P')
    return p


def far_arm_box_low():
    """Frame 1: his left arm down at his side, carrying the box by its top edge against his thigh."""
    limb = arm([((59.5, 46), (61.5, 56), 2.6, 2.3), ((61.5, 56), (62.5, 63), 2.2, 2.0)],
               base='c', lit='d', shade='b')
    sl = sleeve([(56, 42), (61, 43), (63, 50), (59, 51.5), (57, 48)], [(59, 51), (62, 50)], lit=False)
    return [(limb, True), (sl, True)]


LOW_HAND = [
    # x: 59-64
    ".kkkk.",      # 62
    "kcddck",      # 63
    "kcdddk",      # 64  fingers hooked over the box's top edge
    "kbccdk",      # 65
    ".kkkk.",      # 66
]


#FRAMES

def build(frame):
    cv = Canvas(96, 96)
    for leg in legs():
        cv.stamp(leg)
    for s in shoes():
        cv.stamp(s, outline=False)
    if frame == 0:
        for part, ol in far_arm_box():
            cv.stamp(part, outline=ol)
    else:
        for part, ol in far_arm_box_low():
            cv.stamp(part, outline=ol)
    cv.stamp(neck())
    cv.stamp(torso.shirt())
    # the idle slouches: head pushed a pixel forward and down into his shoulders
    hd = headmod.head(shout=(frame == 1))
    if frame == 0:
        hd = {(x + 1, y + 1): k for (x, y), k in hd.items()}
    cv.stamp(hd, outline=False)
    if frame == 0:
        for part, ol in near_arm_hip():
            cv.stamp(part, outline=ol)
        cv.stamp(box_part(), outline=False)
        cv.stamp(amap(FAR_HAND_BOX, 59, 42), outline=False)
    else:
        cv.stamp(pop_cloud())
        cv.stamp(amap([r.replace(' ', '') for r in STAR], 27, 0), outline=False)
        for q, k in GLINTS.items():
            cv.px[q] = k
        for part, ol in raised_arm():
            cv.stamp(part, outline=ol)
        cv.stamp(box_part(dx=0, dy=40), outline=False)
        cv.stamp(amap(LOW_HAND, 59, 62), outline=False)
    return cv


# The parts are placed in build coordinates; the finished frames are shifted one pixel left so the
# body (torso, jeans, head) centres on the anchor column x = 48.
ANCHOR_SHIFT = -1


def frame_px(frame):
    return {(x + ANCHOR_SHIFT, y): k for (x, y), k in build(frame).px.items()}


def frames():
    return image(frame_px(0)), image(frame_px(1))
