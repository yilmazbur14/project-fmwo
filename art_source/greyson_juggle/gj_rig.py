"""Greyson's juggle rig: the APPROVED rig, carried into a 192x144 frame and turned there.

The approved rig (art_source/greyson_redesign, gr_*) and the fight rig on it (art_source/
greyson_fight, gf_*) belong to another artist. They are imported READ-ONLY, through gf_base, which
proves on import that the approved rig still draws the approved sprite pixel for pixel, and adds
the cannon's two bore darks to the palette in memory. Nothing here edits, or writes into, either
folder (every module sets sys.dont_write_bytecode).

HOW HE TURNS WITHOUT BEING RE-LIT FROM BELOW
Almost all of him is PROCEDURAL in the approved rig: every body part is a traced polygon with a
form (an ellipsoid or a tube) and muscles (gr_muscle Bumps and Regions) that tilt its normal, lit
by one light from the upper left. Nothing of that is a picture, so nothing is rotated as one. A
Tf carries his own space (the approved 112x112 rig's coordinates) into the frame, and each part is
re-built there:
  - the outlines: the approved polygon points, carried by Tf, rasterised in the frame;
  - the volume: the approved form, asked in his own space (Tf.inv) and its normal carried back
    out (Tf.normal, the inverse transpose), so the form turns with him;
  - the muscles: the approved bumps, asked the same way; their slopes are measured in the frame;
  - the light: the rig's own K.lambert, fixed on the screen, upper left.
So every part keeps the approved shapes and volumes at any angle, and is lit from the upper left
at every angle. At the identity each of these reduces to the approved code exactly, and
check_identity() proves it against four approved frames (see there).

THE HAND-DRAWN PARTS (the mane and the face; the fists' and boots' STRUCTURE maps) carry no
normals. The fists and boots are structure only (lines and part labels) and are shaded after the
turn, in the frame, by their approved forms turned as above. The head is carried as a picture: a
quarter turn copies it texel for texel; any other turn goes by three shears (Paeth), which moves
every texel to exactly one texel, so the face's 1px lines (the lens rims, the squeezed eyes, the
mouth) stay whole; a squashed head (the crash) samples a 4x Scale2x upscale (the first half of
RotSprite). Those two get a fresh 1px keyline round them. The head is RE-LIT BY A DELTA first: each
hair and skin pixel moves along its ramp by how much the turn changes the light on a sphere fitted
to the skull, the slope fitted once on the approved head. At angle 0 the delta is zero and the
approved head comes back exactly.

THE CANNON (gf_cannon) is generated along any axis and lit by the screen light already: it is
simply built between its two ends carried into the frame.

Coordinates are the approved rig's: pixel centres on integers, column 56 the mirror axis
(x' = 112 - x), y down. Angles are in degrees on screen, clockwise positive.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
FIGHT = os.path.join(ART, 'greyson_fight')
RIG = os.path.join(ART, 'greyson_redesign')
for _p in (HERE, FIGHT):
    while _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, FIGHT)
import gf_base as B       # noqa: E402  proves the approved rig on import; puts RIG and ART on the path
sys.path.insert(0, HERE)  # this folder first again; every module here is gj_*, so nothing clashes
import gf_fig             # noqa: E402
import gf_faces           # noqa: E402
import gf_cannon          # noqa: E402
import gf_arms            # noqa: E402
import gf_hands           # noqa: E402
from gr_muscle import Bump, Form, Layer, Region, RegionLayer  # noqa: E402

K, gr_fig, gr_arms, gr_hands, gr_face, gr_boots = (B.K, B.gr_fig, B.gr_arms, B.gr_hands,
                                                  B.gr_face, B.gr_boots)
for _m, _d in ((gf_fig, FIGHT), (gf_faces, FIGHT), (gf_cannon, FIGHT), (gf_arms, FIGHT),
               (gf_hands, FIGHT), (K, RIG), (gr_fig, RIG)):
    if os.path.normcase(os.path.dirname(os.path.abspath(_m.__file__))) != os.path.normcase(_d):
        raise ImportError('%s came from %s, not %s' % (_m.__name__, _m.__file__, _d))

W, H = 192, 144
FEET = (96, 143)          # the bottom-centre texel his feet stand on in the ground frames
AX = K.AX
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
L2 = (K.LIGHT3[0], K.LIGHT3[1])
SKIN = '123456'
HAIR = 'abcde'


def mp(p):
    return (AX - p[0], p[1])


# ------------------------------------------------------------------------------------ Tf

def _rot(deg):
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    c = float(round(c)) if abs(c - round(c)) < 1e-12 else c
    s = float(round(s)) if abs(s - round(s)) < 1e-12 else s
    return (c, -s, s, c)


def _snap(v):
    r = float(round(v))
    return r if abs(v - r) < 1e-12 else v


def _mul(m, n):
    """m . n, with entries a hair from 0 or 1 snapped to it (a -120 body turn and a +30 head tilt
    make an exact quarter turn, and should be treated as one)."""
    a, b, c, d = m
    e, f, g, h = n
    return tuple(_snap(v) for v in (a * e + b * g, a * f + b * h, c * e + d * g, c * f + d * h))


class Tf(object):
    """His own space -> the frame:  P = A (p - pivot) + dest,  A = (a b; c d).
    `angle` is the rotation A carries (for the head's relight), clockwise positive on screen."""

    def __init__(self, m=(1.0, 0.0, 0.0, 1.0), pivot=(0.0, 0.0), dest=None, angle=0.0):
        self.m = tuple(float(v) for v in m)
        self.pivot = (float(pivot[0]), float(pivot[1]))
        self.dest = self.pivot if dest is None else (float(dest[0]), float(dest[1]))
        self.angle = float(angle)
        a, b, c, d = self.m
        det = a * d - b * c
        self.im = (d / det, -b / det, -c / det, a / det)
        self.ident = self.m == (1.0, 0.0, 0.0, 1.0) and self.dest == self.pivot

    @staticmethod
    def make(angle=0.0, pivot=(56.0, 70.0), dest=None, squash=(1.0, 1.0)):
        """Turn `angle` about `pivot` (his own space), put the pivot on `dest` (the frame), then
        squash on the screen (x, y) about it."""
        m = _mul((float(squash[0]), 0.0, 0.0, float(squash[1])), _rot(angle))
        return Tf(m, pivot, dest, angle)

    def fwd(self, x, y):
        if self.ident:
            return (x, y)
        a, b, c, d = self.m
        dx, dy = x - self.pivot[0], y - self.pivot[1]
        return (a * dx + b * dy + self.dest[0], c * dx + d * dy + self.dest[1])

    def inv(self, X, Y):
        if self.ident:
            return (X, Y)
        a, b, c, d = self.im
        dx, dy = X - self.dest[0], Y - self.dest[1]
        return (a * dx + b * dy + self.pivot[0], c * dx + d * dy + self.pivot[1])

    def normal(self, nx, ny):
        """A normal's (x, y) carried into the frame: the inverse transpose of A. z is unchanged
        (a squash in the picture plane leaves depth alone)."""
        if self.ident:
            return (nx, ny)
        a, b, c, d = self.im
        return (a * nx + c * ny, b * nx + d * ny)

    def vec(self, vx, vy):
        a, b, c, d = self.m
        return (a * vx + b * vy, c * vx + d * vy)

    def sub(self, pivot, turn, shift=(0.0, 0.0)):
        """A part hinged at `pivot` (his own space), turned a further `turn` degrees there and
        moved `shift` (his own space): a limb swung at its joint, a head tipped on the neck."""
        if turn == 0 and shift == (0.0, 0.0):
            return self
        return Tf(_mul(self.m, _rot(turn)), pivot,
                  self.fwd(pivot[0] + shift[0], pivot[1] + shift[1]), self.angle + turn)

    def quarter(self):
        return all(v in (0.0, 1.0, -1.0) for v in self.m) and abs(self.m[0] * self.m[3]
                                                                   - self.m[1] * self.m[2]) == 1.0

    def whole(self):
        """A quarter turn (or none) landing pixel centres on pixel centres: a pixel map then
        moves texel for texel."""
        if not self.quarter():
            return False
        X, Y = self.fwd(0.0, 0.0)
        return abs(X - round(X)) < 1e-9 and abs(Y - round(Y)) < 1e-9


IDENT = Tf()


# ------------------------------------------------------------------------------------ wrappers

class TForm(object):
    """An approved Form, asked in his own space and its normal carried into the frame."""

    def __init__(self, form, T):
        self.form, self.T = form, T

    def normal(self, X, Y):
        x, y = self.T.inv(X, Y)
        n = self.form.normal(x, y)
        nx, ny = self.T.normal(n[0], n[1])
        return (nx, ny, n[2])


def tform(form, T):
    return form if T.ident else TForm(form, T)


class TBump(object):
    """An approved Bump, asked in his own space; its slope is measured in the frame (the same
    finite difference as Bump.grad), so it turns with him."""

    def __init__(self, bump, T):
        self.b, self.T = bump, T
        self.name, self.cast, self.depth, self.z0 = bump.name, bump.cast, bump.depth, bump.z0

    def h(self, X, Y):
        x, y = self.T.inv(X, Y)
        return self.b.h(x, y)

    def grad(self, X, Y, e=0.35):
        def hh(px, py):
            v = self.h(px, py)
            return self.z0 if v is None else v
        return ((hh(X + e, Y) - hh(X - e, Y)) / (2 * e), (hh(X, Y + e) - hh(X, Y - e)) / (2 * e))


def tbumps(bumps, T):
    return bumps if T.ident else [TBump(b, T) for b in bumps]


def tpoly(pts, T):
    return K.poly([T.fwd(x, y) for (x, y) in pts])


def tpixels(pixels, T):
    """A set of his pixels (a 1px line, say) in the frame: every frame pixel whose centre falls in
    one of them. Exact at the identity; a connected line at any angle."""
    if T.ident:
        return set(pixels)
    pix = set(pixels)
    xs, ys = [], []
    for (x, y) in pix:
        for dx in (-0.5, 0.5):
            for dy in (-0.5, 0.5):
                X, Y = T.fwd(x + dx, y + dy)
                xs.append(X)
                ys.append(Y)
    out = set()
    for Y in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for X in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            x, y = T.inv(X, Y)
            if (int(math.floor(x + 0.5)), int(math.floor(y + 0.5))) in pix:
                out.add((X, Y))
    return out


def t_ellipsoid(part, T, cx, cy, rx, ry, ramp, cuts, bulge=1.0):
    """K.ellipsoid, asked in his own space."""
    for (X, Y) in list(part):
        x, y = T.inv(X, Y)
        u = (x - cx) / rx
        v = (y - cy) / ry
        r2 = u * u + v * v
        z = math.sqrt(max(0.0, 1.0 - min(1.0, r2))) * bulge
        nu, nv = T.normal(u, v)
        part[(X, Y)] = K.tone(K.lambert((nu, nv, z)), ramp, cuts)


def cylinder_n(x, y, p0, p1, r, tilt=0.0):
    """K.cylinder's normal at a point of his own space."""
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    al = math.hypot(ax, ay) or 1.0
    ax, ay = ax / al, ay / al
    nx, ny = -ay, ax
    s = ((x - x0) * nx + (y - y0) * ny) / r
    s = max(-1.0, min(1.0, s))
    z = math.sqrt(max(0.0, 1.0 - s * s))
    return (s * nx - tilt * ax, s * ny - tilt * ay, z)


def ellipsoid_n(x, y, cx, cy, rx, ry, bulge=1.0):
    """K.ellipsoid's normal at a point of his own space."""
    u = (x - cx) / rx
    v = (y - cy) / ry
    r2 = u * u + v * v
    return (u, v, math.sqrt(max(0.0, 1.0 - min(1.0, r2))) * bulge)


def lit(T, n):
    """The tone intensity of a normal of his own space, turned into the frame."""
    nx, ny = T.normal(n[0], n[1])
    return K.lambert((nx, ny, n[2]))


# ------------------------------------------------------------------------------------ pixel maps

def scale2x(grid):
    """Scale2x / EPX on a {(x, y): key} map within its bbox -> (the 2x map in local coordinates,
    the bbox's first pixel)."""
    xs = [q[0] for q in grid]
    ys = [q[1] for q in grid]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1

    def at(x, y):
        return grid.get((x0 + x, y0 + y), '.') if (0 <= x < w and 0 <= y < h) else '.'

    out = {}
    for y in range(h):
        for x in range(w):
            p = grid.get((x0 + x, y0 + y), '.')
            a, b, c, d = at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            e = (c if (c == a and c != d and a != b) else p,
                 a if (a == b and a != c and b != d) else p,
                 d if (d == c and d != b and c != a) else p,
                 b if (b == d and b != a and d != c) else p)
            for i, k in enumerate(e):
                if k != '.':
                    out[(2 * x + (i & 1), 2 * y + (i >> 1))] = k
    return out, (x0, y0)


def fill_outline(part):
    """The map with its OUTER keyline replaced by the colour beside it, so a turn samples a solid
    silhouette and a fresh 1px keyline can be drawn round the turned shape. Interior black (the
    parting, the glasses' lash lines, the mouth, the fists' finger lines) is kept."""
    body = set(part)
    outer = {q for q, k in part.items()
             if k == 'k' and any((q[0] + dx, q[1] + dy) not in body for dx, dy in N4)}
    out = dict(part)
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in sorted(todo):
            nb = [out[(x + dx, y + dy)] for dx, dy in N8
                  if (x + dx, y + dy) in out and (x + dx, y + dy) not in todo
                  and out[(x + dx, y + dy)] != 'k']
            if nb:
                # sorted before the tie-break: a set of one-letter keys iterates in an order that
                # changes with the per-process string hash seed
                out[(x, y)] = max(sorted(set(nb)), key=nb.count)
                done.append((x, y))
        if not done:
            for q in todo:
                del out[q]
            break
        todo -= set(done)
    return out


def _rnd(v):
    return int(math.floor(v + 0.5))


def sheared(part, T, pivot):
    """A map turned by THREE SHEARS (Paeth): x += a*y, y += b*x, x += a*y with a = -tan(t/2),
    b = sin(t), each rounded to whole pixels. Every texel lands on exactly one texel -- nothing is
    resampled, nothing lost, nothing doubled -- so a 1px line (a lens rim, a squeezed eye, the
    mouth) stays one unbroken pixel line, stepped. For a pure turn about a pixel-centre pivot.
    -> (frame map, source)."""
    t = math.radians(T.angle)
    a, b = -math.tan(t / 2.0), math.sin(t)
    DX, DY = T.fwd(*pivot)
    DX, DY = _rnd(DX), _rnd(DY)
    px, py = int(pivot[0]), int(pivot[1])
    out, src = {}, {}
    for (x, y), k in part.items():
        dx, dy = x - px, y - py
        x1 = dx + _rnd(a * dy)
        y1 = dy + _rnd(b * x1)
        x2 = x1 + _rnd(a * y1)
        q = (x2 + DX, y1 + DY)
        out[q] = k
        src[q] = (x, y)
    return out, src


def pure_turn(T):
    """T is a turn and a move only (no squash)."""
    a, b, c, d = T.m
    return abs(a * a + c * c - 1.0) < 1e-9 and abs(b * b + d * d - 1.0) < 1e-9 and \
        abs(a * b + c * d) < 1e-9 and a * d - b * c > 0


def turned(part, T, shear_pivot=None):
    """A {(x, y): key} map of his own space, carried into the frame by T.
    -> (frame map, source: {frame pixel: the his-space pixel it came from}, needs_outline).
    A quarter turn (or none) copies texel for texel and keeps the map's own keyline. Given a
    pixel-centre `shear_pivot`, any other pure turn goes by three shears (sheared). Anything else
    (a squash) samples a 4x Scale2x upscale of the map. Both of those fill the map's outer keyline
    first and need a fresh 1px keyline stamped round the result."""
    if T.quarter():
        # a quarter turn moves every texel by the same whole-pixel pattern: copied texel for
        # texel, a fractional placement rounded the same way for all of them (floor(v + 0.5),
        # never round(), whose ties go to the even number and would tear the map apart)
        out, src = {}, {}
        for (x, y), k in part.items():
            X, Y = T.fwd(x, y)
            q = (_rnd(X), _rnd(Y))
            out[q] = k
            src[q] = (x, y)
        return out, src, False
    if shear_pivot is not None and pure_turn(T):
        out, src = sheared(fill_outline(part), T, shear_pivot)
        return out, src, True
    big1, o1 = scale2x(fill_outline(part))
    big2, _ = scale2x(big1)
    xs = [q[0] for q in part]
    ys = [q[1] for q in part]
    corners = [T.fwd(a, b) for a in (min(xs) - 0.5, max(xs) + 0.5)
               for b in (min(ys) - 0.5, max(ys) + 0.5)]
    X0 = int(math.floor(min(p[0] for p in corners))) - 1
    X1 = int(math.ceil(max(p[0] for p in corners))) + 1
    Y0 = int(math.floor(min(p[1] for p in corners))) - 1
    Y1 = int(math.ceil(max(p[1] for p in corners))) + 1
    out, src = {}, {}
    for Y in range(Y0, Y1 + 1):
        for X in range(X0, X1 + 1):
            u, v = T.inv(X, Y)
            i = int(math.floor((u + 0.5 - o1[0]) * 4))
            j = int(math.floor((v + 0.5 - o1[1]) * 4))
            k = big2.get((i, j))
            if k is not None:
                out[(X, Y)] = k
                src[(X, Y)] = (int(math.floor(u + 0.5)), int(math.floor(v + 0.5)))
    return out, src, True


# ------------------------------------------------------------------------------------ the parts
# The approved parts, each re-built in the frame through a Tf. The polygon points below are the
# approved rig's own, copied because they live inside its functions; check_identity() proves the
# copies (and everything else here) against the approved frames on every build.

CUTS = gr_fig.CUTS
LEG_PTS = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6),
           (53.4, 98.8), (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]


