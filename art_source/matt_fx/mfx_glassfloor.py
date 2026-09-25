"""matt_glass_floor.png: the bed of glass on rows B and A. 1 frame of 64x60, tiled left to right.
THE PIVOT IS THE TOP-LEFT (0, 0); the code tiles it across the glass band (Rect2(113, 787, 1692, 180), 60
texels tall at 3x) as Sprite2D regions with repeat. It is seamless left to right (column 63 meets column 0);
it is exactly one tile tall.

The plan's glass ramp (#FFFFFF #E6FBFF #B8ECF5 #7FC9DB #4D8FA6), no keyline, two stepped alphas:
  rows 0-6    the jagged danger edge: a row of upright shards like broken bottle tops, 4-7 texels tall and
              4-7 wide, lit (white, then #E6FBFF) on their left faces and #4D8FA6 on their right faces, on a
              dark #4D8FA6 foot
  rows 7-59   the bed: a translucent sheen (#B8ECF5 at alpha 96, the mat showing through, lightened) with
              glass slivers scattered on it (Poisson-spaced, wrapping left to right so the tile repeats):
              each a light #E6FBFF or #B8ECF5 sliver with a white edge on its upper-left side, a dark edge
              opposite, and a drop shadow (#4D8FA6 at alpha 150) down-right of it on the floor
"""
import math
import random

import mfx_pal as pal

W, H = 64, 60
EDGE = 6
FRAME_SIZE = (64, 60)
NOTE = '1 frame, tiled left to right; top-left pivot; the top 6 rows are the danger edge'
SEED = 20260923


def wrap_dx(a, b):
    d = abs(a - b) % W
    return min(d, W - d)


def tri_contains(px, py, a, b, c):
    def side(p, q, r):
        return (p[0] - r[0]) * (q[1] - r[1]) - (q[0] - r[0]) * (p[1] - r[1])
    d1, d2, d3 = side((px, py), a, b), side((px, py), b, c), side((px, py), c, a)
    neg = d1 < 0 or d2 < 0 or d3 < 0
    pos = d1 > 0 or d2 > 0 or d3 > 0
    return not (neg and pos)


# Local keys for the tile's translucent parts (stepped alpha, the ramp's own colours).
LOCAL = {
    '~': (0xB8, 0xEC, 0xF5, 96),      # the sheen over the whole bed: the mat shows through, lightened
    ':': (0x4D, 0x8F, 0xA6, 150),     # a shard's drop shadow on the floor
}


def poisson(rnd, n_try, min_d):
    """Points over the bed, no two closer than min_d (distance wraps left to right)."""
    pts = []
    for _ in range(n_try):
        x, y = rnd.uniform(0, W), rnd.uniform(EDGE + 3, H - 2)
        if all(math.hypot(wrap_dx(x, px), y - py) >= min_d for (px, py) in pts):
            pts.append((x, y))
    return pts


def sliver(rnd, cx, cy):
    """One shard: a sharp triangle, long and thin, at a random angle."""
    length = rnd.uniform(7.0, 12.5)
    width = rnd.uniform(3.2, 5.6)
    a = rnd.uniform(0, math.pi)
    dx, dy = math.cos(a), math.sin(a)
    px_, py_ = -dy, dx
    skew = rnd.uniform(-0.35, 0.35)
    tip = (cx + dx * length * 0.5, cy + dy * length * 0.5)
    b1 = (cx - dx * length * 0.5 + px_ * width * (0.5 + skew), cy - dy * length * 0.5 + py_ * width * (0.5 + skew))
    b2 = (cx - dx * length * 0.5 - px_ * width * (0.5 - skew), cy - dy * length * 0.5 - py_ * width * (0.5 - skew))
    return (tip, b1, b2)


def cover_of(tri, y_min):
    cover = set()
    xs = [p[0] for p in tri]
    ys = [p[1] for p in tri]
    for off in (-W, 0, W):
        t = tuple((p[0] + off, p[1]) for p in tri)
        for y in range(max(y_min, int(min(ys)) - 1), min(H, int(max(ys)) + 2)):
            for xx in range(int(min(xs) + off) - 1, int(max(xs) + off) + 2):
                if 0 <= xx < W and tri_contains(xx + 0.5, y + 0.5, *t):
                    cover.add((xx, y))
    return cover


def bed(g):
    """Scattered shards on a translucent sheen: each a light sliver with a white edge where it catches the
    light (its upper-left side), a dark edge opposite, and a drop shadow down-right of it on the floor."""
    rnd = random.Random(SEED)
    for y in range(EDGE, H):
        for x in range(W):
            g[y][x] = '~'
    for (cx, cy) in poisson(rnd, 900, 7.6):
        tri = sliver(rnd, cx, cy)
        fill = rnd.choice('EIIEI')
        cover = cover_of(tri, EDGE + 1)
        if len(cover) < 4:
            continue
        for (x, y) in cover:                                     # the shadow first, one texel down-right
            sx, sy = (x + 1) % W, y + 1
            if sy < H and g[sy][sx] == '~' and (sx, sy) not in cover:
                g[sy][sx] = ':'
        for (x, y) in cover:
            up_out = (x, y - 1) not in cover
            left_out = ((x - 1) % W, y) not in cover
            down_out = (x, y + 1) not in cover
            right_out = ((x + 1) % W, y) not in cover
            if up_out or left_out:
                k = 'W'
            elif down_out or right_out:
                k = 'K' if fill == 'I' else 'J'
            else:
                k = fill
            g[y][x] = k


def teeth():
    """The danger edge's silhouette: for each column, the row where the glass starts (0..EDGE), made of
    upright shards of uneven height and width."""
    rnd = random.Random(SEED + 2)
    tops = [EDGE + 1] * W
    x = 0
    spikes = []
    while x < W:
        w = rnd.choice((5, 6, 6, 7, 8))
        h = rnd.choice((4, 5, 6, 7, 7, 6))
        spikes.append((x, w, h))
        x += w
    for (x0, w, h) in spikes:
        peak = x0 + rnd.uniform(0.3, 0.7) * (w - 1)
        half = max(1.0, (w - 1) / 2.0 + 0.4)
        for i in range(w):
            rise = h * max(0.0, 1.0 - abs((x0 + i) - peak) / half)
            top = int(round(EDGE + 1 - rise))
            xx = (x0 + i) % W
            tops[xx] = min(tops[xx], max(0, top))
    return tops, spikes


def edge(g):
    """A row of upright shards like broken bottle tops: lit left faces, dark right faces, white tips."""
    tops, spikes = teeth()
    for x in range(W):
        for y in range(tops[x], EDGE + 1):
            lx, rx = (x - 1) % W, (x + 1) % W
            if tops[lx] > y and tops[rx] > y:
                k = 'W'
            elif tops[lx] > y:
                k = 'W' if y - tops[x] < 3 else 'E'
            elif tops[rx] > y:
                k = 'K'
            else:
                k = 'I' if (y - tops[x]) % 4 else 'E'
            g[y][x] = k
    for x in range(W):                                            # a dark foot under the row of teeth
        g[EDGE + 1][x] = 'K' if g[EDGE + 1][x] in '~:' else g[EDGE + 1][x]


def frame():
    g = pal.blank(W, H)
    bed(g)
    edge(g)
    return pal.Frame(pal.rows(g), LOCAL)


def frames():
    return [frame()]
