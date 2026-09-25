"""Shared drawing for Danny's floor effects on the green canvas: cracks (the mat's own greens: a K core, k
sides, a lifted edge n catching the light and its shade m), dust (his cool whites and grey-blue: W Q P g,
canvas powder), and chips of mat thrown up (n m k). No keyline.
"""
import math
import random


def zigzag(x0, y0, x1, y1, seed, jag=1.2, step=2.5):
    """A crack's path from (x0,y0) to (x1,y1): straight runs with small random kinks."""
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
    """The texels a polyline passes through (a 4-connected path, no gaps)."""
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


def crack(g, pts, wide=False, lip=True):
    """Draw a crack along pts: a K core (two texels where `wide`), a lifted lit lip n on its upper-left side
    and a shaded lip m on the other (only onto empty texels or other floor keys)."""
    H, W = len(g), len(g[0])
    floor = set('.nmkK')
    core = line_texels(pts)
    for (x, y) in core:
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = 'K'
            if wide and 0 <= y + 1 < H and g[y + 1][x] in floor:
                g[y + 1][x] = 'k'
    if not lip:
        return
    for (x, y) in core:
        for (dx, dy, k) in ((0, -1, 'n'), (-1, 0, 'n'), (0, 1, 'm'), (1, 0, 'm')):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H and g[yy][xx] == '.':
                g[yy][xx] = k


# Dust thinning out in stepped alpha: each dust key's version at alpha 168 and at 96 (frame-local keys).
DUST_KEYS = 'WQPgN'
DUST_ALPHA = {168: dict(zip('ACHIT', ('FFFFFF', 'F0F5FF', 'CBDBFC', '8595B8', '3F3F74'))),
              96: dict(zip('UXabc', ('FFFFFF', 'F0F5FF', 'CBDBFC', '8595B8', '3F3F74')))}


def dust_alpha(g, level):
    """Swap every dust texel in g for its alpha-`level` key; returns the frame-local palette for them."""
    keys = list(DUST_ALPHA[level].keys())
    for row in g:
        for x, k in enumerate(row):
            if k in DUST_KEYS:
                row[x] = keys[DUST_KEYS.index(k)]
    from dfx_pal import hx
    return {k: hx(v, level) for k, v in DUST_ALPHA[level].items()}


def puff(g, cx, cy, r, shade=0, keys='WQPgN', squash=1.0):
    """A dust puff lit from the top left, `squash` times as tall as wide: shade 0 is fresh (white heart),
    higher is greyer. Only onto empty texels, crack or chips (dust sits in front of the floor marks)."""
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
            if g[y][x] in '.nmkK' or g[y][x] in keys:
                cur = keys.index(g[y][x]) if g[y][x] in keys else 99
                if i < cur or g[y][x] not in keys:
                    g[y][x] = keys[i]


def chip(g, x, y, big=False):
    """A chip of mat thrown up: its lit top over a dark underside (3x2 when big, 1x2 when not), so it reads
    against the mat it came from."""
    H, W = len(g), len(g[0])
    cells = [(0, 0, 'n'), (0, 1, 'K')] + ([(1, 0, 'n'), (2, 0, 'm'), (1, 1, 'k'), (2, 1, 'K')] if big else [])
    for (dx, dy, k) in cells:
        xx, yy = int(x) + dx, int(y) + dy
        if 0 <= xx < W and 0 <= yy < H:
            g[yy][xx] = k
