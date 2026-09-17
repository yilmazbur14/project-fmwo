from pngio import *
from collections import Counter
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(120,160,120,255)
for name, x0 in [("Greyson/greyson.png",64),("Computah/computah.png",0),("Mason/mason.png",0),("Liam/liam.png",0),("Bixby/bixby.png",0)]:
    w,h,px = read_png(C+name)
    f = crop(px,x0,0,64,64)
    cnt = Counter(p for row in f for p in row if p[3]>0)
    print(name, len(cnt), "colors; alpha values:", sorted(set(p[3] for row in f for p in row)))
    for c,n in cnt.most_common(40):
        print("   #%02x%02x%02x a%d  %d" % (c[0],c[1],c[2],c[3],n))
w,h,px = read_png(C+"Computah/computah.png")
write_png("zoom_computah_chest.png", 40*14, 34*14, scale(crop(px,12,0,40,34),14,BG))
w,h,px = read_png(C+"Greyson/greyson.png")
write_png("zoom_greyson_head.png", 40*14, 44*14, scale(crop(px,64+12,0,40,44),14,BG))
write_png("zoom_greyson_trunks.png", 40*14, 30*14, scale(crop(px,64+12,30,40,30),14,BG))
