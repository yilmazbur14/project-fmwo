"""The Four-Element Staff (new, invented for this phase).

A pale ash-wood staff with a steel-shod butt and a round ring head set with four element gems - AIR
(white) at the crown, FIRE (orange) and WATER (blue) at the sides, EARTH (green) at the throat - around
a glowing orb. The orb takes the colour of the element he is bending, so it doubles as the attack tell:
blue before the waves, white before the gust, green before the pillar.

The head is one hand-authored 17x16 sprite that never rotates (it is a ring, so it reads the same at any
angle); the shaft is generated along any line and tucks under the ring. That lets the same design stand
upright, rise overhead, thrust, flail, or lie on the floor. Palette keys come from le_rig.PAL; the orb
uses placeholders ( ) [ ! that orb_map() resolves per element.
"""
import math

import numpy as np

import le_rig as R

HEAD = [
    "........#........",   # 0
    "......##W##......",   # 1  AIR gem (crown)
    "....###wwv###....",   # 2
    "...#211#v#223#...",   # 3
    "..#21122#22233#..",   # 4
    "..#1122###2233#..",   # 5
    ".##122#!()#233##.",   # 6
    ".#l#2#(((()#3#C#.",   # 7  WATER gem / FIRE gem
    "#bb5##)(()[##667#",   # 8
    ".#5#3#))))[#4#7#.",   # 9
    ".##233#[[[#344##.",   # 10
    "..#2333###3344#..",   # 11
    "..#33333#33444#..",   # 12
    "...#334#A#344#...",   # 13 EARTH gem (throat)
    "....###889###....",   # 14
    "......##9##......",   # 15
]
HEAD_C = (8, 8)          # the ring's centre pixel inside the block
RING_R = 7.5             # outer radius incl. keyline

ORB = {  # glint, core, mid, rim - his palette plus ONE new hue per element (b, 8, 6)
    'neutral': ('W', 'W', 'w', 'v'),
    'water': ('W', 'l', 'b', 'q'),
    'earth': ('W', 'W', '8', 'Y'),
    'air': ('W', 'W', 'w', 'l'),
    'fire': ('W', 'W', '6', 'n'),
}
# The wood is his own warm ramp (s d f g), so the staff adds no colours: golden oak against the jacket.
WOODMAP = {'1': 's', '2': 'd', '3': 'f', '4': 'g'}
# Gem darks and glints borrowed from his palette: water dark = his indigo q, fire dark = his jacket
# shadow n, earth dark = his slate Y, glints = his sparkle c.
GEMMAP = {'C': 'W', 'A': 'W', '5': 'q', '7': 'n', '9': 'Y'}
WOOD = 'gfds'
WOOD_TH = [0.3, 0.55, 0.8]
HALF = 2.2               # shaft half width: 5 px with keylines, 3 interior tones on a vertical shaft


def orb_map(rows, orb):
    g, core, mid, rim = ORB[orb]
    tr = str.maketrans(dict({'!': g, '(': core, ')': mid, '[': rim}, **WOODMAP, **GEMMAP))
    return [r.translate(tr) for r in rows]


def head_canvas(orb='neutral'):
    return R.from_text('\n'.join(orb_map(HEAD, orb)))


def shaft(L, butt, head_c, ferrule=True, hide_from=None, knots=True):
    """Generated shaft from the butt point to the head centre (float coords, any angle) into canvas L.
    hide_from: (s0) texels from the butt that are hidden (e.g. inside his mouth) - not drawn."""
    h, w = L.shape
    X, Y = R.centres(w, h)
    bx, by = butt
    hx_, hy_ = head_c
    ln = math.hypot(hx_ - bx, hy_ - by)
    ux, uy = (hx_ - bx) / ln, (hy_ - by) / ln
    nx, ny = -uy, ux
    s = (X - bx) * ux + (Y - by) * uy
    t = (X - bx) * nx + (Y - by) * ny
    s0 = hide_from if hide_from is not None else -0.5
    m = (s >= s0) & (s <= ln) & (np.abs(t) <= HALF)
    tt = np.clip(t / HALF, -1, 1)
    v = R.lambert((nx * tt, ny * tt, np.sqrt(np.clip(1 - tt * tt, 0, None))))
    wood = R.quant(v, WOOD, WOOD_TH)
    if knots:
        k = ((np.floor(s).astype(int) % 13) == 7) & (np.abs(tt) < 0.35)
        wood = np.where(k, 'g', wood)
    R.paint_part(L, m, wood)
    if ferrule and hide_from is None:
        mf = (s >= -0.5) & (s <= 3.4) & (np.abs(t) <= HALF + 0.05)
        R.paint_part(L, mf, np.where(tt < -0.3, 'm', np.where(tt < 0.35, 'M', 'e')))
    return L


def staff(w, h, butt, head_c, orb='neutral', ferrule=True, hide_from=None, head=True):
    """The whole staff into a fresh canvas: shaft first, head centred on head_c (rounded) over it."""
    L = R.blank(w, h)
    shaft(L, butt, head_c, ferrule=ferrule, hide_from=hide_from)
    if head:
        hc = head_canvas(orb)
        R.composite(L, hc, int(round(head_c[0] - 0.5)) - HEAD_C[0], int(round(head_c[1] - 0.5)) - HEAD_C[1])
    return L


def upright(w, h, x_col, y_top, length, orb='neutral', ferrule=True):
    """Vertical staff: shaft centre column x_col (the head's centre column), head block top row y_top."""
    head_c = (x_col + 0.5, y_top + HEAD_C[1] + 0.5)
    butt = (x_col + 0.5, y_top + length - 0.5)
    return staff(w, h, butt, head_c, orb=orb, ferrule=ferrule)


def standalone():
    """Approval sheet frames: the staff upright with each orb state (24x80), plus lying at 30 degrees."""
    out = []
    for o in ('neutral', 'water', 'earth', 'air', 'fire'):
        out.append(upright(24, 80, 11, 3, 74, orb=o))
    return out
