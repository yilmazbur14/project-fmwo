import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *
from palette import PAL

names = sys.argv[1:]
ims = []
for n in names:
    rows = load_rows(os.path.join(HERE, 'parts', n + '.txt'))
    g = [list(r) for r in rows]
    pix = to_pix(g, PAL)
    w, h = len(rows[0]), len(rows)
    from pngio import upscale
    ims.append(upscale(w, h, pix, 8, bg='checker'))
    ims3 = upscale(w, h, pix, 3, bg='checker')
W2, H2, out = hstack(ims, gap=16)
from pngio import write_png
write_png(os.path.join(HERE, 'parts_preview.png'), W2, H2, out)
print('ok', W2, H2)
