"""Bitmap text helpers: glyph bitmaps, EPX (Scale2x) smoothing, outline/shadow painting."""
from lib import text_width


def bitmap(s, font, spacing=1):
    h = max(len(font[ch]) for ch in s)
    w = text_width(s, font, 1, spacing)
    bm = [[False] * w for _ in range(h)]
    cx = 0
    for ch in s:
        g = font[ch]
        for j, r in enumerate(g):
            for i, c in enumerate(r):
                if c == 'X':
                    bm[j][cx + i] = True
        cx += len(g[0]) + spacing
    return bm


def epx(bm):
    h, w = len(bm), len(bm[0])

    def g(x, y):
        return bm[y][x] if 0 <= x < w and 0 <= y < h else False

    out = [[False] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            P = g(x, y)
            A, B, C, D = g(x, y - 1), g(x + 1, y), g(x - 1, y), g(x, y + 1)
            e1 = e2 = e3 = e4 = P
            if C == A and C != D and A != B:
                e1 = A
            if A == B and A != C and B != D:
                e2 = B
            if D == C and D != B and C != A:
                e3 = C
            if B == D and B != A and D != C:
                e4 = D
            out[2 * y][2 * x] = e1
            out[2 * y][2 * x + 1] = e2
            out[2 * y + 1][2 * x] = e3
            out[2 * y + 1][2 * x + 1] = e4
    return out


def nearest(bm, s):
    return [[bm[y // s][x // s] for x in range(len(bm[0]) * s)] for y in range(len(bm) * s)]


def pixels(bm, x0, y0):
    return {(x0 + x, y0 + y) for y, r in enumerate(bm) for x, v in enumerate(r) if v}


def paint_text(c, pts, fill, outline=None, shadow=None, shadow_off=(0, 2), outline8=False):
    """pts: set of pixels. shadow painted first, then outline ring, then fill."""
    if shadow:
        dx, dy = shadow_off
        sh = set()
        for (x, y) in pts:
            for k in range(1, max(abs(dx), abs(dy)) + 1):
                sx = x + (dx * k) // max(abs(dx), abs(dy))
                sy = y + (dy * k) // max(abs(dx), abs(dy))
                sh.add((sx, sy))
        c.mask(sh - pts, shadow)
    if outline:
        ring = set()
        nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if outline8:
            nb = nb + ((1, 1), (-1, -1), (1, -1), (-1, 1))
        for (x, y) in pts:
            for (dx, dy) in nb:
                q = (x + dx, y + dy)
                if q not in pts:
                    ring.add(q)
        c.mask(ring, outline)
    c.mask(pts, fill)


def size(bm):
    return len(bm[0]), len(bm)
