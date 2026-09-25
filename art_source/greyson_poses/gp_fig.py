"""Greyson's pose frames: the approved fight frames rebuilt with their joints free to move, and
the new frames built the same way.

The four approved frames (greyson_fight_approval.png f1-f4) are rebuilt here from the fight rig's
own parts with every joint at rest; the self-test proves each is pixel-identical to the approved
file. The strike, the breathing flex, the spoiled pose and the spirit bomb's hold / grin / throw
are the same builders with joints turned (whole traced muscle polygons and their forms rotated
about the shoulder, then the forearm about the elbow) and small, named changes. Nothing is
redrawn as a rotated picture: every frame is shaded fresh under the rig's upper-left light.

Each builder returns (canvas, anchors): anchors are frame texels, x right and y down, feet on row
111: 'feet', 'crown' (the top of his hair on the head's centre line) and 'muzzle' (the centre of
the cannon's muzzle face).

    python -B gp_fig.py      # self-test: the approved frames at rest; numbers of every frame
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_base as G  # noqa: E402
from gr_muscle import Form, Region, RegionLayer  # noqa: E402

K, gr_arms, gr_hands, gr_face, gr_fig, gr_boots = G.K, G.gr_arms, G.gr_hands, G.gr_face, \
    G.gr_fig, G.gr_boots
gf_arms, gf_back, gf_cannon, gf_faces, gf_hands = G.gf_arms, G.gf_back, G.gf_cannon, G.gf_faces, \
    G.gf_hands
Canvas = K.Canvas
FEET = (56, 111)


# ------------------------------------------------------------------------------------ joints

def rot(p, c, deg):
    """Rotate point p about c by deg (screen space, y down: positive turns clockwise)."""
    if not deg:
        return p
    t = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(t) - y * math.sin(t), c[1] + x * math.sin(t) + y * math.cos(t))


def rot_form(f, c, deg):
    if not deg:
        return f
    if f.axis is not None:
        a, b = f.axis
        return Form(axis=[rot(a, c, deg), rot(b, c, deg)], r=f.r, flat=f.flat)
    cx, cy, rx, ry = f.ell
    nx, ny = rot((cx, cy), c, deg)
    return Form(ellipsoid=(nx, ny, rx, ry), flat=f.flat)


class Arm:
    """An arm's traced polygons and forms (left-side coordinates) with two joints:
    the whole arm turns `sh` degrees about the shoulder (the delt only `delt_frac` of that), then
    the forearm group turns `el` degrees about the elbow. `shift` moves named regions by (dx, dy)
    afterwards (a biceps peaking, say). Points carried with the arm (a fist, the cannon's ends)
    go through the same joints with .upper() or .fore()."""

    FORE = ('forearm', 'brach')

    def __init__(self, polys, forms, shoulder, elbow, sh=0.0, el=0.0, delt_frac=0.3, shift=None):
        self.p0, self.f0 = polys, forms
        self.shoulder, self.elbow = shoulder, elbow
        self.sh, self.el, self.delt_frac = sh, el, delt_frac
        self.shift = shift or {}

    def _deg(self, name):
        return self.sh * self.delt_frac if name == 'delt' else self.sh

    def fore(self, p):
        return rot(rot(p, self.elbow, self.el), self.shoulder, self.sh)

    def upper(self, p):
        return rot(p, self.shoulder, self.sh)

    def polys(self):
        out = {}
        for n, pts in self.p0.items():
            if n in self.FORE:
                pts = [self.fore(p) for p in pts]
            else:
                pts = [rot(p, self.shoulder, self._deg(n)) for p in pts]
            dx, dy = self.shift.get(n, (0, 0))
            out[n] = [(x + dx, y + dy) for (x, y) in pts]
        return out

    def forms(self):
        out = {}
        for n, f in self.f0.items():
            if n in self.FORE:
                f = rot_form(rot_form(f, self.elbow, self.el), self.shoulder, self.sh)
            else:
                f = rot_form(f, self.shoulder, self._deg(n))
            dx, dy = self.shift.get(n, (0, 0))
            if dx or dy:
                if f.axis is not None:
                    (a, b) = f.axis
                    f = Form(axis=[(a[0] + dx, a[1] + dy), (b[0] + dx, b[1] + dy)], r=f.r, flat=f.flat)
                else:
                    cx, cy, rx, ry = f.ell
                    f = Form(ellipsoid=(cx + dx, cy + dy, rx, ry), flat=f.flat)
            out[n] = f
        return out


def arm_layer(arm, spec, side, keep=None):
    """gf_fig.arm_layer's shading (the rig's), from an Arm."""
    polys, forms = arm.polys(), arm.forms()
    regions = []
    for name, pts in polys.items():
        if keep is not None and name not in keep:
            continue
        amp, rnd, cast, depth = spec[name]
        pts = K.mpts(pts) if side else pts
        form = gr_arms._mirror_form(forms[name]) if side else forms[name]
        regions.append(Region(name, K.poly(pts), amp=amp, round_px=rnd, cast=cast, depth=depth,
                              form=form))
    base = forms['upper'] if not side else gr_arms._mirror_form(forms['upper'])
    return RegionLayer(base, regions).shade(cuts=gr_arms.CUTS)[0]


def mp(p):
    return (K.AX - p[0], p[1])


def finish(cv, keep=()):
    """gf_fig.finish: orphan skin tones swept (the hand-drawn face keeps its pixels), then any
    pinhole between two keylines closed with keyline."""
    K.despeckle(cv.px, keep=set(keep))
    x0, y0, x1, y1 = K.bbox(cv.px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in cv.px and all(q in cv.px for q in
                                           ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                cv.px[(x, y)] = 'k'
    return cv


def front_base(cv, lat_flare):
    """gf_fig.front_base: the approved legs, boots, torso, trunks and waistband."""
    P = gr_fig.Pose('idle')
    P.lat_flare = lat_flare
    for side in (0, 1):
        cv.stamp(K.despeckle(gr_fig.leg(side)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    cv.stamp(K.despeckle(gr_fig.torso(P)))
    cv.stamp(gr_fig.trunks())
    cv.stamp(gr_fig.waistband(), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y)] = 'k'


def back_base(cv, flare):
    """gf_fig.back_base: legs, boots, torso, trunks and waistband from behind."""
    for side in (0, 1):
        cv.stamp(K.despeckle(gf_back.back_leg(side)))
    for side in (0, 1):
        cv.stamp(gf_back.back_boot(side), outline=False)
    cv.stamp(K.despeckle(gf_back.back_torso(flare)))
    cv.stamp(gf_back.back_trunks())
    cv.stamp(gf_back.back_waistband(), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y)] = 'k'


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def rnd(p):
    return (int(round(p[0])), int(round(p[1])))


def crown_of(part, outlined=False):
    """The top of the head: its top row, on the centre of the head's top three rows (so a skull
    turned in profile, whose highest texel sits toward the back, still reports its middle); one
    row higher when the part is stamped with an outline, which draws its keyline above it."""
    y0 = min(y for (x, y) in part)
    xs = sorted(x for (x, y) in part if y <= y0 + 2)
    xc = (xs[0] + xs[-1]) // 2
    return (xc, min(y for (x, y) in part if x == xc) - (1 if outlined else 0))


# ------------------------------------------------------------------------------------ pose B
# the front double biceps (ref 26.png), on the approved f1. Joints for the LEFT arm (his right).
B_SHOULDER, B_ELBOW = (31.0, 56.5), (13.0, 57.0)


def pose_b(flare=1.5, sh=0.0, el=0.0, peak=0, face='flex', extras='sweat', head_dy=0):
    """sh/el turn both arms (mirrored) at the shoulder and the elbow; peak lifts both biceps
    peaks that many rows; face: an approved or fight face. At the defaults: the approved f2."""
    cv = Canvas()
    front_base(cv, flare)
    shift = {'biceps': (0, -peak)} if peak else None
    arm = Arm(gr_arms.FLEX, gr_arms.FLEX_FORMS, B_SHOULDER, B_ELBOW, sh=sh, el=el, shift=shift)
    cv.stamp(K.despeckle(arm_layer(arm, gr_arms.FLEX_SPEC, 0)))
    cv.stamp(K.despeckle(arm_layer(arm, gr_arms.FLEX_SPEC, 1, keep=('delt', 'biceps', 'upper'))))
    p0, p1 = mp(arm.fore((13.6, 58.0))), mp(arm.fore((15.0, 28.0)))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.5))
    cv.stamp(gr_hands.fist('flex', 0, arm.fore((15.0, 40.0))), outline=False)
    fc = head_part(face, extras, head_dy)
    cv.stamp(fc[0], outline=False)
    finish(cv, fc[1])
    return cv, {'feet': FEET, 'crown': crown_of(moved(gr_face.mane(), 0, head_dy)), 'muzzle': rnd(p1)}


def head_part(face, extras, dy=0):
    """(head part, the face's own pixels for finish()) for a front head: the approved mane with
    an approved or fight face, plus extras ('sweat' = the approved bead)."""
    if face in gr_face.FACES:
        part = gr_face.mane()
        f = gr_face.face(face)
    else:
        part = gr_face.mane()
        f = gf_faces.face(face) if face in gf_faces.FACES else FACES_NEW[face]()
    part.update(f)
    if extras == 'sweat':
        part.update(gr_face.SWEAT)
    elif isinstance(extras, dict):
        part.update(extras)
    return moved(part, 0, dy), set(moved(f, 0, dy))


FACES_NEW = {}      # filled in by gp_faces


# ------------------------------------------------------------------------------------ pose C
# the rear V (ref 27.png): his back to us, both arms up and out. Joints, left-side coordinates.
C_SHOULDER, C_ELBOW = (31.4, 51.2), (18.0, 33.0)


def pose_c(flare=3.2, sh=0.0, el=0.0, hand_dy=0):
    """At the defaults: the approved f3. The screen-left arm is his LEFT (the cannon)."""
    cv = Canvas()
    back_base(cv, flare)
    cv.stamp(gf_back.back_head(), outline=False)
    arm = Arm(gf_arms.REAR_V, gf_arms.REAR_V_FORMS, C_SHOULDER, C_ELBOW, sh=sh, el=el)
    cv.stamp(K.despeckle(arm_layer(arm, gf_arms.REAR_V_SPEC, 0, keep=('delt', 'upper', 'biceps'))))
    cv.stamp(K.despeckle(arm_layer(arm, gf_arms.REAR_V_SPEC, 1)))
    ex, ey = gf_arms.REAR_V_ELBOW
    p0, p1 = arm.fore((ex + 0.4, ey + 1.4)), arm.fore((ex - 8.0, ey - 25.6))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.5))
    wx, wy = arm.fore(gf_arms.REAR_V_WRIST)
    cv.stamp(gf_hands.hand('open', 1, (wx, wy + hand_dy)), outline=False)
    finish(cv)
    return cv, {'feet': FEET, 'crown': crown_of(gf_back.back_head()), 'muzzle': rnd(p1)}


# ------------------------------------------------------------------------------------ pose A
# the three-quarter back twist (ref 25.png). EXT: his left arm (screen left, the cannon), UP: his
# right arm (drawn left, mirrored to screen right), elbow high, fist at the back of his head.
A_EXT_SHOULDER = (33.0, 52.0)
A_UP_SHOULDER, A_UP_ELBOW = (31.0, 52.0), (22.0, 32.0)


def pose_a(flare=2.4, ext_sh=0.0, up_sh=0.0, up_el=0.0, head='profile'):
    """At the defaults: the approved f1. head 'back': still turned away (the back of the head, as
    in the rear V), for the strike before he turns his face along the arm."""
    cv = Canvas()
    back_base(cv, flare)
    up = Arm(gf_arms.TWIST_UP, gf_arms.TWIST_UP_FORMS, A_UP_SHOULDER, A_UP_ELBOW, sh=up_sh, el=up_el)
    cv.stamp(K.despeckle(arm_layer(up, gf_arms.TWIST_SPEC, 1)))
    if head == 'profile':
        hair, face = gf_back.profile_head()
        cv.stamp(hair)
        cv.stamp(face, outline=False)
        crown = crown_of(hair, outlined=True)
    else:
        face = {}
        cv.stamp(gf_back.back_head(), outline=False)
        crown = crown_of(gf_back.back_head())
    cv.stamp(gr_hands.fist('flex', 1, up.fore(gf_arms.TWIST_FIST)), outline=False)
    ext = Arm(gf_arms.TWIST_EXT, gf_arms.TWIST_EXT_FORMS, A_EXT_SHOULDER, gf_arms.TWIST_EXT_ELBOW,
              sh=ext_sh)
    cv.stamp(K.despeckle(arm_layer(ext, gf_arms.TWIST_SPEC, 0)))
    ex, ey = gf_arms.TWIST_EXT_ELBOW
    p0, p1 = ext.upper((ex + 1.2, ey)), ext.upper((ex - 9.6, ey + 9.6))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.72))
    finish(cv, face)
    return cv, {'feet': FEET, 'crown': crown, 'muzzle': rnd(p1)}


# ------------------------------------------------------------------------------------ spirit
# the one-arm raise: his left arm (screen right) straight up, the cannon to the sky.
S_SHOULDER = (29.6, 53.6)


def spirit(flare=1.0, face='roar', extras=None, sh=0.0, head_dy=0):
    """At the defaults: the approved f4 (muzzle (82, 7))."""
    cv = Canvas()
    front_base(cv, flare)
    cv.stamp(K.despeckle(gr_arms.arm('idle', 0)))
    arm = Arm(gf_arms.RAISED, gf_arms.RAISED_FORMS, S_SHOULDER, gf_arms.RAISED_ELBOW, sh=sh)
    cv.stamp(K.despeckle(arm_layer(arm, gf_arms.RAISED_SPEC, 1)))
    ex, ey = gf_arms.RAISED_ELBOW
    p0, p1 = mp(arm.upper((ex, ey + 1.5))), mp(arm.upper((ex + 0.4, 7.0)))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.5))
    cv.stamp(gr_hands.fist('idle', 0, (25.0, 84.5)), outline=False)
    fc = head_part(face, extras, head_dy)
    cv.stamp(fc[0], outline=False)
    finish(cv, fc[1])
    return cv, {'feet': FEET, 'crown': crown_of(moved(gr_face.mane(), 0, head_dy)), 'muzzle': rnd(p1)}


# ------------------------------------------------------------------------------------ new frames
import gp_faces  # noqa: E402

FACES_NEW.update({n: (lambda n=n: gp_faces.face(n)) for n in gp_faces.FACES})

# the approved idle arm's joints (gr_arms.IDLE, left-side coordinates)
I_SHOULDER, I_ELBOW = (30.0, 57.0), (22.0, 71.5)
IDLE_FIST = (25.0, 84.5)
CANNON_HANG = ((21.4, 70.0), (13.8, 95.0))      # the fight idle's cannon, elbow to muzzle


def capsule(p0, p1, r0, r1, n=12):
    """A closed outline round the segment p0 -> p1, radius r0 at p0 and r1 at p1."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    pts = []
    for i in range(n + 1):                                  # the far cap
        a = -math.pi / 2 + math.pi * i / n
        pts.append((x1 + r1 * (math.cos(a) * ux + math.sin(a) * nx),
                    y1 + r1 * (math.cos(a) * uy + math.sin(a) * ny)))
    for i in range(n + 1):                                  # the near cap
        a = math.pi / 2 + math.pi * i / n
        pts.append((x0 + r0 * (math.cos(a) * ux + math.sin(a) * nx),
                    y0 + r0 * (math.cos(a) * uy + math.sin(a) * ny)))
    return pts


def hanging_cannon_arm(cv, sh=0.0):
    """His left arm (screen right) as in the fight idle: the approved delt, triceps and biceps,
    the cannon hanging from the elbow, muzzle down and a little out; turned `sh` at the
    shoulder. Returns the muzzle point."""
    arm = Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, I_SHOULDER, I_ELBOW, sh=sh)
    cv.stamp(K.despeckle(arm_layer(arm, gr_arms.SPEC, 1, keep=('delt', 'upper', 'biceps'))))
    p0, p1 = mp(arm.upper(CANNON_HANG[0])), mp(arm.upper(CANNON_HANG[1]))
    cv.stamp(gf_cannon.cannon(p0, p1, face=0.62))
    return p1


