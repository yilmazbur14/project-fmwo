"""Parts the standing finale sheets share: arms in new poses (each in the fitted tee's short sleeve),
hands, and the pink energy of his zap. Build coordinates, facing screen-right.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfs_base as B  # noqa: E402

V = B.V
JF = B.JF


#HANDS

# his left hand (screen-right, in shade) thrust out, pointing: the index finger out along the line of
# the arm, the thumb over it, the other three curled under. The wrist joins at the left.
POINT_R = [
    ".kkkk.......",
    ".kcdckkkkkk.",
    "kbcddddddddk",
    "kbccbkkkkkk.",
    "kabcbak.....",
    ".kabak......",
    "..kkk.......",
]
POINT_TIP = (10, 2)            # the fingertip's texel in POINT_R

# his left hand raised, open, fingers spread and hooked (the zap's wind-up), in shade; the wrist at
# the bottom. jfc_front's WAVE mirrored and taken a step down the skin ramp.
CLAW_R = [
    "...k.k.k.",
    "..kdkckck",
    "..kckckck",
    "..kccccbk",
    "kkcccccbk",
    "kccccccbk",
    "kbccccbbk",
    ".kbbccbk.",
    "..kbcck..",
    "..kbcbk..",
]
CLAW_WRIST = (4.5, 9)

# his left fist raised (the arms-up), in shade: the approved raised fist (jordan.raised_arm) mirrored,
# a step down the ramp
_FIST_UP = [
    ".kkkkkkk.",
    "kebebdbdk",
    "kebdbdbck",
    "kdbdbdbck",
    "kddddddck",
    "kkkkkdcbk",
    "keeedkcbk",
    ".kddckbk.",
    "..kkkkk..",
]
_DOWN = {'e': 'd', 'd': 'c', 'c': 'b', 'b': 'a', 'a': 'a'}
FIST_UP_FAR = [''.join(_DOWN.get(ch, ch) for ch in reversed(r)) for r in _FIST_UP]


def at(rows, x0, y0):
    return B.close_gaps(B.amap(B.rows_of(rows), int(round(x0)), int(round(y0))))


#ARMS

def near_arm_tense(dx=0, dy=0):
    """His right arm rigid and held off his side, the elbow bowed out, the fist clenched by his hip in
    the pink wristband (jordan_rage's)."""
    root = (B.NEAR_ROOT[0] + dx, B.NEAR_ROOT[1] + dy)
    el = (33.6 + dx, 55.8 + dy)
    wr = (34.6 + dx, 61.4 + dy)
    arm = B.arm([(root, el, 1.55, 1.45), (el, wr, 1.45, 1.3)], knobs=((el[0], el[1] + 0.2, 1.9),))
    sl = B.near_sleeve(root, el)
    band = B.amap(B.rows_of(B.BAND), 31 + dx, 58 + dy)
    fist = B.amap(B.rows_of(B.FIST_HANG), 31 + dx, 61 + dy)
    return [(arm, True), (sl, True), (band, False), (fist, False)], (31 + dx, 61 + dy)


def far_arm_tense(dx=0, dy=0):
    root = (B.FAR_ROOT[0] + dx, B.FAR_ROOT[1] + dy)
    el = (64.2 + dx, 55.4 + dy)
    wr = (64.4 + dx, 61.2 + dy)
    arm = B.arm([(root, el, 1.5, 1.4), (el, wr, 1.4, 1.3)], knobs=((el[0], el[1] + 0.2, 1.7),), far=True)
    sl = B.far_sleeve(root, el)
    fist = B.amap(B.rows_of(B.FIST_HANG_FAR), 61 + dx, 61 + dy)
    return [(arm, True), (sl, True), (fist, False)], (61 + dx, 61 + dy)


RAISED_NEAR_ROOT = (40.8, 47.5)          # v2's raised arm
RAISED_FAR_ROOT = (58.4, 47.5)           # janim_taunt's far arm up


def far_raised_cuff(arm):
    """The sleeve on his raised left arm: the rig's raised cuff (jv2_body.RAISED_CUFF, the skinny
    build's since 2026-09-28) mirrored onto the far shoulder (about x = 49.6, as janim_taunt mirrors
    v2's), in his shadow: no lit rim, the dark red of its underside, the trim across the opening."""
    pts = B.V.RAISED_CUFF
    part = B.fill(B.poly([(99.2 - x, y) for (x, y) in pts]), 'R')
    B.rim(part, 'V', 1, 0)
    B.rim(part, 'v', 0, 1, only='RV')
    B.stroke(part, [(59, 47), (58, 49)], 'V', only='R')
    top = min(y for (x, y) in part)
    for (x, y) in list(part):
        if y == top:
            part[(x, y)] = '1'
    return part


def far_arm_raised(elbow, wrist):
    """His left arm raised: out of the fitted cuff at his shoulder, a bony elbow, the forearm up."""
    arm = B.arm([(RAISED_FAR_ROOT, elbow, 1.55, 1.45), (elbow, wrist, 1.45, 1.3)],
                knobs=((elbow[0], elbow[1] + 0.2, 1.8),), far=True)
    for (x, y) in list(arm):                   # the raised arm catches the light on its inner side
        if arm[(x, y)] == 'c' and x <= elbow[0] and y <= elbow[1] + 2:
            arm[(x, y)] = 'd'
    sl = far_raised_cuff(arm)
    through = {q: k for q, k in arm.items() if q[1] in (41, 42)}
    return [(arm, True), (sl, True), (through, False)]


def far_arm_out(elbow, wrist):
    """His left arm thrust out from the shoulder, in the fitted short sleeve."""
    arm = B.arm([(B.FAR_ROOT, elbow, 1.5, 1.4), (elbow, wrist, 1.4, 1.3)], knobs=((elbow[0], elbow[1], 1.6),),
                far=True)
    sl = B.far_sleeve(B.FAR_ROOT, elbow, length=4.2)
    return [(arm, True), (sl, True)]


#THE ZAP'S ENERGY (effects: no keyline)

def orb(cx, cy, r):
    """A glowing ball of his pink: a white-hot core, a pale ring, pink, and the dark pink edge that
    keeps it off a pale floor."""
    out = {}
    for y in range(int(cy - r - 2), int(cy + r + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            d = math.hypot(x - cx, y - cy)
            if d <= r * 0.42:
                out[(x, y)] = 'W'
            elif d <= r * 0.72:
                out[(x, y)] = 'Q'
            elif d <= r + 0.05:
                out[(x, y)] = 'P'
            elif d <= r + 0.75:
                out[(x, y)] = 'q'
    return out


def bolt(x0, y0, dirs, key='Q', tip='W'):
    """A crackle: a jagged one-pixel line stepping through `dirs` ((dx, dy) steps), white at the tip."""
    out = {}
    x, y = x0, y0
    for i, (dx, dy) in enumerate(dirs):
        x, y = x + dx, y + dy
        out[(x, y)] = tip if i == len(dirs) - 1 else key
    return out


ARCS = {
    # jagged one-pixel arcs, as (start direction, steps...): each leaves the orb's rim and zigzags out
    'burst': [((1, -1), (1, 0), (1, -1), (0, -1), (1, -1), (1, 0)),
              ((1, 1), (1, 0), (1, 1), (1, 1), (0, 1), (1, 1)),
              ((0, -1), (-1, -1), (0, -1), (1, -1), (0, -1)),
              ((0, 1), (-1, 1), (0, 1), (-1, 1), (0, 1)),
              ((1, 0), (1, 0), (1, 1), (1, 0), (1, -1), (1, 0), (1, 0)),
              ((-1, -1), (-1, 0), (-1, -1), (0, -1))],
    'hold': [((1, -1), (1, 0), (1, -1), (0, -1)), ((1, 1), (0, 1), (1, 1), (1, 0)),
             ((1, 0), (1, 0), (1, 1), (1, 0)), ((0, -1), (-1, -1), (0, -1))],
    'gather': [((-1, -1), (0, -1), (-1, -1), (0, -1)), ((1, -1), (1, 0), (1, -1), (0, -1)),
               ((1, 1), (0, 1), (1, 0)), ((-1, 1), (-1, 0), (-1, 1))],
    'up': [((-1, -1), (0, -1), (-1, -1), (0, -1), (-1, 0)), ((1, -1), (1, -1), (0, -1), (1, 0)),
           ((0, -1), (1, -1), (0, -1), (-1, -1), (0, -1)), ((-1, 0), (-1, -1), (-1, 0), (-1, 1)),
           ((1, 0), (1, 1), (1, 0))],
}
SPARKS = {
    'burst': [(7, -5, 'W'), (8, 4, 'Q'), (-3, -7, 'Q'), (5, 7, 'W'), (10, -1, 'Q')],
    'hold': [(5, -4, 'Q'), (6, 3, 'W')],
    'gather': [(-5, -2, 'Q'), (4, -5, 'W'), (-2, 5, 'Q'), (5, 3, 'Q')],
    'up': [(-5, -3, 'W'), (4, -6, 'Q'), (5, 1, 'W')],
}


def crackle(cx, cy, r, which):
    """The orb with crackling arcs leaving its rim, and loose sparks further out. `which` picks the
    set, so the frames of a gesture differ."""
    out = orb(cx, cy, r)
    ox, oy = int(round(cx)), int(round(cy))
    for dirs in ARCS[which]:
        sx, sy = dirs[0]
        start = (ox + int(round(sx * (r + 0.5))), oy + int(round(sy * (r + 0.5))))
        for q, k in bolt(start[0] - sx, start[1] - sy, dirs).items():
            out.setdefault(q, k)
    for (x, y, k) in SPARKS[which]:
        out.setdefault((ox + x, oy + y), k)
    return out


def arc_between(a, b, amp=2, key='Q'):
    """A crackle bridging two points: a jagged line from a to b, kicked up and down `amp` pixels on
    alternate steps, white where it kinks."""
    out = {}
    (x0, y0), (x1, y1) = a, b
    n = max(abs(x1 - x0), abs(y1 - y0))
    kick = [0, -amp, -1, amp - 1, 0, -amp + 1, 1, -amp]
    prev = None
    for i in range(n + 1):
        t = i / float(n)
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t)) + kick[(i // 3) % len(kick)]
        if prev is not None:
            for q in B.line(prev[0], prev[1], x, y):
                out.setdefault(q, key)
        if i % 3 == 0 and 0 < i < n:
            out[(x, y)] = 'W'
        prev = (x, y)
    return out


def wisps(cx, cy):
    """What is left of it: two pink wisps curling up off the fingertip, fading."""
    out = {}
    for (x, y, k) in ((0, 0, 'P'), (1, -1, 'Q'), (1, -2, 'P'), (0, -3, 'Q'), (0, -4, 'q'),
                      (3, -1, 'Q'), (4, -2, 'P'), (4, -3, 'q'), (-1, -2, 'q')):
        out[(cx + x, cy + y)] = k
    return out
