"""The three heads, from one design.

Every head part is authored in "head space": the middle head's own frame-0 pixel coordinates (so the
numbers are the ones tuned on the middle head), plus a depth z per vertex (ears behind the skull,
muzzle and nose forward). Xf projects head space onto the frame: a turn about the vertical axis
(phi, which slides forward things sideways and so gives the side heads their 3/4 view), a scale, a
tilt and a position. The middle head is the identity. The left head is the right head mirrored.

Stamp order (back to front): ears, crest, mouth, lower fangs, jaw, tongue, upper fangs, cheek tufts,
skull with the muzzle and blaze, nose, brows, eyes. The fangs go under the lips so they hang out of
the mouth rather than sitting on the muzzle.
"""
import math

from pal import AX, fill, poly
from shapes import edge, poly_line, recolor

HX, HY = 95.5, 40.0          # head-space origin (the middle head's centre line, eye level)


class Xf:
    def __init__(self, cx=HX, cy=HY, phi=0.0, s=1.0, theta=0.0):
        self.cx, self.cy, self.s = cx, cy, s
        self.cp, self.sp = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        self.ct, self.st = math.cos(math.radians(theta)), math.sin(math.radians(theta))

    def p(self, x, y, z=0.0):
        lx, ly = x - HX, y - HY
        x1 = lx * self.cp + z * self.sp
        x2, y2 = self.s * x1, self.s * ly
        return (self.cx + x2 * self.ct - y2 * self.st, self.cy + x2 * self.st + y2 * self.ct)

    def inv(self, X, Y, z=0.0):
        """Screen pixel back to head space, for a surface at depth z."""
        x3, y3 = X - self.cx, Y - self.cy
        x2 = x3 * self.ct + y3 * self.st
        y2 = -x3 * self.st + y3 * self.ct
        x1, ly = x2 / self.s, y2 / self.s
        lx = (x1 - z * self.sp) / self.cp
        return (lx + HX, ly + HY)

    def poly(self, pts, z=0.0):
        """Rasterise a head-space polygon; vertices are (x, y) or (x, y, z)."""
        return poly([self.p(*v) if len(v) == 3 else self.p(v[0], v[1], z) for v in pts])

    def line(self, pts, z=0.0):
        q = [self.p(*v) if len(v) == 3 else self.p(v[0], v[1], z) for v in pts]
        return poly_line(q)


def mirror_pts(pts):
    return [(2 * HX - v[0],) + tuple(v[1:]) for v in pts]


def half(pts):
    """Full symmetric polygon from its right half (top centre first, bottom centre last)."""
    return list(pts) + mirror_pts(list(reversed(pts)))


def both_sides(pts):
    return [list(pts), mirror_pts(pts)]


def head_y(xf, part, z):
    """Head-space y of each pixel of a part (for plane thresholds)."""
    return {p: xf.inv(p[0], p[1], z)[1] for p in part}


#PARTS

def ear(xf, side=1):
    pts = [(113, 18), (119, 17), (123, 20), (126, 27), (128, 36), (129, 46), (130, 58), (131, 66),
           (133, 72), (133, 81), (129, 76), (127, 89), (124, 78), (121, 85), (119, 73), (118, 62),
           (117, 50), (116, 36), (115, 26)]
    fold = [(122, 26), (123, 40), (124, 56), (124, 66)]
    if side < 0:
        pts, fold = mirror_pts(pts), mirror_pts(fold)
    z = -4
    e = fill(xf.poly(pts, z), 'r')
    out_dx = 1 if side > 0 else -1
    hy = head_y(xf, e, z)
    # the lit leather of the ear, a band down its front; the rest falls into shadow
    for p in list(e):
        hx_ = xf.inv(p[0], p[1], z)[0]
        dist = abs(hx_ - HX)
        if dist < 126 - HX and hy[p] < 62:
            e[p] = 's'
    recolor(e, edge(e, out_dx, 0, 2), 'q')           # darker outer edge, like the real ears
    recolor(e, edge(e, -out_dx, 0, 1), 'q')          # tucked behind the cheek
    top = {p for p in e if hy[p] <= 24}
    recolor(e, top, 't')
    recolor(e, edge(e, 0, -1, 1) & top, 'u')
    for p in xf.line(fold, z):
        if p in e:
            e[p] = 'q'
    # Hades' violet rim light down the shadowed outer edge
    for p in edge(e, out_dx, 0, 1):
        if 40 <= hy[p] <= 64:
            e[p] = 'e'
    # a hard black crease where the ear folds over at the top, and one down its outer lobe
    crease = [(121, 24), (122, 36)]
    lobe = [(126, 46), (127, 58)]
    if side < 0:
        crease, lobe = mirror_pts(crease), mirror_pts(lobe)
    for seg in (crease, lobe):
        for p in xf.line(seg, z):
            if p in e:
                e[p] = 'k'
    # the ragged bottom burns: ember up the tips, yellow at their points
    for p in list(e):
        yy = hy[p]
        if yy >= 71:
            e[p] = 'u' if yy < 77 else ('v' if yy < 82 else 'P')
        elif yy >= 67:
            e[p] = 't' if e[p] not in 'qke' else 's'
    return e


