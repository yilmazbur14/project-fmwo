"""python jr_look.py module [scale] [f0,f1..] [x0 y0 x1 y1]: a zoomed strip of a sheet's frames into rider/look."""
import importlib
import sys
sys.dont_write_bytecode = True
import jr_common as C
import jr_sheet as S
from PIL import Image

mod = importlib.import_module(sys.argv[1])
s = int(sys.argv[2]) if len(sys.argv) > 2 else 6
fr = mod.frames()
idx = [int(i) for i in sys.argv[3].split(',')] if len(sys.argv) > 3 else range(len(fr))
crop = [int(v) for v in sys.argv[4:8]] if len(sys.argv) > 7 else [0, 0, 96, 96]
ims = []
for i in idx:
    im = C.render(fr[i].px).crop(crop)
    ims.append(C.up(im, s, (120, 165, 92, 255)))
out = Image.new('RGBA', (sum(i.width for i in ims) + 6 * (len(ims) - 1), ims[0].height), (10, 10, 12, 255))
x = 0
for i in ims:
    out.paste(i, (x, 0))
    x += i.width + 6
print(C.look(out, 'z_%s.png' % mod.NAME, 1))
