"""Danny in SIDE view, facing screen-right: the Sumo Headbutt (the user's brief and reference of
2026-09-24, images/24.png: the body a horizontal missile, the head leading, both arms pressed along his
sides with the fists at the belt, the legs straight back together, the soles trailing).

The approved rig is front view only, so the profile is new drawing, made the rig's way: every part is
one keylined form sculpted with its muscles (sumo_lib.sculpt), stamped back to front so the keylines
cut the black separations between forms. Every part hangs on a joint chain (hip -> torso -> neck /
shoulder -> elbow; hip -> thigh -> knee -> ankle) and is posed as GEOMETRY, then lit in the frame,
so however far he turns (the torpedo is horizontal) the light stays at the upper left. The painted
parts (the knit ribs of the mawashi, the collar's rims, the chain, the rope) are drawn from each
part's own coordinates through the pose.

The head is drawn upright in profile with pixel-authored features and its knit, lit with the light
turned against the head's turn (fight.lit, the juggle's rule), then turned into place: an exact
quarter turn is lossless (jkit.rot90); any other angle is RotSprite with the features lifted off and
put back crisp.

Identity carried over: the knit beanie over the whole skull in blue / light-blue ribs with its deep
cuff and ear flap, the heavy slit eye, the broad nose, the red collar scrap and the gold chain, the
mawashi in the beanie's ribs with the gold rope, the navy apron with its gold fringe, the white wrist
and ankle wraps, bare feet. No kabuki paint.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fight as FT  # noqa: E402
import anim  # noqa: E402
import sumo_lib as L  # noqa: E402
from sumo_lib import Canvas, spoly, sculpt, shade, capsule, ellipse, taper_line, amap, SKIN  # noqa: E402
import danny_v2 as D  # noqa: E402
import lib as jl  # noqa: E402

K = FT.K
SKINSET = set(SKIN)


# ------------------------------------------------------------------ JOINTS
class J:
    """A joint frame: local p -> parent(at + R(deg) p). Screen degrees, clockwise positive."""

    def __init__(self, deg=0.0, at=(0.0, 0.0), parent=None):
        self.deg, self.at, self.parent = deg, at, parent

    def __call__(self, p):
        a = math.radians(self.deg)
        c, s = math.cos(a), math.sin(a)
        q = (self.at[0] + p[0] * c - p[1] * s, self.at[1] + p[0] * s + p[1] * c)
        return self.parent(q) if self.parent else q

    def inverse(self, q):
        if self.parent:
            q = self.parent.inverse(q)
        a = math.radians(-self.deg)
        c, s = math.cos(a), math.sin(a)
        dx, dy = q[0] - self.at[0], q[1] - self.at[1]
        return (dx * c - dy * s, dx * s + dy * c)

    def angle(self):
        return self.deg + (self.parent.angle() if self.parent else 0.0)


def P(pts, xf, iters=2):
    return spoly([xf(p) for p in pts], iters)


LIFT = 0.0


def lit_sculpt(*a, **kw):
    """sumo_lib.sculpt with the pose's fill added to its exposure."""
    kw['exposure'] = kw.get('exposure', 0.0) + LIFT
    return sculpt(*a, **kw)


def seg(xf, p0, p1, r0, r1, bellies=(), exposure=0.04, sigma=4.0):
    """A capsule limb segment from local p0 to p1, posed, then sculpted (lit in the frame)."""
    a, b = xf(p0), xf(p1)
    return FT.limb(a, b, r0, r1, exposure=exposure + LIFT, sigma=sigma, bellies=list(bellies))


# ------------------------------------------------------------------ THE TORSO (hip joint at 0, 0)
TORSO = [(-14, -80), (-25, -76), (-32, -67), (-36.5, -55), (-38, -42), (-37, -28), (-33.5, -16), (-28, -6),
         (-20, 2), (26, 3), (37, -3), (45, -12), (48.5, -24), (46.5, -36), (39, -43), (35, -50), (30, -56),
         (21, -60), (12, -61), (4, -64), (-4, -74)]
