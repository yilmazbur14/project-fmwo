"""The KO: Greyson topples backward UP the screen and lands on his back (greyson_brawl_ko f1-f4),
his feet staying on row 111 the whole way; f4 is the frame Defeated holds.

The fall is a rotation backward about his feet, drawn in the game's own projection: bodies stand
full height and the floor is foreshortened by half (the ring's mat is 565x285 texels for a square
ring), so a body tipped back by theta shows its height at s = cos(theta) + 0.5 sin(theta) of
standing: it first STRETCHES as he tips (the head rises up the screen, s peaks at 1.12 near 27
degrees), then shrinks to one half lying flat. That transform is applied to the rig's own geometry
(polygon points, muscle bumps re-fitted to the squash the way the brawl rig's crouch re-fits them,
and the forms that light them) and everything is shaded fresh under the house light; nothing is a
squashed picture. The parts that have no geometry to transform are drawn for it: the head lying
face-up (the face seen from the chin end, the mane fanned out on the mat) and the boots turned
soles-to-us.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gz_base as Z  # noqa: E402

K, G, P, F, BD, A = Z.K, Z.G, Z.P, Z.F, Z.BD, Z.A
gr_fig, gr_arms, gr_hands, gr_face, gf_cannon = Z.gr_fig, Z.gr_arms, Z.gr_hands, Z.gr_face, \
    Z.gf_cannon
from gr_muscle import Bump, Form, Layer  # noqa: E402

Canvas, moved = Z.Canvas, Z.moved
FEET_Y = 111.0


def s_of(theta_deg):
    t = math.radians(theta_deg)
    return math.cos(t) + 0.5 * math.sin(t)


class Tilt:
    """y' = pivot - (pivot - y) * s: the body tipped back about row `pivot` (his heels)."""

    def __init__(self, s, pivot=FEET_Y):
        self.s, self.pivot = s, pivot

    def y(self, y):
        return self.pivot - (self.pivot - y) * self.s

    def pt(self, p):
        return (p[0], self.y(p[1]))

    def pts(self, ps):
        return [self.pt(p) for p in ps]

    def bump(self, b):
        """The bump's ellipse squashed vertically by s: its axes re-fitted (gb_body.Crouch's way)."""
        ang = math.radians(b.ang)
        ca, sa = math.cos(ang), math.sin(ang)
        fa = math.hypot(ca, sa * self.s)
        fb = math.hypot(-sa, ca * self.s)
        new_ang = math.degrees(math.atan2(sa * self.s, ca))
        return Bump(b.name, self.pt(b.c), b.a * fa, b.b * fb, new_ang, b.amp, b.z0, b.p, b.prof,
                    b.cast, b.depth, b.taper, b.skew)

    def form(self, f):
        if f.axis is not None:
            a, b = f.axis
            return Form(axis=[self.pt(a), self.pt(b)], r=f.r, flat=f.flat)
        cx, cy, rx, ry = f.ell
        return Form(ellipsoid=(cx, self.y(cy), rx, ry * self.s), flat=f.flat)


# ------------------------------------------------------------------------------------ the body

# the design rig's leg outline (gr_fig.leg), copied as data; its bumps are gr_fig.LEG_BUMPS
LEG_PTS = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6), (53.4, 98.8),
           (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]
# the design rig's torso outline (gr_fig.torso, half, mirrored), as data
TORSO_HALF = [(56, 41.0), (49.6, 41.2), (45.6, 43.2), (41.0, 45.6), (36.4, 48.4), (32.6, 51.2),
              (31.6, 53.6), (33.6, 56.0), (32.4, 61.2), (32.6, 64.6), (34.6, 68.0), (38.6, 71.2),
              (43.4, 74.0), (45.6, 75.6), (46.0, 77.5), (56, 77.5)]
TRUNKS_HALF = [(56, 74.2), (46.0, 74.2), (45.0, 77.0), (44.2, 79.8), (47.4, 81.0), (51.6, 82.6),
               (54.2, 84.0), (56, 84.6)]
BAND_HALF = [(56, 73.8), (45.8, 73.8), (45.3, 75.6), (56, 75.6)]


