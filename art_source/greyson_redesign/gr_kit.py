"""Greyson redesign toolkit: palette, polygon fill, form shading, a keylining canvas, the audit,
the cleanup and the measurements. Self-contained on purpose (every module here is named gr_*), so
it cannot shadow or be shadowed by another rig's pal / lib / shapes.

Frames are 112x112, feet on row 111. Column 56 is the anchor and the mirror axis: x' = 112 - x.
Light comes from the upper left. Nothing in this module writes files.
"""
import math
import sys
from collections import Counter

sys.dont_write_bytecode = True

from PIL import Image  # noqa: E402

W = H = 112
AX = 112                 # mirror: x' = 112 - x, so column 56 maps to itself


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour. Ramps run light -> dark.
PAL = {
    'k': hx('000000'),                                   # keyline: pure black, as the human cast
    # skin: the house ramp (Matt's, Carter's, Josh's), light -> dark
    '1': hx('FBD6B0'), '2': hx('F0B98E'), '3': hx('DB976C'), '4': hx('B86C4E'), '5': hx('84412F'),
    '6': hx('552619'),
    # strawberry blonde: the mane, brows, moustache
    'a': hx('FFF1B4'), 'b': hx('F7D06A'), 'c': hx('E5A548'), 'd': hx('C27434'), 'e': hx('8C4522'),
    # purple posing trunks: Computah's own paint ramp, so the robot wears its maker's colours
    # ('A', its top highlight, is kept for the ramp's sake; these two frames don't reach it)
    'A': hx('C892F2'), 'B': hx('A063DC'), 'C': hx('7C3BB4'), 'D': hx('592687'), 'E': hx('391555'),
    # whites: boots, teeth, sclera, glints (Matt's cool whites)
    'W': hx('FFFFFF'), 'X': hx('D5D9EC'), 'x': hx('9DA1C0'),
    # charcoal: boot soles
    'L': hx('2A2A38'), 'M': hx('3F3F52'),
    # eyes: the portrait's blue (#639BFF) with a pale lower half and a deep pupil
    'o': hx('B4DCFF'), 'O': hx('639BFF'), 'n': hx('1E3566'),
    # gold wire glasses
    'g': hx('FFE98C'), 'G': hx('D4A23A'),
    # the forehead vein: the portrait's red (#D95763), and its shadow side
    'v': hx('D95763'), 'V': hx('9E3A48'),
}

RAMPS = {
    'skin': '123456',
    'hair': 'abcde',
    'purple': 'ABCDE',
    'white': 'WXx',
    'char': 'ML',
    'eye': 'oOn',
    'gold': 'gG',
    'vein': 'vV',
}

DARKER, LIGHTER = {}, {}
for _r in RAMPS.values():
    for _i, _k in enumerate(_r):
        DARKER[_k] = _r[min(_i + 1, len(_r) - 1)]
        LIGHTER[_k] = _r[max(_i - 1, 0)]
DARKER['k'] = LIGHTER['k'] = 'k'

ALLOWED = set(PAL)


# ------------------------------------------------------------------------------------ shapes

