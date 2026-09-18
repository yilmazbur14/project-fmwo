"""demon_finish.png - the white-out when the fifth clone is done and the lights
come up, with Carter's emblem burning in it.

The emblem is NOT redrawn here.  carter_akuma/intro_sigil.py already owns that
shape and it is stamped on the back of the approved sprite; a second copy would
drift.  Instead its polygons are re-rasterised at 3x resolution, by pointing
intro_sigil.poly at a wrapper that scales the points and telling lib to work on
a 288x288 grid.  That gives clean diagonals at the larger size, which a
nearest-neighbour upscale of the 96x96 mask would not - it would triple every
stair-step on the horns.

The one subtlety is the mirror axis.  lib.mirror is row[::-1], so it reflects
about the canvas centre, W/2; intro_sigil lays its halves out about x=47.5 and
relies on sym() to force the result symmetric.  Scaled by 3 the shape's axis
lands on 142.5 while the canvas centre is 144.0, and sym() would fatten the
emblem by a pixel and a half on one side.  Adding 0.5*scale to every x puts the
two axes back on top of each other.
"""
import math
import os
import sys

from fxlib import Mask, Cv, ell, ray, poly, ramp, sheet, hexc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'carter_akuma'))
import lib as CLIB                                  # noqa: E402
import intro_sigil                                  # noqa: E402

S = 224                    # 672 px at 3x, centred on screen
C = 112.0
VO = ramp('void')
GO = ramp('gold')
EM = ramp('ember')
WHITE = hexc('ffffff')
PINK = hexc('ffd2d8')


def sigil_mask(scale=3):
    """intro_sigil's shipped emblem, re-rasterised `scale` times larger"""
    keep_w, keep_h, keep_poly = CLIB.W, CLIB.H, intro_sigil.poly
    CLIB.W = CLIB.H = 96 * scale
    off = 0.5 * scale
    intro_sigil.poly = lambda pts: keep_poly(
        [(x * scale + off, y * scale) for x, y in pts])
    try:
        raw = intro_sigil.sigil()                   # the trident that shipped
    finally:
        CLIB.W, CLIB.H, intro_sigil.poly = keep_w, keep_h, keep_poly

    n = 96 * scale
    m = Mask(n, n, [[bool(v) for v in row] for row in raw])
    bb = m.bbox()
    out = Mask(S, S)
    ox = int(C - (bb[0] + bb[2] + 1) / 2.0)
    oy = int(C - (bb[1] + bb[3] + 1) / 2.0)
    for y in range(bb[1], bb[3] + 1):
        for x in range(bb[0], bb[2] + 1):
            if m.g[y][x] and 0 <= x + ox < S and 0 <= y + oy < S:
                out.g[y + oy][x + ox] = True
    return out


SIGIL = None


def _sigil():
    global SIGIL
    if SIGIL is None:
        SIGIL = sigil_mask(3)
    return SIGIL


def _bloom(r, steps, squash=1.0):
    """a disc of light quantised into rings, ordered-dithered at each boundary"""
    m = []
    for i, _ in enumerate(steps):
        rr = r * (1.0 - i / float(len(steps)))
        m.append(ell(S, S, C, C, rr, rr * squash))
    return m


def frame(f):
    cv = Cv(S, S)
    # Radius of the bloom, and how much of it is pure white.  The cap is 108:
    # at 112 the disc runs off a 224 canvas and the white-out grows visible
    # straight edges where it is clipped.  The actual screen white-out is the
    # coder's full-screen ColorRect, not this sprite - see the contract.
    rad = (54.0, 84.0, 108.0, 94.0, 66.0)[f]
    hot = (0.34, 0.54, 0.80, 0.42, 0.10)[f]
    thin = (16, 16, 16, 12, 6)[f]

    # ---- rays, behind everything
    rays = Mask(S, S)
    for i in range(16):
        a = i * 22.5 + f * 4.0
        rays = rays | ray(S, S, C, C, a, rad * 0.5, rad * (1.5 - f * 0.12),
                          5.0 - f * 0.6, 0.6)
    cv.paint(rays.dither(max(4, thin - 4)), GO[2] if f < 4 else VO[3])
    cv.paint(rays.erode(2).dither(max(4, thin - 2)), GO[1] if f < 4 else VO[2])

    # ---- the bloom
    discs = _bloom(rad, range(6))
    cols = ([GO[3], GO[2], GO[1], GO[0], WHITE, WHITE] if f < 4 else
            [VO[4], VO[3], VO[3], VO[2], VO[1], VO[1]])
    for i, d in enumerate(discs):
        cv.paint(d.dither(thin if i else max(6, thin - 6)), cols[i])
    white = ell(S, S, C, C, rad * hot, rad * hot)
    cv.paint(white, WHITE)

    # ---- the emblem, burning in the middle of it
    sg = _sigil()
    if f == 0:
        # igniting: only the edges have caught
        cv.paint(sg.ring(1, diag=True), GO[0])
        cv.paint(sg.erode(1).dither(6, off=1), EM[2])
    elif f == 1:
        cv.paint(sg.grow(2, diag=True), GO[0])
        cv.paint(sg, WHITE)
        cv.paint(sg.erode(3), GO[1])
    elif f == 2:
        # peak white-out: the emblem holds as a dark mark inside the white so
        # it is still legible when everything around it is blown out
        cv.paint(sg.grow(3, diag=True), WHITE)
        cv.paint(sg, EM[3])
        cv.paint(sg.erode(2), EM[2])
        cv.paint(sg.erode(4), GO[1])
    elif f == 3:
        cv.paint(sg.grow(1, diag=True), EM[4])
        cv.paint(sg, EM[2])
        cv.paint(sg.erode(2), GO[1])
        cv.paint(sg.erode(4).dither(9), WHITE)
    else:
        # last breath: a violet ghost of the mark
        cv.paint(sg.dither(9, off=2), VO[2])
        cv.paint(sg.erode(2).dither(7, off=1), VO[1])

    # ---- embers drifting off the ring
    for i in range(20 - f * 3):
        a = math.radians(i * 19.0 + f * 7.0)
        r = rad * (0.95 + (i % 5) * 0.09)
        cv.set(int(C + math.cos(a) * r), int(C + math.sin(a) * r),
               GO[0] if i % 3 else PINK)
    return cv


def build(path):
    return sheet([frame(i) for i in range(5)], path)