def t_leg(side, T):
    """gr_fig.leg."""
    bumps = gr_fig.side_bumps(gr_fig.LEG_BUMPS, side)
    pix = tpoly(gr_fig.mps(LEG_PTS, side), T)
    c = gr_fig.mp((46.2, 90), side)
    form = Form(axis=[(c[0], 80), (c[0], 104)], r=9.5)
    lay = Layer(pix, tform(form, T), tbumps(bumps, T), floor=0.2, strength=1.0)
    return lay.shade_owned(cuts=CUTS)[0]


def torso_half(f):
    return [(56, 41.0), (49.6, 41.2), (45.6, 43.2), (41.0, 45.6), (36.4, 48.4), (32.6, 51.2),
            (31.6, 53.6), (33.6, 56.0), (32.4 - f, 61.2), (32.6 - f, 64.6), (34.6 - f * 0.5, 68.0),
            (38.6, 71.2), (43.4, 74.0), (45.6, 75.6), (46.0, 77.5), (56, 77.5)]


def t_torso(flare, T):
    """gr_fig.torso with the lats flared `flare` (the approved Pose.lat_flare). The jaw's and the
    mane's shadow over the neck is asked in his own space, so it stays under his jaw."""
    P = gr_fig.Pose('idle')
    P.lat_flare = flare
    pix = tpoly(K.sym(torso_half(flare)), T)
    form = Form(ellipsoid=(55, 58, 25, 24))
    lay = Layer(pix, tform(form, T), tbumps(gr_fig.both(gr_fig.torso_bumps(P)), T), floor=0.25,
                strength=1.0)
    part = lay.shade_owned(cuts=CUTS, floor_cast=1)[0]
    for (X, Y) in list(part):
        x, y = T.inv(X, Y)
        if 45 <= x <= 67 and y <= 52:
            steps = 2 if y <= 51 else 1
            for _ in range(steps):
                part[(X, Y)] = K.DARKER[part[(X, Y)]]
    return part


