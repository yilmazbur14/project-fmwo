"""Toolkit for Carter's polish pass: palette, a keylining canvas in PIXEL space, shapes, volume
shading, ASCII part maps, hand-edit helpers and measuring.

Everything here works on the finished 96x96 frame directly. The approved rig (art_source/carter_akuma)
authored in design space and re-rasterised at 0.84, which is where several of its rough edges came
from (1px tatters swallowed, flat-topped dome, rows of strokes that crossed after rounding). This rig
never rescales: a pixel written is the pixel shipped.

A canvas is a dict {(x, y): key}. Parts are dicts of the same shape, stamped back to front. A part
stamped with outline=True draws a 1px black keyline (4-neighbour, so diagonals stay one pixel thin)
over whatever is under its edge - that is where the interior separations between shapes come from.
Mirror axis x' = 95 - x (centre 47.5), feet on row 95, light from the upper left.
"""
import math
import os

from PIL import Image

W = H = 96
AX = 95          # mirror: x' = AX - x
HERE = os.path.dirname(os.path.abspath(__file__))


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour; ramps run light -> dark. Every hex is one of the approved sheet's own colours
# (art_source/carter_akuma/lib.py) so the family is unchanged - the polish is in where they go.
PAL = {
    'k': hx('000000'),                                                     # keyline: pure black
    # skin
    's': hx('fbd6b0'), 't': hx('f0b98e'), 'u': hx('db976c'), 'v': hx('b86c4e'), 'w': hx('84412f'),
    'W': hx('552619'),
    # Carter's orange: beard, brows
    '1': hx('ffb45e'), '2': hx('f09040'), '3': hx('d66c28'), '4': hx('b05b21'), '5': hx('703414'),
    '6': hx('4a2210'),
    # gi navy
    'a': hx('4a6ed8'), 'b': hx('2d4392'), 'c': hx('1d2b60'), 'd': hx('14204a'), 'e': hx('0c1430'),
    'f': hx('060a1e'),
    # gi, the violet the hem burns toward (the approved sheet's own fade steps)
    'A': hx('34236d'), 'B': hx('292767'), 'C': hx('23184e'), 'D': hx('1b1c4c'), 'E': hx('150f33'),
    'F': hx('111131'),
    # hand wraps
    'g': hx('fff2d6'), 'h': hx('f0d8a4'), 'i': hx('d0ae74'), 'j': hx('a07e4c'), 'l': hx('6e5230'),
    'm': hx('42301a'),
    # rope belt
    'n': hx('c8a46a'), 'o': hx('a07c46'), 'p': hx('74562e'), 'q': hx('50381c'), 'r': hx('32210f'),
    # prayer beads
    'G': hx('c08a58'), 'H': hx('84542e'), 'I': hx('58341c'), 'J': hx('3a2010'), 'L': hx('221208'),
    # aura, hot
    'x': hx('ffe2c0'), 'X': hx('ff9a6a'), 'y': hx('ff4a3c'), 'Y': hx('c01830'), 'z': hx('780c28'),
    'Z': hx('440618'),
    # aura, violet
    'P': hx('e2a2f4'), 'Q': hx('b45ae0'), 'R': hx('7c2eb0'), 'S': hx('4e1878'), 'T': hx('2e0c4c'),
    'U': hx('19062a'),
    # glowing eyes
    'M': hx('ffffff'), 'O': hx('ffd2d8'), 'V': hx('ff5a62'), '7': hx('e0203c'), '8': hx('90102a'),
    '9': hx('54061a'),
    # steel: the cross earring
    '#': hx('e6ecf2'), '%': hx('bed6ff'), '&': hx('9badb7'), '*': hx('6b7c8c'),
}

RAMP = {
    'skin': 'stuvwW',
    'hair': '123456',
    'gi': 'abcdef',
    'giv': 'ABCDEF',
    'wrap': 'ghijlm',
    'belt': 'nopqr',
    'bead': 'GHIJL',
    'ember': 'xXyYzZ',
    'void': 'PQRSTU',
    'glow': 'MOV789',
}

