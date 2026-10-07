"""The chase-edition box at any angle, drawn so its straight edges stay straight.

Rotating the box's pixel map directly (by shears, or by RotSprite-style sampling) bends its borders
and the black window frame into wobbles and breaks. Here the box is re-drawn from its structure
instead: the flat fills are sampled, the outer keyline is the rotated rectangle's own boundary, the
header and base dividers and the window-frame verticals are ruled as exact straight lines, and the
two pieces of art (the gold star on the header, the plumber in the window) are pasted upright for
small tilts or sampled for big ones.

At 0 degrees it reproduces the rig's box pixel for pixel (checked in _selftest).

Box-local coordinates: u across (0..15), v down (0..21), the pixel (col, row) covering
[col, col + 1) x [row, row + 1). The rig's BOX map sits with its top-left at build (61, 25).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402

BW, BH = 15, 21
MAP = B.rows_of(B.jordan.BOX)
assert len(MAP) == BH and all(len(r) == BW for r in MAP)


def _src(c, r):
    return MAP[r][c] if 0 <= r < BH and 0 <= c < BW else '.'


# The art pasted on top: the star (cols 4..10, rows 1..5) and the plumber (cols 3..11, rows 8..16),
# every non-fill pixel of those boxes.
STAR_BOX = (4, 1, 10, 5)
FIG_BOX = (3, 8, 11, 16)


def _art(box, fillkeys):
    c0, r0, c1, r1 = box
    return {(c, r): _src(c, r) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
            if _src(c, r) not in fillkeys}


STAR_ART = _art(STAR_BOX, 'R')
FIG_ART = _art(FIG_BOX, 'wx')


def _fill_key(u, v):
    """The flat fill under (u, v), with the ruled lines, border and art taken out."""
    c, r = int(math.floor(u)), int(math.floor(v))
    c = min(max(c, 1), BW - 2)
    r = min(max(r, 1), BH - 2)
    if r == 6:                      # the header divider: split it between its neighbours
        r = 5 if v < 6.5 else 7
    if r == 18:
        r = 17 if v < 18.5 else 19
    if 7 <= r <= 17:                # window band
        if c == 2:
            c = 1 if u < 2.5 else 3
        if c == 12:
            c = 13 if u >= 12.5 else 11
        if 3 <= c <= 11:
            k = MAP[r][c]
            return k if k in 'wx' else 'w'
        return MAP[r][c]
    if 1 <= r <= 5:                 # header: flat red between the lit and shaded edges
        if 2 <= c <= 11:
            return 'R'
        return MAP[r][c]
    return MAP[r][c]


def _inside(u, v):
    if not (0 <= u < BW and 0 <= v < BH):
        return False
    if (u < 1 or u >= BW - 1) and (v < 1 or v >= BH - 1):
        return False                # the rounded corners
    return True


def draw(deg, anchor_uv, anchor_xy, art='auto', glint=None):
    """The box turned `deg` degrees clockwise about its local point `anchor_uv`, which lands on the
    build point `anchor_xy`. art: 'upright' pastes the star and the figure unrotated (right for tilts
    of up to about 12 degrees), 'sample' turns them with the box, 'auto' picks by angle.
    glint: an optional (u0, u1) band across the window where the plastic catches the light."""
    th = math.radians(deg)
    c, s = math.cos(th), math.sin(th)
    au, av = anchor_uv
    ax, ay = anchor_xy

    def to_local(X, Y):
        dx, dy = X + 0.5 - ax, Y + 0.5 - ay
        return c * dx + s * dy + au, -s * dx + c * dy + av

    def to_dest(u, v):
        du, dv = u - au, v - av
        return c * du - s * dv + ax, s * du + c * dv + ay

    corners = [to_dest(0, 0), to_dest(BW, 0), to_dest(0, BH), to_dest(BW, BH)]
    x0 = int(math.floor(min(p[0] for p in corners))) - 1
    x1 = int(math.ceil(max(p[0] for p in corners))) + 1
    y0 = int(math.floor(min(p[1] for p in corners))) - 1
    y1 = int(math.ceil(max(p[1] for p in corners))) + 1
    if art == 'auto':
        art = 'upright' if abs(deg) <= 12 else 'sample'

    inside = {}
    for Y in range(y0, y1 + 1):
        for X in range(x0, x1 + 1):
            u, v = to_local(X, Y)
            if _inside(u, v):
                inside[(X, Y)] = (u, v)
    out = {}
    for q, (u, v) in inside.items():
        if art == 'sample':
            k = _src(int(math.floor(u)), int(math.floor(v)))
            out[q] = k if k != '.' else _fill_key(u, v)
        else:
            out[q] = _fill_key(u, v)
    if glint:
        g0, g1 = glint
        for q, (u, v) in inside.items():
            if 3 <= u < 12 and 7 <= v < 18 and out[q] in 'w' and g0 <= u + (v - 7) * 0.5 < g1:
                out[q] = 'x'
    if art == 'upright':
        for (art_map, box) in ((STAR_ART, STAR_BOX), (FIG_ART, FIG_BOX)):
            cu = (box[0] + box[2] + 1) / 2.0
            cv = (box[1] + box[3] + 1) / 2.0
            dxf, dyf = to_dest(cu, cv)
            ox = int(math.floor(dxf - cu + 0.5))
            oy = int(math.floor(dyf - cv + 0.5))
            for (cc, rr), k in art_map.items():
                q = (cc + ox, rr + oy)
                if q in inside:
                    out[q] = k
    if art == 'upright' or deg % 90:
        # the ruled lines: exact straight lines between the rotated end points
        for (ua, va, ub, vb) in ((0.5, 6.5, BW - 0.5, 6.5), (0.5, 18.5, BW - 0.5, 18.5),
                                 (2.5, 6.5, 2.5, 18.5), (12.5, 6.5, 12.5, 18.5)):
            pa, pb = to_dest(ua, va), to_dest(ub, vb)
            for q in B.line(int(math.floor(pa[0])), int(math.floor(pa[1])),
                            int(math.floor(pb[0])), int(math.floor(pb[1]))):
                if q in inside:
                    out[q] = 'k'
    # the border: every inside pixel with a 4-neighbour outside
    for (X, Y) in inside:
        if any(n not in inside for n in ((X + 1, Y), (X - 1, Y), (X, Y + 1), (X, Y - 1))):
            out[(X, Y)] = 'k'
    return out


def _rnd(v):
    return int(math.floor(v + 0.5))


def tilt(deg, anchor_uv, anchor_xy):
    """A small tilt (up to ~12 degrees, clockwise positive) that keeps every row and every column of
    the box intact: rows slide sideways, then columns slide up or down, so the one-pixel gold bars,
    frame lines and border keep their width and just step. Where a row step and a column step meet,
    the one pixel neither covers is filled from the box's own map at that spot."""
    th = math.radians(deg)
    t = math.tan(th)
    au, av = anchor_uv
    ax, ay = anchor_xy
    out = {}

    def place(cc, rr):
        ox = _rnd(-t * (rr + 0.5 - av))
        oy = _rnd(t * (cc + 0.5 - au))
        return (ax + cc - int(au) + ox, ay + rr - int(av) + oy)

    for rr, row in enumerate(MAP):
        for cc, k in enumerate(row):
            if k == '.':
                continue
            # the star and the figure are sheared as plain fill here and pasted upright below, so a
            # step never cuts through them
            if (cc, rr) in STAR_ART:
                k = 'R'
            elif (cc, rr) in FIG_ART:
                k = 'w'
            q = place(cc, rr)
            if q in out:
                raise ValueError('tilt %s: two box pixels land on %s' % (deg, q))
            out[q] = k
    for art_map, box in ((STAR_ART, STAR_BOX), (FIG_ART, FIG_BOX)):
        cu = (box[0] + box[2]) // 2
        cv = (box[1] + box[3]) // 2
        qx, qy = place(cu, cv)
        for (cc, rr), k in art_map.items():
            out[(qx + cc - cu, qy + rr - cv)] = k
    c, s = math.cos(th), math.sin(th)
    xs = [q[0] for q in out]
    ys = [q[1] for q in out]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) in out:
                continue
            if sum(n in out for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))) >= 3:
                dx, dy = x + 0.5 - (ax + 0.5), y + 0.5 - (ay + 0.5)
                u, v = c * dx + s * dy + au, -s * dx + c * dy + av
                k = _src(int(math.floor(u)), int(math.floor(v)))
                out[(x, y)] = k if k != '.' else 'k'
    return out