def hit_knocked(sh=16.0, cn_sh=14.0, head=(1, 1), flare=1.0, bead=(11, -5)):
    """pose_hit f0: knocked out of the pose. Both arms flung loose and out from the body, the
    head jolted, the wince; the flex face's sweat bead knocked off his temple (`bead` offsets it
    from its place on the approved flex face; None leaves it off)."""
    cv = Canvas()
    front_base(cv, flare)
    arm = Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, I_SHOULDER, I_ELBOW, sh=sh)
    cv.stamp(K.despeckle(arm_layer(arm, gr_arms.SPEC, 0)))
    muzzle = hanging_cannon_arm(cv, cn_sh)
    cv.stamp(gr_hands.fist('idle', 0, arm.fore(IDLE_FIST)), outline=False)
    hp, fpx = head_part('wince', None)
    cv.stamp(moved(hp, head[0], head[1]), outline=False)
    fx = set()
    if bead is not None:
        drop = moved(gr_face.SWEAT, head[0] + bead[0], head[1] + bead[1])
        cv.stamp(drop, outline=False)
        fx = set(drop)
    finish(cv, set(moved({p: 1 for p in fpx}, head[0], head[1])) | fx)
    return cv, {'feet': FEET, 'crown': crown_of(moved(gr_face.mane(), head[0], head[1])),
                'muzzle': rnd(muzzle)}


