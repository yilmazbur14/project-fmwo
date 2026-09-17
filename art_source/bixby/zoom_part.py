import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *
from palette import PAL
from pngio import upscale, write_png
n, s = sys.argv[1], int(sys.argv[2])
rows = load_rows(os.path.join(HERE, 'parts', n + '.txt'))
g = [list(r) for r in rows]
W2, H2, out = upscale(len(rows[0]), len(rows), to_pix(g, PAL), s, bg='checker')
write_png(os.path.join(HERE, n + '_zoom.png'), W2, H2, out)
# also a 3x "game scale" copy
W3, H3, out3 = upscale(len(rows[0]), len(rows), to_pix(g, PAL), 3, bg=(40, 44, 52, 255))
write_png(os.path.join(HERE, n + '_3x.png'), W3, H3, out3)
print('ok')
