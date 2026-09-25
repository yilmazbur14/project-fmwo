"""Greyson's fight hands, in the approved convention (gr_hands): structure maps ('k' lines,
's' skin, '@' the anchor, which is skin), shaded afterwards segment by segment under one
hand-wide form lit from the upper left, so a mirrored hand is re-lit rather than flipped. Uses the
approved module's own helpers and never touches its state.

  'open'   the rear V's open hand, fingers spread (ref 27.png): the back of the hand toward us,
           four fingers fanned up, the thumb out toward the head. Drawn as the LEFT hand's map;
           his right hand is the mirror.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402
from gr_muscle import Form, Region, RegionLayer  # noqa: E402

K, gr_hands = B.K, B.gr_hands

OPEN_L = [
    ".kk.kk.kk....",
    "ksskssksskkk.",
    "ksskssksskssk",
    "ksskssksskssk",
    "kssssssssksk.",
    "ksssssssssk..",
    "ksssssssssk..",
    ".ksss@ssskk..",
    "..kssssk.....",
    "..kkkkkk.....",
]

MAPS = {'open': OPEN_L}


def _check():
    for name, rows in MAPS.items():
        w = len(rows[0])
        for i, r in enumerate(rows):
            assert len(r) == w, (name, i, r)
        assert sum(r.count('@') for r in rows) == 1, name


_check()


def hand(name, side, center):
    """The hand `name` on `side` (0 = screen left, 1 = the mirror), its anchor on `center`
    (left-side coordinates; mirrored for side 1). The same shading as gr_hands.fist."""
    px, (ax, ay) = gr_hands._structure(MAPS[name], side)
    cx = int(round(K.AX - center[0])) if side else int(round(center[0]))
    cy = int(round(center[1]))
    placed = {(cx + c - ax, cy + r - ay): ch for (c, r), ch in px.items()}
    skin = [p for p, ch in placed.items() if ch == 's']
    xs = [p[0] for p in skin]
    ys = [p[1] for p in skin]
    form = Form(ellipsoid=((min(xs) + max(xs)) / 2.0 - 0.5, (min(ys) + max(ys)) / 2.0 - 0.5,
                           (max(xs) - min(xs)) / 2.0 + 2.0, (max(ys) - min(ys)) / 2.0 + 2.0))
    regions = [Region('seg%d' % i, comp, amp=1.2, round_px=1.6, cast=0, depth=0)
               for i, comp in enumerate(gr_hands._components(skin))]
    shaded = RegionLayer(form, regions).shade(cuts=gr_hands.CUTS, lines=False)[0]
    out = {p: 'k' for p, ch in placed.items() if ch == 'k'}
    out.update(shaded)
    return out
