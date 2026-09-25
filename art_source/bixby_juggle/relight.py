"""Keep the light where the cast's light is while the body turns.

The rig lights every part with shapes.edge() recipes: a lit rim on the side facing (0, -1), shade on
the side facing (0, +1), and a body-relative falloff on the sides (+-1, 0) (the approved frontal,
mirrored light). Rotating a finished frame would carry the top light round with the body. Instead the
vertical recipes are asked, while the part is built in its own upright frame, for the side that will
face screen-up (or screen-down) once the frame is turned by `theta`: the rig's own volume, only the
normal rotated. The side recipes are left alone: a frontal light is unchanged by a turn in the picture
plane. At theta 0 every recipe is the rig's own, so the approved look is reproduced pixel for pixel.

Parts the rig mirrors for the left side are built in right-side space, so their recipes are turned by
M . R(-theta) instead of R(-theta).
"""
import contextlib
import math

import shapes
import body
import heads
import rig_body
import rig_wings
import wings
import rig_fx

_ORIG = shapes.edge
_MODS = (shapes, body, heads, rig_body, rig_wings, wings, rig_fx)

# the active turn: None, or the 2x2 matrix taking a screen direction to the part's build space
_T = [None]
# whether the side recipes swap: the rig lights a part's (-1, 0) side (its inner side) and shades its
# (+1, 0) side. Turned a quarter, that pair runs up and down the screen, and for half the parts the lit
# side would face down; those parts swap their side recipes so the light still comes from above.
_SWAP = [False]


def _dir_edge(part, ux, uy, depth):
    """Pixels of `part` whose ray toward (ux, uy) leaves the part within `depth` px (sub-pixel)."""
    body_ = set(part)
    out = set()
    steps = max(1, int(round(depth / 0.1)))
    for (x, y) in body_:
        for i in range(1, steps + 1):
            t = depth * i / steps
            q = (int(math.floor(x + ux * t + 0.5)), int(math.floor(y + uy * t + 0.5)))
            if q != (x, y) and q not in body_:
                out.add((x, y))
                break
    return out


def edge(part, dx, dy, depth=1):
    T = _T[0]
    if T is not None and dy == 0 and dx != 0 and _SWAP[0]:
        return _ORIG(part, -dx, 0, depth)
    if T is None or dx != 0 or dy == 0:
        return _ORIG(part, dx, dy, depth)
    ux = T[0][0] * dx + T[0][1] * dy
    uy = T[1][0] * dx + T[1][1] * dy
    if abs(ux) < 1e-9 and abs(abs(uy) - 1) < 1e-9:
        return _ORIG(part, 0, int(round(uy)), depth)
    if abs(uy) < 1e-9 and abs(abs(ux) - 1) < 1e-9:
        return _ORIG(part, int(round(ux)), 0, depth)
    return _dir_edge(part, ux, uy, depth)


def screen_to_build(theta, mirrored=False):
    """R(-theta), or M . R(-theta) for a part built on the right and mirrored to the left."""
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    R_inv = [[c, s], [-s, c]]
    if mirrored:
        R_inv = [[-R_inv[0][0], -R_inv[0][1]], [R_inv[1][0], R_inv[1][1]]]
    return R_inv


def lit_side_down(theta, mirrored=False):
    """Does this part's lit side, (-1, 0) where it is built, face down the screen once turned?"""
    t = math.radians(theta)
    lx = 1.0 if mirrored else -1.0          # the lit side in the frame's own (upright) space
    sy = math.sin(t) * lx                   # its screen y after the turn R(theta)
    return sy > 0.25


@contextlib.contextmanager
def lit(theta, mirrored=False):
    """Build parts inside this block lit for a frame turned by `theta` (degrees, clockwise)."""
    prev, prev_swap = _T[0], _SWAP[0]
    _T[0] = None if (theta % 360 == 0 and not mirrored) else screen_to_build(theta, mirrored)
    if theta % 360 == 0 and mirrored:
        _T[0] = None            # the mirror of the upright light is the rig's own
    _SWAP[0] = _T[0] is not None and lit_side_down(theta, mirrored)
    saved = [getattr(m, 'edge', None) for m in _MODS]
    for m in _MODS:
        if m is not shapes:
            m.edge = edge
    try:
        yield
    finally:
        for m, e in zip(_MODS, saved):
            if m is not shapes:
                m.edge = e
        _T[0], _SWAP[0] = prev, prev_swap
