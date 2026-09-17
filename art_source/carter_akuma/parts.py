"""Carter (Satsui no Hado) - mask builders for the 96x96 frames.

Layout (frame 0, standing):
  aura       rows  0..16
  skull      rows 11..40
  beard      rows 25..44
  shoulders  row  41
  chest/abs  rows 44..64
  rope belt  rows 63..71
  gi pants   rows 61..85
  shins      rows 85..91
  feet       rows 87..95   <- feet plane = bottom edge of the frame
"""
import math
from lib import (W, H, poly, ell, rrect, union, inter, sub, mirror, sym,
                 halfplane, empty, count, grow, ring, dither)

AXF = 95.0  # mirror axis: x' = 95 - x  (centre 47.5)


def mir_pts(half):
    """half = points down the LEFT side, top -> bottom, first/last on the axis."""
    return half + [(AXF - x, y) for x, y in reversed(half[1:-1])]


def cyl(a, b, r0, r1=None):
    """tapered capsule from a to b"""
    if r1 is None:
        r1 = r0
    m = empty()
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - x0, y + 0.5 - y0
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
            cx, cy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                m[y][x] = True
    return m


def lmir(m):
    return union(m, mirror(m))


# ------------------------------------------------------------------ head

HEAD_HALF = [
    (47.5, 11.4),
    (41.6, 11.8),
    (37.2, 13.6),
    (34.2, 17.0),
    (33.0, 21.4),
    (33.2, 27.0),
    (34.6, 32.2),
    (37.4, 36.4),
    (41.6, 39.2),
    (47.5, 40.4),
]


def head():
    return poly(mir_pts(HEAD_HALF))


def ears():
    return lmir(union(ell(33.4, 27.4, 3.3, 4.5), ell(34.6, 25.4, 2.8, 3.4)))


def beard_mass():
    """solid short beard over the jaw and chin - Carter's shape, trimmed."""
    from lib import erode, band
    hd = head()
    low = poly(mir_pts([
        (47.5, 45.0),
        (44.0, 44.6),
        (40.6, 42.6),
        (37.4, 39.0),
        (35.4, 34.8),
        (34.8, 32.4),
        (47.5, 31.8),
    ]))
    low = inter(low, grow(hd, 3))
    # sideburns: a narrow strip up the side of the face to the ear
    sb = inter(sub(hd, erode(hd, 4)), band(26.0, 36.0))
    return union(low, sb)


def moustache():
    """thick moustache with a small skin notch under the nose"""
    m = poly(mir_pts([
        (47.5, 31.4), (44.6, 31.2), (41.2, 32.2), (40.2, 35.0),
        (42.4, 36.4), (47.5, 36.8),
    ]))
    notch = poly([(45.4, 29.0), (49.6, 29.0), (49.6, 32.6), (45.4, 32.6)])
    return sub(m, notch)


def beard():
    return union(beard_mass(), moustache())


def neck():
    return poly(mir_pts([
        (47.5, 35.0), (43.2, 35.4), (41.6, 38.6), (41.2, 44.0), (47.5, 46.0),
    ]))


# ------------------------------------------------------------------ torso

TORSO_HALF = [
    (47.5, 41.0),
    (39.6, 41.4),
    (32.8, 44.0),
    (28.2, 48.0),
    (26.9, 53.4),
    (28.2, 58.8),
    (31.2, 62.8),
    (32.4, 67.0),
    (47.5, 69.0),
]


def torso():
    return poly(mir_pts(TORSO_HALF))


def pecs():
    return lmir(ell(41.4, 52.6, 7.2, 5.6, -8))


def delts():
    return lmir(union(ell(25.4, 51.6, 9.6, 8.6, -12),
                      ell(27.8, 46.4, 7.8, 5.4, -22)))


def upperarms():
    return lmir(cyl((26.2, 50.2), (22.0, 64.0), 7.0, 6.0))


def forearms():
    return lmir(cyl((22.0, 64.0), (20.8, 73.8), 6.0, 5.2))


def fists():
    return lmir(union(ell(19.8, 78.2, 5.2, 5.0), ell(20.8, 74.8, 4.8, 3.8)))


def arms():
    return union(upperarms(), forearms(), fists())


# ------------------------------------------------------------------ lower body

def hips():
    return poly(mir_pts([
        (47.5, 59.8), (34.6, 60.4), (31.0, 63.8), (30.6, 70.2), (47.5, 72.2),
    ]))


def thighs():
    return lmir(cyl((40.0, 64.5), (34.2, 84.4), 9.2, 8.4))


def crotch_cut():
    return poly([(44.6, 73.6), (50.4, 73.6), (53.6, 96.5), (41.4, 96.5)])


def shins():
    return lmir(cyl((34.0, 83.0), (33.0, 90.4), 5.6, 5.2))


