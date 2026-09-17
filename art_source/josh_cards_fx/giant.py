"""The giant floor card: the slab itself, its landing-warning shadow, and the slam impact.

Geometry.  The arena is seen in a shallow 3/4 view, so a card lying flat on the mat is a
trapezoid: the far edge is shorter than the near edge and the far half is compressed down the
screen.  Everything is drawn by mapping each screen pixel back into card space (U, V) and
painting the face design there, so the border, the lattice and the spade all foreshorten
together instead of looking like a flat rectangle with a gradient on it.
"""
import math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

CW, CH = 191, 293                 # one third of the arena floor, in texels, at 3x

# --- trapezoid, in canvas pixels -------------------------------------------------
CX = 95.0                         # centre column (canvas is 191 wide -> 0..190)
Y_FAR, Y_NEAR = 8.0, 274.0        # top face: far edge row, near edge row
HW_FAR, HW_NEAR = 71.0, 91.0      # half-widths of those edges
THICK = 9                         # card-stock slab depth, in rows

# card-space aspect: a playing card is 2.5 x 3.5
CARD_W, CARD_H = 1.0, 1.4


def uv(x, y):
    """Screen pixel -> card space (U, V) in [0,1], or None when outside the top face."""
    t = (y + 0.5 - Y_FAR) / (Y_NEAR - Y_FAR)
    if t < 0.0 or t > 1.0:
        return None
    hw = HW_FAR + (HW_NEAR - HW_FAR) * t
    u = (x + 0.5 - CX) / hw
    if abs(u) > 1.0:
        return None
    # perspective-correct V: the far half of the card occupies fewer screen rows
    a = HW_NEAR / HW_FAR
    v = t * a / (1.0 + t * (a - 1.0))
    return (u + 1.0) * 0.5, v


def edge_dist(U, V):
    """Distance to the card's border, in card units, with rounded corners."""
    dx = min(U, 1.0 - U) * CARD_W
    dy = min(V, 1.0 - V) * CARD_H
    rc = 0.085
    if dx < rc and dy < rc:
        return rc - math.hypot(rc - dx, rc - dy)
    return min(dx, dy)


# --------------------------------------------------------------------------- spade
def spade_hit(x, y):
    """x, y in [-1, 1]; the spade's point is at y = -1."""
    if (x + 0.40) ** 2 + (y - 0.06) ** 2 <= 0.53 ** 2:
        return True
    if (x - 0.40) ** 2 + (y - 0.06) ** 2 <= 0.53 ** 2:
        return True
    if -1.0 <= y <= 0.06 and abs(x) <= 0.93 * (y + 1.0) / 1.06:
        return True
    if 0.18 <= y <= 0.94:                       # stem, flaring into a foot
        t = (y - 0.18) / 0.76
        w = 0.055 + 0.30 * t ** 3.4
        if abs(x) <= w:
            return True
    return False


def lattice(U, V):
    """Art-deco diamond lattice, in card space - a quiet texture on the cream field."""
    a = U * 9.0 + V * 11.0
    b = U * 9.0 - V * 11.0
    fa = abs(a - math.floor(a) - 0.5)
    fb = abs(b - math.floor(b) - 0.5)
    return fa > 0.40 or fb > 0.40


# --------------------------------------------------------------------------- face
def _band(t, edge, soft, x, y, seed):
    """Threshold with a 1-step ordered-dither transition, so tone steps don't read as a hard
    diagonal seam across a big flat shape."""
    if t > edge + soft:
        return True
    if t < edge - soft:
        return False
    k = (t - (edge - soft)) / (2 * soft)
    return hashf(x, y, seed) < k


