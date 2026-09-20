"""Eric v2 articulated rig for the Broken / Juggle / Winded sheets (256x192 frames, feet at (128,191)).

The approved v2 body (designer A's rig2 / scaled.py / parts.py) is built from part SHAPES (polygons,
ellipses) plus a volume model per part, a fixed light, 5-6 tone ramps and a 1 px black outline.
This module re-renders those same shapes under a per-group rigid transform (rotate about a pivot,
move the pivot) straight into frame space. A rotated part is therefore drawn fresh at its new angle:
its outline is re-traced at 1 px and its shading re-computed from the rotated volume model under the
unchanged top-left light. Nothing is pixel-rotated.

At angle 0 every part reproduces the approved layer pixel for pixel (see selftest()).

    tf = Tf(pivot96, at, ang)   # 96-space pivot, frame-space destination, degrees clockwise
    lay = Layer(); torso(lay, tf)                     # render one part group into a layer
    fr = Layer(); fr.over(lay)                        # composite layers in z order
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROP = os.path.join(ROOT, 'prop')
if PROP not in sys.path:
    sys.path.insert(0, PROP)

import rig2 as R          # noqa: E402  (sets up the shared toolkit path, sweat blues)
import scaled as SC       # noqa: E402
import lib                # noqa: E402
import parts              # noqa: E402
import headmap            # noqa: E402
import headrender         # noqa: E402
import head_s             # noqa: E402
from headstrokes import STROKES   # noqa: E402
from lib import PALC, BLACK, _DARKER, _LIGHTER, hexc, RAMPS, TH_METAL, TH_SOFT, TH_CLOTH  # noqa: E402

FW, FH = 256, 192
S = 0.8                      # body scale (scaled.py)
HS = 0.84                    # head scale (scaled.py)
T0 = (0, 0, 0, 0)
NECK96 = (48.0, 40.0)        # head pivot in 96-space; lands on NECK_F in the idle
NECK_F = (128.0, 147.2)

for _k, _v in {'Z': 'fff7d6', 'V': 'ff9fb0', 'U': 'd84a64'}.items():   # hot white, tongue pink, tongue red
    lib.PAL[_k] = _v
    PALC[_k] = hexc(_v)

_ORIG_NORMALS = SC._orig_normals


def normals_ext(mask, model):
    """lib.normals plus 'rsphere': the lib sphere model rotated by `ang` degrees (clockwise)."""
    if model[0] != 'rsphere':
        return _ORIG_NORMALS(mask, model)
    _, cx, cy, rx, ry, flat, ang = model
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    W, H = lib.W, lib.H
    out = [[None] * W for _ in range(H)]
    for y in range(H):
        row = mask[y]
        for x in range(W):
            if not row[x]:
                continue
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = (dx * ca + dy * sa) / rx
            v = (-dx * sa + dy * ca) / ry
            d = u * u + v * v
            if d > 0.97:
                s = math.sqrt(0.97 / d)
                u, v, d = u * s, v * s, 0.97
            nz = math.sqrt(1 - d) + flat
            out[y][x] = (u * ca - v * sa, u * sa + v * ca, nz)
    return out


lib.normals = normals_ext


def wf():
    lib.W, lib.H = FW, FH


# ------------------------------------------------------------------ layers
class Layer(R.Frame):
    """256x192 grid of rgba-or-None (rig2.Frame) with compositing helpers."""

    def over(self, other, dx=0, dy=0):
        src = other.px if hasattr(other, 'px') else other
        for y, row in enumerate(src):
            yy = y + dy
            if not 0 <= yy < FH:
                continue
            for x, p in enumerate(row):
                if p is None or (len(p) == 4 and p[3] == 0):
                    continue
                xx = x + dx
                if 0 <= xx < FW:
                    self.px[yy][xx] = p

    def cv(self):
        wf()
        c = lib.Canvas()
        c.px = self.px
        return c

    def mask(self):
        return [[p is not None for p in row] for row in self.px]

    def copy(self):
        c = Layer()
        c.px = [row[:] for row in self.px]
        return c


# ------------------------------------------------------------------ transforms
class Tf:
    """96-space point -> frame: scale s about pivot96, rotate `ang` degrees clockwise, pivot lands on `at`.
    mirror=True reflects the source about the body centre line (x -> 96 - x) first."""

    def __init__(self, pivot96=(48.0, 96.0), at=(128.0, 192.0), ang=0.0, s=S):
        self.p = pivot96
        self.at = at
        self.a = float(ang)
        self.s = s
        r = math.radians(self.a)
        self.c, self.sn = math.cos(r), math.sin(r)

    def pt(self, x, y):
        dx, dy = (x - self.p[0]) * self.s, (y - self.p[1]) * self.s
        return (self.at[0] + dx * self.c - dy * self.sn, self.at[1] + dx * self.sn + dy * self.c)

    def inv(self, X, Y):
        dx, dy = X - self.at[0], Y - self.at[1]
        return (self.p[0] + (dx * self.c + dy * self.sn) / self.s, self.p[1] + (-dx * self.sn + dy * self.c) / self.s)

    def rot(self, vx, vy):
        return (vx * self.c - vy * self.sn, vx * self.sn + vy * self.c)

    def zero(self):
        return abs(self.a) < 1e-9

    def shift(self):
        """integer frame shift when this is the idle placement moved by whole pixels (angle 0, s 0.8)"""
        if not self.zero() or abs(self.s - S) > 1e-9:
            return None
        X, Y = self.pt(48.0, 96.0)
        dx, dy = X - 128.0, Y - 192.0
        if abs(dx - round(dx)) < 1e-9 and abs(dy - round(dy)) < 1e-9:
            return int(round(dx)), int(round(dy))
        return None


def idle_tf(dx=0, dy=0):
    return Tf((48.0, 96.0), (128.0 + dx, 192.0 + dy), 0.0)


def about(tf, pivot96, ang, move=(0.0, 0.0)):
    """tf rotated by `ang` more degrees about a 96-space point, then moved by `move` (frame px)."""
    X, Y = tf.pt(*pivot96)
    return Tf(pivot96, (X + move[0], Y + move[1]), tf.a + ang, tf.s)


def P(tf, pts):
    wf()
    return lib.poly([tf.pt(x, y) for x, y in pts])


def E(tf, cx, cy, rx, ry, ang=0.0):
    wf()
    X, Y = tf.pt(cx, cy)
    return lib.ell(X, Y, rx * tf.s, ry * tf.s, ang + tf.a)


def SPH(tf, cx, cy, rx, ry, flat=0.0):
    X, Y = tf.pt(cx, cy)
    return ('rsphere', X, Y, rx * tf.s, ry * tf.s, flat, tf.a)


def CYL(tf, p0, p1, r):
    return ('cyl', tf.pt(*p0), tf.pt(*p1), r * tf.s)


def mir(pts):
    return [(96 - x, y) for x, y in pts]


# ------------------------------------------------------------------ raster helpers (frame space)
def empty():
    return [[False] * FW for _ in range(FH)]


def interior(m):
    return lib.sub(m, parts_edge(m))


def parts_edge(m):
    """parts.edge at frame size (parts.py bound W/H = 96 at import, so it cannot be used here)"""
    e = empty()
    for y in range(FH):
        row = m[y]
        for x in range(FW):
            if row[x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < FW and 0 <= yy < FH) or not m[yy][xx]:
                        e[y][x] = True
                        break
    return e


def arc_line(cx, cy, rx, ry, x0, x1):
    """parts.arc_line at frame size: lower half-ellipse arc x0..x1 as an 8-connected 1 px line"""
    m = empty()
    prev = None
    for x in range(x0, x1 + 1):
        t = (x + 0.5 - cx) / rx
        if abs(t) >= 1:
            continue
        y = int(math.floor(cy + ry * math.sqrt(1 - t * t)))
        if prev is not None and abs(y - prev) > 1:
            step = 1 if y > prev else -1
            for yy in range(prev + step, y, step):
                xx = x - 1 if (x + 0.5) < cx else x
                if 0 <= yy < FH:
                    m[yy][xx] = True
        if 0 <= y < FH:
            m[y][x] = True
        prev = y
    return m


def bres(p0, p1):
    x0, y0 = int(math.floor(p0[0])), int(math.floor(p0[1]))
    x1, y1 = int(math.floor(p1[0])), int(math.floor(p1[1]))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def thin(pts):
    """drop L-corner pixels of a pixel path so it stays 8-connected and 1 px thick"""
    out = []
    seen = set()
    for p in pts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    changed = True
    while changed:
        changed = False
        for i in range(1, len(out) - 1):
            a, b, c = out[i - 1], out[i], out[i + 1]
            if abs(a[0] - c[0]) <= 1 and abs(a[1] - c[1]) <= 1:
                del out[i]
                changed = True
                break
    return out


def polyline(pts):
    path = []
    for a, b in zip(pts, pts[1:]):
        seg = bres(a, b)
        if path and seg and seg[0] == path[-1]:
            seg = seg[1:]
        path.extend(seg)
    return thin(path)


def mask_of(pix):
    m = empty()
    for x, y in pix:
        if 0 <= x < FW and 0 <= y < FH:
            m[y][x] = True
    return m


def near8(vx, vy):
    """nearest of the 8 neighbour steps to a direction"""
    a = math.atan2(vy, vx)
    k = int(round(a / (math.pi / 4))) % 8
    return [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)][k]


def stamp_grid(lay, grid, x0, y0, only_on=False):
    rows = grid.strip('\n').split('\n')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x, y = x0 + dx, y0 + dy
            if not (0 <= x < FW and 0 <= y < FH):
                continue
            if only_on and lay.px[y][x] is None:
                continue
            lay.px[y][x] = PALC[ch]


# ------------------------------------------------------------------ body parts (torso group)
_CAPE = [(48, 40), (30, 39), (17, 45), (11.5, 56), (8.5, 68), (6.5, 80), (5, 90),
         (7, 94.5), (10, 90.5), (13.5, 95.5), (18, 90), (22, 94), (26, 91), (30, 95.5), (34, 92),
         (48, 92),
         (62, 92.5), (66, 95.5), (70, 91), (74.5, 94.5), (79, 89.5), (83, 95), (86.5, 90.5), (90, 93.5), (91.5, 88),
         (89.5, 78), (87.5, 67), (84.5, 56), (79, 45), (66, 39)]
_CAPE_FOLDS = [((13, 62), (10, 86)), ((19, 70), (18, 89)), ((81, 64), (84, 86)), ((75, 72), (76, 88))]
CAPE_TH = [9.0, 0.95, 0.80, 0.55, 0.2]


def cape_idle(lay, tf):
    cv = lay.cv()
    m = P(tf, _CAPE)
    cv.part(m, 'cape', SPH(tf, 44, 56, 46, 46, 0.7), th=CAPE_TH, bias=0)
    for p0, p1 in _CAPE_FOLDS:
        if tf.zero():
            ln = lib.inter(mask_of(bres_round(tf.pt(*p0), tf.pt(*p1))), m)
        else:
            ln = lib.inter(mask_of(polyline([tf.pt(*p0), tf.pt(*p1)])), m)
        for y in range(FH):
            for x in range(FW):
                if ln[y][x] and cv.px[y][x] != BLACK:
                    cv.px[y][x] = PALC['S']
    return m


def bres_round(p0, p1):
    """parts.seg_line semantics: endpoints rounded, not floored"""
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    return bres((x0 + 0.5, y0 + 0.5), (x1 + 0.5, y1 + 0.5))


def cape_poly(lay, pts, folds=(), light=None, th=CAPE_TH, bias=0, inner_pts=None, flat=0.55):
    """free cape shape in frame space. light = (cx, cy, r) sphere centre for its volume. Each fold is a
    dark crease with a lit ridge beside it on the side facing the light."""
    cv = lay.cv()
    wf()
    m = lib.poly(pts)
    if light is None:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        light = ((min(xs) + max(xs)) / 2 - 3, (min(ys) + max(ys)) / 2, max(max(xs) - min(xs), max(ys) - min(ys)) * 0.55)
    cx, cy, r = light
    cv.part(m, 'cape', ('sphere', cx, cy, r, r, flat), th=th, bias=bias)
    inn = interior(m)
    crease = set()
    ridge = set()
    for f in folds:
        path = polyline(f)
        for i, (x, y) in enumerate(path):
            if not (0 <= x < FW and 0 <= y < FH) or not inn[y][x]:
                continue
            crease.add((x, y))
            j0, j1 = max(0, i - 2), min(len(path) - 1, i + 2)
            dx, dy = path[j1][0] - path[j0][0], path[j1][1] - path[j0][1]
            nx, ny = -dy, dx
            if nx * -0.6 + ny * -0.8 < 0:
                nx, ny = -nx, -ny
            s = near8(nx, ny)
            ridge.add((x + s[0], y + s[1]))
    for x, y in ridge - crease:
        if 0 <= x < FW and 0 <= y < FH and inn[y][x] and cv.px[y][x] != BLACK:
            cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
    for x, y in crease:
        if cv.px[y][x] != BLACK:
            cv.px[y][x] = PALC['S'] if cv.px[y][x] != PALC['S'] else PALC['T']
    if inner_pts:
        im = lib.inter(lib.poly(inner_pts), inn)
        for y in range(FH):
            for x in range(FW):
                if im[y][x] and cv.px[y][x] != BLACK:
                    cv.px[y][x] = PALC['T']
    return m


def flap(lay, tf):
    cv = lay.cv()
    m = P(tf, lib.sym_pts([(48, 76), (43, 76), (42.6, 87), (44.2, 91.5), (48, 89.5)]))
    cv.part(m, 'cape', CYL(tf, (47, 60), (47, 100), 6), th=TH_CLOTH, bias=0)
    return m


_TASSET = [(25.5, 71), (46.2, 77), (46.8, 84.2), (44.5, 86), (36, 86.4), (28, 85.4), (23.2, 83), (23.6, 77)]
_TSEAM = [(23.5, 79.2), (46.5, 81.8), (46.5, 82.8), (23.5, 80.2)]
_TBEV = [(23.5, 80.2), (46.5, 82.8), (46.5, 83.8), (23.5, 81.2)]


def tassets(lay, tf, sides=(0, 1), flare=0.0):
    """flare: degrees each tasset swings out about its top outer corner (kneeling / sitting spreads them)"""
    cv = lay.cv()
    masks = []
    for side in sides:
        f = (lambda pts: pts) if side == 0 else mir
        cx = 34 if side == 0 else 62
        t = tf
        if flare:
            piv = (25.5, 71) if side == 0 else (70.5, 71)
            t = about(tf, piv, -flare if side == 0 else flare)
        m = P(t, f(_TASSET))
        cv.part(m, 'plate', CYL(t, (cx, 60), (cx + (1.5 if side == 0 else -1.5), 100), 14), th=TH_METAL)
        inn = interior(m)
        seam = P(t, f(_TSEAM))
        cv.line_on(lib.inter(seam, inn), BLACK)
        bev = P(t, f(_TBEV))
        cv.recolor(lib.inter(bev, inn), 'plate', CYL(t, (cx, 60), (cx, 100), 14), th=TH_METAL, bias=-1)
        cv.outline(m)
        for x, y in [(27, 75), (43, 79), (42, 84)]:
            sx = x + 0.5 if side == 0 else 96 - (x + 0.5)
            X, Y = t.pt(sx, y + 0.5)
            X, Y = int(math.floor(X)), int(math.floor(Y))
            if 0 <= Y < FH and 0 <= X < FW and cv.px[Y][X] not in (None, BLACK):
                cv.set(X, Y, 'E')
                if cv.px[Y - 1][X - 1] not in (None, BLACK):
                    cv.set(X - 1, Y - 1, 'W')
        masks.append(m)
    return masks


def belt(lay, tf):
    cv = lay.cv()
    m = P(tf, lib.sym_pts([(48, 69), (36, 67.6), (26, 64.4), (22.4, 63.6), (22.6, 70.4), (27, 73.4), (35, 76.6),
                           (42, 78.2), (48, 78.6)]))
    cv.part(m, 'leath', SPH(tf, 44, 60, 30, 20, 0.2), th=TH_SOFT)
    return m


_TORSO = [(48, 33), (39, 34), (31, 37), (26, 42), (22.5, 49), (21, 56), (21.3, 61.5), (23.2, 65.8),
          (27.3, 69.2), (34, 71.4), (41, 72.4), (48, 72.7)]


def torso(lay, tf, widen=0.0, drop=0.0):
    cv = lay.cv()
    half = []
    for x, y in _TORSO:
        if (widen or drop) and y > 44:
            k = min(1.0, (y - 44) / 14.0)
            x = x - widen * k
            y = y + drop * k
        half.append((x, y))
    m = P(tf, lib.sym_pts(half))
    cv.part(m, 'plate', SPH(tf, 46.5, 53, 28.5 + widen, 25.5, 0.05), th=TH_METAL)
    inner = interior(m)
    # fauld seam: lower half of an ellipse, with a bevel highlight on the side away from the arc
    if tf.zero():
        X, Y = tf.pt(48, 37.6)
        x0 = int(math.floor(tf.pt(20, 0)[0]))
        x1 = int(math.ceil(tf.pt(76, 0)[0]))
        wf()
        ln = lib.inter(arc_line(X, Y, 40 * tf.s, 31.8 * tf.s, x0, x1), inner)
        down = (0, 1)
    else:
        pts = []
        for i in range(0, 181):
            t = math.pi * i / 180.0
            lx, ly = 48 + 40 * math.cos(t), 37.6 + 31.8 * math.sin(t)
            if 20 <= lx <= 77:
                pts.append(tf.pt(lx, ly))
        ln = lib.inter(mask_of(polyline(pts)), inner)
        down = near8(*tf.rot(0, 1))
    below = empty()
    for y in range(FH):
        for x in range(FW):
            if ln[y][x]:
                xx, yy = x + down[0], y + down[1]
                if 0 <= xx < FW and 0 <= yy < FH and inner[yy][xx] and not ln[yy][xx]:
                    below[yy][xx] = True
    for y in range(FH):
        for x in range(FW):
            if below[y][x] and cv.px[y][x] != BLACK:
                cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
    cv.line_on(ln, BLACK)
    cross = lib.union(P(tf, [(45, 54), (51, 54), (51, 69), (45, 69)]), P(tf, [(38, 57), (58, 57), (58, 63), (38, 63)]))
    cv.part(cross, 'red', SPH(tf, 46.5, 53, 28.5, 25.5, 0.05), th=[0.95, 0.72, 0.42, -9, -9])
    return m


BUCKLE = SC.BUCKLE
STRAP = SC.STRAP


def buckle(lay, tf):
    """brass buckle + the two tasset straps"""
    if tf.zero():
        bx, by = tf.pt(48, 74.5)
        stamp_grid(lay, BUCKLE, int(round(bx)) - 3, int(round(by)) - 1)
        for sx in (34.5, 61.5):
            x, y = tf.pt(sx, 73.5)
            stamp_grid(lay, STRAP, int(round(x)) - 2, int(round(y)))
        return
    cv = lay.cv()
    for sx in (34.5, 61.5):
        st = P(tf, [(sx - 1.6, 73.2), (sx + 1.6, 73.2), (sx + 1.6, 80.8), (sx - 1.6, 80.8)])
        cv.part(st, 'leath', CYL(tf, (sx, 60), (sx, 90), 2.2), th=TH_SOFT, bias=1)
        bk = P(tf, [(sx - 1.6, 75.4), (sx + 1.6, 75.4), (sx + 1.6, 77.6), (sx - 1.6, 77.6)])
        cv.recolor(lib.inter(bk, interior(st)), 'brass', SPH(tf, sx - 1, 75, 3, 3, 0.2), th=TH_SOFT)
    b = P(tf, [(44.6, 73.2), (51.4, 73.2), (51.4, 78.6), (44.6, 78.6)])
    cv.part(b, 'brass', SPH(tf, 46.5, 74.5, 5, 4, 0.2), th=[0.95, 0.75, 0.45, 0.1, -9])
    hole = P(tf, [(46.6, 75.2), (49.4, 75.2), (49.4, 76.6), (46.6, 76.6)])
    cv.paint(lib.inter(hole, interior(b)), PALC['n'])


def gorget(lay, tf):
    cv = lay.cv()
    m = P(tf, lib.sym_pts([(48, 30.5), (40, 31), (34.5, 33.5), (32.2, 37.5), (34.5, 41.5), (41, 43.8), (48, 44.3)]))
    cv.part(m, 'plate', SPH(tf, 46, 36, 16, 9, 0.2), th=TH_METAL, bias=1)
    return m


ROUNDEL = SC.ROUNDEL


def roundel(lay, cx, cy, ang):
    """disc + red cross emblem drawn fresh at `ang` (the approved stamp at 0)"""
    if abs(ang) < 1e-9:
        stamp_grid(lay, ROUNDEL, int(round(cx)) - 4, int(round(cy)) - 4)
        return
    cv = lay.cv()
    wf()
    d = lib.ell(cx, cy, 4.4, 4.4)
    cv.part(d, 'plate', ('sphere', cx - 1.0, cy - 1.2, 5.2, 5.2, 0.0), th=[0.97, 0.82, 0.5, 0.15, -9])
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    arms = [((cx - vx * 2.0, cy - vy * 2.0), (cx + vx * 2.0, cy + vy * 2.0)),
            ((cx - ux * 2.0, cy - uy * 2.0), (cx + ux * 2.0, cy + uy * 2.0))]
    pix = set()
    for p0, p1 in arms:
        for p in polyline([p0, p1]):
            if 0 <= p[0] < FW and 0 <= p[1] < FH:
                pix.add(p)
    if not pix:
        return
    for x, y in pix:
        if cv.px[y][x] not in (None, BLACK):
            cv.px[y][x] = PALC['X']
    # the cross's lower-right edge in shadow, like the stamp
    for x, y in pix:
        for q in ((x + 1, y), (x, y + 1)):
            if q not in pix and 0 <= q[0] < FW and 0 <= q[1] < FH:
                c = cv.px[q[1]][q[0]]
                if c not in (None, BLACK) and c != PALC['X'] and q[0] > cx - 0.5 and q[1] > cy - 0.5:
                    pass
    lo = max(pix, key=lambda p: p[0] + p[1])
    cv.px[lo[1]][lo[0]] = PALC['y']


def pauldron(lay, tf, side):
    """side 0 = viewer-left (his right), 1 = viewer-right"""
    cv = lay.cv()
    right = side == 1
    sx = (lambda x: 96 - x) if right else (lambda x: x)
    sg = -1 if right else 1
    l2 = E(tf, sx(19.3), 54, 11.3, 5.6, -18 * sg)
    cv.part(l2, 'plate', SPH(tf, sx(18.5), 52.5, 12, 6.5, 0.1), th=TH_METAL)
    l1 = E(tf, sx(20.8), 49.2, 13, 6.6, -15 * sg)
    cv.part(l1, 'plate', SPH(tf, sx(20), 47.5, 13.5, 7.5, 0.1), th=TH_METAL)
    dome = E(tf, sx(23.5), 41.3, 13.6, 10.6, -12 * sg)
    cv.part(dome, 'plate', SPH(tf, sx(22.5), 40.5, 13.5, 11, 0.0), th=TH_METAL)
    # rolled rim along the lower edge of the dome (groove + bright lip)
    cx0, cy0 = tf.pt(23.5 if not right else 96 - 23.5, 41.3)
    a = math.radians(-12 * sg + tf.a)
    ca, sa = math.cos(a), math.sin(a)
    for y in range(FH):
        for x in range(FW):
            if not dome[y][x] or cv.px[y][x] == BLACK:
                continue
            dx, dy = x + 0.5 - cx0, y + 0.5 - cy0
            uu = (dx * ca + dy * sa) / (13.6 * tf.s)
            vv = (-dx * sa + dy * ca) / (10.6 * tf.s)
            t = math.sqrt(uu * uu + vv * vv)
            if vv < 0.15:
                continue
            if 0.68 <= t < 0.79:
                cv.px[y][x] = _DARKER.get(cv.px[y][x], cv.px[y][x])
            elif 0.79 <= t < 0.92:
                cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
    rx, ry = tf.pt(23.5 if not right else 96 - 23.5, 41.0)
    roundel(lay, rx, ry, tf.a)
    for (x, y) in [(13, 49), (20, 51), (27, 52), (12, 54), (18, 57)]:
        px_ = x + 0.5 if not right else 96 - (x + 0.5)
        X, Y = tf.pt(px_, y + 0.5)
        X, Y = int(math.floor(X)), int(math.floor(Y))
        if 0 <= Y < FH and 0 <= X < FW and cv.px[Y][X] not in (None, BLACK):
            cv.set(X, Y, 'E')
            if cv.px[Y - 1][X - 1] not in (None, BLACK):
                cv.set(X - 1, Y - 1, 'W')
    return dome


LEG_L = SC.LEG_L


def legs_idle(lay, dx=0, dy=0):
    """the approved standing lower legs (stamp)"""
    x0, y0 = 23 + 80 + dx, 88 + 96 + dy
    stamp_grid(lay, '\n'.join(LEG_L), x0, y0)
    stamp_grid(lay, '\n'.join(SC.right_leg_rows(LEG_L)), 95 - (23 + len(LEG_L[0]) - 1) + 80 + dx, y0)


# ------------------------------------------------------------------ head (label map, drawn at any angle)
FEATURES = set('nkepuol')


def _source_labels():
    """the hand-authored 96-space head map with its face features folded back into the base regions
    (features are drawn per expression, fresh, after the head is placed)"""
    g = headmap.grid
    lab = {}
    for r, row in enumerate(g):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            if ch in 'nkepu':
                ch = 'f'
            elif ch in 'ol':
                ch = 'd'
            lab[(headmap.X0 + c, headmap.Y0 + r)] = ch
    return lab


_SRC = _source_labels()
_V2LAB = None


def v2_labels():
    """approved v2 idle head labels in FRAME space (head_s, face fix included)"""
    global _V2LAB
    if _V2LAB is None:
        _V2LAB = {(x + 80, y + 96): ch for (x, y), ch in head_s.labels().items()}
    return _V2LAB


class HeadTf:
    """head pivot at the neck: source 96-space (48,40) scaled HS, rotated ang, placed at `at`"""

    def __init__(self, at=NECK_F, ang=0.0, s=HS):
        self.at, self.a, self.s = at, float(ang), s
        r = math.radians(self.a)
        self.c, self.sn = math.cos(r), math.sin(r)

    def pt(self, x, y):
        dx, dy = (x - NECK96[0]) * self.s, (y - NECK96[1]) * self.s
        return (self.at[0] + dx * self.c - dy * self.sn, self.at[1] + dx * self.sn + dy * self.c)

    def inv(self, X, Y):
        dx, dy = X - self.at[0], Y - self.at[1]
        return (NECK96[0] + (dx * self.c + dy * self.sn) / self.s, NECK96[1] + (-dx * self.sn + dy * self.c) / self.s)

    def local(self, lx, ly):
        """head-local frame offset (idle frame px relative to NECK_F) -> frame point"""
        return (self.at[0] + lx * self.c - ly * self.sn, self.at[1] + lx * self.sn + ly * self.c)

    def zero(self):
        return abs(self.a) < 1e-9


def head_labels(ht):
    if ht.zero() and abs(ht.s - HS) < 1e-9:
        dx, dy = ht.at[0] - NECK_F[0], ht.at[1] - NECK_F[1]
        if abs(dx - round(dx)) < 1e-6 and abs(dy - round(dy)) < 1e-6:
            dx, dy = int(round(dx)), int(round(dy))
            base = v2_labels()
            lab = {}
            for (x, y), ch in base.items():
                if ch in 'nepu' or (ch == 'k' and y < 138):
                    ch = 'f'
                elif ch in 'ol' or ch == 'k':
                    ch = 'd'        # the idle mouth line sits between moustache and beard
                lab[(x + dx, y + dy)] = ch
            return lab
    xs = [ht.pt(x + a, y + b)[0] for (x, y) in _SRC for a, b in ((0, 0), (1, 1))]
    ys = [ht.pt(x + a, y + b)[1] for (x, y) in _SRC for a, b in ((0, 0), (1, 1))]
    lab = {}
    for Y in range(max(0, int(min(ys)) - 2), min(FH, int(max(ys)) + 3)):
        for X in range(max(0, int(min(xs)) - 2), min(FW, int(max(xs)) + 3)):
            sx, sy = ht.inv(X + 0.5, Y + 0.5)
            k = (int(math.floor(sx)), int(math.floor(sy)))
            if k in _SRC:
                lab[(X, Y)] = _SRC[k]
    return lab


def _clean_labels(lab, passes=2):
    """remove 1 px label specks left by resampling at odd angles (a pixel whose 4 neighbours mostly
    disagree with it takes the majority label; lone silhouette pixels are dropped)"""
    for _ in range(passes):
        chg = []
        for (x, y), a in lab.items():
            nb = [lab.get(q) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))]
            present = [b for b in nb if b is not None]
            if len(present) <= 1:
                chg.append(((x, y), None))
                continue
            same = sum(1 for b in present if b == a)
            if same == 0 and len(present) >= 3:
                chg.append(((x, y), max(set(present), key=present.count)))
        for k, v in chg:
            if v is None:
                lab.pop(k, None)
            else:
                lab[k] = v
    return lab


def render_head(lay, ht, expr=None, strokes=True):
    """draw the head at HeadTf ht with expression `expr` (see faces.py); returns the label dict"""
    lab = head_labels(ht)
    if not ht.zero():
        lab = _clean_labels(lab)
    regs = {}
    for (x, y), ch in lab.items():
        regs.setdefault(ch, set()).add((x, y))
    allm = set(lab)
    # outline around the silhouette
    for (x, y) in allm:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in allm and 0 <= q[0] < FW and 0 <= q[1] < FH:
                lay.px[q[1]][q[0]] = BLACK
    wf()
    for ch, pix in regs.items():
        m = mask_of(pix)
        if ch in headrender.MODELS:
            ramp, model, th = headrender.MODELS[ch]
            _, cx, cy, rx, ry = model[:5]
            flat = model[5] if len(model) > 5 else 0.0
            X, Y = ht.pt(cx, cy)
            mdl = ('rsphere', X, Y, rx * ht.s, ry * ht.s, flat, ht.a)
            idx = lib.shade_idx(m, mdl, th)
            rp = [hexc(c) for c in RAMPS[ramp]]
            for (x, y) in pix:
                lay.px[y][x] = rp[min(idx[y][x], len(rp) - 1)]
        else:
            for (x, y) in pix:
                lay.px[y][x] = PALC[headrender.FLAT[ch]]
    paint = []
    for (x, y), a in lab.items():
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            b = lab.get((x + dx, y + dy))
            if b is not None and b != a and headrender.LINE_ON.get((a, b)):
                paint.append((x, y, headrender.LINE_ON[(a, b)]))
                break
    for x, y, ch in paint:
        lay.px[y][x] = PALC[ch]
    if strokes:
        rows = STROKES.split('\n')
        done = set()
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                if ch == '.':
                    continue
                X, Y = ht.pt(headmap.X0 + c + 0.5, headmap.Y0 + r + 0.5)
                X, Y = int(math.floor(X)), int(math.floor(Y))
                if (X, Y) in done or (X, Y) not in lab:
                    continue
                done.add((X, Y))
                cur = lay.px[Y][X]
                if cur is None or cur == BLACK:
                    continue
                if ch == '-':
                    lay.px[Y][X] = _DARKER.get(cur, cur)
                elif ch == '+':
                    lay.px[Y][X] = _LIGHTER.get(cur, cur)
                else:
                    lay.px[Y][X] = PALC[ch]
    if expr is not None:
        expr(lay, ht, lab)
    return lab


# ------------------------------------------------------------------ limbs and hands
def limb(lay, a, b, width, ramp='plate'):
    wf()
    R.limb(lay, a, b, width, ramp=ramp)


def cop(lay, c, rx, ry):
    wf()
    R.cop(lay, c, rx, ry)


def fist(lay, x, y, horizontal=False, shadow=True):
    wf()
    R.fist(lay, x, y, horizontal=horizontal, shadow=shadow)


def _local(origin, ang):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)

    def T(lx, ly):
        return (origin[0] + lx * ca - ly * sa, origin[1] + lx * sa + ly * ca)
    return T


def gauntlet_open(lay, wrist, ang, spread=1.0, curl=0.0, mirror=False):
    """a limp open armoured hand (mitten plate, finger grooves, thumb), drawn fresh at `ang`
    (degrees clockwise; 0 = fingers pointing down). mirror puts the thumb on the other side."""
    cv = lay.cv()
    wf()
    T = _local(wrist, ang)
    sx = -1 if mirror else 1
    thumb = lib.ell(*T(-5.0 * sx, 4.2), 2.2, 3.4, ang - 28 * sx)
    cv.part(thumb, 'iron', ('sphere',) + T(-5.5 * sx, 3.0) + (3.5, 4.0, 0.2), th=TH_METAL)
    hand = lib.poly([T(-4.2, 0.0), T(4.4, 0.0), T(5.0, 4.5), T(4.6, 9.0 + curl), T(3.0, 11.0 + curl),
                     T(-2.6, 11.0 + curl), T(-4.2, 9.2 + curl), T(-4.8, 4.5)])
    cv.part(hand, 'iron', ('sphere',) + T(-1.2, 3.0) + (7.5, 9.0, 0.25), th=TH_METAL)
    inn = interior(hand)
    for fx in (-1.2, 1.6):
        g = mask_of(polyline([T(fx, 6.3), T(fx, 10.4 + curl)]))
        cv.line_on(lib.inter(g, inn), BLACK)
    kn = mask_of(polyline([T(-3.6, 5.0), T(4.0, 5.0)]))
    for y in range(FH):
        for x in range(FW):
            if kn[y][x] and inn[y][x] and cv.px[y][x] != BLACK:
                cv.px[y][x] = _DARKER.get(cv.px[y][x], cv.px[y][x])
    cuff = lib.poly([T(-5.0, -4.2), T(5.0, -4.2), T(4.6, 0.6), T(-4.6, 0.6)])
    cv.part(cuff, 'iron', ('cyl', T(-3.0, -2.0), T(3.0, -2.0), 6.0), th=TH_METAL, bias=-1)


def leg_front(lay, hip, knee, ankle, foot_ang=None, thigh_w=11.0, dark=0, thigh=True, foot_w=15.0, boot=None):
    """an armoured leg seen from the front at any angle: cuisse (thigh), knee cop, greave flaring toward
    the ankle, and a rounded toe-on sabaton with its lame line (the standing stamp's pieces as shapes)."""
    cv = lay.cv()
    wf()
    if thigh:
        L = math.hypot(knee[0] - hip[0], knee[1] - hip[1])
        nx, ny = -(knee[1] - hip[1]) / L * thigh_w / 2, (knee[0] - hip[0]) / L * thigh_w / 2
        m = lib.poly([(hip[0] + nx, hip[1] + ny), (knee[0] + nx, knee[1] + ny), (knee[0] - nx, knee[1] - ny),
                      (hip[0] - nx, hip[1] - ny)])
        cv.part(m, 'plate', ('cyl', hip, knee, thigh_w / 2 + 0.5), th=TH_METAL, bias=dark)
    ang = math.degrees(math.atan2(ankle[1] - knee[1], ankle[0] - knee[0])) - 90
    T = _local(knee, ang)
    Ls = math.hypot(ankle[0] - knee[0], ankle[1] - knee[1])
    shin = lib.poly([T(-4.8, 0), T(4.8, 0), T(6.2, Ls), T(-6.2, Ls)])
    cv.part(shin, 'plate', ('cyl', T(0, 0), T(0, Ls), 6.4), th=TH_METAL, bias=dark)
    if boot is not None:
        boot_profile(lay, ankle, boot[0], boot[1], dark=dark)
        kc = lib.ell(knee[0], knee[1], 5.8, 4.4, ang)
        cv.part(kc, 'plate', ('rsphere', knee[0] - 1.0, knee[1] - 1.2, 6.4, 5.2, 0.0, ang), th=TH_METAL, bias=dark)
        return
    fa = ang if foot_ang is None else foot_ang
    F = _local(ankle, fa)
    hw = foot_w / 2
    foot = lib.poly([F(-hw + 2.2, -1.0), F(hw - 2.2, -1.0), F(hw - 0.4, 0.6), F(hw, 3.6), F(hw - 1.4, 5.8),
                     F(-hw + 1.4, 5.8), F(-hw, 3.6), F(-hw + 0.4, 0.6)])
    cv.part(foot, 'plate', ('rsphere',) + F(-2.5, 0.2) + (hw * 1.25, 6.5, 0.1, fa), th=TH_METAL, bias=dark)
    finn = interior(foot)
    ln = mask_of(polyline([F(-hw + 0.8, 2.2), F(hw - 0.8, 2.2)]))
    cv.line_on(lib.inter(ln, finn), BLACK)
    kc = lib.ell(knee[0], knee[1], 5.8, 4.4, ang)
    cv.part(kc, 'plate', ('rsphere', knee[0] - 1.0, knee[1] - 1.2, 6.4, 5.2, 0.0, ang), th=TH_METAL, bias=dark)


def boot_profile(lay, ankle, toe_dir, sole_dir, reach=9.5, h=7.2, cuff=6.2, dark=0):
    """a pointed sabaton seen from the side. (a, b) = ankle + a*toe_dir + b*sole_dir: the cuff spans
    a = -cuff..cuff over the shin end, the toe box runs `reach` px past it, the sole sits at b = h."""
    cv = lay.cv()
    wf()
    tl = math.hypot(*toe_dir)
    tx, ty = toe_dir[0] / tl, toe_dir[1] / tl
    sl = math.hypot(*sole_dir)
    sx, sy = sole_dir[0] / sl, sole_dir[1] / sl

    def T(a, b):
        return (ankle[0] + a * tx + b * sx, ankle[1] + a * ty + b * sy)
    e = cuff + reach
    pts = [T(-cuff - 0.2, -2.2), T(cuff, -2.2), T(cuff + 1.4, 0.6), T(e - 3.2, 2.2), T(e - 0.2, 4.0), T(e, 5.8),
           T(e - 1.6, h), T(-cuff + 1.4, h), T(-cuff - 0.6, h - 1.6), T(-cuff - 0.6, 0.0)]
    m = lib.poly(pts)
    c = T(-1.0, 0.5)
    ang = math.degrees(math.atan2(ty, tx))
    cv.part(m, 'plate', ('rsphere', c[0] - 1.2, c[1] - 1.2, e * 0.75, h * 1.3, 0.1, ang), th=TH_METAL, bias=dark)
    inn = interior(m)
    for p0, p1 in ((T(cuff + 0.6, -1.4), T(cuff + 0.6, h - 0.8)), (T(-cuff, h - 2.2), T(e - 1.4, h - 2.2))):
        ln = mask_of(polyline([p0, p1]))
        cv.line_on(lib.inter(ln, inn), BLACK)
    return m


def spin_arcs(lay, c, arcs, ch='W', edge='A'):
    """thin motion arcs around a spinning body: arcs = [(radius, a0_deg, a1_deg, width)], drawn fading
    from the head of the arc (a1) back to its tail (a0)"""
    for r, a0, a1, w in arcs:
        n = max(8, int(abs(a1 - a0) / 180.0 * math.pi * r * 1.5))
        pts = [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        path = polyline(pts)
        L = len(path)
        for i, (x, y) in enumerate(path):
            if not (0 <= x < FW and 0 <= y < FH):
                continue
            t = i / max(1, L - 1)
            lay.px[y][x] = PALC[ch if t > 0.45 else edge]
            if w > 1 and t > 0.6:
                dx, dy = x - c[0], y - c[1]
                q = (x - (1 if dx > 0 else -1) * (abs(dx) >= abs(dy)), y - (1 if dy > 0 else -1) * (abs(dy) > abs(dx)))
                if 0 <= q[0] < FW and 0 <= q[1] < FH:
                    lay.px[q[1]][q[0]] = PALC[edge]


def cast_shadow(lay, top, dx=1, dy=2):
    """darken the pixels of `lay` just below/right of the opaque pixels of `top` (a contact shadow)"""
    pts = [(x, y) for y in range(FH) for x in range(FW) if top.px[y][x] is not None]
    s = set(pts)
    for x, y in {(x + dx, y + dy) for x, y in pts} - s:
        if 0 <= x < FW and 0 <= y < FH:
            c = lay.px[y][x]
            if c is not None and c != BLACK:
                lay.px[y][x] = _DARKER.get(c, c)


# ------------------------------------------------------------------ self test
def idle_layers(dx=0, dy=0):
    tf = idle_tf(dx, dy)
    out = {}
    for name, fn in (('cape', lambda L: cape_idle(L, tf)), ('legs', lambda L: legs_idle(L, dx, dy)),
                     ('flap', lambda L: flap(L, tf)), ('tassets', lambda L: tassets(L, tf)),
                     ('belt', lambda L: belt(L, tf)), ('torso', lambda L: torso(L, tf)),
                     ('buckle', lambda L: buckle(L, tf)), ('gorget', lambda L: gorget(L, tf)),
                     ('paulL', lambda L: pauldron(L, tf, 0)), ('paulR', lambda L: pauldron(L, tf, 1)),
                     ('head', lambda L: render_head(L, HeadTf((NECK_F[0] + dx, NECK_F[1] + dy)), expr=idle_face))):
        L = Layer()
        fn(L)
        out[name] = L
    return out


def idle_face(lay, ht, lab):
    """the approved v2 idle face features (head_s FACE_FIX), drawn in head-local pixels"""
    import faces
    faces.draw(lay, ht, faces.IDLE, lab)


def selftest(verbose=True):
    ref = R.layers()
    mine = idle_layers()
    bad = 0
    for name, L in mine.items():
        r96 = ref[name]
        want = Layer()
        want.put96(r96, 0, 0)
        d = [(x, y) for y in range(FH) for x in range(FW)
             if (want.px[y][x] or T0) != (L.px[y][x] or T0)
             and not ((want.px[y][x] is None or want.px[y][x] == T0) and L.px[y][x] is None)]
        if verbose:
            print('%-8s diff %d %s' % (name, len(d), d[:6]))
        bad += len(d)
    return bad


if __name__ == '__main__':
    selftest()
