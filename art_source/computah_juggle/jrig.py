"""Computah's juggle frames: the APPROVED rig, carried into a 192x144 frame.

Nothing here redraws him.  Every body part is drawn by the approved rig in
art_source/computah_redesign/computah_mm.py -- _helmet, _cannon, _arm, _leg,
_torso, _finish -- which is imported read-only and never written to.  What this
module adds is WHERE those parts land: every shape the rig builds is wrapped in an
affine transform (a turn about his middle, plus a mat-squash on the crash frames)
before the rig's own Canvas shades it.

WHY THE GEOMETRY TURNS AND NOT THE PICTURE
The contract's lighting trap: rotating a finished sprite rotates its shading with
it, so a tumbling body ends up lit from below while the cast is lit from the upper
left.  Computah's rig does not bake light into pixels -- pixlib's Canvas shades
every shape from that shape's own surface normal against ONE fixed light at the
upper left (pixlib.LIGHT).  So turning the SHAPES keeps the rig's own volumes (the
same helmet dome, the same capsule limbs, the same barrel profile) and turns only
their normals, and the fixed light does the rest.  Nothing is refitted to a rotated
bounding box, so the ramp cannot collapse; lint.py measures it per frame anyway.

At angle 0 with a whole-pixel offset the transform is exact: a pose drawn here is
the rig's own art, pixel for pixel (check_identity() proves it against build_hit).

THREE THINGS THE RIG STAMPS PIXEL BY PIXEL rather than shading from a shape -- the
antenna ball, the four LED cells and the face plate.  Those are carried through the
same transform by inverse sampling (every frame pixel asks which rig pixel is under
it), so a turned face plate can never come out with holes punched in it.
"""
import contextlib
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ART, 'computah_redesign'))
sys.path.insert(0, os.path.join(ART, 'greyson_computah'))
sys.path.insert(0, ART)

import computah_mm as M     # noqa: E402  the approved rig, read-only
import pixlib as P          # noqa: E402

M._set_frame(96)            # K = 1: every rig number means what it means on his sheets

# ---------------------------------------------------------------- frame ------
# 192x144 is 2x wide and 1.5x tall against his 96x96 sheets: the same expansion
# Mason (64 -> 128x96) and Eric (128 -> 256x192) took.  His farthest point from his
# middle is the antenna ball, 58 texels out, so a turn about the chest needs a
# 116-texel circle plus the flung limbs; 144 tall holds it with room for the
# sparks and the smoke.
W, H = 192, 144
FEET = (96, 143)             # the bottom-centre texel his feet stand on (ground frames)
OUTLINE = M.OUTLINE          # #0C111A, never pure black
CLEAR = (0, 0, 0, 0)

# His middle in his own frame: the chest, just above the capacitor.  The turn is
# made about this point, so the tumble spins in place instead of wobbling.
COM = (47.5, 62.0)


class Tf(object):
    """His own 96-space -> the juggle frame.

        p' = Squash . Turn(angle) . (p - pivot) + dest

    `angle` is in degrees, clockwise-positive on screen (y points down), the same
    convention as Mason's jlib.matrix.  A NEGATIVE angle tips him backwards, which
    is what an uppercut to a right-facing chin does.  `squash` is applied in FRAME
    space after the turn, about `dest`, so a body flattens against the mat whatever
    angle it lies at."""

    def __init__(self, angle=0.0, dest=(96.0, 72.0), pivot=COM, squash=(1.0, 1.0)):
        self.angle = float(angle)
        t = math.radians(self.angle)
        self.co, self.si = math.cos(t), math.sin(t)
        # Snap the exact quarter turns, so 90 degrees is an exact 90 and not a
        # 6e-17 skew that nudges a rounding the wrong way.
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
        dx = rx * self.co + ry * self.si
        dy = -rx * self.si + ry * self.co
        return (dx + self.pivot[0], dy + self.pivot[1])

    def turn(self, nx, ny):
        """A direction in his frame -> the same direction on screen.  Rotation only:
        the squash is a cartoon beat, not a new shape, so it does not bend normals."""
        return (nx * self.co - ny * self.si, nx * self.si + ny * self.co)

    def unturn(self, nx, ny):
        return (nx * self.co + ny * self.si, -nx * self.si + ny * self.co)

    def px(self, x, y):
        """A rig pixel INDEX -> the frame pixel its centre lands in."""
        X, Y = self.fwd(x + 0.5, y + 0.5)
        return (int(math.floor(X)), int(math.floor(Y)))

    def sub(self, pivot, turn):
        """A part hinged at `pivot` (a rig point) and turned `turn` degrees on its own
        -- a head tipped back on the neck, a leg swung at the hip -- inside this
        transform.  The part is drawn in its own rest orientation, so every crease,
        cuff and sole line the rig puts across it stays across it."""
        return Tf(self.angle + turn, dest=self.fwd(*pivot), pivot=pivot,
                  squash=self.sq)

    def aim(self, root, frame_deg, reach):
        """The rig point `reach` texels from `root` along a bearing measured ON
        SCREEN (0 right, 90 down).  A limp limb hangs the way gravity points, not the
        way his body happens to be lying, so limbs are aimed in the frame."""
        a = math.radians(frame_deg)
        ux, uy = self.unturn(math.cos(a), math.sin(a))
        return (root[0] + ux * reach, root[1] + uy * reach)


