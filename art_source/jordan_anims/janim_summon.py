"""jordan_summon.png: 4 frames, played once. The fist-pump that pops his figures in. In v2's look.

  0  wind-up: powering up. Knees knocking as he dips, teeth gritted, the near stick arm hanging tense
     with the fist clenched at his hip, the box hanging from the other
  1  the punch: the fist whips up past his head with a speed trail, the pop just flashing on it, the
     sleeve bunching at his shoulder
  2  the approved v2 fist-pump frame, pixel for pixel: the pink pop and star
  3  recovery: the fist pulled down into a "yes!", the pop breaking into loose puffs, grinning

The pop copies the grammar of the funko summon pop (Funkos/funko_spawn_pop.png): a small flower
flash, the keylined cloud with its star, then loose unkeylined puffs and a small star on top.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402
import janim_box as BX  # noqa: E402
import janim_heads as HD  # noqa: E402

J = B.jordan
V = B.V2B
NAME = 'jordan_summon'
TIMES = [0.3, 0.08, 0.26, 0.16]
LOOP = False
POP_FRAME = 2
APPROVED = {POP_FRAME: 1}   # frame 2 is the approved v2 frame 1

HEAD_AT = B.V2F.HEAD_AT[1]        # v2's fist-pump head
BOX_AT = B.V2F.BOX_AT[1]          # the box at his hip, as an offset from the rig box's (61, 25)
LOW_HAND_AT = B.V2F.LOW_HAND_AT


#LEGS

def crouch_legs(drop=(72, 81), knees_in=1):
    """v2's thin jeans in a dip: `drop` rows are taken out of the thighs and shins (the hips sink while
    the soles stay put) and the bony knees knock a pixel further in."""
    jeans = V.legs()
    out = {}
    for (x, y), k in jeans.items():
        if y in drop:
            continue
        out[(x, y + sum(1 for r in drop if r > y))] = k
    res = {}
    for (x, y), k in out.items():
        dx = 0
        if 75 <= y <= 81:
            dx = knees_in if x <= 49 else -knees_in
        res[(x + dx, y)] = k
    return res


#THE NEAR ARM

FIST_UP = B.rows_of([
    # x: 27-35 (the approved raised fist, palm out, and its wrist)
    ".kkkkkkk.",
    "kebebdbdk",
    "kebdbdbck",
    "kdbdbdbck",
    "kddddddck",
    "kkkkkdcbk",
    "keeedkcbk",
    ".kddckbk.",
    "..kkkkk..",
    "..kdddk..",
    "..kdcck..",
])
# v2's wristband: 7 wide, hanging loose on the thin wrist
BAND = B.rows_of([
    "kkkkkkk",
    "kQPPPqk",
    "kQPPqqk",
    "kkkkkkk",
])
# the same band round a wrist that runs sideways: 7 tall
BAND_SIDE = B.rows_of([
    "kkkk",
    "kQPk",
    "kQPk",
    "kPPk",
    "kPqk",
    "kqqk",
    "kkkk",
])
# The fist held low in front of him, knuckles forward (to his right), thumb on top, lit from above.
FIST_SIDE = B.rows_of([
    # x: 0-6
    ".kkkkk.",
    "kdeeedk",
    "kkkkkdk",
    "kdbdbck",
    "kdbdbck",
    "kcbcbbk",
    ".kkkkk.",
])


def drooping_sleeve(dy, hem_x=36, hem_y=56):
    """The near sleeve hanging off his narrow shoulder down the upper arm, far wider than the arm,
    its trimmed hem nearly at the elbow (v2's near sleeve, re-hung for an arm held closer in)."""
    return V.sleeve([(44.2, 43.4 + dy), (41.4, 44.6 + dy), (38.8, 47 + dy), (37, 50.6 + dy),
                     (hem_x - 1.2, hem_y - 2.4 + dy), (hem_x + 3.6, hem_y + 1.4 + dy), (42, 54 + dy),
                     (43, 50.6 + dy), (43.6, 47 + dy)],
                    [(hem_x - 1, hem_y - 2 + dy), (hem_x + 3, hem_y + 1 + dy)])


# A fist clenched hanging at his side, knuckles down, lit on top.
FIST_HANG = B.rows_of([
    ".kkkkk.",
    "kdeeddk",
    "kdddddk",
    "kcdddck",
    "kbcbcbk",
    "kbkbkbk",
    ".kkkkk.",
])


def near_arm_cocked(dy):
    """Wind-up: powering up. The stick arm hangs tense out of the drooping sleeve, the bony elbow
    kinked out, the fist clenched at his hip; the loose wristband shows against the air."""
    arm = V.limb([((40.6, 49.2 + dy), (36.4, 57.4 + dy), 1.55, 1.45), ((36.4, 57.4 + dy), (35.6, 63.2 + dy), 1.45, 1.3)],
                  knobs=((36.4, 57.6 + dy, 1.9),))
    sl = drooping_sleeve(dy, hem_x=36, hem_y=54)
    band = B.amap(BAND, 32, 60 + dy)
    fist = B.amap(FIST_HANG, 32, 63 + dy)
    return [(arm, True), (sl, True), (band, False), (fist, False)]


def raised_arm(dy=0, fist_dy=0):
    """v2's fist-pump arm (jv2_body.raised_arm), copied here so the fist can stop `fist_dy` short of
    the top and the whole arm move with the body by `dy`. With both 0 it is v2's exactly."""
    ey = 34.6 + dy + fist_dy / 2.0
    arm = V.limb([((40.8, 47.5 + dy), (35.4, ey), 1.6, 1.5), ((35.4, ey), (31.4, 22.5 + dy + fist_dy), 1.5, 1.3)],
                 knobs=((35.4, ey + 0.2, 1.9),))
    sl = B.shift(V.raised_sleeve(B.shift(arm, 0, -dy)), 0, dy)
    band = B.amap(BAND, 28, 22 + dy + fist_dy)
    fist = B.shift(J.raised_arm()[2][0], 0, dy + fist_dy)
    through = {q: k for q, k in arm.items() if q[1] in (41 + dy, 42 + dy)}
    return [(arm, True), (sl, True), (through, False), (band, False), (fist, False)]


def near_arm_yes(dy):
    """Recovery: the elbow dropped out to his side, the stick forearm up, the fist pulled down beside
    his head; the sleeve droops off the upper arm."""
    arm = V.limb([((40.6, 48.8 + dy), (33.6, 51.6 + dy), 1.55, 1.45), ((33.6, 51.6 + dy), (31.4, 42.5 + dy), 1.45, 1.3)],
                 knobs=((33.6, 51.8 + dy, 1.9),))
    sl = V.sleeve([(44.2, 43.4 + dy), (41.4, 44.6 + dy), (38.6, 46.6 + dy), (35.4, 48.6 + dy), (34, 50.8 + dy),
                   (37.8, 53.6 + dy), (41.4, 52.6 + dy), (42.8, 49.8 + dy), (43.4, 46.8 + dy)],
                  [(35, 51 + dy), (38, 53 + dy)])
    band = B.amap(BAND, 28, 40 + dy)
    fist = B.amap(FIST_UP, 27, 29 + dy)
    return [(arm, True), (sl, True), (band, False), (fist, False)]


#THE POP

def flash(cx, cy):
    """spawn_pop frame 0 in his palette: a small keylined flower puff with a pale cross on it."""
    shape = B.ellipse(cx, cy, 2.6, 2.4)
    for ddx, ddy in ((0, -2.2), (2.2, 0), (0, 2.2), (-2.2, 0)):
        shape |= B.ellipse(cx + ddx, cy + ddy, 1.6, 1.6)
    p = B.fill(shape, 'P')
    B.rim(p, 'Q', -1, 0)
    B.rim(p, 'Q', 0, -1)
    B.rim(p, 'q', 1, 0)
    B.rim(p, 'q', 0, 1, only='P')
    cxr, cyr = int(round(cx)), int(round(cy))
    for d in (-2, -1, 1, 2):
        for q in ((cxr + d, cyr), (cxr, cyr + d)):
            if q in p:
                p[q] = 'Y'
    p[(cxr, cyr)] = 'W'
    return p


PUFF = B.rows_of([".QP.", "QPPq", "PPqq", ".qq."])
PUFF_S = B.rows_of(["QP", "Pq"])
STAR_S = B.rows_of([
    "...k...",
    "..kYk..",
    "kkkYOkk",
    "kYYOOok",
    ".kOOOk.",
    ".kokok.",
    ".kk.kk.",
])


def dispersal():
    """spawn_pop's last frame in his palette: the cloud broken into loose puffs drifting outward
    (no keylines: they are dissolving), sparkles, and a small star on top. Build coordinates."""
    out, fx = {}, set()
    for (x, y, big) in ((17, 6, True), (21, 12, True), (29, 14, False), (37, 12, True), (42, 6, True),
                        (22, 2, False), (39, 1, False)):
        m = B.amap(PUFF if big else PUFF_S, x, y)
        out.update(m)
        fx |= set(m)
    out.update(B.amap(STAR_S, 28, 0))
    for (gx, gy) in ((15, 1), (46, 11), (26, 17)):
        for q, k in (((gx, gy), 'W'), ((gx + 1, gy), 'Q'), ((gx - 1, gy), 'Q'), ((gx, gy + 1), 'Q'),
                     ((gx, gy - 1), 'Q')):
            out[q] = k
            fx.add(q)
    return out, fx


def speed_trail(dy):
    """Streaks left behind the rising fist along its swing (free-floating, no keylines)."""
    out = {}
    for (x0, y0, n, k) in ((24, 24, 7, 'W'), (26, 29, 5, 'Q'), (22, 30, 4, 'Q'), (28, 34, 3, 'W')):
        for i in range(n):
            out[(x0, y0 + dy + i)] = k
    return out


#FRAMES

def lower_body(cv, crouch=False):
    cv.stamp(crouch_legs() if crouch else V.legs())
    for s in V.shoes():
        cv.stamp(s, outline=False)


def far_side(cv, dip):
    for part, ol in V.far_arm_box_low():
        cv.stamp(B.shift(part, 0, dip), outline=ol)


def torso(cv, dip, head_dx):
    """The thin neck (leaning with the head), the hanging tee and the dandruff, dipped by `dip`."""
    cv.stamp(B.shift(V.neck(head_dx), 0, dip))
    cv.stamp(B.shift(V.shirt(1), 0, dip))
    B.dandruff(cv.px, 0, dip)


def box_low(cv, dip):
    cv.stamp(B.rec('box', B.shift(J.box_part(*BOX_AT), 0, dip)), outline=False)
    cv.stamp(B.rec('hand_far', B.shift(B.amap(V.LOW_HAND, *LOW_HAND_AT), 0, dip)), outline=False)


def build_windup():
    dip = 2
    hx, hy = HEAD_AT[0] + 1, HEAD_AT[1] + dip
    cv = B.Canvas(96, 96)
    lower_body(cv, crouch=True)
    far_side(cv, dip)
    torso(cv, dip, hx)
    cv.stamp(B.rec('head', HD.head('grit', hx, hy)), outline=False)
    arm = near_arm_cocked(dip)
    B.rec('fist', arm[3][0])
    B.stamp_all(cv, arm)
    box_low(cv, dip)
    return cv, set()


def build_punch():
    dip = -1
    cv = B.Canvas(96, 96)
    lower_body(cv)
    far_side(cv, dip)
    torso(cv, dip, HEAD_AT[0])
    cv.stamp(B.rec('head', HD.head('shout', HEAD_AT[0], HEAD_AT[1] + dip)), outline=False)
    trail = speed_trail(dip)
    for q, k in trail.items():
        if q not in cv.px:
            cv.px[q] = k
    arm = raised_arm(dip, 3)
    B.rec('fist', arm[4][0])
    B.stamp_all(cv, arm)
    cv.stamp(B.rec('pop', flash(31, 9 + dip + 3 - 1)))
    box_low(cv, dip)
    return cv, set(trail)


def build_pump():
    """The approved v2 fist-pump, re-built part for part like jv2_frames.build(1) so its anchor points
    can be recorded; make_frames checks it matches v2's frame exactly and ships v2's frame."""
    cv = B.Canvas(96, 96)
    lower_body(cv)
    far_side(cv, 0)
    torso(cv, 0, HEAD_AT[0])
    cv.stamp(B.rec('head', HD.head('shout', *HEAD_AT)), outline=False)
    cv.stamp(B.rec('pop', J.pop_cloud()))
    cv.stamp(B.rec('star', B.amap(B.rows_of(J.STAR), 27, 0)), outline=False)
    for q, k in J.GLINTS.items():
        cv.px[q] = k
    arm = raised_arm()
    B.rec('fist', arm[4][0])
    B.stamp_all(cv, arm)
    box_low(cv, 0)
    return cv, set(J.GLINTS)


def build_recover():
    dip = 0
    cv = B.Canvas(96, 96)
    lower_body(cv)
    far_side(cv, dip)
    torso(cv, dip, HEAD_AT[0])
    cv.stamp(B.rec('head', HD.head('grin', HEAD_AT[0], HEAD_AT[1] + dip)), outline=False)
    pop, fx = dispersal()
    B.rec('pop', pop)
    for q, k in pop.items():
        cv.px[q] = k
    arm = near_arm_yes(dip)
    B.rec('fist', arm[3][0])
    B.stamp_all(cv, arm)
    box_low(cv, dip)
    return cv, fx


def builders():
    return [build_windup, build_punch, build_pump, build_recover]


def frames_info():
    return B.make_frames(builders(), approved=APPROVED)


def frames():
    return [(px, fx) for px, fx, _info in frames_info()]


if __name__ == '__main__':
    assert raised_arm() == V.raised_arm(), 'the copied raised arm no longer matches v2'
    for i, (px, fx) in enumerate(frames()):
        st = B.stats(B.to_image(px))
        a = B.audit(px, fx)
        print(i, st, 'gaps', a['gaps'], 'lone', a['lone'], 'holes', a['holes'], 'keys', a['keys'])
