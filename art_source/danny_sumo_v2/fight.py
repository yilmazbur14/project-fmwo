"""Danny's fight poses (the user's brief of 2026-09-24), front view, from the approved sumo rig.

build(spec) is anim.build_frame with more joints. It draws in the same order from the same approved
parts, and with every new option at its default it reproduces the approved frames pixel for pixel
(check_same() proves it on every export). Nothing in anim.py or the parts it uses is edited: the new
options are new stages and new parts in this file, and new face maps in fight_faces.py.

New spec keys, on top of anim.DEFAULT:
  legs       also 'airv' (the Sumo Smash: seated, knees up, lifted off the mat, rear lowest),
             'launch' (the jump's push-off: the legs driven straight) and 'tachi' (the push's low
             crouch: knees out and forward, weight on the balls of the feet)
  leg_deg    'airv': how far each seated leg swings up about the hip (degrees)
  sit_dy     'sit' / 'airv': the seated legs' own drop (the defeat's are drawn for a body 10 px down)
  arms       also 'push' (both palms driven low and forward, the tug-of-war), 'knee' (a hand on the
             knee, the jump's crouch)
  cock_rot   {side: (shoulder_deg, elbow_deg)}: the cocked arm raised or lowered about the shoulder,
             its forearm about the elbow (side 1 = viewer's left)
  push_at    {side: (x, y, scale)}: where a 'push' palm is (viewer's-left x; the right is mirrored)
  eyes       a name, or (left, right) for two different eyes
  head_dx    the head's own sideways move
  puff       the cheeks blown out round a mouthful, 0..1
  jaw        the chin dropped by n px (the spit)
  sweat      [(x, y)] sweat drops (their top-left texel)
  drool      a thread of drool from the sleeping mouth
  bubble     also 5, the sleep's biggest
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import anim  # noqa: E402  the approved pose builder (used, never edited)
import fight_faces as FF  # noqa: E402  installs the new maps into anim.EYES / anim.MOUTHS
import sumo_lib as L  # noqa: E402
from sumo_lib import Canvas, spoly, sculpt, amap, taper_line, mirror_pts, ellipse, capsule, shade, MIR, SKIN  # noqa: E402,F401
import face as F  # noqa: E402
import gear as G  # noqa: E402
import hands as HN  # noqa: E402
import limbs as LB  # noqa: E402
import torso as T  # noqa: E402
import danny_v2 as D  # noqa: E402
import slap as SL  # noqa: E402
import lib as jl  # noqa: E402

FW, FH = anim.FW, anim.FH
SKINSET = set(SKIN)
anim.BUBBLE_R.setdefault(5, 8.4)

DEFAULT = dict(anim.DEFAULT, leg_deg=0.0, sit_dy=0, cock_rot=None, push_at=None, head_dx=0, puff=0.0, jaw=0,
               sweat=(), drool=False, head_tilt=0.0)

AS = os.path.dirname(HERE)


def _load(name, path):
    import importlib.util
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# The juggle's kit (RotSprite, the rank-preserving face relight, the audit helpers), loaded by file
# path and never put on sys.path: several art_source folders have modules with the same names.
K = _load('jkit', os.path.join(AS, 'josh_juggle', 'jkit.py'))


def shadow():
    """The cast-shadow offset, read at stamp time (a turned render swaps it; see lit())."""
    return anim.SHADOW


# ------------------------------------------------------------------ LIGHT FOR A TURNED PART
LIGHT0 = tuple(float(v) for v in L.LIGHT)
_DEFAULTS = L.intensity.__defaults__
_SHADOW0 = anim.SHADOW


def _turn(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


class lit:
    """Render a part that is about to be turned by `deg` (screen degrees, clockwise): inside this
    block the key light and the cast-shadow offset are turned the OTHER way, so once the part is
    turned it is lit from the upper left like everything else. The rig's own volume is kept; only
    the normal turns relative to the light (the juggle's rule, danny_juggle/dparts.Render)."""

    def __init__(self, deg):
        self.deg = deg

    def __enter__(self):
        lx, ly = _turn(LIGHT0[:2], -self.deg)
        sx, sy = _turn(_SHADOW0, -self.deg)
        L.intensity.__defaults__ = (_DEFAULTS[0], _DEFAULTS[1], _DEFAULTS[2], (lx, ly, LIGHT0[2]), _DEFAULTS[4])
        anim.SHADOW = (int(round(sx)), int(round(sy)))
        return self

    def __exit__(self, *exc):
        L.intensity.__defaults__ = _DEFAULTS
        anim.SHADOW = _SHADOW0
        return False


def rot_pt(p, deg, pivot):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    dx, dy = p[0] - pivot[0], p[1] - pivot[1]
    return (pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c)


def rot_pts(pts, deg, pivot):
    if not deg:
        return list(pts)
    return [rot_pt(p, deg, pivot) for p in pts]


def shift(part, dx, dy):
    return anim.shift(part, dx, dy)


# ------------------------------------------------------------------ PALMS AT ANY ANGLE
def palm(cx, cy, s=1.0, thumb=-1, exposure=0.0, fan=1.0, thumb_reach=15.0, deg=0.0):
    """slap.palm, turned by deg about its centre (the fingers lean with the forearm). At deg 0 it is
    slap.palm exactly."""
    if not deg:
        return SL.palm(cx, cy, s, thumb, exposure, fan, thumb_reach)
    a = math.radians(deg)
    c, sn = math.cos(a), math.sin(a)

    def at(x, y):                         # a point given relative to the palm's centre, unscaled
        x, y = x * s, y * s
        return (cx + x * c - y * sn, cy + x * sn + y * c)

    P = lambda pts: spoly([at(x, y) for (x, y) in pts])  # noqa: E731
    heel = P([(-8.5, 8.5), (-9.8, 1.5), (-8.8, -5.5), (8.8, -5.5), (9.8, 1.5), (8.5, 8.5), (0, 10.5)])
    fingers = []
    for dx, lean, ln, r in ((-6.2, -3.6, 8.8, 2.3), (-2.1, -1.2, 11.0, 2.4), (2.2, 1.2, 10.4, 2.35),
                            (6.3, 3.6, 7.6, 2.1)):
        if thumb > 0:
            dx, lean = -dx, -lean
        fingers.append(capsule(at(dx, -4.5), at(dx + lean * fan, -(4.5 + ln)), r * s, (r - 0.3) * s))
    th = capsule(at(thumb * 8.6, 3.0), at(thumb * thumb_reach, -3.5), 2.6 * s, 2.2 * s)
    layers = []
    hp = shade(heel, sigma=3.5 * s, exposure=0.08 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP)
    for i in range(-6, 6):
        q = at(i, -1.0 + abs(i) * 0.12)
        q = (int(round(q[0])), int(round(q[1])))
        if q in hp:
            hp[q] = '4'
    layers.append((hp, True))
    for f in fingers:
        layers.append((shade(f, sigma=2.0 * s, exposure=0.05 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP), True))
    layers.append((shade(th, sigma=2.2 * s, exposure=0.05 + exposure, cuts=L.CUTS, wrap=L.SKIN_WRAP), True))
    return layers


# ------------------------------------------------------------------ ARMS
def arm_cock(cv, side, s):
    """The approved cocked arm, raised or lowered about the shoulder and its forearm bent about the
    elbow (cock_rot). Geometry is the viewer's-left arm's, turned, then mirrored for the right; the
    light is run after the turn, so both are lit from the upper left. With no rotation it is
    anim.arm_cock exactly."""
    rot = (s['cock_rot'] or {}).get(side, (0.0, 0.0))
    if not rot[0] and not rot[1]:
        return anim.arm_cock(cv, side, s)
    sh_deg, el_deg = rot
    dx, dy = s['body']
    SHOULDER, ELBOW = (38.0, 60.0), (11.0, 69.0)
    elbow = rot_pt(ELBOW, sh_deg, SHOULDER)

    def up(pts):                          # the upper arm turns about the shoulder
        return rot_pts(pts, sh_deg, SHOULDER)

    def fore(pts):                        # the forearm turns about the elbow, then rides the upper arm
        return [(x + elbow[0] - ELBOW[0], y + elbow[1] - ELBOW[1]) for (x, y) in rot_pts(pts, sh_deg + el_deg, ELBOW)]

    m = (lambda pts: pts) if side > 0 else mirror_pts
    sd = shadow()
    cv.stamp(shift(sculpt(spoly(m(up(SL.C_UPPER))), [(spoly(m(up(SL.C_BICEPS))), 2.2, 0.35)], sigma=4.5, exposure=0.05),
                   dx, dy), shadow=sd)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=sd, under=1)
    cv.stamp(shift(sculpt(spoly(m(fore(SL.C_FORE))), [(spoly(m(fore(SL.C_BRACHIO))), 2.0, 0.3)], sigma=4.0,
                          exposure=0.06), dx, dy), shadow=sd)
    cv.stamp(shift(anim.wrap_band(m(fore(SL.C_WRAP)), side), dx, dy))
    pc = fore([(15.0, 20.5)])[0]
    cx = pc[0] if side > 0 else MIR - pc[0]
    deg = (sh_deg + el_deg) * (1 if side > 0 else -1)
    for layer, outline in palm(cx, pc[1], 1.05, thumb=-side, fan=1.2, thumb_reach=10.5, deg=deg):
        cv.stamp(shift(layer, dx, dy), outline=outline)


