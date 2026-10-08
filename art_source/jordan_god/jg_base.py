"""Demon-god Jordan (approval pass, three takes): the shared kit.

Everything is a dict canvas {(x, y): key}; keys map to colours through a per-take palette. Jordan's
approved v2 idle (Assets/Characters/Jordan/jordan_redesign_v2.png, frame 0) is READ, never written:
its pixels are turned back into palette keys so the god forms can start from his own face, hair and
Peach print (the derived-art rule: identity comes from the character's own pixels).

Nothing in this module writes a file. The export script writes only into art_source/jordan_god/.
"""
import math
import os
import sys

sys.dont_write_bytecode = True

from PIL import Image, ImageDraw  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
ROOT = os.path.dirname(ART)
V2_PNG = os.path.join(ROOT, 'Assets', 'Characters', 'Jordan', 'jordan_redesign_v2.png')
PLAYER_PNG = os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png')
ASEPRITE = os.environ.get(
    'ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')

if ART not in sys.path:
    sys.path.append(ART)


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# ------------------------------------------------------------------ Jordan's approved palette
# The v2 sheet's keys (art_source/jordan_redesign/kit.py plus v2's pallor skin), re-declared here
# so this rig reads nothing but the PNG. Ramps run dark -> light.
JORDAN = {
    'k': hx('000000'),
    'a': hx('4E3A33'), 'b': hx('7D6353'), 'c': hx('AA9173'), 'd': hx('CDB694'), 'e': hx('E7D8B6'),
    'p': hx('9A6558'),
    'h': hx('1A110D'), 'i': hx('2B1C15'), 'j': hx('432D21'), 'l': hx('5F412E'), 'm': hx('7F5B3E'),
    'A': hx('A27B57'),
    'W': hx('F3EEE4'),
    'v': hx('4C0D1A'), 'V': hx('8C1B2D'), 'R': hx('C9293F'), 'T': hx('EC5A5B'), 'U': hx('FF9C8C'),
    'q': hx('B04A78'), 'P': hx('EE7FAE'), 'Q': hx('FFC3DB'),
    'n': hx('141A31'), 'N': hx('222F55'), 's': hx('33467B'), 'S': hx('4A62A0'),
    '1': hx('2C2F39'), '2': hx('4C505D'), '3': hx('7B8090'), '9': hx('BAB6AC'), '0': hx('F2EFE7'),
    'g': hx('7A5216'), 'G': hx('B07D22'), 'o': hx('E0AB35'), 'O': hx('F5D94E'), 'Y': hx('FFF3B0'),
    'w': hx('86A9C2'), 'x': hx('CFE4EE'),
    'B': hx('2F55B5'), 'D': hx('1C2F73'),
    'f': hx('FBE3CC'),
}
_INV = {v: k for k, v in JORDAN.items()}


def v2_keys(frame=0):
    """Frame `frame` of the approved v2 sheet as {(x, y): key}."""
    im = Image.open(V2_PNG).convert('RGBA')
    fr = im.crop((frame * 96, 0, frame * 96 + 96, 96))
    out = {}
    px = fr.load()
    for y in range(96):
        for x in range(96):
            c = px[x, y]
            if c[3] == 0:
                continue
            if c not in _INV:
                raise ValueError('v2 colour %s at %s is not in the approved palette' % (c, (x, y)))
            out[(x, y)] = _INV[c]
    return out


# ------------------------------------------------------------------ shapes (sets of pixels)

