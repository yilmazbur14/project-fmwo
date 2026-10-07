"""Jordan's room - shared canvas, palette and drawing helpers.

Everything is authored on the game's 3x grid: 1 texel = 3 screen px, so the
room is 640x360 texels -> 1920x1080 on screen, exactly like the arena
(arena_ringside.png) and the intro street (street_buildings.png).

Palette: DawnBringer 32 only, the palette of the intro street, the poster
close-up and the controls room. Keyline: pure black #000000 on props, none on
the big surfaces (wall paper, floor boards), matching those environment sheets.

Pixels are palette keys (one char each, same keys as art_source/cutscene_env)
stored as small ints in a numpy array; 255 is transparent. Nothing here writes
files - see jr_export.py.
"""
import math

import numpy as np

# ---------------------------------------------------------------- palette
DB32 = [
    ('K', '000000'), ('N', '222034'), ('M', '45283c'), ('B', '663931'),
    ('w', '8f563b'), ('O', 'df7126'), ('d', 'd9a066'), ('s', 'eec39a'),
    ('Y', 'fbf236'), ('1', '99e550'), ('2', '6abe30'), ('3', '37946e'),
    ('4', '4b692f'), ('5', '524b24'), ('6', '323c39'), ('I', '3f3f74'),
    ('7', '306082'), ('U', '5b6ee1'), ('u', '639bff'), ('c', '5fcde4'),
    ('P', 'cbdbfc'), ('W', 'ffffff'), ('g', '9badb7'), ('F', '847e87'),
    ('D', '696a6a'), ('E', '595652'), ('V', '76428a'), ('R', 'ac3232'),
    ('r', 'd95763'), ('8', 'd77bba'), ('9', '8f974a'), ('A', '8a6f30'),
]
KEYS = ''.join(k for k, _ in DB32)
IDX = {k: i for i, (k, _) in enumerate(DB32)}
RGB = np.array([[int(h[i:i + 2], 16) for i in (0, 2, 4)] for _, h in DB32], np.uint8)
T = 255                      # transparent
W, H = 640, 360              # native room size in texels
SCALE = 3                    # game scale

# one step darker, staying in the colour's own hue family
DARKER = {
    'W': 'P', 'P': 'g', 'g': 'F', 'F': 'D', 'D': 'E', 'E': '6', '6': 'N', 'N': 'K', 'K': 'K',
    's': 'd', 'd': 'w', 'w': 'B', 'B': 'M', 'M': 'N',
    'Y': 'd', 'A': '5', '5': 'N', 'O': 'w',
    'r': 'R', 'R': 'B', '8': 'V', 'V': 'M',
    'c': '7', 'u': 'U', 'U': 'I', '7': 'I', 'I': 'N',
    '1': '2', '2': '3', '3': '4', '4': '6', '9': '5',
}


def ix(k):
    """palette key (or index) -> index"""
    if isinstance(k, (int, np.integer)):
        return int(k)
    return IDX[k]


def darker(k, n=1):
    for _ in range(n):
        k = DARKER[k]
    return k


# ---------------------------------------------------------------- dithering
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])


def bayer(x, y):
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0