# The tug-of-war push. At game scale the player's hands are level with Danny's ankle wraps, so to
# meet them palm to glove he reaches DOWN: the approved upper arm swung in about the shoulder, a
# long forearm driven down and forward, and the palm facing the viewer low in front of his knees.
# Written for the viewer's left arm (his right), in the body's own frame (before `body` moves it).
SHOULDER_P = (30.0, 58.0)


def _along(p0, p1, t, off=0.0):
    """The point a fraction t from p0 to p1, pushed `off` px off the axis (+ = to the right of the
    direction of travel, screen coordinates)."""
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(ax, ay) or 1.0
    return (p0[0] + ax * t - ay / ln * off, p0[1] + ay * t + ax / ln * off)


def limb(p0, p1, r0, r1, belly=None, sigma=4.0, exposure=0.04, bellies=()):
    """A new limb segment as the rig draws one: a tapered capsule sculpted with muscle bellies
    (smaller capsules along it, `bellies` = [(t0, t1, radius, off)]) so it shades as a form, not a
    tube. `belly` = (t0, t1, radius) is one centred belly."""
    mask = capsule(p0, p1, r0, r1)
    lay = []
    specs = list(bellies) + ([belly + (0.0,)] if belly else [])
    for (t0, t1, rb, off) in specs:
        a, b = _along(p0, p1, t0, off), _along(p0, p1, t1, off)
        lay.append((capsule(a, b, rb, rb * 0.75) & mask, 2.0, 0.3))
    return sculpt(mask, lay, sigma=sigma, exposure=exposure)


