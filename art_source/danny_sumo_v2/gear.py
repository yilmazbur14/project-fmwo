"""Danny's sumo gear: the torn collar scrap and the gold chain (from his shirt and portrait), the
mawashi apron, the gold rope, wrist and ankle wraps."""
import math

from sumo_lib import spoly, poly, ellipse, line, amap, band, mirror_pts, MIR, edge, shrink, grow
import lib as jl

CX = 87.5


def sym(left):
    right = mirror_pts(left[::-1])
    return left + right[1:-1] if left[0][0] == CX else left + right


# ------------------------------------------------------------------ COLLAR
# The shirt's neckband: all that survived the tear. It rides under the jaw, and its lower edge is
# torn: an irregular saw-tooth cut into the band itself, in the band's own reds. (Hanging tatters
# were tried and dropped: dark red strands under the chin read as drips, the same trap as the
# kabuki paint.)
COLLAR = [(87.5, 45), (70, 43.5), (62.5, 40.5), (59.5, 43.5), (60.5, 49.5), (65.5, 54.5), (73, 57.8),
          (80.5, 59.2), (87.5, 59.5)]
# a clean band with a few nicks where it tore: (x, depth) from the lower edge
NICKS = {68: 1, 69: 2, 70: 1, 83: 1, 84: 1, 95: 1, 96: 2, 97: 1, 106: 1}


def collar():
    mask = spoly(sym(COLLAR))
    bottom = {}
    for (x, y) in mask:
        bottom[x] = max(bottom.get(x, y), y)
    mask = {(x, y) for (x, y) in mask if y <= bottom[x] - NICKS.get(x, 0)}
    part = {p: 'R' for p in mask}
    jl.rim(part, 'r', 0, -1, depth=1)             # the band's top edge catches the light
    jl.rim(part, 'M', 0, 1, depth=1)              # its torn lower edge rolls under
    for (x, y) in list(part):
        if x > 101 and part[(x, y)] == 'R':
            part[(x, y)] = 'M'                    # the far side turns away
    return part


# ------------------------------------------------------------------ APRON
# The kesho-mawashi: a navy apron hanging from the belt, printed with Mount Fuji over seigaiha waves in
# his blues (a callback to the approved form's mountain apron), with a gold fringe at the hem.
APRON_X0, APRON_X1 = 70, 105          # inclusive columns of the cloth
APRON_Y0, APRON_Y1 = 107, 129         # top (under the rope) and hem


def apron():
    x0, x1, y0, y1 = APRON_X0, APRON_X1, APRON_Y0, APRON_Y1
    part = {}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            part[(x, y)] = 'V'
    # cloth shading: the top in the belt's shadow, the right side turning away, a lit left edge
    for (x, y) in part:
        if y <= y0 + 1:
            part[(x, y)] = 'U'
        elif x >= x1 - 1:
            part[(x, y)] = 'U'
    # a light-blue inner border
    for y in range(y0 + 3, y1 - 1):
        part[(x0 + 1, y)] = 'X'
        part[(x1 - 1, y)] = 'B'
    for x in range(x0 + 1, x1):
        part[(x, y1 - 1)] = 'B'
        part[(x, y0 + 3)] = 'B' if x > x0 + 1 else 'X'
    # Mount Fuji: a flat-topped cone, lit on the left, snowcap with a ragged lower edge
    fuji = poly([(84.2, 110.6), (90.8, 110.6), (100.5, 121.5), (74.5, 121.5)])
    for (x, y) in fuji:
        if x0 + 2 <= x <= x1 - 2:
            part[(x, y)] = 'X' if x < 87.5 else 'B'
    snow_edge = {84: 114, 85: 115, 86: 114, 87: 116, 88: 115, 89: 114, 90: 116, 91: 114, 92: 115,
                 83: 113, 82: 114, 81: 115, 93: 114, 94: 115, 80: 116, 95: 116}
    for (x, y) in fuji:
        lim = snow_edge.get(x, 112)
        if y <= lim:
            part[(x, y)] = 'W' if x < 87.5 else 'w'
    for x in range(84, 91):
        part[(x, 110)] = 'k'                       # the summit's keyline
    for (x, y) in edge(fuji):
        if y > 110 and (x, y) in part and x0 + 1 < x < x1 - 1:
            if (x - 1, y) not in fuji or (x + 1, y) not in fuji:
                part[(x, y)] = 'k'
    # seigaiha waves: two rows of arches across the bottom
    for row, (cy, off) in enumerate(((124.5, 0), (127.5, 3))):
        for cx in range(x0 - 3 + off, x1 + 4, 6):
            for (x, y) in ellipse(cx + 0.5, cy, 3.2, 3.2):
                if y > cy or not (x0 + 2 <= x <= x1 - 2) or not (y0 < y < y1 - 1):
                    continue
                d = ((x - cx - 0.5) ** 2 + (y - cy) ** 2) ** 0.5
                if d > 2.3:
                    part[(x, y)] = 'w' if row == 0 else 's'
                elif d > 1.2:
                    part[(x, y)] = 's' if row == 0 else 'B'
                else:
                    part[(x, y)] = 'V'
    return part