PEC = [(11, -66), (24, -61), (32, -52), (31, -45), (21, -41), (11, -45), (7, -56)]
BELLY = [(6, -44), (24, -45), (40, -40), (48, -26), (44, -11), (32, -2), (14, -2), (4, -18)]
LATS = [(-18, -80), (-27, -70), (-32, -54), (-32, -36), (-26, -24), (-18, -36), (-15, -58)]
TRAP = [(-13, -80), (-22, -75), (-20, -66), (-8, -66), (-5, -74)]
PEC_LINE = [(10, -46), (18, -42.5), (26, -43.5), (31, -46)]
BELLY_LINE = [(30, -5), (38, -8), (43, -14)]            # the belly's underside turning under
LAT_LINE = [(-24, -66), (-28, -50), (-28, -34)]
DELT_GROOVE = [(5, -69), (4, -58), (2, -47)]             # between the deltoid's front and side heads
NAVEL = [(46, -25), (44, -24)]
GLUTE_LINE = [(-30, 16), (-22, 19.5), (-13, 17)]         # the buttock's fold over the thigh
KNEE_LINE = [(-8.0, 39.0), (-4.0, 43.0)]                 # thigh frame: the crease behind the knee
CALF_LINE = [(-5.5, 3.0), (-6.5, 11.0), (-5.0, 18.0)]    # knee frame: the calf's outer head
BELT = [(-35, -19), (-8, -17), (18, -13), (34, -10), (40.5, -4), (38, 5.5), (16, 7), (-10, 7), (-33, 5.5),
        (-38.5, -3), (-37.5, -12)]
BELT_AXIS, BELT_R = 0.0, 36.0
BUTT = [(-34, 2), (-37, 9), (-35, 17), (-28, 21), (-17, 21), (-9, 15), (-11, 6)]
APRON = [(31, 4), (39, 3), (40.5, 8), (40.5, 22), (38.5, 28), (32, 28), (31, 16)]
COLLAR = [(18, -62), (13, -68), (3, -72.5), (-9, -75.5), (-17, -73.5), (-15.5, -66.5), (-6, -64.5), (4, -60.5),
          (12, -55.5), (19, -55)]
CHAIN = [(5, -60), (11, -56), (18, -52.5), (25, -51), (31, -50)]
NECK = (6.0, -58.0)
SHOULDER = (-5.0, -54.0)
DELT = [(-4, -76), (10, -72), (17, -61), (17, -48), (11, -38), (-1, -33), (-14, -36), (-21, -47), (-21, -62),
        (-15, -72)]
DELT_FRONT = [(2, -72), (13, -63), (15, -48), (7, -39), (0, -45), (-1, -61)]

# ------------------------------------------------------------------ LIMBS (each in its own joint frame)
UPPER = ((0.0, 8.0), (0.0, 33.0), 12.5, 10.5)          # shoulder frame: hangs along +y
ELBOW = (0.0, 35.0)
FORE = ((0.0, 0.0), (0.0, 23.0), 10.0, 7.8)            # elbow frame
WRIST = (0.0, 23.0)
ARM_LINE = [(-1.0, 12.0), (-1.5, 22.0), (-1.0, 31.0)]   # the biceps / triceps split, shoulder frame
FIST = [(-9, 20), (7, 20), (10, 25.5), (10, 34), (6, 39), (-5, 39.5), (-10, 33)]   # elbow frame
FIST_LINES = [((-6, 30), (8, 30)), ((-5, 34.5), (7.5, 34.5))]
# an open hand, flung loose (the recoil): the palm edge-on, the fingers splayed along the forearm's line
HAND_OPEN = [(-8, 20), (6, 20), (9.5, 26), (10.5, 34), (9.5, 42), (6.5, 46), (2, 46.5), (-2.5, 44), (-5.5, 38),
             (-9, 31)]
