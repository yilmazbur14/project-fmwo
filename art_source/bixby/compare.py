"""Side-by-side: Bixby | Mason | Liam at a given scale on a dark backdrop."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from pngio import read_png, write_png, upscale
from canvas import hstack
P = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters'
src = sys.argv[1]
s = int(sys.argv[2])
out = sys.argv[3]
ims = []
for path in [src, P + '/Mason/mason.png', P + '/Liam/liam.png']:
    w, h, pix = read_png(path)
    ims.append(upscale(w, h, pix, s, bg=(46, 50, 60, 255)))
W, H, o = hstack(ims, gap=12, bg=(28, 30, 36, 255))
write_png(out, W, H, o)
print('ok', W, H)
