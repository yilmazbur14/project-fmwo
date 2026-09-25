"""Carter's juggle frames: the APPROVED polish rig, carried into a 192x144 frame.

The rig in art_source/carter_polish is imported read-only (its README's rule), and so is its lib: the
key-per-pixel Canvas and the approved palette are THE canvas and palette here.  carter_akuma's own lib
is never loaded in this interpreter -- the 天 comes through carter_polish/mark.py, which runs that rig
in a subprocess.

HOW HE TURNS WITHOUT BEING RE-LIT FROM BELOW
Everything the three-quarter rig (rig34) draws from joints -- limbs, fists, caps, the torso's skin --
chooses its lit side from the SCREEN light (rig34.LIGHT), so the joints are simply carried into the
frame and drawn there: the rig's own volumes, lit from the upper left whatever angle he is at.

A few of its parts bake the light, or gravity, into BODY coordinates: the jacket is lighter toward the
collar, the feet toward their tops, the trousers turn violet below the hips, the belt is levelled, the
beads sag.  Those are recomputed here the only way that keeps them exact: every frame pixel is mapped
BACK into his own 96x96 space (Tf.inv) and asked the rig's own question there -- except the light,
which is asked in the frame.  At angle 0 each reduces to rig34's own code, pixel for pixel, and
check_identity() proves it against the approved sheets.

The head is hand-drawn (head.HEAD), so it carries no normals.  It is turned by inverse sampling (an
exact copy at a quarter turn; Scale2x-smoothed at any other angle, the first half of RotSprite) and
RE-LIT BY A DELTA: every skin and beard pixel moves along its ramp by how much the turn changed the
light on a sphere fitted to the skull.  The hand-drawn detail rides along untouched; at angle 0 the
delta is zero, so the approved head is reproduced exactly.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
POLISH = os.path.join(ART, 'carter_polish')
for _p in (HERE, POLISH):
    if _p in sys.path:
        sys.path.remove(_p)
sys.path.insert(0, HERE)
sys.path.insert(1, POLISH)
sys.path.insert(2, ART)

import lib as L            # noqa: E402  carter_polish/lib.py, read-only
import head as HD          # noqa: E402
import faces as FC         # noqa: E402
import rig34 as RG         # noqa: E402

assert os.path.dirname(os.path.abspath(L.__file__)) == POLISH, 'lib resolved to the wrong rig'

W, H = 192, 144
FEET = (96, 143)             # bottom-centre texel his feet stand on (ground frames)
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
SKIN = 'stuvwW'
BEARD = '123456'


class Tf(object):
    """His own 96-space -> the juggle frame:  p' = Squash . Turn(angle) . (p - pivot) + dest.
    angle in degrees, clockwise-positive on screen (y down); negative tips him backwards."""

    def __init__(self, angle=0.0, dest=(96.0, 72.0), pivot=(47.5, 64.0), squash=(1.0, 1.0)):
        self.angle = float(angle)
        t = math.radians(self.angle)
        self.co, self.si = math.cos(t), math.sin(t)
        for v in ('co', 'si'):
            r = round(getattr(self, v))
            if abs(getattr(self, v) - r) < 1e-12:
                setattr(self, v, float(r))
        self.pivot = (float(pivot[0]), float(pivot[1]))
        self.dest = (float(dest[0]), float(dest[1]))
        self.sq = (float(squash[0]), float(squash[1]))
        self.scale = math.sqrt(self.sq[0] * self.sq[1])

    def fwd(self, x, y):
        dx, dy = x - self.pivot[0], y - self.pivot[1]
        rx = dx * self.co - dy * self.si
        ry = dx * self.si + dy * self.co
        return (rx * self.sq[0] + self.dest[0], ry * self.sq[1] + self.dest[1])

    def inv(self, X, Y):
        rx = (X - self.dest[0]) / self.sq[0]
        ry = (Y - self.dest[1]) / self.sq[1]
        return (rx * self.co + ry * self.si + self.pivot[0],
                -rx * self.si + ry * self.co + self.pivot[1])

    def turn(self, nx, ny):
        return (nx * self.co - ny * self.si, nx * self.si + ny * self.co)

    def unturn(self, nx, ny):
        return (nx * self.co + ny * self.si, -nx * self.si + ny * self.co)

    def sub(self, pivot, turn, shift=(0.0, 0.0)):
        """A part hinged at `pivot` (his own space), turned a further `turn` degrees and shifted
        `shift` (his own space) -- a head tipped on the neck."""
        return Tf(self.angle + turn, dest=self.fwd(pivot[0] + shift[0], pivot[1] + shift[1]),
                  pivot=pivot, squash=self.sq)

    def quarter(self):
        return (self.sq == (1.0, 1.0) and abs(self.co) in (0.0, 1.0)
                and abs(self.si) in (0.0, 1.0))

    def whole(self):
        """True when this is a quarter turn landing on whole pixels -- then a pixel map moves texel
        for texel and needs no resampling at all."""
        if not self.quarter():
            return False
        X, Y = self.fwd(0.5, 0.5)
        return abs((X - 0.5) - round(X - 0.5)) < 1e-9 and abs((Y - 0.5) - round(Y - 0.5)) < 1e-9


def canvas():
    return L.Canvas(W, H)


# ------------------------------------------------------------ pixel maps, turned
def scale2x(grid):
    """Scale2x / EPX on a {(x, y): key} map within its bbox; '.' is empty."""
    xs = [q[0] for q in grid]
    ys = [q[1] for q in grid]
    x0, y0 = min(xs), min(ys)
    w, h = max(xs) - x0 + 1, max(ys) - y0 + 1

    def at(x, y):
        return grid.get((x0 + min(max(x, 0), w - 1), y0 + min(max(y, 0), h - 1)), '.') \
            if (0 <= x < w and 0 <= y < h) else '.'

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
    """The part with its OUTER keyline replaced by the colour beside it, so a turn samples a solid
    silhouette and the keyline can be drawn fresh at 1px round the turned shape.  Interior black
    (brows, lids, the mouth line) is kept."""
    body = set(part)
    outer = {q for q, k in part.items()
             if k == 'k' and any((q[0] + dx, q[1] + dy) not in body for dx, dy in N4)}
    out = dict(part)
    todo = set(outer)
    while todo:
        done = []
        for (x, y) in todo:
            nb = [out[(x + dx, y + dy)] for dx, dy in N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
                  if (x + dx, y + dy) in out and (x + dx, y + dy) not in todo
                  and out[(x + dx, y + dy)] != 'k']
            if nb:
                # SORTED before the tie-break: a set of one-letter keys iterates in an order that
                # changes with Python's per-process string hash seed, so max(set(...)) would settle
                # a tie differently from one run to the next
                out[(x, y)] = max(sorted(set(nb)), key=nb.count)
                done.append((x, y))
        if not done:
            for q in todo:
                del out[q]
            break
        todo -= set(done)
    return out


def turned(part, T):
    """A {(x, y): key} map of his own space, carried into the frame by T.
    A whole-pixel quarter turn copies texel for texel (the map keeps its own hand-drawn keyline);
    anything else fills the outer keyline, samples a 4x Scale2x upscale, and returns
    (pixels, needs_outline=True) so the caller stamps a fresh 1px keyline round it."""
    if T.whole():
        out = {}
        for (x, y), k in part.items():
            X, Y = T.fwd(x + 0.5, y + 0.5)
            out[(int(math.floor(X)), int(math.floor(Y)))] = k
        return out, False
    # two Scale2x passes: the first returns local 2x coordinates from the map's bbox corner o1, the
    # second works on those (its own corner is 0, 0)
    big1, o1 = scale2x(fill_outline(part))
    big2, _ = scale2x(big1)
    xs = [q[0] for q in part]
    ys = [q[1] for q in part]
    corners = [T.fwd(a, b) for a in (min(xs), max(xs) + 1) for b in (min(ys), max(ys) + 1)]
    X0 = int(math.floor(min(p[0] for p in corners))) - 1
    X1 = int(math.ceil(max(p[0] for p in corners))) + 1
    Y0 = int(math.floor(min(p[1] for p in corners))) - 1
    Y1 = int(math.ceil(max(p[1] for p in corners))) + 1
    out = {}
    for Y in range(Y0, Y1 + 1):
        for X in range(X0, X1 + 1):
            u, v = T.inv(X + 0.5, Y + 0.5)
            i = int(math.floor((u - o1[0]) * 4))
            j = int(math.floor((v - o1[1]) * 4))
            k = big2.get((i, j))
            if k is not None:
                out[(X, Y)] = k
    return out, True


# ------------------------------------------------------------ the head's light
# A sphere fitted to his skull on the approved head map: dome top on row 24, chin on row 51,
# cheeks 32..63.  Only its NORMALS are used, to move tones -- never to replace them.
HEAD_SPHERE = (47.5, 37.5, 16.0, 14.0)
LIGHT3 = L.LIGHT


def _sphere_n(x, y, sph):
    cx, cy, rx, ry = sph
    u, v = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
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
    pts = [(_dot(_sphere_n(x, y, sph), LIGHT3), ramp.index(k))
           for (x, y), k in part.items() if k in ramp]
    if len(pts) < 8:
        return 4.0
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    return max(1.0, -sxy / sxx) if sxx else 4.0


NECK_SPHERE = (47.5, 51.0, 7.0, 5.0)
# The steps-per-unit-of-light, fitted ONCE on the approved maps themselves -- never on whatever face is
# relit first, or the result would depend on the order frames happen to be drawn in.
HEAD_STEPS = {
    (SKIN, HEAD_SPHERE): _fit_steps(HD.head(), HEAD_SPHERE, SKIN),
    (BEARD, HEAD_SPHERE): _fit_steps(HD.head(), HEAD_SPHERE, BEARD),
    (SKIN, NECK_SPHERE): _fit_steps(L.amap(FC.NECK, 41, 49), NECK_SPHERE, SKIN),
    (BEARD, NECK_SPHERE): 1.0,
}


def relight(part, turn_deg, sph=HEAD_SPHERE):
    """Move every skin and beard pixel of a head map (his own space, before it is turned) along its
    ramp by the change in light the turn makes on the fitted sphere.  turn_deg is the head's total
    turn on screen.  0 changes nothing."""
    if abs(turn_deg) < 1e-9:
        return dict(part)
    t = math.radians(turn_deg)
    co, si = math.cos(t), math.sin(t)
    # the light as the turned head sees it: the screen light turned back by -turn
    lx, ly, lz = LIGHT3
    lb = (lx * co + ly * si, -lx * si + ly * co, lz)
    out = dict(part)
    for ramp in (SKIN, BEARD):
        k_per = HEAD_STEPS[(ramp, sph)]
        for (x, y), k in part.items():
            if k not in ramp:
                continue
            n = _sphere_n(x, y, sph)
            d = _dot(n, lb) - _dot(n, LIGHT3)
            i = ramp.index(k) - int(round(d * k_per))
            out[(x, y)] = ramp[max(0, min(len(ramp) - 1, i))]
    return out
