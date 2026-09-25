"""python zoom.py <frame> [scale] [x0 y0 x1 y1]  - one frame, cropped, at scale, into the scratch folder."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import poses as PZ              # noqa: E402
import view as V                # noqa: E402
from PIL import Image           # noqa: E402

i = int(sys.argv[1])
s = int(sys.argv[2]) if len(sys.argv) > 2 else 8
box = tuple(int(a) for a in sys.argv[3:7]) if len(sys.argv) > 6 else (0, 0, PZ.W, PZ.H)
px = PZ.FRAMES[i][1]()
im = Image.new('RGBA', (PZ.W, PZ.H), (46, 49, 58, 255))
im.alpha_composite(V.image(px))
im = im.crop(box)
im = im.resize((im.width * s, im.height * s), Image.NEAREST)
path = os.path.join(V.SCRATCH, 'zoom_f%d.png' % i)
im.save(path)
print(path, im.size)
