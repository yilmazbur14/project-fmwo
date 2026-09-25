"""Matt's dialogue portrait, Assets/Characters/Matt/portrait.png (64x64), derived from his own
approved frame 0 (Assets/Characters/Matt/matt.png) rather than drawn beside it.

balloon.gd shows it at 128x128; bust framing, the shoulders running off the bottom edge, like
every other portrait.

THE METHOD (the cast's: Josh's, Jordan's)
  1. His own pixels: approved frame 0, rebuilt by the rig and checked against the shipped sheet,
     cropped at x23..73, y6..56: 51 source pixels centred on his anchor column x48.
  2. Scaled 5:4 (mi_resample, the cast's never-blend resampler generalised from 3:2): every source
     pixel lands on exactly one output pixel and each block of four gets one 'between' pixel that
     copies a neighbour. WHY 1.25x AND NOT THE CAST'S 1.5x: Matt's crest is as tall as his face. At
     1.5x a 64 px window holds 43 source rows, which is either the face or the yellow spike tips,
     never both, and the tips are his Exploud crest. At 1.25x the window runs from the inner tips to
     his shoulders, and his face comes out ~31 px wide, where the cast's portraits sit (Josh 33,
     Jordan 33). The centre tip is trimmed at the top edge, as Carter's crest is.
  3. A one-pixel rim-light pass: a lit edge where a shape meets its keyline above, a dark edge
     where it meets one below, one ramp step each.
  4. Hand detail the 96 px sprite had no room for, all in his own palette (see DETAIL below).

    python mi_portrait.py            # build into the scratchpad, measure, round-trip the .aseprite
    python mi_portrait.py --ship     # ...then write Assets/Characters/Matt/portrait.png + .aseprite
"""
import os
import shutil
import subprocess
import sys
import tempfile

import mi_base as B
import mi_resample as RS
from PIL import Image

ASSET = os.path.join(B.ASSETS, 'portrait')
W = H = 64
SX0, SY0, N = 23, 6, 51            # the window in frame 0; 5:4 of 51 is 64
P_, Q_ = 5, 4

RAMP_OF = {}
for _r in B.pal.RAMPS.values():
    for _k in _r:
        RAMP_OF[_k] = _r


