"""Palette-keyed canvas for the intro-cutscene environment art (DB32 only, alpha 0/255)."""
import math
from pngio import write_png, read_png, upscale

DB32 = {
    'K': '#000000', 'N': '#222034', 'M': '#45283c', 'B': '#663931', 'w': '#8f563b',
    'O': '#df7126', 'd': '#d9a066', 's': '#eec39a', 'Y': '#fbf236', '1': '#99e550',
    '2': '#6abe30', '3': '#37946e', '4': '#4b692f', '5': '#524b24', '6': '#323c39',
    'I': '#3f3f74', '7': '#306082', 'U': '#5b6ee1', 'u': '#639bff', 'c': '#5fcde4',
    'P': '#cbdbfc', 'W': '#ffffff', 'g': '#9badb7', 'F': '#847e87', 'D': '#696a6a',
    'E': '#595652', 'V': '#76428a', 'R': '#ac3232', 'r': '#d95763', '8': '#d77bba',
    '9': '#8f974a', 'A': '#8a6f30',
}
RGB = {k: (int(v[1:3], 16), int(v[3:5], 16), int(v[5:7], 16)) for k, v in DB32.items()}
RGB2KEY = {v: k for k, v in RGB.items()}

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    return (BAYER4[y % 4][x % 4] + 0.5) / 16.0


def hsh(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) / 4294967295.0


def vnoise(x, s=0):
    i = math.floor(x)
    f = x - i
    a, b = hsh(i, 0, s), hsh(i + 1, 0, s)
    t = f * f * (3 - 2 * f)
    return a + (b - a) * t


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    # ---------------------------------------------------------- basics
    def inb(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def set(self, x, y, k):
        if k is None:
            return
        if self.inb(x, y):
            self.p[y][x] = k

    def clear(self, x, y):
        if self.inb(x, y):
            self.p[y][x] = None

    def get(self, x, y):
        return self.p[y][x] if self.inb(x, y) else None

    def rect(self, x0, y0, x1, y1, k):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            row = self.p[y]
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                row[x] = k

    def box(self, x0, y0, x1, y1, k):
        self.hline(x0, x1, y0, k)
        self.hline(x0, x1, y1, k)
        self.vline(x0, y0, y1, k)
        self.vline(x1, y0, y1, k)

    def hline(self, x0, x1, y, k):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, k)

    def vline(self, x, y0, y1, k):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, k)

    def line(self, x0, y0, x1, y1, k):
        for (x, y) in line_pts(x0, y0, x1, y1):
            self.set(x, y, k)

    def dither_rect(self, x0, y0, x1, y1, k, t):
        """Paint k where bayer < t (t in 0..1)."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if bayer(x, y) < t:
                    self.set(x, y, k)

    def recolor(self, x0, y0, x1, y1, mapping, t=1.0, only_if=None):
        for y in range(max(0, y0), min(self.h - 1, y1) + 1):
            for x in range(max(0, x0), min(self.w - 1, x1) + 1):
                c = self.p[y][x]
                if c in mapping and (t >= 1.0 or bayer(x, y) < t):
                    self.p[y][x] = mapping[c]

    def mask(self, pts, k):
        for (x, y) in pts:
            self.set(x, y, k)

    def poly(self, pts, k):
        self.mask(poly_mask(pts, self.w, self.h), k)

    def ellipse(self, cx, cy, rx, ry, k):
        self.mask(ellipse_mask(cx, cy, rx, ry), k)

    def stamp(self, rows, x0, y0, cmap=None):
        """ASCII grid; '.' and ' ' are transparent (skipped). cmap remaps chars to keys."""
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch in '. ':
                    continue
                k = cmap.get(ch, ch) if cmap else ch
                self.set(x0 + i, y0 + j, k)

    def blit(self, other, x0, y0):
        for y in range(other.h):
            for x in range(other.w):
                k = other.p[y][x]
                if k is not None:
                    self.set(x0 + x, y0 + y, k)

    def crop(self, x0, y0, w, h):
        c = Canvas(w, h)
        for y in range(h):
            for x in range(w):
                c.p[y][x] = self.get(x0 + x, y0 + y)
        return c

    # ---------------------------------------------------------- text
    def text(self, x, y, s, font, k, scale=1, spacing=1, shadow=None):
        """Draw text; returns width. shadow=(key,dx,dy) drawn first."""
        if shadow:
            sk, dx, dy = shadow
            self.text(x + dx, y + dy, s, font, sk, scale, spacing)
        cx = x
        for ch in s:
            g = font.get(ch)
            if g is None:
                raise KeyError('glyph missing: %r' % ch)
            gw = len(g[0]) if g else 3
            for j, r in enumerate(g):
                for i, c in enumerate(r):
                    if c == 'X':
                        self.rect(cx + i * scale, y + j * scale, cx + i * scale + scale - 1, y + j * scale + scale - 1, k)
            cx += (gw + spacing) * scale
        return cx - x - spacing * scale

    # ---------------------------------------------------------- io
    def rgba(self):
        return [[(RGB[k] + (255,)) if k is not None else (0, 0, 0, 0) for k in row] for row in self.p]

    def save(self, path, s=1, bg=None):
        rows = self.rgba()
        w, h = self.w, self.h
        if s > 1 or bg is not None:
            w, h, rows = upscale(w, h, rows, s, bg=bg)
        write_png(path, w, h, rows)

    @staticmethod
    def load(path):
        w, h, rows = read_png(path)
        c = Canvas(w, h)
        for y in range(h):
            for x in range(w):
                p = rows[y][x]
                if p[3] == 0:
                    continue
                assert p[3] == 255, ('partial alpha', x, y, p)
                c.p[y][x] = RGB2KEY[p[:3]]
        return c


def text_width(s, font, scale=1, spacing=1):
    return sum((len(font[ch][0]) + spacing) * scale for ch in s) - spacing * scale


# -------------------------------------------------------------- geometry
def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
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


def poly_mask(pts, w=4096, h=4096):
    out = set()
    n = len(pts)
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))) - 1)
    y1 = min(h - 1, int(math.ceil(max(ys))) + 1)
    for y in range(y0, y1 + 1):
        cy = y + 0.5
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= cy < by) or (by <= cy < ay):
                xs.append(ax + (cy - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[0::2], xs[1::2]):
            for x in range(max(0, int(math.ceil(a - 0.5))), min(w - 1, int(math.floor(b - 0.5))) + 1):
                out.add((x, y))
    return out


def ellipse_mask(cx, cy, rx, ry):
    out = set()
    for y in range(int(math.floor(cy - ry)) - 1, int(math.ceil(cy + ry)) + 2):
        for x in range(int(math.floor(cx - rx)) - 1, int(math.ceil(cx + rx)) + 2):
            dx = (x + 0.5 - cx) / rx
            dy = (y + 0.5 - cy) / ry
            if dx * dx + dy * dy <= 1.0:
                out.add((x, y))
    return out


def boundary(mask):
    b = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in mask:
                b.add((x, y))
                break
    return b


def outer_ring(mask):
    """Pixels 4-adjacent to the mask but not in it."""
    r = set()
    for (x, y) in mask:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in mask:
                r.add(q)
    return r
