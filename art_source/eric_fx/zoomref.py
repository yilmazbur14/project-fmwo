import sys
from pngio import *
SHEET="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png"
w,h,px=read_png(SHEET)
FL=(136,180,99,255)
def bbox(i):
    f=crop(px,i*128,0,128,128)
    xs=[x for y in range(128) for x in range(128) if f[y][x][3]>0]
    ys=[y for y in range(128) for x in range(128) if f[y][x][3]>0]
    return min(xs),min(ys),max(xs),max(ys)
for i in [0,6,7,8,9,10,21,27,28]:
    print(i,bbox(i))
def zoom(i,x0,y0,ww,hh,s,name):
    f=crop(px,i*128+x0,y0,ww,hh)
    z=scale(f,s,FL)
    write_png(name,len(z[0]),len(z),z)
zoom(21,30,60,70,68,8,"ref_f21_8x.png")
zoom(27,20,60,60,68,8,"ref_f27_8x.png")
