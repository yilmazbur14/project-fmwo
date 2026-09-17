import fxpng, coil_bomb
from coil_bomb import render, to_px, W, H

def centred(**kw):
    g = render(**kw)
    xs = [x for y in range(H) for x in range(W) if g[y][x] != '.']
    ys = [y for y in range(H) for x in range(W) if g[y][x] != '.']
    mid = (min(xs) + max(xs) + 1) / 2.0
    kw2 = dict(kw); kw2['cx'] = kw.get('cx', 15.5) + (16.0 - mid)
    g = render(**kw2)
    xs = [x for y in range(H) for x in range(W) if g[y][x] != '.']
    ys = [y for y in range(H) for x in range(W) if g[y][x] != '.']
    return g, (min(xs), max(xs), min(ys), max(ys))

variants = [
    dict(turns=3.0, rise=4.3, R0=9.6, r0=4.2, phi_deg=28),
    dict(turns=2.8, rise=4.8, R0=9.4, r0=4.5, phi_deg=28),
    dict(turns=3.2, rise=4.0, R0=10.0, r0=4.0, phi_deg=30),
    dict(turns=2.6, rise=5.0, R0=9.4, r0=4.8, phi_deg=25),
    dict(turns=2.9, rise=4.6, R0=9.8, r0=4.4, phi_deg=24, tip_flick=(2.2, 3.6)),
]
grids = []
for v in variants:
    g, bb = centred(**v)
    print(v, 'bbox x%d-%d y%d-%d' % bb)
    grids.append(g)
px = to_px(grids)
fxpng.write_png('coil_iter.png', W * len(grids), H, px)
W8, H8, o = fxpng.view(W * len(grids), H, px, 7, grid=(32, 32))
fxpng.write_png('coil_iter_7x.png', W8, H8, o)