def face_char(U, V, px=0, py=0):
    d = edge_dist(U, V)
    if d <= 0:
        return None
    # light comes from the upper left, as everywhere else in this game
    lit = (1.0 - U) * 0.55 + (1.0 - V) * 0.45

    # ---- borders -----------------------------------------------------------
    if d < 0.016:
        return 'D' if lit > 0.45 else 'A'
    if d < 0.028:
        return 'F' if lit > 0.55 else 'D'        # the bright gold rim
    if d < 0.038:
        return 'A' if lit > 0.40 else 'K'
    if d < 0.072:
        return 'n' if lit > 0.42 else 'N'        # cream margin
    if d < 0.086:
        return 'D' if lit > 0.45 else 'A'        # inner gold frame line
    if d < 0.096:
        return 'K'

    # ---- corner pips (all upright: this is read from above, at speed) -------
    for cu, cv in ((0.150, 0.098), (0.850, 0.098), (0.150, 0.902), (0.850, 0.902)):
        sx = (U - cu) / 0.070
        sy = (V - cv) / 0.055
        if abs(sx) <= 1.0 and abs(sy) <= 1.0 and spade_hit(sx, sy):
            return 'x' if (-sx * 0.5 - sy * 0.5) < 0.55 else 'v'

    # ---- central medallion + spade ----------------------------------------
    mu = (U - 0.5) / 0.335
    mv = (V - 0.5) / 0.300
    md = math.hypot(mu, mv)
    su, sv = (U - 0.5) / 0.225, (V - 0.505) / 0.215
    if abs(su) <= 1.02 and abs(sv) <= 1.02 and spade_hit(su, sv):
        # the spade itself: near-black with a sheen up its left shoulder
        sh = (-su) * 0.62 + (-sv) * 0.38
        if _band(sh, 0.44, 0.13, px, py, 31):
            return 'v'
        if _band(sh, 0.04, 0.15, px, py, 37):
            return 'X'
        return 'x'
    if md <= 1.0:
        if md > 0.94:
            return 'L'                            # dark red ring edge
        if md > 0.86:
            return 'R' if lit > 0.52 else 'Q'
        rl = (-mu) * 0.60 + (-mv) * 0.40
        if _band(rl, 0.54, 0.10, px, py, 41):
            return 'E'                            # specular on the upper-left of the disc
        if _band(rl, 0.20, 0.13, px, py, 43):
            return 'R'
        if _band(rl, -0.32, 0.14, px, py, 47):
            return 'Q'
        return 'q'

    # ---- cream field with its lattice -------------------------------------
    if lattice(U, V):
        return 'N' if lit > 0.52 else 'u'
    return 'n' if lit > 0.46 else 'N'


def top_face():
    c = Cv(CW, CH)
    for y in range(CH):
        for x in range(CW):
            p = uv(x, y)
            if p is None:
                continue
            ch = face_char(p[0], p[1], x, y)
            if ch:
                c.p[y][x] = ch
    return c


# --------------------------------------------------------------------------- slab
def add_wall(c):
    """The cut edge of the card stock, dropped straight down off the near silhouette."""
    wall = ['n', 'u', 'u', 'U', 'U', 'U', 'i', 'i', 'I']
    for x in range(CW):
        col = [y for y in range(CH) if c.p[y][x] != '.']
        if not col:
            continue
        ymax = max(col)
        for k in range(THICK):
            y = ymax + 1 + k
            if y >= CH:
                break
            ch = wall[min(k, len(wall) - 1)]
            # a gold glint runs along the lit lip and dithers out toward the right
            if k <= 1:
                g = 1.0 - x / (CW * 0.78)
                if g > 0 and hashf(x, k, 21) < 0.35 + g * 0.75:
                    ch = 'D' if k == 0 else 'A'
            c.p[y][x] = ch
    return c


def build():
    c = top_face()
    add_wall(c)
    outline(c)
    return c