def leg(side, T, d=0, flare=1.5):
    """The brawl rig's leg (gb_body.leg: the design rig's leg bent d rows, the knee pushed out
    `flare`), then tipped back by T."""
    c = BD.Crouch(d, flare)
    pts = [T.pt(c.pt(p)) for p in LEG_PTS]
    bumps = [T.bump(c.bump(b)) for b in gr_fig.LEG_BUMPS]
    if side:
        pts = K.mpts(pts)
        bumps = [b.mirrored() for b in bumps]
    cx = 46.2 if not side else K.AX - 46.2
    form = T.form(Form(axis=[(cx, c.y(80.0)), (cx, 104.0)], r=9.5))
    return Layer(K.poly(pts), form, bumps, floor=0.2, strength=1.0).shade_owned(cuts=gr_fig.CUTS)[0]


class Drop:
    """The upper body dropped d rows by the crouch, then tipped back by T."""

    def __init__(self, T, d):
        self.T, self.d, self.s = T, d, T.s

    def y(self, y):
        return self.T.y(y + self.d)

    def pt(self, p):
        return (p[0], self.y(p[1]))

    def pts(self, ps):
        return [self.pt(p) for p in ps]

    def bump(self, b):
        shifted = Bump(b.name, (b.c[0], b.c[1] + self.d), b.a, b.b, b.ang, b.amp, b.z0, b.p,
                       b.prof, b.cast, b.depth, b.taper, b.skew)
        return self.T.bump(shifted)

    def form(self, f):
        if f.axis is not None:
            a, b = f.axis
            f = Form(axis=[(a[0], a[1] + self.d), (b[0], b[1] + self.d)], r=f.r, flat=f.flat)
        else:
            cx, cy, rx, ry = f.ell
            f = Form(ellipsoid=(cx, cy + self.d, rx, ry), flat=f.flat)
        return self.T.form(f)


def torso(T, lat_flare=1.0):
    Pz = gr_fig.Pose('idle')
    Pz.lat_flare = lat_flare
    f = lat_flare
    half = [(x - (f if 60 < y < 66 else (f * 0.5 if 66 <= y < 69 else 0.0)), y)
            for (x, y) in TORSO_HALF]
    pix = K.poly(K.sym(T.pts(half)))
    bumps = [T.bump(b) for b in gr_fig.torso_bumps(Pz)]
    bumps = bumps + [b.mirrored() for b in bumps]
    form = T.form(Form(ellipsoid=(55, 58, 25, 24)))
    part = Layer(pix, form, bumps, floor=0.25, strength=1.0).shade_owned(cuts=gr_fig.CUTS,
                                                                        floor_cast=1)[0]
    # the jaw and the mane shade the neck and the top of the chest under them (gr_fig.torso)
    y51, y52 = T.y(51), T.y(52)
    for (x, y) in list(part):
        if 45 <= x <= 67 and y <= y52 + 1e-6:
            steps = 2 if y <= y51 + 1e-6 else 1
            for _ in range(steps):
                part[(x, y)] = K.DARKER[part[(x, y)]]
    return part


def trunks(T):
    part = K.fill(K.poly(K.sym(T.pts(TRUNKS_HALF))), 'C')
    K.ellipsoid(part, 51.5, T.y(76), 15, 10 * T.s, 'ABCDE', (0.86, 0.58, 0.20, -0.25))
    return part


def waistband(T):
    part = K.fill(K.poly(K.sym(T.pts(BAND_HALF))), 'B')
    K.ellipsoid(part, 50, T.y(72), 16, 6 * T.s, 'ABCDE', (0.8, 0.45, 0.0, -0.4))
    return part


def waistband_line(T):
    y = int(round(T.y(76)))
    return [(x, y) for x in range(46, 67)]


def body(cv, T, boots, d=0, flare=1.5, lat_flare=1.0):
    """The brawl rig's front base (gb_body.front_base: legs bent d rows, boots, torso, trunks and
    waistband dropped d), tipped back by T. `boots`: a part (the approved boots standing, the
    turned boots as he goes over). At T.s = 1 this is gb_body.front_base exactly."""
    U = Drop(T, d)
    for side in (0, 1):
        cv.stamp(K.despeckle(leg(side, T, d, flare)))
    cv.stamp(boots, outline=False)
    cv.stamp(K.despeckle(torso(U, lat_flare)))
    cv.stamp(trunks(U))
    cv.stamp(waistband(U), outline=False)
    for p in waistband_line(U):
        cv.px[p] = 'k'
    return U




