"""Danny's new moves (the user's picks of 2026-09-29): the ring-out BELLY BUMP and the parried fifth slam's
BOUNCE onto his back, drawn from the approved rigs.

The approved rigs are IMPORTED READ-ONLY (never edited, their exports never run):
  art_source/danny_sumo_v2/fight_side.py   the side-view body (the approved headbutt torpedo's rig)
  art_source/danny_sumo_v2/fight_tuck.py   the front-view Sumo Smash tuck
  art_source/danny_sumo_v2/fight.py        the lighting, RotSprite and the audit kit
Bytecode writing is switched off before they are imported, so not even a .pyc lands in their folders.

What this file adds, all new drawing made the rig's way (one keylined sculpted form per part, lit AFTER it
is posed so the key light stays at the upper left however far he turns):
  * build_side(spec): fight_side.build with more joints. With every new option at its default it IS
    fight_side.build (check_same() proves it on the approved headbutt frames). New options:
      far_arm    (upper arm, elbow) degrees: the far arm, drawn first and one step darker (the far leg's rule)
      far_hand   'fist' | 'open'
      belly      the belly's front pushed out (< 0, the charge's thrust) or flattened back (> 0, the contact
                 squash), the lost depth bulging it up and down: a deformation of the approved outline
      ripple     n wobble arcs drawn on the belly (the slap, the contact), in keyline fading to dark skin
      stars      the daze: [(x, y, size)] keylined gold stars, stamped last, in frame coordinates
      eyes/mouth also the new profile maps below
  * world(): the joints given as WORLD angles (thigh, calf, foot, upper arm, forearm), converted to the
    rig's parent-relative ones, so a pose reads as it looks.
  * new profile expressions for the side head: 'daze' (a spiral), 'lid' (the heavy sleepy lid, his
    signature), mouths 'tongue' (knocked silly), 'smug' (the tell's grin), 'huff' (a puff of effort).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
AS = os.path.dirname(HERE)
RIG = os.path.join(AS, 'danny_sumo_v2')
if RIG not in sys.path:
    sys.path.insert(0, RIG)

import fight as FT  # noqa: E402
import fight_side as SD  # noqa: E402
import fight_tuck as TK  # noqa: E402
import fight_sheets as FS  # noqa: E402
import anim  # noqa: E402
import sumo_lib as L  # noqa: E402
from sumo_lib import spoly, taper_line, SKIN  # noqa: E402

K = FT.K
SKINSET = set(SKIN)
J = SD.J
P = SD.P


# ------------------------------------------------------------------ NEW PROFILE EXPRESSIONS
# Head-local, top-left of each map, in the approved profile's frame (fight_side.EYES_P / MOUTHS_P: the eye
# sits at (13..20, -17..-12) under the cuff, the mouth at (15..21, -3..2)). Keys are sumo_lib.PAL's.
NEW_EYES = {
    # dazed: a little spiral in the eye's white, the lid gone slack over it
    'daze': ((13, -17), ["..kkkk.",
                         ".kWWWWk",
                         "kWkkkWk",
                         "kWkWkWk",
                         "kWWkWWk",
                         ".kkkkk."]),
    # his signature: the heavy sleepy lid down over a slit (the front view's EYE_L, in profile)
    'lid': ((13, -16), ["3333...",
                        "6666k..",
                        "kkkkkkk",
                        ".kkkkk.",
                        "..444.."]),
}
NEW_MOUTHS = {
    # knocked silly: the jaw hanging, the tongue lolling out over the lip
    'tongue': ((15, -3), ["kkkkkkk",
                          "k1111k.",
                          "k11rrrk",
                          ".kkrrrk",
                          "...krk.",
                          "....k.."]),
    # the tell: a smug closed smirk, its corner (at the back, he faces right) hooked up into the jowl
    'smug': ((14, -4), ["k......",
                        ".kk....",
                        "...kkkk",
                        "...444."]),
    # a huff of effort: lips pushed out round a held breath
    'huff': ((15, -3), ["..kkk..",
                        ".k564k.",
                        ".k443k.",
                        "..kkk.."]),
}


def install_faces():
    """Add the new maps to fight_side's tables, in memory only (the file is not edited)."""
    for k, v in NEW_EYES.items():
        SD.EYES_P.setdefault(k, v)
    for k, v in NEW_MOUTHS.items():
        SD.MOUTHS_P.setdefault(k, v)