def poly(pts):
    """Pixels whose centre lies inside the polygon (even-odd), vertices in pixel-centre coords."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    out = set()
    n = len(pts)
    for py in range(int(math.floor(min(ys))), int(math.ceil(max(ys))) + 1):
        # scanline crossings
        xing = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= py < y2) or (y2 <= py < y1):
                xing.append(x1 + (py - y1) * (x2 - x1) / (y2 - y1))
        xing.sort()
        for a, b in zip(xing[0::2], xing[1::2]):
            for px in range(int(math.ceil(a - 0.5)), int(math.floor(b + 0.5)) + 1):
                if a - 0.5 <= px <= b + 0.5:
                    out.add((px, py))
    return out


def ellipse(cx, cy, rx, ry):
    out = set()
    for y in range(int(math.floor(cy - ry)) - 1, int(math.ceil(cy + ry)) + 2):
        for x in range(int(math.floor(cx - rx)) - 1, int(math.ceil(cx + rx)) + 2):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                out.add((x, y))
    return out


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def line(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
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
        if out and seg and out[-1] == seg[0]:
            seg = seg[1:]
        out.extend(seg)
    return out


def bezier(p0, p1, p2, p3=None, n=48):
    """Points along a quadratic (3 pts) or cubic (4 pts) Bezier."""
    pts = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0]
                 + t ** 3 * p3[0])
            y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1]
                 + t ** 3 * p3[1])
        pts.append((x, y))
    return pts


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with end radii r0, r1."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, max(r0, 0.5), max(r0, 0.5)) | ellipse(x1, y1, max(r1, 0.5), max(r1, 0.5))


def tube(pts, radii):
    """A tapered tube along a polyline of points with a radius per point."""
    out = set()
    for (p0, p1), (r0, r1) in zip(zip(pts, pts[1:]), zip(radii, radii[1:])):
        out |= capsule(p0, p1, r0, r1)
    return out


def ribbon(pts, radii):
    """Like tube, but the outline is one polygon (smoother for long curved shapes)."""
    left, right = [], []
    n = len(pts)
    for i in range(n):
        x, y = pts[i]
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        r = radii[i]
        left.append((x + nx * r, y + ny * r))
        right.append((x - nx * r, y - ny * r))
    return poly(left + right[::-1])


def mirror_set(pixels, axis2):
    """Mirror about x = axis2 / 2 (axis2 = 191 mirrors a 192-wide frame about its centre line)."""
    return {(axis2 - x, y) for (x, y) in pixels}


def mirror_part(part, axis2):
    return {(axis2 - x, y): k for (x, y), k in part.items()}


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def fill(pixels, key):
    return {p: key for p in pixels}


def neighbours4(p):
    x, y = p
    return ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))


def neighbours8(p):
    x, y = p
    return [(x + dx, y + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy]


def edge(pixels):
    """Pixels of the set that touch the outside (4-neighbour)."""
    s = set(pixels)
    return {p for p in s if any(q not in s for q in neighbours4(p))}


def grow(pixels, n=1, diag=False):
    s = set(pixels)
    for _ in range(n):
        add = set()
        for p in s:
            for q in (neighbours8(p) if diag else neighbours4(p)):
                add.add(q)
        s |= add
    return s


def shrink(pixels, n=1):
    s = set(pixels)
    for _ in range(n):
        s = {p for p in s if all(q in s for q in neighbours4(p))}
    return s


# ------------------------------------------------------------------ volume shading

def distance_in(mask):
    """Chamfer distance (3-4) from each pixel of `mask` to the nearest pixel outside it, in px."""
    if not mask:
        return {}
    xs = [p[0] for p in mask]
    ys = [p[1] for p in mask]
    x0, y0, x1, y1 = min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1
    W, H = x1 - x0 + 1, y1 - y0 + 1
    INF = 10 ** 9
    d = [[0 if (x + x0, y + y0) not in mask else INF for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            v = d[y][x]
            if v == 0:
                continue
            if x > 0:
                v = min(v, d[y][x - 1] + 3)
            if y > 0:
                v = min(v, d[y - 1][x] + 3)
                if x > 0:
                    v = min(v, d[y - 1][x - 1] + 4)
                if x < W - 1:
                    v = min(v, d[y - 1][x + 1] + 4)
            d[y][x] = v
    for y in range(H - 1, -1, -1):
        for x in range(W - 1, -1, -1):
            v = d[y][x]
            if v == 0:
                continue
            if x < W - 1:
                v = min(v, d[y][x + 1] + 3)
            if y < H - 1:
                v = min(v, d[y + 1][x] + 3)
                if x < W - 1:
                    v = min(v, d[y + 1][x + 1] + 4)
                if x > 0:
                    v = min(v, d[y + 1][x - 1] + 4)
            d[y][x] = v
    return {(x + x0, y + y0): d[y][x] / 3.0 for y in range(H) for x in range(W) if (x + x0, y + y0) in mask}


LIGHT = (-0.55, -0.75, 0.62)   # upper-left, toward the viewer: the cast's light


def _norm(v):
    ln = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / ln for c in v)


def shade(mask, ramp, radius=None, light=LIGHT, bias=0.0, cuts=None, flat=0.0, dist=None):
    """Round the mask into a volume and light it: returns {pixel: key} using `ramp` (dark -> light).

    The height field is a rounded bevel over the distance to the mask's edge (a tube for thin
    parts, a pillow-edged slab for wide ones); its normal is lit by `light`. `cuts` are the
    intensity thresholds between the ramp steps (len(ramp) - 1 of them); `bias` shifts the
    intensity; `flat` (0..1) flattens the normal toward the viewer (broad planes)."""
    if not mask:
        return {}
    L = _norm(light)
    d = dist if dist is not None else distance_in(mask)
    R = radius or max(1.5, max(d.values()))
    h = {}
    for p, v in d.items():
        t = min(v / R, 1.0)
        h[p] = R * math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2))
    n = len(ramp)
    if cuts is None:
        cuts = [0.18 + 0.64 * i / (n - 2) for i in range(n - 1)] if n > 2 else [0.5]
    out = {}
    for (x, y), hv in h.items():
        hl = h.get((x - 1, y), 0.0)
        hr = h.get((x + 1, y), 0.0)
        hu = h.get((x, y - 1), 0.0)
        hd = h.get((x, y + 1), 0.0)
        gx = (hr - hl) / 2.0
        gy = (hd - hu) / 2.0
        nv = _norm((-gx * (1 - flat), -gy * (1 - flat), 1.0))
        I = max(0.0, nv[0] * L[0] + nv[1] * L[1] + nv[2] * L[2]) + bias
        k = 0
        while k < len(cuts) and I > cuts[k]:
            k += 1
        out[(x, y)] = ramp[k]
    return out


def _closest_on_polyline(p, pts):
    """(segment index, t along it, signed perpendicular distance, perpendicular unit vector)."""
    best = None
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
        cx, cy = a[0] + dx * t, a[1] + dy * t
        d2 = (p[0] - cx) ** 2 + (p[1] - cy) ** 2
        if best is None or d2 < best[0]:
            ln = math.sqrt(L2)
            nx, ny = -dy / ln, dx / ln
            s = (p[0] - cx) * nx + (p[1] - cy) * ny
            best = (d2, i, t, s, (nx, ny))
    return best[1:]


def tube_shade(pts, radii, ramp, light=LIGHT, cuts=None, bias=0.0, mask=None, pad=0.35):
    """A cylinder along a polyline, lit properly: each pixel takes its normal from its signed
    distance to the centre line (so a thin diagonal limb shades as one smooth cylinder instead of
    the stripes a distance field gives)."""
    if mask is None:
        mask = set()
        for (a, b), (r0, r1) in zip(zip(pts, pts[1:]), zip(radii, radii[1:])):
            mask |= capsule(a, b, r0, r1)
    L = _norm(light)
    n = len(ramp)
    if cuts is None:
        cuts = [0.18 + 0.64 * i / (n - 2) for i in range(n - 1)] if n > 2 else [0.5]
    # cumulative length for radius interpolation
    out = {}
    for p in mask:
        i, t, s, (nx, ny) = _closest_on_polyline(p, pts)
        r = radii[i] + (radii[i + 1] - radii[i]) * t
        u = max(-1.0, min(1.0, s / (r + pad)))
        nz = math.sqrt(max(0.0, 1.0 - u * u))
        nv = (nx * u, ny * u, nz)
        I = max(0.0, nv[0] * L[0] + nv[1] * L[1] + nv[2] * L[2]) + bias
        k = 0
        while k < len(cuts) and I > cuts[k]:
            k += 1
        out[p] = ramp[k]
    return out


def gradient(mask, ramp, p0, p1, cuts=None):
    """Linear ramp along p0 -> p1 (0 at p0, 1 at p1), quantised to `ramp`."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1.0
    n = len(ramp)
    if cuts is None:
        cuts = [(i + 1) / n for i in range(n - 1)]
    out = {}
    for (x, y) in mask:
        t = ((x - x0) * dx + (y - y0) * dy) / L2
        k = 0
        while k < len(cuts) and t > cuts[k]:
            k += 1
        out[(x, y)] = ramp[k]
    return out