def crease(px, p0, p1, t0, t1, off, taper=3):
    """An open anatomy line along a limb (the rig's arm lines): black, fading into dark skin."""
    taper_line(px, [_along(p0, p1, t0 + (t1 - t0) * i / 4.0, off) for i in range(5)], 'k', taper_key='3',
               taper=taper, only=SKINSET)


def wrap_at(p0, p1, t, r, length=7.0):
    """A wrist wrap round a limb at fraction t from p0 to p1, r its half-width: a quad across it."""
    ax, ay = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(ax, ay) or 1.0
    ux, uy = ax / ln, ay / ln
    nx, ny = -uy, ux
    cx, cy = p0[0] + ax * t, p0[1] + ay * t
    h = length / 2.0
    return [(cx - ux * h + nx * r, cy - uy * h + ny * r), (cx + ux * h + nx * r, cy + uy * h + ny * r),
            (cx + ux * h - nx * r, cy + uy * h - ny * r), (cx - ux * h - nx * r, cy - uy * h - ny * r)]


def arm_push(cv, side, s):
    """push_at[side] = (palm x, palm y, palm scale) for the viewer's-left arm, body frame."""
    dx, dy = s['body']
    px_, py_, sc = (s['push_at'] or {}).get(side, (66.0, 112.0, 1.15))
    swing = -14.0
    m = (lambda pts: pts) if side > 0 else mirror_pts
    sd = shadow()
    up = lambda pts: rot_pts(pts, swing, SHOULDER_P)  # noqa: E731
    cv.stamp(shift(sculpt(spoly(m(up(LB.UPPER))), [(spoly(m(up(p))), 2.2, 0.28) for p in (LB.BICEPS, LB.TRICEPS)],
                          sigma=4.5, exposure=0.04), dx, dy), shadow=sd)
    cv.stamp(shift(LB.deltoid(side), dx, dy), shadow=sd, under=1)
    taper_line(cv.px, [(x + dx, y + dy) for (x, y) in m(up(LB.ARM_LINE))], 'k', taper_key='3', taper=0,
               only=SKINSET)
    elbow, wrist = m([rot_pt((15.0, 86.0), swing, SHOULDER_P), (px_ - 6.0 * sc, py_ + 4.0 * sc)])
    # geometry mirrored first, then lit: both forearms take the light from the upper left. As thick
    # as the approved ready forearm at the elbow, the brachioradialis swelling on its outer (upper)
    # side and the flexors under it, tapering to the wrap; the line between them as the rig draws it.
    out = -side * 3.2                      # the outer side of this forearm, off its axis
    fore = limb(elbow, wrist, 10.5, 7.6, exposure=0.05,
                bellies=[(0.02, 0.5, 7.5, out), (0.12, 0.62, 6.5, -out)])
    cv.stamp(shift(fore, dx, dy), shadow=sd)
    e2, w2 = (elbow[0] + dx, elbow[1] + dy), (wrist[0] + dx, wrist[1] + dy)
    crease(cv.px, e2, w2, 0.14, 0.62, -side * 0.6, taper=3)
    cv.stamp(shift(anim.wrap_band(wrap_at(elbow, wrist, 0.84, 8.2), side), dx, dy))
    cx = px_ if side > 0 else MIR - px_
    for layer, outline in SL.palm(cx, py_, s=sc, thumb=side, exposure=0.03):
        cv.stamp(shift(layer, dx, dy), outline=outline, shadow=sd)