# ------------------------------------------------------------------------------------ the boots
# Turned soles-to-us as he goes over: the charcoal sole with its tread, the heel block, and the
# white upper showing round the edge and over the toe. STRUCTURE for the LEFT boot ('u' upper,
# 's' sole, 't' tread, 'h' heel, 'k' lines), rows 97-111, x 38-52; shaded afterwards, so the
# mirrored right boot keeps the upper-left light.
SOLE_X0, SOLE_Y0 = 38, 97
SOLE_L = [
    "....kkkkkkk....",   # 97   the toe cap's top edge
    "..kkuuuuuuukk..",   # 98   the toe cap, pointing up
    ".kuuuuuuuuuuuk.",   # 99
    ".kukkkkkkkkkuk.",   # 100  where the sole meets the upper
    "kukssssssssskuk",   # 101  the sole
    "kukssssssssskuk",   # 102
    "kukststststskuk",   # 103  tread
    "kukssssssssskuk",   # 104
    "kukststststskuk",   # 105
    ".kukssssssskuk.",   # 106  the arch
    ".kukssssssskuk.",   # 107
    ".kukkkkkkkkkuk.",   # 108  the heel's front edge
    ".kukhhhhhhhkuk.",   # 109  the heel
    ".kukhhhhhhhkuk.",   # 110
    "..kkkkkkkkkkk..",   # 111  his feet's row
]
for _i, _r in enumerate(SOLE_L):
    assert len(_r) == 15, (SOLE_Y0 + _i, _r, len(_r))


# Halfway over (the fall's middle frame): the toe box tipped up toward us, the front of the sole
# showing under it, the heel still planted on row 111.
TIP_Y0 = 99
TIP_L = [
    "....kkkkkkk....",   # 99   the toe cap tipped up
    "..kkuuuuuuukk..",   # 100
    ".kuuuuuuuuuuuk.",   # 101
    "kuuuuuuuuuuuuuk",   # 102
    "kuuuuuuuuuuuuuk",   # 103
    "kukkkkkkkkkkkuk",   # 104  the sole's toe edge, seen from under
    "kukssssssssskuk",   # 105  the sole
    "kukststststskuk",   # 106  tread
    "kukssssssssskuk",   # 107
    ".kukssssssskuk.",   # 108  the arch
    ".kukkkkkkkkkuk.",   # 109  the heel's front edge
    ".kukhhhhhhhkuk.",   # 110  the heel
    "..kkkkkkkkkkk..",   # 111  his feet's row
]
for _i, _r in enumerate(TIP_L):
    assert len(_r) == 15, (TIP_Y0 + _i, _r, len(_r))


def turned_boots(rows=None, y0=None):
    """Both boots turned toward us (SOLE_L lying, TIP_L halfway), heels on row 111."""
    rows = SOLE_L if rows is None else rows
    y0 = SOLE_Y0 if y0 is None else y0
    out = {}
    for side in (0, 1):
        struct = {}
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == '.':
                    continue
                x = SOLE_X0 + c
                if side:
                    x = K.AX - x
                struct[(x, y0 + r)] = ch
        xs = [x for (x, y), ch in struct.items() if ch != 'k']
        cx = (min(xs) + max(xs)) / 2.0
        upper = {p: 'W' for p, ch in struct.items() if ch == 'u'}
        K.ellipsoid(upper, cx - 1.0, y0 + 4.0, 8.5, 9.0, 'WXx', (0.40, -0.20))
        sole = {p: 'M' for p, ch in struct.items() if ch in 'sth'}
        K.ellipsoid(sole, cx - 1.5, y0 + 5.0, 6.0, 8.0, 'ML', (0.45,))
        for p, ch in struct.items():
            if ch == 't':
                sole[p] = 'L'                     # the tread's grooves
            elif ch == 'h' and p[1] == 110:
                sole[p] = 'L'
        out.update({p: 'k' for p, ch in struct.items() if ch == 'k'})
        out.update(upper)
        out.update(sole)
    return out


def sole_boots():
    return turned_boots(SOLE_L, SOLE_Y0)


def tip_boots():
    return turned_boots(TIP_L, TIP_Y0)


# ------------------------------------------------------------------------------------ the head, lying

