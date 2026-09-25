"""Greyson's body in the brawl's LIGHT CROUCH: the approved legs, boots, torso, trunks and head,
dropped `d` rows with the knees bent (every leg point and muscle squeezed toward the boot, the
knees pushed a little out), the boots left planted on row 111.

The legs are the approved leg's own outline and muscles (gr_fig.leg: its points copied here as
data, its Bumps transformed), shaded fresh under the same light, so the crouch is the same leg
drawn bent, not a squashed picture.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402
from gr_muscle import Bump, Form, Layer  # noqa: E402

K, G, P = B.K, B.G, B.P
gr_fig, gr_face, gr_boots = G.gr_fig, G.gr_face, G.gr_boots

# the approved leg's outline (gr_fig.leg), hip at the top, the boot's cuff at the bottom
LEG_PTS = [(42.5, 78.5), (38.9, 82.6), (37.1, 87.4), (37.2, 92.2), (39.2, 95.4), (40.2, 97.4),
           (38.6, 99.4), (39.8, 101.2), (41.0, 102.4), (52.0, 102.4), (53.4, 100.6), (53.4, 98.8),
           (52.6, 97.4), (54.6, 94.4), (55.9, 89.5), (56.0, 80.0)]
HIP, ANKLE = 78.5, 102.4


class Crouch:
    """The bend: rows above the ankle squeezed toward it so the hip drops d rows; the knee pushed
    `flare` columns outward (a bell over the leg, peaking a little below the middle)."""

    def __init__(self, d, flare=1.5):
        self.d, self.flare = d, flare
        self.s = (ANKLE - HIP - d) / (ANKLE - HIP)

    def y(self, y):
        return ANKLE - (ANKLE - y) * self.s if y < ANKLE else y

    def pt(self, p, bend=True):
        x, y = p
        y2 = self.y(y)
        if not bend or y >= ANKLE:
            return (x, y2)
        t = max(0.0, min(1.0, (y2 - (HIP + self.d)) / (ANKLE - HIP - self.d)))
        bell = math.sin(math.pi * t ** 0.8)
        return (x - self.flare * bell, y2)            # left leg: outward is -x

    def bump(self, b):
        ang = math.radians(b.ang)
        ca, sa = math.cos(ang), math.sin(ang)
        fa = math.hypot(ca, sa * self.s)
        fb = math.hypot(-sa, ca * self.s)
        new_ang = math.degrees(math.atan2(sa * self.s, ca))
        return Bump(b.name, self.pt(b.c), b.a * fa, b.b * fb, new_ang, b.amp, b.z0, b.p, b.prof,
                    b.cast, b.depth, b.taper, b.skew)


def leg(side, d, flare=1.5):
    c = Crouch(d, flare)
    pts = [c.pt(p) for p in LEG_PTS]
    bumps = [c.bump(b) for b in gr_fig.LEG_BUMPS]
    if side:
        pts = K.mpts(pts)
        bumps = [b.mirrored() for b in bumps]
    cx = 46.2 if not side else K.AX - 46.2
    form = Form(axis=[(cx, c.y(80.0)), (cx, 104)], r=9.5)
    lay = Layer(K.poly(pts), form, bumps, floor=0.2, strength=1.0)
    return lay.shade_owned(cuts=gr_fig.CUTS)[0]


def moved(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def front_base(cv, d, lat_flare=1.0, flare=1.5):
    """Legs bent d rows, boots planted, torso, trunks and waistband dropped d rows."""
    Pz = gr_fig.Pose('idle')
    Pz.lat_flare = lat_flare
    for side in (0, 1):
        cv.stamp(K.despeckle(leg(side, d, flare)))
    for side in (0, 1):
        cv.stamp(gr_boots.boot(side), outline=False)
    cv.stamp(moved(K.despeckle(gr_fig.torso(Pz)), 0, d))
    cv.stamp(moved(gr_fig.trunks(), 0, d))
    cv.stamp(moved(gr_fig.waistband(), 0, d), outline=False)
    for (x, y) in gr_fig.waistband_line():
        cv.px[(x, y + d)] = 'k'


def head(face_rows_or_name, dx=0, dy=0, extras=None):
    """The approved mane and a face (approved, fight or new), moved; -> (part, face pixels)."""
    part, fpx = P.head_part(face_rows_or_name, extras)
    return moved(part, dx, dy), set(moved({p: 1 for p in fpx}, dx, dy))