# ------------------------------------------------------------------ LEGS
def legs_sit(cv, s, deg=0.0):
    """The defeat's seated legs, lowered by sit_dy, each swung up about its hip by deg (the Sumo
    Smash's knees-up V). Turned as geometry, then lit: the light stays upper left."""
    ddy = s['sit_dy']
    sd = shadow()
    HIP = (66.0, 124.0)

    def xf(side):
        piv = HIP if side > 0 else (MIR - HIP[0], HIP[1])
        a = deg if side > 0 else -deg           # screen angles turn clockwise: + lifts the left leg's foot

        def f(p):
            q = rot_pt(p, a, piv) if a else p
            return (q[0], q[1] + ddy)
        return f

    for side in (1, -1):
        f = xf(side)
        m = (lambda pts: pts) if side > 0 else mirror_pts
        part = sculpt(spoly([f(p) for p in m(LB.THIGH_SIT)]), [(spoly([f(p) for p in m(LB.QUAD_SIT)]), 3.0, 0.3)],
                      sigma=6.0, bulge=0.45, exposure=0.08, tilt=(0.0, -0.55))
        cv.stamp(part, shadow=sd)
    for side in (1, -1):
        f = xf(side)
        m = (lambda pts: pts) if side > 0 else mirror_pts
        cv.stamp(sculpt(spoly([f(p) for p in m(LB.FOOT_SIT)]), [(spoly([f(p) for p in m(LB.SOLE_SIT)]), 2.0, 0.25)],
                        sigma=3.0, exposure=0.1), shadow=sd)
        for a_, b_ in LB.TOE_SPLITS_SIT:
            taper_line(cv.px, [f(p) for p in m([a_, b_])], 'k', only=SKINSET)


# ------------------------------------------------------------------ HEAD
def face_mask(dx, dy, puff=0.0, jaw=0):
    def drop(p):
        x, y = p
        if jaw and y > 36:
            y += jaw * min(1.0, (y - 36) / 14.0)
        return (x + dx, y + dy)
    m = spoly([drop(p) for p in D.sym(D.FACE)])
    if puff:
        for cx in (68.5, MIR - 68.5):
            m |= ellipse(cx + dx, 43.5 + dy + jaw * 0.6, 9.0 * puff + 0.5, 8.0 * puff + 0.5)
    return m