class Xf(P.Shape):
    """An approved rig shape, carried into the frame by a Tf.  Its sdf is the rig
    shape's own, asked at the point the frame pixel maps back to; its normal is the
    rig shape's own, turned.  The Canvas then lights that turned normal with the
    cast's one fixed light."""

    def __init__(self, inner, T):
        self.inner, self.T = inner, T
        self.round_r = inner.round_r * T.scale

    def bbox(self):
        x0, y0, x1, y1 = self.inner.bbox()
        pts = [self.T.fwd(a, b) for a in (x0, x1) for b in (y0, y1)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)

    def sdf(self, x, y):
        u, v = self.T.inv(x, y)
        return self.inner.sdf(u, v) * self.T.scale

    def normal(self, x, y):
        u, v = self.T.inv(x, y)
        nx, ny, nz = self.inner.normal(u, v)
        a, b = self.T.turn(nx, ny)
        return (a, b, nz)


NAMES = ('E', 'CAP', 'RR', 'PO', 'PX', 'SPAN')
_ORIG = {n: getattr(M, n) for n in NAMES}


class Shapes(object):
    """The rig's six shape constructors, bound to one transform.  Every shape the
    rig's part functions build goes through one of these six."""

    def __init__(self, T):
        self.T = T

    def E(self, cx, cy, rx, ry, round_r=None):
        return Xf(_ORIG['E'](cx, cy, rx, ry, round_r), self.T)

    def CAP(self, p0, p1, r0, r1=None, round_r=None):
        return Xf(_ORIG['CAP'](p0, p1, r0, r1, round_r), self.T)

    def RR(self, x0, y0, x1, y1, r=4.0, round_r=5.0):
        return Xf(_ORIG['RR'](x0, y0, x1, y1, r, round_r), self.T)

    def PO(self, pts, round_r=7.0):
        return Xf(_ORIG['PO'](pts, round_r), self.T)

    def PX(self, x, y):
        return self.T.px(*_ORIG['PX'](x, y))

    def SPAN(self, x0, x1, y):
        return [self.T.px(a, b) for (a, b) in _ORIG['SPAN'](x0, x1, y)]


@contextlib.contextmanager
def placed(T):
    """Inside this block the rig's own part functions draw into the juggle frame.

    The rig's part functions (_helmet, _torso, _sparks ...) build every shape
    through six module-level constructors -- E, CAP, RR, PO, PX, SPAN -- so swapping
    those six for transformed ones, for the length of one call, carries the part
    into the frame unchanged.  Whatever was bound before is always put back, even
    on an error, so blocks can nest."""
    s = Shapes(T)
    saved = {n: getattr(M, n) for n in NAMES}
    for n in NAMES:
        setattr(M, n, getattr(s, n))
    try:
        yield s
    finally:
        for n, f in saved.items():
            setattr(M, n, f)


