import sys
from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
S = 3
FL = (136, 180, 99, 255)
GROUND = (104, 140, 76, 255)
sw = sys.argv[1] if len(sys.argv) > 1 else 'wip_sword.png'
hm = sys.argv[2] if len(sys.argv) > 2 else 'wip_hammer.png'
out = sys.argv[3] if len(sys.argv) > 3 else 'lineup_3x.png'
_, _, old = read_png(C + "Eric/EricTopDownRevised.png"); old = crop(old, 21 * 128, 0, 128, 128)
_, _, s = read_png(sw)
_, _, h = read_png(hm)
_, _, mason = read_png(C + "Mason/mason.png")
_, _, carter = read_png(C + "Carter/carter_redesign.png"); carter = crop(carter, 0, 0, 64, 64)
_, _, mech = read_png(C + "GreysonMech/greyson_mech.png")
# old Eric frames are 128 at scale 3.5 in-game; show them at 3.5x equivalently -> nearest: scale 3 of 128 then we note it
items = [(old, 128, 3.5), (s, 96, S), (h, 96, S), (mason, 64, S), (carter, 64, S), (mech, 96, S)]
pad = 16
Wt = pad + sum(int(round(w * sc)) + pad for _, w, sc in items)
Ht = max(int(round(w * sc)) for _, w, sc in items) + 2 * pad
canvas = blank(Wt, Ht, FL)
base = Ht - pad
for yy in range(base, Ht):
    for xx in range(Wt):
        canvas[yy][xx] = GROUND
x = pad
def scale_f(px, f):
    h, w = len(px), len(px[0])
    W2, H2 = int(round(w * f)), int(round(h * f))
    return [[px[min(h - 1, int(yy / f))][min(w - 1, int(xx / f))] for xx in range(W2)] for yy in range(H2)]
for im, w, sc in items:
    img = scale_f(im, sc)
    paste(canvas, img, x, base - len(img))
    x += len(img[0]) + pad
write_png(out, Wt, Ht, canvas)
print(Wt, Ht)