# ------------------------------------------------------------------ canvas

class Canvas:
    """A layered pixel canvas. stamp() puts a part on top; with outline=True a 1px keyline goes
    round the part first (over whatever is below), which gives the interior separations."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.px = {}

    def stamp(self, part, outline=True, line_key='k', only_over=None, clip=True):
        if outline:
            body = set(part)
            for p in body:
                for q in neighbours4(p):
                    if q not in body and (not clip or (0 <= q[0] < self.w and 0 <= q[1] < self.h)):
                        if only_over is None or self.px.get(q) in only_over:
                            self.px[q] = line_key
        for q, k in part.items():
            if not clip or (0 <= q[0] < self.w and 0 <= q[1] < self.h):
                self.px[q] = k

    def under(self, part, outline=True, line_key='k'):
        """Stamp a part BEHIND what is already drawn (fills only empty pixels)."""
        body = set(part)
        if outline:
            for p in body:
                for q in neighbours4(p):
                    if q not in body and q not in self.px and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                        self.px[q] = line_key
        for q, k in part.items():
            if q not in self.px and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                self.px[q] = k

    def erase(self, pixels):
        for p in pixels:
            self.px.pop(p, None)

    def paint(self, pixels, key, only=None):
        for p in pixels:
            if p in self.px and (only is None or self.px[p] in only):
                self.px[p] = key

    def outline_all(self, line_key='k'):
        """Close the silhouette: every empty pixel 4-touching a non-line pixel becomes keyline."""
        add = set()
        for p, k in self.px.items():
            if k == line_key:
                continue
            for q in neighbours4(p):
                if q not in self.px and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                    add.add(q)
        for q in add:
            self.px[q] = line_key

    def image(self, pal):
        return image(self.px, self.w, self.h, pal)


def image(px, w, h, pal):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ld = im.load()
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            ld[x, y] = pal[k]
    return im


# ------------------------------------------------------------------ upscaling Jordan's own pixels

def epx(part):
    """Scale2x (EPX) in key space: 2x with diagonals kept one step wide."""
    out = {}

    def g(x, y):
        return part.get((x, y))

    for (x, y), P in part.items():
        A, B, C, D = g(x, y - 1), g(x + 1, y), g(x - 1, y), g(x, y + 1)
        e1 = e2 = e3 = e4 = P
        if C == A and C != D and A != B and A is not None:
            e1 = A
        if A == B and A != C and B != D and B is not None:
            e2 = B
        if D == C and D != B and C != A and C is not None:
            e3 = C
        if B == D and B != A and D != C and D is not None:
            e4 = D
        out[(2 * x, 2 * y)] = e1
        out[(2 * x + 1, 2 * y)] = e2
        out[(2 * x, 2 * y + 1)] = e3
        out[(2 * x + 1, 2 * y + 1)] = e4
    # EPX never creates pixels outside the source's 2x cells, but it can leave a corner of a cell
    # empty-looking when a neighbour is transparent; transparent corners stay transparent.
    return out


def thin_keyline(part, line='k'):
    """After a 2x upscale the keyline is two pixels thick. Recolour the inner layer of every
    double line to the fill it borders, so the line is one pixel again (the silhouette is kept)."""
    out = dict(part)

    def fill_of(p):
        counts = {}
        for q in neighbours4(p):
            k = out.get(q)
            if k is not None and k != line:
                counts[k] = counts.get(k, 0) + 1
        if not counts:
            for q in neighbours8(p):
                k = out.get(q)
                if k is not None and k != line:
                    counts[k] = counts.get(k, 0) + 1
        return max(counts, key=counts.get) if counts else None

    outer = {p for p, k in out.items() if k == line and any(q not in out for q in neighbours4(p))}
    # 1) the silhouette band: black pixels that sit just inside an outer black pixel
    change = {}
    for p, k in out.items():
        if k != line or p in outer:
            continue
        if any(q in outer for q in neighbours4(p)) and any(out.get(q) not in (None, line) for q in neighbours4(p)):
            f = fill_of(p)
            if f:
                change[p] = f
    out.update(change)
    # 2) interior double lines: keep the upper / left pixel of a 2-thick run
    change = {}
    for (x, y), k in out.items():
        if k != line or (x, y) in outer:
            continue
        L, R = out.get((x - 1, y)), out.get((x + 1, y))
        U, D = out.get((x, y - 1)), out.get((x, y + 1))
        if L == line and R not in (None, line) and out.get((x - 2, y)) not in (None, line):
            change[(x, y)] = R
        elif U == line and D not in (None, line) and out.get((x, y - 2)) not in (None, line):
            change[(x, y)] = D
    out.update(change)
    return out


# ------------------------------------------------------------------ measuring

def stats(im):
    flat = getattr(im, 'get_flattened_data', None)
    data = list(flat() if flat else im.getdata())
    op = [c for c in data if c[3] > 0]
    semi = sum(1 for c in data if 0 < c[3] < 255)
    black = sum(1 for c in op if c[:3] == (0, 0, 0))
    return {'opaque': len(op), 'colours': len(set(op)), 'black': black / max(1, len(op)), 'semi': semi}


def audit(px, fx=(), line='k'):
    """Keyline gaps (body pixels touching transparency), lone specks and pinholes."""
    fx = set(fx)
    gaps, lone, holes = [], [], []
    for (x, y), k in px.items():
        if (x, y) in fx:
            continue
        if k != line and any(q not in px for q in neighbours4((x, y))):
            gaps.append((x, y, k))
        if not any(q in px for q in neighbours8((x, y))):
            lone.append((x, y, k))
    xs = [p[0] for p in px]
    ys = [p[1] for p in px]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            if (x, y) not in px and all(q in px for q in neighbours4((x, y))):
                holes.append((x, y))
    return {'gaps': gaps, 'lone': lone, 'holes': holes}


# ------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def grid(im, s, major=10, bg=BG):
    big = up(im, s, bg)
    ld = big.load()
    for gx in range(0, big.width, s):
        major_line = (gx // s) % major == 0
        for y in range(big.height):
            c = ld[gx, y]
            t = 0.35 if major_line else 0.12
            col = (255, 80, 200) if major_line else (255, 255, 255)
            ld[gx, y] = tuple(int(c[i] * (1 - t) + col[i] * t) for i in range(3)) + (255,)
    for gy in range(0, big.height, s):
        major_line = (gy // s) % major == 0
        for x in range(big.width):
            c = ld[x, gy]
            t = 0.35 if major_line else 0.12
            col = (255, 80, 200) if major_line else (255, 255, 255)
            ld[x, gy] = tuple(int(c[i] * (1 - t) + col[i] * t) for i in range(3)) + (255,)
    return big


def dump(px, x0, y0, x1, y1):
    lines = ['      ' + ' '.join('%-5d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        row = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(row[i:i + 5] for i in range(0, len(row), 5)))
    return '\n'.join(lines)


def amap(rows, x0, y0, skip='.'):
    out = {}
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        for c, ch in enumerate(row):
            if ch != skip:
                out[(x0 + c, y0 + r)] = ch
    return out


def patch(px, edits):
    """(y, x0, keys): '.' erases, '_' keeps, spaces ignored."""
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            if ch == '.':
                px.pop((x, y), None)
            elif ch != '_':
                px[(x, y)] = ch
            x += 1


def label(im, text, pad=16, bg=(12, 10, 16, 255), col=(225, 222, 235, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), bg)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 2), text, fill=col)
    return out
