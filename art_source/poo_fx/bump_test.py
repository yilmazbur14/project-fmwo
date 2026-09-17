import math, fxpng
import explo_gen5 as g5
from explo_gen import Frame, disc, LIGHT, to_px, W, H

def bump_plus(t, x, y):
    g5.lump(t, x, y, 1.2)

def bump_bubble(t, x, y):
    ix, iy = int(x), int(y)
    for p in ((ix - 1, iy), (ix - 1, iy - 1), (ix, iy - 1)):
        if p in t: t[p] = 'd'
    for p in ((ix + 1, iy), (ix + 1, iy + 1), (ix, iy + 1)):
        if p in t: t[p] = 'b'
    if (ix + 1, iy - 1) in t: t[(ix + 1, iy - 1)] = 'c'
    if (ix - 1, iy + 1) in t: t[(ix - 1, iy + 1)] = 'c'

def bump_2x2(t, x, y):
    ix, iy = int(x), int(y)
    for p, ch in (((ix, iy), 'e'), ((ix + 1, iy), 'd'), ((ix, iy + 1), 'd'), ((ix + 1, iy + 1), 'b')):
        if p in t: t[p] = ch

def bump_arc(t, x, y):
    """small highlight arc over a shadow crease: a glossy lump, 5x3."""
    ix, iy = int(x), int(y)
    for p, ch in (((ix - 1, iy), 'd'), ((ix, iy - 1), 'e'), ((ix + 1, iy - 1), 'd'),
                  ((ix - 1, iy + 1), 'b'), ((ix, iy + 1), 'b'), ((ix + 1, iy + 1), 'b'), ((ix + 2, iy), 'b')):
        if p in t: t[p] = ch

def none_(t, x, y):
    pass

styles = [('none', none_), ('plus', bump_plus), ('bubble', bump_bubble), ('2x2', bump_2x2), ('arc', bump_arc)]
grids = []
for name, fn in styles:
    f = Frame()
    arms = [(-105, 8.0, 2.8, 1.0, 2.0), (-58, 3.5, 2.8, 1.3, 0), (-20, 7.0, 2.6, 1.0, 1.7),
            (22, 4.0, 2.8, 1.3, 0), (62, 8.5, 2.8, 1.0, 2.0), (108, 4.5, 2.6, 1.2, 0),
            (150, 7.5, 2.8, 1.0, 1.8), (195, 3.5, 2.6, 1.3, 0), (232, 8.0, 2.8, 1.0, 1.9)]
    m = g5.splat(24.0, 24.0, 8.5, arms, lumps=((-80, 3.0), (0, 3.0), (85, 3.0), (128, 2.5), (172, 3.0), (212, 2.5), (260, 2.5)), wob=g5.WOB_BIG)
    t = g5.flat_shade(m, hmax=1.8)
    for (lx, ly) in ((27.5, 20.5), (19.5, 27.5), (29.5, 29.5), (23.5, 32.5), (15.5, 21.5)):
        fn(t, lx, ly)
    g5.gloss(t, [(18, 19), (19, 18), (20, 18), (21, 17), (26, 19)])
    f.paint(t)
    grids.append(f.g)
    print(name)
px = to_px(grids)
sub = [row for row in px[8:40]]
sub = [[p for i, p in enumerate(row) if (i % 48) >= 6 and (i % 48) < 42] for row in sub]
a, b, o = fxpng.view(36 * len(styles), 32, sub, 6, grid=(36, 0))
fxpng.write_png('bump_test_6x.png', a, b, o)
a, b, o = fxpng.view(36 * len(styles), 32, sub, 3, bg=(136, 180, 99), grid=(36, 0))
fxpng.write_png('bump_test_3x.png', a, b, o)
