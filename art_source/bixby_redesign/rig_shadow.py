"""Shadows for the redesign, 192x48 per frame, solid black (the fight sets SHADOW_ALPHA), centred on
(96, 25) as BixbyBeastArtLayout.SHADOW_CENTRE. Built as top-down footprints like the approved ones
(art_source/bixby_beast/shadow.py, anim_shadows.py), refitted to the new silhouette: bigger heads,
tattered wings, the tail out to the left.

bixby_beast_shadow.png         4 frames, one per hover frame (the span breathes with the flap)
bixby_beast_shadow_ground.png  0 standing / crouched, 1 spent with the wings flat on the floor,
                               2-3 normal Bixby and Bixby with Liam (not the beast: kept exactly)
"""
import os

from PIL import Image

from pal import ellipse, poly
from shapes import chain

SW, SH = 192, 48
CX, CY = 96, 25
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OLD_GROUND = os.path.join(ROOT, 'Assets', 'Characters', 'Bixby', 'bixby_beast_shadow_ground.png')

# wing span per hover frame: 0 up, 1 level on the downstroke (widest), 2 down, 3 rising
SPANS = [0.9, 1.0, 0.93, 0.96]


def tattered_wing(side, half, y_lead=-9, droop=0):
    """One wing's footprint: a leading edge out to the tip, then a torn trailing edge back in."""
    s = side
    pts = [(CX - 18 * s, CY - 7), (CX - half * 0.55 * s, CY - 12), (CX - half * s, CY + y_lead)]
    # trailing edge: finger tips with torn notches between, back to the body
    tips = [(0.95, 2), (0.74, 8), (0.52, 11), (0.32, 11)]
    prev = (half, y_lead)
    for fx, fy in tips:
        mx, my = (prev[0] + half * fx) / 2, (prev[1] + fy) / 2
        pts.append((CX - (mx + 2) * s, CY + my - 3 + droop))       # notch in
        pts.append((CX - (mx - 1) * s, CY + my + droop))
        pts.append((CX - half * fx * s, CY + fy + droop))          # the finger tip
        prev = (half * fx, fy)
    pts.append((CX - 16 * s, CY + 7))
    return poly(pts)


def close(m):
    """Round off single-pixel nicks (dilate then erode, 8-neighbour), then fill enclosed holes."""
    dil = set(m)
    for (x, y) in m:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                dil.add((x + dx, y + dy))
    out = set()
    for (x, y) in dil:
        if all((x + dx, y + dy) in dil for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            out.add((x, y))
    # anything the outside can't reach is a hole: fill it
    outside = set()
    stack = [(-1, -1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in outside or (x, y) in out or not (-1 <= x <= SW and -1 <= y <= SH):
            continue
        outside.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return {(x, y) for x in range(SW) for y in range(SH) if (x, y) not in outside}


def body_air():
    m = ellipse(CX, CY + 1, 30, 12.5)
    # three heads toward the player (the bottom of the shadow); the middle one biggest
    for dx, rx, ry in ((-26, 9, 5.5), (0, 11, 6.5), (26, 9, 5.5)):
        m |= ellipse(CX + dx, CY + 9, rx, ry)
    # the tail trailing out behind to the left, the flame tip a blob at its end
    m |= chain([(CX - 8, CY - 8), (CX - 24, CY - 14), (CX - 40, CY - 15), (CX - 52, CY - 12)], 3.2, 1.2)
    m |= ellipse(CX - 55, CY - 12, 3.4, 2.6)
    return m


def air(k):
    m = body_air() | tattered_wing(1, 88 * k) | tattered_wing(-1, 88 * k)
    return close(m)


def ground(k):
    if k == 0:           # standing or crouched: body, paws out front, tail curled on the floor, folded wings
        m = ellipse(CX, CY, 34, 11)
        for dx in (-30, 30):
            m |= ellipse(CX + dx, CY + 6, 9, 4.5)
        for dx in (-62, 62):
            m |= ellipse(CX + dx, CY + 3, 8, 4)
        m |= ellipse(CX - 50, CY - 3, 15, 7) | ellipse(CX + 50, CY - 3, 15, 7)
        m |= chain([(CX - 26, CY - 3), (CX - 46, CY - 8), (CX - 66, CY - 6), (CX - 80, CY - 1)], 3.4, 1.4)
    else:                # spent: flat out, the wings spread over the floor
        m = ellipse(CX, CY, 37, 12)
        m |= tattered_wing(1, 92, y_lead=-2, droop=2) | tattered_wing(-1, 92, y_lead=-2, droop=2)
        m |= chain([(CX - 26, CY - 3), (CX - 46, CY - 6), (CX - 66, CY - 4), (CX - 80, CY + 1)], 3.4, 1.4)
    return close(m)


def image(mask):
    im = Image.new('RGBA', (SW, SH), (0, 0, 0, 0))
    for (x, y) in mask:
        if 0 <= x < SW and 0 <= y < SH:
            im.putpixel((x, y), (0, 0, 0, 255))
    return im


def air_frames():
    return [image(air(k)) for k in SPANS]


def ground_frames():
    """Frames 0-1 refitted; 2-3 (normal Bixby, Bixby with Liam) copied from the approved sheet. The
    approved sheet is snapshotted into the scratchpad before anything overwrites it."""
    import view
    snap = os.path.join(view.SCRATCH, 'all_sheets', 'old_shadow_ground_snapshot.png')
    if not os.path.exists(snap):
        Image.open(OLD_GROUND).save(snap)
    old = Image.open(snap).convert('RGBA')
    return [image(ground(0)), image(ground(1)),
            old.crop((2 * SW, 0, 3 * SW, SH)), old.crop((3 * SW, 0, 4 * SW, SH))]
