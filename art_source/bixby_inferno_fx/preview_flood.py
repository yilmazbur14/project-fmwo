"""Previews of the flood tile into the scratchpad view folder (never into Assets)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flood  # noqa: E402
import pal  # noqa: E402
import tiletest  # noqa: E402
from view import save, zoom  # noqa: E402

fr = flood.frames()
print(len(fr), 'frames')
tiletest.seam_report(fr[0:2], 'smoulder')
tiletest.seam_report(fr[4:8], 'burn')
for i in (2, 3, 8, 9, 10):
    tiletest.seam_report([fr[i]], 'frame %d' % i)
sh = pal.sheet([fr])
print(pal.stats(sh), ''.join(sorted(pal.keys_used(fr))))
print(save(zoom(sh, 5, grid=(57, 41)), 'flood_all_x5.png'))
which = sys.argv[1:] or ['smoulder', 'faint', 'burn']
if 'smoulder' in which:
    print(save(tiletest.tiled(fr[0:2], 6, 5, scale=3), 'flood_smoulder_tiled_x3.png'))
if 'faint' in which:
    print(save(tiletest.tiled(fr[0:2], 6, 5, scale=3, alpha=0.45), 'flood_smoulder_faint_tiled_x3.png'))
if 'burn' in which:
    print(save(tiletest.tiled(fr[4:8], 6, 5, scale=3), 'flood_burn_tiled_x3.png'))
for i in (2, 3, 8, 9, 10):
    if 'f%d' % i in which:
        print(save(tiletest.tiled([fr[i]], 6, 5, scale=3), 'flood_f%d_tiled_x3.png' % i))
