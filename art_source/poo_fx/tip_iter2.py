import fxpng
from bomb_gen import *
variants = [
    dict(base_sy=30.4, end_taper=0.55, flick_taper=0.55, tip_flick=(2.0, 3.6)),
    dict(base_sy=30.4, end_taper=0.55, flick_taper=0.50, tip_flick=(2.8, 4.0)),
    dict(base_sy=30.4, end_taper=0.50, flick_taper=0.45, tip_flick=(3.0, 3.2), flick_pow=2.5),
    dict(base_sy=30.4, end_taper=0.60, flick_taper=0.50, tip_flick=(1.5, 4.5)),
    dict(base_sy=30.4, turns=3.0, end_taper=0.55, flick_taper=0.50, tip_flick=(2.5, 4.2)),
]
grids = []
for v in variants:
    g, zb = centred_coil(**v)
    grids.append(g)
    print(v, bbox(g))
px = to_px(grids)
fxpng.write_png('tip_iter2.png', 32 * len(grids), 32, px)
a, b, o = fxpng.view(32 * len(grids), 32, px, 7, grid=(32, 32))
fxpng.write_png('tip_iter2_7x.png', a, b, o)