def crest(xf):
    pts = half([(95.5, 1), (97, 6), (99, 11), (101, 8), (105, 3), (104, 8), (104, 12), (108, 10),
                (114, 6), (111, 12), (110, 15), (116, 13), (122, 11), (117, 17), (117, 22), (95.5, 22)])
    c = fill(xf.poly(pts, -2), 's')
    recolor(c, edge(c, -1, 0, 1), 't')
    recolor(c, edge(c, 0, -1, 1), 't')
    # black cuts parting the flames at their roots
    for seg in ([(100, 11), (101, 16)], [(107, 12), (107, 17)], [(113, 15), (112, 19)]):
        for s in both_sides(seg):
            for p in xf.line(s, -2):
                if p in c:
                    c[p] = 'k'
    return c


# the skull outline; its lower edge is the upper lip, which sits forward on the muzzle
SKULL = half([(95.5, 13, 2), (103, 14, 1), (110, 17, 0), (115, 21, 0), (118, 27, 0), (119, 34, 0),
              (118, 40, 1), (122, 45, 0), (117, 46, 1), (121, 51, 0), (115, 51, 2), (117, 57, 2),
              (111, 57, 8), (108, 55, 10), (104, 56, 12), (100, 56, 13), (95.5, 57, 14)])
# the muzzle as a solid, so a turned head's snout sticks out past its skull
SNOUT = half([(95.5, 33, 9), (98, 33, 9), (100, 36, 10), (103, 41, 12), (106, 46, 12), (108, 51, 12),
              (109, 56, 11), (95.5, 57, 15)])
BLAZE = half([(95.5, 13, 3), (100, 13, 3), (99, 17, 4), (98, 21, 5), (98, 34, 8), (95.5, 34, 8)])
MUZZLE = half([(95.5, 33, 9), (98, 33, 9), (100, 36, 10), (103, 41, 12), (106, 46, 12), (108, 51, 12),
               (109, 56, 11), (95.5, 56, 15)])
MUZZLE_SIDE = [(100, 38, 10), (103, 41, 12), (106, 46, 12), (108, 51, 12), (109, 56, 11), (104, 56, 13),
               (103, 50, 13), (101, 44, 12)]
MUZZLE_TOP = half([(95.5, 13, 3), (99, 13, 3), (98, 17, 4), (97, 22, 5), (97, 36, 9), (95.5, 38, 10)])
CHEEK = [(109, 37, 4), (114, 34, 3), (117, 37, 2), (115, 40, 2), (112, 39, 3)]
# Hades-style hard shadow cuts: the skull's flank behind the eye, and the cheek under the tan patch
FLANK = [(113, 24, 0), (119, 28, 0), (120, 44, 0), (116, 40, 1), (114, 33, 1)]
UNDER_CHEEK = [(104, 44, 6), (112, 41, 3), (118, 42, 1), (121, 47, 0), (116, 52, 1), (108, 53, 6)]
SOCKET = [(100, 34, 6), (106, 34, 5), (113, 30, 4), (114, 33, 4), (107, 37, 5), (101, 37, 6)]