# the mane fanned out on the mat round his head (half, mirrored): the back hair spread a little way
# up the screen behind his head, and the two long curtains spilling out over his shoulders onto
# the mat, ending in points
HALO_HALF = [(56, 61.6), (51.8, 62.0), (47.8, 63.0), (44.4, 64.8), (41.8, 67.4), (40.0, 70.4),
             (38.8, 73.6), (37.4, 76.8), (35.4, 79.4), (33.4, 82.0), (32.4, 84.8), (34.4, 85.6),
             (36.2, 84.2), (37.2, 87.0), (39.4, 85.2), (40.8, 87.4), (42.6, 84.2), (44.4, 81.8),
             (46.2, 80.2), (56, 80.2)]
HEAD_C = (56.0, 82.0)       # where the strands spring from (the back of his head, under the face)


def _jitter(i):
    """A fixed wobble per strand, so the strands curve a little and aren't spaced like spokes."""
    return ((i * 37) % 11) / 11.0 - 0.5


def halo():
    pix = K.poly(K.sym(HALO_HALF))
    part = {}
    for (x, y) in pix:
        dx, dy = x - HEAD_C[0], y - HEAD_C[1]
        r = math.hypot(dx, dy / 0.75)
        ang = math.atan2(dy, abs(dx))                 # mirror-symmetric strand layout...
        # ...but the light is not: upper-left brightest
        lit = -(dx / 24.0) * 0.55 - (dy / 18.0) * 0.62
        k = 'b' if lit > 0.20 else ('c' if lit > -0.20 else 'd')
        if lit > 0.62 and r > 12:
            k = 'a'
        # strands: seven each side, each wobbling a little as it runs outward, drawn as a darker
        # line only (lighter stripes between them read as noise at 3x)
        t = (ang + math.pi / 2) / math.pi * 7.0
        i = int(math.floor(t))
        f = t - i + 0.22 * _jitter(i) * (r / 14.0)
        if f < 0.16 and r > 9:
            k = K.DARKER[k]
        part[(x, y)] = k
    # the parting runs straight up the screen from his forehead
    for y in range(62, 70):
        if (56, y) in part:
            part[(56, y)] = 'k'
    return part


FACE_X0, FACE_Y0 = 46, 69


def _rows(pairs):
    out = []
    for i, (l, r) in enumerate(pairs):
        assert len(l) == 11 and len(r) == 10, (FACE_Y0 + i, l, r)
        out.append(l + r)
    return out


# the face lying face-up, seen from the chin end (about six tenths of its standing height): the
# forehead's red chevron, the brows gone slack, KO X eyes behind the gold rims, the nostrils
# showing, the moustache, the jaw hung open with the tongue lolling out over his lip
LYING_FACE = _rows([
    # left x 46-56    right x 57-66       y
    ("..........v", ".........."),   # 69  the vein up to the parting
    ("........1v1", "V2........"),   # 70
    (".....111v22", "2V233....."),   # 71
    ("..1dddd2222", "223eeee4.."),   # 72  brows, slack
    ("12gggGGG222", "23GGGGGG44"),   # 73  the rims' tops
    ("1G2k2k22GGG", "GG33k3k3G4"),   # 74  X eyes
    ("1G22k222G12", "3G333k33G4"),   # 75
    ("1G2k2k22G12", "3G33k3k3G4"),   # 76
    ("12GGGGGG212", "33GGGGGG44"),   # 77  the rims' bottoms
    ("11222222343", "4333333344"),   # 78  the nostrils, seen from under the nose
    ("12223dccccc", "ccdde33344"),   # 79  the moustache
    ("k222dk66666", "66kkd3344k"),   # 80  the jaw hung open
    (".k222kvvVk6", "k3333444k."),   # 81  the tongue out over the lip
    ("..kkkkvVkkk", "kkkkkkk..."),   # 82  the jaw's keyline
    (".....kkk...", ".........."),   # 83  the tongue's tip
])


def lying_head():
    part = K.Canvas()
    part.stamp(halo())
    face = {(FACE_X0 + c, FACE_Y0 + r): ch for r, row in enumerate(LYING_FACE)
            for c, ch in enumerate(row) if ch != '.'}
    part.px.update(face)
    # the face is framed in black where it meets the mane, as the standing mane frames it
    hair = set('abcde')
    for (x, y), ch in face.items():
        if ch == 'k':
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in face and part.px.get(q) in hair:
                part.px[q] = 'k'
    return part.px, set(face)


# ------------------------------------------------------------------------------------ f4, lying

