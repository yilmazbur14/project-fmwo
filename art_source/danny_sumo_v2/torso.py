"""The torso as ONE form: traps, chest, belly and flanks inflated together. The pecs, the belly and
the obliques are sculpted on that surface as plateaus of their own outlines (flat-topped, turning at
their edges), so the light flows across one body. Anatomy is drawn with open lines along the
muscles' turning edges - the pecs' lower edge, the sternum, the obliques - not closed outlines.

Every function takes xf, a point transform (x, y) -> (x', y'), so a pose can lean the whole torso;
the shading is run after the transform, so the light stays upper left however the body turns.
"""
import math

from sumo_lib import (spoly, shade, plateau, height_fn, domes, mirror_pts, taper_line, MIR, SKIN)
import sumo_lib as L

CX = 87.5


def ident(p):
    return p


def rot(pivot, deg, shift=(0.0, 0.0)):
    """A pose transform: rotate about pivot by deg (negative leans the top to the viewer's left),
    then shift."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    px_, py_ = pivot

    def f(p):
        dx, dy = p[0] - px_, p[1] - py_
        return (px_ + dx * c - dy * s + shift[0], py_ + dx * s + dy * c + shift[1])

    def inv(p):
        dx, dy = p[0] - shift[0] - px_, p[1] - shift[1] - py_
        return (px_ + dx * c + dy * s, py_ - dx * s + dy * c)
    f.inverse = inv
    return f


def sym(left):
    right = mirror_pts(left[::-1])
    return left + right[1:-1] if left[0][0] == CX else left + right


TRAP = [(87.5, 18), (66, 20), (54, 24.5), (44, 29), (36, 33.5), (31, 39), (40, 46), (60, 48), (87.5, 49)]
FLANK = [(87.5, 36), (58, 38), (49, 44), (46.5, 56), (47, 70), (48, 84), (49, 94), (87.5, 96)]
PEC = [(87, 42), (77, 40), (65, 40.5), (56, 43), (50, 48.5), (47.5, 55.5), (49, 61.5), (54, 66.5),
       (62, 69.5), (72, 70.5), (80, 69), (85.5, 66.5), (87, 64)]
BELLY = [(87.5, 60), (72, 61.5), (61, 65), (54, 71), (51, 78), (51, 84.5), (54, 89.5), (60, 93),
         (68, 95), (78, 96), (87.5, 96.2)]
TRAP_MUSCLE = [(62, 24), (52, 27.5), (42, 32), (35, 36.5), (37, 41), (48, 40), (60, 36), (66, 30)]
OBLIQUE = [(53, 93), (51.5, 87), (51, 80), (52, 73), (54.5, 67.5)]
NAVEL = {(86, 85): '6', (87, 85): '6', (88, 85): '6', (89, 85): '5',
         (86, 86): '3', (87, 86): 'k', (88, 86): 'k', (89, 86): '3',
         (87, 87): '3', (88, 87): '4'}


def P(pts, xf):
    return spoly([xf(p) for p in pts])


def mask(xf=ident):
    m = set()
    for pts in (sym(TRAP), sym(FLANK), sym(BELLY)):
        m |= P(pts, xf)
    m |= P(PEC, xf) | P(mirror_pts(PEC), xf)
    return m


def pec_masks(xf=ident):
    return P(PEC, xf), P(mirror_pts(PEC), xf)


def swell(belly):
    """Breath: the belly grows about the top of its outline (the pecs hold it down), by `belly`
    steps of about a pixel at its hem."""
    if not belly:
        return ident
    sx, sy = 1.0 + 0.014 * belly, 1.0 + 0.028 * belly

    def f(p):
        return (CX + (p[0] - CX) * sx, 60.0 + (p[1] - 60.0) * sy)
    return f


def build(xf=ident, sigma=8.0, bulge=0.7, exposure=0.02, a_pec=0.32, a_belly=0.45, a_trap=0.12, s_pec=2.4,
          s_belly=5.5, low_belly=(87.5, 86.0, 33.0, 16.0, 0.40, 0.7), belly=0):
    """low_belly: a dome (cx, cy, rx, ry, amp, power) that makes the belly protrude most below its
    middle, so its upper two thirds face the light and only a band under the peak turns away.
    belly: breath, see swell()."""
    sw = swell(belly)
    m = set()
    for pts in (sym(TRAP), sym(FLANK)):
        m |= P(pts, xf)
    m |= P([sw(p) for p in sym(BELLY)], xf)
    m |= P(PEC, xf) | P(mirror_pts(PEC), xf)
    pl, pr = pec_masks(xf)
    belly = P([sw(p) for p in sym(BELLY)], xf)
    trap = P(TRAP_MUSCLE, xf) | P(mirror_pts(TRAP_MUSCLE), xf)
    plates = height_fn(plateau(pl | pr, s_pec, a_pec),
                       plateau(belly, s_belly, a_belly),
                       plateau(trap, 3.0, a_trap))
    if low_belly:
        cx, cy = xf(sw(low_belly[:2]))
        dome = domes([(cx, cy) + tuple(low_belly[2:])])
    else:
        dome = (lambda x, y: 0.0)
    part = shade(m, sigma=sigma, bulge=bulge, exposure=exposure, height=lambda x, y: plates(x, y) + dome(x, y),
                 cuts=L.CUTS, wrap=L.SKIN_WRAP)
    return m, part


def lower_edge(mask_):
    """The row of pixels just under a mask, per column: its turning edge as a line."""
    bottom = {}
    for (x, y) in mask_:
        bottom[x] = max(bottom.get(x, y), y)
    return sorted((x, y + 1) for x, y in bottom.items())


def _xp(q, xf):
    x, y = xf(q)
    return (int(round(x)), int(round(y)))


def lines(px, xf=ident, belly=0):
    """Open anatomy lines onto a canvas dict (after the torso is stamped). belly: the breath the
    torso was built with, so the lines on the belly (obliques, navel) ride it."""
    skin = set(SKIN)
    sw = swell(belly)
    bx = (lambda p: xf(sw(p))) if belly else xf
    pl, pr = pec_masks(xf)
    for side, pm in ((1, pl), (-1, pr)):
        edge_px = lower_edge(pm)
        # outer end (towards the armpit) heavy, inner end (at the sternum) single
        xs = [x for x, y in edge_px]
        lo, hi = min(xs), max(xs)
        for (x, y) in edge_px:
            if px.get((x, y)) in skin:
                px[(x, y)] = 'k'
            outer = (x - lo) / max(1, hi - lo) if side < 0 else (hi - x) / max(1, hi - lo)
            if outer > 0.55 and px.get((x, y + 1)) in skin:
                px[(x, y + 1)] = 'k'
            # the shadow the slab throws on the belly under it
            for d in (1, 2) if outer <= 0.55 else (2, 3):
                q = (x, y + d)
                if px.get(q) in skin:
                    px[q] = L.DARKER.get(px[q], px[q])
    # obliques: an open line up the flank from the belt, fading out under the pec
    for side in (1, -1):
        ob = OBLIQUE if side > 0 else [(MIR - x, y) for (x, y) in OBLIQUE]
        taper_line(px, [bx(p) for p in ob], 'k', taper_key='3', taper=4, only=skin)
    # the sternum: a groove between the pecs, dark rather than black, closing in black at its foot
    for y in range(57, 67):
        for x in (87, 88):
            q = _xp((x, y), xf)
            if px.get(q) in skin:
                px[q] = '3' if y < 64 else 'k'
    # the navel, with the lit lip above it
    for q, k in NAVEL.items():
        px[_xp(q, bx)] = k