THUMB_OPEN = [(-8, 24), (-13, 28), (-15.5, 33), (-13.5, 36), (-9, 33)]
FINGER_SPLITS = [((0.5, 33), (1.5, 45)), ((4.5, 32), (6, 44))]
THIGH = ((0.0, 4.0), (0.0, 40.0), 19.0, 13.5)          # hip frame
KNEE = (0.0, 42.0)
CALF = ((0.0, 0.0), (0.0, 27.0), 12.5, 7.8)            # knee frame
ANKLE = (0.0, 29.0)
FOOT = [(-7, -3), (-8.5, 3), (-6.5, 8.5), (4, 10), (16, 10), (24, 9.5), (27.5, 7), (26.5, 3.5), (18.5, 0.5),
        (8, -3.5), (0, -6)]                             # ankle frame: toes along +x, the sole at +y
TOE_SPLITS = [((21.5, 4.5), (21.5, 9)), ((24.5, 5), (24.5, 9))]

# ------------------------------------------------------------------ THE HEAD (neck pivot at 0, 0)
H_FACE = [(19, -19), (21, -16), (20.5, -13), (23, -11), (26.5, -7), (28, -4), (26, -2), (23, -1.5), (23.5, 0.5),
          (21, 2), (22.5, 3.5), (21.5, 7), (17, 10.5), (9, 12.5), (0, 12), (-9, 8), (-15, 1), (-18, -10),
          (-12, -22), (2, -25)]
H_CHEEK = [(4, -14), (14, -12), (19, -6), (17, 3), (9, 7), (0, 5), (-4, -4)]
H_CROWN = [(20, -19.5), (20.5, -26), (17.5, -33), (11, -39.5), (2.5, -43), (-7.5, -43), (-16.5, -40), (-24, -34),
           (-28.5, -26), (-30, -17), (-29, -9), (-25.5, -4), (-17, -4), (-5, -18), (10, -22)]
H_CUFF = [(21.5, -26.5), (22, -20.5), (21, -17.5), (12.5, -18), (3.5, -17.5), (-2.5, -14.5), (-5.5, -8), (-8, -2),
          (-14.5, 0), (-21, -1), (-26, -4), (-29, -10), (-30, -18), (-28.5, -26), (-15.5, -26.5), (2.5, -27),
          (13.5, -27.5)]
H_AXIS = -4.0                  # the head's vertical axis (the ribs converge on it)
HC = (64, 64)                  # where the head's pivot sits on its own render canvas

# features, pixel-authored for the upright profile (head-local top-left, keys: sumo_lib.PAL)
EYES_P = {
    # the glare: the heavy lid's edge slanting down to the front, a sliver of white, the pupil forward
    'glare': ((13, -16), ["kkk....",
                          "33kkkk.",
                          ".kWWUUk",
                          "..kkkkk",
                          "...333."]),
    # screwed shut (the bonk): the lids clamped into a chevron pointing forward
    'squeeze': ((13, -16), ["kkk....",
                            "..kkkk.",
                            ".....kk",
                            "..kkkk.",
                            "kkk...."]),
    # surprise (the recoil): the eye thrown open round a small pupil
    'wide': ((14, -17), [".kkkk.",
                         "kWWWWk",
                         "kWWUUk",
                         "kWWWWk",
                         ".kkkk."]),
    # dazed: an X
    'x': ((14, -17), ["kk...kk",
                      "..k.k..",
                      "...k...",
                      "..k.k..",
                      "kk...kk"]),
}
MOUTHS_P = {
    # gritted: the clenched teeth seen from the side, lips pulled back
    'grit': ((15, -3), ["kkkkkkk",
                        "kWWkWWk",
                        "khhkhhk",
                        ".kkkkk."]),
    # the kiai: the jaw open, teeth and tongue
    'shout': ((15, -2), ["kkkkkkk",
                         "kWWWWkk",
                         "k1111k.",
                         "k1rrr1k",
                         ".kkkkk."]),
    # the bonk: a wobbling 'ow' (teeth clenched, the lip pushed out)
    'ow': ((15, -3), ["kkkkkkk",
                      "kWWWWWk",
                      "khhhhhk",
                      ".kkkkk."]),
}
NOSTRIL = [(22, -3), (23, -3), (23, -4)]
JOWL_LINE = [(13, 3), (8, 7), (2, 8.5)]
JAW_LINE = [(14.5, 9), (8, 11), (0, 10.5), (-7, 7)]      # the double chin's underside, as the front view's