def skull(xf):
    head = fill(xf.poly(SKULL) | xf.poly(SNOUT), 't')
    hy = head_y(xf, head, 2)
    for p in list(head):
        if hy[p] >= 44:
            head[p] = 's'
    for s in both_sides(FLANK):
        for p in xf.poly(s):
            if p in head:
                head[p] = 's'
    for s in both_sides(UNDER_CHEEK):
        for p in xf.poly(s):
            if p in head:
                head[p] = 'r'
    for s in both_sides(SOCKET):
        for p in xf.poly(s):
            if p in head:
                head[p] = 's'
    recolor(head, edge(head, 0, 1, 2), 'r')
    recolor(head, edge(head, 0, 1, 1), 'q')
    recolor(head, edge(head, 1, 0, 1) | edge(head, -1, 0, 1), 'r', only='st')
    for s in both_sides(CHEEK):
        for p in xf.poly(s):
            if p in head and head[p] in 'ts':
                head[p] = 'u'
    # hard black cuts under the cheekbones (the Hades codex's slivers of shadow)
    for seg in ([(111, 45, 3), (117, 50, 1)], [(104, 48, 8), (108, 54, 8)]):
        for s in both_sides(seg):
            for p in xf.line(s):
                if p in head and head[p] in 'rs':
                    head[p] = 'k'
    for p in xf.poly(BLAZE) | xf.poly(MUZZLE):
        if p in head:
            head[p] = 'x'
    for s in both_sides(MUZZLE_SIDE):
        for p in xf.poly(s):
            if p in head and head[p] == 'x':
                head[p] = 'y'
    for p in xf.poly(MUZZLE_TOP):
        if p in head and head[p] == 'x':
            head[p] = 'w'
    return head


def ruff(xf):
    """Jowls and throat ruff behind the jaw: fills the head down to the collar, ear to ear, and spikes
    down over the collar."""
    pts = half([(95.5, 50, 4), (113, 50, 2), (118, 56, 0), (119, 66, 0), (118, 76, 0), (119, 84, 0),
                (114, 80, 1), (111, 87, 2), (107, 81, 3), (95.5, 84, 6)])
    r = fill(xf.poly(pts), 's')
    recolor(r, edge(r, 0, 1, 2), 'r')
    recolor(r, edge(r, 1, 0, 1) | edge(r, -1, 0, 1), 'r')
    # black cuts raking down through the jowl fur into each spike
    for seg in ([(115, 66, 0), (117, 78, 0)], [(110, 74, 3), (111, 83, 2)]):
        for s in both_sides(seg):
            for p in xf.line(s):
                if p in r:
                    r[p] = 'k'
    return r


MOUTH = half([(95.5, 54, 12), (104, 54, 11), (110, 56, 8), (113, 61, 5), (112, 68, 5), (106, 73, 8),
              (95.5, 75, 10)])
THROAT = half([(95.5, 58, 8), (101, 58, 8), (104, 63, 7), (101, 68, 7), (95.5, 69, 8)])


def mouth(xf):
    m = fill(xf.poly(MOUTH), 'q')
    for p in xf.poly(THROAT):
        m[p] = 'k'
    return m


JAW = half([(95.5, 72, 11), (103, 71, 10), (109, 67, 7), (113, 62, 4), (114, 68, 4), (111, 75, 6),
            (106, 80, 8), (102, 83, 9), (99, 83, 10), (97, 87, 10), (95.5, 85, 10)])
JAW_CORNER = half([(95.5, 60, 6), (113, 60, 4), (116, 66, 4), (112, 76, 5), (108, 72, 6), (110, 66, 6)])


def jaw(xf):
    j = fill(xf.poly(JAW), 'x')
    recolor(j, edge(j, 0, 1, 2), 'y')
    recolor(j, edge(j, 0, -1, 1), 'w', only='x')
    for p in xf.poly(JAW_CORNER):
        if p in j:
            hx_ = xf.inv(p[0], p[1], 5)[0]
            if abs(hx_ - HX) > 11:
                j[p] = 's'
    return j


def nose(xf):
    pts = half([(95.5, 43), (99, 43), (102, 45), (103, 48), (101, 50), (98, 50), (95.5, 51)])
    n = fill(xf.poly(pts, 15), 'a')
    recolor(n, edge(n, 0, -1, 1), 'c')
    hi = [(97, 44), (98, 44), (99, 45)]
    nostrils = [(100, 48), (101, 48), (100, 49)]
    for group, key in ((hi, 'd'), (nostrils + mirror_pts(nostrils), 'k')):
        for v in group:
            q = tuple(int(round(c)) for c in xf.p(v[0], v[1], 15))
            if q in n:
                n[q] = key
    return n


