"""Captain Burak's kit: his palette, a layered canvas that keylines every part it stamps, pixel-centre
polygon / ellipse / capsule fills, normal-based form shading, ASCII part maps, and preview helpers.

Self-contained on purpose: it imports nothing from other characters' rigs, so edits elsewhere can't
change this sprite, and running it can't write bytecode into anyone else's folder.

A canvas is a dict {(x, y): key}. Parts are dicts of the same shape, stamped back to front; a part
stamped with outline=True first draws a 1px black line (cross dilation, so diagonals stay one pixel
thin) round itself over whatever is below. That is where the house style's interior separations
come from.

Nothing here writes into Assets/.
"""
import math
import os
import sys

sys.dont_write_bytecode = True
from PIL import Image, ImageDraw  # noqa: E402

W = H = 96
HERE = os.path.dirname(os.path.abspath(__file__))


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour. Ramps run light -> dark unless noted.
PAL = {
    'k': hx('000000'),                                   # keyline: pure black, the house convention
    # skin: the player Burak's own six tones (player_4dir_sheet.png / bust_burak.png), so the boss
    # and the player read as the same man
    '1': hx('F0BE8C'), '2': hx('E2A874'), '3': hx('D79864'), '4': hx('BE8254'), '5': hx('AC714F'),
    '6': hx('7A4A33'),
    'p': hx('C8705E'),                                   # lower lip
    's': hx('A88068'),                                   # stubble: a greyed skin shadow
    # hair: near-black with a warm brown sheen (17.jpg), darkest -> sheen
    'h': hx('0D0909'), 'i': hx('1A1212'), 'j': hx('2A1D19'), 'l': hx('36251E'), 'm': hx('503729'),
    # black felt and leather: tricorn, boots, belt, cannonball (cool, so the hair stays separate)
    'q': hx('15151D'), 'r': hx('23232F'), 't': hx('353547'), 'u': hx('4E4F66'),
    # gold: hat trim, coat trim and buttons, buckle, knuckle-bow, pistol brass, muzzle flash
    'Y': hx('FFF3B0'), 'O': hx('F5D94E'), 'o': hx('E0AB35'), 'G': hx('B07D22'), 'g': hx('7A5216'),
    # crimson: the captain's greatcoat
    'U': hx('F07F7A'), 'T': hx('D8434F'), 'R': hx('B02436'), 'V': hx('7E162B'), 'v': hx('4A0C1B'),
    # sash red: the player's headband red, so the sash and bandana tie back to him
    'y': hx('D95763'), 'X': hx('AC3232'), 'x': hx('6E1F22'),
    # his white tee (warm), also eye whites, teeth and the smoke
    'W': hx('FFFCF4'), 'w': hx('E8E1D3'), 'e': hx('C3B9A9'), 'f': hx('8F877B'),
    # steel and silver (cool): cutlass blade, figaro chain, pistol lock
    'B': hx('DCE3EE'), 'A': hx('A6AFC1'), 'Z': hx('6D7589'), 'z': hx('444A5C'),
    # dark brown: trousers, pistol stock, irises
    '0': hx('7C5438'), '9': hx('5C3B28'), '8': hx('41291C'), '7': hx('281810'),
}

RAMPS = {
    'skin': '123456', 'hair': 'mljih', 'felt': 'utrq', 'gold': 'YOoGg', 'coat': 'UTRVv',
    'sash': 'yXx', 'tee': 'Wwef', 'steel': 'BAZz', 'brown': '0987',
}


# ------------------------------------------------------------------ shapes (sets of pixels)

def poly(pts):
    """Pixels whose centre is inside the polygon (vertices in pixel-centre coordinates) or on it."""
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
    cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross) > 0.35 * math.hypot(x2 - x1, y2 - y1) + 1e-9:
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
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


def line(x0, y0, x1, y1):
    """Bresenham, inclusive."""
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
    for (a, b) in zip(pts, pts[1:]):
        seg = line(a[0], a[1], b[0], b[1])
        out.extend(seg if not out else seg[1:])
    return out