def head_render(eyes='glare', mouth='grit', deg=0.0):
    """The FACE alone (skin, nostril, jowl, eyes, mouth), upright in its own canvas (pivot at HC),
    lit for a turn of `deg`. The beanie is drawn afterwards in the frame (knit_head), so its ribs
    stay crisp at any angle. Returns (key map, face mask, feature pixels)."""
    ox, oy = HC
    at = lambda pts: [(x + ox, y + oy) for (x, y) in pts]  # noqa: E731
    with FT.lit(deg):
        sd = FT.shadow()
        cv = FT.FreeCanvas()
        face = spoly(at(H_FACE))
        cheek = spoly(at(H_CHEEK))
        cv.stamp(sculpt(face, [(cheek, 3.0, 0.3)], sigma=6.0, exposure=0.16, bulge=0.55), shadow=sd)
        feats = {}
        for (x, y) in NOSTRIL:
            cv.px[(x + ox, y + oy)] = 'k'
            feats[(x + ox, y + oy)] = 'k'
        taper_line(cv.px, at(JOWL_LINE), 'k', taper_key='3', taper=2, only=SKINSET)
        taper_line(cv.px, at(JAW_LINE), '3', only=SKINSET)
        for table, key in ((EYES_P, eyes), (MOUTHS_P, mouth)):
            (fx, fy), rows = table[key]
            for q, k in amap(rows, fx + ox, fy + oy).items():
                cv.px[q] = k
                feats[q] = k
    return cv.px, face, feats


def knit_head(pts, hxf, rref=27.0, sigma=9, iters=2):
    """A beanie part (crown or cuff) drawn in the frame: its outline posed, its tones ranked on the
    posed shape (lit where it now faces), each pixel's rib taken from where it came from on the
    upright head (the meridians round the head's own vertical axis, as danny_v2.meridians)."""
    local = spoly(pts, iters)
    rows = {}
    for (x, y) in local:
        lo, hi = rows.get(y, (x, x))
        rows[y] = (min(lo, x), max(hi, x))
    widest = max((hi - lo + 1) / 2.0 for lo, hi in rows.values())
    mask = spoly([hxf(p) for p in pts], iters)
    idx = L.rank(mask, D.KNIT_DIST, sigma=sigma)

    def rib(x, y):
        lx, ly = hxf.inverse((x, y))
        yy = int(round(ly))
        if yy not in rows:
            yy = min(rows, key=lambda r: abs(r - yy))
        lo, hi = rows[yy]
        r = max((hi - lo + 1) / 2.0, 0.62 * widest)
        t = max(-1.0, min(1.0, (lx - H_AXIS) / r))
        return math.asin(t) * rref + 1.0
    return L.knit(idx, D.PATTERN, rib, D.KNIT)


# The features are turned WITH the face by RotSprite (a lifted feature can only turn by quarter turns,
# which laid the torpedo's eye on its side); at a quarter turn the whole face turns losslessly.
LIFT_FEATURES = False