TRUNKS_PTS = [(56, 74.2), (46.0, 74.2), (45.0, 77.0), (44.2, 79.8), (47.4, 81.0), (51.6, 82.6),
              (54.2, 84.0), (56, 84.6)]
BAND_PTS = [(56, 73.8), (45.8, 73.8), (45.3, 75.6), (56, 75.6)]


def t_trunks(T):
    part = K.fill(tpoly(K.sym(TRUNKS_PTS), T), 'C')
    t_ellipsoid(part, T, 51.5, 76, 15, 10, 'ABCDE', (0.86, 0.58, 0.20, -0.25))
    return part


def t_waistband(T):
    part = K.fill(tpoly(K.sym(BAND_PTS), T), 'B')
    t_ellipsoid(part, T, 50, 72, 16, 6, 'ABCDE', (0.8, 0.45, 0.0, -0.4))
    return part


def t_waistband_line(T):
    return tpixels(gr_fig.waistband_line(), T)


def t_boot(side, T):
    """gr_boots.boot: the approved structure map carried into the frame, then shaded there by the
    approved shaft (a tube), toe (an ellipsoid) and sole rules asked in his own space.
    -> (part, needs_outline)."""
    rows = gr_boots._rows()
    part = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            x = gr_boots.X0 + c
            if side:
                x = K.AX - x
            part[(x, gr_boots.Y0 + r)] = ch
    body = [p for p, ch in part.items() if ch in 'cstl']
    xs = [p[0] for p in body]
    cx = (min(xs) + max(xs)) / 2.0
    lab, _, ol = turned(part, T)
    # the sole's lit edge: the approved rule (its top row, its left half) is the edge facing the
    # light; turned, it is whichever row and half face the light now
    up_lit = (T.normal(0.0, -1.0)[0] * L2[0] + T.normal(0.0, -1.0)[1] * L2[1]) > 0
    left_lit = (T.normal(-1.0, 0.0)[0] * L2[0] + T.normal(-1.0, 0.0)[1] * L2[1]) > 0
    out = {}
    for q, ch in lab.items():
        if ch == 'k':
            out[q] = 'k'
            continue
        x, y = T.inv(*q)
        if ch in 'csl':
            k = K.tone(lit(T, cylinder_n(x, y, (cx - 0.5, 96), (cx - 0.5, 112), 6.8)), 'WXx',
                       (0.34, -0.30))
            if ch == 'c':
                k = K.DARKER[k]
            elif ch == 'l':
                k = 'x'
        elif ch == 't':
            k = K.tone(lit(T, ellipsoid_n(x, y, cx - 1.5, 105.5, 9.5, 4.0)), 'WXx', (0.34, -0.25))
        else:  # 'o', the sole
            row = int(math.floor(y + 0.5))
            top = (row == 109) if up_lit else (row == 110)
            half = (x < cx) if left_lit else (x > cx)
            k = 'M' if (top and half) else 'L'
        out[q] = k
    return out, ol