install_faces()


# ------------------------------------------------------------------ WORLD ANGLES -> RIG ANGLES
def world(lean=0.0, head=0.0, arm=None, fore=None, thigh=None, calf=None, foot=None, far_leg=None,
          far_arm=None, far_off=(6.0, 0.0), **kw):
    """A side pose given in WORLD degrees (0 = pointing straight down, + = swung toward his back, which is
    screen-left while he faces right). Returns a spec for build_side.
      arm, fore          the near upper arm's and forearm's world angles
      thigh, calf, foot  the near leg's; foot is the sole's tilt (0 flat, + toes up)
      far_leg            (thigh, calf, foot) world angles of the far leg
      far_arm            (upper, fore) world angles of the far arm
    """
    s = dict(kw)
    s['lean'] = lean
    s['head'] = head
    if arm is not None:
        s['arm'] = arm - lean
        s['elbow'] = (fore if fore is not None else arm) - arm
    if thigh is not None:
        s['thigh'] = thigh - lean
        s['knee'] = (calf if calf is not None else thigh) - thigh
        c = calf if calf is not None else thigh
        s['foot'] = (0.0 if foot is None else -foot) - c
    if far_leg is not None:
        ft, fc, ff = far_leg
        s['far'] = ((ft - lean, fc - ft, (0.0 if ff is None else -ff) - fc), far_off)
    if far_arm is not None:
        fa, ff2 = far_arm
        s['far_arm'] = (fa - lean, ff2 - fa)
    return s


# ------------------------------------------------------------------ THE BELLY
def belly_xf(amount, x0=12.0, x1=49.0, yc=-24.0):
    """A deformation of the torso's own points: the belly's front moved back by `amount` of its depth past
    x0 (a flattening against whatever it hit), or forward for amount < 0 (the thrust); the depth it loses
    it gains in height, bulging up and down about yc. Smooth: nothing behind x0 moves."""
    if not amount:
        return None

    def f(p):
        x, y = p
        if x <= x0:
            return p
        t = min(1.0, (x - x0) / (x1 - x0))
        w = t * t * (3 - 2 * t)
        nx = x - amount * w * (x - x0) * 0.42
        ny = yc + (y - yc) * (1.0 + amount * w * 0.24)
        return (nx, ny)
    return f


def dpts(pts, f):
    return [f(p) for p in pts] if f else list(pts)


# ------------------------------------------------------------------ STARS (the daze)
STAR_BIG = ["....k....",
            "...kyk...",
            "...kYk...",
            "kkkkYkkkk",
            "kyyYYYYok",
            ".kyYYYok.",
            "..kYYYk..",
            ".kYokoYk.",
            ".kok.kok.",
            ".kk...kk."]
STAR_SMALL = ["...k...",
              "..kyk..",
              "kkkYkkk",
              "kyYYYok",
              ".kYYok.",
              ".kokok.",
              ".kk.kk."]


def star(cx, cy, big=True):
    rows = STAR_BIG if big else STAR_SMALL
    h, w = len(rows), len(rows[0])
    x0, y0 = int(round(cx)) - w // 2, int(round(cy)) - h // 2
    return {(x0 + c, y0 + r): ch for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != '.'}


def daze_ring(cx, cy, rx, ry, phase, n=3):
    """n stars round an ellipse over his head, `phase` degrees round it: (back half, front half) key maps,
    the back ones smaller (farther). 30 degrees a frame loops in 4 frames with three stars."""
    back, front = {}, {}
    for i in range(n):
        a = math.radians(phase + 360.0 * i / n)
        x, y = cx + rx * math.cos(a), cy + ry * math.sin(a)
        near = math.sin(a) > 0
        (front if near else back).update(star(x, y, big=near))
    return back, front