# --------------------------------------------------------------------------- shadow
def build_shadow():
    """The landing warning: a 50% checker-dithered black footprint with a dashed gold border.

    Dithered rather than semi-transparent so the PNG stays 0/255 alpha; it already reads as a
    half-strength shadow over the green mat with no modulate at all.
    """
    c = Cv(CW, CH)
    inside = Cv(CW, CH)
    for y in range(CH):
        for x in range(CW):
            p = uv(x, y)
            if p is None:
                continue
            if edge_dist(p[0], p[1]) <= 0:
                continue
            inside.p[y][x] = '#'
    for y in range(CH):
        for x in range(CW):
            if inside.p[y][x] == '.':
                continue
            p = uv(x, y)
            d = edge_dist(p[0], p[1])
            if d < 0.020:
                c.p[y][x] = '#'                          # solid black lip
            elif d < 0.055:
                # dashed gold warning band, marching around the border
                s = (x * 2 + y * 3) // 7
                c.p[y][x] = 'A' if s % 3 else 'K'
            elif (x + y) % 2 == 0:
                c.p[y][x] = '#'                          # 50% checker interior
    return c


# --------------------------------------------------------------------------- impact
IW, IH = 231, 80                   # 20 texels of overhang each side of the 191-wide card
HORIZON = 60                       # this row lines up with the card's near edge
FRAMES = 5


def puff_cloud(c, lobes, ramp=('i', 'U', 'u', 'N', 'n')):
    """Overlapping round lobes rendered as ONE cloud with real volume: each pixel is shaded by
    the lobe that owns it, lit from the upper left, then the whole silhouette gets a black
    outline.  This is what stops billowing dust reading as a flat cream blanket."""
    own = {}
    for li, (lx, ly, lr) in enumerate(lobes):
        if lr <= 0:
            continue
        for y in range(int(ly - lr) - 1, int(ly + lr) + 2):
            for x in range(int(lx - lr) - 1, int(lx + lr) + 2):
                if not c.inb(x, y):
                    continue
                dx, dy = (x + 0.5 - lx) / lr, (y + 0.5 - ly) / lr
                d = math.hypot(dx, dy)
                if d > 1.0:
                    continue
                w = 1.0 - d
                if (x, y) not in own or w > own[(x, y)][0]:
                    own[(x, y)] = (w, dx, dy, li)
    for (x, y), (w, dx, dy, li) in own.items():
        # shade each lobe as a real sphere - a dot product against the surface normal, so the
        # terminator curves around the lobe instead of cutting a flat diagonal band across it
        nz = math.sqrt(max(0.0, 1.0 - dx * dx - dy * dy))
        lit = dx * -0.550 + dy * -0.661 + nz * 0.510   # grazing light: keeps a real shadow side
        t = max(0.0, min(0.999, (lit + 0.82) / 1.78))
        c.p[y][x] = ramp_pick(list(ramp), t)
    return c


def floor_cracks(c, grow, fade):
    """Angular black cracks jabbing outward from under the near edge, with a lit inner lip."""
    if grow <= 0:
        return c
    dark, lip = ('I', 'i') if fade < 0.5 else ('i', 'U')
    for k in range(9):
        bx = 22 + k * 23 + (k % 2) * 6
        ang = (bx - IW * 0.5) / (IW * 0.5) * 0.85
        ln = int((9 + (k * 5) % 11) * grow)
        x, y = float(bx), float(HORIZON + 1)
        d = 0
        for s in range(ln):
            if s and s % 4 == 0:                      # kink, so it reads as a crack not a hair
                d = (hashf(k, s, 11) - 0.5) * 1.6
            x += ang + d * 0.5
            y += 1.0
            for j in range(2 if s < ln * 0.62 else 1):
                c.set(int(x) + j, int(y), dark)
            if s % 3 == 0:
                c.set(int(x) - 1, int(y), lip)
    return c


