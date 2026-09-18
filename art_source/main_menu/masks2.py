# SUPERSEDED: the tower's live silhouettes are masks_clean.txt, which bg.py reads directly.
# Nothing imports this file; its sprite paths are several redesigns out of date.
import sys, json
from pngio import read_png, write_png
P="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
SRC={"eric":("Eric/eric_redesign_sword.png",128,128),"greyson":("Greyson/greyson.png",64,64),"computah":("Computah/computah.png",64,64),
"carter":("Carter/carter_redesign.png",64,64),"josh":("Josh/josh_redesign.png",64,64),"mason":("Mason/mason.png",64,64),
"liam":("Liam/liam.png",64,64),"bixby":("Bixby/bixby.png",64,64),"jordan":("Jordan/jordan.png",64,64)}
CFG={"eric":(0,3.0,0.34),"greyson":(1,2.0,0.34),"computah":(0,2.0,0.2),"carter":(0,2.1,0.34),"josh":(0,2.1,0.34),
"mason":(0,2.1,0.34),"liam":(0,2.1,0.34),"bixby":(0,2.2,0.34),"jordan":(0,1.9,0.34)}
def frame(name,fi):
    f,fw,fh=SRC[name]; w,h,px=read_png(P+f)
    return [[px[y][fi*fw+x] for x in range(fw)] for y in range(fh)],fw,fh
def mask(name):
    fi,factor,thr=CFG[name]; ss=4
    px,fw,fh=frame(name,fi)
    xs=[x for y in range(fh) for x in range(fw) if px[y][x][3]>0]
    ys=[y for y in range(fh) for x in range(fw) if px[y][x][3]>0]
    x0,y0,x1,y1=min(xs),min(ys),max(xs)+1,max(ys)+1
    TW=int(round((x1-x0)/factor)); TH=int(round((y1-y0)/factor))
    rows=[]
    for ty in range(TH):
        r=''
        for tx in range(TW):
            hit=0
            for sy in range(ss):
                for sx in range(ss):
                    X=int(x0+(tx+(sx+0.5)/ss)*factor); Y=int(y1-(TH-ty)*factor+((sy+0.5)/ss)*factor)
                    if 0<=X<fw and 0<=Y<fh and px[Y][X][3]>0: hit+=1
            r+='#' if hit/(ss*ss)>=thr else '.'
        rows.append(r)
    return rows
if __name__=='__main__':
    out={}
    for n in CFG: out[n]=mask(n)
    with open('masks_raw2.txt','w') as f:
        for n,rows in out.items():
            f.write('[%s]\n'%n); f.write('\n'.join(rows)+'\n\n')
    print(open('masks_raw2.txt').read())
