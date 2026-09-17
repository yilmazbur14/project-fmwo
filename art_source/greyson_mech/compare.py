import sys
from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
src = sys.argv[1]; out = sys.argv[2]
S = 3
BG = (86, 110, 92, 255)
_,_,g = read_png(C + "Greyson/greyson.png"); g = crop(g, 64, 0, 64, 64)
_,_,c = read_png(C + "Computah/computah.png"); c = crop(c, 0, 0, 64, 64)
_,_,ms = read_png(C + "Mason/mason.png")
_,_,mech = read_png(src)
items = [(g, 64), (c, 64), (mech, 96), (ms, 64)]
pad = 12
Wt = sum(w * S for _, w in items) + pad * (len(items) + 1)
Ht = 96 * S + pad * 2
canvas = blank(Wt, Ht, BG)
x = pad
for im, w in items:
    sc = scale(im, S)
    paste(canvas, sc, x, pad + (96 - w) * S)
    x += w * S + pad
# ground line
for xx in range(Wt):
    canvas[pad + 96 * S][xx] = (60, 76, 64, 255)
write_png(out, Wt, Ht, canvas)
print(Wt, Ht)