# ------------------------------------------------- inverse-sampled stamps ----
def stamp(c, T, local, lock=False):
    """Carry {rig pixel index: value} into the frame.  A value is a '#rrggbb' raw
    colour or a (material, ramp level) pair, exactly as pixlib.Canvas.stamp takes
    them.  Every frame pixel asks which rig pixel is under its centre, so a turned
    panel cannot come out with holes in it; at angle 0 it is an exact copy."""
    if not local:
        return
    xs = [k[0] for k in local]
    ys = [k[1] for k in local]
    x0, x1, y0, y1 = min(xs), max(xs) + 1, min(ys), max(ys) + 1
    corners = [T.fwd(a, b) for a in (x0, x1) for b in (y0, y1)]
    X0 = max(0, int(math.floor(min(p[0] for p in corners))) - 1)
    X1 = min(c.w - 1, int(math.ceil(max(p[0] for p in corners))) + 1)
    Y0 = max(0, int(math.floor(min(p[1] for p in corners))) - 1)
    Y1 = min(c.h - 1, int(math.ceil(max(p[1] for p in corners))) + 1)
    for Y in range(Y0, Y1 + 1):
        for X in range(X0, X1 + 1):
            u, v = T.inv(X + 0.5, Y + 0.5)
            k = (int(math.floor(u)), int(math.floor(v)))
            val = local.get(k)
            if val is None:
                continue
            if isinstance(val, str):
                c.raw[Y][X] = P._hex(val)
                if lock or c.mat[Y][X] is None:
                    c.prio[Y][X] = 99
            else:
                c.mat[Y][X] = val[0]
                c.lvl[Y][X] = val[1]
                c.prio[Y][X] = 99
            if lock:
                c.locked[Y][X] = True


def antenna(c, T, pts, ball, cc, prio=1):
    """M._antenna, with the ball's centre carried through T.  The ball keeps its
    highlight on the UPPER LEFT of the screen whatever way he is turned: it is a
    lit sphere, and the light does not move."""
    S = Shapes(T)
    for i in range(len(pts) - 1):
        c.add(S.CAP(pts[i], pts[i + 1], 2.6 - i * 0.22, 2.3 - i * 0.22), "shell",
              prio=prio)
    bx, by, br = ball
    hi, mid = cc[1], cc[2]
    X, Y = T.px(int(round(bx)), int(round(by)))
    for dy in range(-int(br) - 1, int(br) + 2):
        for dx in range(-int(br) - 1, int(br) + 2):
            if dx * dx + dy * dy <= br * br:
                c.raw_px([(X + dx, Y + dy)], hi if (dx <= 0 and dy <= 0) else mid)


def capacitor(c, T, cx, cy, cc, cell_w=3, gap=3, bh=6.4, prio=20, lit=None,
              blaze=False):
    """M._capacitor with the LED cells carried through T.  `lit` may be a set of
    cell indices (0 = leftmost) to light out of order, which is how the tumble's
    cells flicker; by default the first cc[0] cells are lit, as on his sheets."""
    S = Shapes(T)
    n_lit, hi, mid, dk, glow, _eye = cc
    on_set = set(range(n_lit)) if lit is None else set(lit)
    step = cell_w + gap
    span = step * 4 - gap
    bez = S.RR(cx - span / 2.0 - 2.2, cy - bh, cx + span / 2.0 + 2.2, cy + bh,
               r=3.0, round_r=4.0)
    c.add(bez, "armour", prio=prio, bias=2)
    c.contour(bez, width=1.3, delta=3, mats=("shell",), below_prio=prio)
    half = max(2, int(round(bh - 2.4)))
    ix = int(round(cx - span / 2.0))
    cw = max(2, int(round(cell_w)))
    st = max(cw + 1, int(round(step)))
    cyp = int(round(cy))
    c.add(S.RR(cx - span / 2.0 - 1.4, cy - bh + 2.4, cx + span / 2.0 + 1.0,
               cy + bh - 2.4, r=1.5, round_r=2.0), "glass", prio=prio + 1)
    local = {}
    for i in range(4):
        on = i in on_set
        for x in range(ix + i * st, ix + i * st + cw):
            for y in range(cyp - half, cyp + half + 1):
                if on:
                    col = hi if y <= cyp - half + 1 else (mid if y <= cyp + 1 else dk)
                    if x == ix + i * st + cw - 1 and y > cyp - half + 1:
                        col = dk
                else:
                    col = "#46536A" if y <= cyp else "#333E52"
                local[(x, y)] = col
    lo, hy = cyp - half - 1, cyp + half + 1
    right = ix + 3 * st + cw
    for x in range(ix - 1, right + 1):
        local[(x, lo)] = glow
        local[(x, hy)] = glow
    for y in range(lo, hy + 1):
        local[(ix - 1, y)] = glow
        local[(right, y)] = glow
    if blaze:
        for x in range(ix - 2, right + 2):
            local[(x, lo - 1)] = M.BEAM_HI
            local[(x, hy + 1)] = M.BEAM_HI
    stamp(c, T, local)


