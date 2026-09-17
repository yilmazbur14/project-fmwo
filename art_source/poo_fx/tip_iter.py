import math, fxpng, bomb_gen
from bomb_gen import *

# patch coil() tip taper via a wrapper: re-implement the flick with configurable taper
def coil_tip(taper=0.55, **kw):
    orig = bomb_gen.coil
    src_flick = kw.get('tip_flick', (2.0, 3.4))
    return orig(**kw)

variants = [
    dict(base_sy=30.4, tip_flick=(2.0, 3.4)),
    dict(base_sy=30.4, tip_flick=(2.6, 4.2)),
    dict(base_sy=30.4, tip_flick=(3.2, 3.6)),
    dict(base_sy=30.4, tip_flick=(1.2, 4.6)),
    dict(base_sy=30.4, turns=3.05, tip_flick=(2.8, 4.0)),
]
grids = []
for v in variants:
    g, zb = centred_coil(**v)
    grids.append(g)
    print(v, bbox(g))
px = to_px(grids)
fxpng.write_png('tip_iter.png', 32 * len(grids), 32, px)
a, b, o = fxpng.view(32 * len(grids), 32, px, 7, grid=(32, 32))
fxpng.write_png('tip_iter_7x.png', a, b, o)