def fringe():
    """The gold fringe under the hem: strands with black between them, ragged at the bottom."""
    part = {}
    lengths = [4, 5, 4, 3, 5, 4, 5, 3, 4, 5, 4, 4, 5, 3, 4, 5, 4, 3]
    for i, x in enumerate(range(APRON_X0, APRON_X1 + 1, 2)):
        n = lengths[i % len(lengths)]
        for j in range(n):
            part[(x, APRON_Y1 + 1 + j)] = 'Y' if j == 0 else ('o' if j < n - 1 else 'O')
        if x + 1 <= APRON_X1:
            part[(x + 1, APRON_Y1 + 1)] = 'o'
    return part


def rope(y=108, x0=47, x1=128):
    """A braided gold rope along the belt's lower edge, where the apron hangs from it: a two-pixel
    twist, each turn lit on its upper left."""
    part = {}
    for x in range(x0, x1 + 1):
        t = (x - CX) / 44.0
        yy = y - int(round(3.0 * t * t))        # the belt curves round the hips: it rides up
        ph = (x - x0) % 3
        part[(x, yy)] = ('Y', 'o', 'O')[ph]
        part[(x, yy + 1)] = ('o', 'O', 'g')[ph]
    return part


# ------------------------------------------------------------------ CHAIN
def chain(pts, lit_every=2):
    """A gold chain along a polyline: 2px links alternating lit and shaded, on the pixels of the
    line and the one below it. Stamp with outline=True for its keyline."""
    path = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = jl.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
        if path and seg[0] == path[-1]:
            seg = seg[1:]
        path.extend(seg)
    part = {}
    for i, (x, y) in enumerate(path):
        link = (i // lit_every) % 2
        part[(x, y)] = 'Y' if link == 0 else 'o'
        part[(x, y + 1)] = 'o' if link == 0 else 'O'
    return part


CHAIN_L = [(67, 52), (72, 57.5), (78, 62), (84, 64.8), (87, 65.5)]


def gold_chain():
    left = CHAIN_L
    right = [(MIR - x, y) for (x, y) in left[::-1]]
    part = chain(left + right[1:])
    # the lowest links hang in the light: a glint
    part[(80, 63)] = 'y'
    return part


# ------------------------------------------------------------------ POSED GEAR
def _xpt(xf, p):
    x, y = xf(p)
    return (int(round(x)), int(round(y)))


def rope_xf(xf, y=108, x0=47, x1=128):
    """The rope along a turned belt: its centreline is moved, then re-laid as a two-pixel twist."""
    pts = []
    for x in list(range(x0, x1 + 1, 3)) + [x1]:
        t = (x - CX) / 44.0
        pts.append(xf((x, y - int(round(3.0 * t * t)) + 0.2)))
    path = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        seg = jl.line(int(round(ax)), int(round(ay)), int(round(bx)), int(round(by)))
        if path and seg[0] == path[-1]:
            seg = seg[1:]
        path.extend(seg)
    part = {}
    for i, (x, yy) in enumerate(path):
        ph = i % 3
        part[(x, yy)] = ('Y', 'o', 'O')[ph]
        part[(x, yy + 1)] = ('o', 'O', 'g')[ph]
    return part


def gold_chain_xf(xf):
    left = CHAIN_L
    right = [(MIR - x, y) for (x, y) in left[::-1]]
    part = chain([xf(p) for p in left + right[1:]])
    gx, gy = _xpt(xf, (80, 63))
    if (gx, gy) in part:
        part[(gx, gy)] = 'y'
    return part


def collar_xf(xf):
    mask = spoly([xf(p) for p in sym(COLLAR)])
    bottom = {}
    for (x, y) in mask:
        bottom[x] = max(bottom.get(x, y), y)
    nicks = {}
    for nx_, dep in NICKS.items():
        nicks[_xpt(xf, (nx_, 57))[0]] = dep
    mask = {(x, y) for (x, y) in mask if y <= bottom[x] - nicks.get(x, 0)}
    part = {p: 'R' for p in mask}
    jl.rim(part, 'r', 0, -1, depth=1)
    jl.rim(part, 'M', 0, 1, depth=1)
    far = xf((101, 50))[0]
    for (x, y) in list(part):
        if x > far and part[(x, y)] == 'R':
            part[(x, y)] = 'M'
    return part
