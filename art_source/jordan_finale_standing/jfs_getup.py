"""jordan_getup.png: 4 frames, played once (0.125 s each: the walk-out's 0.5 s GETUP_TIME), at his KO
spot in the arena, before he storms out. Facing screen-right like every sheet of his.

It starts where jordan_defeat.png leaves him (its frame 5: sunk back on his heels, head hung, his hand
fallen on the chase box lying on its side), in the fitted tee, and ends standing and furious:

  0  the snap: still sunk on his heels, but his head jerks up glaring (the quiff still flopped from the
     beating), his hand closing on the box, the other balled into a fist on the floor
  1  the kneel: up on one knee, his right foot planted, the other knee still down behind him, the box
     snatched up off the floor
  2  rising: pushing up off the planted foot, legs almost straight, leaning into it, the box hanging
     from his hand at his hip; the anger mark pops
  3  up and furious: standing, the box at his hip (the fist-pump's hold), the other fist clenched, the
     quiff sprung back up, teeth clenched, the anger mark and steam: the stance he storms off from
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402
import jfs_faces as FA  # noqa: E402
import jfs_parts as P  # noqa: E402

V = B.V
J = B.J
AD = B.AD
BX = B.BX
NAME = 'jordan_getup'
TIMES = [0.125, 0.125, 0.125, 0.125]
LOOP = False

HEAD_AT = (3, 2)                    # v2's idle head offset (the defeat's)
NECK_PIVOT = AD.NECK_PIVOT


#LEGS

def far_shin_back(knee=(46.0, 92.0), ankle=(33.0, 90.5)):
    """The far shin lying back along the floor from the knee (behind the near leg), in shadow (0.5
    thinner on the skinny build, as janim_defeat's near shin)."""
    part = B.fill(B.capsule(knee, ankle, 1.5, 1.8), 'n')
    B.rim(part, 'N', 0, -1)
    ax = int(round(ankle[0]))
    for (x, y) in list(part):
        if x <= ax + 1:
            part[(x, y)] = 'n'
    return part


# the far sneaker kneeling on tucked toes, behind (janim_defeat.TUCKED a step darker)
TUCKED_FAR = [''.join({'0': '9', '9': '2', '2': '1', '1': '1'}.get(ch, ch) for ch in r) for r in AD.TUCKED]

# the near leg planted forward: the thigh out level from the hip to a knee up at hip height, the shin
# straight down to the foot flat on the floor (build coordinates). SKINNY since 2026-09-28: the thigh
# and shin a pixel thinner, the far thigh as janim_defeat's skinny kneel, the seat the waist's 43-55.
NEAR_UP = [(42.6, 78.6), (46.6, 77.4), (52.6, 77.8), (55.8, 79.0), (55.6, 82.0), (55.0, 86.0), (55.8, 89.0),
           (50.6, 89.0), (51.6, 86.0), (51.4, 82.8), (46.0, 82.6), (42.8, 82.4)]     # the hem spreads onto the shoe
FAR_DOWN = [(52.1, 77.0), (55.4, 77.0), (55.8, 82.0), (56.0, 87.0), (55.6, 91.0), (54.4, 93.0), (52.8, 93.0),
            (51.6, 91.0), (51.2, 87.0), (51.6, 82.0)]
HIPS_KNEEL = [(42.6, 75.0), (55.4, 75.0), (55.2, 80.0), (53.0, 81.4), (50.0, 82.5), (47.0, 81.4), (42.8, 80.0)]


def kneel_one_legs():
    """Jeans for the kneel: the far leg down on its knee (upright thigh, shin lying back), the near
    leg planted forward, knee up."""
    near_px, far_px, hips_px = B.poly(NEAR_UP), B.poly(FAR_DOWN), B.poly(HIPS_KNEEL)
    part = B.fill(near_px | far_px | hips_px, 'N')
    span = B.V2B.span
    for (x, y) in list(part):
        if (x, y) in near_px and not (x, y) in hips_px:
            lo, hi = span(near_px, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x == hi else 'N'))
            if y <= 78:
                k = 's' if k == 'N' else k            # the top of the level thigh catches the light
        elif (x, y) in far_px and y >= 81:
            lo, hi = span(far_px, y)
            k = 'n' if x in (lo, hi) else ('s' if x == lo + 1 else 'N')
        else:
            lo, hi = span(part, y)
            k = 'S' if x == lo else ('s' if x == lo + 1 else ('n' if x >= hi - 1 else 'N'))
        part[(x, y)] = k
    B.stroke(part, [(49, 75), (49, 80)], 'n')                    # the fly
    B.stroke(part, [(52, 78), (55, 79)], 'S', only='Nsn')         # the knee's lit cap
    B.stroke(part, [(52, 83), (52, 88)], 's', only='N')          # the shin's front
    B.stroke(part, [(47, 81), (50, 82)], 'n', only='Ns')          # the fold behind the knee
    return part


def near_shoe_planted(dx=10, dy=0):
    far, near = J.shoes()
    near = dict(near)
    near[(47, 91)] = 'k'                        # v2's fix to the approved toe cap's gap
    return B.shift(near, dx, dy)


#ARMS

