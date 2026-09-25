"""Shared pieces for the glass bursts: fragments on ballistic paths, drawn as tiny glass facets."""
import math
import random

GLASS_BY_AGE = ['W', 'E', 'I', 'J', 'K']      # hot and bright early, darker as they fall and settle


def fragments(seed, n, speed, up_bias, spread_deg, size_range, mirrored=False):
    """n fragments: (vx, vy, size, spin phase). Angles fan round straight up (-90) by +-spread. Mirrored:
    every fragment has a twin flying the other way, so the burst is balanced."""
    rnd = random.Random(seed)
    out = []
    for i in range(n // 2 if mirrored else n):
        a = math.radians(-90 + rnd.uniform(-spread_deg, spread_deg))
        v = speed * rnd.uniform(0.6, 1.05)
        vx, vy = math.cos(a) * v, math.sin(a) * v * up_bias
        size, spin = rnd.choice(size_range), rnd.randrange(4)
        out.append((vx, vy, size, spin))
        if mirrored:
            out.append((-vx * rnd.uniform(0.8, 1.2), vy * rnd.uniform(0.85, 1.1), size, spin + 1))
    return out


SHAPES = {
    1: [[(0, 0)]],
    2: [[(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)], [(1, 0), (0, 1)]],
    3: [[(0, 0), (1, 0), (0, 1)], [(0, 0), (1, 0), (1, 1)], [(1, 0), (0, 1), (1, 1)], [(0, 0), (0, 1), (1, 1)]],
    4: [[(1, 0), (0, 1), (1, 1), (2, 1)], [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
    # bigger shards for the crash: small triangles and slivers
    5: [[(1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2)], [(0, 0), (1, 0), (2, 0), (1, 1), (2, 1), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2)], [(0, 0), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2)]],
    6: [[(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)], [(3, 0), (2, 1), (3, 1), (1, 2), (2, 2), (0, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1), (1, 2), (2, 2)], [(1, 0), (1, 1), (2, 1), (1, 2), (2, 2), (2, 3)]],
}


def put_bit(g, x, y, size, spin, age_key, floor_y=None):
    """A fragment: its first texel lit white while it's young, the rest in the age colour."""
    shape = SHAPES[size][spin % len(SHAPES[size])]
    H, W = len(g), len(g[0])
    for j, (dx, dy) in enumerate(shape):
        px, py = int(round(x)) + dx, int(round(y)) + dy
        if floor_y is not None and py > floor_y:
            py = floor_y
        if 0 <= px < W and 0 <= py < H:
            g[py][px] = 'W' if (j == 0 and age_key in 'WEI') else age_key