def t_arm_layer(polys, forms, spec, side, Ts, keep=None):
    """gf_fig.arm_layer (and so gr_arms.arm) with each region carried by its own Tf: Ts maps a
    region name to its Tf (the upper arm's regions by the upper bone, the forearm's by the lower
    one, the delt by its own). The layer's base form goes with the upper arm."""
    regions = []
    for name, pts in polys.items():
        if keep is not None and name not in keep:
            continue
        amp, rnd, cast, depth = spec[name]
        pts = K.mpts(pts) if side else pts
        form = gr_arms._mirror_form(forms[name]) if side else forms[name]
        T = Ts[name]
        regions.append(Region(name, tpoly(pts, T), amp=amp, round_px=rnd, cast=cast, depth=depth,
                              form=tform(form, T)))
    base = forms['upper'] if not side else gr_arms._mirror_form(forms['upper'])
    return RegionLayer(tform(base, Ts['upper']), regions).shade(cuts=gr_arms.CUTS)[0]


def _structure_part(rows, side, center):
    """gr_hands' structure map placed with its anchor on `center` (his own space, left-side
    coordinates, mirrored for side 1), as gr_hands.fist places it."""
    px, (ax, ay) = gr_hands._structure(rows, side)
    cx = int(round(K.AX - center[0])) if side else int(round(center[0]))
    cy = int(round(center[1]))
    return {(cx + c - ax, cy + r - ay): ch for (c, r), ch in px.items()}