# ------------------------------------------------------------------ THE SIDE BUILD
DEFAULT = dict(SD.DEFAULT, far_arm=None, far_hand='fist', belly=0.0, ripple=0, ripple_at=(40.0, -24.0),
               stars_back=None, stars_front=None, fist_open=False, wobble=0, wobble_span=(-44.0, 2.0), smack=None,
               marks=(), collar_low=False, sweat=(), shock=False, stomp=False, collar_band=False)


def far_arm(cv, pz, s, sd):
    """The far arm: the near arm's parts on a shoulder just behind the near one, one step darker."""
    ua, el = s['far_arm']
    T = pz.torso
    up = J(ua, (-8.0, -56.0), T)
    fo = J(el, SD.ELBOW, up)
    dark = -0.16
    (a, b, r0, r1) = SD.UPPER
    cv.stamp(SD.seg(up, a, b, r0, r1, bellies=[(0.15, 0.85, 8.0, 3.5), (0.1, 0.75, 7.5, -3.5)], exposure=0.04 + dark,
                    sigma=4.5), shadow=sd, under=1)
    (a, b, r0, r1) = SD.FORE
    cv.stamp(SD.seg(fo, a, b, r0, r1, bellies=[(0.05, 0.55, 8.0, 3.0), (0.1, 0.6, 6.5, -3.0)], exposure=0.05 + dark),
             shadow=sd, under=1)
    cv.stamp(anim.wrap_band(FT.wrap_at(fo(a), fo(b), 0.86, 8.0, length=6.0), -1))
    hand(cv, fo, s['far_hand'], sd, dark)


def hand(cv, fo, kind, sd, dark=0.0):
    if kind == 'open':
        cv.stamp(SD.lit_sculpt(P(SD.THUMB_OPEN, fo), [], sigma=2.0, exposure=0.05 + dark), shadow=sd)
        cv.stamp(SD.lit_sculpt(P(SD.HAND_OPEN, fo), [], sigma=3.0, exposure=0.07 + dark), shadow=sd)
        for p0, p1 in SD.FINGER_SPLITS:
            taper_line(cv.px, [fo(p0), fo(p1)], 'k', only=SKINSET)
    else:
        cv.stamp(SD.lit_sculpt(P(SD.FIST, fo), [], sigma=3.0, exposure=0.05 + dark), shadow=sd)
        for p0, p1 in SD.FIST_LINES:
            taper_line(cv.px, [fo(p0), fo(p1)], 'k', only=SKINSET)


def ripple(cv, T, n, at, bf):
    """Wobble arcs on the belly after a smack: open keyline arcs round `at` (torso-local), fading to dark skin,
    only on skin. They follow the belly's deformation."""
    cx, cy = at
    for i in range(n):
        r = 7.0 + 6.0 * i
        pts = []
        for j in range(9):
            a = math.radians(125 + 110 * j / 8.0)          # the arc opening toward the belly's front
            p = (cx + r * math.cos(a) * 0.55, cy + r * math.sin(a))
            pts.append(T(bf(p) if bf else p))
        taper_line(cv.px, pts[1:-1], 'k', taper_key='3', taper=2, only=SKINSET)