def feet():
    return lmir(poly([
        (27.0, 87.4), (39.4, 87.0), (40.2, 91.6), (38.8, 95.6),
        (25.0, 95.6), (23.2, 92.6), (23.8, 89.6),
    ]))


def legs():
    return sub(union(thighs(), shins(), feet()), crotch_cut())


# ------------------------------------------------------------------ costume

def _hem_cut(lo, hi, step=3.4, x0=15.0, x1=81.0):
    """region below a zigzag line - used to tear a hem."""
    pts = []
    x = x0
    i = 0
    while x <= x1:
        pts.append((x, lo if i % 2 == 0 else hi))
        x += step
        i += 1
    pts.append((x1 + 1, hi))
    pts.append((x1 + 1, 97.0))
    pts.append((x0 - 1, 97.0))
    return poly(pts)


def gi_shoulders():
    """torn fabric cap over the top of each deltoid - the sleeve is gone."""
    l = poly([
        (41.6, 39.6), (42.2, 46.2), (39.2, 50.0), (38.2, 56.4),
        (35.8, 51.6), (33.6, 57.4), (30.6, 52.0), (27.4, 57.8),
        (24.2, 52.2), (20.8, 55.0), (18.8, 48.6), (20.6, 43.4),
        (26.0, 40.8), (33.4, 39.6),
    ])
    return lmir(l)


def gi_lapels():
    """the open front edge of the jacket down each side of the chest."""
    l = poly([
        (29.4, 43.4), (37.4, 47.6), (36.6, 53.2), (36.8, 59.2),
        (38.0, 65.4), (39.6, 71.4), (37.4, 76.2), (29.2, 75.4),
        (27.2, 68.0), (26.4, 60.0), (27.0, 49.6),
    ])
    return lmir(l)


def _hem_cut(lo, hi, step=3.4, x0=15.0, x1=81.0):
    """region below a zigzag line - used to tear a hem."""
    pts = []
    x = x0
    i = 0
    while x <= x1:
        pts.append((x, lo if i % 2 == 0 else hi))
        x += step
        i += 1
    pts.append((x1 + 1, hi))
    pts.append((x1 + 1, 97.0))
    pts.append((x0 - 1, 97.0))
    return poly(pts)


def _band(y0, y1):
    from lib import band
    return band(y0, y1)


def gi_jacket():
    j = union(gi_shoulders(), gi_lapels())
    j = sub(j, _hem_cut(71.4, 75.4, step=2.8))
    return sub(j, inter(union(upperarms(), forearms()), _band(58.0, 96.0)))


def gi_flaps():
    return inter(gi_jacket(), _band(62.0, 78.0))


def gi_panels():
    return gi_jacket()


def gi_pants():
    """one baggy navy mass from the belt to a torn hem above the ankles."""
    body = poly(mir_pts([
        (47.5, 60.6), (33.4, 61.4), (29.6, 65.6), (29.0, 72.0),
        (29.8, 77.0), (31.0, 81.4), (47.5, 82.4),
    ]))
    body = union(body, sub(thighs(), crotch_cut()))
    return sub(sub(body, _hem_cut(79.0, 82.6, step=3.0)), crotch_cut())


def pant_hem_rags():
    from lib import empty as _e
    return _e()


def belt():
    return poly([(29.2, 62.6), (65.8, 62.6), (66.2, 68.4), (28.8, 68.4)])


def belt_knot():
    return union(ell(47.5, 65.2, 5.4, 3.8),
                 poly([(44.2, 67.8), (46.8, 67.8), (46.0, 75.6), (43.4, 74.6)]),
                 poly([(48.8, 67.8), (51.4, 67.8), (52.0, 73.6), (49.4, 74.2)]))


def wraps_wrist():
    return lmir(cyl((21.4, 70.2), (20.4, 74.6), 5.6, 5.2))


def wraps_fist():
    return lmir(union(ell(19.8, 78.2, 5.2, 5.0), ell(20.8, 74.8, 4.8, 3.8)))


def wraps_ankle():
    from lib import empty as _e
    return _e()


def beads_centres():
    """big juzu beads: arc across the chest, up over both shoulders."""
    pts = []
    for i in range(7):
        t = i / 6.0
        x = 40.4 + t * 14.2
        y = 45.2 + math.sin(math.pi * t) * 7.0
        pts.append((x, y))
    pts += [(37.4, 43.4), (34.4, 42.4), (31.4, 42.0),
            (58.6, 43.4), (61.6, 42.4), (64.6, 42.0)]
    return pts


def beads(r=2.6):
    m = empty()
    for cx, cy in beads_centres():
        m = union(m, ell(cx, cy, r, r))
    return m


def body_mask():
    return union(legs(), gi_pants(), gi_jacket(), hips(),
                 torso(), delts(), arms(), neck(), head(),
                 ears(), beard())


def empty_mask():
    from lib import empty as _e
    return _e()
