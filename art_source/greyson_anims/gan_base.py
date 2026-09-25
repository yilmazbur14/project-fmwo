"""Greyson's attack animations (idle, throw, teleport, slam, hit, broken, defeat, victory): the base.

Built on the APPROVED fight rig (art_source/greyson_fight, gf_*), which is built on the approved
design rig (art_source/greyson_redesign, gr_*). Both belong to their artist and are imported
READ-ONLY: nothing here edits them, and bytecode writing is off so importing leaves no __pycache__
in their folders. gf_base proves on import that the approved design rig still draws the shipped
greyson_redesign.png; this module proves in turn that the fight rig still draws the approved
greyson_fight_approval.png, frame for frame, before anything is built on it.

Every module here is named gan_*, so none can shadow (or be shadowed by) gf_* or gr_*.

Coordinates are the rigs' own: 112x112 frames, feet on row 111, column 56 the anchor, light from
the upper left. His LEFT arm (the screen's right in a front view) wears Computah's cannon.

The one new tool is arm(): an arm generated from its joints (shoulder, elbow, wrist) into the same
muscle regions the approved arms are traced as (the delt cap, the biceps on the inner side, the
triceps as the whole upper arm, the forearm and its brachioradialis bulge), with the same forms,
the same shading and the same dark-skin separation lines, so a new pose is shaded exactly like the
approved ones. Nothing in this module writes files.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
FIGHT = os.path.join(ART, 'greyson_fight')
RIG = os.path.join(ART, 'greyson_redesign')
ROOT = os.path.dirname(ART)
ASSETS = os.path.join(ROOT, 'Assets', 'Characters', 'Greyson')
APPROVAL_PNG = os.path.join(ASSETS, 'greyson_fight_approval.png')

if FIGHT not in sys.path:
    sys.path.insert(0, FIGHT)

import gf_base          # noqa: E402  proves the approved design rig on import
import gf_fig           # noqa: E402
import gf_arms          # noqa: E402
import gf_cannon        # noqa: E402
import gf_barbell       # noqa: E402
import gf_faces         # noqa: E402
import gf_hands         # noqa: E402

if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _same_dir(mod, folder):
    return os.path.normcase(os.path.dirname(os.path.abspath(mod.__file__))) == \
        os.path.normcase(os.path.abspath(folder))


for _m in (gf_base, gf_fig, gf_arms, gf_cannon, gf_barbell, gf_faces, gf_hands):
    if not _same_dir(_m, FIGHT):
        raise ImportError('%s came from %s, not the fight rig %s' % (_m.__name__, _m.__file__, FIGHT))
for _m in (gf_base.K, gf_base.M, gf_base.gr_fig, gf_base.gr_face, gf_base.gr_arms,
           gf_base.gr_hands, gf_base.gr_boots):
    if not _same_dir(_m, RIG):
        raise ImportError('%s came from %s, not the design rig %s' % (_m.__name__, _m.__file__, RIG))

from gr_muscle import Form, Region, RegionLayer  # noqa: E402
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

K = gf_base.K
gr_fig, gr_arms, gr_hands, gr_face, gr_boots = (gf_base.gr_fig, gf_base.gr_arms, gf_base.gr_hands,
                                                gf_base.gr_face, gf_base.gr_boots)
W = H = 112
AX = K.AX
FEET = (56, 111)
ALLOWED = gf_base.ALLOWED
Canvas = K.Canvas

APPROVAL_FRAMES = ('idle', 'pose_a', 'pose_b', 'pose_c', 'spirit')


def approval_sheet():
    return Image.open(APPROVAL_PNG).convert('RGBA')


def check_fight_rig():
    sheet = approval_sheet()
    for i, name in enumerate(APPROVAL_FRAMES):
        d = pixel_diff(gf_fig.build(name).image(), sheet.crop((112 * i, 0, 112 * i + 112, 112)))
        if d:
            raise SystemExit('the fight rig no longer draws approved frame %d (%s): %s' % (i, name, d))


check_fight_rig()


# ------------------------------------------------------------------------------------ helpers

def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def image(px, w=W, h=H):
    return gf_base.image(px, w, h)


def audit(px, fx=()):
    return gf_base.audit(px, fx)


def stats(im):
    return K.stats(im)


def bbox(px):
    return K.bbox(px)


def finish(cv, keep=()):
    """The approved rig's last sweep (gf_fig.finish): orphan skin tones cleaned (hand-drawn face
    pixels kept), then any pinhole between two keylines closed with keyline."""
    return gf_fig.finish(cv, keep)


def unit(v):
    L = math.hypot(v[0], v[1]) or 1.0
    return (v[0] / L, v[1] / L)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


# ------------------------------------------------------------------------------------ arms

LINE = gr_arms.LINE
SPEC = dict(gr_arms.SPEC)
FLEX_SPEC = dict(gr_arms.FLEX_SPEC)
CUTS = gr_arms.CUTS


class ArmRef:
    """An approved arm pose used as a TEMPLATE: its traced muscle polygons and forms (left-arm,
    screen coordinates) and the joints they were traced around. Every point is re-expressed in the
    arm's own frame: along the bone from the joint (t) and across it toward the triceps side (s).
    Upper-arm regions ride the shoulder->elbow bone, forearm regions the elbow->wrist bone."""

    def __init__(self, polys, forms, spec, S, E, Wr, tri, upper_names=('delt', 'upper', 'biceps')):
        self.polys, self.forms, self.spec = polys, forms, spec
        self.S, self.E, self.Wr, self.tri = S, E, Wr, tri
        self.upper_names = set(upper_names)


def _frame(p0, p1, tri):
    u = unit((p1[0] - p0[0], p1[1] - p0[1]))
    n = (-u[1], u[0])
    if n[0] * tri[0] + n[1] * tri[1] < 0:
        n = (-n[0], -n[1])
    return u, n, math.hypot(p1[0] - p0[0], p1[1] - p0[1])


def _to_local(p, o, u, n):
    d = (p[0] - o[0], p[1] - o[1])
    return (d[0] * u[0] + d[1] * u[1], d[0] * n[0] + d[1] * n[1])


def _to_screen(ts, o, u, n, scale):
    t, s_ = ts
    return (o[0] + u[0] * t * scale + n[0] * s_, o[1] + u[1] * t * scale + n[1] * s_)


# The approved ready-stance arm (gr_arms.IDLE), traced round these joints: the shoulder at the
# delt's centre, the elbow, the wrist over the fist's anchor. The triceps faces out (screen left).
IDLE_REF = ArmRef(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC,
                  S=(28.0, 56.0), E=(22.5, 72.5), Wr=(26.5, 83.5), tri=(-1, 0))
# The approved barbell carry (gf_arms.CARRY): the upper arm hanging, the forearm folded up across the
# lat to the fist in front of the chest.
CARRY_REF = ArmRef(gf_arms.CARRY, gf_arms.CARRY_FORMS, gf_arms.CARRY_SPEC,
                   S=(28.0, 56.0), E=(23.5, 73.0), Wr=(39.5, 59.5), tri=(-1, 0))
# The approved double biceps (gr_arms.FLEX): the upper arm out level with the triceps hanging under
# it, the biceps peaked above, the forearm standing up to the fist at the temple.
FLEX_REF = ArmRef(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC,
                  S=(30.0, 54.0), E=(12.0, 57.5), Wr=(15.0, 41.0), tri=(0, 1))
# The approved raised arm (gf_arms.RAISED, the spirit raise): straight up, the delt bunched on the
# shoulder. It has no forearm (the cannon replaces it); a flesh raised arm borrows IDLE_REF's.
RAISED_REF = ArmRef(gf_arms.RAISED, gf_arms.RAISED_FORMS, gf_arms.RAISED_SPEC,
                    S=(29.6, 53.6), E=(29.4, 31.0), Wr=(29.2, 16.0), tri=(-1, 0))


def arm(S, E, Wr=None, tri=(-1, 0), ref=None, keep=None, thick=1.0, fore_ref=None):
    """One arm in SCREEN coordinates from its joints: shoulder S, elbow E, wrist Wr (None when the
    forearm is replaced, e.g. by the cannon). `tri` is the side the triceps faces (away from the
    body when the arm hangs, down when it is held out, back when raised). The approved arm `ref`
    (IDLE_REF by default) is carried onto the new bones: each of its traced muscles keeps its shape
    along its own bone (stretched to the new bone's length) and its width across it (times
    `thick`). Returns the shaded part; stamp it WITH an outline, like the approved arms."""
    ref = ref or IDLE_REF
    u1, n1, L1 = _frame(S, E, tri)
    if Wr is not None:
        u2, n2, L2 = _frame(E, Wr, tri)
    regions = []
    first_form = None
    items = [(name, pts, ref) for name, pts in ref.polys.items() if name in ref.upper_names]
    fr = fore_ref or ref
    items += [(name, pts, fr) for name, pts in fr.polys.items() if name not in fr.upper_names]
    for name, pts, ref in items:
        ru1, rn1, rL1 = _frame(ref.S, ref.E, ref.tri)
        ru2, rn2, rL2 = _frame(ref.E, ref.Wr, ref.tri)
        if keep is not None and name not in keep:
            continue
        if name not in ref.upper_names and Wr is None:
            continue
        if name in ref.upper_names:
            new = [_to_screen((t, s_ * thick), S, u1, n1, L1 / rL1)
                   for (t, s_) in (_to_local(p, ref.S, ru1, rn1) for p in pts)]
        else:
            new = [_to_screen((t, s_ * thick), E, u2, n2, L2 / rL2)
                   for (t, s_) in (_to_local(p, ref.E, ru2, rn2) for p in pts)]
        f = ref.forms[name]
        if f.axis is not None:
            if name in ref.upper_names:
                ax = [_to_screen(_to_local(q, ref.S, ru1, rn1), S, u1, n1, L1 / rL1) for q in f.axis]
            else:
                ax = [_to_screen(_to_local(q, ref.E, ru2, rn2), E, u2, n2, L2 / rL2) for q in f.axis]
            form = Form(axis=ax, r=f.r * thick, flat=f.flat)
        else:
            cx, cy, rx, ry = f.ell
            c = _to_screen(_to_local((cx, cy), ref.S, ru1, rn1), S, u1, n1, L1 / rL1)
            form = Form(ellipsoid=(c[0], c[1], rx * thick, ry * thick), flat=f.flat)
        if name == 'upper':
            first_form = form
        amp, rnd, cast, depth = ref.spec[name]
        regions.append(Region(name, K.poly(new), amp=amp, round_px=rnd, cast=cast, depth=depth,
                              form=form))
    lay = RegionLayer(first_form or regions[0].form, regions)
    return K.despeckle(lay.shade(cuts=CUTS)[0])


# ------------------------------------------------------------------------------------ the rest of him

def front_base(cv, lat_flare=0.5, dx=0, dy=0, legs=None, torso_dy=0):
    """The approved front parts (gf_fig.front_base): legs, boots, torso, trunks, waistband, with the
    upper body (torso) moved by (dx, dy + torso_dy) and the legs given (or the approved ones)."""
    rec('base', (dx, dy + torso_dy))
    P = gr_fig.Pose('idle')
    P.lat_flare = lat_flare
    if legs is None:
        for side in (0, 1):
            cv.stamp(K.despeckle(gr_fig.leg(side)))
        for side in (0, 1):
            cv.stamp(gr_boots.boot(side), outline=False)
    else:
        legs(cv)
    cv.stamp(moved(K.despeckle(gr_fig.torso(P)), dx, dy + torso_dy))
    cv.stamp(moved(gr_fig.trunks(), dx, dy))
    cv.stamp(moved(gr_fig.waistband(), dx, dy), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x + dx, y + dy)] = 'k'


def squash_legs(drop=(), spread=0, dx=0, stretch=()):
    """The approved legs and boots with `drop` rows taken out of the thighs and shins (the hips
    sink, the soles stay on row 111) or `stretch` rows doubled (the hips rise: a spring onto his
    toes), and the knees spread `spread` px outward (a squat, as it reads with him square to us);
    the whole upper part can slide by dx (a lean). -> a stamp function."""
    def remap(y):
        """old row -> new row(s) for a leg pixel (the soles fixed)."""
        if y in drop:
            return []
        ny = y + sum(1 for r in drop if r > y) - sum(1 for r in stretch if r > y)
        return [ny - 1, ny] if y in stretch else [ny]

    def stamp(cv):
        for side in (0, 1):
            lg = K.despeckle(gr_fig.leg(side))
            out = {}
            for (x, y), k in lg.items():
                for ny in remap(y):
                    sx = 0
                    if spread and 84 <= ny <= 100:
                        w = 1.0 - abs(ny - 93) / 9.0
                        sx = int(round(spread * w)) * (-1 if side == 0 else 1)
                    lean = int(round(dx * max(0, 100 - ny) / 22.0)) if dx else 0
                    out[(x + sx + lean, ny)] = k
            cv.stamp(out)
        for side in (0, 1):
            cv.stamp(gr_boots.boot(side), outline=False)
    return stamp


# ------------------------------------------------------------------------------------ weapons

def barbell(grip, plate_c=None, squash=0.88, ang=None, r=10.4, bare_end=None):
    """The approved barbell (gf_barbell) from the grip to the plate's centre: -> [(part, outline)].
    The plate's long axis is square to the bar (as in the approved idle: bar at 44 degrees, plate at
    -45) unless `ang` is given; `squash` is how face-on the plate is (0.88 in the approved idle, the
    bar running back over his shoulder; lower when the bar lies across the picture). With
    plate_c None the bar ends bare at `bare_end` (the plate has just left it)."""
    out = []
    if plate_c is not None:
        if ang is None:
            ang = math.degrees(math.atan2(plate_c[1] - grip[1], plate_c[0] - grip[0])) - 90.0
        out.append((rec('plate', gf_barbell.plate(plate_c, r=r, squash=squash, ang=ang)), True))
        out.append((rec('bar', gf_barbell.bar(plate_c, grip)), True))
    else:
        out.append((rec('bar', gf_barbell.bar(bare_end, grip)), True))
    return out


def cannon(socket, muzzle, face=0.5):
    """Computah's cannon over his left forearm (gf_cannon), from the socket at his elbow to the
    muzzle. Stamp WITH an outline."""
    return gf_cannon.cannon(socket, muzzle, face=face)


def streaks(pts, key='X', every=1):
    """Speed lines: free-floating single-pixel lines (no keyline), as FX pixels."""
    out = {}
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) or 1
        for i in range(0, n + 1, every):
            out[(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)))] = key
    return out


# ------------------------------------------------------------------------------------ recording

_REC = [None]


def rec(name, value):
    """Frame builders hand named parts or points to this while a measurement is recording."""
    if _REC[0] is not None:
        _REC[0][name] = value
    return value


def record(builder):
    _REC[0] = {}
    try:
        res = builder()
        got = _REC[0]
    finally:
        _REC[0] = None
    return res, got


def make_frames(builders, approved=None):
    """builders: zero-argument callables returning (Canvas, fx pixels). `approved` maps a frame
    index to the approval sheet's frame that it must equal pixel for pixel (that builder has to
    reproduce it, and the approval sheet's own frame is what ships). -> [(px, fx, info)]."""
    out = []
    sheet = approval_sheet() if approved else None
    for i, b in enumerate(builders):
        (cv, fx), info = record(b)
        px = dict(cv.px)
        if approved and i in approved:
            ref = sheet.crop((112 * approved[i], 0, 112 * approved[i] + 112, 112))
            d = pixel_diff(image(px), ref)
            if d:
                raise SystemExit('frame %d must be approved frame %d but differs: %s' % (i, approved[i], d))
        out.append((px, set(fx), info))
    return out
