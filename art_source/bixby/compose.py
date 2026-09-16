"""Stage 2: composition test - real head stamps over a coat-pattern body blocking."""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *
from palette import PAL


def part(name):
    return load_rows(os.path.join(HERE, 'parts', name + '.txt'))


def tube_colored(g, path, widths, split, c0, c1):
    """Tail: paint outline+fill; fill colour c0 before `split` fraction, c1 after."""
    m = mask_tube(path, widths)
    # arc-length parameter for each pixel = nearest path sample
    samples = []
    total = sum(math.hypot(path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
                for i in range(len(path) - 1))
    acc = 0
    for i in range(len(path) - 1):
        (x0, y0), (x1, y1) = path[i], path[i + 1]
        L = math.hypot(x1 - x0, y1 - y0)
        for s in range(40):
            t = s / 40
            samples.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, (acc + L * t) / total))
        acc += L
    for (x, y) in m:
        edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            g[y][x] = 'K'
            continue
        best = min(samples, key=lambda s: (s[0] - x - 0.5) ** 2 + (s[1] - y - 0.5) ** 2)
        g[y][x] = c0 if best[2] < split else c1
    return m


def region(g, mask, fill, within=None):
    """Recolour interior (non-K) pixels of `within` that fall in `mask`."""
    for (x, y) in mask:
        if 0 <= x < 64 and 0 <= y < 64 and g[y][x] not in ('K', '.'):
            if within is None or (x, y) in within:
                g[y][x] = fill


def build(variant):
    g = blank()
    v = variant
    # ---------------- tail
    tube_colored(g, v['tail'], v['tail_w'], 0.5, 'k', 'w')
    # ---------------- far legs
    for poly in v['far_legs']:
        paint_part(g, mask_poly(poly), 'v')
    # ---------------- body
    body = mask_poly(v['body'])
    paint_part(g, body, 'k')
    region(g, mask_poly(v['white_front']), 'w', body)
    region(g, mask_poly(v['stripe']), 'w', body)
    region(g, mask_poly(v['tan_hip']), '3', body)
    # ---------------- necks + collars (side necks first, centre last)
    for neck, collar in v['necks']:
        nm = mask_poly(neck)
        paint_part(g, nm, 'w')
        cm = mask_poly(collar)
        paint_part(g, cm, 'r')
    # ---------------- heads
    for name, ox, oy in v['heads']:
        stamp(g, part(name), ox, oy)
    return g


A2 = dict(
    tail=[(8, 46), (3.5, 40), (2.2, 32), (2.5, 24), (4.5, 17), (8.5, 12.5), (13, 11)],
    tail_w=(3.3, 2.0),
    far_legs=[
        [(16, 46), (23, 46), (22, 55), (23, 60), (15, 60), (16, 55)],
        [(45, 46), (52, 46), (51, 55), (52, 60), (44, 60), (45, 55)],
    ],
    body=[(3, 42), (8, 38), (20, 36), (34, 35), (46, 34), (53, 36), (57, 41), (57, 47),
          (53, 51),
          (47, 51), (47, 57), (48, 63), (37, 63), (38, 57), (37, 51),   # near front leg
          (24, 51), (15, 51),
          (15, 57), (16, 63), (5, 63), (6, 57), (4, 51)],               # near hind leg
    white_front=[(36, 30), (64, 30), (64, 64), (0, 64), (0, 50), (36, 49)],
    stripe=[(22, 30), (28, 30), (29, 52), (23, 52)],
    tan_hip=[(0, 46), (14, 46), (14, 50), (0, 50)],
    necks=[
        ([(9, 30), (21, 30), (27, 42), (14, 43)], [(10.5, 34), (22.5, 34), (24, 38), (12, 38.5)]),
        ([(55, 30), (43, 30), (37, 42), (50, 43)], [(53.5, 34), (41.5, 34), (40, 38), (52, 38.5)]),
        ([(24, 16), (39, 16), (40, 40), (23, 40)], [(23, 23), (40, 23), (40, 27), (23, 27)]),
    ],
    heads=[('head_l', 3, 15), ('head_r', 36, 15), ('head_c', 18, 0)],
)


A3 = dict(
    tail=[(7, 43), (3.2, 37), (2.0, 30), (2.4, 23), (4.3, 16.5), (8.0, 12.5), (12.5, 11)],
    tail_w=(3.4, 2.0),
    far_legs=[
        [(17, 47), (23, 47), (23, 53), (21.5, 57), (22.5, 60.5), (15.5, 60.5), (16.5, 56)],
        [(46, 47), (53, 47), (52.5, 55), (53.5, 60.5), (46, 60.5), (46.5, 55)],
    ],
    body=[(2, 45), (3, 41), (6, 38), (12, 36.5), (22, 35.5), (34, 34.5), (44, 34), (50, 35),
          (55, 38.5), (57, 43), (56, 48), (53, 51),
          (48, 52), (47.5, 56), (46.5, 60), (48.5, 63), (37, 63), (38, 59), (38, 55), (37, 51.5),
          (30, 50.5), (22, 49.5), (17.5, 50),
          (16.5, 54), (15.5, 58), (16.5, 63), (5, 63), (6, 59), (5, 55), (3, 50)],
    white_front=[(40, 30), (64, 30), (64, 64), (0, 64), (0, 49), (14, 47), (26, 46.5), (36, 45), (44, 40)],
    stripe=[(23, 30), (30, 30), (29, 47), (22, 47)],
    tan_hip=[(0, 46), (16, 45.5), (16, 48), (0, 49)],
    necks=[
        ([(9, 29), (20, 29), (29, 43), (15, 44)], [(10.5, 32), (21.5, 32), (23.5, 36), (12.5, 36.5)]),
        ([(54, 29), (43, 29), (35, 43), (49, 44)], [(52.5, 32), (41.5, 32), (39.5, 36), (50.5, 36.5)]),
        ([(24, 18), (39, 18), (41, 40), (22, 40)], [(23, 23), (40, 23), (40, 27), (23, 27)]),
    ],
    heads=[('head_l', 3, 14), ('head_r', 36, 14), ('head_c', 18, 1)],
)


A4 = dict(A3)
A4.update(
    white_front=[(47, 30), (64, 30), (64, 64), (0, 64), (0, 51), (16, 48.5), (30, 48), (40, 47), (45, 43)],
    stripe=[(22, 30), (28, 30), (27, 48), (21, 48)],
    tan_hip=[(0, 47.5), (17, 46), (17, 48.5), (0, 51)],
    necks=[
        ([(10, 30), (20, 30), (22, 39), (12, 39)], [(10, 32), (21, 32), (22, 36), (11, 36)]),
        ([(53, 30), (43, 30), (41, 39), (51, 39)], [(53, 32), (42, 32), (41, 36), (52, 36)]),
        ([(25, 20), (38, 20), (39, 38), (24, 38)], [(24, 23), (39, 23), (39, 27), (24, 27)]),
    ],
)

if __name__ == '__main__':
    variants = {'A4': A4}
    for name, v in variants.items():
        g = build(v)
        save_rows(os.path.join(HERE, 'comp_%s.txt' % name), g)
        save_png(os.path.join(HERE, 'comp_%s_8x.png' % name), g, PAL, 8, bg='checker')
        save_png(os.path.join(HERE, 'comp_%s_3x.png' % name), g, PAL, 3, bg=(40, 44, 52, 255))
    print('ok')
