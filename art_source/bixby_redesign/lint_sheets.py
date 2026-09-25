"""Check every scratch sheet frame: drawn extent against BixbyBeastArtLayout.BODY_DRAWN (x 2..189,
y 2..157 for 192x160 frames) and anything touching the frame edge (which would clip or bleed)."""
import os
import sys

from PIL import Image

import view

D = os.path.join(view.SCRATCH, 'all_sheets')
SHEETS = [('bixby_beast.png', 160), ('bixby_beast_fly.png', 160), ('bixby_beast_takeoff.png', 160),
          ('bixby_beast_land.png', 160), ('bixby_beast_roar.png', 160), ('bixby_beast_recover.png', 160),
          ('bixby_beast_hit.png', 160), ('bixby_dizzy.png', 160), ('bixby_pound.png', 160),
          ('bixby_spin.png', 160), ('bixby_beast_firebreath.png', 256)]

bad = 0
for name, fh in SHEETS:
    p = os.path.join(D, name)
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert('RGBA')
    n = im.width // 192
    boxes = []
    for i in range(n):
        bb = im.crop((i * 192, 0, i * 192 + 192, fh)).getbbox()
        boxes.append(bb)
        x0, y0, x1, y1 = bb
        if x0 < 2 or x1 > 190 or y0 < 2 or (fh == 160 and y1 > 158):
            bad += 1
            print('  OUT OF BODY_DRAWN: %s frame %d bbox %s' % (name, i, bb))
    print('%-28s %s' % (name, ' '.join(str(b) for b in boxes)))
sys.exit(1 if bad else 0)