def t_hand(rows, side, center, T):
    """gr_hands.fist / gf_hands.hand: the structure carried into the frame, each finger segment
    shaded there as its own pillow under the approved hand-wide form (fitted in his own space,
    turned). -> (part, needs_outline)."""
    placed = _structure_part(rows, side, center)
    skin = [p for p, ch in placed.items() if ch == 's']
    xs = [p[0] for p in skin]
    ys = [p[1] for p in skin]
    form = Form(ellipsoid=((min(xs) + max(xs)) / 2.0 - 0.5, (min(ys) + max(ys)) / 2.0 - 0.5,
                           (max(xs) - min(xs)) / 2.0 + 2.0, (max(ys) - min(ys)) / 2.0 + 2.0))
    lab, _, ol = turned(placed, T)
    skin_f = [p for p, ch in lab.items() if ch == 's']
    regions = [Region('seg%d' % i, comp, amp=1.2, round_px=1.6, cast=0, depth=0)
               for i, comp in enumerate(gr_hands._components(skin_f))]
    shaded = RegionLayer(tform(form, T), regions).shade(cuts=gr_hands.CUTS, lines=False)[0]
    out = {p: 'k' for p, ch in lab.items() if ch == 'k'}
    out.update(shaded)
    return out, ol


# ------------------------------------------------------------------------------------ the head