def head(cv, s):
    """anim.head with more expression: two different eyes, puffed cheeks, a dropped jaw, sweat and
    drool. With none of those it is anim.head exactly."""
    dx = s['body'][0] + s['head_dx']
    dy = s['body'][1] + s['head_dy']
    sd = shadow()
    face = face_mask(dx, dy, s['puff'], s['jaw'])
    cv.stamp(F.face_base(face, dx, dy), shadow=sd)
    if s['puff']:
        # the blown-out cheeks catch the light on their upper left; the far one a tone down
        for (cx, k) in ((66.0, '7'), (MIR - 71.0, '6')):
            for q in ellipse(cx + dx, 41.0 + dy, 2.2, 1.6):
                if q in face and cv.px.get(q) in SKINSET:
                    cv.px[q] = k
    eyes = s['eyes'] if isinstance(s['eyes'], tuple) else (s['eyes'], s['eyes'])
    el = anim.EYES[eyes[0]]
    er = anim.EYES[eyes[1]]
    parts = [amap(el[0], 66 + dx, el[2] + dy), amap(er[1], 96 + dx, er[2] + dy), amap(F.NOSE, 81 + dx, 31 + dy),
             amap(anim.MOUTHS[s['mouth']], 78 + dx, 43 + dy)]
    for part in parts:
        for q, k in part.items():
            cv.px[q] = k
    crown = spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CROWN)])
    cv.stamp(D.knit_part_at(crown, 27.0, dx, sigma=9), shadow=sd)
    cuff = spoly([(x + dx, y + dy) for (x, y) in D.sym(D.CUFF)], 1)
    cv.stamp(D.knit_part_at(cuff, 27.0, dx, sigma=4))
    if s['drool']:
        cv.stamp(amap(FF.DROOL, 91 + dx, 47 + dy + s['jaw']), outline=False)
    for (x, y) in s['sweat']:
        cv.stamp(amap(FF.SWEAT, x + dx, y + dy), outline=False)
    if s['bubble']:
        r = anim.BUBBLE_R[s['bubble']]
        cv.stamp(F.bubble(92.6 + r + dx, 41.5 + (r - 4.4) * 0.45 + dy, r=r))
    if s['pop']:
        cx, cy = 97 + dx, 41 + dy
        for (ox, oy), k in anim.POP:
            cv.px[(cx + ox, cy + oy)] = k


FEATURE_KEYS = set('kWU1rRh2')


def _dparts():
    """The juggle's Danny parts (for relight_face, the rank-preserving relight of the face's painted
    cel bands), loaded by file path like the kit."""
    return _load('dparts', os.path.join(AS, 'danny_juggle', 'dparts.py'))


def feature_boxes(s):
    dx = s['body'][0] + s['head_dx']
    dy = s['body'][1] + s['head_dy']
    eyes = s['eyes'] if isinstance(s['eyes'], tuple) else (s['eyes'], s['eyes'])
    rows = len(anim.MOUTHS[s['mouth']])
    return [(66 + dx, anim.EYES[eyes[0]][2] + dy, 14, 7), (96 + dx, anim.EYES[eyes[1]][2] + dy, 14, 7),
            (81 + dx, 31 + dy, 15, 11), (78 + dx, 43 + dy, 20, rows + 1)]


def head_turned(s, deg, pivot):
    """The head alone, lit for a turn of `deg` and turned about `pivot` with RotSprite. The eyes,
    nose and mouth are lifted off first and put back crisp at their turned centres, the face's
    painted cel bands relit (the juggle's relight_face). Returns (key map with its own keyline,
    the turned nostril, the turn matrix)."""
    s2 = dict(s, bubble=0, pop=False)
    with lit(deg):
        cv = FreeCanvas()
        head(cv, s2)
    dx = s['body'][0] + s['head_dx']
    dy = s['body'][1] + s['head_dy']
    face = face_mask(dx, dy, s['puff'], s['jaw'])
    import types
    px = _dparts().relight_face(types.SimpleNamespace(deg=deg, face=face, px=cv.px))
    feats = []
    for (x0, y0, w, h) in feature_boxes(s):
        f = {(x, y): px[(x, y)] for x in range(x0, x0 + w) for y in range(y0, y0 + h)
             if (x, y) in face and px.get((x, y)) in FEATURE_KEYS}
        feats.append((f, '5'))
    M = K.turn_squash(deg)
    out = K.rekeyline(K.affine_with_features(px, M, pivot, pivot, feats, turns=0))
    nostril = K.affine_pt((92.6 + dx, 41.5 + dy), M, pivot, pivot)
    return out, nostril, M