def cannon(c, T, sh, muzzle, r=8.0, prio=16):
    """M._cannon, line for line, except for the TWO accents that are really light.

    The rig lays a lit spine along one side of the barrel and a dark belly along
    the other, choosing the side from the barrel's direction; and it nudges the
    bore's inner highlight toward the upper left.  On every pose he ships with, the
    barrel points right or down-right, and both land on the side facing the light.
    Turned through a tumble, the same rules would light the belly and shade the
    spine.  Here both are placed by the light ON SCREEN.  On his shipped poses the
    result is identical (check_identity() covers the hit frame's barrel)."""
    S = Shapes(T)
    ax, ay = muzzle[0] - sh[0], muzzle[1] - sh[1]
    L = math.hypot(ax, ay) or 1.0
    ax, ay = ax / L, ay / L
    px, py = -ay, ax
    # the rig lights the side at -p; keep that unless -p faces away from the light
    nx, ny = T.turn(-px, -py)
    sgn = 1.0 if nx * P.LIGHT[0] + ny * P.LIGHT[1] >= 0 else -1.0

    def at(t):
        return (sh[0] + ax * L * t, sh[1] + ay * L * t)

    gun = P.Union([S.CAP(at(t0), at(t1), r * k0, r * k1)
                   for (t0, k0), (t1, k1) in zip(M.PROFILE, M.PROFILE[1:])],
                  k=1.4 * M.K, round_r=7.0 * M.K)
    c.add(gun, "armour", prio=prio, bias=2)
    c.contour(gun, width=1.5, delta=3, mats=("shell", "armour"), below_prio=prio)

    for t, kk in ((0.20, 0.76), (0.76, 0.78)):
        bx, by = at(t)
        rr = r * kk + 1.6
        c.shade_px([S.PX(bx + px * u, by + py * u)
                    for u in [q * 0.4 - rr for q in range(int(rr * 5) + 1)]],
                   2, "armour")
    for q in range(40):
        t = 0.26 + q * 0.019
        bx, by = at(t)
        rr = r * 0.70
        c.shade_px([S.PX(bx - sgn * px * rr, by - sgn * py * rr)], -2, "armour")
        c.shade_px([S.PX(bx + sgn * px * rr, by + sgn * py * rr)], 2, "armour")

    face_ = (muzzle[0] + ax * 0.6, muzzle[1] + ay * 0.6)
    ox, oy = T.unturn(-0.7, -0.7)          # the rig's (-0.7, -0.7), on screen
    c.add(S.E(face_[0], face_[1], r * 0.68, r * 0.68), "dark", prio=prio + 2, flat=4)
    c.add(S.E(face_[0] - ax * 1.2 + ox, face_[1] - ay * 1.2 + oy,
              r * 0.38, r * 0.38), "dark", prio=prio + 3, flat=2)
    c.contour(S.E(face_[0], face_[1], r * 0.68, r * 0.68), width=1.3, delta=-2,
              mats=("armour",))
    return face_


# The face plate's own characters (M._face), plus the handful the juggle faces add.
# Every colour below is already on his shipped sheets: the white-hot eye and its
# fringe are the `hit` mood's, the greens are the beam's, the cyan and the pale
# yellow are his spark colours.
EXTRA_CHARS = {
    "W": "#FFFFFF",      # white-hot LED core (the `hit` mood's R)
    "Y": "#FFD9A0",      # its fringe (the `hit` mood's G)
    "g": "#4FE066",      # beam mid green: a torn scanline
    "h": "#A9FFB4",      # beam light green
    "c": "#8CD8FF",      # spark cyan
    "s": "#FFF6C8",      # spark pale yellow
}


def face_chars(cc, mood="calm"):
    """M._face's character table, verbatim, so a plate stamped here uses exactly
    the colours his sheets do."""
    eye = cc[5]
    chars = {
        "v": ("dark", 0), "V": ("glass", 1), "M": ("glass", 4), "t": "#D8E4F2",
        "G": M._mix(eye, "#101820", 0.45), "R": eye,
    }
    if mood == "angry":
        chars["G"] = M._mix(eye, "#FFD8A0", 0.30)
    if mood == "lock":
        chars["G"] = "#FFD9A0"
        chars["R"] = "#FFFFFF"
        chars["t"] = "#FFFFFF"
    if mood == "hit":
        chars["G"] = "#FFD9A0"
        chars["R"] = "#FFFFFF"
    if mood == "dim":
        chars["G"] = M._mix(eye, "#101820", 0.72)
        chars["R"] = M._mix(eye, "#101820", 0.45)
    if mood == "dead":
        chars["G"] = "#2A2430"
        chars["R"] = "#5E2A26"
        chars["t"] = "#7E8A99"
    if mood == "ember":
        chars["G"] = "#3A2226"
        chars["R"] = "#B8392C"
        chars["t"] = "#7E8A99"
    out = dict(EXTRA_CHARS)
    out.update(chars)
    return out


