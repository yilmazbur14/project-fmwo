"""The kaiju: a vinyl collectible grown to full size, Jordan's mount for phase 1.

A PARODY, original in its details: the silhouette is the genre's (an upright heavy reptile, rows of
jagged dorsal plates, a thick tail, a small fierce head, blue breath); what is ours is a slate-teal
vinyl hide with a toy's gloss, sand-coloured belly scutes, bone plates that glow (the "glow chase"
variant), amber eyes, and the toy winks: articulation cuts at the shoulder and the hip.

Three-quarter view facing screen-right, lit from the upper left. Frame coordinates (W x H), the soles
on SOLE_Y. Parts are stamped back to front; each part keylines itself over what is under it (the
house style's interior separations) and casts a short shadow down-right onto what is under it.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kj_common as K  # noqa: E402
import kj_shade as S  # noqa: E402
from kj_shade import Cap, Ell  # noqa: E402

W, H = 192, 172
SOLE_Y = 171           # the soles' keyline: the frame's bottom row


#CANVAS

class KCanvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def inb(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, cast=2, only_cast=None):
        """Stamp a part: a cast shadow down-right onto what is already there, the keyline round it,
        then the part. Nothing goes below the floor: fills stop on row SOLE_Y - 1 (flat soles, the
        tail lying on the mat), so the keyline closes along SOLE_Y."""
        part = {q: k for q, k in part.items() if q[1] < SOLE_Y}
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
                if only_cast is not None and k not in only_cast:
                    continue
                self.px[q] = S.DARKER.get(k, k)
        for q in ring:
            if self.inb(q) and q[1] <= SOLE_Y:
                self.px[q] = 'k'
        for q, k in part.items():
            if self.inb(q):
                self.px[q] = k


#DORSAL PLATES

# the back ridge the plates grow from, tail tip -> nape
RIDGE = [(5, 149), (14, 155), (26, 158), (38, 156), (50, 150), (59, 141), (64, 129), (66, 116),
         (70, 103), (77, 91), (87, 82), (98, 75), (107, 70), (114, 66)]


def ridge_at(s):
    """Point and unit tangent at arc-length fraction s (0 tail tip .. 1 nape) along RIDGE."""
    segs = []
    tot = 0.0
    for a, b in zip(RIDGE, RIDGE[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        segs.append((a, b, L))
        tot += L
    d = s * tot
    for a, b, L in segs:
        if d <= L or (a, b, L) == segs[-1]:
            t = min(1.0, d / L)
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            return p, ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        d -= L
    raise AssertionError


# a jagged plate in local units: across (-0.5 .. 0.5 at the base), along (0 base .. 1 tip)
PLATE_BIG = [(-0.50, 0.00), (-0.44, 0.20), (-0.66, 0.34), (-0.36, 0.40), (-0.48, 0.62), (-0.18, 0.60),
             (0.00, 1.00), (0.15, 0.62), (0.40, 0.66), (0.24, 0.44), (0.54, 0.34), (0.38, 0.18),
             (0.50, 0.00)]
PLATE_MID = [(-0.50, 0.00), (-0.46, 0.30), (-0.64, 0.46), (-0.22, 0.56), (0.00, 1.00), (0.20, 0.58),
             (0.52, 0.44), (0.36, 0.24), (0.50, 0.00)]
PLATE_SMALL = [(-0.50, 0.00), (-0.40, 0.48), (0.00, 1.00), (0.34, 0.50), (0.50, 0.00)]


def plate_poly(base, direction, h, w):
    dx, dy = direction
    px, py = -dy, dx                       # across the plate (its left = the lit side)
    shape = PLATE_BIG if h >= 15 else (PLATE_MID if h >= 9 else PLATE_SMALL)
    return [(base[0] + px * a * w + dx * b * h, base[1] + py * a * w + dy * b * h) for (a, b) in shape]


# (s along the ridge, height, group). Groups light in order 0 (tail tip) .. 6 (nape): the countdown.
PLATES = [
    (0.030, 6.0, 0), (0.075, 7.5, 0), (0.125, 8.5, 0),
    (0.180, 9.5, 1), (0.235, 10.5, 1), (0.290, 12.0, 1),
    (0.345, 13.5, 2), (0.400, 15.5, 2),
    (0.455, 17.5, 3), (0.515, 20.0, 3),
    (0.580, 22.5, 4), (0.645, 24.0, 4),
    (0.715, 23.0, 5), (0.785, 20.5, 5),
    (0.850, 16.5, 6), (0.910, 12.5, 6), (0.960, 9.0, 6),
]
N_GROUPS = 7


def plate_dir(tg, lean=0.38):
    nx, ny = tg[1], -tg[0]                 # outward: left of travel (up / left)
    dx, dy = nx - tg[0] * lean, ny - tg[1] * lean
    ln = math.hypot(dx, dy)
    return dx / ln, dy / ln


def plate_part(pts, glow=0.0, dim=False):
    """Shade a plate. glow 0: bone, lit on its left face, dark on its right, a vein up the middle.
    glow 1: lit from inside, white-hot up the vein, cyan, blue at the rim. Between: the glow has
    risen that far up from the base, a bright leading edge on it."""
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
        across = (rx * -uy + ry * ux) / halfw          # < 0: the left, lit face
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
            if a < 0.13 and along < 0.7:
                k = '5'                                  # the vein
            elif across < 0:
                k = '7' if across < -0.6 else '6'
            else:
                k = '4' if across > 0.58 else '5'
            if along > 0.84:
                k = '7' if across < 0.25 else '6'
            if dim:
                k = {'7': '6', '6': '5', '5': '4', '4': '4'}[k]
            if glow > 0 and along <= glow + 0.14:
                k = 'I' if k in '45' else 'J'            # the glow's leading edge creeping up
        out[(x, y)] = k
    return out


def plates(group_glow, row='main'):
    """[(part, group)] for one row of plates, back to front. 'far': the far row, behind and between
    the main ones, smaller; 'main': the tall centre row on the silhouette."""
    parts = []
    for (s, size, g) in PLATES:
        glow = group_glow.get(g, 0.0)
        if row == 'far':
            p, tg = ridge_at(min(0.99, s + 0.028))
            d = plate_dir(tg, lean=0.2)
            base = (p[0] + 1.5 - d[0] * 1.0, p[1] - 1.5 - d[1] * 1.0)
            h, w = size * 0.72 + 1.5, size * 0.66 + 1.0
        else:
            p, tg = ridge_at(s)
            d = plate_dir(tg)
            base = (p[0] - d[0] * 2.5, p[1] - d[1] * 2.5)
            h, w = size + 2.5, size * 0.74 + 1.5
        parts.append((plate_part(plate_poly(base, d, h, w), glow, dim=(row == 'far')), g))
    return parts


#BODY PARTS (frame coordinates)

def tail_prims():
    return [Cap((70, 141), (47, 156), 15.0, 12.0), Cap((47, 156), (26, 162), 12.0, 8.0),
            Cap((26, 162), (11, 158), 8.0, 5.0), Cap((11, 158), (5, 149), 5.0, 2.6)]


def far_leg_prims():
    return [Ell(121, 139, 15, 16), Cap((123, 148), (125, 162), 10.5, 9.5)]


def far_foot_prims():
    return [Ell(126, 165.5, 15, 6.2), Ell(139, 167.5, 5, 4.2), Ell(145, 168.5, 3.8, 3.2)]


def far_arm_prims():
    return [Cap((128, 100), (140, 107), 6.0, 5.0), Cap((140, 107), (147, 103), 5.0, 4.4)]


def torso_prims():
    return [Ell(99, 128, 36, 29), Ell(103, 102, 30, 24),
            Cap((106, 92), (120, 80), 15.5, 13.0)]


def near_leg_prims():
    return [Ell(80, 138, 19, 18), Cap((75, 150), (71, 162), 12.0, 11.0)]


def near_foot_prims():
    return [Ell(70, 165.5, 19, 6.4), Ell(87, 167.0, 5.5, 4.6), Ell(94, 168.5, 4.2, 3.4)]


def near_arm_parts():
    """The near arm as separate keylined pieces, back to front: upper arm, forearm, palm, three
    fingers (each with a hooked bone claw). Raised in front of the chest, claws out."""
    upper = [Cap((86, 96), (92, 112), 7.6, 6.6)]
    fore = [Cap((92, 112), (109, 105), 7.0, 5.6)]
    palm = [Ell(112.5, 105, 5.2, 4.6)]
    fingers = [[Cap((115, 101.5), (120.5, 102.5), 2.3, 1.9)],
               [Cap((116, 105.5), (121.5, 107.5), 2.3, 1.9)],
               [Cap((114.5, 109), (118, 112.5), 2.3, 1.9)]]
    claw_tips = [(124.5, 104.5, 1, 0.6), (124.5, 110.5, 0.7, 1), (119.5, 116.5, 0.2, 1)]
    return upper, fore, palm, fingers, claw_tips


def far_arm_parts():
    upper = [Cap((128, 99), (139, 106), 6.0, 5.0)]
    fore = [Cap((139, 106), (146, 102), 5.0, 4.2)]
    fingers = [[Cap((148, 99.5), (152, 99.5), 1.9, 1.6)], [Cap((149, 103), (152.5, 104.5), 1.9, 1.6)]]
    claw_tips = [(155.5, 100.5, 1, 0.5), (155, 107.5, 0.6, 1)]
    return upper, fore, fingers, claw_tips


# vinyl gloss: crisp hand-placed highlight streaks (the toy's sheen), frame coordinates
GLOSS = [
    [(66, 128), (68, 125), (71, 123), (75, 122)],         # the near thigh
    [(67, 129), (69, 126)],
    [(84, 87), (87, 85), (91, 84)],                       # the shoulder
    [(85, 88), (88, 86)],
    [(80, 108), (82, 106)],                               # the flank
    [(124, 63), (129, 62)],                               # the skull
    [(156, 69), (159, 69)],                               # the snout
    [(37, 150), (41, 148), (44, 147)],                    # the tail
    [(88, 98), (89, 97)],                                 # the upper arm
]


def gloss(px):
    for pts in GLOSS:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for q in K.line(x0, y0, x1, y1):
                if px.get(q) in ('@', '+', '=', '&'):
                    px[q] = '~'


#THE HEAD: a traced silhouette, shaded with the normals of the forms under it

SKULL = [(113, 70), (117, 64), (125, 61), (135, 60), (141, 59), (147, 59), (151, 61), (153, 64),
         (155, 66), (160, 67), (165, 69), (167, 71), (167.5, 77), (166, 81), (152, 82.5), (145, 83.5),
         (139, 84.5), (134, 86.5), (130, 90), (124, 92), (117, 91), (113, 86), (111.5, 78)]
JAW = [(131, 87.5), (139, 85.5), (148, 84.5), (157, 83.5), (163, 83.5), (164.5, 86), (162.5, 90),
       (155, 93.5), (144, 96), (133, 96), (126, 93)]


def head_prims():
    return [Ell(128, 74, 16, 13),                             # the cranium
            Ell(145, 64.5, 8.5, 4.2, z=3.0),      # the brow ridge, jutting over the eye
            Cap((141, 74), (161, 75), 9.0, 6.6),              # the muzzle
            Ell(126, 83, 9.5, 7.0, z=1.0)]                    # the jaw muscle under the cheek


def head_fallback():
    return Ell(138, 76, 32, 22, z=-30)


def jaw_prims():
    return [Cap((130, 91), (159, 88.5), 6.0, 4.5)]


# the face, drawn over the shaded head (frame coordinates)
BROW_LINE = [(139, 65), (140, 65), (141, 65), (142, 66), (143, 66), (144, 66), (145, 66), (146, 67),
             (147, 67), (148, 67), (149, 67), (150, 68), (151, 68), (152, 68)]
EYE = {(142, 67): 'k', (143, 67): 'O', (144, 67): 'Y', (145, 67): 'k',
       (142, 68): 'k', (143, 68): 'G', (144, 68): 'O', (145, 68): 'k', (146, 68): 'O', (147, 68): 'O',
       (148, 68): 'O', (149, 68): 'G'}
EYE_LID = [(x, 69) for x in range(143, 151)]
NOSTRIL = [(161, 70), (162, 70), (162, 71)]
MOUTH_LINE = ([(x, 82) for x in range(152, 166)] + [(x, 83) for x in range(145, 152)] +
              [(x, 84) for x in range(139, 145)] + [(x, 85) for x in range(135, 139)] + [(133, 86), (134, 86)])


def head_part(charge=False):
    clip = K.poly(SKULL)
    part, info = S.shade_clip(head_prims(), clip, 'hide', head_fallback(), bias=0.04, flatten=0.85,
                              bounce=0.35)
    bumps(part, seed=17, step=4)
    S.rim_light(part)
    for q in BROW_LINE:
        part[q] = 'k'
        up = (q[0], q[1] - 1)                          # the brow's underside, in its own shadow
        if part.get(up) not in (None, 'k'):
            part[up] = '&' if part[up] in ('@', '+', '=', '~') else part[up]
    for q in BROW_LINE[3:]:
        up = (q[0], q[1] - 2)
        if part.get(up) in ('+', '=', '~'):
            part[up] = '@'
    part[(138, 64)] = 'k'
    for q, k in EYE.items():
        part[q] = k
    for q in EYE_LID:
        part[q] = 'k'
    for x in range(143, 152):                          # the socket under the eye
        if part.get((x, 70)) not in (None, 'k'):
            part[(x, 70)] = '%'
    for q in NOSTRIL:
        part[q] = 'k'
    part[(161, 71)] = '%'
    for q in MOUTH_LINE:
        if q in part:
            part[q] = 'k'
    for q in MOUTH_LINE:                               # the upper lip rolls under: a dark edge
        up = (q[0], q[1] - 1)
        if part.get(up) not in (None, 'k'):
            part[up] = '%'
    for q in ((119, 77), (120, 77), (119, 78)):        # the ear hole behind the jaw muscle
        part[q] = 'k'
    return part, info


def jaw_part(open_by=0):
    """The lower jaw. open_by drops its front (hinged at the back) to show the mouth."""
    pts = []
    for (x, y) in JAW:
        t = max(0.0, (x - 128) / 34.0)
        pts.append((x, y + open_by * t))
    clip = K.poly(pts)
    prims = [Cap((130, 91 + open_by * 0.1), (159, 88.5 + open_by * 0.9), 6.0, 4.5)]
    part, info = S.shade_clip(prims, clip, 'hide', Ell(146, 90 + open_by * 0.5, 24, 10, z=-20), bias=0.0,
                              bounce=0.3)
    bumps(part, seed=23, step=4)
    return part


# fangs: (x, top y, rows, width) hanging from the upper jaw over the lower lip, and pointing up from
# the lower jaw over the upper lip
UPPER_FANGS = [(162, 83, 3, 2), (157, 83, 2, 1), (151, 84, 3, 2), (145, 84, 2, 1), (140, 85, 2, 1)]
LOWER_FANGS = [(154, 81, 2, 1), (148, 82, 2, 1), (142, 83, 2, 1)]


def fang_pixels(x, y, n, w, up=False):
    """A bone fang with its own keyline: w (1 or 2) wide at the root, tapering to a point."""
    px = {}
    for i in range(n):
        yy = y - i if up else y + i
        ww = w if i < n - 1 else 1
        for j in range(ww):
            k = '7' if i == 0 else ('6' if i < n - 1 else '5')
            if j == 1:
                k = '5' if k != '7' else '6'
            px[(x + j, yy)] = k
    ring = {}
    for (fx, fy) in px:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (fx + dx, fy + dy)
            if q not in px:
                ring[q] = 'k'
    return px, ring


def mouth(cv, open_by=0, glow=False, jaw_px=None, head_px=None):
    """The closed snarl: fangs over the lips. Open (the breath charge): the gap between the jaws lit
    from the throat, white-hot at the back, cyan, blue at the lips; the lower lip and the fangs catch
    the light. Returns the effect pixels (none when closed)."""
    fx = set()
    if open_by:
        jaw_fill = {q for q, k in (jaw_px or {}).items() if k != 'k'}
        head_fill = {q for q, k in (head_px or {}).items() if k != 'k'}
        inside = set()
        for (x, y) in MOUTH_LINE:
            col = []
            yy = y + 1
            while yy < y + 14 and (x, yy) not in jaw_fill and (x, yy) not in head_fill:
                col.append((x, yy))
                yy += 1
            if (x, yy) in jaw_fill:                      # only where the dropped jaw closes the column
                inside.update(col)
        lips = set()
        for (x, y) in list(inside):
            if (x, y + 1) in jaw_fill:
                inside.discard((x, y))                   # the jaw's own keyline stays as the lip line
                lips.add((x, y + 1))
        ys = {}
        for (x, y) in inside:
            ys.setdefault(x, []).append(y)
        for (x, y) in inside:
            t = (x - 133) / 32.0
            col = ys[x]
            mid = (min(col) + max(col)) / 2.0
            depth = abs(y - mid) / max(1.0, (max(col) - min(col)) / 2.0 + 0.5)
            if glow:
                if depth < 0.45 and t < 0.75:
                    k = 'X'
                elif depth < 0.8:
                    k = 'K' if t < 0.85 else 'J'
                else:
                    k = 'J' if t < 0.6 else 'I'
            else:
                k = 'v'
            cv.px[(x, y)] = k
        if glow:
            for (x, y) in inside:                         # light escaping the open front: an effect
                if any(q not in cv.px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                    fx.add((x, y))
            for q in lips:                                # the lower lip lit from the throat
                cv.px[q] = 'I'
    for (x, y, n, w) in UPPER_FANGS:
        px, ring = fang_pixels(x, y, n, w)
        for q, k in ring.items():
            if q not in px and q[1] >= y and cv.px.get(q) not in ('X', 'K', 'J', 'I'):
                cv.px[q] = 'k'
        for q, k in px.items():
            cv.px[q] = k
    if not open_by:
        for (x, y, n, w) in LOWER_FANGS:
            px, ring = fang_pixels(x, y, n, w, up=True)
            for q, k in ring.items():
                if q not in px and q[1] <= y and cv.px.get(q) is not None:
                    cv.px[q] = 'k'
            for q, k in px.items():
                cv.px[q] = k
    if glow and open_by:
        # the glow spilling from the open mouth: a flare off the front, no keyline (an effect)
        flare = {(168, 84): 'K', (169, 84): 'J', (168, 85): 'X', (169, 85): 'K', (170, 85): 'J',
                 (171, 85): 'I', (168, 86): 'K', (169, 86): 'J', (168, 87): 'J', (172, 83): 'I',
                 (173, 87): 'J', (174, 84): 'K', (171, 81): 'J', (176, 86): 'I', (170, 89): 'I'}
        for q, k in flare.items():
            if q not in cv.px:
                cv.px[q] = k
                fx.add(q)
    return fx


def glow_halo(cv, lit_parts, seed=5):
    """Lit plates shine past their keyline: a 1px blue halo on the open side of each lit plate's
    outline, and a few white-cyan sparks off the tips. Effects, so no keyline. Returns their pixels."""
    fx = set()
    lit = set()
    for part in lit_parts:
        lit |= {q for q, k in part.items() if k in ('X', 'K', 'J', 'I')}
    ring = set()
    for (x, y) in lit:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ring.add((x + dx, y + dy))
    for (x, y) in ring:
        if cv.px.get((x, y)) != 'k':
            continue
        for dx, dy in ((-1, 0), (0, -1), (-1, -1), (1, -1)):
            q = (x + dx, y + dy)
            if q not in cv.px:
                h = (q[0] * 7349 + q[1] * 1931 + seed) % 7
                if h < 4:
                    cv.px[q] = 'I'
                    fx.add(q)
    return fx


def sparks(cv, points):
    """Tiny cross-shaped sparks (white centre, cyan arms) at the given points, where empty."""
    fx = set()
    for (x, y) in points:
        star = {(x, y): 'X', (x + 1, y): 'J', (x - 1, y): 'J', (x, y + 1): 'J', (x, y - 1): 'J'}
        if all(q not in cv.px for q in star):
            for q, k in star.items():
                cv.px[q] = k
                fx.add(q)
    return fx


def near_hand():
    """The near hand: three thick fingers curled forward, bone claws hooked down (frame coords)."""
    rows = [
        # x: 106-110 111-115 116-120 121-124
        ".kkkk kkk.. ..... ....",    # 103
        "k@++@ @@kk. ..... ....",    # 104
        "k++=+ @@@&k k.... ....",    # 105
        "k+=+@ @@&&k 7k... ....",    # 106
        "k+++@ @&&&k 67k.. ....",    # 107
        "k@+@@ &&&&k k57k. ....",    # 108
        "k@@@& &&%kk +kk5k ....",    # 109
        "k@@&& &%k@+ @&kk. ....",    # 110
        ".k&&% %k++@ &&k7k ....",    # 111
        ".k&%% k+@@& &%k67 k...",    # 112
        "..k%k k@@&& %%kk5 7k..",    # 113
        "..kk. .k&&% %k.kk 57k.",    # 114
        "..... ..k%% k...k 5k..",    # 115
        "..... ...kk 7k..k k...",    # 116
        "..... ....k 67k.. ....",    # 117
        "..... ....k 5k... ....",    # 118
        "..... .....k k... ....",    # 119
    ]
    return K.amap([r.replace(' ', '') for r in rows], 106, 103)


#SURFACE DETAIL

# where the belly scutes run: a band down the front, throat -> crotch: (centre polyline, half widths)
BELLY_LINE = [(126, 86), (127, 98), (125, 111), (120, 124), (114, 138), (108, 151)]
BELLY_HALF = [5.0, 8.0, 10.0, 11.0, 10.0, 7.0]


def _closest_on(line_pts, p):
    best = None
    acc = 0.0
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(line_pts, line_pts[1:]))
    for i, (a, b) in enumerate(zip(line_pts, line_pts[1:])):
        vx, vy = b[0] - a[0], b[1] - a[1]
        L2 = vx * vx + vy * vy
        L = math.sqrt(L2)
        t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
        cx, cy = a[0] + vx * t, a[1] + vy * t
        d = math.hypot(p[0] - cx, p[1] - cy)
        if best is None or d < best[0]:
            best = (d, (acc + t * L) / tot, i, t, (cx, cy))
        acc += L
    return best


def belly(part, info):
    """Recolour the front band of the torso as sand scutes, shaded by the same light, ridged every
    6px: a dark seam with a lit lip above it; a dark rim where the scutes meet the hide."""
    tot = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(BELLY_LINE, BELLY_LINE[1:]))
    region = {}
    for q in list(part):
        d, s, i, t, c = _closest_on(BELLY_LINE, q)
        hw = BELLY_HALF[i] * (1 - t) + BELLY_HALF[i + 1] * t
        if d <= hw:
            lam = info[q][0]
            idx = sum(1 for cut in (0.12, 0.42, 0.7) if lam + 0.08 >= cut)
            region[q] = (s * tot, d / hw)
            part[q] = S.BELLY[idx]
    for q, (along, rel) in region.items():
        a = along + rel * rel * 2.2
        if int(a) % 6 == 0 and rel < 0.98:
            part[q] = 'k'
        elif int(a) % 6 == 5 and rel < 0.9 and part[q] in ('E', 'F'):
            part[q] = S.LIGHTER[part[q]]
    edge = []
    for q in region:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            r = (q[0] + dx, q[1] + dy)
            if r in part and r not in region:
                edge.append(q)
                break
    for q in edge:
        part[q] = 'k'
    return region


def bumps(part, seed=7, step=5, keys=('@', '+', '&')):
    """The sculpted hide: small raised bumps on a jittered grid, each a lit pixel with a dark pixel
    under-right of it, kept off the edges."""
    xs = [x for (x, y) in part]
    ys = [y for (x, y) in part]
    for gy in range(min(ys), max(ys) + 1, step):
        for gx in range(min(xs), max(xs) + 1, step):
            h = (gx * 73856093 ^ gy * 19349663 ^ seed * 83492791) & 0xFFFF
            x = gx + (h % 3) - 1 + ((gy // step) % 2) * 2
            y = gy + ((h >> 4) % 3) - 1
            q = (x, y)
            if part.get(q) not in keys:
                continue
            if not all((x + dx, y + dy) in part for dx in (-2, -1, 0, 1, 2) for dy in (-2, -1, 0, 1, 2)):
                continue
            part[q] = S.LIGHTER[part[q]]
            r = (x + 1, y + 1)
            if part.get(r) in S.DARKER:
                part[r] = S.DARKER[part[r]]


def seam(part, pts, dark='k', lit='='):
    """A toy's articulation cut round a limb: a dark line with a lit bevel above-left of it."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in K.line(x0, y0, x1, y1):
            if (x, y) in part:
                part[(x, y)] = dark
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for (x, y) in K.line(x0, y0, x1, y1):
            q = (x, y - 1)
            if q in part and part[q] not in ('k', dark):
                part[q] = lit if part[q] in ('@', '+', '&', '%', '=') else part[q]


