"""Bixby's heads in profile, for the Flyby (drawn facing right; the engine mirrors for flying left).

The approved heads (art_source/bixby_redesign/heads.py) are hanging-eared ovals drawn to face the
camera; turned past about 55 degrees they collapse, and in any three-quarter view the far ear hangs
beside the mouth. The Flyby's lead mouth has to be the front of him below the floor line, so these
heads are drawn in profile: the original Bixby's side heads (Assets/Characters/Bixby/bixby.png) are
beagle profiles, and this is that profile in the approved Hades look. Every colour, shading rule and
feature is the approved head's (heads.py): blood-red fur t/s/r with the ember cheek u, the bone blaze
running into the bone muzzle, black nose, mint eye under a heavy black brow lit in ember, the crest of
flames, the long ear with black cuts, a violet rim and a burning ragged hem, the jowl ruff, the wine
collar with gold spikes, and on the middle head Liam's steel headband and its two tails.

A head is authored in local units: u runs forward along the snout, v runs down, the origin is the
eye. HX pitches it (snout down for pitch > 0), scales it and places it.
"""
import fb_common  # noqa: F401  (puts the rig on sys.path, read-only)
import math

from pal import fill, poly
from shapes import capsule, chain, edge, poly_line, recolor


class HX:
    def __init__(self, ox, oy, pitch=0.0, s=1.0):
        a = math.radians(pitch)
        self.ox, self.oy, self.s = ox, oy, s
        self.c, self.sn = math.cos(a), math.sin(a)

    def p(self, u, v):
        return (self.ox + self.s * (u * self.c - v * self.sn), self.oy + self.s * (u * self.sn + v * self.c))

    def ip(self, u, v):
        x, y = self.p(u, v)
        return (int(round(x)), int(round(y)))

    def inv(self, x, y):
        dx, dy = (x - self.ox) / self.s, (y - self.oy) / self.s
        return (dx * self.c + dy * self.sn, -dx * self.sn + dy * self.c)

    def poly(self, pts):
        return poly([self.p(u, v) for (u, v) in pts])

    def line(self, pts):
        return poly_line([self.p(u, v) for (u, v) in pts])

    def cap(self, a, b, r0, r1):
        return capsule(self.p(*a), self.p(*b), r0 * self.s, r1 * self.s)


def local(part, xf):
    """{pixel: (u, v)} for a part, so it can be shaded by where it is on the head."""
    return {q: xf.inv(q[0], q[1]) for q in part}


def cut(part, xf, segs, only=None):
    for seg in segs:
        for q in xf.line(seg):
            if q in part and (only is None or part[q] in only):
                part[q] = 'k'


#CREST: the fan of flames over the forehead, seen from the side: tallest at the brow, swept back

CREST = [(3, -10), (3, -13.5), (1.5, -18), (-0.5, -14), (-3.5, -18.5), (-5.5, -14.8), (-9, -18),
         (-10.5, -14), (-13.5, -15), (-13, -9.5), (-10, -9), (0, -9)]


def crest(xf):
    c = fill(xf.poly(CREST), 's')
    loc = local(c, xf)
    recolor(c, edge(c, 1, 0, 1), 't')
    recolor(c, edge(c, 0, -1, 1), 't')
    for q, (u, v) in loc.items():
        if v < -16.5:
            c[q] = 'u'                            # the tips catch the ember
    cut(c, xf, [[(-0.5, -14), (-1, -11.5)], [(-5.5, -14.8), (-6, -12.5)], [(-10.5, -14), (-11, -11.5)]])
    return c


#SKULL: cranium, blaze and muzzle as one solid; its lower edge is the upper lip

SKULL = [(6, -7), (11, -6.5), (16, -6), (19, -3.5), (19.5, 0.5), (19, 3), (17, 5), (12, 6.5), (6, 6.5),
         (1, 6), (-5, 7), (-11, 6.5), (-13.5, 3), (-15, -3), (-13.5, -8.5), (-10, -12.5), (-4, -13.5),
         (1, -12), (4, -9.5)]
BLAZE = [(-5, -13.8), (-1, -13), (2.5, -11), (5, -8), (7, -6.8), (12, -6.6), (16, -6.2), (16, -4.3),
         (12, -4.6), (6.5, -5), (3.5, -6.5), (1, -9.5), (-2, -11.5), (-5, -12)]