# one step lighter / darker inside a ramp (used by '+' and '-' in maps and by relight)
DARKER, LIGHTER = {}, {}
for _r in RAMP.values():
    for _i, _k in enumerate(_r):
        DARKER[_k] = _r[min(_i + 1, len(_r) - 1)]
        LIGHTER[_k] = _r[max(_i - 1, 0)]


# ------------------------------------------------------------------ shapes (sets of (x, y))

def poly(pts):
    """Pixels whose centre (x, y) is inside the polygon or on its edge (vertices in pixel-centre
    coordinates), so a polygon drawn on whole pixels keeps its boundary pixels."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    out = set()
    n = len(pts)
    for py in range(int(math.floor(min(ys))) - 1, int(math.ceil(max(ys))) + 2):
        for px in range(int(math.floor(min(xs))) - 1, int(math.ceil(max(xs))) + 2):
            if _inside(px, py, pts, n):
                out.add((px, py))
    return out


def _inside(x, y, pts, n):
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if _on_segment(x, y, x1, y1, x2, y2):
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


def _on_segment(x, y, x1, y1, x2, y2):
    L = math.hypot(x2 - x1, y2 - y1)
    if L == 0:
        return abs(x - x1) < 0.01 and abs(y - y1) < 0.01
    cross = abs((x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)) / L
    if cross > 0.35:
        return False
    return min(x1, x2) - 0.01 <= x <= max(x1, x2) + 0.01 and min(y1, y2) - 0.01 <= y <= max(y1, y2) + 0.01


def ellipse(cx, cy, rx, ry):
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def rect(x0, y0, x1, y1):
    """Inclusive corners."""
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    out = set()
    rmax = max(r0, r1)
    for y in range(int(min(y0, y1) - rmax) - 1, int(max(y0, y1) + rmax) + 2):
        for x in range(int(min(x0, x1) - rmax) - 1, int(max(x0, x1) + rmax) + 2):
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
            cx, cy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                out.add((x, y))
    return out


def line(x0, y0, x1, y1):
    """Bresenham, inclusive."""
    out = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        out.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return out


def polyline(pts):
    out = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = line(x0, y0, x1, y1)
        out.extend(seg if not out else seg[1:])
    return out


def mirror_set(s):
    return {(AX - x, y) for (x, y) in s}


def sym(s):
    return set(s) | mirror_set(s)


def grow(s, n=1):
    out = set(s)
    for _ in range(n):
        out |= {(x + dx, y + dy) for (x, y) in out for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))}
    return out


def erode(s, n=1):
    out = set(s)
    for _ in range(n):
        out = {(x, y) for (x, y) in out
               if all((x + dx, y + dy) in out for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
    return out


def edge(s):
    """The pixels of s that touch the outside (4-neighbour)."""
    return {(x, y) for (x, y) in s
            if any((x + dx, y + dy) not in s for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}


def band(y0, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(W)}


def halfplane(p0, p1):
    """Pixels to the left of the directed line p0 -> p1 (screen coordinates, y down)."""
    (x0, y0), (x1, y1) = p0, p1
    return {(x, y) for y in range(H) for x in range(W)
            if (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < 0}


# ------------------------------------------------------------------ volume shading

LIGHT = (-0.45, -0.6, 1.1)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)


def _intensity(n):
    nx, ny, nz = n
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]) / l


def n_sphere(cx, cy, rx, ry, flat=0.0):
    def f(x, y):
        u = (x - cx) / rx
        v = (y - cy) / ry
        d = u * u + v * v
        if d > 0.97:
            s = math.sqrt(0.97 / d)
            u, v, d = u * s, v * s, 0.97
        return (u, v, math.sqrt(1 - d) + flat)
    return f


def n_cyl(a, b, r):
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    px, py = -dy / L, dx / L

    def f(x, y):
        s = ((x - x0) * px + (y - y0) * py) / r
        s = max(-0.985, min(0.985, s))
        return (s * px, s * py, math.sqrt(1 - s * s))
    return f


def n_flat(nx, ny):
    return lambda x, y: (nx, ny, 1.0)


def n_dist(mask, R):
    """A pillow-free 'inflate': height grows with the distance to the edge, capped at R."""
    mask = set(mask)
    Rr = int(R) + 2
    hgt = {}
    for (x, y) in mask:
        best = Rr
        for dy in range(-Rr, Rr + 1):
            for dx in range(-Rr, Rr + 1):
                if (x + dx, y + dy) not in mask:
                    d = math.sqrt(dx * dx + dy * dy) - 0.5
                    if d < best:
                        best = d
        t = min(best, R) / R
        hgt[(x, y)] = R * math.sqrt(max(0.0, 1 - (1 - t) ** 2))

    def g(x, y):
        return hgt.get((x, y), 0.0)

    def f(x, y):
        return (-(g(x + 1, y) - g(x - 1, y)) / 2, -(g(x, y + 1) - g(x, y - 1)) / 2, 1.0)
    return f


def shade(mask, ramp, normal, th, bias=0, clean=2):
    """Fill mask with a ramp by lighting a normal field: th are descending intensity thresholds, one
    per ramp step after the first. clean: majority passes that dissolve single-pixel islands, which
    is what keeps the clusters clean instead of pillowed."""
    keys = RAMP[ramp] if ramp in RAMP else ramp
    idx = {}
    for (x, y) in mask:
        I = _intensity(normal(x, y))
        i = len(th)
        for j, t in enumerate(th):
            if I >= t:
                i = j
                break
        idx[(x, y)] = max(0, min(len(keys) - 1, i + bias))
    for _ in range(clean):
        chg = []
        for (x, y), v in idx.items():
            nb = [idx[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in idx]
            if len(nb) >= 3 and v not in nb:
                chg.append(((x, y), max(set(nb), key=nb.count)))
        for q, v in chg:
            idx[q] = v
    return {q: keys[i] for q, i in idx.items()}


def despeckle(part, passes=2, protect=''):
    """Recolour pixels that match none of their 4 neighbours (within the part) to the majority."""
    for _ in range(passes):
        chg = []
        for (x, y), k in part.items():
            if k in protect:
                continue
            nb = [part[q] for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if q in part]
            if len(nb) >= 3 and k not in nb:
                chg.append(((x, y), max(set(nb), key=nb.count)))
        for q, k in chg:
            part[q] = k
    return part


# ------------------------------------------------------------------ part helpers

def fill(pixels, key):
    return {p: key for p in pixels}


def paint(part, pixels, key, only=None):
    """Recolour the pixels of part that fall inside pixels (a clip, never an extension)."""
    for p in pixels:
        if p in part and (only is None or part[p] in only):
            part[p] = key


def rim(part, key, dx, dy, depth=1, only=None):
    """Recolour the pixels of part within depth steps of its edge in direction (dx, dy)."""
    hits = []
    for (x, y) in part:
        if only is not None and part[(x, y)] not in only:
            continue
        for d in range(1, depth + 1):
            if (x + dx * d, y + dy * d) not in part:
                hits.append((x, y))
                break
    for p in hits:
        part[p] = key


def stroke(part, pts, key, only=None):
    for p in polyline(pts):
        if p in part and (only is None or part[p] in only):
            part[p] = key


def amap(rows, x0, y0, skip='.'):
    """ASCII part map: one character per pixel, skip is transparent, spaces ignored (rule rows in
    fives for counting)."""
    out = {}
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        for c, ch in enumerate(row):
            if ch != skip:
                out[(x0 + c, y0 + r)] = ch
    return out


def mirror_part(part):
    return {(AX - x, y): k for (x, y), k in part.items()}


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


# ------------------------------------------------------------------ canvas

class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def inside(self, q):
        return 0 <= q[0] < self.w and 0 <= q[1] < self.h

    def stamp(self, part, outline=True, under=False):
        """Keyline round the part (over whatever is below), then the part. under=True paints only
        where the canvas is still empty, for things that sit behind what is already drawn."""
        if outline:
            body = set(part)
            for (x, y) in body:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body and self.inside(q) and (not under or q not in self.px):
                        self.px[q] = 'k'
        for q, k in part.items():
            if self.inside(q) and (not under or q not in self.px):
                self.px[q] = k

    def erase(self, pixels):
        for p in pixels:
            self.px.pop(p, None)

    def image(self):
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        for (x, y), k in self.px.items():
            if self.inside((x, y)):
                im.putpixel((x, y), PAL[k])
        return im

    def copy(self):
        c = Canvas(self.w, self.h)
        c.px = dict(self.px)
        return c


# ------------------------------------------------------------------ hand edits

def dump(px, x0, y0, x1, y1):
    """Rows of keys for a region (inclusive), ruled in fives, labelled with their y."""
    lines = ['      ' + ' '.join('%-5d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        row = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(row[i:i + 5] for i in range(0, len(row), 5)))
    return '\n'.join(lines)


def patch(px, edits):
    """Overwrite horizontal spans: edits are (y, x0, keys). In keys '.' erases, '_' keeps what is
    there, '-' / '+' step it one tone darker / lighter within its ramp; spaces are ignored."""
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            q = (x, y)
            if ch == '.':
                px.pop(q, None)
            elif ch == '-':
                if q in px:
                    px[q] = DARKER.get(px[q], px[q])
            elif ch == '+':
                if q in px:
                    px[q] = LIGHTER.get(px[q], px[q])
            elif ch != '_':
                px[q] = ch
            x += 1


def region(rows, x0, y0):
    """A full rectangular ASCII region to lay over the canvas: '.' erases, '_' keeps."""
    return [(y0 + r, x0, row) for r, row in enumerate(rows)]


# ------------------------------------------------------------------ measuring

def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    px = [c for c in data if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': black / max(1, len(px)),
            'alphas': sorted(set(c[3] for c in data))}


def colour_counts(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    rev = {v[:3]: k for k, v in PAL.items()}
    out = {}
    for c in data:
        if c[3]:
            k = rev.get(c[:3], '?')
            out[k] = out.get(k, 0) + 1
    return out


# ------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)


def upscale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def on_bg(im, bg=BG):
    out = Image.new('RGBA', im.size, bg)
    out.alpha_composite(im)
    return out


def grid_view(im, s, x0=0, y0=0, x1=None, y1=None):
    """An upscaled crop with a pixel grid (magenta every 10) for placing things by coordinate."""
    x1 = im.width - 1 if x1 is None else x1
    y1 = im.height - 1 if y1 is None else y1
    crop = on_bg(im.crop((x0, y0, x1 + 1, y1 + 1)))
    big = upscale(crop, s)
    px = big.load()
    for gx in range(crop.width):
        c = (255, 80, 200, 110) if (x0 + gx) % 10 == 0 else (255, 255, 255, 24)
        for y in range(big.height):
            px[gx * s, y] = _blend(px[gx * s, y], c)
    for gy in range(crop.height):
        c = (255, 80, 200, 110) if (y0 + gy) % 10 == 0 else (255, 255, 255, 24)
        for x in range(big.width):
            px[x, gy * s] = _blend(px[x, gy * s], c)
    return big


def _blend(a, b):
    t = b[3] / 255.0
    return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t),
            int(a[2] * (1 - t) + b[2] * t), 255)


def n_limb(segments):
    """Normals for a limb built of several capsules (a, b, r): each pixel takes the cylinder of the
    nearest bone, so an arm shades as one continuous form instead of stacked pieces."""
    cyls = [(a, b, n_cyl(a, b, r)) for a, b, r in segments]

    def f(x, y):
        best, fn = None, None
        for (x0, y0), (x1, y1), g in cyls:
            dx, dy = x1 - x0, y1 - y0
            L2 = dx * dx + dy * dy or 1.0
            t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
            d = (x - x0 - dx * t) ** 2 + (y - y0 - dy * t) ** 2
            if best is None or d < best:
                best, fn = d, g
        return fn(x, y)
    return f


def flat(im):
    """All pixels of an image as a list (Pillow 12 renamed getdata to get_flattened_data)."""
    f = getattr(im, 'get_flattened_data', None)
    return list(f() if f else im.getdata())
