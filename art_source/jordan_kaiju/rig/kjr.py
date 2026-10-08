"""The kaiju rig, posable (wave 1): the approved v2 kaiju (kj_kaiju2 + kj_frames2) rebuilt on a bone
hierarchy so every sheet is drawn from the approved design, not redrawn by hand.

  * DESIGN coordinates are the approval's (soles on 171, feet centred on x 98). Every part, plate root,
    line and mark belongs to a BONE; a POSE gives each bone a rotation about its pivot (degrees,
    clockwise, in its parent's space) and a shift (design units). At the rest pose every transform is
    the identity, so the rest frame is the approved kaiju pixel for pixel (checked by kjr_check).
  * Shading is the approval's: analytic normals turned with their bone, the light fixed (upper left).
  * Surface texture (bumps, scales) is laid out on the REST frame's grid, exactly as the approval did,
    then carried by the bones, so it rides on the skin instead of crawling across it.
  * The face at rest (unturned, unscaled) is the approval's pixel maps; turned or scaled, the same maps
    are resampled (nearest) about their anchors and re-keylined.
  * `sc` (design -> frame scale) is 1.45 for the fight; the grow / shrink frames re-render smaller.

Nothing here writes a file.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
from kj_shade import Cap, Ell  # noqa: E402

BASE_SC = 1.45
DX0, DY0 = 98.0, 171.0           # design anchor: the feet centre on the soles' keyline
FW, FH = 224, 232                # the body frame (texels): fits rear, leap, stumble and kneel
FEET = (98, 206)                 # where the design anchor (feet centre, soles row) lands: the pivot


#BONES: name -> (parent, pivot in design coordinates)

BONES = {
    'root': (None, (98.0, 171.0)),
    'pelvis': ('root', (100.0, 132.0)),
    'chest': ('pelvis', (102.0, 116.0)),
    'head': ('chest', (121.0, 80.0)),
    'jaw': ('head', (131.0, 88.0)),
    'n_upper': ('chest', (86.0, 96.0)),
    'n_fore': ('n_upper', (92.0, 112.0)),
    'f_upper': ('chest', (128.0, 99.0)),
    'f_fore': ('f_upper', (139.0, 106.0)),
    'n_thigh': ('pelvis', (80.0, 126.0)),
    'n_shin': ('n_thigh', (75.0, 150.0)),
    'n_foot': ('n_shin', (71.0, 162.0)),
    'f_thigh': ('pelvis', (121.0, 126.0)),
    'f_shin': ('f_thigh', (123.0, 148.0)),
    'f_foot': ('f_shin', (125.0, 162.0)),
    't1': ('pelvis', (64.0, 140.0)),
    't2': ('t1', (57.0, 153.0)),
    't3': ('t2', (55.0, 163.0)),
    't4': ('t3', (62.0, 174.0)),
    't5': ('t4', (80.0, 178.6)),
    't6': ('t5', (94.0, 177.2)),
}
ORDER = list(BONES)              # parents before children

SOLE_N = (70.0, 171.0)           # the soles' centres (design), on their foot bones
SOLE_F = (126.0, 171.0)
SEAT = (126.0, 65.5)             # Jordan's seat: the top-back of the skull at the neck base (head bone)
MOUTH_PT = (168.5, 85.6)         # the beam's origin, closed mouth (head bone)
CROWN_PT = (141.0, 59.0)         # the top of the brow


def _mul(a, b):
    """Affine 2x3 product a . b."""
    return (a[0] * b[0] + a[1] * b[3], a[0] * b[1] + a[1] * b[4], a[0] * b[2] + a[1] * b[5] + a[2],
            a[3] * b[0] + a[4] * b[3], a[3] * b[1] + a[4] * b[4], a[3] * b[2] + a[4] * b[5] + a[5])


IDENT = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0)


def _local(pivot, deg, dx, dy):
    if not deg and not dx and not dy:
        return IDENT
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    px, py = pivot
    return (c, -s, px - c * px + s * py + dx, s, c, py - s * px - c * py + dy)


class Rig:
    """A posed kaiju: world transforms for every bone and the design -> frame mapping."""

    def __init__(self, pose=None, sc=BASE_SC, feet=FEET, sx=1.0):
        self.pose = pose or {}
        self.sc = sc
        self.sx = sx
        self.ox, self.oy = feet
        self.world = {}
        self.rot = {}
        for b in ORDER:
            parent, pivot = BONES[b]
            deg, dx, dy = self.pose.get(b, (0.0, 0.0, 0.0))
            loc = _local(pivot, deg, dx, dy)
            if parent is None:
                self.world[b] = loc
                self.rot[b] = deg
            else:
                self.world[b] = _mul(self.world[parent], loc) if loc is not IDENT else self.world[parent]
                self.rot[b] = self.rot[parent] + deg
        self.rest = not any(any(v) for v in self.pose.values()) and sc == BASE_SC and sx == 1.0

    # design (on bone b) -> design (world)
    def W(self, b, p):
        m = self.world[b]
        if m is IDENT:
            return p
        return (m[0] * p[0] + m[1] * p[1] + m[2], m[3] * p[0] + m[4] * p[1] + m[5])

    def T(self, b, p):
        x, y = self.W(b, p)
        if self.sx != 1.0:
            return (self.ox + self.sc * self.sx * (x - DX0), self.oy + self.sc * (y - DY0))
        return (self.ox + self.sc * (x - DX0), self.oy + self.sc * (y - DY0))

    def fx_(self, x):
        """A frame x laid out unflipped about the feet, flipped / squashed by sx."""
        return self.ox + (x - self.ox) * self.sx if self.sx != 1.0 else x

    def Ti(self, b, p):
        x, y = self.T(b, p)
        return (int(round(x)), int(round(y)))

    def R(self, r):
        return r * self.sc

    def E(self, b, cx, cy, rx, ry, z=0.0):
        p = self.T(b, (cx, cy))
        if self.sx != 1.0:
            a = abs(self.sx)
            return Ell(p[0], p[1], self.R(rx) * a, self.R(ry), z=self.R(z),
                       ang=self.rot[b] * (1 if self.sx > 0 else -1))
        return Ell(p[0], p[1], self.R(rx), self.R(ry), z=self.R(z), ang=self.rot[b])

    def C(self, b, p0, p1, r0, r1, z=0.0):
        if self.sx != 1.0:
            k = 0.5 + 0.5 * abs(self.sx)
            return Cap(self.T(b, p0), self.T(b, p1), self.R(r0) * k, self.R(r1) * k, z=self.R(z))
        return Cap(self.T(b, p0), self.T(b, p1), self.R(r0), self.R(r1), z=self.R(z))

    def TP(self, b, pts):
        return [self.T(b, p) for p in pts]

    def tline(self, b, pts):
        out = []
        ip = [self.Ti(b, p) for p in pts]
        for (x0, y0), (x1, y1) in zip(ip, ip[1:]):
            for q in K.line(x0, y0, x1, y1):
                if not out or out[-1] != q:
                    out.append(q)
        return out

    def inv(self, q):
        """Frame -> world design."""
        return ((q[0] - self.ox) / (self.sc * self.sx) + DX0, (q[1] - self.oy) / self.sc + DY0)

    def to_local(self, b, wp):
        """World design point -> the point on bone b that lands there."""
        m = self.world[b]
        if m is IDENT:
            return wp
        det = m[0] * m[4] - m[1] * m[3]
        x, y = wp[0] - m[2], wp[1] - m[5]
        return ((m[4] * x - m[1] * y) / det, (-m[3] * x + m[0] * y) / det)

    def turn(self, b, v):
        """A direction on bone b, turned into the world."""
        a = math.radians(self.rot[b])
        c, s = math.cos(a), math.sin(a)
        return ((v[0] * c - v[1] * s) * self.sx, v[0] * s + v[1] * c)

    def floor(self):
        return int(round(self.oy))


#CANVAS (the approval's, with the floor clip)

class KCanvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}
        self.owner = {}
        self.lod = False             # small sizes: only the silhouette, the plates and the belly band keep lines

    def inb(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, cast=2, floor=None, owner=None, keep_line=False):
        if self.lod and not keep_line:
            outline, cast = False, 0
        if floor is not None:
            part = {q: k for q, k in part.items() if q[1] < floor}
        body = set(part)
        ring = set()
        if outline:
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body:
                        ring.add(q)
        if cast:
            shadow = set()
            for (x, y) in body:
                for d in range(1, cast + 2):
                    for (sx, sy) in ((d, d), (d, d - 1), (d - 1, d)):
                        q = (x + sx, y + sy)
                        if q not in body and q not in ring:
                            shadow.add(q)
            for q in shadow:
                k = self.px.get(q)
                if k is None or k == 'k':
                    continue
                self.px[q] = S.DARKER.get(k, k)
        for q in ring:
            if self.inb(q) and (floor is None or q[1] <= floor):
                self.px[q] = 'k'
                self.owner[q] = None
        for q, k in part.items():
            if self.inb(q):
                self.px[q] = k
                self.owner[q] = owner


#PART SPECS (design coordinates, per bone): ('E', bone, cx, cy, rx, ry[, z]) / ('C', bone, p0, p1, r0, r1)

def prims(rig, spec):
    out = []
    for item in spec:
        if item[0] == 'E':
            _, b, cx, cy, rx, ry, *z = item
            out.append(rig.E(b, cx, cy, rx, ry, z[0] if z else 0.0))
        else:
            _, b, p0, p1, r0, r1 = item
            out.append(rig.C(b, p0, p1, r0, r1))
    return out


def spec_bone_at(rest_rig, spec, q):
    """The bone owning frame pixel q at rest: the spec item on top there (highest), else the first."""
    best, bone = None, spec[0][1]
    for item, p in zip(spec, prims(rest_rig, spec)):
        s = p.sample(q[0], q[1])
        if s is not None and (best is None or s[1] > best):
            best, bone = s[1], item[1]
    return bone


TAIL_BACK = [('C', 't1', (64, 140), (57, 153), 14.0, 12.5), ('C', 't2', (57, 153), (55, 163), 12.5, 10.5)]
TAIL_FRONT = [('C', 't3', (55, 163), (62, 174), 10.5, 8.2), ('C', 't4', (62, 174), (80, 178.6), 8.2, 6.0),
              ('C', 't5', (80, 178.6), (94, 177.2), 6.0, 4.0), ('C', 't6', (94, 177.2), (101, 172), 4.0, 2.3)]
FAR_LEG = [('E', 'f_thigh', 121, 139, 15, 16), ('C', 'f_shin', (123, 148), (125, 162), 10.5, 9.5)]
FAR_FOOT = [('E', 'f_foot', 126, 165.5, 15, 6.2)]
FAR_TOES = [[('E', 'f_foot', 139, 167.5, 5, 4.2)], [('E', 'f_foot', 145, 168.5, 3.8, 3.2)]]
BELLY = [('E', 'pelvis', 99, 128, 36, 29)]
CHEST = [('E', 'chest', 103, 102, 30, 24), ('C', 'chest', (106, 92), (120, 80), 15.5, 13.0)]
NEAR_LEG = [('E', 'n_thigh', 80, 138, 19, 18), ('C', 'n_shin', (75, 150), (71, 162), 12.0, 11.0)]
NEAR_FOOT = [('E', 'n_foot', 70, 165.5, 19, 6.4)]
NEAR_TOES = [[('E', 'n_foot', 87, 167.0, 5.5, 4.6)], [('E', 'n_foot', 94, 168.5, 4.2, 3.4)]]
N_UPPER = [('C', 'n_upper', (86, 96), (92, 112), 7.6, 6.6)]
N_FORE = [('C', 'n_fore', (92, 112), (109, 105), 7.0, 5.6)]
N_PALM = [('E', 'n_fore', 112.5, 105, 5.2, 4.6)]
N_FINGERS = [[('C', 'n_fore', (115, 101.5), (120.5, 102.5), 2.3, 1.9)],
             [('C', 'n_fore', (116, 105.5), (121.5, 107.5), 2.3, 1.9)],
             [('C', 'n_fore', (114.5, 109), (118, 112.5), 2.3, 1.9)]]
N_TIPS = [('n_fore', 124.5, 104.5, 1, 0.6), ('n_fore', 124.5, 110.5, 0.7, 1), ('n_fore', 119.5, 116.5, 0.2, 1)]
F_UPPER = [('C', 'f_upper', (128, 99), (139, 106), 6.0, 5.0)]
F_FORE = [('C', 'f_fore', (139, 106), (146, 102), 5.0, 4.2)]
F_FINGERS = [[('C', 'f_fore', (148, 99.5), (152, 99.5), 1.9, 1.6)],
             [('C', 'f_fore', (149, 103), (152.5, 104.5), 1.9, 1.6)]]
F_TIPS = [('f_fore', 155.5, 100.5, 1, 0.5), ('f_fore', 155, 107.5, 0.6, 1)]
NFOOT_TIPS = [('n_foot', 99, 170, 1, 0.2), ('n_foot', 92, 172, 1, 0.6)]
FFOOT_TIPS = [('f_foot', 149, 170, 1, 0.3), ('f_foot', 143, 171, 1, 0.5)]
COLLAR = [('E', 'head', 121.0, 81.0, 13.6, 12.6)]      # the head layer's neck swivel (covers the stump)


#DORSAL PLATES

RIDGE = [('t6', (101.5, 170.5)), ('t6', (95, 174.6)), ('t5', (81, 175.4)), ('t4', (67, 171.6)),
         ('t3', (58, 165)), ('t2', (53.5, 156)), ('t1', (56, 145)), ('pelvis', (61, 134)),
         ('pelvis', (64, 124)), ('chest', (66, 113)), ('chest', (70, 102)), ('chest', (77, 91)),
         ('chest', (87, 82)), ('chest', (98, 75)), ('chest', (107, 70)), ('chest', (114, 66))]
TAIL_FRONT_END = 4
PLATES = [
    (0.030, 3.2, 0), (0.085, 3.8, 0), (0.145, 4.4, 0),
    (0.215, 6.5, 1), (0.265, 8.0, 1), (0.315, 9.5, 1),
    (0.365, 11.0, 2), (0.415, 12.5, 2),
    (0.465, 14.5, 3), (0.515, 16.5, 3),
    (0.565, 19.0, 4), (0.620, 21.5, 4),
    (0.680, 23.5, 5), (0.740, 23.0, 5),
    (0.805, 20.0, 6), (0.865, 16.0, 6), (0.925, 12.0, 6), (0.975, 8.5, 6),
]
N_GROUPS = 7
PLATE_BIG = [(-0.50, 0.00), (-0.44, 0.20), (-0.66, 0.34), (-0.36, 0.40), (-0.48, 0.62), (-0.18, 0.60),
             (0.00, 1.00), (0.15, 0.62), (0.40, 0.66), (0.24, 0.44), (0.54, 0.34), (0.38, 0.18),
             (0.50, 0.00)]
PLATE_MID = [(-0.50, 0.00), (-0.46, 0.30), (-0.64, 0.46), (-0.22, 0.56), (0.00, 1.00), (0.20, 0.58),
             (0.52, 0.44), (0.36, 0.24), (0.50, 0.00)]
PLATE_SMALL = [(-0.50, 0.00), (-0.40, 0.48), (0.00, 1.00), (0.34, 0.50), (0.50, 0.00)]


def _rest_ridge_s():
    pts = [p for (_, p) in RIDGE]
    tot = 0.0
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        tot += math.hypot(b[0] - a[0], b[1] - a[1])
        acc.append(tot)
    return [a / tot for a in acc]


RIDGE_S = _rest_ridge_s()


def ridge_at(rig, s):
    """The point and unit tangent at rest arc fraction s, on the POSED ridge (each segment carried by
    its bones), in world design coordinates."""
    pts = [rig.W(b, p) for (b, p) in RIDGE]
    rest = [p for (_, p) in RIDGE]
    segs, tot = [], 0.0
    for a, b in zip(rest, rest[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append(L)
        tot += L
    d = s * tot
    for i, L in enumerate(segs):
        if d <= L or i == len(segs) - 1:
            t = min(1.0, d / L)
            a, b = pts[i], pts[i + 1]
            ln = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln)
        d -= L
    raise AssertionError


def outward(tg):
    a = (tg[1], -tg[0])
    b = (-tg[1], tg[0])
    return a if (a[1] + 0.4 * a[0]) < (b[1] + 0.4 * b[0]) else b


def plate_dir(tg, lean=0.38):
    n = outward(tg)
    dx, dy = n[0] - tg[0] * lean, n[1] - tg[1] * lean
    ln = math.hypot(dx, dy)
    return dx / ln, dy / ln


def plate_poly(base, direction, h, w):
    dx, dy = direction
    px, py = -dy, dx
    shape = PLATE_BIG if h >= 20 else (PLATE_MID if h >= 12 else PLATE_SMALL)
    return [(base[0] + px * a * w + dx * b * h, base[1] + py * a * w + dy * b * h) for (a, b) in shape]


def plate_part(pts, glow=0.0, dim=False, flash=False):
    shape = K.poly(pts)
    if not shape:
        return {}
    base = ((pts[0][0] + pts[-1][0]) / 2.0, (pts[0][1] + pts[-1][1]) / 2.0)
    tip = max(pts, key=lambda p: math.hypot(p[0] - base[0], p[1] - base[1]))
    ax, ay = tip[0] - base[0], tip[1] - base[1]
    L = math.hypot(ax, ay) or 1.0
    ux, uy = ax / L, ay / L
    halfw = max(1.0, max(abs((x - base[0]) * -uy + (y - base[1]) * ux) for (x, y) in shape))
    out = {}
    for (x, y) in shape:
        rx, ry = x - base[0], y - base[1]
        along = (rx * ux + ry * uy) / L
        across = (rx * -uy + ry * ux) / halfw
        a = abs(across)
        if flash:
            k = 'X' if a < 0.5 else ('K' if a < 0.8 else 'J')
        elif glow > 0 and along <= glow:
            if a < 0.2:
                k = 'X' if along < glow - 0.18 else 'K'
            elif a < 0.46:
                k = 'K'
            elif a < 0.74:
                k = 'J'
            else:
                k = 'I'
            if along < 0.1:
                k = 'J' if a < 0.4 else 'I'
        else:
            if a < 0.11 and along < 0.72:
                k = '5'
            elif across < 0:
                k = '7' if across < -0.62 else '6'
            else:
                k = '4' if across > 0.6 else '5'
            if along > 0.86:
                k = '7' if across < 0.25 else '6'
            if dim:
                k = {'7': '6', '6': '5', '5': '4', '4': '4'}[k]
            if glow > 0 and along <= glow + 0.14:
                k = 'I' if k in '45' else 'J'
        out[(x, y)] = k
    return out


def plates(rig, group_glow, row='main', flash=False):
    parts = []
    for (s, size, g) in PLATES:
        glow = group_glow.get(g, 0.0)
        if row == 'far':
            p, tg = ridge_at(rig, min(0.995, s + 0.022))
            d = plate_dir(tg, lean=0.2)
            n = outward(tg)
            bp = (p[0] + 1.2 - n[0] * 0.6, p[1] - 1.2 - n[1] * 0.6)
            h, w = size * 0.72 + 1.5, size * 0.66 + 1.0
        else:
            p, tg = ridge_at(rig, s)
            d = plate_dir(tg)
            bp = (p[0] - d[0] * 2.5, p[1] - d[1] * 2.5)
            h, w = size + 2.5, size * 0.74 + 1.5
        base = (rig.ox + rig.sc * (bp[0] - DX0), rig.oy + rig.sc * (bp[1] - DY0))
        pts = plate_poly(base, d, rig.R(h), rig.R(w))
        if rig.sx != 1.0:
            pts = [(rig.fx_(x), y) for (x, y) in pts]
        parts.append((plate_part(pts, glow, dim=(row == 'far'), flash=flash and glow > 0), g, s))
    return parts


#SURFACE DETAIL, laid out on the rest frame and carried by the bones

def _carry(rig, rest, spec, q0):
    """Where rest-frame pixel q0 (on the part `spec`) lands in the posed frame."""
    if rig.rest:
        return q0
    b = spec_bone_at(rest, spec, q0)
    wp = rest.inv(q0)                     # the rest pose: world == bone-local
    x, y = rig.T(b, wp)
    return (int(round(x)), int(round(y)))


# the approval laid its texture out on its own working canvas (feet at (102, 220)); the grid and its
# hash run in those coordinates so the rest frame reproduces it exactly
APPROVAL_FEET = (102, 220)


def _hoff(rest):
    return (int(round(rest.ox)) - APPROVAL_FEET[0], int(round(rest.oy)) - APPROVAL_FEET[1])


def rest_part_box(rest, spec, clip=None):
    pix = set(clip) if clip is not None else S.part_pixels(prims(rest, spec))
    xs = [x for (x, y) in pix]
    ys = [y for (x, y) in pix]
    return min(xs), min(ys), max(xs), max(ys)


def bumps(rig, rest, spec, part, seed=7, step=7, keys=('@', '+', '&'), clip=None):
    if rig.sc < 0.7 * BASE_SC:
        return
    ux, uy = _hoff(rest)
    x0, y0, x1, y1 = rest_part_box(rest, spec, clip)
    for gy in range(y0 - uy, y1 - uy + 1, step):
        for gx in range(x0 - ux, x1 - ux + 1, step):
            h = (gx * 73856093 ^ gy * 19349663 ^ seed * 83492791) & 0xFFFF
            x = gx + (h % 3) - 1 + ((gy // step) % 2) * (step // 2)
            y = gy + ((h >> 4) % 3) - 1
            x, y = _carry(rig, rest, spec, (x + ux, y + uy))
            q = (x, y)
            if part.get(q) not in keys:
                continue
            if not all((x + dx, y + dy) in part for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)):
                continue
            part[q] = S.LIGHTER[part[q]]
            if (h >> 8) % 2 and (x + 1, y) in part and part[(x + 1, y)] in keys:
                part[(x + 1, y)] = S.LIGHTER[part[(x + 1, y)]]
            r = (x + 1, y + 1)
            if part.get(r) in S.DARKER:
                part[r] = S.DARKER[part[r]]


def scales(rig, rest, spec, part, seed=1, dx=5, dy=4, keys=('@', '+', '&', '%'), margin=2, clip=None):
    if rig.sc < 0.7 * BASE_SC:
        return
    ux, uy = _hoff(rest)
    x0, y0, x1, y1 = rest_part_box(rest, spec, clip)
    for gy in range(y0 - uy, y1 - uy + 1, dy):
        off = (dx // 2) if (gy // dy) % 2 else 0
        for gx in range(x0 - ux + off, x1 - ux + 1, dx):
            h = (gx * 92821 ^ gy * 68917 ^ seed * 1237) & 0xFFF
            if h % 5 == 0:
                continue
            x, y = gx + (h % 2), gy + ((h >> 5) % 3) - 1
            x, y = _carry(rig, rest, spec, (x + ux, y + uy))
            n = 1 + (h >> 7) % 3
            pts = [(x + i, y) for i in range(n)]
            if any(part.get(q) not in keys for q in pts):
                continue
            if not all((x + ax, y + ay) in part for ax in range(-margin, margin + 2)
                       for ay in range(-margin, margin + 1)):
                continue
            for q in pts:
                part[q] = 'k' if part[q] in ('%', '&') else S.DARKER[part[q]]
            for q in ((x - 1, y - 1), (x, y - 1)):
                if part.get(q) in keys and (h >> 3) % 3:
                    part[q] = S.LIGHTER[part[q]]
                    break


BELLY_LINE = [('chest', (126, 86)), ('chest', (127, 98)), ('chest', (125, 111)), ('pelvis', (120, 124)),
              ('pelvis', (114, 138)), ('pelvis', (108, 151))]
BELLY_HALF = [5.0, 8.0, 10.0, 11.0, 10.0, 7.0]
BELLY_STEP = 9


def _closest_on(line_pts, p):
    best, acc = None, 0.0
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line_pts, line_pts[1:]))
    for i, (a, b) in enumerate(zip(line_pts, line_pts[1:])):
        vx, vy = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vy * vy
        L = math.sqrt(L2)
        t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
        cx, cy = a[0] + vx * t, a[1] + vy * t
        d = math.hypot(p[0] - cx, p[1] - cy)
        if best is None or d < best[0]:
            best = (d, (acc + t * L) / tot, i, t)
        acc += L
    return best


def belly(rig, part, info, seams=True):
    line_f = [rig.T(b, p) for (b, p) in BELLY_LINE]
    half = [rig.R(h) * (0.5 + 0.5 * abs(rig.sx)) for h in BELLY_HALF]
    step = max(3, int(round(BELLY_STEP * rig.sc / BASE_SC)))
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line_f, line_f[1:]))
    region = {}
    for q in list(part):
        d, s, i, t = _closest_on(line_f, q)
        hw = half[i] * (1 - t) + half[i + 1] * t
        if d <= hw:
            lam = info[q][0]
            idx = sum(1 for cut in (0.12, 0.42, 0.72) if lam + 0.06 >= cut)
            region[q] = (s * tot, d / hw)
            part[q] = S.BONE[idx]
    for q, (along, rel) in region.items():
        a = along + rel * rel * 2.4 * rig.sc / BASE_SC
        if seams and int(a) % step == 0 and rel < 0.92 and along < tot - 7 * rig.sc / BASE_SC:
            part[q] = 'k'
        elif int(a) % step == step - 1 and rel < 0.9 and part[q] in ('5', '6'):
            part[q] = S.LIGHTER[part[q]]
    edge = [q for q in region if any((q[0] + dx, q[1] + dy) in part and (q[0] + dx, q[1] + dy) not in region
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        part[q] = 'k'
    return region


def seam(rig, b, part, pts):
    if rig.sc < 0.5 * BASE_SC:
        return
    pix = rig.tline(b, pts)
    for q in pix:
        if q in part:
            part[q] = 'k'
    for (x, y) in pix:
        q = (x, y - 1)
        if q in part and part[q] != 'k' and part[q] in ('@', '+', '&', '%', '#', '='):
            part[q] = '='


def claws(rig, tips, size=3.0):
    out = {}
    for (b, tx, ty, dx, dy) in tips:
        tx, ty = rig.T(b, (tx, ty))
        dx, dy = rig.turn(b, (dx, dy))
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px, py = -uy, ux
        sz = rig.R(size)
        base = (tx - ux * sz, ty - uy * sz)
        hw = rig.R(1.3)
        pts = [(base[0] + px * hw, base[1] + py * hw), (tx, ty), (base[0] - px * hw, base[1] - py * hw)]
        shape = K.poly(pts)
        for q in shape:
            out[q] = '6'
        for q in shape:
            if (q[0] - 1, q[1]) not in shape or (q[0], q[1] - 1) not in shape:
                out[q] = '7'
            if (q[0] + 1, q[1]) not in shape and (q[0], q[1] + 1) not in shape:
                out[q] = '5'
    return out


GLOSS = [
    ('n_thigh', [(66, 128), (68, 125), (71, 123), (75, 122)]),
    ('chest', [(84, 87), (87, 85), (91, 84)]),
    ('chest', [(80, 108), (82, 106)]),
    ('head', [(124, 63), (129, 62)]),
    ('head', [(156, 69), (160, 69.5)]),
    ('t1', [(60, 146), (58, 150)]),
    ('n_upper', [(88, 98), (89.5, 96.5)]),
    ('pelvis', [(117, 132), (119, 129)]),
]
KNEE_CREASES = [('n_shin', [(61, 150), (63, 153), (66, 155)]), ('f_shin', [(108, 149), (110, 151)])]
FOLDS = [
    ('chest', [(119, 89), (122, 91.5), (125, 92.5)]),
    ('chest', [(117, 93), (120.5, 95.5), (124, 96.5)]),
    ('n_fore', [(94, 114.5), (96, 117)]),
    ('t4', [(70, 168.5), (72, 172), (71, 175.5)]),
    ('t5', [(82, 171.5), (83.5, 175), (82.5, 178)]),
    ('t5', [(91, 171), (92, 174)]),
]


# which part each detail line belongs to (it is only drawn where that part shows)
# (the approval drew the knee creases and neck folds over whatever lay there at rest; these sets keep
# exactly those, so the rest frame is unchanged, and stop them landing on anything else when posed)
GLOSS_OWNER = [{'near_leg'}, {'chest'}, {'chest'}, {'head'}, {'head'}, {'tail_back'}, {'n_upper'}, {'belly'}]
CREASE_OWNER = [{'near_leg', 'tail_back'}, {'far_leg', 'belly'}]
FOLD_OWNER = [{'chest', 'head'}, {'chest', 'head'}, {'n_fore'}, {'tail_front'}, {'tail_front'}, {'tail_front'}]


def _ok(owner, q, want):
    return owner is None or want is None or owner.get(q) in want


def gloss(rig, px, skip_bones=(), owner=None):
    if rig.sc < 0.5 * BASE_SC:
        return
    for (b, pts), want in zip(GLOSS, GLOSS_OWNER):
        if b in skip_bones:
            continue
        for (x, y) in rig.tline(b, pts):
            if px.get((x, y)) in ('@', '+', '=', '&') and _ok(owner, (x, y), want):
                px[(x, y)] = '~'
            q = (x, y + 1)
            if px.get(q) in ('@', '+', '&') and _ok(owner, q, want):
                px[q] = '='


def lines_k(rig, px, table, skip_bones=(), min_sc=0.5, any_key=False, owner=None, owners=None):
    if rig.sc < min_sc * BASE_SC:
        return
    for i, (b, pts) in enumerate(table):
        if b in skip_bones:
            continue
        want = owners[i] if owners else None
        for q in rig.tline(b, pts):
            if px.get(q) not in (None, 'k') and (any_key or px.get(q) in ('#', '%', '&', '@', '+', '=', '~')) \
                    and _ok(owner, q, want):
                px[q] = 'k'


STAR = ["...O...", "..OYO..", "OOOYOOO", ".OOOOG.", "..OGO..", ".OG.GO."]
STAR_AT = ('f_foot', (113.5, 162.5))


#SMALL PIXEL SPRITES, turned and scaled about an anchor

def sprite_place(rows, anchor_px, rig, b, anchor_design, keyline=True):
    """Lay a pixel map (rows of keys, '.' clear) whose (0, 0) cell sits at anchor_px at rest, onto the
    posed frame: at rest a straight copy; turned / scaled, each target pixel samples the map (nearest)
    through the inverse turn and scale about the map's anchor, the colours only, then the keyline is
    rebuilt round them. Returns {pixel: key}."""
    cells = {(c, r): ch for r, row in enumerate(rows) for c, ch in enumerate(row) if ch != '.'}
    if rig.rest:
        return {(anchor_px[0] + c, anchor_px[1] + r): ch for (c, r), ch in cells.items()}
    k = rig.sc / BASE_SC
    ang = math.radians(rig.rot[b])
    ca, sa = math.cos(ang), math.sin(ang)
    ax, ay = rig.T(b, anchor_design)
    col = {q: ch for q, ch in cells.items() if ch != 'k'}
    if not col:
        return {}
    cs = [c for (c, r) in cells]
    rs = [r for (c, r) in cells]
    span = (max(cs) - min(cs) + 2, max(rs) - min(rs) + 2)
    rad = int(math.ceil(max(span) * max(1.0, k) / min(1.0, abs(rig.sx)))) + 2
    out = {}
    for ty in range(int(ay) - rad, int(ay) + rad + 1):
        for tx in range(int(ax) - rad, int(ax) + rad + 1):
            # target pixel centre -> map coordinates
            vx, vy = tx + 0.5 - ax, ty + 0.5 - ay
            vx = vx / rig.sx
            ux = (vx * ca + vy * sa) / k
            uy = (-vx * sa + vy * ca) / k
            c, r = int(math.floor(ux)), int(math.floor(uy))
            ch = cells.get((c, r))
            if ch is not None:
                out[(tx, ty)] = ch
    if keyline:
        ring = set()
        for (x, y), ch in out.items():
            if ch == 'k':
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in out:
                    ring.add(q)
        for q in ring:
            out[q] = 'k'
    return out


#THE HEAD

SKULL = [(113, 70), (117, 64), (125, 61), (135, 60), (141, 59), (147, 59), (151, 61), (153, 64),
         (155, 66), (160, 67), (165, 69), (167, 71), (167.5, 77), (166, 81), (152, 82.5), (145, 83.5),
         (139, 84.5), (134, 86.5), (130, 90), (124, 92), (117, 91), (113, 86), (111.5, 78)]
JAW = [(131, 87.5), (139, 85.5), (148, 84.5), (157, 83.5), (163, 83.5), (164.5, 86), (162.5, 90),
       (155, 93.5), (144, 96), (133, 96), (126, 93)]
JAW_TOP = [(131, 87.5), (139, 85.5), (148, 84.5), (157, 83.5), (163, 83.5)]
HEAD_SPEC = [('E', 'head', 128, 74, 16, 13), ('E', 'head', 145, 64.5, 8.5, 4.2, 3.0),
             ('C', 'head', (141, 74), (161, 75), 9.0, 6.6), ('E', 'head', 126, 83, 9.5, 7.0, 1.0)]
HEAD_FB = ('E', 'head', 138, 76, 32, 22, -30)
JAW_SPEC = [('C', 'jaw', (130, 91), (159, 88.5), 6.0, 4.5)]
JAW_FB = ('E', 'jaw', 146, 90, 24, 10, -20)
BROW = [(138.5, 64.5), (145.5, 66.0), (152.5, 68.3)]
EYE_MAP = ["kGOYYOkOOGkk...", ".kGOOOkOOOOGk..", "..kkGOkOOOGGkk.", "....kkkkkkkk..."]
EYE_AT = (142.2, 66.6)
# other eyes, laid at the same anchor (+ offset): the pained squint, the knocked-out swirls
_SW = [".kkkkkkk.", "kWWWWWWWk", "kWkkkkkWk", "kWkWWWkWk", "kWkWkkkWk", "kWkWWWWWk", ".kkkkkkk."]
EYE_STYLES = {
    'squint': (["kk...........", ".kkkk........", "...kkkkkkkk..", "............."], (1, 0)),
    'swirl': (_SW, (3, -2)),
    'swirl_b': ([r[::-1] for r in _SW[::-1]], (3, -2)),
}            # design point whose rest pixel (+1, 0) is the map's (0, 0)
NOSTRIL = [(160.4, 69.8), (162.6, 69.8), (162.8, 71.4), (161.0, 71.2)]
MOUTH = [(166.5, 81.6), (152, 82.2), (145, 83.2), (139, 84.2), (135, 85.2), (132.6, 86.4)]
EAR = [(118.4, 76.6), (120.6, 76.6), (120.4, 78.6), (118.6, 78.4)]
UPPER_FANGS = [(162, 82.6, 4, 3), (157, 82.8, 3, 2), (151, 83.4, 4, 3), (145, 84.0, 3, 2), (140, 84.8, 3, 2)]
LOWER_FANGS = [(154.5, 82.0, 3, 2), (148.5, 82.8, 3, 2), (142.5, 83.6, 2, 1)]


def head_part(rig, rest):
    clip = K.poly(rig.TP('head', SKULL))
    fb = prims(rig, [HEAD_FB])[0]
    part, info = S.shade_clip(prims(rig, HEAD_SPEC), clip, 'hide', fb, bias=0.04, flatten=0.85, bounce=0.35)
    spec = HEAD_SPEC + [HEAD_FB]
    rclip = K.poly(rest.TP('head', SKULL))
    bumps(rig, rest, spec, part, seed=17, step=6, clip=rclip)
    scales(rig, rest, spec, part, seed=19, dx=6, dy=5, clip=rclip)
    S.rim_light(part)
    small = rig.sc < 0.55 * BASE_SC
    # the brow
    brow = rig.tline('head', BROW)
    nx, ny = rig.turn('head', (0.0, 1.0))
    thick = (int(round(nx)), int(round(ny))) if not rig.rest else (0, 1)
    for (x, y) in brow:
        for q in ((x, y), (x + thick[0], y + thick[1])) if not small else ((x, y),):
            if q in part:
                part[q] = 'k'
        up = (x - thick[0], y - thick[1])
        if part.get(up) not in (None, 'k'):
            part[up] = '&'
        up2 = (x - 2 * thick[0], y - 2 * thick[1])
        if part.get(up2) in ('@', '&', '%'):
            part[up2] = '+'
    # the eye
    rest_anchor = rest.Ti('head', EYE_AT)
    rest_anchor = (rest_anchor[0] + 1, rest_anchor[1])
    anchor_design = rest.inv(rest_anchor)
    if small:
        ex, ey = rig.Ti('head', (146.0, 67.6))
        part[(ex, ey)] = 'O'
        part[(ex + 1, ey)] = 'k'
    elif getattr(rig, 'eye', 'normal') != 'normal':
        style = rig.eye
        rows, off = EYE_STYLES[style]
        a = (rest_anchor[0] + off[0], rest_anchor[1] + off[1])
        eye = sprite_place(rows, a, rig, 'head', rest.inv(a), keyline=True)
        for q, k in eye.items():
            if q in part or k != 'k':
                part[q] = k
    else:
        eye = sprite_place(EYE_MAP, rest_anchor, rig, 'head', anchor_design, keyline=not rig.rest)
        for q, k in eye.items():
            if q in part or k != 'k':
                part[q] = k
        # the socket's shadow under it
        if rig.rest:
            ex, ey = rest_anchor
            for c in range(3, 13):
                q = (ex + c, ey + len(EYE_MAP))
                if part.get(q) not in (None, 'k'):
                    part[q] = '%'
        else:
            for (x, y), k in eye.items():
                if k == 'k':
                    q = (x + int(round(nx)), y + int(round(ny)))
                    if part.get(q) not in (None, 'k') and q not in eye:
                        part[q] = '%'
    for q in K.poly(rig.TP('head', NOSTRIL)):
        part[q] = 'k'
    if not small:
        for q in K.poly(rig.TP('head', EAR)):
            part[q] = 'k'
    for q in rig.tline('head', MOUTH):
        if q in part:
            part[q] = 'k'
    for (x, y) in rig.tline('head', MOUTH):
        up = (x - thick[0], y - thick[1])
        if part.get(up) not in (None, 'k'):
            part[up] = '%'
    return part


def jaw_part(rig, rest):
    clip = K.poly(rig.TP('jaw', JAW))
    fb = prims(rig, [JAW_FB])[0]
    part, info = S.shade_clip(prims(rig, JAW_SPEC), clip, 'hide', fb, bias=0.0, bounce=0.3)
    spec = JAW_SPEC + [JAW_FB]
    rclip = K.poly(rest.TP('jaw', JAW))
    bumps(rig, rest, spec, part, seed=23, step=6, clip=rclip)
    scales(rig, rest, spec, part, seed=29, dx=6, dy=5, clip=rclip)
    S.rim_light(part)
    return part


def collar_part(rig):
    part, _ = S.shade(prims(rig, COLLAR), 'hide', bias=-0.02, bounce=0.3)
    S.rim_light(part)
    seam(rig, 'head', part, [(108.5, 84), (114, 89), (121, 92.5), (128, 92)])
    return part


def fang_pixels(x, y, n, w, up=False):
    px = {}
    for i in range(n):
        ww = max(1, int(round(w - (w - 1) * i / max(1, n - 1))))
        yy = y - i if up else y + i
        for j in range(ww):
            if i == 0:
                k = '7' if j == 0 else '6'
            elif i < n - 1:
                k = '6' if j == 0 else '5'
            else:
                k = '5'
            px[(x + j, yy)] = k
    ring = {}
    for (fx, fy) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (fx + dx, fy + dy)
            if q not in px:
                ring[q] = 'k'
    return px, ring


def _fang_rows(n, w, up=False):
    px, _ = fang_pixels(0, 0, n, w, up)
    ys = [y for (x, y) in px]
    y0 = min(ys)
    rows = []
    for y in range(y0, max(ys) + 1):
        rows.append(''.join(px.get((x, y), '.') for x in range(0, w)))
    return rows, -y0


def mouth_interior(rig, jaw_deg):
    """The open mouth's polygon in the frame: the upper jaw's mouth line front to back, then the
    turned jaw's top edge back to front."""
    if jaw_deg <= 0:
        return None
    upper = [rig.T('head', p) for p in MOUTH]
    lower = [rig.T('jaw', p) for p in JAW_TOP]
    return upper + lower


