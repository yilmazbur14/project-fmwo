"""Toolkit for Josh's redesigned initial sprite: palette, a layered canvas that keylines every part it
stamps, pixel-centre polygon and ellipse fills, ASCII part maps, and the previews.

A canvas is a dict {(x, y): key}. Parts are dicts of the same shape, stamped back to front; a part
stamped with outline=True draws a 1px black line (cross dilation, so diagonals stay one pixel thin)
over whatever is under its edge, which is where the house style's interior separations come from.
"""
import math
import os

from PIL import Image

W = H = 80
HERE = os.path.dirname(os.path.abspath(__file__))


def hx(s):
    s = s.lstrip('#')
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# One key per colour. Ramps run dark -> light. Hues are Josh's approved ones where he had them.
PAL = {
    'k': hx('000000'),                                   # keyline: pure black, as measured
    # skin
    'a': hx('84412F'), 'b': hx('B86C4E'), 'c': hx('DB976C'), 'd': hx('F0B98E'), 'e': hx('FBD6B0'),
    'p': hx('E0917C'),                                   # lip / blush
    # hair, beard, leather
    'h': hx('130B09'), 'i': hx('24160F'), 'j': hx('3D261A'), 'l': hx('5F3C29'), 'm': hx('8A5B3D'),
    # wine: hat, cravat
    'w': hx('2B0A12'), 'x': hx('4D1420'), 'y': hx('7A2032'), 'z': hx('A63B4B'), 'Z': hx('C96C74'),
    # crimson: coat lining, gloves
    'v': hx('4A0C16'), 'V': hx('861826'), 'R': hx('C2283A'), 'T': hx('E8605A'),
    # gold
    'g': hx('7A5216'), 'G': hx('B07D22'), 'o': hx('E0AB35'), 'O': hx('F5D94E'), 'Y': hx('FFF3B0'),
    'r': hx('E07A2C'),
    # cream: duster, shirt, card faces
    '5': hx('463C2C'), '6': hx('6B5D44'), '7': hx('9E8D68'), '8': hx('C8B994'), '9': hx('E6DBBE'),
    '0': hx('F6EFDC'),
    # indigo: waistcoat, trousers
    'n': hx('14142A'), 'N': hx('20203C'), 's': hx('32335C'), 'S': hx('45487F'), 't': hx('5E63A0'),
    'W': hx('FFFFFF'),
}


#SHAPES (all return sets of pixel coordinates)

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
    # On-edge counts as inside, so a polygon drawn on whole pixels keeps its boundary pixels.
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
    if abs(cross) > 1e-6 * max(1.0, abs(x2 - x1) + abs(y2 - y1)) * 0.5 + 0.35 * math.hypot(x2 - x1, y2 - y1):
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


def fill(pixels, key):
    return {p: key for p in pixels}


def paint(part, pixels, key):
    """Recolour the pixels of `part` that fall inside `pixels` (a clip, never an extension)."""
    for p in pixels:
        if p in part:
            part[p] = key


def rim(part, key, dx, dy, depth=1, only=None):
    """Recolour the pixels of `part` within `depth` steps of its edge in direction (dx, dy): a lit
    rim with (-1, 0), a shadow side with (1, 0), and so on. `only` limits it to pixels of those keys."""
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
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        for p in line(x0, y0, x1, y1):
            if p in part and (only is None or part[p] in only):
                part[p] = key


def amap(rows, x0, y0, skip='.'):
    """An ASCII part map: one character per pixel, `skip` transparent. Spaces are ignored so rows
    can be ruled into groups of five for counting."""
    out = {}
    for r, row in enumerate(rows):
        row = row.replace(' ', '')
        for c, ch in enumerate(row):
            if ch != skip:
                out[(x0 + c, y0 + r)] = ch
    return out


def shift(part, dx, dy):
    return {(x + dx, y + dy): k for (x, y), k in part.items()}


def mirror(part, axis_x):
    return {(2 * axis_x - x, y): k for (x, y), k in part.items()}


#CANVAS

class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.px = {}

    def stamp(self, part, outline=True, keep_line=False):
        """Stamp a part. With outline, a 1px keyline goes round it first, over anything below.
        keep_line: the part's own 'k' pixels do not grow the outline (they are drawn as detail)."""
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

    def erase(self, pixels):
        for p in pixels:
            self.px.pop(p, None)

    def image(self):
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        for (x, y), k in self.px.items():
            im.putpixel((x, y), PAL[k])
        return im


#MEASURING

def stats(im):
    px = [c for c in im.getdata() if c[3] > 0] if not hasattr(im, 'get_flattened_data') \
        else [c for c in im.get_flattened_data() if c[3] > 0]
    black = sum(1 for c in px if c[:3] == (0, 0, 0))
    return {'opaque': len(px), 'colours': len(set(px)), 'black': black / max(1, len(px))}


#PREVIEWS

BG = (46, 49, 58, 255)


def upscale(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def on_bg(im, bg=BG, pad=0):
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), bg)
    out.alpha_composite(im, (pad, pad))
    return out


def grid(im, s, every=1, col=(255, 255, 255, 28), major=10, major_col=(255, 80, 200, 90)):
    """An upscaled copy with a pixel grid, for placing things by coordinate."""
    big = upscale(on_bg(im), s)
    px = big.load()
    for gx in range(0, big.width, s * every):
        c = major_col if (gx // s) % major == 0 else col
        for y in range(big.height):
            px[gx, y] = _blend(px[gx, y], c)
    for gy in range(0, big.height, s * every):
        c = major_col if (gy // s) % major == 0 else col
        for x in range(big.width):
            px[x, gy] = _blend(px[x, gy], c)
    return big


def _blend(a, b):
    t = b[3] / 255.0
    return (int(a[0] * (1 - t) + b[0] * t), int(a[1] * (1 - t) + b[1] * t), int(a[2] * (1 - t) + b[2] * t), 255)


#HAND EDITS

def dump(px, x0, y0, x1, y1):
    """Rows of keys for a region (inclusive), ruled in fives, labelled with their y."""
    lines = ['      ' + ' '.join('%-5d' % x for x in range(x0, x1 + 1, 5))]
    for y in range(y0, y1 + 1):
        row = ''.join(px.get((x, y), '.') for x in range(x0, x1 + 1))
        lines.append('%3d:  ' % y + ' '.join(row[i:i + 5] for i in range(0, len(row), 5)))
    return '\n'.join(lines)


def patch(px, edits):
    """Overwrite horizontal spans: edits are (y, x0, keys). In keys, '.' erases, '_' keeps, spaces
    are ignored so spans can be ruled in fives."""
    for y, x0, keys in edits:
        x = x0
        for ch in keys.replace(' ', ''):
            if ch == '.':
                px.pop((x, y), None)
            elif ch != '_':
                px[(x, y)] = ch
            x += 1