def head_tilted(cv, s):
    """The head lolled over by head_tilt degrees about the chin, laid on the body with its cast
    shadow; the sleep bubble drawn after, upright, off the turned nostril."""
    deg = s['head_tilt']
    dx = s['body'][0] + s['head_dx']
    dy = s['body'][1] + s['head_dy']
    pivot = (87.5 + dx, 50.0 + dy)
    part, nostril, M = head_turned(s, deg, pivot)
    sd = shadow()
    body = set(part)
    for q in {(x + sd[0], y + sd[1]) for (x, y) in body} - body:
        k = cv.px.get(q)
        if k is not None and k != 'k':
            cv.px[q] = L.DARKER.get(k, k)
    for q, k in part.items():
        if cv.inside(q):
            cv.px[q] = k
    ux, uy = M[0], M[2]
    if s['bubble']:
        r = anim.BUBBLE_R[s['bubble']]
        cv.stamp(F.bubble(nostril[0] + ux * r, nostril[1] + uy * r + (r - 4.4) * 0.45, r=r))
    if s['pop']:
        pop_burst(cv, nostril[0] + ux * 4.4, nostril[1] + uy * 4.4 - 0.5)


def collar_trim(side):
    """gear.collar with its wing lowered on one side (side 1: the viewer's left). The wing rises
    under the jaw to the ear flap and is hidden there; when the head lolls over, the jaw lifts off
    that side and the wing would show as a red flag beside the face (the kabuki paint was taken
    out for reading as blood at 3x). Lowered, it stays a band round the neck."""
    import lib as _jl
    pts = list(G.sym(G.COLLAR))
    # the band keeps the height it shows under the jowl in the approved front view (about 8 px)
    low = {(87.5, 45): (87.5, 47), (70, 43.5): (70, 50.5), (62.5, 40.5): (64, 50), (59.5, 43.5): (61.5, 51.5)}
    if side < 0:
        low = {(MIR - x, y): (MIR - a, b) for (x, y), (a, b) in low.items()}
    pts = [low.get(p, p) for p in pts]
    mask = spoly(pts)
    bottom = {}
    for (x, y) in mask:
        bottom[x] = max(bottom.get(x, y), y)
    mask = {(x, y) for (x, y) in mask if y <= bottom[x] - G.NICKS.get(x, 0)}
    part = {p: 'R' for p in mask}
    _jl.rim(part, 'r', 0, -1, depth=1)
    _jl.rim(part, 'M', 0, 1, depth=1)
    for (x, y) in list(part):
        if x > 101 and part[(x, y)] == 'R':
            part[(x, y)] = 'M'
    return part


def neck(cv, s):
    """anim.neck; with a lolled head, the collar's uncovered wing is lowered (collar_trim)."""
    if not s['head_tilt']:
        return anim.neck(cv, s)
    dx, dy = s['body']
    cv.stamp(shift(G.gold_chain(), dx, dy))
    cv.stamp(shift(collar_trim(1 if s['head_tilt'] > 0 else -1), dx, dy), shadow=shadow())


# The bubble's pop, as the approved juggle draws it (danny_juggle/dposes.pop): the rig's ring of
# droplets, each a keylined 2x2 bead so it reads over his face at 3x, and a white flash at the centre.
POP_BEAD = {(0, 0): 'W', (1, 0): 'H', (0, 1): 'H', (1, 1): 'h'}


