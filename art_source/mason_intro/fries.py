"""Loose french fries on the floor: the bait trail for Mason's entrance.

Mason is lured into the arena by a line of dropped fries and eats his way along
it.  These are the pieces the intro lays down - loose fries on the mat, not a
carton.  The carton is props.fries() over in mason_nuggets/rig/props.py and
these came out of it: the same YEL body with YEL_MID separating one fry from
the next, and the carton's own RED / RED_HI reused as ketchup.

FRAME CONTRACT
  fry_trail.png - 7 frames of 32x16, hframes = 7, vframes = 1.
  Every piece is centred on texel (16, 8), so a Sprite2D with the default
  centred origin drops it exactly on the floor point it is placed at.  Nothing
  reaches the frame border with anything but keyline, so no piece is clipped.

  0 fry_a    one fry, bent, lying across the line   the workhorse of the trail
  1 fry_b    one fry, steeper and shorter           so a repeat is not obvious
  2 pair     two fries crossed
  3 scatter  three fries and crumbs                 a dropped handful
  4 smear    one fry dragged through ketchup        breaks up the yellow line
  5 eaten_s  a broken bit and crumbs, small         what 0-1 leave behind
  6 eaten_w  two broken bits and crumbs, wide       what 2-4 leave behind

  flip_h is safe on any of them and doubles the variety.  These are lit from
  above, so mirroring moves only the one darkened cut end.  flip_v is not: it
  would put the lit face of every fry against the mat.

SIZE
  At SCALE 3 a frame is 96x48 screen px and a single fry is 22 texels long by 6
  across - 66 x 18 screen px, a little longer than one of Mason's feet, which
  measure 18 texels on mason_sheet.png.  That is a big fry.  A fry drawn to his
  actual scale would be three texels long, which is a crumb, and food already
  runs oversized in this game - a chicken nugget falls as a meteor.  Under about
  four texels of thickness the keyline is more than half the object and the
  yellow stops reading as food at all.

LIGHT AND GROUNDING
  Mason's own key light, rig._L = (-0.50, -0.62, 0.60): up and to the left.  A
  fry is a prism, so across its four texels it takes the yellow ramp
  props.yellow_colour() already gives a yellow limb - two rows of YEL on the lit
  face, YEL_MID down the side, YEL_DEEP along the edge that meets the mat - and
  the cut end facing away from the light drops one further band.

  Nothing here carries a cast shadow.  That is the convention the rest of the
  floor props follow: poo_bomb sits on the mat with no shadow at all, the one
  shadow in Mason's art (mason_leap_shadow) is a separate sprite for when he is
  off the ground, and the arena mat is a flat green with no value structure for
  a shadow to sit in.  What grounds a fry instead is that it is drawn squashed
  into the floor plane - short, thick and foreshortened rather than seen from
  the side - with the YEL_DEEP contact edge sitting directly on the black
  keyline along its lower side.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'mason'))

from rig import (BLACK, YEL, YEL_MID, YEL_DEEP, RED, RED_HI,  # noqa: E402
                 hex2rgba, LX, LY)

FW, FH = 32, 16
CX, CY = 16.0, 8.0
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# The light flattened into the floor plane, normalised.  LX, LY come straight
# from Mason's rig so this can never drift away from the sheet's lighting.
_l = math.hypot(LX, LY)
L2 = (LX / _l, LY / _l)

HALF = 2.0              # half-thickness of a fry: four texels across, one per ramp band
RAMP = (YEL, YEL, YEL_MID, YEL_DEEP, YEL_DEEP)


# ----------------------------------------------------------------- grid helpers
def blank():
    return [[(0, 0, 0, 0)] * FW for _ in range(FH)]


def put(g, x, y, col):
    if 0 <= x < FW and 0 <= y < FH:
        g[y][x] = hex2rgba(col) if isinstance(col, str) else col


def opaque(g, x, y):
    return 0 <= x < FW and 0 <= y < FH and g[y][x][3] != 0


def outline(g, mask):
    """1px pure black on every texel sharing an edge with the mask.

    4-neighbour, not 8: an 8-neighbour keyline runs four and five texels long
    across a shallow diagonal and at SCALE 3 the black jacket swallows the food.
    Mason's keyline is #000000 and nothing else - it is NOT Computah's #0C111A."""
    for (x, y) in mask:
        for dx, dy in N4:
            if (x + dx, y + dy) not in mask:
                put(g, x + dx, y + dy, BLACK)


