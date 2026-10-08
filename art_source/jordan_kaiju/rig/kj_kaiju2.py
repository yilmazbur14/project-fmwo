"""The kaiju, v2: Jordan's mount for phase 1, at the architect's layout scale (2026-10-04 update):
standing against the LEFT ropes, FACING RIGHT into the open ring, never mirrored.

A PARODY, original in its details. The genre's silhouette (an upright heavy reptile, jagged dorsal
plates, a thick tail, a small fierce head, blue breath); ours: a charcoal-teal vinyl hide with a toy's
gloss, an ivory scuted belly, ivory plates that light ice-blue to white (the glow chase variant),
amber-gold eyes, toy joint seams at the shoulders, hips and tail base, a gold star sticker on the
stomping (far) foot, and the tail curled forward round the near foot the way display figures stand.

The design is authored in DESIGN coordinates (the v1 approval frame's space: soles on row 171, the
feet centred on x 98) and drawn through one transform, T: design -> frame, scale SC. Jordan is never
scaled: he is drawn at his own pixel scale (the game's 3x, like the kaiju) and only placed.
Lit from the upper left like the cast.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
from kj_shade import Cap, Ell  # noqa: E402

SC = 1.45                    # design -> frame scale
DX0, DY0 = 98.0, 171.0       # the design anchor: the feet centre on the soles' keyline
OX, OY = 102.0, 220.0        # where the anchor lands on the working canvas
CW, CH = 224, 246            # the working canvas (cropped to the frame at the end)
SOLE = int(round(OY))        # the soles' keyline row on the working canvas


def T(x, y):
    return (OX + SC * (x - DX0), OY + SC * (y - DY0))


def Ti(x, y):
    p = T(x, y)
    return (int(round(p[0])), int(round(p[1])))


def R(r):
    return r * SC


def E(cx, cy, rx, ry, z=0.0):
    p = T(cx, cy)
    return Ell(p[0], p[1], R(rx), R(ry), z=R(z))


def C(p0, p1, r0, r1, z=0.0):
    return Cap(T(*p0), T(*p1), R(r0), R(r1), z=R(z))


def TP(pts):
    return [T(x, y) for (x, y) in pts]


def tline(pts):
    """A polyline in design coordinates -> the frame pixels along it (Bresenham per segment)."""
    out = []
    ip = [Ti(x, y) for (x, y) in pts]
    for (x0, y0), (x1, y1) in zip(ip, ip[1:]):
        for q in K.line(x0, y0, x1, y1):
            if not out or out[-1] != q:
                out.append(q)
    return out


#CANVAS

class KCanvas:
    def __init__(self, w=CW, h=CH):
        self.w, self.h = w, h
        self.px = {}

    def inb(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, cast=2, floor=None):
        """A cast shadow down-right onto what is already there, the keyline round the part, then the
        part. Fills stop above `floor` (default the soles' keyline row), so soles are flat."""
        floor = SOLE if floor is None else floor
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
            if self.inb(q) and q[1] <= floor:
                self.px[q] = 'k'
        for q, k in part.items():
            if self.inb(q):
                self.px[q] = k


#DORSAL PLATES (design coordinates)

# the back ridge, tail tip -> nape: along the top of the tail's forward curl, round its back curve,
# up the back to the base of the skull
RIDGE = [(101.5, 170.5), (95, 174.6), (81, 175.4), (67, 171.6), (58, 165), (53.5, 156), (56, 145),
         (61, 134), (64, 124), (66, 113), (70, 102), (77, 91), (87, 82), (98, 75), (107, 70), (114, 66)]
TAIL_FRONT_END = 4           # RIDGE[0..4] runs along the tail's forward curl (drawn in front of the foot)


def _ridge_segs():
    segs, tot = [], 0.0
    for a, b in zip(RIDGE, RIDGE[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L))
        tot += L
    return segs, tot


def ridge_at(s):
    segs, tot = _ridge_segs()
    d = s * tot
    for a, b, L in segs:
        if d <= L or (a, b, L) == segs[-1]:
            t = min(1.0, d / L)
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        d -= L
    raise AssertionError


PLATE_BIG = [(-0.50, 0.00), (-0.44, 0.20), (-0.66, 0.34), (-0.36, 0.40), (-0.48, 0.62), (-0.18, 0.60),
             (0.00, 1.00), (0.15, 0.62), (0.40, 0.66), (0.24, 0.44), (0.54, 0.34), (0.38, 0.18),
             (0.50, 0.00)]
PLATE_MID = [(-0.50, 0.00), (-0.46, 0.30), (-0.64, 0.46), (-0.22, 0.56), (0.00, 1.00), (0.20, 0.58),
             (0.52, 0.44), (0.36, 0.24), (0.50, 0.00)]
PLATE_SMALL = [(-0.50, 0.00), (-0.40, 0.48), (0.00, 1.00), (0.34, 0.50), (0.50, 0.00)]


def plate_poly(base, direction, h, w):
    """Frame-space plate outline; base / h / w already in frame units."""
    dx, dy = direction
    px, py = -dy, dx
    shape = PLATE_BIG if h >= 20 else (PLATE_MID if h >= 12 else PLATE_SMALL)
    return [(base[0] + px * a * w + dx * b * h, base[1] + py * a * w + dy * b * h) for (a, b) in shape]


# (s along the ridge, height in design units, group). Groups light 0 (tail tip) .. 6 (nape).
PLATES = [
    (0.030, 3.2, 0), (0.085, 3.8, 0), (0.145, 4.4, 0),           # nubs along the tail's forward curl
    (0.215, 6.5, 1), (0.265, 8.0, 1), (0.315, 9.5, 1),           # up the tail's root
    (0.365, 11.0, 2), (0.415, 12.5, 2),
    (0.465, 14.5, 3), (0.515, 16.5, 3),
    (0.565, 19.0, 4), (0.620, 21.5, 4),
    (0.680, 23.5, 5), (0.740, 23.0, 5),
    (0.805, 20.0, 6), (0.865, 16.0, 6), (0.925, 12.0, 6), (0.975, 8.5, 6),
]
N_GROUPS = 7


def outward(tg):
    """The ridge's outward side: whichever normal points up (and, on a vertical run, left)."""
    a = (tg[1], -tg[0])
    b = (-tg[1], tg[0])
    return a if (a[1] + 0.4 * a[0]) < (b[1] + 0.4 * b[0]) else b


def plate_dir(tg, lean=0.38):
    n = outward(tg)
    dx, dy = n[0] - tg[0] * lean, n[1] - tg[1] * lean
    ln = math.hypot(dx, dy)
    return dx / ln, dy / ln


def plate_part(pts, glow=0.0, dim=False):
    shape = K.poly(pts)
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
        if glow > 0 and along <= glow:
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


def plates(group_glow, row='main'):
    parts = []
    for (s, size, g) in PLATES:
        glow = group_glow.get(g, 0.0)
        if row == 'far':
            p, tg = ridge_at(min(0.995, s + 0.022))
            d = plate_dir(tg, lean=0.2)
            n = outward(tg)
            # the far row sits a little up-right of the ridge (across the back, away from us)
            bp = (p[0] + 1.2 - n[0] * 0.6, p[1] - 1.2 - n[1] * 0.6)
            h, w = size * 0.72 + 1.5, size * 0.66 + 1.0
        else:
            p, tg = ridge_at(s)
            d = plate_dir(tg)
            bp = (p[0] - d[0] * 2.5, p[1] - d[1] * 2.5)
            h, w = size + 2.5, size * 0.74 + 1.5
        base = T(*bp)
        parts.append((plate_part(plate_poly(base, d, R(h), R(w)), glow, dim=(row == 'far')), g))
    return parts


#BODY (design coordinates through T)

def tail_back_prims():
    """The tail's root: out of the back of the hips and down to the mat (behind the near leg)."""
    return [C((64, 140), (57, 153), 14.0, 12.5), C((57, 153), (55, 163), 12.5, 10.5)]


def tail_front_prims():
    """The tail curled forward round the front of the near heel, the tip lifting (how display
    figures stand): drawn in front of the near foot."""
    return [C((55, 163), (62, 174), 10.5, 8.2), C((62, 174), (80, 178.6), 8.2, 6.0),
            C((80, 178.6), (94, 177.2), 6.0, 4.0), C((94, 177.2), (101, 172), 4.0, 2.3)]


TAIL_FLOOR = Ti(0, 184.0)[1]       # the tail lies on the mat a little in front of the feet


def far_leg_prims():
    return [E(121, 139, 15, 16), C((123, 148), (125, 162), 10.5, 9.5)]


def far_foot_prims():
    return [E(126, 165.5, 15, 6.2), E(139, 167.5, 5, 4.2), E(145, 168.5, 3.8, 3.2)]


def torso_prims():
    return [E(99, 128, 36, 29), E(103, 102, 30, 24), C((106, 92), (120, 80), 15.5, 13.0)]


def near_leg_prims():
    return [E(80, 138, 19, 18), C((75, 150), (71, 162), 12.0, 11.0)]


def near_foot_prims():
    return [E(70, 165.5, 19, 6.4), E(87, 167.0, 5.5, 4.6), E(94, 168.5, 4.2, 3.4)]


def near_arm_parts():
    upper = [C((86, 96), (92, 112), 7.6, 6.6)]
    fore = [C((92, 112), (109, 105), 7.0, 5.6)]
    palm = [E(112.5, 105, 5.2, 4.6)]
    fingers = [[C((115, 101.5), (120.5, 102.5), 2.3, 1.9)],
               [C((116, 105.5), (121.5, 107.5), 2.3, 1.9)],
               [C((114.5, 109), (118, 112.5), 2.3, 1.9)]]
    tips = [(124.5, 104.5, 1, 0.6), (124.5, 110.5, 0.7, 1), (119.5, 116.5, 0.2, 1)]
    return upper, fore, palm, fingers, tips


def far_arm_parts():
    upper = [C((128, 99), (139, 106), 6.0, 5.0)]
    fore = [C((139, 106), (146, 102), 5.0, 4.2)]
    fingers = [[C((148, 99.5), (152, 99.5), 1.9, 1.6)], [C((149, 103), (152.5, 104.5), 1.9, 1.6)]]
    tips = [(155.5, 100.5, 1, 0.5), (155, 107.5, 0.6, 1)]
    return upper, fore, fingers, tips


#THE HEAD

SKULL = [(113, 70), (117, 64), (125, 61), (135, 60), (141, 59), (147, 59), (151, 61), (153, 64),
         (155, 66), (160, 67), (165, 69), (167, 71), (167.5, 77), (166, 81), (152, 82.5), (145, 83.5),
         (139, 84.5), (134, 86.5), (130, 90), (124, 92), (117, 91), (113, 86), (111.5, 78)]
JAW = [(131, 87.5), (139, 85.5), (148, 84.5), (157, 83.5), (163, 83.5), (164.5, 86), (162.5, 90),
       (155, 93.5), (144, 96), (133, 96), (126, 93)]


def head_prims():
    return [E(128, 74, 16, 13), E(145, 64.5, 8.5, 4.2, z=3.0), C((141, 74), (161, 75), 9.0, 6.6),
            E(126, 83, 9.5, 7.0, z=1.0)]


BROW = [(138.5, 64.5), (145.5, 66.0), (152.5, 68.3)]
EYE_MAP = [                       # frame pixels, top-left at the eye anchor
    "kGOYYOkOOGkk...",
    ".kGOOOkOOOOGk..",
    "..kkGOkOOOGGkk.",
    "....kkkkkkkk...",
]
NOSTRIL = [(160.4, 69.8), (162.6, 69.8), (162.8, 71.4), (161.0, 71.2)]
MOUTH = [(166.5, 81.6), (152, 82.2), (145, 83.2), (139, 84.2), (135, 85.2), (132.6, 86.4)]
EAR = [(118.4, 76.6), (120.6, 76.6), (120.4, 78.6), (118.6, 78.4)]


def mouth_pixels():
    return tline(MOUTH)


def head_part():
    clip = K.poly(TP(SKULL))
    fb = E(138, 76, 32, 22, z=-30)
    part, info = S.shade_clip(head_prims(), clip, 'hide', fb, bias=0.04, flatten=0.85, bounce=0.35)
    bumps(part, seed=17, step=6)
    scales(part, seed=19, dx=6, dy=5)
    S.rim_light(part)
    # the brow: a heavy black scowl line, two pixels deep, its underside in shadow, its top lit
    brow = tline(BROW)
    for (x, y) in brow:
        for q in ((x, y), (x, y + 1)):
            if q in part:
                part[q] = 'k'
        up = (x, y - 1)
        if part.get(up) not in (None, 'k'):
            part[up] = '&'
        up2 = (x, y - 2)
        if part.get(up2) in ('@', '&', '%'):
            part[up2] = '+'
    # the eye under it: an amber-gold slit pressed down at the front by the scowl, a black slit
    # pupil, a hot glint, the lower lid, the socket's shadow under it
    ex, ey = Ti(142.2, 66.6)
    ex, ey = ex + 1, ey
    for r, row in enumerate(EYE_MAP):
        for c, ch in enumerate(row):
            if ch != '.':
                part[(ex + c, ey + r)] = ch
    for c in range(3, 13):
        q = (ex + c, ey + len(EYE_MAP))
        if part.get(q) not in (None, 'k'):
            part[q] = '%'
    for q in K.poly(TP(NOSTRIL)):
        part[q] = 'k'
    for q in K.poly(TP(EAR)):
        part[q] = 'k'
    # the mouth line, the upper lip rolling under above it
    for q in mouth_pixels():
        if q in part:
            part[q] = 'k'
    for (x, y) in mouth_pixels():
        up = (x, y - 1)
        if part.get(up) not in (None, 'k'):
            part[up] = '%'
    return part


def jaw_part(open_by=0.0):
    pts = []
    for (x, y) in JAW:
        t = max(0.0, (x - 128) / 34.0)
        pts.append((x, y + open_by * t))
    clip = K.poly(TP(pts))
    prims = [C((130, 91 + open_by * 0.1), (159, 88.5 + open_by * 0.9), 6.0, 4.5)]
    fb = E(146, 90 + open_by * 0.5, 24, 10, z=-20)
    part, info = S.shade_clip(prims, clip, 'hide', fb, bias=0.0, bounce=0.3)
    bumps(part, seed=23, step=6)
    scales(part, seed=29, dx=6, dy=5)
    S.rim_light(part)
    return part


# fangs (design x, design top y, rows, width): hanging from the upper jaw over the lower lip; up from
# the lower jaw over the upper lip
UPPER_FANGS = [(162, 82.6, 4, 3), (157, 82.8, 3, 2), (151, 83.4, 4, 3), (145, 84.0, 3, 2), (140, 84.8, 3, 2)]
LOWER_FANGS = [(154.5, 82.0, 3, 2), (148.5, 82.8, 3, 2), (142.5, 83.6, 2, 1)]


def fang(x, y, n, w, up=False):
    """A bone fang `w` wide at the root tapering to a point over `n` rows, with its keyline ring."""
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


def mouth(cv, open_by=0.0, glow=False, jaw_px=None, head_px=None):
    """Closed: the snarl, fangs over the lips. Open (the charge): the gap between the jaws lit from the
    throat, white-hot, cyan, blue at the lips; the lower lip catches the light; a flare spills out of
    the front. Returns the effect pixels."""
    fx = set()
    ml = mouth_pixels()
    if open_by:
        jaw_fill = {q for q, k in (jaw_px or {}).items() if k != 'k'}
        head_fill = {q for q, k in (head_px or {}).items() if k != 'k'}
        inside, lips = set(), set()
        for (x, y) in ml:
            col, yy = [], y + 1
            while yy < y + 24 and (x, yy) not in jaw_fill and (x, yy) not in head_fill:
                col.append((x, yy))
                yy += 1
            if (x, yy) in jaw_fill:
                inside.update(col[:-1])
                lips.add((x, yy))
        ys = {}
        for (x, y) in inside:
            ys.setdefault(x, []).append(y)
        x_lo = min(x for (x, y) in ml)
        x_hi = max(x for (x, y) in ml)
        for (x, y) in inside:
            t = (x - x_lo) / max(1.0, x_hi - x_lo)
            col = ys[x]
            mid = (min(col) + max(col)) / 2.0
            depth = abs(y - mid) / max(1.0, (max(col) - min(col)) / 2.0 + 0.5)
            if glow:
                if depth < 0.45 and t < 0.8:
                    k = 'X'
                elif depth < 0.8:
                    k = 'K' if t < 0.88 else 'J'
                else:
                    k = 'J' if t < 0.6 else 'I'
            else:
                k = 'v'
            cv.px[(x, y)] = k
        if glow:
            for (x, y) in inside:
                if any(q not in cv.px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                    fx.add((x, y))
            for q in lips:
                cv.px[q] = 'I'
    for (x, y, n, w) in UPPER_FANGS:
        fxp, fy = Ti(x, y)
        # sit the root on the mouth line's row at that column
        rows = [yy for (xx, yy) in ml if xx == fxp]
        if rows:
            fy = max(rows) + 1
        px, ring = fang(fxp, fy, n, w)
        for q in ring:
            if q not in px and q[1] >= fy and cv.px.get(q) not in ('X', 'K', 'J', 'I'):
                cv.px[q] = 'k'
        for q, k in px.items():
            cv.px[q] = k
    if not open_by:
        for (x, y, n, w) in LOWER_FANGS:
            fxp, fy = Ti(x, y)
            rows = [yy for (xx, yy) in ml if xx == fxp]
            if rows:
                fy = min(rows) - 1
            px, ring = fang(fxp, fy, n, w, up=True)
            for q in ring:
                if q not in px and q[1] <= fy and cv.px.get(q) is not None:
                    cv.px[q] = 'k'
            for q, k in px.items():
                cv.px[q] = k
    if glow and open_by:
        fx |= flare(cv)
    return fx


def flare(cv):
    """The glow spilling out of the open front of the mouth: a small burst, no keyline."""
    fx = set()
    ox, oy = mouth_origin(True)
    burst = {(0, 0): 'X', (1, 0): 'X', (2, 0): 'K', (3, 0): 'J', (4, 0): 'I', (0, -1): 'K', (1, -1): 'K',
             (2, -1): 'J', (0, 1): 'K', (1, 1): 'K', (2, 1): 'J', (0, -2): 'J', (1, -2): 'I', (0, 2): 'J',
             (1, 2): 'I', (6, -2): 'K', (7, -2): 'J', (6, 3): 'J', (9, 1): 'I', (5, -4): 'I', (4, 4): 'I'}
    for (dx, dy), k in burst.items():
        q = (ox + dx, oy + dy)
        if q not in cv.px:
            cv.px[q] = k
            fx.add(q)
    return fx


def mouth_origin(charge=False):
    """The beam's origin: just in front of the open mouth's front, on its centre line (frame px)."""
    return Ti(168.5, 85.6 if not charge else 88.0)


#SURFACE DETAIL

BELLY_LINE = [(126, 86), (127, 98), (125, 111), (120, 124), (114, 138), (108, 151)]
BELLY_HALF = [5.0, 8.0, 10.0, 11.0, 10.0, 7.0]
BELLY_STEP = 9               # frame px between scute seams


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


def belly(part, info):
    """The front band as ivory scutes (the plates' own bone ramp), lit by the same light, a black seam
    every BELLY_STEP px curved like hoops round the belly, a lit lip above each; a black rim."""
    line_f = TP(BELLY_LINE)
    half = [R(h) for h in BELLY_HALF]
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
        a = along + rel * rel * 2.4
        if int(a) % BELLY_STEP == 0 and rel < 0.92 and along < tot - 7:
            part[q] = 'k'
        elif int(a) % BELLY_STEP == BELLY_STEP - 1 and rel < 0.9 and part[q] in ('5', '6'):
            part[q] = S.LIGHTER[part[q]]
    edge = [q for q in region if any((q[0] + dx, q[1] + dy) in part and (q[0] + dx, q[1] + dy) not in region
                                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for q in edge:
        part[q] = 'k'
    return region


def bumps(part, seed=7, step=7, keys=('@', '+', '&')):
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    for gy in range(min(ys), max(ys) + 1, step):
        for gx in range(min(xs), max(xs) + 1, step):
            h = (gx * 73856093 ^ gy * 19349663 ^ seed * 83492791) & 0xFFFF
            x = gx + (h % 3) - 1 + ((gy // step) % 2) * (step // 2)
            y = gy + ((h >> 4) % 3) - 1
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


def seam(part, design_pts):
    """A toy joint seam round a limb: a black cut with a lit bevel on its upper side."""
    pix = tline(design_pts)
    for q in pix:
        if q in part:
            part[q] = 'k'
    for (x, y) in pix:
        q = (x, y - 1)
        if q in part and part[q] != 'k' and part[q] in ('@', '+', '&', '%', '#', '='):
            part[q] = '='


def claws(tips, size=3.0):
    out = {}
    for (tx, ty, dx, dy) in tips:
        tx, ty = T(tx, ty)
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px, py = -uy, ux
        sz = R(size)
        base = (tx - ux * sz, ty - uy * sz)
        hw = R(1.3)
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
    [(66, 128), (68, 125), (71, 123), (75, 122)],
    [(84, 87), (87, 85), (91, 84)],
    [(80, 108), (82, 106)],
    [(124, 63), (129, 62)],
    [(156, 69), (160, 69.5)],
    [(60, 146), (58, 150)],
    [(88, 98), (89.5, 96.5)],
    [(117, 132), (119, 129)],
]
KNEE_CREASES = [[(61, 150), (63, 153), (66, 155)], [(108, 149), (110, 151)]]


def gloss(px):
    """The vinyl's sheen: crisp highlight streaks, two pixels thick (the core and a soft edge)."""
    for pts in GLOSS:
        line = tline(pts)
        for (x, y) in line:
            if px.get((x, y)) in ('@', '+', '=', '&'):
                px[(x, y)] = '~'
            q = (x, y + 1)
            if px.get(q) in ('@', '+', '&'):
                px[q] = '='


def creases(px):
    for pts in KNEE_CREASES:
        for q in tline(pts):
            if px.get(q) not in (None, 'k'):
                px[q] = 'k'


# the chase edition's gold star sticker on the stomping (far) foot: its sole carries the full star
# (seen when the foot lifts); the heel shows its edge here
STAR = [
    "...O...",
    "..OYO..",
    "OOOYOOO",
    ".OOOOG.",
    "..OGO..",
    ".OG.GO.",
]


def star_mark(px, at=None):
    ax, ay = at or Ti(113.5, 162.5)
    for r, row in enumerate(STAR):
        for c, ch in enumerate(row):
            q = (ax + c - 3, ay + r - 3)
            if ch != '.' and px.get(q) not in (None, 'k'):
                px[q] = ch


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


def sparks(cv, design_points):
    fx = set()
    for (dx_, dy_) in design_points:
        x, y = Ti(dx_, dy_)
        star = {(x, y): 'X', (x + 1, y): 'J', (x - 1, y): 'J', (x, y + 1): 'J', (x, y - 1): 'J'}
        if all(q not in cv.px for q in star):
            for q, k in star.items():
                cv.px[q] = k
                fx.add(q)
    return fx


def close_holes(px):
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


def ridge_s_at_index(i):
    """Arc-length fraction of RIDGE[i]."""
    segs, tot = _ridge_segs()
    return sum(L for (_, _, L) in segs[:i]) / tot


def scales(part, seed=1, dx=5, dy=4, keys=('@', '+', '&', '%'), margin=2, skip=None):
    """The hide's sculpted scales: a brick pattern of short dark arcs (two pixels, one tone down),
    each with a lit pixel above-left of it, kept off the part's edges and off `skip` pixels."""
    skip = skip or set()
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    for gy in range(min(ys), max(ys) + 1, dy):
        off = (dx // 2) if (gy // dy) % 2 else 0
        for gx in range(min(xs) + off, max(xs) + 1, dx):
            h = (gx * 92821 ^ gy * 68917 ^ seed * 1237) & 0xFFF
            if h % 5 == 0:
                continue                                  # not every scale reads
            x, y = gx + (h % 2), gy + ((h >> 5) % 3) - 1
            n = 1 + (h >> 7) % 3
            pts = [(x + i, y) for i in range(n)]
            if any(part.get(q) not in keys or q in skip for q in pts):
                continue
            if not all((x + ax, y + ay) in part for ax in range(-margin, margin + 2)
                       for ay in range(-margin, margin + 1)):
                continue
            for q in pts:
                part[q] = 'k' if part[q] in ('%', '&') else S.DARKER[part[q]]
            for q in ((x - 1, y - 1), (x, y - 1)):
                if part.get(q) in keys and q not in skip and (h >> 3) % 3:
                    part[q] = S.LIGHTER[part[q]]
                    break


FOLDS = [
    [(119, 89), (122, 91.5), (125, 92.5)],            # skin folds on the neck under the jaw
    [(117, 93), (120.5, 95.5), (124, 96.5)],
    [(94, 114.5), (96, 117)],                          # the elbow crease
    [(70, 168.5), (72, 172), (71, 175.5)],             # rings round the tail's forward curl
    [(82, 171.5), (83.5, 175), (82.5, 178)],
    [(91, 171), (92, 174)],
]


def folds(px):
    for pts in FOLDS:
        for q in tline(pts):
            if px.get(q) not in (None, 'k') and px.get(q) in ('#', '%', '&', '@', '+', '=', '~'):
                px[q] = 'k'
