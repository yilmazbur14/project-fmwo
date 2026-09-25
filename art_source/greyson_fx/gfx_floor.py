"""Shared drawing for Greyson's floor effects on the green canvas: cracks (the mat's own greens: a Q core, q
sides, a lifted lit lip n and its shade m), chalk dust (W w E e f), chips of mat (n m q Q). No keyline.
"""
import math
import random


def zigzag(x0, y0, x1, y1, seed, jag=1.2, step=2.5):
    rnd = random.Random(seed)
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    n = max(2, int(L / step))
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    pts = []
    for i in range(n + 1):
        t = i / n
        j = rnd.uniform(-jag, jag) if 0 < i < n else 0.0
        pts.append((x0 + (x1 - x0) * t + nx * j, y0 + (y1 - y0) * t + ny * j))
    return pts


def line_texels(pts):
    out = []
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        n = int(max(abs(bx - ax), abs(by - ay)) * 2) + 1
        for k in range(n + 1):
            t = k / n
            p = (int(math.floor(ax + (bx - ax) * t)), int(math.floor(ay + (by - ay) * t)))
            if not out or out[-1] != p:
                if out and abs(out[-1][0] - p[0]) + abs(out[-1][1] - p[1]) == 2:
                    out.append((p[0], out[-1][1]))
                out.append(p)
    return out


def crack(g, pts, core='Q', lip=('n', 'm'), wide=False, only_empty_lip=True):
    H, W = len(g), len(g[0])
    tex = line_texels(pts)
    for (x, y) in tex:
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = core
            if wide and y + 1 < H:
                g[y + 1][x] = core
    if lip:
        for (x, y) in tex:
            for (dx, dy, k) in ((0, -1, lip[0]), (-1, 0, lip[0]), (0, 1 + (1 if wide else 0), lip[1]), (1, 0, lip[1])):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and (g[yy][xx] == '.' or not only_empty_lip):
                    g[yy][xx] = k
    return tex


def puff(g, cx, cy, r, shade=0, keys='WwEef', squash=1.0, only_empty=True):
    H, W = len(g), len(g[0])
    for y in range(max(0, int(cy - r) - 1), min(H, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(W, int(cx + r) + 2)):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) / squash
            d = math.hypot(dx, dy)
            if d > r:
                continue
            hl = math.hypot(dx + 0.32 * r, dy + 0.38 * r)
            i = 0 if hl < 0.45 * r else (1 if hl < 0.8 * r else 2)
            if d > r - 1.1 and dx + dy > 0.2 * r:
                i = 3
            i = min(len(keys) - 1, i + shade)
            cur = g[y][x]
            if cur in keys:
                if i < keys.index(cur):
                    g[y][x] = keys[i]
            elif cur == '.' or not only_empty or cur in 'nmqQ':
                g[y][x] = keys[i]


def chip(g, x, y, big=True):
    H, W = len(g), len(g[0])
    cells = [(0, 0, 'n'), (0, 1, 'Q')] + ([(1, 0, 'n'), (2, 0, 'm'), (1, 1, 'q'), (2, 1, 'Q')] if big else [])
    for (dx, dy, k) in cells:
        xx, yy = int(x) + dx, int(y) + dy
        if 0 <= xx < W and 0 <= yy < H:
            g[yy][xx] = k