def head_placed(eyes, mouth, world_deg, neck_world, sd):
    """The head turned by world_deg and moved so its pivot sits on the neck: the face (lit against
    the turn, then turned: a quarter turn exactly, any other angle by RotSprite with the features
    kept crisp), then the beanie drawn over it in the frame."""
    px, face, feats = head_render(eyes, mouth, world_deg)
    if world_deg % 360:
        import types
        px = FT._dparts().relight_face(types.SimpleNamespace(deg=world_deg, face=face, px=px))
    to = (int(round(neck_world[0])), int(round(neck_world[1])))
    turns = int(round(world_deg / 90.0))
    if abs(world_deg - 90 * turns) < 1e-6:
        out = K.rot90(px, turns, HC, to)
    else:
        M = K.turn_squash(world_deg)
        lifted = [(dict(feats), '5')] if LIFT_FEATURES else []
        out = K.rekeyline(K.affine_with_features(px, M, HC, to, lifted, turns=turns))
    hxf = J(world_deg, (float(to[0]), float(to[1])))
    cv = FT.FreeCanvas(pad=160)
    cv.px = dict(out)
    cv.stamp(knit_head(H_CROWN, hxf), shadow=sd)
    cv.stamp(knit_head(H_CUFF, hxf, sigma=4, iters=1))
    L.clean_lone(cv.px)
    return cv.px


# ------------------------------------------------------------------ POSES
DEFAULT = dict(
    hip=(100.0, 90.0),     # where the hip joint is in the frame
    lean=0.0,              # the torso's turn about the hip (90: horizontal, head to the right)
    head=0.0,              # the head's own turn on the neck
    arm=0.0, elbow=0.0,    # near arm: upper arm about the shoulder, forearm about the elbow
    thigh=0.0, knee=0.0, foot=0.0,
    far=None,              # the far leg's (thigh, knee, foot) and its offset, or None for legs together
    eyes='glare', mouth='grit', hand='fist',
    squash=None,           # (sx, sy, about): the bonk, applied to the posed body as geometry
    lift=0.0,              # a fill on every part (a hunched pose turns most of him away from the key light)
    flutter=0.0,           # the apron's flap in the wind (degrees about its top)
)


class Pose:
    def __init__(self, spec):
        s = dict(DEFAULT, **spec)
        self.s = s
        sq = s['squash']
        base = None
        if sq:
            sx, sy, about = sq

            class _S:
                def __call__(self, p):
                    return (about[0] + (p[0] - about[0]) * sx, about[1] + (p[1] - about[1]) * sy)

                def inverse(self, q):
                    return (about[0] + (q[0] - about[0]) / sx, about[1] + (q[1] - about[1]) / sy)

                def angle(self):
                    return 0.0
            base = _S()
        self.torso = J(s['lean'], s['hip'], base)
        self.neck = J(s['head'], NECK, self.torso)
        self.upper = J(s['arm'], SHOULDER, self.torso)
        self.fore = J(s['elbow'], ELBOW, self.upper)
        self.thigh = J(s['thigh'], (0.0, 0.0), self.torso)
        self.calf = J(s['knee'], KNEE, self.thigh)
        self.foot = J(s['foot'], ANKLE, self.calf)
        far = s['far']
        if far:
            (ft, fk, ff), off = far
            self.fthigh = J(ft, off, self.torso)
            self.fcalf = J(fk, KNEE, self.fthigh)
            self.ffoot = J(ff, ANKLE, self.fcalf)