def hit_annoyed(flare=0.5):
    """pose_hit f1: annoyed. His right fist clenched in front of his chest (the fight idle's
    carry arm, without the barbell), the cannon hanging, the flat down-turned glare."""
    cv = Canvas()
    front_base(cv, flare)
    carry = Arm(gf_arms.CARRY, gf_arms.CARRY_FORMS, I_SHOULDER, (24.0, 73.0))
    cv.stamp(K.despeckle(arm_layer(carry, gf_arms.CARRY_SPEC, 0)))
    muzzle = hanging_cannon_arm(cv)
    hp, fpx = head_part('annoyed', None)
    cv.stamp(hp, outline=False)
    cv.stamp(gr_hands.fist('idle', 0, (41.0, 55.0)), outline=False)
    finish(cv, fpx)
    return cv, {'feet': FEET, 'crown': crown_of(gr_face.mane()), 'muzzle': rnd(muzzle)}


# the throw: his left arm (screen right) snapped forward and down at the player, foreshortened
# toward us, the bore turned to face us. Left-side coordinates, mirrored.
T_SHOULDER = (29.6, 53.6)


def spirit_throw(elbow=(32.0, 62.0), muzzle=(36.5, 73.0), face=0.85, sh=12.0, head=(0, 1),
                 flare=1.2, face_name='roar'):
    cv = Canvas()
    front_base(cv, flare)
    arm = Arm(gr_arms.IDLE, gr_arms.IDLE_FORMS, I_SHOULDER, I_ELBOW, sh=sh)
    cv.stamp(K.despeckle(arm_layer(arm, gr_arms.SPEC, 0)))
    cv.stamp(gr_hands.fist('idle', 0, arm.fore(IDLE_FIST)), outline=False)
    hp, fpx = head_part(face_name, None)
    cv.stamp(moved(hp, head[0], head[1]), outline=False)
    polys = {'delt': gf_arms.RAISED['delt'],
             'upper': capsule(T_SHOULDER, elbow, 6.6, 6.2)}
    forms = {'delt': gf_arms.RAISED_FORMS['delt'],
             'upper': Form(axis=[T_SHOULDER, elbow], r=6.8)}
    spec = {'delt': gf_arms.RAISED_SPEC['delt'], 'upper': (1.6, 2.8, 2, 2)}
    t = Arm(polys, forms, T_SHOULDER, elbow)
    cv.stamp(K.despeckle(arm_layer(t, spec, 1)))
    p0, p1 = mp(elbow), mp(muzzle)
    cv.stamp(gf_cannon.cannon(p0, p1, face=face))
    finish(cv, moved({p: 1 for p in fpx}, head[0], head[1]))
    return cv, {'feet': FEET, 'crown': crown_of(moved(gr_face.mane(), head[0], head[1])),
                'muzzle': rnd(p1)}