MUZZLE = [(9, -6.2), (16, -5.5), (19, -3), (19.5, 0.5), (19, 3), (17, 5), (12, 6.5), (6, 6.5), (6.5, 2.5),
          (8, -2)]
MUZZLE_SHADE = [(6, 0.5), (11, 0), (16, -0.5), (19.5, 0.8), (19, 3), (17, 5), (12, 6.5), (6, 6.5)]
CHEEK = [(-9, -0.5), (-4, -1.5), (1, 0), (-1, 3), (-7, 3.5)]
UNDER_CHEEK = [(-14, 2), (-7, 4), (0, 4.5), (1, 6), (-5, 7), (-11, 6.5)]
SOCKET = [(-4, -3.5), (0, -6), (6, -6), (7.5, -3), (3, -0.5), (-2, -0.5)]


def skull(xf):
    head = fill(xf.poly(SKULL), 't')
    loc = local(head, xf)
    for q, (u, v) in loc.items():
        if v >= 2.5:
            head[q] = 's'
        elif u < -11 and v > -7:                  # the back of the skull, turned from the light
            head[q] = 's'
    for q in xf.poly(UNDER_CHEEK):
        if q in head:
            head[q] = 'r'
    for q in xf.poly(SOCKET):
        if q in head:
            head[q] = 's'
    recolor(head, edge(head, 0, 1, 1), 'r')
    recolor(head, edge(head, -1, 0, 1), 'r', only='st')
    for q in xf.poly(CHEEK):
        if q in head and head[q] in 'ts':
            head[q] = 'u'
    for q in edge(head, 0, -1, 1):                # the dome's lit top
        if q in head and head[q] == 't':
            head[q] = 'u'
    # hard black slivers under the cheekbone and behind the eye (the Hades codex's cuts)
    cut(head, xf, [[(-12, 1.5), (-4, 4.5)], [(-14, -5), (-15.5, 1)], [(-9, -9), (-11, -4)]], only='rstu')
    for q in xf.poly(BLAZE) | xf.poly(MUZZLE):
        if q in head:
            head[q] = 'x'
    for q in xf.poly(MUZZLE_SHADE):
        if q in head and head[q] == 'x':
            head[q] = 'y'
    for q in edge(head, 0, -1, 1) | edge(head, 1, 0, 1):
        if q in head and head[q] == 'x':          # the lit ridge of the blaze and the bridge
            head[q] = 'w'
    for q in edge(head, 0, 1, 1):
        if q in head and head[q] == 'y':
            head[q] = 'z'
    return head


def nose(xf):
    n = fill(xf.poly([(15.5, -6), (18.5, -7), (21, -5.5), (21.8, -2.5), (21, 0.5), (18.5, 1), (16, -1.5)]), 'a')
    recolor(n, edge(n, 0, -1, 1), 'c')
    for (u, v), k in (((18.5, -5.5), 'd'), ((19.5, -5.5), 'd'), ((20.5, -0.5), 'k'), ((19.5, 0), 'k')):
        q = xf.ip(u, v)
        if q in n:
            n[q] = k
    return n


def brow(xf):
    b = fill(xf.poly([(-5, -2.8), (-1.5, -6), (3, -7.6), (8, -7.4), (8.3, -6.2), (3.5, -5.6), (-0.5, -4.2),
                      (-4, -1.8)]), 'k')
    lit = {q: 'u' for q in xf.line([(-3.5, -5.2), (0, -7.4), (4.5, -8.6), (7.8, -8.4)])}
    return b, lit


def eye(xf):
    e = fill(xf.poly([(-3.5, -1.5), (-0.5, -4), (4, -5), (7, -4), (5.5, -1.5), (1, -0.5)]), 'i')
    recolor(e, edge(e, 0, -1, 1), 'h')
    recolor(e, edge(e, 0, 1, 1), 'j', only='i')
    for (u, v), k in (((4.5, -3.2), 'k'), ((5.5, -3), 'k'), ((1, -2.5), 'W')):
        q = xf.ip(u, v)
        if q in e:
            e[q] = k
    return e


#JAW, MAW, FANGS, TONGUE

JAW_HINGE = (-4, 6)


def swing(pts, jaw):
    """Jaw points rotated about the hinge by `jaw` degrees (positive drops it open)."""
    a = math.radians(jaw)
    c, s = math.cos(a), math.sin(a)
    hx, hy = JAW_HINGE
    return [(hx + (u - hx) * c - (v - hy) * s, hy + (u - hx) * s + (v - hy) * c) for (u, v) in pts]