def leg(cv, thigh, calf, foot, sd, dark=0.0, wrap=True):
    """Foot, then the calf over it with the ankle wrap, then the thigh over the calf's top: its
    rounded end is the knee (the approved legs are stacked the same way)."""
    cv.stamp(lit_sculpt(P(FOOT, foot), [], sigma=3.0, exposure=0.06 + dark, tilt=(0.0, -0.3)), shadow=sd)
    for p0, p1 in TOE_SPLITS:
        taper_line(cv.px, [foot(p0), foot(p1)], 'k', only=SKINSET)
    (a, b, r0, r1) = CALF
    cv.stamp(seg(calf, a, b, r0, r1, bellies=[(0.08, 0.6, 9.0, -3.5), (0.05, 0.8, 5.0, 4.0)], exposure=0.05 + dark,
                 sigma=4.5), shadow=sd, under=1)
    if wrap:
        cv.stamp(anim.wrap_band(FT.wrap_at(calf(a), calf(b), 0.88, 8.4, length=6.0), 1))
    taper_line(cv.px, [calf(p) for p in CALF_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    (a, b, r0, r1) = THIGH
    cv.stamp(seg(thigh, a, b, r0, r1, bellies=[(0.1, 0.8, 12.0, 4.0), (0.15, 0.75, 10.0, -4.0)],
                 exposure=0.05 + dark, sigma=6.0), shadow=sd, under=1)
    taper_line(cv.px, [thigh(p) for p in KNEE_LINE], 'k', only=SKINSET)


def knit_band(mask, xf, axis, r, rref=40.0, sigma=5):
    """The rig's knit on a posed band: tones ranked on the posed shape, each pixel's rib from where it
    came from in the band's own frame (vertical ribs round the hips, crowding at its turning edges)."""
    idx = L.rank(mask, D.KNIT_DIST, sigma=sigma)

    def rib(x, y):
        lx, ly = xf.inverse((x, y))
        t = max(-1.0, min(1.0, (lx - axis) / r))
        return math.asin(t) * rref + 1.0
    return L.knit(idx, D.PATTERN, rib, D.KNIT)


def rope(xf, x0=-33.0, x1=35.0, y=4.5):
    pts = [xf((x0 + (x1 - x0) * i / 12.0, y)) for i in range(13)]
    path = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        sg = L.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by)))
        if path and sg[0] == path[-1]:
            sg = sg[1:]
        path.extend(sg)
    part = {}
    for i, (x, y) in enumerate(path):
        ph = i % 3
        part[(x, y)] = ('Y', 'o', 'O')[ph]
        part.setdefault((x, y + 1), ('o', 'O', 'g')[ph])
    return part


def collar(xf):
    part = {p: 'R' for p in P(COLLAR, xf, 1)}
    jl.rim(part, 'r', 0, -1, depth=1)
    jl.rim(part, 'M', 0, 1, depth=1)
    jl.rim(part, 'M', 1, 0, depth=1)
    return part


def chain(xf):
    return G_chain([xf(p) for p in CHAIN])


def G_chain(pts):
    import gear as G
    return G.chain(pts)


def apron(xf, flutter):
    """The apron seen edge-on from the side: its navy face in a sliver with the light-blue border,
    blown back by `flutter` degrees about its top; the gold fringe at its hem."""
    top = ((31 + 40.5) / 2.0, 4.0)
    fl = J(flutter, top, xf) if flutter else None

    def f(p):
        return fl((p[0] - top[0], p[1] - top[1])) if fl else xf(p)
    mask = spoly([f(p) for p in APRON], 1)
    part = {q: 'V' for q in mask}
    jl.rim(part, 'X', -1, 0, depth=1)
    jl.rim(part, 'U', 1, 0, depth=1)
    jl.rim(part, 'B', 0, 1, depth=1)
    fringe = {}
    for i in range(4):
        a = f((32.5 + i * 2.2, 28.5))
        b = f((32.5 + i * 2.2, 32.5 - (i % 2)))
        for j, q in enumerate(L.line(int(round(a[0])), int(round(a[1])), int(round(b[0])), int(round(b[1])))):
            fringe[q] = 'Y' if j == 0 else 'o'
    return part, fringe


