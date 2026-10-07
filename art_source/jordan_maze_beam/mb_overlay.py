"""Greyson's anticipation overlay: his eyes blaze and heat climbs his cannon as the beam charges, and
his levelled muzzle glows while the beam pours out of it.

SPIRIT OVERLAY: 112 x 112 texels a frame, laid exactly over the puppet's spirit sheet
(Assets/Characters/Jordan/Puppets/greyson/greyson_spirit.png, read here, never written): a child
Sprite2D with the puppet sprite's own centring, offset and flip, drawn above it. 8 frames:
  0-2  over spirit frame 0 (arm up), charge stage 1, 2, 3
  3-5  over spirit frame 1 (arm up), charge stage 1, 2, 3
  6-7  over spirit frame 3 (the throw), alternating every 0.05 s through the trace and the hold
Only the changed texels are drawn; every colour is the take's own.
"""
import os

import numpy as np
from PIL import Image

import mb_core as C

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SPIRIT = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'Puppets', 'greyson', 'greyson_spirit.png')
FW = 112
OVERLAY_FRAMES = 8

EYE_BLUE = (0x66, 0xC6, 0xEC)
RED = (0xD2, 0x40, 0x3A)
CRIMSON = (0x9F, 0x1C, 0x2E)
VOID = (0x17, 0x11, 0x1D)
SLATE = (0x3A, 0x41, 0x53)
THROW_MUZZLE = (66, 70)

# eye ramps per pulse: the slit's four texels, outer to inner, and the flare either side
EYES = {
    'a': [(('r', 's', 'h', 's'), None, None), (('s', 'h', 'w', 'h'), 's', None), (('h', 'w', 'w', 'w'), 's', 'r')],
    'b': [(('d', 'c', 'r', 'c'), None, None), (('c', 'r', 'w', 'r'), 'c', None), (('r', 'w', 'w', 'w'), 'r', 'c')],
}
# heat rings climbing the raised barrel, one band of rows per stage, bottom to top
RINGS = [(24, 27), (16, 19), (9, 12)]
RING_KEYS = {'a': ('s', 'r'), 'b': ('b', 'l')}
MUZZLE_KEYS = {'a': ('w', 'h', 's', 'c'), 'b': ('w', 'e', 'b', 'l')}


def _sheet():
    return np.array(Image.open(SPIRIT).convert('RGBA'))


def _frame(sheet, k):
    return sheet[:, k * FW:(k + 1) * FW]


def _eyes(fr):
    """The two eye slits: [(row, [x...]) for the viewer's left eye, then the right]."""
    ys, xs = np.nonzero((fr[..., 0] == EYE_BLUE[0]) & (fr[..., 1] == EYE_BLUE[1]) & (fr[..., 2] == EYE_BLUE[2])
                        & (fr[..., 3] > 0))
    face = [(y, x) for y, x in zip(ys.tolist(), xs.tolist()) if 30 <= y <= 45]
    face.sort(key=lambda p: p[1])
    (yl, xl), (yr, xr) = face[0], face[-1]
    return [(yl, [xl - 2, xl - 1, xl, xl + 1]), (yr, [xr + 2, xr + 1, xr, xr - 1])]


def _rgb(fr, y, x):
    return tuple(int(v) for v in fr[y, x, :3])


def overlay(pal, f, take):
    sheet = _sheet()
    g = C.blank(FW, FW)
    if f < 6:
        base = _frame(sheet, 0 if f < 3 else 1)
        stage = f % 3
    else:
        base = _frame(sheet, 3)
        stage = 2
    slit, flare, tip = EYES[take][stage]
    for (y, xs), side in zip(_eyes(base), (-1, 1)):
        # xs runs outer to inner
        for x, k in zip(xs, slit):
            g[y, x] = pal[k]
        if flare:
            g[y, xs[0] + side] = pal[flare]
            g[y, xs[-1] - side] = pal[flare] if stage == 2 else g[y, xs[-1] - side]
        if tip:
            g[y, xs[0] + 2 * side] = pal[tip]
            g[y - 1, xs[2]] = pal['h' if take == 'a' else 'e']
    if f < 6:
        # the heat ring for this stage climbing the barrel (only its red texels change)
        y0, y1 = RINGS[stage]
        hot, warm = RING_KEYS[take]
        for y in range(y0, y1):
            for x in range(70, 96):
                if base[y, x, 3] == 0:
                    continue
                c = _rgb(base, y, x)
                if c == RED:
                    g[y, x] = pal[hot]
                elif c == CRIMSON:
                    g[y, x] = pal[warm]
    else:
        # the levelled muzzle: its dark mouth glowing out from the middle
        mx, my = THROW_MUZZLE
        keys = MUZZLE_KEYS[take]
        grow = 0.0 if f == 6 else 0.8
        for y in range(56, 80):
            for x in range(56, 76):
                if base[y, x, 3] == 0:
                    continue
                if _rgb(base, y, x) not in (VOID, SLATE):
                    continue
                d = ((x + 0.5 - (mx + 0.5)) ** 2 + (y + 0.5 - (my + 0.5)) ** 2) ** 0.5
                k = keys[0] if d < 2.2 + grow else keys[1] if d < 3.6 + grow else keys[2] if d < 4.8 + grow else keys[3]
                g[y, x] = pal[k]
    return g


def overlay_a(pal, f):
    return overlay(pal, f, 'a')


def overlay_b(pal, f):
    return overlay(pal, f, 'b')