def poly(pts):
    """Pixels whose centre is inside the polygon or on its edge (vertices in pixel-centre
    coordinates)."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    out = set()
    n = len(pts)
    for py in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for px in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            if _inside(px, py, pts, n):
                out.add((px, py))
    return out


def _on_edge(x, y, pts, n, eps=1e-6):
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if min(x1, x2) - eps <= x <= max(x1, x2) + eps and min(y1, y2) - eps <= y <= max(y1, y2) + eps:
            if abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)) <= eps * max(1.0, abs(x2 - x1) + abs(y2 - y1)):
                return True
    return False


def _inside(x, y, pts, n):
    # A pixel centre exactly on an edge counts as inside. The bare crossing test keeps such points
    # on left-hand edges and drops them on right-hand ones, so a polygon and its mirror (x' = 112 - x)
    # would rasterise differently; inclusive edges make the rule mirror-symmetric.
    if _on_edge(x, y, pts, n):
        return True
    c = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            xint = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < xint:
                c = not c
        j = i
    return c


def mpts(pts):
    return [(AX - x, y) for (x, y) in pts]


def sym(half):
    """A left-half outline running from the top of the axis round to the bottom of the axis ->
    the whole closed outline, mirrored about column 56."""
    right = [(AX - x, y) for (x, y) in reversed(half) if abs(x - AX / 2) > 1e-6]
    return half + right


def fill(pixels, key):
    return {p: key for p in pixels}


# ------------------------------------------------------------------------------------ shading

LIGHT3 = (-0.55, -0.62, 0.56)       # toward the light: left, up, out of the screen
_l = math.sqrt(sum(c * c for c in LIGHT3))
LIGHT3 = tuple(c / _l for c in LIGHT3)


def tone(i, ramp, cuts):
    """ramp: keys light -> dark; cuts: descending intensity thresholds, one fewer than the ramp."""
    for k, c in zip(ramp, cuts):
        if i >= c:
            return k
    return ramp[-1]


def lambert(n):
    ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
    return (n[0] * LIGHT3[0] + n[1] * LIGHT3[1] + n[2] * LIGHT3[2]) / ln


def ellipsoid(part, cx, cy, rx, ry, ramp, cuts, bulge=1.0):
    """Shade `part` as the front of an ellipsoid centred (cx, cy); bulge < 1 flattens it."""
    for (x, y) in list(part):
        u = (x - cx) / rx
        v = (y - cy) / ry
        r2 = u * u + v * v
        z = math.sqrt(max(0.0, 1.0 - min(1.0, r2))) * bulge
        part[(x, y)] = tone(lambert((u, v, z)), ramp, cuts)


def cylinder(part, p0, p1, r, ramp, cuts, tilt=0.0):
    """Shade `part` as a cylinder of radius r along p0 -> p1."""
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    al = math.hypot(ax, ay) or 1.0
    ax, ay = ax / al, ay / al
    nx, ny = -ay, ax
    for (x, y) in list(part):
        s = ((x - x0) * nx + (y - y0) * ny) / r
        s = max(-1.0, min(1.0, s))
        z = math.sqrt(max(0.0, 1.0 - s * s))
        n = (s * nx - tilt * ax, s * ny - tilt * ay, z)
        part[(x, y)] = tone(lambert(n), ramp, cuts)


def despeckle(part, keys='123456', passes=2, keep=()):
    """Pixel-art cleanup for procedurally shaded layers: a pixel of `keys` with no 8-neighbour of
    its own key (an orphan, which reads as noise at 3x) takes the most common key among its
    4-neighbours inside the part (keylines excluded). Pixels in `keep` (hand drawn) never change."""
    for _ in range(passes):
        changes = {}
        for (x, y), k in part.items():
            if k not in keys or (x, y) in keep:
                continue
            if any(part.get((x + dx, y + dy)) == k
                   for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
                continue
            n4 = [part.get(q) for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))]
            n4 = [q for q in n4 if q is not None and q != 'k' and q in keys]
            if n4:
                changes[(x, y)] = Counter(n4).most_common(1)[0][0]
        if not changes:
            break
        part.update(changes)
    return part


# ------------------------------------------------------------------------------------ canvas

class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def stamp(self, part, outline=True):
        """Stamp a part back to front. With outline, a 1px keyline (4-neighbour dilation, so
        diagonals stay one pixel thin) goes round it first, over anything already drawn: that is
        where the house style's black separations between overlapping forms come from."""
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                        self.px[q] = 'k'
        for q, k in part.items():
            if 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                self.px[q] = k

    def image(self):
        return image(self.px, self.w, self.h)


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PAL[k])
    return im


def dump(px, x0, y0, x1, y1):
    """Rows of keys for a region (inclusive), ruled in fives, labelled with their y: the way to
    read a frame back as a grid when revising it."""
    lines = ['      ' + ''.join('%-6d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        row = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(row[i:i + 5] for i in range(0, len(row), 5)))
    return '\n'.join(lines)


# ------------------------------------------------------------------------------------ checks

def flat(im):
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())


def stats(im):
    data = flat(im.convert('RGBA'))
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)),
            'semi': semi}


def bbox(px):
    xs = [x for (x, y) in px]
    ys = [y for (x, y) in px]
    return min(xs), min(ys), max(xs), max(ys)


def audit(px, fx=()):
    """Problems a frame must not ship with:
      gaps   colour pixels touching transparency (a hole in the keyline)
      lone   pixels with no neighbour at all (stray specks)
      holes  transparent pixels boxed in on four sides (a pinhole)
      keys   palette keys outside PAL
    `fx` lists effect pixels that float free by design."""
    fx = set(fx)
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        n4 = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if k != 'k' and any(q not in px for q in n4):
            gaps.append((x, y, k))
        if not any((x + dx, y + dy) in px for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
            lone.append((x, y, k))
    x0, y0, x1, y1 = bbox(px)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x, y) not in px and all(q in px for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                holes.append((x, y))
    keys = sorted(set(px.values()) - ALLOWED)
    return {'gaps': gaps, 'lone': lone, 'holes': holes, 'keys': keys}


# ------------------------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)


def upscale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def grid(im, s, major=8, col=(255, 255, 255, 22), major_col=(255, 80, 200, 80)):
    """An upscaled copy with a pixel grid, for placing things by coordinate."""
    big = upscale(on_bg(im), s)
    px = big.load()
    for gx in range(0, big.width, s):
        c = major_col if (gx // s) % major == 0 else col
        for y in range(big.height):
            px[gx, y] = _blend(px[gx, y], c)
    for gy in range(0, big.height, s):
        c = major_col if (gy // s) % major == 0 else col
        for x in range(big.width):
            px[x, gy] = _blend(px[x, gy], c)
    return big


def _blend(a, b):
    t = b[3] / 255.0
    return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t),
            int(a[2] * (1 - t) + b[2] * t), 255)