def box_at(deg, anchor_uv, anchor_xy):
    """The box turned `deg` degrees (clockwise positive) about box point anchor_uv, placed so that
    point sits on build point anchor_xy. Each range of angles uses whichever method looked cleanest
    when they were compared side by side at 7x:
      0            the rig's box, as is
      up to 12     tilt(): rows and columns sheared, the star and figure pasted upright
      up to 30     draw(): the frame re-drawn turned, the star and figure kept upright
      90, 180...   draw(): exact quarter turns
      otherwise    RotSprite-style turn of the whole box (a tumbling box: the figure turns with it)"""
    if deg == 0:
        return {(anchor_xy[0] - int(anchor_uv[0]) + c, anchor_xy[1] - int(anchor_uv[1]) + r): k
                for r, row in enumerate(MAP) for c, k in enumerate(row) if k != '.'}
    if abs(deg) <= 12:
        return tilt(deg, anchor_uv, anchor_xy)
    if abs(deg) <= 30:
        return draw(deg, anchor_uv, anchor_xy, art='upright')
    if deg % 90 == 0:
        return draw(deg, anchor_uv, anchor_xy)
    ax, ay = anchor_xy
    au, av = anchor_uv
    flat = box_at(0, (0, 0), (int(round(ax - au)), int(round(ay - av))))
    return B.close_gaps(B.rotsprite(flat, deg, (ax, ay)))


def rig_box(dx=0, dy=0):
    return B.jordan.box_part(dx, dy)


def _selftest():
    ref = rig_box()
    got = draw(0, (0, 0), (61, 25))
    bad = [(q, ref.get(q), got.get(q)) for q in set(ref) | set(got) if ref.get(q) != got.get(q)]
    print('box at 0 deg vs the rig box:', 'identical' if not bad else '%d px differ %s' % (len(bad), sorted(bad)[:12]))
    return not bad


if __name__ == '__main__':
    sys.exit(0 if _selftest() else 1)
