"""Greyson, redesigned: the whole figure, 112x112, feet on row 111, column 56 the anchor and the
mirror axis (x' = 112 - x). Built back to front:
  legs (gr_muscle bump layers)  ->  boots (gr_boots)  ->  torso: neck, traps, chest, lats, abs as
  ONE layer  ->  trunks and waistband  ->  arms (gr_arms, traced muscle polygons)  ->  fists
  (gr_hands)  ->  head (gr_face, hand drawn)  ->  a sweep for orphan skin tones.
Layers are keylined where they overlap (a limb over the body is black); anatomy inside a layer is
lines in a dark tone of the skin, the house rule (art_source/vs_card_v2/STYLE.md).

Poses (Pose.name):
  'idle'  the ready stance: arms flared out by the lats (they cannot hang straight), elbows bent,
          fists clenched beside the thighs, feet planted wide. The stance he holds between
          attacks, and the one every attack will start from.
  'flex'  the signature: a front double biceps, fists at temple height, biceps peaked, lats
          spread under the raised arms, straining through gritted teeth.
Right-hand parts are built from mirrored points, never mirrored pixels, so they keep the
upper-left light.

    python -B gr_fig.py        # prints each pose's numbers and audit; writes nothing
Writing files is gr_export.py's job alone.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gr_kit as K  # noqa: E402
import gr_face  # noqa: E402
import gr_hands  # noqa: E402
import gr_arms  # noqa: E402
import gr_boots  # noqa: E402
from gr_kit import AX, Canvas, ellipsoid, fill, mpts, poly, sym  # noqa: E402
from gr_muscle import Bump, Form, Layer  # noqa: E402

CUTS = (0.78, 0.48, 0.21, -0.06)


def mp(p, side):
    return (AX - p[0], p[1]) if side else p


def mps(pts, side):
    return mpts(pts) if side else pts


def side_bumps(bumps, side):
    return [b.mirrored() for b in bumps] if side else bumps


def both(bumps):
    return bumps + [b.mirrored() for b in bumps]


# ------------------------------------------------------------------------------------ pose

class Pose:
    """What differs between the frames besides the arms (whose shapes live in gr_arms)."""

    def __init__(self, name):
        self.name = name
        if name == 'idle':
            self.fist = (25.0, 84.5)        # the fist beside the thigh
            self.face = 'idle'
            self.lat_flare = 0.5            # the lats push the arms out
        else:
            self.fist = (15.0, 40.0)        # the fist at the temple
            self.face = 'flex'
            self.lat_flare = 1.5            # spread wide under the raised arms


# ------------------------------------------------------------------------------------ legs

LEG_BUMPS = [
    Bump('sweep', (41.4, 87.6), 9.2, 5.2, ang=97, amp=1.8, cast=2, depth=2, taper=-0.15),
    Bump('front', (48.0, 88.8), 8.8, 4.6, ang=100, amp=1.6, cast=1, depth=3, taper=0.35),
    Bump('add', (53.0, 85.4), 5.0, 3.0, ang=100, amp=0.9, cast=1, depth=1),
    Bump('knee', (46.4, 97.2), 3.2, 2.2, amp=0.7, cast=1, depth=2),
    Bump('calfL', (41.6, 100.6), 4.6, 3.2, ang=100, amp=1.4, cast=2, depth=2),
    Bump('calfM', (50.8, 101.2), 4.0, 3.0, ang=80, amp=1.4, cast=2, depth=2),
]


def leg(side):
    """A bodybuilder's leg: the outer quad sweep, the teardrop, the inner thigh, the knee and the
    two calf heads, tucking into the boot's cuff."""
    bumps = side_bumps(LEG_BUMPS, side)
    pts = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6), (53.4, 98.8),
           (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]
    pix = poly(mps(pts, side))
    c = mp((46.2, 90), side)
    form = Form(axis=[(c[0], 80), (c[0], 104)], r=9.5)
    lay = Layer(pix, form, bumps, floor=0.2, strength=1.0)
    return lay.shade_owned(cuts=CUTS)[0]


# ------------------------------------------------------------------------------------ torso