def build_side(spec, canvas=None):
    """fight_side.build with the new joints and options (see the module note). Returns (canvas, pose)."""
    s = dict(DEFAULT, **spec)
    base = {k: v for k, v in s.items() if k in SD.DEFAULT}
    pz = SD.Pose(base)
    SD.LIFT = s['lift']
    cv = canvas or FT.FreeCanvas(pad=160)
    sd = FT.shadow()
    T = pz.torso
    bf = belly_xf(s['belly'])
    if s['stars_back']:
        cv.stamp(s['stars_back'])
    if s['far_arm']:
        far_arm(cv, pz, s, sd)
    if s['far']:
        SD.leg(cv, pz.fthigh, pz.fcalf, pz.ffoot, sd, dark=-0.16)
    body = P(dpts(SD.TORSO, bf), T)
    lay = [(P(SD.PEC, T), 2.4, 0.3), (P(dpts(SD.BELLY, bf), T), 5.0, 0.42), (P(SD.LATS, T), 3.0, 0.18),
           (P(SD.TRAP, T), 3.0, 0.12)]
    cv.stamp(SD.lit_sculpt(body, lay, sigma=8.0, bulge=0.7, exposure=0.03), shadow=sd, under=1)
    taper_line(cv.px, [T(p) for p in SD.PEC_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    taper_line(cv.px, [T(p) for p in dpts(SD.BELLY_LINE, bf)], 'k', taper_key='3', taper=2, only=SKINSET)
    taper_line(cv.px, [T(p) for p in SD.LAT_LINE], 'k', taper_key='3', taper=3, only=SKINSET)
    for q in dpts(SD.NAVEL, bf):
        x, y = T(q)
        if cv.px.get((int(round(x)), int(round(y)))) in SKINSET:
            cv.px[(int(round(x)), int(round(y)))] = 'k'
    if s['ripple']:
        ripple(cv, T, s['ripple'], s['ripple_at'], bf)
    cv.stamp(SD.lit_sculpt(P(SD.BUTT, T), [], sigma=4.5, exposure=0.02), shadow=sd, under=1)
    taper_line(cv.px, [T(p) for p in SD.GLUTE_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    SD.leg(cv, pz.thigh, pz.calf, pz.foot, sd)
    belt = P(SD.BELT, T)
    cv.stamp(SD.knit_band(belt, T, SD.BELT_AXIS, SD.BELT_R), shadow=sd)
    cv.stamp(SD.rope(T), shadow=sd)
    ap, fr = SD.apron(T, s['flutter'])
    cv.stamp(ap, shadow=sd)
    cv.stamp(fr)
    if s['collar_low']:
        cv.stamp(chain_low(T))
        cv.stamp(collar_low(T), shadow=sd)
    else:
        cv.stamp(SD.chain(T))
        cv.stamp(SD.collar(T), shadow=sd)
    cv.stamp(SD.lit_sculpt(P(SD.DELT, T), [(P(SD.DELT_FRONT, T), 2.6, 0.25)], sigma=6.5, exposure=0.06), shadow=sd,
             under=1)
    taper_line(cv.px, [T(p) for p in SD.DELT_GROOVE], 'k', taper_key='3', taper=2, only=SKINSET)
    hpx = SD.head_placed(s['eyes'], s['mouth'], pz.neck.angle(), pz.neck((0.0, 0.0)), sd)
    hb = set(hpx)
    for q in {(x + sd[0], y + sd[1]) for (x, y) in hb} - hb:
        k = cv.px.get(q)
        if k is not None and k != 'k':
            cv.px[q] = L.DARKER.get(k, k)
    for q, k in hpx.items():
        if cv.inside(q):
            cv.px[q] = k
    hxf = J(pz.neck.angle(), pz.neck((0.0, 0.0)))
    if s['collar_band']:
        collar_band(cv, hb, pz, T)
    for p in s['sweat']:
        x, y = hxf(p)
        cv.stamp(L.amap(FF_SWEAT, int(round(x)) - 2, int(round(y)) - 3), outline=False)
    if s['shock']:
        shock(cv, hxf)
    (a, b, r0, r1) = SD.UPPER
    cv.stamp(SD.seg(pz.upper, a, b, r0, r1, bellies=[(0.15, 0.85, 8.0, 3.5), (0.1, 0.75, 7.5, -3.5)], exposure=0.04,
                    sigma=4.5), shadow=sd, under=1)
    taper_line(cv.px, [pz.upper(p) for p in SD.ARM_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    (a, b, r0, r1) = SD.FORE
    cv.stamp(SD.seg(pz.fore, a, b, r0, r1, bellies=[(0.05, 0.55, 8.0, 3.0), (0.1, 0.6, 6.5, -3.0)], exposure=0.05),
             shadow=sd, under=1)
    FT.crease(cv.px, pz.fore(a), pz.fore(b), 0.12, 0.62, 0.8, taper=3)
    cv.stamp(anim.wrap_band(FT.wrap_at(pz.fore(a), pz.fore(b), 0.86, 8.0, length=6.0), 1))
    hand(cv, pz.fore, s['hand'], sd)
    if s['stars_front']:
        cv.stamp(s['stars_front'])
    if s['wobble']:
        wobble(cv, T, s['wobble'], s['wobble_span'], bf)
    if s['smack']:
        smack(cv, pz.fore, s['smack'])
    for seg_ in s['marks']:
        mark(cv, seg_)
    if s['stomp']:
        stomp_marks(cv, pz.foot)
    L.clean_lone(cv.px)
    return cv, pz


def check_same():
    """With no new option set, build_side must BE the approved fight_side.build: every approved headbutt
    frame is rebuilt both ways and compared texel for texel."""
    out = []
    for (name, spec, ms) in FS.SHEETS['danny_sumo_headbutt']['frames']:
        a = SD.build(spec['side'])[0].px
        b = build_side(spec['side'])[0].px
        out.append((name, a == b))
    return out


if __name__ == '__main__':
    print('build_side == fight_side.build on the approved headbutt:', check_same())


# ------------------------------------------------------------------ REACHING A POINT
def arm_ik(lean, hip, target, bend=1, reach=30.0, upper=35.0, shoulder=None):
    """World angles (upper arm, forearm) that put the near hand's middle `reach` along the forearm on `target`
    (frame coordinates), for a torso at `hip` leaning `lean`. bend +1 / -1 picks the elbow's side."""
    T = J(lean, hip)
    sx, sy = T(shoulder or SD.SHOULDER)
    tx, ty = target
    dx, dy = tx - sx, ty - sy
    d = max(1e-6, min(math.hypot(dx, dy), (upper + reach) * 0.999))
    base = math.atan2(dy, dx)
    c = (upper * upper + d * d - reach * reach) / (2 * upper * d)
    a = math.acos(max(-1.0, min(1.0, c)))
    au = base + bend * a
    ex, ey = sx + upper * math.cos(au), sy + upper * math.sin(au)
    af = math.atan2(ty - ey, tx - ex)
    return math.degrees(au) - 90.0, math.degrees(af) - 90.0


def torso_pt(lean, hip, p, belly=0.0):
    """A torso-local point (after the belly deformation) in frame coordinates."""
    bf = belly_xf(belly)
    return J(lean, hip)(bf(p) if bf else p)


# ------------------------------------------------------------------ MOTION MARKS (keyline, drawn only on empty texels)
def _front_outline(bf, y0, y1):
    """The torso's front edge between torso-local rows y0 and y1 (the belly), as a polyline with outward normals."""
    pts = dpts(SD.TORSO, bf)
    n = len(pts)
    out = []
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        for j in range(6):
            t = j / 6.0
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            if y0 <= y <= y1 and x > 8:
                ln = math.hypot(bx - ax, by - ay) or 1.0
                out.append((x, y, -(by - ay) / ln, (bx - ax) / ln))     # outward: the outline runs anticlockwise
    return out


def wobble(cv, T, n, span, bf):
    """The belly still wobbling: n arcs just outside its front edge, following it, in keyline. Drawn only where
    nothing is (they read as motion round the silhouette, not as marks on it)."""
    edge_ = _front_outline(bf, span[0], span[1])
    edge_.sort(key=lambda e: e[1])
    for i in range(n):
        d = 4.0 + 4.0 * i
        pts = [T((x + nx * d, y + ny * d)) for (x, y, nx, ny) in edge_]
        m = len(pts)
        keep = pts[int(m * (0.18 + 0.08 * i)):int(m * (0.82 - 0.08 * i))]
        path = []
        for (ax, ay), (bx, by) in zip(keep, keep[1:]):
            for q in L.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by))):
                if not path or path[-1] != q:
                    path.append(q)
        for q in path:
            if q not in cv.px:
                cv.px[q] = 'k'


def smack(cv, fore, spec):
    """Impact ticks round the hand where it lands: (n, radius, from_deg, to_deg) in the hand's own frame angle."""
    n, r, a0, a1 = spec
    c = fore((0.0, 32.0))
    ang = math.degrees(math.atan2(fore((0.0, 40.0))[1] - c[1], fore((0.0, 40.0))[0] - c[0]))
    for i in range(n):
        a = math.radians(ang + a0 + (a1 - a0) * i / max(1, n - 1))
        p0 = (c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)
        p1 = (c[0] + math.cos(a) * (r + 5), c[1] + math.sin(a) * (r + 5))
        for q in L.line(int(round(p0[0])), int(round(p0[1])), int(round(p1[0])), int(round(p1[1]))):
            if q not in cv.px:
                cv.px[q] = 'k'


def mark(cv, seg_):
    """A free motion line in frame coordinates: ((x0, y0), (x1, y1)), keyline, only on empty texels."""
    (x0, y0), (x1, y1) = seg_
    for q in L.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
        if q not in cv.px:
            cv.px[q] = 'k'


# ------------------------------------------------------------------ PLANTED FEET
THIGH_LEN, CALF_LEN, SOLE = 42.0, 29.0, 10.0


def calf_for(drop, thigh, sign=1):
    """The calf's world angle that puts the sole `drop` texels below the hip joint for a thigh at `thigh` (world
    degrees): 42 cos t + 29 cos c + 10 = drop. sign +1 swings the shin back (a knee bent forward), -1 forward."""
    c = (drop - SOLE - THIGH_LEN * math.cos(math.radians(thigh))) / CALF_LEN
    c = max(-1.0, min(1.0, c))
    return sign * math.degrees(math.acos(c))


# ------------------------------------------------------------------ THE COLLAR, WORN LOW ENOUGH TO SHOW IN PROFILE
# The approved side view seats the collar scrap and the chain where the double chin covers them: in the headbutt
# only a fleck of the chain shows, under the lips. Here the band is seated at the base of the neck, its front a few
# texels under the jaw (as the front view shows it under the jowls), and the chain hangs on the chest below it.
# Torso-local, drawn before the head, so the head still covers whatever it overlaps.
COLLAR_LOW = [(-4, -45), (-2, -48.5), (8, -51), (16, -53.5), (24, -55.5), (25.5, -48), (23.5, -41.5), (14, -41),
              (6, -42.5), (-2, -43.5)]
CHAIN_LOW = [(-2, -40), (6, -39), (14, -37.5), (22, -36.5), (29, -36), (33, -36.5)]


def collar_low(xf):
    part = {p: 'R' for p in P(COLLAR_LOW, xf, 1)}
    import lib as jl
    jl.rim(part, 'r', 0, -1, depth=1)
    jl.rim(part, 'M', 0, 1, depth=1)
    jl.rim(part, 'M', -1, 0, depth=1)
    return part


def chain_low(xf):
    return SD.G_chain([xf(p) for p in CHAIN_LOW])


# ------------------------------------------------------------------ COMIC MARKS ON THE HEAD
import fight_faces as _FF  # noqa: E402  (the approved sweat drop, reused)
FF_SWEAT = _FF.SWEAT


def shock(cv, hxf):
    """Surprise ticks: three short keyline strokes fanning out over the crown (head-local, turned with the head),
    drawn only on empty texels."""
    for (a0, a1) in (((-14, -48), (-18, -56)), ((2, -52), (2, -61)), ((17, -47), (22, -55))):
        (x0, y0), (x1, y1) = hxf(a0), hxf(a1)
        for q in L.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))):
            if q not in cv.px:
                cv.px[q] = 'k'