# ------------------------------------------------------------------------- fry
def fry_mask(pts, half=HALF):
    """Texels within `half` of a polyline.  Two points give a straight fry,
    three a bent one - fries are cut, fried and dropped, not extruded, and the
    kink is most of what stops a loose fry reading as a yellow dash.

    Returns {texel: (distance along, offset across)} where the offset is +1 on
    the side facing the key light and -1 on the side lying against the mat."""
    segs = []
    run = 0.0
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        vx, vy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(vx, vy)
        ux, uy = vx / ln, vy / ln
        nx, ny = -uy, ux
        if nx * L2[0] + ny * L2[1] < 0:          # +n always points into the light
            nx, ny = -nx, -ny
        segs.append((i, a, ln, (ux, uy), (nx, ny), run))
        run += ln
    last = len(segs) - 1
    mask = {}
    for y in range(FH):
        for x in range(FW):
            px, py = x + 0.5, y + 0.5
            best = None
            for (i, a, ln, (ux, uy), (nx, ny), base) in segs:
                dx, dy = px - a[0], py - a[1]
                proj = dx * ux + dy * uy
                s = max(0.0, min(ln, proj))
                d = math.hypot(px - (a[0] + s * ux), py - (a[1] + s * uy))
                # Square-cut ends.  A plain distance-to-segment gives a capsule,
                # and a capsule at this size reads as a sausage; a fry is cut off
                # a potato with a blade and both ends are flat.
                if (i == 0 and proj < -0.5) or (i == last and proj > ln + 0.5):
                    continue
                if best is None or d < best[0]:
                    best = (d, base + s, (dx * nx + dy * ny) / half)
            if best is not None and best[0] <= half:
                mask[(x, y)] = best[1:]
    # The cut end facing away from the key light drops a band.  Not on a broken
    # bit two texels long, where one end is half the piece.
    ax, ay = pts[0]
    bx, by = pts[-1]
    along = (bx - ax) * L2[0] + (by - ay) * L2[1]
    end = None if run < 3.0 else (run if along < 0 else 0.0)
    return mask, run, end


def draw_fry(g, pts, half=HALF):
    """Keyline first, then the ramp across the fry's width.

    Fries are laid back to front, so one dropped later cuts its own keyline into
    the one under it and reads as lying on top rather than fused to it."""
    mask, _, dark_end = fry_mask(pts, half)
    outline(g, set(mask))
    paint_fry(g, mask, dark_end)
    return set(mask)


def paint_fry(g, mask, dark_end):
    """The ramp across a fry, four texels of it: the YEL / YEL_MID / YEL_DEEP
    cylinder props.yellow_colour() gives a yellow limb, with the lit face two
    rows wide so a fry reads as food rather than as a keyline with a filling.

    Three texels across was tried first and it forced one row per tone with no
    highlight to speak of, and 43% of the sheet came out keyline - a stick that
    thin is mostly perimeter."""
    for (x, y), (s, u) in mask.items():
        band = 0 if u > 0.50 else (1 if u > 0.0 else (2 if u > -0.50 else 3))
        if dark_end is not None and abs(s - dark_end) < 0.9:
            band += 1                    # the cut end pointing away from the key
        put(g, x, y, RAMP[min(band, 4)])


# ------------------------------------------------------------------ loose bits
def crumbs(g, pts, col=YEL_MID):
    """Bare unoutlined texels, the way props.nugget() already draws its crumbs.
    A crumb with a keyline round it would be eight black texels to one of food."""
    for (x, y) in pts:
        put(g, x, y, col)


def chunk(g, cx, cy, ln=3.2, half=1.5):
    """A broken-off bit of fry: a keylined nub two or three texels across, small
    enough that the size alone says fragment.  A 32-texel frame has no room for
    a bite mark that reads - a one-texel notch on a stub is three screen pixels
    at SCALE 3 - so the leftovers are broken pieces rather than gnawed ends."""
    return draw_fry(g, [(cx - ln / 2, cy + 0.3), (cx + ln / 2, cy - 0.3)], half)