def brow(xf, side=1):
    pts = [(98, 32), (101, 29), (106, 26), (112, 23), (117, 21), (116, 24), (111, 27), (105, 30), (100, 33)]
    ridge = [(100, 28), (106, 25), (112, 22), (115, 20)]
    if side < 0:
        pts, ridge = mirror_pts(pts), mirror_pts(ridge)
    b = fill(xf.poly(pts, 7), 'k')
    lit = {p: 'u' for p in xf.line(ridge, 7)}
    return b, lit


def eye(xf, side=1):
    pts = [(101, 34), (105, 32), (110, 29), (113, 28), (112, 31), (107, 34), (103, 35)]
    pupil = [(104, 33), (105, 33), (104, 34)]
    glint = [(108, 31)]
    if side < 0:
        pts, pupil, glint = mirror_pts(pts), mirror_pts(pupil), mirror_pts(glint)
    e = fill(xf.poly(pts, 6), 'i')
    recolor(e, edge(e, 0, -1, 1), 'h')
    recolor(e, edge(e, 0, 1, 1), 'j', only='i')
    for group, key in ((pupil, 'k'), (glint, 'W')):
        for v in group:
            q = tuple(int(round(c)) for c in xf.p(v[0], v[1], 6))
            if q in e:
                e[q] = key
    return e


def fang(xf, pts, z):
    f = fill(xf.poly(pts, z), 'x')
    recolor(f, edge(f, -1, 0, 1), 'w')
    recolor(f, edge(f, 1, 0, 1), 'y')
    return f


UPPER_FANG = [(102, 54), (106, 54), (105, 60), (104, 65), (103, 65), (102, 60)]
LOWER_FANG = [(105, 71), (108, 70), (108, 66), (107, 62)]


def tongue(xf, flip=False):
    pts = [(86, 62), (94, 62), (95, 70), (94, 78), (92, 86), (89, 93), (85, 94), (82, 90), (82, 81), (84, 72)]
    groove = [(89, 70), (88, 80), (87, 88)]
    shine = [(85, 76), (85, 77), (86, 82)]
    if flip:
        pts, groove, shine = mirror_pts(pts), mirror_pts(groove), mirror_pts(shine)
    t = fill(xf.poly(pts, 12), 'N')
    recolor(t, edge(t, -1, 0, 1), 'p')
    recolor(t, edge(t, 1, 0, 1), 'n')
    recolor(t, edge(t, 0, 1, 1), 'n')
    for p in xf.line(groove, 12):
        if p in t:
            t[p] = 'n'
    for v in shine:
        q = tuple(int(round(c)) for c in xf.p(v[0], v[1], 12))
        if q in t:
            t[q] = 'P'
    return t


#COLLAR (the approved red collar, restyled with gold spikes) and HEADBAND (Liam's), in head space

COLLAR = half([(95.5, 86), (104, 85), (112, 82), (120, 78), (122, 84), (115, 91), (104, 96), (95.5, 97)])
COLLAR_SPIKES = [[(98, 96), (102, 95), (100, 102)], [(106, 94), (110, 92), (110, 99)],
                 [(114, 90), (118, 87), (120, 94)]]
COLLAR_STUDS = [(100, 91), (108, 89), (115, 85), (104, 90)]


def collar(xf):
    band = fill(xf.poly(COLLAR), 'L')
    recolor(band, edge(band, 0, -1, 2), 'm')
    recolor(band, edge(band, 0, -1, 1), 'M')
    recolor(band, edge(band, 0, 1, 1), 'l')
    for v in COLLAR_STUDS + mirror_pts(COLLAR_STUDS):
        q = tuple(int(round(c)) for c in xf.p(*v))
        if q in band:
            band[q] = 'O'
            below = (q[0], q[1] + 1)
            if below in band:
                band[below] = 'G'
    spikes = []
    for tri in COLLAR_SPIKES:
        for t in both_sides(tri):
            sp = fill(xf.poly(t), 'o')
            recolor(sp, edge(sp, -1, 0, 1), 'O')
            recolor(sp, edge(sp, 1, 0, 1), 'G')
            recolor(sp, edge(sp, 0, -1, 1) & edge(sp, 1, 0, 1), 'g')
            spikes.append(sp)
    return band, spikes


