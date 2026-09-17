"""RotSprite-lite for char canvases: Scale2x x3 (8x), nearest rotate, centre-sample down."""
import math
from jlib import *


def scale2x(g):
    h, w = len(g), len(g[0])
    out = [['.'] * (w * 2) for _ in range(h * 2)]
    for y in range(h):
        for x in range(w):
            P = g[y][x]
            A = g[y - 1][x] if y > 0 else P
            B = g[y][x + 1] if x < w - 1 else P
            C = g[y][x - 1] if x > 0 else P
            D = g[y + 1][x] if y < h - 1 else P
            e0 = e1 = e2 = e3 = P
            if C == A and C != D and A != B:
                e0 = A
            if A == B and A != C and B != D:
                e1 = B
            if D == C and D != B and C != A:
                e2 = C
            if B == D and B != A and D != C:
                e3 = D
            out[2 * y][2 * x] = e0
            out[2 * y][2 * x + 1] = e1
            out[2 * y + 1][2 * x] = e2
            out[2 * y + 1][2 * x + 1] = e3
    return out


def rotate(c, deg, pivot, offset=(0, 0)):
    """Rotate char canvas c by deg (clockwise positive on screen) about pivot (x, y); returns new canvas."""
    g = scale2x(scale2x(scale2x(c)))
    S = 8
    th = math.radians(deg)
    ct, st = math.cos(th), math.sin(th)
    px, py = pivot
    out = blank()
    for y in range(H):
        for x in range(W):
            # output pixel centre relative to pivot (after offset), inverse-rotate into source
            X = x + 0.5 - px - offset[0]
            Y = y + 0.5 - py - offset[1]
            sx = ct * X + st * Y + px
            sy = -st * X + ct * Y + py
            ix, iy = int(math.floor(sx * S)), int(math.floor(sy * S))
            if 0 <= ix < W * S and 0 <= iy < H * S:
                out[y][x] = g[iy][ix]
    return out