def box(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def rim_pass(px, keep):
    """1px lit edge where a shape meets its keyline (or the outside) above, 1px dark edge where it
    meets one below, one ramp step each way (Matt's ramps run light -> dark). `keep` is left alone."""
    todo = {}
    for (x, y), k in px.items():
        if k not in RAMP_OF or (x, y) in keep:
            continue
        up, dn = px.get((x, y - 1)), px.get((x, y + 1))
        up_k = up in ('k', None)
        dn_k = dn in ('k', None)
        if up_k and not dn_k:
            todo[(x, y)] = B.LIGHTER[k]
        elif dn_k and not up_k:
            todo[(x, y)] = B.DARKER[k]
    px.update(todo)


def rim_keep():
    """The face keeps the sprite's own values: brows, eyes, nose, grin and the ears' bowls."""
    keep = set()
    for b in (
        (16, 33, 49, 40),        # brows and eyes
        (28, 38, 36, 47),        # nose
        (22, 49, 44, 56),        # the grin
        (10, 36, 17, 47),        # near ear
        (47, 36, 55, 47),        # far ear
    ):
        keep |= box(*b)
    return keep


def base():
    """Steps 1-3: frame 0's window, scaled, rim-lit."""
    px = RS.resample(B.approved_frame_px(0), SX0, SY0, N, P_, Q_)
    rim_pass(px, rim_keep())
    return px


# ---------------------------------------------------------------------------------------- DETAIL
# Step 4, in portrait coordinates (0..63), all over the tones already there.
HAIR = set('hijl')
SKIN = set('123456')
YEL = set('abcde')

# The locks under the crest: a black parting running up from the hairline into the V between each
# pair of spikes, and a lit strand along the next lock's edge toward the light (its left side).
PARTINGS = [
    [(15, 27), (17, 22), (19, 17), (21, 14)],     # outer-left / inner-left
    [(23, 28), (25, 22), (26, 16), (27, 11)],     # inner-left / centre
    [(37, 28), (37, 22), (37, 16), (37, 11)],     # centre / inner-right
    [(45, 27), (46, 22), (46, 17), (45, 14)],     # inner-right / outer-right
]
LOCK_SHINE = [
    [(16, 27), (18, 22), (20, 18)],
    [(24, 28), (26, 22), (27, 17)],
    [(38, 27), (38, 22), (38, 17)],
    [(46, 26), (47, 22)],
]
# the short sides combed back: a parting and a lit strand on each
SIDE_PARTINGS = [
    [(13, 31), (15, 29)],
    [(50, 31), (51, 29)],
]
SIDE_SHINE = [
    [(14, 32), (16, 30)],
]

# Each ear as its own shape: the helix lit on its outer rim, the bowl shaded down to the canal.
EAR_L = [
    (37, 10, "k122i"),
    (38, 10, "k2333"),
    (39, 10, "k2443"),
    (40, 10, "k2453"),
    (41, 10, "k2453"),
    (42, 10, "k3343"),
    (43, 10, "k3333"),
]
EAR_R = [
    (38, 49, "4344k"),
    (39, 49, "4454k"),
    (40, 49, "4554k"),
    (41, 49, "4654k"),
    (42, 49, "4644k"),
    (43, 49, "444kk"),
]


def pline(px, pts, key, only):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for q in B.line(x0, y0, x1, y1):
            if px.get(q) in only:
                px[q] = key


def patch(px, edits):
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            if ch == '.':
                px.pop((x, y), None)
            elif ch != '_':
                px[(x, y)] = ch
            x += 1


def collar_ribs(px):
    """The ribbed collar: every other column one step darker across the band, as the rig ribs the
    cuffs, only on the yellow band below the chin."""
    for (x, y), k in list(px.items()):
        if k in YEL and 57 <= y <= 62 and 20 <= x <= 48 and x % 2 == 0:
            px[(x, y)] = B.DARKER[k]


def build():
    px = base()
    for ln in PARTINGS:
        pline(px, ln, 'k', HAIR)
    for ln in LOCK_SHINE:
        pline(px, ln, 'l', set('hij'))
    for ln in SIDE_PARTINGS:
        pline(px, ln, 'k', HAIR)
    for ln in SIDE_SHINE:
        pline(px, ln, 'j', set('hi'))
    patch(px, EAR_L)
    patch(px, EAR_R)
    collar_ribs(px)
    return px


def build_image():
    return B.image(build(), W, H)


def sprite_crop():
    f0 = B.approved_frame_px(0)
    return {(x - SX0, y - SY0): k for (x, y), k in f0.items()
            if SX0 <= x < SX0 + N and SY0 <= y < SY0 + N}


def measure(im):
    crop = B.image(sprite_crop(), N, N)
    s, p = B.stats(crop), B.stats(im)
    f0 = B.stats(B.approved_sheet().crop((0, 0, 96, 96)))
    print('portrait.png                  %4d px  black %4.1f%%  colours %d' % (p['opaque'], 100 * p['black'], p['colours']))
    print('same crop of frame 0 (1x)     %4d px  black %4.1f%%  colours %d' % (s['opaque'], 100 * s['black'], s['colours']))
    print('  frame 0 whole               %4d px  black %4.1f%%  colours %d' % (f0['opaque'], 100 * f0['black'], f0['colours']))
    return p, s


if __name__ == '__main__':
    import mi_view as V
    px = build()
    im = B.image(px, W, H)
    measure(im)
    V.save(V.row([V.label(V.up(B.image(base(), W, H), 6), 'base'), V.label(V.up(im, 6), 'detail')]),
           'portrait_detail.png')
    V.save(V.ruled(im.crop((0, 0, 64, 34)), 16, 0, 0), 'portrait_top.png')
    V.save(V.ruled(im.crop((0, 28, 64, 64)), 16, 0, 28), 'portrait_bottom.png')