JAW = [(-6, 6), (2, 6), (9, 6.2), (15, 6.3), (17.5, 7), (16.5, 9.3), (12, 10.5), (5, 11), (-1, 10.5),
       (-6, 9)]
LOWER_FANG = [(13, 6.8), (15.5, 6.8), (14.8, 3.2)]
UPPER_FANG = [(10.5, 5.5), (13.5, 5.5), (12, 10.8)]
INCISORS = [(15.5, 5.2), (17.8, 4.8), (17.5, 6.2), (15.5, 6.2)]


def jaw(xf, open_deg=0.0):
    j = fill(xf.poly(swing(JAW, open_deg)), 'x')
    recolor(j, edge(j, 0, 1, 2), 'y')
    recolor(j, edge(j, 0, 1, 1), 'z')
    recolor(j, edge(j, 0, -1, 1), 'w', only='x')
    for q, (u, v) in local(j, xf).items():        # the jaw's corner is fur, not bone
        if u < 0 and (u - JAW_HINGE[0]) < 4:
            j[q] = 's'
    return j


def lower_fang(xf, open_deg=0.0):
    f = fill(xf.poly(swing(LOWER_FANG, open_deg)), 'x')
    recolor(f, edge(f, 1, 0, 1), 'w')
    recolor(f, edge(f, -1, 0, 1), 'y')
    return f


def upper_fang(xf):
    f = fill(xf.poly(UPPER_FANG), 'x')
    recolor(f, edge(f, 1, 0, 1), 'w')
    recolor(f, edge(f, -1, 0, 1), 'y')
    return f


def maw(xf, open_deg):
    """The open mouth: dark gum between the jaws, the black of the throat at its back."""
    upper = [(17.5, 5.5), (12, 6), (5, 6), (-2, 6.2)]
    lower = swing([(-2, 6.8), (5, 6.8), (12, 6.8), (17, 7)], open_deg)
    m = fill(xf.poly([(-4.5, 6)] + lower + upper), 'q')
    back = [(-4.5, 6), (2, 6.2)] + swing([(4, 7.5), (-1, 7.2)], open_deg)
    for q in xf.poly(back):
        m[q] = 'k'
    return m


def throat_glow(xf, open_deg, hot=True):
    """Fire in the maw: white-hot at the throat, cooling to orange at the lips."""
    upper = [(17.5, 5.5), (12, 6), (5, 6), (-2, 6.2)]
    lower = swing([(-2, 6.8), (5, 6.8), (12, 6.8), (17, 7)], open_deg)
    area = xf.poly([(-4.5, 6)] + lower + upper)
    cx, cy = xf.p(*swing([(3, 7)], open_deg * 0.5)[0])
    out = {}
    for q in area:
        d = math.hypot(q[0] - cx, q[1] - cy) / xf.s
        out[q] = ('!' if d < 1.8 else 'Y' if d < 3.6 else 'P' if d < 6.5 else 'p') if hot else \
                 ('P' if d < 2 else 'p' if d < 4.5 else 'N')
    return out


def tongue(xf, open_deg=0.0, hang=0.0):
    """Lolling over the lower jaw's lip and down, streaming a little in the wind."""
    pts = [(3, 7.2), (12, 7.5), (16, 9), (18, 12 + hang), (16.5, 15 + hang), (13.5, 14.5 + hang),
           (11.5, 11), (4, 10)]
    t = fill(xf.poly(swing(pts, open_deg)), 'N')
    recolor(t, edge(t, 1, 0, 1), 'p')
    recolor(t, edge(t, 0, 1, 1), 'n')
    recolor(t, edge(t, -1, 0, 1), 'n')
    for q in xf.line(swing([(6, 8.5), (13, 9.5), (15.5, 12.5 + hang)], open_deg)):
        if q in t and t[q] == 'N':
            t[q] = 'n'
    q = xf.ip(*swing([(14, 8.5)], open_deg)[0])
    if q in t:
        t[q] = 'P'
    return t


#EAR, RUFF, COLLAR