def build(spec, canvas=None):
    pz = Pose(spec)
    s = pz.s
    global LIFT
    LIFT = s['lift']
    cv = canvas or FT.FreeCanvas(pad=160)
    sd = FT.shadow()
    T = pz.torso
    # the far leg, in the body's shadow
    if s['far']:
        leg(cv, pz.fthigh, pz.fcalf, pz.ffoot, sd, dark=-0.16)
    # the torso: one form, pec, belly, lats and traps sculpted on it
    body = P(TORSO, T)
    lay = [(P(PEC, T), 2.4, 0.3), (P(BELLY, T), 5.0, 0.42), (P(LATS, T), 3.0, 0.18), (P(TRAP, T), 3.0, 0.12)]
    cv.stamp(lit_sculpt(body, lay, sigma=8.0, bulge=0.7, exposure=0.03), shadow=sd, under=1)
    taper_line(cv.px, [T(p) for p in PEC_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    taper_line(cv.px, [T(p) for p in BELLY_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    taper_line(cv.px, [T(p) for p in LAT_LINE], 'k', taper_key='3', taper=3, only=SKINSET)
    for q in NAVEL:
        x, y = T(q)
        if cv.px.get((int(round(x)), int(round(y)))) in SKINSET:
            cv.px[(int(round(x)), int(round(y)))] = 'k'
    cv.stamp(lit_sculpt(P(BUTT, T), [], sigma=4.5, exposure=0.02), shadow=sd, under=1)
    taper_line(cv.px, [T(p) for p in GLUTE_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    # the near leg, then the mawashi over the top of both thighs, its rope, the apron at its front
    leg(cv, pz.thigh, pz.calf, pz.foot, sd)
    belt = P(BELT, T)
    cv.stamp(knit_band(belt, T, BELT_AXIS, BELT_R), shadow=sd)
    cv.stamp(rope(T), shadow=sd)
    ap, fr = apron(T, s['flutter'])
    cv.stamp(ap, shadow=sd)
    cv.stamp(fr)
    # the collar and chain at the neck
    cv.stamp(chain(T))
    cv.stamp(collar(T), shadow=sd)
    # the near shoulder, then the head, then the rest of the near arm
    cv.stamp(lit_sculpt(P(DELT, T), [(P(DELT_FRONT, T), 2.6, 0.25)], sigma=6.5, exposure=0.06), shadow=sd, under=1)
    taper_line(cv.px, [T(p) for p in DELT_GROOVE], 'k', taper_key='3', taper=2, only=SKINSET)
    hpx = head_placed(s['eyes'], s['mouth'], pz.neck.angle(), pz.neck((0.0, 0.0)), sd)
    hb = set(hpx)
    for q in {(x + sd[0], y + sd[1]) for (x, y) in hb} - hb:
        k = cv.px.get(q)
        if k is not None and k != 'k':
            cv.px[q] = L.DARKER.get(k, k)
    for q, k in hpx.items():
        if cv.inside(q):
            cv.px[q] = k
    (a, b, r0, r1) = UPPER
    cv.stamp(seg(pz.upper, a, b, r0, r1, bellies=[(0.15, 0.85, 8.0, 3.5), (0.1, 0.75, 7.5, -3.5)], exposure=0.04,
                 sigma=4.5), shadow=sd, under=1)
    taper_line(cv.px, [pz.upper(p) for p in ARM_LINE], 'k', taper_key='3', taper=2, only=SKINSET)
    (a, b, r0, r1) = FORE
    cv.stamp(seg(pz.fore, a, b, r0, r1, bellies=[(0.05, 0.55, 8.0, 3.0), (0.1, 0.6, 6.5, -3.0)], exposure=0.05),
             shadow=sd, under=1)
    FT.crease(cv.px, pz.fore(a), pz.fore(b), 0.12, 0.62, 0.8, taper=3)
    cv.stamp(anim.wrap_band(FT.wrap_at(pz.fore(a), pz.fore(b), 0.86, 8.0, length=6.0), 1))
    if s['hand'] == 'open':
        cv.stamp(lit_sculpt(P(THUMB_OPEN, pz.fore), [], sigma=2.0, exposure=0.05), shadow=sd)
        cv.stamp(lit_sculpt(P(HAND_OPEN, pz.fore), [], sigma=3.0, exposure=0.07), shadow=sd)
        for p0, p1 in FINGER_SPLITS:
            taper_line(cv.px, [pz.fore(p0), pz.fore(p1)], 'k', only=SKINSET)
    else:
        cv.stamp(lit_sculpt(P(FIST, pz.fore), [], sigma=3.0, exposure=0.05), shadow=sd)
        for p0, p1 in FIST_LINES:
            taper_line(cv.px, [pz.fore(p0), pz.fore(p1)], 'k', only=SKINSET)
    L.clean_lone(cv.px)
    return cv, pz