def stomp_marks(cv, foot):
    """The stomp's impact: short keyline strokes kicked up either side of the planted sole (foot-local: the sole
    runs along +x at y 10), only on empty texels."""
    for (x0, y0, x1, y1) in ((-11, 8, -17, 1), (-12, 11, -20, 8), (30, 8, 36, 1), (31, 11, 39, 8)):
        (ax, ay), (bx, by) = foot((x0, y0)), foot((x1, y1))
        for q in L.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by))):
            if q not in cv.px:
                cv.px[q] = 'k'


# ------------------------------------------------------------------ THE COLLAR BAND UNDER THE JOWL (take 2, 2026-09-30)
# The user approved "the collar showing in profile"; the low collar above still hid under his double chin in most
# poses (Danny D measured 101 collar-red texels over the whole bump sheet, against ~270 a frame in the front idle).
# This draws the scrap the way the front view shows it wrapping round the side: a red band hugging the underside of
# his jaw, lit rim on top, the torn dark edge under it, a keyline below, from under the ear flap to the throat.
# It is laid AFTER the head but only on the body under it (never on the head, never past the silhouette), so the
# silhouette, the anchors and everything else stay as they are; the chain is re-laid under the band.
BAND_LX = (-11.0, 21.0)        # head-local span: from under the ear flap's front to the front of the throat
BAND_T = 6                     # rows of band under the jaw (the front view shows about 6-8 under the jowls)
BAND_NICKS = {-6: 1, -5: 1, 4: 1, 5: 2, 6: 1, 14: 1, 15: 1}   # torn lower edge, head-local x -> rows missing
GOLD_KEYS = set('YoOyg')


