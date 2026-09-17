"""Block-in for the idle: parts as row spans with z-order; automatic 1px black outline
on every part edge that borders empty space or a part behind it."""
from lib import *

PARTS = []  # (name, z, fillchar, {y: [(x0,x1),...]})


def part(name, z, ch, spans):
    d = {}
    for y, segs in spans.items():
        if isinstance(segs, tuple):
            segs = [segs]
        d[y] = segs
    PARTS.append((name, z, ch, d))


def rng(a, b, seg):
    return {y: seg for y in range(a, b + 1)}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            out.setdefault(k, [])
            out[k] += v if isinstance(v, list) else [v]
    return out


def mirror_spans(sp):
    out = {}
    for y, segs in sp.items():
        segs = segs if isinstance(segs, list) else [segs]
        out[y] = [(63 - b, 63 - a) for a, b in segs]
    return out


# ---------------- head (egg) ----------------
head = merge({3: (27, 36), 4: (24, 39), 5: (23, 40)}, rng(6, 7, (22, 41)), rng(8, 17, (21, 42)),
             rng(18, 19, (22, 41)), rng(20, 21, (23, 40)), {22: (24, 39)})
part('head', 7, 's', head)

earL = merge({13: (19, 21)}, rng(14, 17, (18, 21)), {18: (19, 21), 19: (20, 21)})
part('earL', 6, 's', earL)
part('earR', 6, 'm', mirror_spans(earL))

beard = merge({17: [(22, 22), (41, 41)], 18: [(22, 23), (40, 41)], 19: [(22, 24), (27, 36), (39, 41)]},
              rng(20, 21, (23, 40)), rng(22, 23, (24, 39)), rng(24, 25, (25, 38)),
              {26: (26, 37), 27: (27, 36), 28: (28, 35), 29: (29, 34), 30: (30, 33), 31: (31, 32)})
part('beard', 8, 'o', beard)

# ---------------- torso ----------------
torso = merge(rng(20, 21, (25, 38)), {22: (23, 40), 23: (21, 42), 24: (18, 45), 25: (15, 48), 26: (14, 49)},
              rng(27, 28, (13, 50)), rng(29, 32, (18, 45)), {33: (19, 44)}, rng(34, 36, (20, 43)),
              rng(37, 39, (21, 42)), rng(40, 42, (22, 41)), rng(43, 49, (23, 40)))
part('torso', 3, 's', torso)

armL = merge({25: (14, 17), 26: (12, 19), 27: (11, 20)}, rng(28, 31, (10, 20)), rng(32, 33, (10, 19)),
             {34: (10, 18)}, rng(35, 36, (9, 18)), rng(37, 41, (9, 17)), rng(42, 43, (10, 18)),
             {44: (11, 18)}, rng(45, 49, (11, 19)), {50: (12, 19), 51: (12, 18)})
part('armL', 5, 's', armL)

armR = merge({25: (46, 49), 26: (44, 51), 27: (43, 52)}, rng(28, 31, (43, 53)), rng(32, 33, (44, 53)),
             {34: (45, 53), 35: (45, 54)}, rng(36, 40, (46, 54)), {41: (45, 54), 42: (44, 53), 43: (43, 52),
             44: (42, 51)}, rng(45, 49, (41, 49)), {50: (42, 48)})
part('armR', 5, 'm', armR)

speedo = merge(rng(44, 49, (23, 40)), {50: (24, 39), 51: (26, 37)})
part('speedo', 4, 'b', speedo)

legs = merge({48: [(23, 31), (32, 40)]}, rng(49, 51, [(22, 31), (32, 41)]), {52: [(22, 30), (33, 41)],
             53: [(21, 30), (33, 42)], 54: [(21, 29), (34, 42)], 55: [(20, 29), (34, 42)], 56: [(20, 29), (34, 42)]})
part('legs', 1, 's', legs)

boots = merge(rng(56, 60, [(19, 29), (34, 43)]), {61: [(18, 29), (34, 44)]}, rng(62, 63, [(17, 29), (34, 45)]))
part('boots', 2, 'k', boots)


def render():
    label = [[None] * 64 for _ in range(64)]
    zmap = [[0] * 64 for _ in range(64)]
    g = blank()
    for name, z, ch, sp in sorted(PARTS, key=lambda p: p[1]):
        for y, segs in sp.items():
            for a, b in segs:
                for x in range(a, b + 1):
                    if 0 <= x < 64 and 0 <= y < 64 and z >= zmap[y][x]:
                        label[y][x] = name
                        zmap[y][x] = z
                        g[y][x] = ch
    out = [row[:] for row in g]
    for y in range(64):
        for x in range(64):
            if label[y][x] is None:
                continue
            z = zmap[y][x]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < 64 and 0 <= ny < 64):
                    continue  # canvas edge (feet on bottom edge): handled below
                if label[ny][nx] is None or (zmap[ny][nx] < z and label[ny][nx] != label[y][x]):
                    out[y][x] = '#'
                    break
            if y == 63:
                out[y][x] = '#'
    return out


if __name__ == '__main__':
    g = render()
    save_grid(os.path.join(HERE, 'blockin_f0.txt'), g)
    pix = grid_to_pix(g)
    save(os.path.join(HERE, 'blockin_f0_8x.png'), zoom(pix, 8))
    print('ok')