def build_impact():
    """5 frames of the slam.  Row HORIZON lines up with the card's near edge: dust erupts above
    it, the floor cracks jab out below it, and the whole thing overhangs the card by 20 texels
    each side so the shockwave clears the card's corners."""
    # cloud shape: 13 lobes across the width.  (x, size, rise, survives-to-frame)
    seeds = [(0.030, 0.72, 0.70, 4), (0.098, 1.22, 1.05, 4), (0.170, 0.55, 0.55, 2),
             (0.242, 1.04, 0.92, 3), (0.318, 0.78, 0.66, 4), (0.392, 1.30, 1.10, 3),
             (0.500, 0.90, 0.80, 2), (0.608, 1.26, 1.06, 4), (0.682, 0.62, 0.58, 3),
             (0.758, 1.10, 0.95, 4), (0.830, 0.72, 0.62, 2), (0.902, 1.18, 1.02, 4),
             (0.970, 0.80, 0.72, 3)]
    # per-frame: cloud scale, rise, lateral spread, crack growth, gold strength
    keys = [(0.55, 0.00, 0.00, 0.15, 1.00),
            (0.95, 0.52, 0.20, 0.55, 0.80),
            (1.00, 1.05, 0.58, 1.00, 0.40),
            (0.82, 1.55, 1.00, 1.00, 0.12),
            (0.58, 2.05, 1.45, 1.00, 0.00)]
    out = []
    for f, (sc, rise, spread, grow, gold) in enumerate(keys):
        c = Cv(IW, IH)
        t = f / float(FRAMES - 1)

        floor_cracks(c, grow, t)

        # --- the dust bank ---------------------------------------------------
        lobes = []
        for (nx, rs, rh, life) in seeds:
            if f > life:
                continue                       # the bank breaks up into separate puffs
            off = (nx - 0.5) * 2.0
            lx = IW * 0.5 + off * (IW * 0.5 - 6) * (1.0 + spread * 0.16)
            r = (6.0 + 9.5 * rs) * sc
            # staggered heights keep the bank from reading as a row of identical bumps
            stagger = (0.0, 4.5, 1.5, 6.0)[int(nx * 97) % 4]
            ly = HORIZON - 1 - r * 0.42 - rise * 11.0 * rh - abs(off) * 2.0 - stagger * (0.3 + rise)
            lobes.append((lx, ly, r))
            # a second, smaller lobe stacked up and inboard gives the bank a crown
            if rs > 1.0 and f <= 3:
                lobes.append((lx - off * 4.0, ly - r * 0.70, r * 0.60 * (0.7 + sc * 0.3)))
        puff_cloud(c, lobes)
        outline(c)

        # --- gold shock line skimming out along the card's near edge ---------
        if gold > 0.02:
            reach = 44 + t * 108
            for side in (-1, 1):
                for k in range(64):
                    a = k / 63.0
                    px = IW * 0.5 + side * reach * (a ** 1.15)
                    py = HORIZON - 2 - a * a * 5.0 - rise * 3.0 + math.sin(a * 9.0) * 1.4
                    if not (0 <= px < IW):
                        continue
                    h = max(1, int(round((1.0 - a * 0.75) * 7.0 * gold)))
                    for j in range(h):
                        v = gold * (1.0 - a * 0.42) * (1.0 - j / float(h + 1.2))
                        c.set(int(px), int(py) - j, ramp_pick(['A', 'D', 'F', 'Y', 'w'], v))
                    # the wave drags a short tail back along the ground
                    if k % 2 == 0:
                        c.set(int(px), int(py) + 1, 'A' if gold > 0.5 else 'K')

        # --- debris chips and embers thrown clear ----------------------------
        if f >= 1:
            for k in range(26):
                a = hashf(k, 0, 9)
                b = hashf(k, 1, 13)
                px = IW * 0.5 + (a - 0.5) * IW * (0.55 + spread * 0.5)
                py = HORIZON - 6 - b * 20 - rise * 16
                if not (0 <= px < IW - 1 and 0 <= py < IH - 1):
                    continue
                if b > 0.55 and gold > 0.1:
                    c.set(int(px), int(py), 'F')            # gold ember
                else:
                    c.set(int(px), int(py), 'i')            # floor chip
                    c.set(int(px) + 1, int(py), 'U')
        out.append(c)
    return out


def all_assets():
    card = build()
    shadow = build_shadow()
    imp = build_impact()
    return card, shadow, imp
