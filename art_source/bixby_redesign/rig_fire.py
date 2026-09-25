"""Fire-breath frames (192x256): the rig's body with the approved streams, recoloured into the
redesign's ember ramp.

The streams are the ones BixbyBeastArtLayout.FIRE_OUTLINES were traced round, lifted pixel for pixel
from the old sheet (only fire-coloured pixels inside each traced outline, so no old body comes with
them) and recoloured. The side heads swing in so their throats sit on the streams' old origins
(about (50, 85) and (141, 85)), and the middle maw is open over the middle stream's (96, 76). So the
fire hitboxes, FIRE_DRAWN and FIRE_GROUND_CONTACT stay valid.
"""
import math
import os
import re

from PIL import Image

import rig
import rig_poses as RP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OLD_FIRE = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby', 'bixby_beast_firebreath.png')
LAYOUT = os.path.join(ROOT, 'Scripts', 'BixbyBeastArtLayout.gd')

# the approved fire's seven tones -> the redesign's ramp
RECOLOUR = {(0xFF, 0xFF, 0xFF): 'w', (0xFF, 0xF7, 0xA0): 'Y', (0xFB, 0xF2, 0x36): 'P', (0xF5, 0x8A, 0x38): 'p',
            (0xDF, 0x71, 0x26): 'N', (0xAC, 0x32, 0x32): 'n', (0x6E, 0x1E, 0x22): 'r'}

_CACHE = {}


def outlines():
    """FIRE_OUTLINES from the layout script (read only)."""
    src = open(LAYOUT, encoding='utf-8').read()
    out = {}
    for n in (1, 2):
        m = re.search(r'\b%d: \[(.*?)\]' % n, src, re.S)
        out[n] = [(float(a), float(b)) for a, b in re.findall(r'Vector2\(([\d.]+), ([\d.]+)\)', m.group(1))]
    return out


def stream(frame):
    """{(x, y): key} of the approved stream on firebreath frame 1 or 2, recoloured.

    The approved stream must be read from the approved sheet, so the first call snapshots it; once the
    redesigned sheet has been written over it, the snapshot in the scratchpad is used instead."""
    if frame in _CACHE:
        return _CACHE[frame]
    from pal import poly
    import view
    snap = os.path.join(view.SCRATCH, 'all_sheets', 'old_firebreath_snapshot.png')
    if not os.path.exists(snap):
        Image.open(OLD_FIRE).save(snap)
    im = Image.open(snap).convert('RGBA')
    mask = poly(outlines()[frame])
    # the outline was traced to within a texel, so a few embers and tongue tips escape it: below the
    # body (y >= 150, where no old body fire colours are) take fire pixels up to 3px outside it too
    grown = set()
    for (x, y) in mask:
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                if y + dy >= 150:
                    grown.add((x + dx, y + dy))
    mask = mask | grown
    f = im.crop((frame * 192, 0, frame * 192 + 192, 256))
    out = {}
    for (x, y) in mask:
        if 0 <= x < 192 and 0 <= y < 256:
            c = f.getpixel((x, y))
            if c[3] and c[:3] in RECOLOUR:
                out[(x, y)] = RECOLOUR[c[:3]]
    _CACHE[frame] = out
    return out


def throat_glow(cx, cy, r=4.2):
    def f(cv, P):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                d = math.hypot(x - cx, (y - cy) * 1.1)
                if d <= r and cv.px.get((x, y)) in ('k', 'q', None):
                    cv.px[(x, y)] = 'Y' if d < 1.4 else 'P' if d < 2.4 else 'p' if d < 3.3 else 'N'
    return f


SIDE_IN = dict(dx=-11, dy=-3)       # throats onto the old side-stream origins


def body(frame):
    """0 windup: all three maws alight; 1-2 breathing (the stream goes on top)."""
    P = rig.pose(RP.SIGNATURE, H=256)
    P['side'] = dict(mouth='roar', low_dy=3, **SIDE_IN)
    P['neck'] = ((118, 98), (142 + SIDE_IN['dx'], 82 + SIDE_IN['dy']))
    P['mid'] = dict(P['mid'])
    if frame > 0:
        P['mid'].pop('fx', None)             # the stream replaces the ember draw
        P['tails_wave'] = 1
    # the side throats (the roar map's throat, moved with the heads)
    tx, ty = 152 + SIDE_IN['dx'], 92 - 4 + SIDE_IN['dy'] - 3
    P['fx'] = list(P.get('fx', [])) + [throat_glow(tx, ty), throat_glow(191 - tx, ty)]
    return P


def frames():
    out = []
    for fr in (0, 1, 2):
        cv = rig.build(body(fr))
        if fr:
            for q, k in stream(fr).items():
                cv.px[q] = k
        out.append(cv.image())
    return out
