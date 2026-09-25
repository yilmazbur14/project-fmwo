"""Danny's sumo fists and wrist wraps.

The ready stance holds both fists in front at waist height, knuckles to the viewer: four finger
faces split by black lines, the knuckle ridge catching the light along the top, the thumb locked
across the bottom on the side towards his body. Each finger is its own keylined form, so the
separations come from the stamping; the light is re-run for each side, so both fists are lit from
the upper left.
"""
from sumo_lib import (Canvas, spoly, ellipse, capsule, shade, amap, MIR, edge, band)
import lib as jl


def _fingers(side, ox, oy):
    """Masks, back to front: the hand behind, the four finger faces (outside -> in), the thumb.
    Local coordinates are for the viewer's-left fist (pinky outside on the left); side=-1 mirrors
    the geometry about the frame's axis."""
    def P(pts):
        pts = [(ox + x, oy + y) for (x, y) in pts]
        if side < 0:
            pts = [(MIR - x, y) for (x, y) in pts]
        return spoly(pts, 2)

    hand = P([(3, 3), (9, 0.5), (18, 0), (25, 2.5), (27, 9), (26.5, 17), (23, 21.5), (13, 22.5),
              (5, 21), (1, 15), (0.5, 8)])
    # finger faces: knuckle at the top, curled tip at the bottom; the middle finger stands proud
    fingers = [
        P([(1.5, 5.5), (4, 3), (7, 3), (8, 6), (8, 14.5), (6.5, 16), (3, 16), (1.5, 13.5)]),     # pinky
        P([(7.5, 2.5), (10, 0.8), (13.5, 1), (14.5, 4), (14.5, 15.5), (13, 17), (9, 17), (7.5, 15)]),
        P([(14, 1), (16.5, -0.5), (20.5, 0), (21.5, 3), (21.5, 16), (20, 17.5), (15.5, 17.5), (14, 15.5)]),
        P([(21, 2), (23.5, 1), (26, 3), (26.8, 7), (26.5, 15), (25, 16.5), (22, 16.5), (21, 14.5)]),  # index
    ]
    thumb = P([(8.5, 16.5), (13, 14.5), (21, 14.2), (26.5, 15.5), (28, 18.5), (25.5, 21.5), (17, 22.5),
               (10, 21.5), (7.5, 19)])
    return hand, fingers, thumb


def fist(side, ox=33, oy=79):
    """The fist as a stamped layer dict, keylines included."""
    hand, fingers, thumb = _fingers(side, ox, oy)
    cv = Canvas()
    cv.stamp(shade(hand, sigma=4, exposure=-0.12))
    for f in fingers:
        cv.stamp(shade(f, sigma=2.6, exposure=0.03))
    cv.stamp(shade(thumb, sigma=2.6, exposure=0.05))
    return cv.px


# The wrap round the wrist: white bandage, wound on the diagonal, its far edge in shade.
def wrap(side, ox=29, oy=83, w=6, h=13):
    """A wrist wrap as a keylined band, the diagonal turns of the bandage drawn in the cool shade."""
    pts = [(ox + 1, oy), (ox + w, oy + 0.5), (ox + w + 0.5, oy + h), (ox + 1.5, oy + h + 0.5), (ox, oy + h * 0.5)]
    if side < 0:
        pts = [(MIR - x, y) for (x, y) in pts]
    body = spoly(pts, 1)
    part = {p: 'W' for p in body}
    for (x, y) in body:
        u = (x if side > 0 else MIR - x) - ox
        if (u + (y - oy)) % 4 == 0:
            part[(x, y)] = 'H'
    jl.rim(part, 'H', 1, 0, depth=1)
    jl.rim(part, 'h', 0, 1, depth=1)
    if side < 0:
        jl.rim(part, 'h', 1, 0, depth=1)
    return part