# The ear hangs from its root under gravity and trails in the wind, so it is laid out in frame space
# from the root (which rides the head): offsets in units of s, +y down, then swept back by EAR_SWEEP.
EAR_ROOT = (-11.5, -6.5)
EAR = [(2.6, 0), (3.2, 6), (3.0, 12), (2.4, 17), (2.2, 21.5), (0.4, 19), (-1.0, 23), (-2.4, 19.5),
       (-3.8, 22.5), (-4.2, 18), (-4.6, 12), (-4.4, 5.5), (-3.6, 0.5), (-1.6, -1.5), (0.8, -1.5)]
EAR_SWEEP = 0.14
EAR_LEN = 23.0


def ear(xf, sweep=EAR_SWEEP):
    rx, ry = xf.p(*EAR_ROOT)
    s = xf.s

    def at(dx, dy):
        return (rx + s * (dx - sweep * dy), ry + s * dy)
    e = fill(poly([at(dx, dy) for (dx, dy) in EAR]), 'r')
    rel = {q: ((q[0] - rx) / s + sweep * (q[1] - ry) / s, (q[1] - ry) / s) for q in e}
    for q, (dx, dy) in rel.items():               # the lit leather down its front
        if dx > -0.5 and dy < EAR_LEN * 0.66:
            e[q] = 's'
    recolor(e, edge(e, -1, 0, 2), 'q')            # its back edge falls into shadow
    top = {q for q, (dx, dy) in rel.items() if dy <= 1.5}
    recolor(e, top, 't')
    recolor(e, edge(e, 0, -1, 1) & top, 'u')
    for q in poly_line([at(-0.9, 3), at(-0.9, 10), at(-1.4, 16)]):     # the fold
        if q in e and e[q] in 'rs':
            e[q] = 'q'
    for q in edge(e, -1, 0, 1):                   # Hades' violet rim down the shadowed back edge
        dx, dy = rel[q]
        if 4 <= dy <= EAR_LEN * 0.66:
            e[q] = 'e'
    for seg in ([at(1.4, 1), at(1.0, 5.5)], [at(-3.0, 7), at(-3.3, 12.5)], [at(0.9, 9.5), at(0.5, 14.5)]):
        for q in poly_line(seg):
            if q in e:
                e[q] = 'k'
    for q, (dx, dy) in rel.items():               # the ragged hem burns
        if dy >= EAR_LEN * 0.85:
            e[q] = 'P'
        elif dy >= EAR_LEN * 0.75:
            e[q] = 'v'
        elif dy >= EAR_LEN * 0.63:
            e[q] = 'u'
        elif dy >= EAR_LEN * 0.56 and e[q] not in 'qke':
            e[q] = 't'
    return e


RUFF = [(-2, 7), (-4, 11.5), (-3, 15.5), (-6.5, 13), (-8, 17.5), (-10.5, 13), (-13, 16), (-15, 10),
        (-16.5, 4), (-11, 6.5)]


def ruff(xf):
    r = fill(xf.poly(RUFF), 's')
    recolor(r, edge(r, 0, 1, 2), 'r')
    recolor(r, edge(r, -1, 0, 1), 'r')
    cut(r, xf, [[(-5, 8), (-5, 12)], [(-9.5, 8), (-10, 13)]])
    return r


def collar(xf):
    """The wine collar round the throat where the neck leaves the head (under the ear, behind the jaw),
    its gold studs, and gold spikes hanging off its lower edge as on the approved collars."""
    pts = [(-16.5, 0.5), (-11.5, 2.5), (-9.0, 11.5), (-11.5, 15.0), (-16.0, 13.5), (-18.5, 5.0)]
    band = fill(xf.poly(pts), 'L')
    recolor(band, edge(band, 0, -1, 1), 'M')
    recolor(band, edge(band, 1, 0, 1), 'm')
    recolor(band, edge(band, -1, 0, 1), 'l')
    recolor(band, edge(band, 0, 1, 1), 'l')
    for (u, v) in ((-13.5, 6.0), (-12.5, 10.5)):
        q = xf.ip(u, v)
        if q in band:
            band[q] = 'O'
            below = (q[0], q[1] + 1)
            if below in band:
                band[below] = 'G'
    spikes = []
    for (bu, bv) in ((-10.5, 14.2), (-13.5, 15.0), (-16.6, 13.2)):
        # hanging from the lower edge: "down" on the head, which the pitch turns down and back
        tri = [(bu - 1.8, bv - 0.6), (bu + 1.8, bv - 0.2), (bu + 0.6, bv + 4.6)]
        sp = fill(xf.poly(tri), 'o')
        recolor(sp, edge(sp, 1, 0, 1), 'O')
        recolor(sp, edge(sp, -1, 0, 1), 'G')
        recolor(sp, edge(sp, 0, 1, 1) & edge(sp, -1, 0, 1), 'g')
        spikes.append(sp)
    return band, spikes


