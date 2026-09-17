"""Pixel-perfect lace/string polylines with a cast shadow line under them."""
from blib import W, H


def line_pts(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    x, y = x0, y0
    while True:
        pts.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x += sx
        if e2 <= dx:
            err += dx; y += sy
    return pts


def pixel_perfect(pts):
    """Drop L-corner pixels so the path is a clean 1px 8-connected line."""
    out = []
    for p in pts:
        if out and out[-1] == p:
            continue
        out.append(p)
        while len(out) >= 3:
            a, b, c = out[-3], out[-2], out[-1]
            if abs(a[0] - c[0]) == 1 and abs(a[1] - c[1]) == 1 and (b[0] == a[0] or b[1] == a[1]):
                out.pop(-2)
            else:
                break
    return out


def path(poly):
    pts = []
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        seg = line_pts(x0, y0, x1, y1)
        pts.extend(seg if not pts else seg[1:])
    return pixel_perfect(pts)


def draw_lace(L, poly, ch='L', shade_ch='l', shadow='E', cloth='ABCDEF'):
    pts = path(poly)
    s = set(pts)
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        if 0 <= x < W and 0 <= y < H:
            L[y][x] = ch if i < n * 0.55 or True else shade_ch
    for (x, y) in pts:
        yy = y + 1
        if 0 <= x < W and 0 <= yy < H and (x, yy) not in s and L[yy][x] in cloth:
            L[yy][x] = shadow
    return pts