def hsh(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def smooth(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def ramp_pick(ramp, t, x, y):
    """t in [0,1] over a dark->light ramp of keys, ordered-dithered between steps."""
    n = len(ramp) - 1
    v = min(max(t, 0.0), 1.0) * n
    i = int(v)
    if i >= n:
        return ramp[n]
    return ramp[i + 1] if (v - i) > bayer(x, y) else ramp[i]


def band_index(n, t, x, y, w=0.14):
    """Like ramp_pick but flat inside each step: the ordered dither only fills a
    narrow band (2w of a step) around each threshold, as the street art does."""
    v = min(max(t, 0.0), 1.0) * n
    i = int(v)
    if i >= n:
        return n
    f = v - i
    if f < 0.5 - w:
        return i
    if f > 0.5 + w:
        return i + 1
    return i + 1 if (f - (0.5 - w)) / (2 * w) > bayer(x, y) else i


def band_pick(ramp, t, x, y, w=0.14):
    return ramp[band_index(len(ramp) - 1, t, x, y, w)]


# ---------------------------------------------------------------- geometry
def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def poly_mask(pts, w=W, h=H):
    """Filled polygon (pixel centres inside, even-odd) -> bool array."""
    m = np.zeros((h, w), bool)
    ys = [p[1] for p in pts]
    n = len(pts)
    for y in range(max(0, int(math.floor(min(ys)))), min(h, int(math.ceil(max(ys))) + 1)):
        yc = y + 0.5
        xs = []
        for i in range(n):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            x0 = int(math.ceil(xs[j] - 0.5))
            x1 = int(math.floor(xs[j + 1] - 0.5))
            if x1 >= x0:
                m[y, max(0, x0):min(w, x1 + 1)] = True
    return m


def ellipse_mask(cx, cy, rx, ry, w=W, h=H):
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1.0


def rect_mask(x0, y0, x1, y1, w=W, h=H):
    m = np.zeros((h, w), bool)
    m[max(0, y0):min(h, y1 + 1), max(0, x0):min(w, x1 + 1)] = True
    return m


def border(mask, diag=False):
    """Pixels outside mask that touch it (4-neighbour, or 8 with diag)."""
    m = mask
    g = np.zeros_like(m)
    g[1:, :] |= m[:-1, :]
    g[:-1, :] |= m[1:, :]
    g[:, 1:] |= m[:, :-1]
    g[:, :-1] |= m[:, 1:]
    if diag:
        g[1:, 1:] |= m[:-1, :-1]
        g[1:, :-1] |= m[:-1, 1:]
        g[:-1, 1:] |= m[1:, :-1]
        g[:-1, :-1] |= m[1:, 1:]
    return g & ~m


def inner_edge(mask):
    """Pixels of mask that touch the outside (4-neighbour)."""
    return mask & border(~mask)


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.a = np.full((h, w), T, np.uint8)

    def copy(self):
        c = Canvas(self.w, self.h)
        c.a = self.a.copy()
        return c

    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, k):
        if k is None:
            return
        if 0 <= x < self.w and 0 <= y < self.h:
            self.a[y, x] = ix(k)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            v = int(self.a[y, x])
            return None if v == T else KEYS[v]
        return None

    def rect(self, x0, y0, x1, y1, k):
        if x1 < x0 or y1 < y0:
            return
        self.a[max(0, y0):min(self.h, y1 + 1), max(0, x0):min(self.w, x1 + 1)] = ix(k)

    def hline(self, x0, x1, y, k):
        self.rect(min(x0, x1), y, max(x0, x1), y, k)

    def vline(self, x, y0, y1, k):
        self.rect(x, min(y0, y1), x, max(y0, y1), k)

    def box(self, x0, y0, x1, y1, k):
        self.hline(x0, x1, y0, k)
        self.hline(x0, x1, y1, k)
        self.vline(x0, y0, y1, k)
        self.vline(x1, y0, y1, k)

    def line(self, x0, y0, x1, y1, k):
        for (x, y) in line_pts(x0, y0, x1, y1):
            self.set(x, y, k)

    def fill(self, mask, k):
        self.a[mask] = ix(k)

    def poly(self, pts, k):
        self.fill(poly_mask(pts, self.w, self.h), k)

    def ellipse(self, cx, cy, rx, ry, k):
        self.fill(ellipse_mask(cx, cy, rx, ry, self.w, self.h), k)

    def opaque(self):
        return self.a != T

    def stamp(self, rows, x0, y0, legend=None, flip=False):
        """ASCII grid; '.' and ' ' are transparent. legend maps local chars to palette keys."""
        if isinstance(rows, str):
            rows = [r for r in rows.strip('\n').split('\n')]
        wmax = max(len(r) for r in rows)
        for j, r in enumerate(rows):
            if flip:
                r = r.ljust(wmax, '.')[::-1]
            for i, ch in enumerate(r):
                if ch in '. ':
                    continue
                k = legend.get(ch, ch) if legend else ch
                if k is None:
                    continue
                self.set(x0 + i, y0 + j, k)

    def blit(self, other, x0=0, y0=0):
        """Paste other's opaque pixels at (x0, y0)."""
        sh, sw = other.a.shape
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(self.w, x0 + sw), min(self.h, y0 + sh)
        if X1 <= X0 or Y1 <= Y0:
            return
        src = other.a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        dst = self.a[Y0:Y1, X0:X1]
        m = src != T
        dst[m] = src[m]

    def keyline(self, k='K', diag=False):
        """Black line hugging the outside of everything opaque."""
        b = border(self.opaque(), diag)
        self.a[b] = ix(k)

    def recolor(self, mapping, mask=None):
        a = self.a
        for s, d in mapping.items():
            m = a == ix(s)
            if mask is not None:
                m &= mask
            a[m] = ix(d)

    def darken(self, mask, steps=1):
        for _ in range(steps):
            vals = self.a[mask]
            out = vals.copy()
            for i, k in enumerate(KEYS):
                out[vals == i] = IDX[DARKER[k]]
            self.a[mask] = out

    def rgba(self):
        out = np.zeros((self.h, self.w, 4), np.uint8)
        m = self.a != T
        out[m, :3] = RGB[self.a[m]]
        out[m, 3] = 255
        return out

    def bbox(self):
        ys, xs = np.nonzero(self.a != T)
        if len(xs) == 0:
            return None
        return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def from_rows(rows, legend=None, flip=False):
    """Canvas sized to an ASCII sprite."""
    if isinstance(rows, str):
        rows = [r for r in rows.strip('\n').split('\n')]
    w = max(len(r) for r in rows)
    c = Canvas(w, len(rows))
    c.stamp(rows, 0, 0, legend, flip)
    return c


def to_image(canvas, scale=1):
    from PIL import Image
    im = Image.fromarray(canvas.rgba(), 'RGBA')
    if scale != 1:
        im = im.resize((canvas.w * scale, canvas.h * scale), Image.NEAREST)
    return im
