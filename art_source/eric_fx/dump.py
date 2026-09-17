import sys
from pngio import *
SHEET="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png"
w,h,px=read_png(SHEET)
i,x0,y0,ww,hh=map(int,sys.argv[1:6])
cmap={}
chars="K123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJLMNOPQRSTUVWXYZ"
names={}
f=crop(px,i*128+x0,y0,ww,hh)
print("     "+"".join(str((x0+x)//10%10) for x in range(ww)))
print("     "+"".join(str((x0+x)%10) for x in range(ww)))
for y,row in enumerate(f):
    s=""
    for p in row:
        if p[3]==0: s+="."; continue
        if p not in cmap:
            cmap[p]= "K" if p==(0,0,0,255) else chars[len(cmap)+1 if (0,0,0,255) not in cmap else len(cmap)]
        s+=cmap[p]
    print(f"{y0+y:4d} "+s)
for k,v in cmap.items(): print(v,k)