def ketchup(g, spans, fpts):
    """A fry lying in a drag of ketchup, drawn as one object.

    Outlining the smear and then the fry separately puts two keylines back to
    back through the middle of the piece and it reads as a fry parked beside a
    red slug.  So the silhouette of the two together takes one keyline, and the
    fry only gets an edge of its own where it actually crosses the red.

    `spans` is the smear as {row: (x0, x1)} inclusive - hand-drawn, because a
    formula gives a smear an even edge and a drag does not have one.  It is
    shaded exactly as the carton in props.fries() is: RED_HI on the three
    columns nearest the key light, RED on the rest."""
    bmask = {(x, y) for y, (a, b) in spans.items() for x in range(a, b + 1)}
    fmask, _, dark_end = fry_mask(fpts)
    outline(g, bmask | set(fmask))
    left = min(x for (x, _) in bmask)
    for (x, y) in bmask - set(fmask):
        put(g, x, y, RED_HI if x - left <= 2 else RED)
    for (x, y) in fmask:
        for dx, dy in N4:
            if (x + dx, y + dy) in bmask and (x + dx, y + dy) not in fmask:
                put(g, x + dx, y + dy, BLACK)
    paint_fry(g, fmask, dark_end)


# ---------------------------------------------------------------------- frames
def fry_a():
    """One fry, lying nearly across the line of travel, with a kink in it."""
    g = blank()
    draw_fry(g, [(6.5, 6.0), (16.0, 8.2), (25.5, 8.6)])
    return g


def fry_b():
    """One fry, steeper and shorter: foreshortened, as if pointing away."""
    g = blank()
    draw_fry(g, [(12.5, 12.5), (15.5, 8.0), (19.5, 3.8)])
    crumbs(g, [(24, 10), (8, 6)], YEL_DEEP)
    return g


def pair():
    """Two dropped together.  The steep one crosses the shallow one near the
    middle and all four ends stay clear of the crossing, so it reads as two
    fries rather than as one bent X-shaped object."""
    g = blank()
    draw_fry(g, [(4.0, 9.6), (15.0, 10.8), (26.0, 10.0)])
    draw_fry(g, [(11.0, 13.8), (15.5, 8.8), (20.0, 3.4)])
    return g


def scatter():
    """A dropped handful.  Three angles, back to front, the front two crossing
    the one behind - fries that land together land on each other."""
    g = blank()
    draw_fry(g, [(11.5, 3.2), (17.0, 3.4), (22.5, 4.4)])
    draw_fry(g, [(4.0, 11.4), (10.5, 10.4), (17.0, 10.0)])
    draw_fry(g, [(14.0, 12.6), (19.5, 10.3), (25.5, 8.0)])
    crumbs(g, [(27, 12), (7, 6), (28, 6)], YEL_MID)
    crumbs(g, [(26, 13), (6, 7)], YEL_DEEP)
    return g


def smear():
    """A fry dragged through ketchup.  The smear runs along the trail and the fry
    lies across it, so red shows past both ends and the fry reads as sitting in
    the ketchup rather than beside it.  The thin end is the way it was dragged,
    and the two flecks past it are where it ran out.

    This frame exists to break the line up.  Five yellow stamps laid in a row on
    a green mat make a dotted line; one red one every so often makes a trail."""
    g = blank()
    ketchup(g, {5: (7, 13), 6: (4, 19), 7: (3, 23), 8: (3, 25), 9: (4, 23),
                10: (6, 19), 11: (9, 14)},
            [(8.5, 11.0), (14.0, 8.2), (19.5, 6.0)])
    crumbs(g, [(27, 9), (28, 11)], RED)
    return g


def eaten_s():
    """What one fry leaves: two broken bits and a few crumbs.

    Deliberately quiet.  Mason eats his way up this line and the eye should be
    on him and on the fries still ahead of him, not on the litter behind - a
    residue busy enough to compete would be worse than no residue at all.  What
    it has to do is not be nothing, so the piece does not pop out of existence."""
    g = blank()
    chunk(g, 14.0, 8.6)
    crumbs(g, [(19, 7), (21, 9), (11, 11)], YEL_MID)
    crumbs(g, [(20, 10), (10, 6), (22, 7)], YEL_DEEP)
    return g


def eaten_w():
    """What a pair, a scatter or a smear leaves, over the same footprint."""
    g = blank()
    chunk(g, 10.0, 10.0, ln=3.8)
    chunk(g, 21.0, 6.8, ln=2.6)
    crumbs(g, [(15, 9), (17, 12), (25, 10), (6, 6), (13, 5)], YEL_MID)
    crumbs(g, [(16, 6), (24, 11), (7, 12), (27, 8), (18, 8)], YEL_DEEP)
    return g


FRAMES = [('fry_a', fry_a), ('fry_b', fry_b), ('pair', pair), ('scatter', scatter),
          ('smear', smear), ('eaten_s', eaten_s), ('eaten_w', eaten_w)]

# Which residue a piece leaves when Mason gobbles it.
EATEN = {0: 5, 1: 5, 2: 6, 3: 6, 4: 6}