def collar_band(cv, head, pz, T):
    to = pz.neck((0.0, 0.0))
    hxf = J(pz.neck.angle(), (float(int(round(to[0]))), float(int(round(to[1])))))
    # the jaw's underside in the head's own frame: the lowest head texel per head-local column
    jaw = {}
    for q in head:
        lx, ly = hxf.inverse((q[0], q[1]))
        c = int(round(lx))
        if ly > jaw.get(c, -1e9):
            jaw[c] = ly

    def boundary(q):
        return any((q[0] + dx, q[1] + dy) not in cv.px for dx, dy in K.N4)

    band = {}
    xs = [q for q in head]
    x0, x1 = min(q[0] for q in xs) - 4, max(q[0] for q in xs) + 4
    y0, y1 = min(q[1] for q in xs) - 4, max(q[1] for q in xs) + BAND_T + 6
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            q = (x, y)
            if q in head or q not in cv.px:
                continue
            if cv.px[q] == 'k' and boundary(q):
                continue                                # the silhouette's own keyline stays
            lx, ly = hxf.inverse(q)
            c = int(round(lx))
            if not (BAND_LX[0] <= lx <= BAND_LX[1]) or c not in jaw:
                continue
            d = ly - jaw[c]
            t = BAND_T - BAND_NICKS.get(c, 0)
            if cv.px[q] in GOLD_KEYS:
                t = BAND_T                              # no torn nick over the old chain: no gold fleck left inside
            if 0.0 < d <= t + 0.5:
                band[q] = d
    if not band:
        return
    part = {}
    for q, d in band.items():
        if d <= 1.5:
            k = 'r'
        elif d <= BAND_T - 1.0:
            k = 'R'
        else:
            k = 'M'
        part[q] = k
    # the band turns away from the light toward the back of the neck: its far end a tone down
    for q in part:
        lx, _ = hxf.inverse(q)
        if lx < BAND_LX[0] + 4 and part[q] == 'R':
            part[q] = 'M'
    # re-lay the chain under the band (it hangs below the collar, as in the front view)
    chain = {q: k for q, k in chain_low(T).items() if q not in head and q not in part and q in cv.px
             and not (cv.px[q] == 'k' and boundary(q))}
    for q, k in part.items():
        cv.px[q] = k
    for q, k in chain.items():
        cv.px[q] = k
    # no gold fleck left boxed in by the band (a chain texel the band closed round): it takes the band's colour
    for _ in range(2):
        for q in [q for q, k in cv.px.items() if k in GOLD_KEYS and q not in head]:
            nb = [part.get((q[0] + dx, q[1] + dy)) for dx, dy in K.N4]
            nb = [n for n in nb if n]
            if len(nb) >= 3:
                cv.px[q] = max(sorted(set(nb)), key=nb.count)
                part[q] = cv.px[q]
                chain.pop(q, None)
    # keyline round the band and the chain where they meet skin (never on the head, never past the silhouette)
    laid = set(part) | set(chain)
    for (x, y) in list(laid):
        for dx, dy in K.N4:
            n = (x + dx, y + dy)
            if n not in laid and n not in head and cv.px.get(n) in SKINSET:
                cv.px[n] = 'k'