HEAD_SPHERE = (56.0, 41.0, 17.0, 17.0)   # the skull: crown row 26, jaw row 50, cheeks 39-73


def _sphere_n(x, y, sph):
    cx, cy, rx, ry = sph
    u, v = (x - cx) / rx, (y - cy) / ry
    d = u * u + v * v
    if d > 0.97:
        s = math.sqrt(0.97 / d)
        u, v, d = u * s, v * s, 0.97
    return (u, v, math.sqrt(1.0 - d))


def _dot(n, l):
    return n[0] * l[0] + n[1] * l[1] + n[2] * l[2]


def _fit_steps(part, sph, ramp):
    """Ramp steps per unit of light, fitted on the approved map itself: the least-squares slope of
    tone index against the sphere's lighting, over the ramp's own pixels."""
    pts = [(_dot(_sphere_n(x, y, sph), K.LIGHT3), ramp.index(k))
           for (x, y), k in part.items() if k in ramp]
    if len(pts) < 8:
        return 4.0
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    return max(1.0, -sxy / sxx) if sxx else 4.0


# Fitted ONCE, on the approved idle head, never on whichever head is relit first.
HEAD_STEPS = {SKIN: _fit_steps(gr_face.head('idle'), HEAD_SPHERE, SKIN),
              HAIR: _fit_steps(gr_face.head('idle'), HEAD_SPHERE, HAIR)}


