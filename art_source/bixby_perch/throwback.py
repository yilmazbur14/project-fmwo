"""Heads thrown back to spit upward (the volley), built from the rig's own head parts (heads.py) with
three projections instead of one: the skull tipped back (pitch.PXf), the lower jaw tipped back less and
dropped open below it, and the collar and ruff where the neck is. The gap between the upper lip and the
dropped jaw is the maw, dark at the lips and on fire in the throat.

build(cv, cx, cy, s, phi, theta, pitch, drop) stamps one head. The middle head is phi 0, s 1; the side
heads are the approved side placement's phi -28 / theta 12 / s 0.7 (right; the left is mirrored).
"""
import math

from common import heads, pal, shapes
from pal import fill, poly
from shapes import edge, recolor
from pitch import PXf

H = heads
# the maw between the lips when the jaw hangs open, in head space: from the upper lip's line down to the
# dropped jaw's top (the jaw's own polygon covers the rest)
MAW = H.half([(95.5, 52, 12), (104, 52, 11), (110, 54, 8), (114, 60, 5), (114, 70, 5), (110, 80, 7),
              (104, 84, 9), (95.5, 86, 10)])


def _maw(xf, jaw_xf, throat_hot=True):
    top = xf.poly(MAW[:len(MAW) // 2 + 1] + MAW[len(MAW) // 2 + 1:])
    bottom = jaw_xf.poly(MAW)
    region = top | bottom
    m = fill(region, 'q')
    # the throat: dark, then fire building in it
    ys = [p[1] for p in region]
    xs = [p[0] for p in region]
    cx = (min(xs) + max(xs)) / 2.0
    cy = min(ys) + (max(ys) - min(ys)) * 0.55
    rx = (max(xs) - min(xs)) / 2.0
    ry = (max(ys) - min(ys)) / 2.0
    for p in list(m):
        d = math.hypot((p[0] - cx) / max(1.0, rx * 0.8), (p[1] - cy) / max(1.0, ry * 0.8))
        if d < 0.72:
            m[p] = 'k'
        if throat_hot:
            if d < 0.2:
                m[p] = 'Y'
            elif d < 0.34:
                m[p] = 'P'
            elif d < 0.48:
                m[p] = 'p'
            elif d < 0.6:
                m[p] = 'N'
    return m, (cx, cy)


def build(cv, cx, cy, s=1.0, phi=0.0, theta=0.0, pitch=24.0, drop=9.0, jaw_pitch=None, with_headband=True,
          tongue_flip=False, hot=True, low_dy=0, eyes='squint', tongue=False):
    """One thrown-back head; returns the maw's centre (where the fireball leaves)."""
    pv = (46.0, 0.0)                      # tip about the neck, below the jaw
    xf = PXf(cx, cy, phi, s, theta, pitch, pv)
    jp = pitch * 0.45 if jaw_pitch is None else jaw_pitch
    jaw_xf = PXf(cx, cy + drop * s, phi, s, theta, jp, pv)
    low = H.Xf(cx=cx, cy=cy + low_dy, phi=phi, s=s, theta=theta)
    cv.stamp(H.ear(xf, 1))
    cv.stamp(H.ear(xf, -1))
    cv.stamp(H.crest(xf))
    band, spikes = H.collar(low)
    for sp in spikes:
        cv.stamp(sp)
    cv.stamp(band)
    cv.stamp(H.ruff(low))
    maw, centre = _maw(xf, jaw_xf, hot)
    cv.stamp(maw)
    for side in H.both_sides(H.LOWER_FANG):
        cv.stamp(H.fang(jaw_xf, side, 10))
    cv.stamp(H.jaw(jaw_xf))
    if tongue:
        cv.stamp(H.tongue(jaw_xf, tongue_flip))
    for side in H.both_sides(H.UPPER_FANG):
        cv.stamp(H.fang(xf, side, 12))
    cv.stamp(H.skull(xf))
    cv.stamp(H.nose(xf))
    for side in (1, -1):
        b, lit = H.brow(xf, side)
        cv.stamp(b, outline=False)
        cv.stamp(lit, outline=False)
        e = H.eye(xf, side)
        if eyes == 'squint':
            # narrowed against the blast: keep the eye's lower half
            ys = [p[1] for p in e]
            mid = (min(ys) + max(ys)) / 2.0
            e = {p: k for p, k in e.items() if p[1] >= mid - 0.5}
        cv.stamp(e)
    if with_headband:
        band, plate = H.headband(xf)
        cv.stamp(band)
        cv.stamp(plate)
    return centre


MID = (95.5, 43)          # the approved middle head's placement
SIDE = (156, 70)          # the approved right side head's


def mid(dy=0, pitch=28, drop=10, hot=True, eyes='squint'):
    """A draw hook for perch.build's middle head, and where its maw is."""
    def draw(cv):
        build(cv, MID[0], MID[1] + dy, pitch=pitch, drop=drop, hot=hot, eyes=eyes)
    from common import canvas
    tmp = canvas()
    maw = build(tmp, MID[0], MID[1] + dy, pitch=pitch, drop=drop, hot=hot, eyes=eyes)
    return draw, (int(round(maw[0])), int(round(maw[1])))


def side(dx=0, dy=0, pitch=28, drop=7, hot=True, eyes='squint'):
    """A draw hook for the right side head (pixels), and where its maw is."""
    from common import canvas

    def draw():
        tmp = canvas()
        build(tmp, SIDE[0] + dx, SIDE[1] + dy, s=0.7, phi=-28, theta=12, pitch=pitch, drop=drop,
              with_headband=False, tongue_flip=True, hot=hot, eyes=eyes)
        return dict(tmp.px)
    tmp = canvas()
    maw = build(tmp, SIDE[0] + dx, SIDE[1] + dy, s=0.7, phi=-28, theta=12, pitch=pitch, drop=drop,
                with_headband=False, tongue_flip=True, hot=hot, eyes=eyes)
    return draw, (int(round(maw[0])), int(round(maw[1])))
