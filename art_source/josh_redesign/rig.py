"""The approved Josh (josh3.build_frame) split into layers that can be re-posed, for the ground
animation sheets. Nothing here changes a josh3 part: every layer is built by the same josh3 code and
only moved, sheared or restacked, so frame 0 of the idle rebuilds the approved sprite exactly.

A layer is (px, outline): px a dict {(x, y): key}; outline stamps a keyline round it first.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import josh3                                                       # noqa: E402
import lib                                                         # noqa: E402
from lib import Canvas                                             # noqa: E402


#LAYERS OF THE APPROVED FRAME

def torso_px():
    """Everything build_frame stamps before the far arm: collar, coat, legs, boots, waistcoat, the
    chest and the skirt, with its own keylines."""
    cv = Canvas()
    for c in josh3.collar():
        cv.stamp(c)
    cv.stamp(josh3.coat_back())
    for leg in josh3.legs():
        cv.stamp(leg)
    for b in josh3.boots():
        cv.stamp(b, outline=False)
    for c in josh3.coat_panels():
        cv.stamp(c)
    cv.stamp(josh3.vest())
    lib.patch(cv.px, josh3.CHEST)
    sk = josh3.skirt()
    for q in [q for q in cv.px if 56 <= q[1] <= 71 and 24 <= q[0] <= 58]:
        del cv.px[q]
    cv.px.update(sk)
    lib.patch(cv.px, josh3.VEST_HEM)
    return dict(cv.px)


def far_arm_layers():
    return [(p, o) for p, o in josh3.far_arm()]


def head_px():
    return josh3.head()


def hat_layers():
    return josh3.hat()


def near_arm_layers():
    up, fo = josh3.near_arm()
    return [(up, True), (fo, True)]


def fan_px():
    return lib.amap(josh3.FAN, 6, 34)


def near_hand_px():
    return lib.amap(josh3.NEAR_HAND, 14, 40)


#MOVING LAYERS

def mv(px, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in px.items()}


def mvl(layers, dx, dy):
    return [(mv(p, dx, dy), o) for p, o in layers]


def hshear(px, y0, per, sign=-1, top=None):
    """Lean: rows above y0 shift sideways by one pixel for every `per` rows above it (sign -1 leans
    left, +1 right). Rows at or below y0 stay."""
    out = {}
    for (x, y), k in px.items():
        s = 0
        if y < y0:
            s = sign * ((y0 - y + per - 1) // per)
        out[(x + s, y)] = k
    return out


def vshear(px, cx, per, sign=1):
    """Tilt a wide flat thing (the hat): columns right of cx rise one pixel every `per` columns
    (sign 1), those left of it sink; sign -1 the other way."""
    out = {}
    for (x, y), k in px.items():
        d = x - cx
        s = -sign * (d // per) if d >= 0 else sign * ((-d + per - 1) // per)
        out[(x, y + s)] = k
    return out


def stretch_rows(px, seam, dy):
    """Breath: everything above the seam row moves up by dy (>0), and the seam row repeats to close
    the gap, so the body under it stays planted."""
    out = {}
    for (x, y), k in px.items():
        if y < seam:
            out[(x, y - dy)] = k
        else:
            out[(x, y)] = k
    for i in range(dy):
        for (x, y), k in px.items():
            if y == seam:
                out[(x, seam - 1 - i)] = k
    return out


#COMPOSING

def compose(layers, w=80, h=80):
    cv = Canvas(w, h)
    for part, outline in layers:
        cv.stamp(part, outline=outline)
    return cv


def approved_frame0_layers():
    L = [(torso_px(), False)]
    L += far_arm_layers()
    L.append((head_px(), True))
    L += hat_layers()
    L += near_arm_layers()
    L.append((fan_px(), False))
    L.append((near_hand_px(), False))
    return L


if __name__ == '__main__':
    from PIL import Image
    sys.path.insert(0, os.path.dirname(HERE))
    from imgdiff import pixel_diff
    a = compose(approved_frame0_layers()).image()
    b = josh3.build_frame(False).image()
    shipped = Image.open(os.path.join(HERE, '..', '..', 'Assets', 'Characters', 'Josh',
                                      'josh_cards.png')).convert('RGBA').crop((0, 0, 80, 80))
    print('rig vs build_frame:', pixel_diff(a, b) or 'identical')
    print('rig vs shipped josh_cards f0:', pixel_diff(a, shipped) or 'identical')