def relight(part, turn_deg, sph=HEAD_SPHERE):
    """Every skin and hair pixel of a head map (his own space, before it is turned) moved along its
    ramp by the change in light the turn makes on the fitted sphere. 0 changes nothing."""
    if abs(turn_deg) < 1e-9:
        return dict(part)
    t = math.radians(turn_deg)
    co, si = math.cos(t), math.sin(t)
    lx, ly, lz = K.LIGHT3
    lb = (lx * co + ly * si, -lx * si + ly * co, lz)     # the light as the turned head sees it
    out = dict(part)
    for ramp in (SKIN, HAIR):
        k_per = HEAD_STEPS[ramp]
        for (x, y), k in part.items():
            if k not in ramp:
                continue
            n = _sphere_n(x, y, sph)
            d = _dot(n, lb) - _dot(n, K.LIGHT3)
            i = ramp.index(k) - int(round(d * k_per))
            out[(x, y)] = ramp[max(0, min(len(ramp) - 1, i))]
    return out


def t_head(part, face_px, T, pivot=None):
    """A head map (the mane with a face over it) carried into the frame by T, re-lit first. With a
    pixel-centre `pivot` (the neck), a turn that is not a quarter turn goes by three shears, which
    keeps the face's 1px lines whole. -> (part, the frame pixels that came from the face (for the
    final sweep to keep), outline?)"""
    if T.ident:
        return dict(part), set(face_px), False
    lab, src, ol = turned(relight(part, T.angle), T, shear_pivot=pivot)
    face = set(face_px)
    keep = {q for q, s in src.items() if s in face}
    return lab, keep, ol


# ------------------------------------------------------------------------------------ joints
# His own space, the approved idle's joints (gf_limb's S0 / E0 / W0; the idle fist's anchor; the
# fight idle's cannon ends), for the LEFT side; mp() gives the right side's.
SHOULDER = (30.0, 56.0)
ELBOW = (21.0, 71.0)
WRIST = (25.0, 82.0)
FIST = (25.0, 84.5)
CANNON_SOCKET = (21.4, 70.0)
CANNON_MUZZLE = (13.8, 95.0)
CANNON_LEN = math.hypot(CANNON_MUZZLE[0] - CANNON_SOCKET[0], CANNON_MUZZLE[1] - CANNON_SOCKET[1])
HIP = (47.0, 81.0)
NECK = (56.0, 48.0)
UPPER = ('upper', 'biceps')
LOWER = ('forearm', 'brach')