def bez(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def curve(p0, c, p1, n=24):
    """A quadratic Bezier as a list of whole pixels (no repeats)."""
    out = []
    for i in range(n + 1):
        x, y = bez(p0, c, p1, i / float(n))
        q = (int(round(x)), int(round(y)))
        if not out or out[-1] != q:
            out.append(q)
    return out


# ------------------------------------------------------------------ parts (dicts)

def fill(pixels, key):
    return {p: key for p in pixels}


def paint(part, pixels, key, only=None):
    """Recolour the pixels of `part` that fall inside `pixels` (a clip, never an extension)."""
    for p in pixels:
        if p in part and (only is None or part[p] in only):
            part[p] = key


def rim(part, key, dx, dy, depth=1, only=None):
    """Recolour the pixels of `part` within `depth` steps of its edge in direction (dx, dy)."""
    body = set(part)
    hits = []
    for (x, y) in body:
        if only is not None and part[(x, y)] not in only:
            continue
        for d in range(1, depth + 1):
            if (x + dx * d, y + dy * d) not in body:
                hits.append((x, y))
                break
    for p in hits:
        part[p] = key


def stroke(part, pts, key, only=None):
    """Recolour the pixels of `part` along a polyline."""
    for p in polyline(pts):
        if p in part and (only is None or part[p] in only):
            part[p] = key


def amap(rows, x0, y0, skip='.'):
    """An ASCII part map: one character per pixel, `skip` transparent. Spaces are ignored so rows
    can be ruled into groups of five."""
    out = {}
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        for c, ch in enumerate(row):
            if ch != skip:
                out[(x0 + c, y0 + r)] = ch
    return out


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def mirror(part, axis2=96):
    """Mirror about x = axis2 / 2 (x' = axis2 - x)."""
    return {(axis2 - x, y): k for (x, y), k in part.items()}


# ------------------------------------------------------------------ form shading

LIGHT3 = (-0.55, -0.62, 0.56)       # toward the light: left, up and out of the screen (the cast's light)
_l = math.sqrt(sum(c * c for c in LIGHT3))
LIGHT3 = tuple(c / _l for c in LIGHT3)


def tone(i, ramp, cuts):
    """ramp: keys light -> dark; cuts: descending intensity thresholds, one fewer than the ramp."""
    for k, c in zip(ramp, cuts):
        if i >= c:
            return k
    return ramp[-1]


def lum(n):
    ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
    return (n[0] * LIGHT3[0] + n[1] * LIGHT3[1] + n[2] * LIGHT3[2]) / ln


def ellipsoid(part, cx, cy, rx, ry, ramp, cuts, only=None, bulge=1.0):
    """Shade `part` as the front of an ellipsoid centred (cx, cy)."""
    for (x, y) in list(part):
        if only is not None and part[(x, y)] not in only:
            continue
        u = (x - cx) / rx
        v = (y - cy) / ry
        z = math.sqrt(max(0.0, 1.0 - min(1.0, u * u + v * v))) * bulge
        part[(x, y)] = tone(lum((u, v, z)), ramp, cuts)


def cylinder(part, p0, p1, r, ramp, cuts, only=None, tilt=0.0, offset=0.0):
    """Shade `part` as a cylinder of radius r along p0 -> p1. `tilt` leans the surface toward the
    light along the axis; `offset` slides the round's centre across the axis (px)."""
    (x0, y0), (x1, y1) = p0, p1
    ax, ay = x1 - x0, y1 - y0
    al = math.hypot(ax, ay) or 1.0
    ax, ay = ax / al, ay / al
    nx, ny = -ay, ax
    for (x, y) in list(part):
        if only is not None and part[(x, y)] not in only:
            continue
        s = ((x - x0) * nx + (y - y0) * ny - offset) / r
        s = max(-1.0, min(1.0, s))
        z = math.sqrt(max(0.0, 1.0 - s * s))
        part[(x, y)] = tone(lum((s * nx - tilt * ax, s * ny - tilt * ay, z)), ramp, cuts)


def span(pixels, y):
    xs = [x for (x, yy) in pixels if yy == y]
    return (min(xs), max(xs)) if xs else None


# ------------------------------------------------------------------ canvas

class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}
        self.own = {}                  # which part put each pixel there ('line' for a stamped keyline)

    def stamp(self, part, outline=True, owner=None):
        """Stamp a part; with outline, a 1px keyline goes round it first, over anything below.
        outline='soft': the part's own black pixels are its line already, so only its other pixels
        grow the keyline (no doubled edges on hand-drawn parts). owner: a name recorded for each
        pixel, so later passes (the juggle's relight) can ask what a pixel belongs to."""
        if outline:
            body = set(part)
            for (x, y) in body:
                if outline == 'soft' and part[(x, y)] == 'k':
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in body and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                        self.px[q] = 'k'
                        self.own[q] = 'line'
        for q, k in part.items():
            if 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                self.px[q] = k
                self.own[q] = owner

    def erase(self, pixels):
        for p in pixels:
            self.px.pop(p, None)


def image(px, w=W, h=H):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PAL[k])
    return im


# ------------------------------------------------------------------ hand edits

