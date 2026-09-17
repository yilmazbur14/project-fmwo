"""Preview a region of a built frame at high zoom: python spr.py build_module x y w h scale out"""
import sys, importlib
from jlib import *
from pngio import write_png, scale, checker_bg

mod, x0, y0, w, h, s, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
args = sys.argv[8:]
m = importlib.import_module(mod)
c = m.build(*args)
rgba = to_rgba(c)
crop = [row[x0:x0 + w] for row in rgba[y0:y0 + h]]
crop = checker_bg(w, h, crop, cell=2, c1=(190, 196, 204, 255), c2=(160, 168, 178, 255))
W2, H2, big = scale(w, h, crop, s)
write_png(out, W2, H2, big)
print('ok')