def headband(xf):
    """Worn high on the skull's curve, so the crest flames rise above the plate."""
    band = fill(xf.poly([(74, 18), (80, 14), (88, 11), (95.5, 10), (103, 11), (111, 14), (117, 18),
                         (117, 22), (111, 18), (103, 15), (95.5, 14), (88, 15), (80, 18), (74, 22)]), 'T')
    recolor(band, edge(band, 0, -1, 1), 'U')
    recolor(band, edge(band, 0, 1, 1), 'S')
    plate = fill(xf.poly([(86, 9), (105, 9), (105, 17), (86, 17)]), 'U')
    recolor(plate, edge(plate, 0, -1, 1), 'W')
    recolor(plate, edge(plate, -1, 0, 1), 'W')
    recolor(plate, edge(plate, 1, 0, 1), 'T')
    recolor(plate, edge(plate, 0, 1, 1), 'T')
    for q in xf.line([(91, 11), (94, 14)]):
        if q in plate:
            plate[q] = 'T'
    return band, plate


def headband_tails(xf, wave=0):
    from shapes import chain
    tails = []
    # streaming out to the right, level, across the wing's upper panel (clear of the wrist)
    for path, r in (([(116, 18), (125, 16), (134, 19), (143, 17), (152, 21), (161, 19), (168, 23)], 1.3),
                    ([(116, 20), (124, 22), (133, 25), (142, 24), (150, 28), (158, 27), (164, 31)], 1.1)):
        pts = []
        for i, (x, y) in enumerate(path):
            pts.append(xf.p(x, y + (wave * (1 if i % 2 else -1) if i > 1 else 0), -2))
        t = fill(chain(pts, r, r * 0.8), 'T')
        recolor(t, edge(t, 0, -1, 1), 'U')
        recolor(t, edge(t, 0, 1, 1), 'S')
        tails.append(t)
    return tails


DARKER = {'u': 't', 't': 's', 's': 'r', 'r': 'q'}


def build_dark(cv, xf, tongue_flip=False, with_collar=True):
    """A head set further back: its red fur one step darker, whites, eyes and tongue untouched."""
    tmp = type(cv)()
    build(tmp, xf, tongue_flip, with_collar)
    for p, k in tmp.px.items():
        cv.px[p] = DARKER.get(k, k)


def build(cv, xf, tongue_flip=False, with_collar=True, with_headband=False, features=True, low=None,
          brows=None):
    """Stamp one head. With features=False the mouth, jaw, fangs, tongue and eyes are left for
    hand-drawn maps; the brows follow `features` unless `brows` says otherwise (the middle head's
    hand-drawn eyes sit under procedural brows; the side heads' maps carry their own). `low` is an
    optional separate transform for the collar and ruff (a head thrown back with its jaw dropped keeps
    its collar where the neck is). Returns nothing."""
    low = low or xf
    if brows is None:
        brows = features
    cv.stamp(ear(xf, 1))
    cv.stamp(ear(xf, -1))
    cv.stamp(crest(xf))
    if with_collar:
        band, spikes = collar(low)
        for sp in spikes:
            cv.stamp(sp)
        cv.stamp(band)
    cv.stamp(ruff(low))
    if features:
        cv.stamp(mouth(xf))
        for s in both_sides(LOWER_FANG):
            cv.stamp(fang(xf, s, 10))
        cv.stamp(jaw(xf))
        cv.stamp(tongue(xf, tongue_flip))
        for s in both_sides(UPPER_FANG):
            cv.stamp(fang(xf, s, 12))
    cv.stamp(skull(xf))
    cv.stamp(nose(xf))
    if brows:
        for side in (1, -1):
            b, lit = brow(xf, side)
            cv.stamp(b, outline=False)
            cv.stamp(lit, outline=False)
    if features:
        for side in (1, -1):
            cv.stamp(eye(xf, side))
    if with_headband:
        band, plate = headband(xf)
        cv.stamp(band)
        cv.stamp(plate)
