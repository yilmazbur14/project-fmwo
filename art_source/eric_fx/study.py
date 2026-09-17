import sys
from pngio import *
from collections import Counter
SHEET="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png"
w,h,px=read_png(SHEET)
print(w,h)
c=Counter()
alph=Counter()
for row in px:
    for p in row:
        alph[p[3]]+=1
        if p[3]>0: c[p]+=1
print("alpha",sorted(alph.items())[:10], len(alph))
for col,n in c.most_common(60): print(col,n)
# full sheet grid 2x on floor green in 4 rows of 8
FL=(136,180,99,255)
def frame(i): return crop(px,i*128,0,128,128)
for r in range(4):
    out=blank(8*128,128,FL)
    for k in range(8):
        paste(out,frame(r*8+k),k*128,0)
    s=scale(out,2)
    write_png(f"sheet_row{r}_2x.png",len(s[0]),len(s),s)