#HEADBAND (the middle head's): steel band round the skull under the crest, the plate on the brow

def headband(xf):
    """Liam's band, level round the head just over the brow and back under the ear; the plate on the
    brow. Its knot sits under the ear, where the two tails stream back from."""
    band = fill(xf.poly([(5.8, -8.2), (0, -9.8), (-5, -10.6), (-11, -10.2), (-11.5, -7.6), (-5, -8.0),
                         (0, -7.2), (5.4, -5.8)]), 'T')
    recolor(band, edge(band, 0, -1, 1), 'U')
    recolor(band, edge(band, 0, 1, 1), 'S')
    plate = fill(xf.poly([(2.4, -12.2), (6.8, -10.6), (7.4, -6.0), (3.0, -6.6)]), 'U')
    recolor(plate, edge(plate, 0, -1, 1), 'W')
    recolor(plate, edge(plate, 1, 0, 1), 'W')
    recolor(plate, edge(plate, -1, 0, 1), 'T')
    recolor(plate, edge(plate, 0, 1, 1), 'T')
    q = xf.ip(4.6, -9.2)
    if q in plate:
        plate[q] = 'T'                            # the scratch across the plate
    return band, plate


KNOT = (-11.5, -9.0)


def headband_tails(xf, frame_pts, wave=0):
    """The two tails off the knot at the back of the head, streaming back along `frame_pts`
    (a list of frame points after the knot)."""
    tails = []
    kx, ky = xf.p(*KNOT)
    for off, r in ((0.0, 1.3), (2.6, 1.1)):
        pts = [(kx, ky + off * 0.3)]
        for i, (x, y) in enumerate(frame_pts):
            w = (wave * (1 if i % 2 else -1)) if i > 0 else 0
            pts.append((x, y + off + w))
        tl = fill(chain(pts, r, r * 0.8), 'T')
        recolor(tl, edge(tl, 0, -1, 1), 'U')
        recolor(tl, edge(tl, 0, 1, 1), 'S')
        tails.append(tl)
    return tails


#THE HEAD

DARKER = {'u': 't', 't': 's', 's': 'r', 'r': 'q'}


def build(cv, xf, open_deg=0.0, fire=False, with_headband=False, tongue_hang=0.0, tongue_out=True,
          dark=False, show_ear=True, show_collar=True):
    """Stamp one profile head onto cv, back to front. Returns its mouth points in frame coordinates."""
    tmp = type(cv)(w=cv.w, h=cv.h)
    tmp.stamp(crest(xf))
    tmp.stamp(ruff(xf))
    if show_collar:
        # the collar over the ruff, round the throat where the neck leaves the head; its gold spikes hang
        # off its lower edge, as on the approved collars
        band, spikes = collar(xf)
        for sp in spikes:
            tmp.stamp(sp)
        tmp.stamp(band)
    if open_deg > 0:
        tmp.stamp(maw(xf, open_deg))
        if fire:
            tmp.stamp(throat_glow(xf, open_deg), outline=False)
    tmp.stamp(lower_fang(xf, open_deg))
    tmp.stamp(jaw(xf, open_deg))
    if tongue_out:
        tmp.stamp(tongue(xf, open_deg, tongue_hang))
    tmp.stamp(upper_fang(xf))
    tmp.stamp(skull(xf))
    tmp.stamp(nose(xf))
    b, lit = brow(xf)
    tmp.stamp(b, outline=False)
    tmp.stamp(lit, outline=False)
    tmp.stamp(eye(xf))
    if with_headband:
        hb, plate = headband(xf)
        tmp.stamp(hb)
        tmp.stamp(plate)
    if show_ear:
        tmp.stamp(ear(xf))
    for p, k in tmp.px.items():
        cv.px[p] = DARKER.get(k, k) if dark else k
    lip = swing([(17, 7)], open_deg)[0]
    return dict(nose=xf.p(21.8, -2.5), lip=xf.p(19, 3), jaw_tip=xf.p(*lip), maw=xf.p(*swing([(8, 7)], open_deg * 0.5)[0]))
