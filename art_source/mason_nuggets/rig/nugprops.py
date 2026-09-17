"""Props for Mason's Chicken Nugget Meteor Shower cast (frames 15-18).

Everything is drawn as outlined parts with the painter's algorithm, the same way
rig.draw_part / props.mask_draw work: a part's own 1px boundary is black, so a part
laid over another shows a clean occlusion edge.

Palette: Mason's approved ramps plus DB32 greys/red for the paper bucket.
"""
import math
import rig
from rig import (BLACK, WHITE, CREAM, CREAM_HI, CREAM_MID, CREAM_DEEP, RED, RED_HI,
                 YEL, YEL_MID, YEL_DEEP, LX, LY, LZ)

NUG        = '#D9A066'   # nugget base (props.NUG, DB32)
NUG_DEEP   = '#8F563B'   # nugget crunchy pits / deep shade (DB32)
BK_WHT     = WHITE
BK_WHT_MID = '#CBDBFC'   # DB32 light grey-blue (cool, separates from the cream costume)
BK_WHT_DK  = '#9BADB7'   # DB32 grey-blue
BK_RED_HI  = RED_HI
BK_RED     = RED
BK_RED_DK  = '#7A2A30'   # deep red (between RED and DB32 #45283C)
BK_INSIDE  = '#45283C'   # DB32 dark plum - bucket interior
MOTION     = WHITE

N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


# ----------------------------------------------------------------------------- parts
class Part:
    """A mask of pixels with a colour function; boundary pixels become the outline."""

    def __init__(self, mask, colour, outline=BLACK):
        self.mask = mask          # {(x, y): local value}
        self.colour = colour      # f(x, y, val) -> hex or None
        self.outline = outline

    def paint(self, put):
        for (x, y), val in self.mask.items():
            edge = any((x + dx, y + dy) not in self.mask for dx, dy in N4)
            if edge and self.outline:
                put(x, y, self.outline)
            else:
                col = self.colour(x, y, val)
                if col:
                    put(x, y, col)


def scan(inside, x0, y0, x1, y1, pivot, angle=0.0):
    """inside(u, v) in local coords (rotated by angle about pivot) -> value or None"""
    ca, sa = math.cos(angle), math.sin(angle)
    m = {}
    for y in range(int(math.floor(y0)), int(math.ceil(y1)) + 1):
        for x in range(int(math.floor(x0)), int(math.ceil(x1)) + 1):
            dx, dy = x + 0.5 - pivot[0], y + 0.5 - pivot[1]
            u = ca * dx + sa * dy
            v = -sa * dx + ca * dy
            val = inside(u, v)
            if val is not None and val is not False:
                m[(x, y)] = val
    return m


def band3(v, hi, mid, lo, t_hi, t_lo):
    return hi if v > t_hi else (mid if v > t_lo else lo)


# ----------------------------------------------------------------------------- nugget
def nugget_part(cx, cy, rx, ry, angle=0.0, bumps=(), pits=(), lit=True):
    """Breaded nugget: rounded blob with notches (bumps) in the outline.
    bumps: list of (angle_deg, depth) notches/lumps on the rim (+ lump, - notch)
    pits : local (u, v) pixel offsets for crumb pits (NUG_DEEP)"""
    def inside(u, v):
        th = math.degrees(math.atan2(v / ry, u / rx))
        lim = 1.0
        for a, d in bumps:
            da = (th - a + 540) % 360 - 180
            lim += d * max(0.0, 1.0 - abs(da) / 38.0)
        r = math.hypot(u / rx, v / ry)
        if r <= lim:
            return (u / (rx * lim), v / (ry * lim))
        return None
    R = max(rx, ry) + 2
    m = scan(inside, cx - R, cy - R, cx + R, cy + R, (cx, cy), angle)
    ca, sa = math.cos(angle), math.sin(angle)

    def colour(x, y, val):
        nu, nv = val
        # back to world-space normal so the light stays top-left whatever the spin
        nx = ca * nu - sa * nv
        ny = sa * nu + ca * nv
        d2 = nx * nx + ny * ny
        nz = math.sqrt(max(0.0, 1.0 - min(1.0, d2)))
        L = nx * LX + ny * LY + nz * LZ
        if not lit:
            L -= 0.35
        if L > 0.80:
            return CREAM
        if L > 0.30:
            return NUG
        if L > -0.05:
            return CREAM_DEEP
        return NUG_DEEP
    part = Part(m, colour)

    def paint(put, _p=part):
        _p.paint(put)
        for (pu, pv) in pits:
            x = int(math.floor(cx + ca * pu - sa * pv))
            y = int(math.floor(cy + sa * pu + ca * pv))
            if (x, y) in m and all((x + dx, y + dy) in m for dx, dy in N4):
                put(x, y, NUG_DEEP)
    return paint