def lying(right_elbow=(16.0, 1.0), right_wrist=(8.0, -7.0), left_elbow=(96.0, 1.0),
          muzzle=(102.0, -10.0), cn_face=0.2):
    """greyson_brawl_ko f4: flat on his back, feet to the player (heels on row 111, soles to us),
    the body receding up the screen at half its standing height, the arms flung out on the mat,
    upper arms out sideways and the forearm and cannon pointing up the screen beside his head, the
    mane fanned out round the KO face. Arm points are (x, rows below the shoulder line)."""
    T = Tilt(0.5)
    cv = Canvas()
    U = body(cv, T, sole_boots(), d=0, lat_flare=1.0)
    sh_y = U.y(56.5)
    d_arm = sh_y - 56.5
    re = (right_elbow[0], sh_y + right_elbow[1])
    rw = (right_wrist[0], sh_y + right_wrist[1])
    le = (left_elbow[0], sh_y + left_elbow[1])
    lm = (muzzle[0], sh_y + muzzle[1])
    cv.stamp(K.despeckle(A.upper_layer(0, d_arm, re)))
    cv.stamp(K.despeckle(A.forearm_layer(re, rw)))
    fist = gr_hands.fist('idle', 0, (rw[0], rw[1] - 1.0))
    cv.stamp(fist, outline=False)
    cv.stamp(K.despeckle(A.upper_layer(1, d_arm, le)))
    cn = gf_cannon.cannon(le, lm, face=cn_face)
    cv.stamp(cn)
    hp, fpx = lying_head()
    cv.px.update(hp)
    P.finish(cv, fpx)
    return cv, {'feet': (56, 111), 'crown': (56, min(y for (x, y) in hp if x == 56)),
                'chin': (56, 84), 'fist': F.fist_centre(fist), 'gauntlet': Z.rnd(lm)}


# ------------------------------------------------------------------------------------ f1-f3, going over

import gz_faces  # noqa: E402


def falling(theta, right, left, head='standing', face='ko_snap', head_dx=0, boots='stand',
            fx=None):
    """One frame of the fall, the body tipped back by theta degrees about his heels.
    right = (elbow, fist) and left = (elbow, muzzle), in the frame's own texels.
    head: 'standing' (the approved mane with `face`, carried by the tilt) or 'lying' (the head
    lying face-up, placed where the tilt puts his jaw)."""
    T = Tilt(s_of(theta))
    cv = Canvas()
    stand = {}
    for side in (0, 1):
        stand.update(gr_boots_part(side))
    U = body(cv, T, stand if boots == 'stand' else (tip_boots() if boots == 'tip' else sole_boots()),
             d=0, lat_flare=1.0)
    d_arm = U.y(56.5) - 56.5
    (re, rf), (le, lm) = right, left
    cv.stamp(K.despeckle(A.upper_layer(1, d_arm, le)))
    cn = gf_cannon.cannon(le, lm, face=0.25)
    cv.stamp(cn)
    cv.stamp(K.despeckle(A.upper_layer(0, d_arm, re)))
    L = math.hypot(rf[0] - re[0], rf[1] - re[1]) or 1.0
    wrist = (rf[0] - (rf[0] - re[0]) / L * 4.0, rf[1] - (rf[1] - re[1]) / L * 4.0)
    cv.stamp(K.despeckle(A.forearm_layer(re, wrist)))
    fist = A.fist_part(rf)
    cv.stamp(fist, outline=False)
    if head == 'standing':
        dy = int(round(U.y(38.0) - 38.0))
        hp, fpx = gz_faces.head(face, head_dx, dy)
        cv.stamp(hp, outline=False)
        crown = P.crown_of(moved(gr_face.mane(), head_dx, dy))
        chin = (56 + head_dx, gz_faces.jaw_row(face) + dy + 2)
    else:
        hp, fpx = lying_head()
        dy = int(round(U.y(50.0) + 1.5 - 82))
        hp, fpx = moved(hp, head_dx, dy), {(x + head_dx, y + dy) for (x, y) in fpx}
        cv.px.update(hp)
        crown = (56 + head_dx, min(y for (x, y) in hp if x == 56 + head_dx))
        chin = (56 + head_dx, 84 + dy)
    if fx:
        cv.px.update(fx)
        fpx = set(fpx) | set(fx)
    P.finish(cv, fpx)
    return cv, {'crown': crown, 'chin': chin, 'fist': Z.rnd(rf), 'gauntlet': Z.rnd(lm),
                'theta': theta}


def gr_boots_part(side):
    return Z.G.gr_boots.boot(side)