def bearing(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


# ------------------------------------------------------------------------------------ identity

def _forced_identity():
    """The identity WITHOUT the short cut: every wrapper (TForm, TBump, tpoly, tpixels, the boot's
    and hands' shading, the head's relight and turn) then runs its full arithmetic, which must
    still land exactly on the approved numbers (1, 0 and 0 in the matrix are exact)."""
    T = Tf()
    T.ident = False
    return T


def _canvas_identity(frame, T=IDENT):
    """One approved frame re-built through this rig at the identity."""
    cv = K.Canvas()
    flare = {'idle': 0.5, 'flex': 1.5, 'pose_b': 1.5, 'spirit': 1.0}[frame]
    for side in (0, 1):
        cv.stamp(K.despeckle(t_leg(side, T)))
    for side in (0, 1):
        part, ol = t_boot(side, T)
        cv.stamp(part, outline=ol)
    cv.stamp(K.despeckle(t_torso(flare, T)))
    cv.stamp(t_trunks(T))
    cv.stamp(t_waistband(T), outline=False)
    for q in t_waistband_line(T):
        cv.px[q] = 'k'
    every = {n: T for n in ('delt', 'upper', 'biceps', 'forearm', 'brach')}
    if frame in ('idle', 'flex'):
        polys = gr_arms.IDLE if frame == 'idle' else gr_arms.FLEX
        forms = gr_arms.IDLE_FORMS if frame == 'idle' else gr_arms.FLEX_FORMS
        spec = gr_arms.SPEC if frame == 'idle' else gr_arms.FLEX_SPEC
        for side in (0, 1):
            cv.stamp(K.despeckle(t_arm_layer(polys, forms, spec, side, every)))
        P = gr_fig.Pose(frame)
        for side in (0, 1):
            part, ol = t_hand(gr_hands.MAPS[frame], side, P.fist, T)
            cv.stamp(part, outline=ol)
        head, keep, ol = t_head(gr_face.head(P.face), gr_face.face(P.face), T)
        cv.stamp(head, outline=ol)
        K.despeckle(cv.px, keep=keep)        # gr_fig.build's own last sweep (no pinhole pass)
        return cv
    elif frame == 'pose_b':
        cv.stamp(K.despeckle(t_arm_layer(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC, 0,
                                         every)))
        cv.stamp(K.despeckle(t_arm_layer(gr_arms.FLEX, gr_arms.FLEX_FORMS, gr_arms.FLEX_SPEC, 1,
                                         every, keep=('delt', 'biceps', 'upper'))))
        cv.stamp(gf_cannon.cannon(T.fwd(*mp((13.6, 58.0))), T.fwd(*mp((15.0, 28.0))), face=0.5))
        part, ol = t_hand(gr_hands.MAPS['flex'], 0, (15.0, 40.0), T)
        cv.stamp(part, outline=ol)
        head, keep, ol = t_head(gr_face.head('flex'), gr_face.face('flex'), T)
        cv.stamp(head, outline=ol)
    else:  # spirit
        cv.stamp(K.despeckle(t_arm_layer(gr_arms.IDLE, gr_arms.IDLE_FORMS, gr_arms.SPEC, 0,
                                         every)))
        cv.stamp(K.despeckle(t_arm_layer(gf_arms.RAISED, gf_arms.RAISED_FORMS,
                                         gf_arms.RAISED_SPEC, 1, every)))
        ex, ey = gf_arms.RAISED_ELBOW
        cv.stamp(gf_cannon.cannon(T.fwd(*mp((ex, ey + 1.5))), T.fwd(*mp((ex + 0.4, 7.0))),
                                  face=0.5))
        part, ol = t_hand(gr_hands.MAPS['idle'], 0, (25.0, 84.5), T)
        cv.stamp(part, outline=ol)
        head, keep, ol = t_head(gf_faces.head('roar'), gf_faces.face('roar'), T)
        cv.stamp(head, outline=ol)
    return gf_fig.finish(cv, keep)


def check_identity():
    """Four approved frames re-built through the juggle rig at the identity (every Tf, TForm,
    TBump, tpoly, tpixels, turned and relight path at angle 0) must equal the approved ones pixel
    for pixel: the approved sprite's idle and flex (gr_fig.build), and the fight approval's front
    double biceps and spirit raise (gf_fig; its two back views and its barbell idle are not drawn
    here). -> [(name, None or the first differences)]."""
    refs = {'idle': gr_fig.build('idle').px, 'flex': gr_fig.build('flex').px,
            'pose_b': gf_fig.pose_b().px, 'spirit': gf_fig.spirit().px}
    out = []
    for name, ref in refs.items():
        for label, T in (('', IDENT), (' (no short cut)', _forced_identity())):
            mine = _canvas_identity(name, T).px
            diff = sorted(set(ref) ^ set(mine)) + sorted(q for q in set(ref) & set(mine)
                                                          if ref[q] != mine[q])
            out.append((name + label, diff[:6] if diff else None))
    return out


if __name__ == '__main__':
    for name, d in check_identity():
        print('%-22s %s' % (name, 'identical' if d is None else 'DIFFERS %s' % d))
    print('head relight steps per unit of light: skin %.2f, hair %.2f'
          % (HEAD_STEPS[SKIN], HEAD_STEPS[HAIR]))