def pop_burst(cv, cx, cy, reach=1.3):
    beads = {}
    for (ox, oy), _ in anim.POP:
        bx, by = int(round(cx + ox * reach)), int(round(cy + oy * reach))
        for (ddx, ddy), k in POP_BEAD.items():
            beads[(bx + ddx, by + ddy)] = k
    cv.stamp(beads)
    cx, cy = int(round(cx)), int(round(cy))
    for (ddx, ddy), k in (((0, 0), 'W'), ((1, 0), 'W'), ((-1, 0), 'W'), ((0, 1), 'W'), ((0, -1), 'W'),
                          ((2, 0), 'H'), ((-2, 0), 'H'), ((0, 2), 'H'), ((0, -2), 'H')):
        if (cx + ddx, cy + ddy) in cv.px:
            cv.px[(cx + ddx, cy + ddy)] = k


class FreeCanvas(Canvas):
    """A canvas that keeps what falls outside the 176x144 frame (a pose that needs more room is
    drawn in the rig's own coordinates, then placed in a bigger frame by frame_image)."""

    def __init__(self, pad=64):
        Canvas.__init__(self)
        self.pad = pad

    def inside(self, q):
        p = self.pad
        return -p <= q[0] < self.w + p and -p <= q[1] < self.h + p


# ------------------------------------------------------------------ THE BUILD
BACK_ARMS = ('cock', 'limp', 'rest')
FRONT_ARMS = tuple(anim.STRIKES) + ('push',)
HEAD_ON = True                           # switched off to draw a body alone


def build(spec, free=False):
    """free=True draws on a FreeCanvas: nothing past the 176x144 frame is lost (a taller frame)."""
    s = dict(DEFAULT, **spec)
    anim_s = s
    cv = FreeCanvas() if free else Canvas()
    legs = s['legs']
    if legs == 'stand':
        anim.legs_stand(cv, anim_s)
    elif legs == 'sit':
        legs_sit(cv, s, 0.0)
    elif legs == 'airv':
        legs_sit(cv, s, s['leg_deg'])
    else:
        raise ValueError(legs)
    anim.belt(cv, anim_s)
    anim.torso(cv, anim_s)
    al, ar = s['arms']
    if al == 'ready' and ar == 'ready':
        anim.arms_ready(cv, anim_s)
    neck(cv, s)
    for side, a in ((1, al), (-1, ar)):
        if a == 'cock':
            arm_cock(cv, side, s)
        elif a == 'limp':
            anim.arm_limp(cv, side, anim_s)
        elif a == 'rest':
            anim.arm_rest(cv, side, anim_s)
    if HEAD_ON:
        (head_tilted if s['head_tilt'] else head)(cv, s)
    for side, a in ((1, al), (-1, ar)):
        if a in anim.STRIKES:
            anim.arm_strike(cv, side, a, anim_s)
        elif a == 'push':
            arm_push(cv, side, s)
    L.clean_lone(cv.px)
    return cv


def floor_clip(px, floor=FH - 1):
    """Nothing below the floor row; whatever reaches it touches the floor in keyline. (A body sunk
    onto the mat, the slam: the apron's hem is pressed flat under him.)"""
    out = {q: k for q, k in px.items() if q[1] <= floor}
    for q in [q for q in out if q[1] == floor]:
        out[q] = 'k'
    return out


def image_of(px, w=FW, h=FH, ox=0, oy=0):
    """A key map as an RGBA image of w x h, the rig's (x, y) placed at (x + ox, y + oy)."""
    from PIL import Image
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    put = im.load()
    for (x, y), k in px.items():
        X, Y = x + ox, y + oy
        if 0 <= X < w and 0 <= Y < h:
            put[X, Y] = L.PAL[k]
    return im


def check_same():
    """With no new option set, this builder must BE the approved one."""
    sys.path.insert(0, os.path.dirname(HERE))
    from imgdiff import pixel_diff
    out = []
    for name, (frames, _) in anim.SHEETS.items():
        for i, (spec, _) in enumerate(frames):
            if spec == anim.SMALL:
                continue
            d = pixel_diff(build(spec).image(), anim.build_frame(spec).image())
            out.append(('%s f%d' % (name, i), d))
    return out


if __name__ == '__main__':
    bad = [(n, d) for n, d in check_same() if d]
    print('fight.build == anim.build_frame on every approved frame:', 'yes' if not bad else bad)