def paint_all(put, painters):
    for p in painters:
        p(put)


# ----------------------------------------------------------------------------- rig glue
def prop(painters_fn):
    """wrap a painters factory (called with ctx) as a rig 'over'/'under' callable"""
    def f(c):
        for p in painters_fn(c):
            p(c.put)
    return f


def speed_lines(segs, col=WHITE, outline=None):
    def f(c):
        for seg in segs:
            for i in range(len(seg) - 1):
                for p in rig.bres(seg[i][0], seg[i][1], seg[i + 1][0], seg[i + 1][1]):
                    c.put(p[0], p[1], col)
    return f


def sparkle(cx, cy, size=2, col=WHITE, core=YEL):
    """4-point glint: plus of white with black outline"""
    def f(c):
        pts = [(0, 0)] + [(d, 0) for d in range(-size, size + 1) if d] + [(0, d) for d in range(-size, size + 1) if d]
        S = set(pts)
        for (u, v) in pts:
            for du, dv in N4:
                if (u + du, v + dv) not in S:
                    c.put(cx + u + du, cy + v + dv, BLACK)
        for (u, v) in pts:
            c.put(cx + u, cy + v, core if (u, v) != (0, 0) and abs(u) + abs(v) == size else col)
    return f


# ----------------------------------------------------------------------------- nugget bucket
def bucket_lip(px, py, wt=40, wb=32, h=16, angle=0.0, rim_ry=2.4, lip=2, stripes=9,
               contents='heap', heap=None, lip_over=0.8):
    """(px, py) = centre of the mouth ellipse = top edge of the white lip band.
    Painters back-to-front: mouth (dark ellipse) -> heap nuggets -> lip band + striped body."""
    hwt, hwb = wt / 2.0, wb / 2.0

    def hw(v):
        t = min(1.0, max(0.0, (v - lip) / max(1.0, h - lip)))
        return hwt - 0.4 + (hwb - hwt + 0.4) * t

    def in_open(u, v):
        if (u / (hwt + lip_over)) ** 2 + (v / rim_ry) ** 2 <= 1.0 and v <= 0.5:
            return ('open', u, v)
        return None

    def in_front(u, v):
        if -0.01 <= v <= lip + 0.99 and abs(u) <= hwt + lip_over:
            return ('lip', u, v)
        if lip + 0.99 < v <= h and abs(u) <= hw(v):
            return ('body', u, v)
        if v > h and (u / hwb) ** 2 + ((v - h) / 1.6) ** 2 <= 1.0:
            return ('body', u, v)
        return None

    R = max(wt, h) + 6
    m_open = scan(in_open, px - R, py - R, px + R, py + R, (px, py), angle)
    m_front = scan(in_front, px - R, py - R, px + R, py + R, (px, py), angle)

    def c_open(x, y, val):
        return BK_INSIDE

    def c_front(x, y, val):
        kind, u, v = val
        if kind == 'lip':
            f = u / (hwt + lip_over)
            if f > 0.60:
                return BK_WHT_DK
            if f > 0.05 or v >= lip:
                return BK_WHT_MID
            return BK_WHT
        halfw = hw(min(v, h))
        f = max(-1.0, min(1.0, u / max(0.5, halfw)))
        t = math.asin(f) / (math.pi / 2)
        s = max(0, min(stripes - 1, int(math.floor((t + 1.0) / 2.0 * stripes))))
        red = (s % 2 == 1)
        if f > 0.58:
            return BK_RED_DK if red else BK_WHT_DK
        if f < -0.30:
            return BK_RED_HI if red else BK_WHT
        return BK_RED if red else BK_WHT_MID

    out = []
    if contents in ('heap', 'empty'):
        out.append(Part(m_open, c_open).paint)
    if contents == 'heap' and heap:
        ca, sa = math.cos(angle), math.sin(angle)
        for (u, v, rx, ry, a, bumps, pits) in heap:
            x = px + ca * u - sa * v
            y = py + sa * u + ca * v
            out.append(nugget_part(x, y, rx, ry, angle + math.radians(a), bumps, pits))
    out.append(Part(m_front, c_front).paint)
    return out