def torso_bumps(P):
    f = P.lat_flare
    return [
        Bump('trap', (43.6, 47.4), 11.0, 4.8, ang=32, amp=1.5, cast=2, depth=1),
        Bump('neck', (52.0, 45.2), 4.6, 1.8, ang=74, amp=0.7, cast=1, depth=2),
        Bump('pec', (47.2, 56.4), 9.8, 6.4, ang=-10, amp=1.9, p=2.3, cast='6', depth=4),
        Bump('lat', (37.6 - f * 0.5, 64.0), 10.4, 4.8 + f * 0.4, ang=62, amp=1.5, cast=2,
             depth=1, taper=-0.2),
        Bump('obl', (45.4, 70.6), 5.6, 3.2, ang=78, amp=1.0, cast=2, depth=2),
        Bump('ab1', (52.2, 65.0), 3.6, 2.1, amp=1.0, p=3.4, cast=2, depth=3),
        Bump('ab2', (52.3, 69.0), 3.5, 2.0, amp=1.0, p=3.4, cast=2, depth=3),
        Bump('ab3', (52.4, 72.8), 3.3, 1.8, amp=0.9, p=3.2, cast=2, depth=3),
    ]


def torso(P):
    """The trunk as ONE layer: neck, traps, chest, lats and abs, so the traps meet the chest in a
    muscle line (a dark tone of the skin) and not a black one. The traps rise steep and high,
    up under the jaw (the portrait's slopes); the neck is a short column in the jaw's shadow."""
    f = P.lat_flare
    half = [(56, 41.0), (49.6, 41.2), (45.6, 43.2), (41.0, 45.6), (36.4, 48.4), (32.6, 51.2),
            (31.6, 53.6), (33.6, 56.0), (32.4 - f, 61.2), (32.6 - f, 64.6), (34.6 - f * 0.5, 68.0),
            (38.6, 71.2), (43.4, 74.0), (45.6, 75.6), (46.0, 77.5), (56, 77.5)]
    pix = poly(sym(half))
    form = Form(ellipsoid=(55, 58, 25, 24))
    lay = Layer(pix, form, both(torso_bumps(P)), floor=0.25, strength=1.0)
    part = lay.shade_owned(cuts=CUTS, floor_cast=1)[0]
    # the jaw and the mane shade the neck and the top of the chest under them
    for (x, y) in list(part):
        if 45 <= x <= 67 and y <= 52:
            steps = 2 if y <= 51 else 1
            for _ in range(steps):
                part[(x, y)] = K.DARKER[part[(x, y)]]
    return part


# ------------------------------------------------------------------------------------ trunks

def trunks():
    """Purple posing trunks, cut high on the hip (the style reference's and his 09-18 sprite's)."""
    pts = sym([(56, 74.2), (46.0, 74.2), (45.0, 77.0), (44.2, 79.8), (47.4, 81.0), (51.6, 82.6),
               (54.2, 84.0), (56, 84.6)])
    part = fill(poly(pts), 'C')
    ellipsoid(part, 51.5, 76, 15, 10, 'ABCDE', (0.86, 0.58, 0.20, -0.25))
    return part


def waistband_line():
    """The black line under the waistband, where the band sits over the trunks."""
    return [(x, 76) for x in range(46, 67)]


def waistband():
    pts = sym([(56, 73.8), (45.8, 73.8), (45.3, 75.6), (56, 75.6)])
    part = fill(poly(pts), 'B')
    ellipsoid(part, 50, 72, 16, 6, 'ABCDE', (0.8, 0.45, 0.0, -0.4))
    return part


# ------------------------------------------------------------------------------------ build

def build(pose='idle'):
    P = Pose(pose)
    cv = Canvas()
    for side in (0, 1):
        cv.stamp(K.despeckle(leg(side)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    cv.stamp(K.despeckle(torso(P)))
    cv.stamp(trunks())
    cv.stamp(waistband(), outline=False)
    for (x, y) in waistband_line():
        cv.px[(x, y)] = 'k'
    for side in (0, 1):
        cv.stamp(K.despeckle(gr_arms.arm(P.name, side)))
    for side in (0, 1):
        cv.stamp(gr_hands.fist(P.name, side, P.fist), outline=False)
    cv.stamp(gr_face.head(P.face), outline=False)
    # one last sweep for orphan skin tones left where layers overlap; the hand-drawn face keeps
    # every pixel it was drawn with
    K.despeckle(cv.px, keep=set(gr_face.face(P.face)))
    return cv


if __name__ == '__main__':
    for pose in ('idle', 'flex'):
        cv = build(pose)
        a = K.audit(cv.px)
        print(pose, K.stats(cv.image()), 'bbox', K.bbox(cv.px),
              'audit', {k: len(v) for k, v in a.items()})