def dump(px, x0, y0, x1, y1):
    """Rows of keys for a region (inclusive), ruled in fives, labelled with their y."""
    lines = ['      ' + ' '.join('%-5d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        row = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(row[i:i + 5] for i in range(0, len(row), 5)))
    return '\n'.join(lines)


def patch(px, edits):
    """Overwrite horizontal spans: edits are (y, x0, keys). In keys '.' erases, '_' keeps, spaces are
    ignored so spans can be ruled in fives."""
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            if ch == '.':
                px.pop((x, y), None)
            elif ch != '_':
                px[(x, y)] = ch
            x += 1


# ------------------------------------------------------------------ measuring

def pixels_of(im):
    flat = getattr(im, 'get_flattened_data', None)
    return list(flat() if flat else im.getdata())


def stats(im):
    px = [c for c in pixels_of(im) if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': black / max(1, len(px))}


# ------------------------------------------------------------------ previews

BG = (46, 49, 58, 255)
DARK = (10, 10, 12, 255)


def up(im, s, bg=BG):
    base = Image.new('RGBA', im.size, bg)
    base.alpha_composite(im)
    return base.resize((im.width * s, im.height * s), Image.NEAREST)


def row(ims, gap=8, bg=DARK):
    w = sum(i.width for i in ims) + gap * (len(ims) - 1)
    h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), bg)
    x = 0
    for i in ims:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def label(im, text, pad=18, col=(220, 220, 228, 255)):
    out = Image.new('RGBA', (im.width, im.height + pad), DARK)
    out.paste(im, (0, pad))
    ImageDraw.Draw(out).text((4, 3), text, fill=col)
    return out


def grid(im, s, x0=0, y0=0, major=5):
    """An upscaled copy with a pixel grid; major lines every `major` px of the ORIGINAL coordinates
    (x0, y0 are the crop's origin, so the major lines land on multiples of `major`)."""
    big = up(im, s)
    p = big.load()
    for gx in range(big.width // s):
        c = (255, 80, 200, 110) if (gx + x0) % major == 0 else (255, 255, 255, 26)
        for y in range(big.height):
            p[gx * s, y] = _blend(p[gx * s, y], c)
    for gy in range(big.height // s):
        c = (255, 80, 200, 110) if (gy + y0) % major == 0 else (255, 255, 255, 26)
        for x in range(big.width):
            p[x, gy * s] = _blend(p[x, gy * s], c)
    return big


def _blend(a, b):
    t = b[3] / 255.0
    return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t), int(a[2] * (1 - t) + b[2] * t), 255)


# ------------------------------------------------------------------ locks of hair

def lock(base, tip, w0, w1, bend=0.0, n=20):
    """A curved, tapering lock from `base` to `tip`: half-width w0 at the base, w1 at the tip, bowed
    sideways by `bend` px (positive bows toward the left of the base->tip direction). Returns
    {pixel: (t, s)} with t its 0..1 position along the lock and s its signed offset across it
    (-1..1, negative on the bowed side)."""
    mx, my = (base[0] + tip[0]) / 2.0, (base[1] + tip[1]) / 2.0
    dx, dy = tip[0] - base[0], tip[1] - base[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = dy / ln, -dx / ln                     # left normal of the direction (screen coords)
    c = (mx + nx * bend, my + ny * bend)
    spine = [bez(base, c, tip, i / float(n)) for i in range(n + 1)]
    left, right = [], []
    for i, p in enumerate(spine):
        a = spine[max(0, i - 1)]
        b = spine[min(n, i + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        ox, oy = ty / tl, -tx / tl
        t = i / float(n)
        w = w0 + (w1 - w0) * t
        left.append((p[0] + ox * w, p[1] + oy * w))
        right.append((p[0] - ox * w, p[1] - oy * w))
    px = poly(left + [tip] + list(reversed(right)))
    out = {}
    for q in px:
        best, bi = 1e9, 0
        for i, sp in enumerate(spine):
            d = (q[0] - sp[0]) ** 2 + (q[1] - sp[1]) ** 2
            if d < best:
                best, bi = d, i
        a = spine[max(0, bi - 1)]
        b = spine[min(n, bi + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]
        tl = math.hypot(tx, ty) or 1.0
        ox, oy = ty / tl, -tx / tl
        t = bi / float(n)
        w = max(0.6, w0 + (w1 - w0) * t)
        s = ((q[0] - spine[bi][0]) * ox + (q[1] - spine[bi][1]) * oy) / w
        # (t, s, nx, ny): (nx, ny) is the unit vector across the lock toward positive s
        out[q] = (t, max(-1.0, min(1.0, -s)), -ox, -oy)
    return out


def shade_lock(info, ramp, cuts, tip_dark=0.8, root_dark=0.12):
    """Tones for a lock from lock(): lit as a round strand from the cast's upper-left light, one
    step darker at the tip and in the hat's shadow at the root."""
    part = {}
    for q, (t, s, nx, ny) in info.items():
        z = math.sqrt(max(0.0, 1.0 - s * s))
        i = lum((s * nx, s * ny, z))
        k = tone(i, ramp, cuts)
        idx = ramp.index(k)
        if t > tip_dark or t < root_dark:
            idx = min(len(ramp) - 1, idx + 1)
        part[q] = ramp[idx]
    return part