def scale2x(grid):
    """Scale2x / EPX on a character grid: each cell becomes 2x2, and a corner takes
    its neighbours' character where two of them agree across it.  Diagonal strokes
    come out as smooth diagonals instead of staircases, which is what lets a turned
    plate keep its chevrons and teeth (the first half of RotSprite)."""
    h, w = len(grid), len(grid[0])

    def at(x, y):
        return grid[min(max(y, 0), h - 1)][min(max(x, 0), w - 1)]

    out = [[None] * (2 * w) for _ in range(2 * h)]
    for y in range(h):
        for x in range(w):
            p = grid[y][x]
            a, b, cc, d = at(x, y - 1), at(x + 1, y), at(x - 1, y), at(x, y + 1)
            out[2 * y][2 * x] = cc if (cc == a and cc != d and a != b) else p
            out[2 * y][2 * x + 1] = a if (a == b and a != cc and b != d) else p
            out[2 * y + 1][2 * x] = d if (d == cc and d != b and cc != a) else p
            out[2 * y + 1][2 * x + 1] = b if (b == d and b != a and d != cc) else p
    return ["".join(r) for r in out]


def _quarter(T):
    """True when T turns by a whole number of quarter turns and does not squash:
    then a plate maps texel for texel and needs no smoothing."""
    return (T.sq == (1.0, 1.0) and abs(T.co) in (0.0, 1.0)
            and abs(T.si) in (0.0, 1.0))


def face(c, T, grid, ox, oy, chars):
    """M._face's stamp, carried through T.  Locked, like the rig's, so no later
    shading pass can touch the plate.

    At a quarter turn it is an exact copy.  At any other angle the plate is first
    upscaled 4x with scale2x and then sampled, so the LED chevrons, rings and teeth
    survive the turn as shapes rather than breaking into scattered texels."""
    ox, oy = int(round(ox)), int(round(oy))
    if _quarter(T):
        local = {}
        for j, row in enumerate(grid):
            for i, ch in enumerate(row):
                if ch in ' .':
                    continue
                v = chars.get(ch)
                if v is not None:
                    local[(ox + i, oy + j)] = v
        stamp(c, T, local, lock=True)
        return
    big = scale2x(scale2x(grid))
    h, w = len(grid), len(grid[0])
    corners = [T.fwd(ox + a, oy + b) for a in (0, w) for b in (0, h)]
    X0 = max(0, int(math.floor(min(p[0] for p in corners))) - 1)
    X1 = min(c.w - 1, int(math.ceil(max(p[0] for p in corners))) + 1)
    Y0 = max(0, int(math.floor(min(p[1] for p in corners))) - 1)
    Y1 = min(c.h - 1, int(math.ceil(max(p[1] for p in corners))) + 1)
    for Y in range(Y0, Y1 + 1):
        for X in range(X0, X1 + 1):
            u, v = T.inv(X + 0.5, Y + 0.5)
            i, j = int(math.floor((u - ox) * 4)), int(math.floor((v - oy) * 4))
            if not (0 <= i < 4 * w and 0 <= j < 4 * h):
                continue
            val = chars.get(big[j][i])
            if val is None:
                continue
            if isinstance(val, str):
                c.raw[Y][X] = P._hex(val)
            else:
                c.mat[Y][X] = val[0]
                c.lvl[Y][X] = val[1]
            c.prio[Y][X] = 99
            c.locked[Y][X] = True


def canvas():
    return P.Canvas(W, H, M.PAL, OUTLINE)


def to_grid(c):
    """The Canvas's finished pixels (outline included) as rows of RGBA tuples."""
    g = [[CLEAR] * W for _ in range(H)]
    for (x, y), col in c.pixels().items():
        g[y][x] = tuple(col)
    return g


# ------------------------------------------------------------- the proof -----
def check_identity():
    """build_hit frame 0, drawn through the juggle machinery at angle 0 and a
    whole-pixel offset, must be the rig's own frame pixel for pixel."""
    from PIL import Image
    sys.path.insert(0, ART)
    from imgdiff import pixel_diff
    import poses
    want = M.build_hit(0).to_image()
    got = poses.replay_build_hit0()
    crop = got.crop((48, 48, 48 + 96, 48 + 96))
    outside = Image.new('RGBA', got.size, (0, 0, 0, 0))
    outside.paste(crop, (48, 48))
    stray = pixel_diff(outside, got)
    return pixel_diff(want, crop), stray