def _ring(pix):
    out = set()
    for (x, y) in pix:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in pix:
                out.add(q)
    return out


def mouth(rig, rest, cv, jaw_deg=0.0, glow=False, jaw_px=None, head_px=None):
    """Teeth and, open, the throat's light (between the jaws' own keylines, which stay). Returns the
    effect pixels."""
    fx = set()
    small = rig.sc < 0.55 * BASE_SC
    poly = mouth_interior(rig, jaw_deg)
    if poly:
        jf = set(jaw_px or {})
        hf = set(head_px or {})
        keep = jf | hf | _ring(jf) | _ring(hf)
        inside = {q for q in K.poly(poly) if q not in keep}
        hinge = rig.T('jaw', (131, 88))
        front = rig.T('head', (166.5, 82.0))
        fx_, fy_ = front[0] - hinge[0], front[1] - hinge[1]
        L = math.hypot(fx_, fy_) or 1.0
        for (x, y) in inside:
            t = ((x - hinge[0]) * fx_ + (y - hinge[1]) * fy_) / (L * L)
            # depth across the gap: distance to the gap's centre line, relative
            cx_, cy_ = rig.T('head', (148, 84.0 + jaw_deg * 0.18))
            if glow:
                core = abs(((x - hinge[0]) * -fy_ + (y - hinge[1]) * fx_) / L
                           - ((cx_ - hinge[0]) * -fy_ + (cy_ - hinge[1]) * fx_) / L)
                gap = rig.R(1.0 + jaw_deg * 0.16)
                rel = core / max(1.0, gap)
                if rel < 0.5 and t < 0.85:
                    k = 'X'
                elif rel < 0.95:
                    k = 'K' if t < 0.9 else 'J'
                else:
                    k = 'J' if t < 0.6 else 'I'
            else:
                k = 'v' if t < 0.7 else 'V'
            cv.px[(x, y)] = k
        for (x, y) in inside:
            if any(q not in cv.px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                if glow:
                    fx.add((x, y))
                else:
                    cv.px[(x, y)] = 'k'
        if glow and jaw_px:
            near = set()
            for (x, y) in inside:
                for dx in (-2, -1, 0, 1, 2):
                    for dy in (-2, -1, 0, 1, 2):
                        near.add((x + dx, y + dy))
            jring = _ring(jf)
            for q in jaw_px:
                if q in near and any(n in jring for n in ((q[0], q[1] - 1), (q[0] - 1, q[1]), (q[0] + 1, q[1]),
                                                           (q[0], q[1] + 1))):
                    if cv.px.get(q) not in (None, 'k'):
                        cv.px[q] = 'I'
    if small:
        return fx
    ml = rig.tline('head', MOUTH)
    for (x, y, n, w) in UPPER_FANGS:
        if rig.rest:
            fxp, fy = rig.Ti('head', (x, y))
            rows = [yy for (xx, yy) in ml if xx == fxp]
            if rows:
                fy = max(rows) + 1
            px, ring = fang_pixels(fxp, fy, n, w)
            for q in ring:
                if q not in px and q[1] >= fy and cv.px.get(q) not in ('X', 'K', 'J', 'I'):
                    cv.px[q] = 'k'
            for q, k in px.items():
                cv.px[q] = k
        else:
            rows, _ = _fang_rows(n, w)
            rest_x, rest_y = rest.Ti('head', (x, y))
            rrows = [yy for (xx, yy) in rest.tline('head', MOUTH) if xx == rest_x]
            if rrows:
                rest_y = max(rrows) + 1
            spr = sprite_place(rows, (rest_x, rest_y), rig, 'head', rest.inv((rest_x, rest_y)))
            for q, k in spr.items():
                if k == 'k' and cv.px.get(q) in ('X', 'K', 'J', 'I'):
                    continue
                cv.px[q] = k
    if not jaw_deg:
        for (x, y, n, w) in LOWER_FANGS:
            if rig.rest:
                fxp, fy = rig.Ti('head', (x, y))
                rows = [yy for (xx, yy) in ml if xx == fxp]
                if rows:
                    fy = min(rows) - 1
                px, ring = fang_pixels(fxp, fy, n, w, up=True)
                for q in ring:
                    if q not in px and q[1] <= fy and cv.px.get(q) is not None:
                        cv.px[q] = 'k'
                for q, k in px.items():
                    cv.px[q] = k
            else:
                rows, top = _fang_rows(n, w, up=True)
                rest_x, rest_y = rest.Ti('head', (x, y))
                rrows = [yy for (xx, yy) in rest.tline('head', MOUTH) if xx == rest_x]
                if rrows:
                    rest_y = min(rrows) - 1
                a = (rest_x, rest_y - (n - 1))
                spr = sprite_place(rows, a, rig, 'head', rest.inv(a))
                for q, k in spr.items():
                    if k == 'k' and q in ml:
                        continue
                    if k == 'k' and cv.px.get(q) is None:
                        continue
                    cv.px[q] = k
    return fx


def flare(rig, cv, origin):
    fx = set()
    ox, oy = origin
    burst = {(0, 0): 'X', (1, 0): 'X', (2, 0): 'K', (3, 0): 'J', (4, 0): 'I', (0, -1): 'K', (1, -1): 'K',
             (2, -1): 'J', (0, 1): 'K', (1, 1): 'K', (2, 1): 'J', (0, -2): 'J', (1, -2): 'I', (0, 2): 'J',
             (1, 2): 'I', (6, -2): 'K', (7, -2): 'J', (6, 3): 'J', (9, 1): 'I', (5, -4): 'I', (4, 4): 'I'}
    a = math.radians(rig.rot['head'])
    c, s = math.cos(a), math.sin(a)
    for (dx, dy), k in burst.items():
        q = (int(round(ox + dx * c - dy * s)), int(round(oy + dx * s + dy * c)))
        if q not in cv.px:
            cv.px[q] = k
            fx.add(q)
    return fx


def glow_halo(cv, lit_parts, seed=5):
    fx, lit, ring = set(), set(), set()
    for part in lit_parts:
        lit |= {q for q, k in part.items() if k in ('X', 'K', 'J', 'I')}
    for (x, y) in lit:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ring.add((x + dx, y + dy))
    for (x, y) in ring:
        if cv.px.get((x, y)) != 'k':
            continue
        for dx, dy in ((-1, 0), (0, -1), (-1, -1), (1, -1)):
            q = (x + dx, y + dy)
            if q not in cv.px and (q[0] * 7349 + q[1] * 1931 + seed) % 7 < 4:
                cv.px[q] = 'I'
                fx.add(q)
    return fx


def sparks(rig, cv, design_points, bone='root'):
    fx = set()
    for p in design_points:
        x, y = rig.Ti(bone, p)
        star = {(x, y): 'X', (x + 1, y): 'J', (x - 1, y): 'J', (x, y + 1): 'J', (x, y - 1): 'J'}
        if all(q not in cv.px for q in star):
            for q, k in star.items():
                cv.px[q] = k
                fx.add(q)
    return fx


def close_holes(px):
    if not px:
        return set()
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    blue = set()
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            if (x, y) not in px and all(q in px for q in n4):
                if any(px[q] == 'I' for q in n4):
                    px[(x, y)] = 'I'
                    blue.add((x, y))
                else:
                    px[(x, y)] = 'k'
    return blue


#IK (two-bone legs)

def leg_ik(rig_pose, side, ankle_target, foot_world=0.0, knee_fwd=True):
    """Set the thigh / shin / foot rotations of `side` ('n' or 'f') in rig_pose (a pose dict) so the
    ankle lands on ankle_target (world design) with the knee bending forward (to the right) and the
    foot turned to foot_world degrees in the world. Uses the pose's pelvis as it stands."""
    hip_b, knee_b, ank_b = side + '_thigh', side + '_shin', side + '_foot'
    hip0 = BONES[hip_b][1]
    knee0 = BONES[knee_b][1]
    ank0 = BONES[ank_b][1]
    probe = Rig({k: v for k, v in rig_pose.items() if k not in (hip_b, knee_b, ank_b)})
    H = probe.W('pelvis', hip0)
    L1 = math.hypot(knee0[0] - hip0[0], knee0[1] - hip0[1])
    L2 = math.hypot(ank0[0] - knee0[0], ank0[1] - knee0[1])
    ax, ay = ankle_target[0] - H[0], ankle_target[1] - H[1]
    d = max(1e-6, min(L1 + L2 - 1e-6, math.hypot(ax, ay)))
    base = math.atan2(ay, ax)
    cos_a = (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    # the knee on the forward (right / +x) side of the hip -> ankle line
    k1 = (H[0] + L1 * math.cos(base + a), H[1] + L1 * math.sin(base + a))
    k2 = (H[0] + L1 * math.cos(base - a), H[1] + L1 * math.sin(base - a))
    Kp = k1 if (k1[0] > k2[0]) == knee_fwd else k2
    th_world = math.degrees(math.atan2(Kp[1] - H[1], Kp[0] - H[0]) - math.atan2(knee0[1] - hip0[1], knee0[0] - hip0[0]))
    sh_world = math.degrees(math.atan2(ankle_target[1] - Kp[1], ankle_target[0] - Kp[0])
                            - math.atan2(ank0[1] - knee0[1], ank0[0] - knee0[0]))
    pel = probe.rot['pelvis']
    rig_pose[hip_b] = (th_world - pel, 0.0, 0.0)
    rig_pose[knee_b] = (sh_world - th_world, 0.0, 0.0)
    rig_pose[ank_b] = (foot_world - sh_world, 0.0, 0.0)
    return rig_pose


def remove_islands(px, keep=(), min_size=14):
    """Drop small loose clumps (8-connected) that a floor clip or a buried part can leave behind;
    `keep` pixels (effects) are left alone and do not count."""
    seen = set()
    drop = []
    for q in list(px):
        if q in seen or q in keep:
            continue
        comp, stack = [], [q]
        seen.add(q)
        while stack:
            c = stack.pop()
            comp.append(c)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (c[0] + dx, c[1] + dy)
                    if n in px and n not in seen and n not in keep:
                        seen.add(n)
                        stack.append(n)
        if len(comp) < min_size:
            drop.extend(comp)
    for q in drop:
        del px[q]
    return drop


def tail_ground(pose, base_y=163.0):
    """Keep the tail's forward curl lying on the mat however the hips move: turn the tail root (t1,
    on top of any turn the pose already gives it) until the curl's start sits back on its rest height,
    then turn the curl (t3) level again."""
    extra1 = pose.get('t1', (0.0, 0.0, 0.0))[0]
    extra3 = pose.get('t3', (0.0, 0.0, 0.0))[0]
    p3 = BONES['t3'][1]

    def y_at(a):
        q = dict(pose)
        q['t1'] = (extra1 + a, 0.0, 0.0)
        return Rig(q).W('t2', p3)[1]
    lo, hi = -80.0, 80.0
    f_lo, f_hi = y_at(lo) - base_y, y_at(hi) - base_y
    if f_lo * f_hi > 0:
        a = lo if abs(f_lo) < abs(f_hi) else hi
    else:
        for _ in range(40):
            mid = (lo + hi) / 2.0
            fm = y_at(mid) - base_y
            if (fm > 0) == (f_hi > 0):
                hi, f_hi = mid, fm
            else:
                lo, f_lo = mid, fm
        a = (lo + hi) / 2.0
    pose['t1'] = (extra1 + a, 0.0, 0.0)
    rot2 = Rig(pose).rot['t2']
    pose['t3'] = (extra3 - rot2, 0.0, 0.0)
    return pose


def seal(px, fx=()):
    """Close any keyline gap: a transparent pixel beside a body colour becomes keyline (effects
    excepted). The rest frame has none, so this never changes it."""
    add = set()
    for (x, y), k in px.items():
        if k == 'k' or (x, y) in fx:
            continue
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in px:
                add.add(q)
    for q in add:
        px[q] = 'k'
    return add