APPROVED_BUILDERS = {'pose_a': pose_a, 'pose_b': pose_b, 'pose_c': pose_c, 'spirit': spirit}

# ------------------------------------------------------------------------------------ the sheets
# name -> [(label, builder, kwargs)], frame 0 leftmost
SHEETS = {
    'greyson_pose_a': [
        ('strike', pose_a, dict(ext_sh=-25, up_sh=-30, head='back')),   # still turned away, arms rising
        ('hold', pose_a, {}),                                          # the approved f1
        ('hold flex', pose_a, dict(flare=3.0, up_sh=3)),               # lats spread, the elbow lifts
    ],
    'greyson_pose_b': [
        ('strike', pose_b, dict(sh=-40, el=30, face='roar', extras=None)),   # arms driving up, "HAA"
        ('hold', pose_b, {}),                                                # the approved f2
        ('hold flex', pose_b, dict(flare=2.3, peak=1)),                      # lats spread, peaks squeezed
    ],
    'greyson_pose_c': [
        ('strike', pose_c, dict(sh=-28, el=50)),        # a rear double biceps, opening up into the V
        ('hold', pose_c, {}),                           # the approved f3
        ('hold flex', pose_c, dict(flare=3.8, sh=2)),   # lats spread, the V lifts
    ],
    'greyson_pose_hit': [
        ('knocked', hit_knocked, dict(sh=45, cn_sh=6, head=(-2, 0))),
        ('annoyed', hit_annoyed, {}),
    ],
    'greyson_spirit': [
        ('arm up', spirit, {}),                                             # the approved f4
        ('hold', spirit, dict(flare=1.8, face='flex', extras='sweat')),     # straining under it
        ('grin', spirit, dict(face='menace')),
        ('THROW', spirit_throw, dict(elbow=(36.0, 60.0), muzzle=(46.0, 70.0), face=0.85, sh=28,
                                     head=(1, 2))),
    ],
}


def build_sheet(name):
    """-> [(label, canvas, anchors)]"""
    return [(label, *fn(**kw)) for label, fn, kw in SHEETS[name]]


def selftest():
    bad = []
    for name, fn in APPROVED_BUILDERS.items():
        cv, anc = fn()
        d = G.pixel_diff(cv.image(), G.approved_frame(name))
        print('%-7s at rest vs approved: %s   anchors %s' % (name, d or 'identical', anc))
        if d:
            bad.append(name)
    return bad


if __name__ == '__main__':
    sys.exit(1 if selftest() else 0)
