"""The marker's 4 frames over the mat, the faint smoulder (45%) and the strong smoulder, at 3x, plus the
sheet at 8x. Writes into the scratchpad view folder only."""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flood  # noqa: E402
import marker  # noqa: E402
import pal  # noqa: E402
import tiletest  # noqa: E402
from view import save, zoom  # noqa: E402

mk = marker.frames()
sh = pal.sheet([mk])
print('marker', pal.stats(sh), ''.join(sorted(pal.keys_used(mk))))
print(save(zoom(sh, 8, grid=(44, 22)), 'marker_x8.png'))

fr = flood.frames()
rows = []
for label, bg in (('mat', None), ('faint', 0.45), ('strong', 1.0)):
    if bg is None:
        base = tiletest.tiled(fr[0:2], 4, 2, scale=1, alpha=0.0)
    else:
        base = tiletest.tiled(fr[0:2], 4, 2, scale=1, alpha=bg)
    base = base.crop((0, 12, 4 * 57, 12 + 50))
    for i, m in enumerate(mk):
        base.alpha_composite(pal.to_image(m), (8 + i * 54, 14))
    rows.append(base)
out = Image.new('RGBA', (rows[0].width, sum(r.height for r in rows)))
y = 0
for r in rows:
    out.paste(r, (0, y))
    y += r.height
print(save(out.resize((out.width * 3, out.height * 3), Image.NEAREST), 'marker_over_floor_x3.png'))
