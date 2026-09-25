"""matt_teleport.png: 6 frames at 0.05 s. Out 0-2, in 3-5: he squeezes into a lavender/gold streak.

    0  out: squash      crouched, eyes squeezed, crest pressed down, arms pulled in
    1  out: streak      stretched into a tall spindle, lavender with a gold core and a gold crest tip
    2  out: thread      a thin lavender/gold thread, nearly gone
    3  in:  thread      the thread again, a shade wider
    4  in:  streak      the spindle, thickening
    5  in:  landing     squashed on landing, arms out, eyes opening
The streak is the character, not an effect, so it keeps his keyline; matt_teleport_fx (the FX
artist's column burst) plays over it.
"""
import math

import mf_base as M
from mf_base import B, A, G, F, H, L, PZ
import mf_faces as FF
import mi_arms


def squash(land=False):
    legs = (lambda f: L.walk_legs(3, (-2, 0, -1.0), (2, 0, 1.0), screen=True))
    arms = PZ.hang_pair(upper_rot=18 if land else -6, fore_rot=16 if land else -10, shoulder_dy=2)
    eyes = G.EY_ANGRY if land else G.EY_SQUEEZE
    return F.Fig(arms=arms, legs=legs, body=(0, 3), head=(0, 5),
                 face=(G.face(G.BR_ANGRY, eyes, FF.M_PRESS), G.X0, G.Y0),
                 spikes=PZ.lerp_spikes(PZ.SP_DROOP, PZ.SP_TIGHT if hasattr(PZ, 'SP_TIGHT') else PZ.SP_IDLE, 0.0))


def spindle(half_w, y0=2, y1=94, cx=48):
    """A keylined vertical spindle: lavender shaded as a cylinder lit from the left, a gold core
    down its middle, the top gold like the crest's tips. It runs y0..y1 with a one-texel point at
    each end, so its keyline lands on row 1 (the approved headroom) and row 95 (his feet)."""
    part = {}
    for y in range(y0, y1 + 1):
        t = (y - y0) / float(y1 - y0)
        w = max(0.5, half_w * (math.sin(math.pi * min(1.0, max(0.0, t))) ** 0.6))
        for x in range(int(math.floor(cx - w)), int(math.ceil(cx + w)) + 1):
            s = (x - cx) / max(w, 0.5)
            if abs(s) > 1.0:
                continue
            gold = t < 0.18
            if abs(s) < 0.2 and not gold:
                k = 'b'
            elif gold:
                k = 'a' if s < -0.3 else ('b' if s < 0.3 else 'c')
            else:
                k = 'A' if s < -0.55 else ('B' if s < -0.1 else ('C' if s < 0.45 else 'D'))
            part[(x, y)] = k
    return part


def streak_fig(half_w):
    part = spindle(half_w)
    cv = B.Canvas(96, 96)
    cv.stamp(part, outline=True)
    return cv.px


class _PxFig:
    """A frame given directly as pixels (the streak frames), shaped like a Fig for the export."""

    def __init__(self, px):
        self._px = px
        self.fx = set()
        self.anchors = {}


def figs():
    return [squash(), _PxFig(streak_fig(7.0)), _PxFig(streak_fig(2.2)),
            _PxFig(streak_fig(2.6)), _PxFig(streak_fig(6.0)), squash(land=True)]


def px_of(f):
    return B.clip(dict(f._px)) if isinstance(f, _PxFig) else F.px_of(f)


class Teleport:
    NAME = 'matt_teleport'

    @staticmethod
    def figs():
        return figs()
