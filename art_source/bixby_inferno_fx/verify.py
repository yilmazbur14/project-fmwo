"""Independent check of what is shipped in Assets/Characters/Bixby: every PNG opens and is a whole frame grid,
its .aseprite re-exports pixel-identical (art_source/imgdiff.py), and a fresh build of the rig matches it.
Reads Assets only; writes its re-exports into the scratchpad."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from imgdiff import pixel_diff  # noqa: E402
from PIL import Image  # noqa: E402

import export  # noqa: E402

GRID = {'bixby_fireball.png': (16, 24, 4, 2), 'bixby_fireball_marker.png': (44, 22, 4, 1),
        'bixby_fireball_impact.png': (48, 40, 5, 1), 'bixby_inferno_flood.png': (57, 41, 11, 1),
        'bixby_inferno_edge.png': (30, 48, 11, 1), 'bixby_inferno_burst.png': (64, 64, 7, 1),
        'bixby_suction.png': (24, 24, 4, 3)}

bad = 0
fresh = export.sheets()
for name, (fw, fh, cols, rows) in GRID.items():
    png = os.path.join(export.ASSETS, name)
    ase = png[:-4] + '.aseprite'
    with Image.open(png) as im:
        im.verify()
    im = Image.open(png).convert('RGBA')
    size_ok = im.size == (fw * cols, fh * rows)
    rt = os.path.join(export.SCRATCH, 'verify_' + name)
    subprocess.run([export.ASEPRITE, '-b', ase, '--save-as', rt], check=True, capture_output=True)
    d_ase = pixel_diff(im, Image.open(rt))
    d_build = pixel_diff(im, fresh[name][0])
    ok = size_ok and d_ase is None and d_build is None
    bad += not ok
    print('%-4s %-28s %dx%d = %dx%d frames of %dx%d | .aseprite %6d B round trip: %s | rebuild: %s'
          % ('OK' if ok else 'FAIL', name, im.width, im.height, cols, rows, fw, fh, os.path.getsize(ase),
             d_ase or 'identical', d_build or 'identical'))
print('verify: %d files, %d failures' % (len(GRID), bad))
sys.exit(1 if bad else 0)
