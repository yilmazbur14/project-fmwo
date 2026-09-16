"""Shoe (tiltable), paper bag (rotatable swing), hands."""
import math
import uparts as P

SHOE_POLY = [(-3.8, -2.8), (1.0, -2.9), (2.6, -1.3), (5.3, -0.9), (6.8, 0.2), (7.3, 1.8),
             (6.8, 3.45), (-4.0, 3.45), (-4.4, 2.0), (-4.3, -1.5)]

BAG_POLY = [(-3.9, -0.6), (3.9, -0.6), (3.9, 2.4), (4.5, 2.5), (4.5, 10.5), (-4.5, 10.5),
            (-4.5, 2.5), (-3.9, 2.4)]


def pip(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xi:
                inside = not inside
    return inside


def _raster(cx, cy, ang_deg, poly, reach):
    """Pixels whose centre falls in poly rotated by ang about (cx, cy).
    + angle turns local +y (down) toward +x. Returns {(x,y): (lx,ly)}."""
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    out = {}
    for y in range(int(cy) - reach, int(cy) + reach + 1):
        for x in range(int(cx) - reach, int(cx) + reach + 1):
            wx, wy = x - cx, y - cy
            lx = wx * ca - wy * sa
            ly = wx * sa + wy * ca
            if pip(lx, ly, poly):
                out[(x, y)] = (lx, ly)
    return out


def _outlined(loc, shade):
    mask = set(loc)
    layer = {}
    for (x, y), (lx, ly) in loc.items():
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            layer[(x, y)] = 'K'
        else:
            layer[(x, y)] = shade(lx, ly)
    return layer


def shoe(ax, ay, ang_deg, far=False, ground=None):
    """Sneaker at ankle; + angle = toe down/heel up (sole rotates clockwise)."""
    loc = _raster(ax, ay, -ang_deg, SHOE_POLY, 10)
    sy = 0
    if ground is not None:
        sy = ground - max(p[1] for p in loc)
    loc = {(x, y + sy): v for (x, y), v in loc.items()}

    def shade(lx, ly):
        if ly > 2.0:
            c = 'M'
        elif lx > 5.0 or (ly > 1.0 and lx > 3.0):
            c = 'n'
        elif ly < -0.6 and lx < 1.2:
            c = 'N'
        else:
            c = 'U'
        if far:
            c = {'N': 'U', 'U': 'n', 'n': 'M', 'M': 'M'}[c]
        return c
    return _outlined(loc, shade), (ax, ay + sy)


def bag(gx, gy, ang_deg=0.0):
    """Kraft takeout bag hanging from grip point (top centre). + angle swings bottom forward."""
    loc = _raster(gx, gy, ang_deg, BAG_POLY, 13)

    def shade(lx, ly):
        if ly < 1.6:                         # rolled top, lit face
            return 'Y' if lx < -1.5 else ('O' if lx < 2.5 else 'r')
        if ly < 2.6:                         # underside of the roll
            return 'r' if lx < 2.5 else 'V'
        if ly < 3.6:                         # crease just under the roll
            return 'O' if lx < -3.0 else ('R' if lx < 3.0 else 'r')
        if ly > 9.4:                         # bottom in shadow
            return 'r' if lx < 3.0 else 'V'
        if lx < -3.0:
            return 'Y' if ly < 6.5 else 'O'
        if lx < -2.0:
            return 'O'
        if lx < 2.6:
            return 'R'
        return 'r'
    return _outlined(loc, shade)


def limb(pts, radii, ramp, bias=0.0, thresh=P.THRESH):
    m = P.mask_stroke(pts, radii)
    return P.render(m, lambda x, y: P.stroke_normal(x, y, pts, radii), ramp, bias, thresh)


# ---- hand-authored sneakers (facing right), one sprite per foot phase
SNEAKERS = {
    'flat': (['KKKKK.......',
              'KNNNUKKK....',
              'KNNUUUUUKK..',
              'KUUUUUUUUnK.',
              'KMMMMMMMMMMK',
              '.KKKKKKKKKK.'], (3, 1)),
    'toe_up': (['........KK..',     # heel strike / toe tap
                '.....KKKNnK.',
                'KKKKKNNUUnMK',
                'KNNNUUUUUMMK',
                'KNNUUUUMMKK.',
                'KUUUMMMKK...',
                'KMMMKKK.....',
                '.KKK........'], (3, 2)),
    'heel_up': (['KKK.........',    # toe-off: toe box flat, heel lifted
                 'KNNKK.......',
                 'KNNUUKK.....',
                 'KMUUUUUKK...',
                 '.KMMUUUUUKK.',
                 '..KKMMUUUnK.',
                 '....KKMMMMMK',
                 '......KKKKK.'], (2, 1)),
}
SNEAKERS['hang'] = SNEAKERS['heel_up']
FAR_SHOE = {'N': 'U', 'U': 'n', 'n': 'M', 'M': 'M', 'K': 'K'}


def shoe(ax, ay, kind, far=False, ground=None):
    """Sneaker whose ankle sits at (ax, ay). Returns (layer, adjusted ankle)."""
    rows, (kx, ky) = SNEAKERS[kind]
    ox, oy = ax - kx, ay - ky
    loc = {}
    for j, row in enumerate(rows):
        for i, c in enumerate(row):
            if c != '.':
                loc[(ox + i, oy + j)] = FAR_SHOE[c] if far else c
    sy = 0 if ground is None else ground - max(p[1] for p in loc)
    return {(x, y + sy): c for (x, y), c in loc.items()}, (ax, ay + sy)


# ---- hand-authored kraft takeout bag (10 x 12): rolled top, crease, front face + side gusset
BAG_SPRITE = [
    '.KKKKKKKK.',
    'KYYOOOOrrK',
    'KOOORRRrVK',
    'KrrrrrrVVK',
    'KYOORRRrVK',
    'KYORRRRrVK',
    'KYORrRRrVK',
    'KOORRrRrVK',
    'KOORRRRrVK',
    'KORRRRRrVK',
    'KrrrrrrVVK',
    'KKKKKKKKKK',
]


def bag(gx, gy, ang_deg=0.0):
    """Hang the bag from grip (gx, gy) = top centre. + angle swings the bottom forward."""
    k = math.tan(math.radians(ang_deg))
    loc = {}
    for j, row in enumerate(BAG_SPRITE):
        off = int(round(k * j))
        for i, c in enumerate(row):
            if c != '.':
                loc[(gx - 4 + i + off, gy + j)] = c
    mask = set(loc)
    layer = {}
    for (x, y), c in loc.items():
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            layer[(x, y)] = 'K'
        else:
            layer[(x, y)] = 'R' if c == 'K' else c
    return layer