def claws(points, size=3):
    """Bone claws: small hooked triangles, (tip x, tip y, dx, dy) pointing along (dx, dy)."""
    out = {}
    for (tx, ty, dx, dy) in points:
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px, py = -uy, ux
        base = (tx - ux * size, ty - uy * size)
        pts = [(base[0] + px * 1.3, base[1] + py * 1.3), (tx, ty), (base[0] - px * 1.3, base[1] - py * 1.3)]
        shape = K.poly(pts)
        for q in shape:
            out[q] = '6'
        for q in shape:
            if (q[0] - 1, q[1]) not in shape or (q[0], q[1] - 1) not in shape:
                out[q] = '7'
            if (q[0] + 1, q[1]) not in shape and (q[0], q[1] + 1) not in shape:
                out[q] = '5'
    return out


# a knee's crease: a short dark fold behind the joint (frame coordinates)
KNEE_CREASES = [[(61, 150), (63, 153), (66, 155)], [(108, 149), (110, 151)]]

# the toy's maker mark: the chase edition's gold star, embossed on the near heel
STAR_MARK = {(55, 162): 'O', (53, 163): 'O', (54, 163): 'O', (55, 163): 'Y', (56, 163): 'O', (57, 163): 'O',
             (54, 164): 'O', (55, 164): 'O', (56, 164): 'G', (54, 165): 'G', (56, 165): 'G'}


def creases(px):
    for pts in KNEE_CREASES:
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            for q in K.line(x0, y0, x1, y1):
                if px.get(q) not in (None, 'k'):
                    px[q] = 'k'


def star_mark(px):
    for q, k in STAR_MARK.items():
        if px.get(q) not in (None, 'k'):
            px[q] = k


def close_holes(px):
    """Pinholes (a transparent pixel boxed in on four sides) take the halo's blue if they sit in it,
    otherwise the keyline. Returns the ones filled with blue (effect pixels)."""
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