def near_fist_down(oy):
    """His right arm hanging from the slumped shoulder, the hand balled into a fist on the floor by
    his knee (janim_defeat.limp_near's arm, the fitted sleeve)."""
    root, el, wr = (40.6, 49.2 + oy), (36.4, 57.2 + oy), (35.6, 63.4 + oy)
    arm = B.arm([(root, el, 1.55, 1.45), (el, wr, 1.45, 1.3)], knobs=((el[0], el[1] + 0.2, 1.9),))
    sl = B.near_sleeve(root, el)
    band = B.amap(B.rows_of(B.BAND), 32, 60 + oy)
    fist = B.amap(B.rows_of(B.FIST_HANG), 32, 63 + oy)
    return [(arm, True), (sl, True), (band, False), (fist, False)]


def far_reach_box(oy):
    """His left arm fallen out onto the box on the floor (janim_defeat.reach_far), the fitted sleeve,
    the hand gripping the box's top edge."""
    root, el, wr = (57.8, 48.5 + oy), (63.4, 56 + oy), (68.4, 62 + oy)
    arm = B.arm([(root, el, 1.5, 1.4), (el, wr, 1.4, 1.3)], knobs=((el[0], el[1] + 0.2, 1.8),), far=True)
    sl = B.far_sleeve(root, el)
    hand = B.amap(B.rows_of(AD.HAND_ON_BOX), 66, 62 + oy)
    return [(arm, True), (sl, True)], hand


def far_arm_hold(dy, dx=0):
    """His left arm hanging with the box from his hand at his hip: v2's far_arm_box_low (fitted), the
    box and the hooked fingers as v2 frame 1 has them, moved by (dx, dy)."""
    parts = [(B.shift(p, dx, dy), ol) for p, ol in V.far_arm_box_low()]
    box = B.shift(J.box_part(3, 41), dx, dy)             # v2 frame 1's BOX_AT
    hand = B.shift(B.amap(V.LOW_HAND, 61, 63), dx, dy)
    return parts, box, hand


#FRAMES

def torso(cv, ox, oy, lean):
    cv.stamp(B.shift(V.neck(lean), ox, oy))
    cv.stamp(B.shift(V.shirt(1), ox, oy))
    B.AB.dandruff(cv.px, ox, oy)


def frame0():
    """The snap. The defeat's last frame (sunk on his heels: janim_defeat.frame_sit(1)) in the fitted
    tee, the head jerked up."""
    oy = 15
    cv = B.Canvas(96, 96)
    AD.lower_kneel(cv, AD.KNEEL_LOW)
    AD.box_on_floor(cv)
    far, hand = far_reach_box(oy)
    B.stamp_all(cv, far)
    torso(cv, 0, oy + 1, HEAD_AT[0] + 1)
    hd = B.tilt(FA.head('glare_shut', 0, 0, hair='flopped'), 6, NECK_PIVOT)
    hd = B.shift(hd, HEAD_AT[0] + 1, HEAD_AT[1] + oy + 1)
    cv.stamp(hd, outline=False)
    B.stamp_all(cv, near_fist_down(oy))
    cv.stamp(hand, outline=False)
    return cv, set()


def frame1():
    """The kneel: up on one knee, the box snatched up."""
    oy = 11
    cv = B.Canvas(96, 96)
    cv.stamp(far_shin_back())
    cv.stamp(B.amap(TUCKED_FAR, 27, 86), outline=False)
    cv.stamp(kneel_one_legs())
    cv.stamp(near_shoe_planted(12, 0), outline=False)
    parts, box, hand = far_arm_hold(oy - 6, 3)
    B.stamp_all(cv, parts)
    torso(cv, 0, oy, HEAD_AT[0] + 1)
    hd = FA.head('glare_shut', HEAD_AT[0] + 1, HEAD_AT[1] + oy, hair='flopped')
    cv.stamp(hd, outline=False)
    B.stamp_all(cv, P.near_arm_tense(0, oy)[0])
    cv.stamp(box, outline=False)
    cv.stamp(hand, outline=False)
    return cv, set()


def frame2():
    """Rising: legs almost straight, leaning into it."""
    oy = 4
    lean = 2
    cv = B.Canvas(96, 96)
    cv.stamp(AS_crouch())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    parts, box, hand = far_arm_hold(oy, lean)
    B.stamp_all(cv, parts)
    torso(cv, lean, oy, HEAD_AT[0] + lean)
    hd = FA.head('glare_shut', HEAD_AT[0] + lean + 1, HEAD_AT[1] + oy, hair='flopped')
    cv.stamp(hd, outline=False)
    B.stamp_all(cv, P.near_arm_tense(lean, oy)[0])
    cv.stamp(box, outline=False)
    cv.stamp(hand, outline=False)
    fx = set()
    FA.anger(cv, hd, fx, steam=False)
    return cv, fx


def AS_crouch():
    return B.AS.crouch_legs(drop=(71, 72, 73, 80), knees_in=1)


def frame3():
    """Up and furious."""
    cv = B.Canvas(96, 96)
    cv.stamp(V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)
    parts, box, hand = far_arm_hold(0)
    B.stamp_all(cv, parts)
    torso(cv, 0, 0, 4)
    hd = FA.head('glare_shut', 4, 3)
    cv.stamp(hd, outline=False)
    B.stamp_all(cv, P.near_arm_tense()[0])
    cv.stamp(box, outline=False)
    cv.stamp(hand, outline=False)
    fx = set()
    FA.anger(cv, hd, fx)
    return cv, fx


def builders():
    return [frame0, frame1, frame2, frame3]


def frames():
    out = []
    for b in builders():
        cv, fx = b()
        out.append((B.fill_holes(B.finish(cv)), {(x + B.ANCHOR_SHIFT, y) for (x, y) in fx}))
    return out
