"""Placing a rig frame into the juggle frame under a turn.

A frame is a key array (0 transparent, else a palette key code). A turn by a multiple of 90 degrees is
an exact pixel permutation, so the art (keylines, faces, paws) survives untouched. Any other turn uses
RotSprite: Scale2x three times (8x, no new colours), inverse-mapped nearest-neighbour, sampled back at
1x. Before a RotSprite turn the silhouette's own black ring is filled with the colour inside it, and
after it the ring is drawn fresh at exactly 1px, so the outline can neither double nor break (the
approach of art_source/mason_juggle/jlib.py). Inverse mapping throughout, so a turn never punches holes.
"""
import math

import numpy as np
from PIL import Image

from pal import PAL

KEYS = sorted(PAL)
CODE = {k: i + 1 for i, k in enumerate(KEYS)}
KEY_OF = {i + 1: k for i, k in enumerate(KEYS)}
BLACK = CODE['k']
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
N8 = N4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))
LUT = np.zeros((len(KEYS) + 1, 4), np.uint8)
for _k, _c in CODE.items():
    LUT[_c] = PAL[_k]


def to_arr(px, w, h, ox=0, oy=0):
    a = np.zeros((h, w), np.uint8)
    for (x, y), k in px.items():
        X, Y = x + ox, y + oy
        if 0 <= X < w and 0 <= Y < h:
            a[Y, X] = CODE[k]
    return a


def to_px(a):
    ys, xs = np.nonzero(a)
    return {(int(x), int(y)): KEY_OF[int(a[y, x])] for y, x in zip(ys, xs)}


def to_img(a):
    return Image.fromarray(LUT[a], 'RGBA')


def from_img(im):
    rgba = np.array(im.convert('RGBA'))
    a = np.zeros(rgba.shape[:2], np.uint8)
    inv = {tuple(v): k for k, v in ((c, tuple(LUT[c])) for c in range(1, len(KEYS) + 1))}
    h, w = a.shape
    for y in range(h):
        for x in range(w):
            p = tuple(rgba[y, x])
            if p[3]:
                a[y, x] = inv[p]
    return a


def scale2x(a):
    h, w = a.shape
    p = np.pad(a, 1, mode='edge')
    P = p[1:-1, 1:-1]
    A = p[:-2, 1:-1]
    D = p[2:, 1:-1]
    C = p[1:-1, :-2]
    B = p[1:-1, 2:]
    out = np.zeros((h * 2, w * 2), np.uint8)
    out[0::2, 0::2] = np.where((C == A) & (C != D) & (A != B), A, P)
    out[0::2, 1::2] = np.where((A == B) & (A != C) & (B != D), B, P)
    out[1::2, 0::2] = np.where((D == C) & (D != B) & (C != A), C, P)
    out[1::2, 1::2] = np.where((B == D) & (B != A) & (D != C), D, P)
    return out


def _shifted(op, dx, dy):
    h, w = op.shape
    pad = np.pad(op, 1)
    return pad[1 + dy:h + 1 + dy, 1 + dx:w + 1 + dx]


def silhouette_ring(a):
    op = a > 0
    ring = np.zeros_like(op)
    for dx, dy in N4:
        ring |= ~_shifted(op, dx, dy)
    return op & ring


def strip_outer(a):
    """The silhouette's black ring, filled with the colour inside it (most common non-black 8-neighbour),
    growing inward until every ring pixel has one."""
    h, w = a.shape
    out = a.copy()
    todo = set(zip(*np.nonzero(silhouette_ring(a) & (a == BLACK))))
    while todo:
        done = []
        for (y, x) in todo:
            c = []
            for dx, dy in N8:
                u, v = x + dx, y + dy
                if 0 <= u < w and 0 <= v < h and out[v, u] and out[v, u] != BLACK and (v, u) not in todo:
                    c.append(int(out[v, u]))
            if c:
                out[y, x] = max(sorted(set(c)), key=c.count)
                done.append((y, x))
        if not done:
            break
        todo -= set(done)
    return out


def exact(theta):
    return abs(theta / 90.0 - round(theta / 90.0)) < 1e-9


def turn(a, theta, pivot, W, H, dest, sx=1.0, sy=1.0, post=(1.0, 1.0)):
    """Place local array `a` into a WxH frame: local point `pivot` lands on `dest`, turned clockwise by
    theta degrees, after a local scale (sx, sy) and before a screen-space scale `post`. Exact for
    multiples of 90 at unit scale."""
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    plain = exact(theta) and sx == 1.0 and sy == 1.0 and tuple(post) == (1.0, 1.0)
    if plain:
        big, f = a, 1
    else:
        big, f = scale2x(scale2x(scale2x(strip_outer(a)))), 8
    bh, bw = big.shape
    Y, X = np.mgrid[0:H, 0:W]
    dx = (X + 0.5 - dest[0]) / post[0]
    dy = (Y + 0.5 - dest[1]) / post[1]
    u = (c * dx + s * dy) / sx + pivot[0]
    v = (-s * dx + c * dy) / sy + pivot[1]
    su = np.floor(u * f + 1e-7).astype(np.int64)
    sv = np.floor(v * f + 1e-7).astype(np.int64)
    ok = (su >= 0) & (su < bw) & (sv >= 0) & (sv < bh)
    out = np.zeros((H, W), np.uint8)
    out[ok] = big[sv[ok], su[ok]]
    if not plain:
        out = tidy(out)
    return out


def tidy(a, passes=2):
    """After a resampled turn: drop crumbs (fewer than two 4-neighbours), close pinholes, and draw the
    silhouette's keyline fresh at 1px."""
    a = a.copy()
    for _ in range(passes):
        op = a > 0
        n = sum(_shifted(op, dx, dy).astype(int) for dx, dy in N4)
        a[op & (n < 2)] = 0
    op = a > 0
    n = sum(_shifted(op, dx, dy).astype(int) for dx, dy in N4)
    for y, x in zip(*np.nonzero(~op & (n == 4))):
        cs = [int(a[y + dy, x + dx]) for dx, dy in N4 if a[y + dy, x + dx] != BLACK]
        a[y, x] = max(sorted(set(cs)), key=cs.count) if cs else BLACK
    a[silhouette_ring(a)] = BLACK
    return a


def over(dst, src):
    """src composited over dst (opaque pixels win)."""
    out = dst.copy()
    m = src > 0
    out[m] = src[m]
    return out


def upscale(im, s, bg=(46, 49, 58, 255)):
    g = Image.new('RGBA', im.size, bg)
    g.alpha_composite(im)
    return g.resize((im.width * s, im.height * s), Image.NEAREST)
