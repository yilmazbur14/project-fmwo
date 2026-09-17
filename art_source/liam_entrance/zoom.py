"""zoom.py SRC S OUT [x y w h] -- nearest-neighbour zoom onto a neutral bg, written to le_prev/"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png, write_png, crop, scale
PREV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'le_prev')
BG = (96, 112, 104, 255)
src, s, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
w, h, px = read_png(src)
if len(sys.argv) >= 8:
    x0, y0, rw, rh = (int(v) for v in sys.argv[4:8])
    px = crop(px, x0, y0, rw, rh); w, h = rw, rh
write_png(os.path.join(PREV, out), w * s, h * s, scale(px, s, BG))
print(os.path.join(PREV, out))
