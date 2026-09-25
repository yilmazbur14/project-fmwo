"""Shared palette and helpers for Carter's MESSATSU effects.

The engine is carter_demon_fx/fxlib.py, imported rather than copied, so these
effects share the Raging Demon's masks, dither and palette and cannot drift
away from them.

THE PALETTE IS THE DEMON'S OWN.  Every violet here is RAMPS['void'], the ramp
his aura, his clones and the parry break's smoke are drawn in, plus white.  The
only red is RAMPS['glow'] - his eye ramp - and it is spent in exactly two
places: his eyes in the dark and the rim of a surge, which is the parry cue.
The aim line and the lock are violet, never red or yellow: those two colours
are this fight's answer key.

SIX COLOURS A SHEET.  demon_parry_break.png measures six opaque colours, a
four-step hot ramp (ffc21e ffe45c fffce0 ffffff) over a two-step violet smoke
(4e1878 7c2eb0), with no partial alpha anywhere.  Every sheet here is held to
that: six colours, all alpha 255, falloffs done by ordered dither.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', 'carter_demon_fx'))

from fxlib import (Mask, Cv, ell, poly, ray, rect, ramp, sheet, hexc,   # noqa: E402,F401
                   bayer01, quant, field, CLEAR, stamp_mask)

VO = ramp('void')      # e2a2f4 b45ae0 7c2eb0 4e1878 2e0c4c 19062a
GL = ramp('glow')      # ffffff ffd2d8 ff5a62 e0203c 90102a 54061a
WHITE = hexc('ffffff')

# The beam's ramp, brightest first.  Painted, so it has to read as violet over
# a lit green mat - additive violet on that mat mixes to grey (see beam.py).
W, P, Q, R, S, T = WHITE, VO[0], VO[1], VO[2], VO[3], VO[4]


def sn(k, p, phase, period=32.0):
    """one harmonic of a pattern that repeats every `period` texels"""
    import math
    return math.sin(2.0 * math.pi * k * p / period + phase)


def colours(cv_or_list):
    """distinct colours drawn on a canvas (or a list of canvases)"""
    cvs = cv_or_list if isinstance(cv_or_list, list) else [cv_or_list]
    seen = set()
    for cv in cvs:
        for row in cv.px:
            for p in row:
                if p is not None and p[3] > 0:
                    seen.add(p)
    return seen
