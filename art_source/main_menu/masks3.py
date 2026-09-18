"""Silhouette masks with interior contour hints derived from the sprites' black linework."""
# SUPERSEDED: the tower's live silhouettes are masks_clean.txt, which bg.py reads directly.
# Nothing imports this file; its sprite paths are several redesigns out of date.
import sys, json
from pngio import read_png, write_png
from masks2 import SRC, frame
CFG={"eric":(0,3.0,0.34),"greyson":(1,2.0,0.34),"computah":(0,2.0,0.2),"carter":(0,2.0,0.34),"josh":(0,2.0,0.34),
"mason":(0,2.0,0.34),"liam":(0,2.0,0.34),"bixby":(0,2.0,0.34),"jordan":(0,1.9,0.34)}
def luma(p): return 0.3*p[0]+0.59*p[1]+0.11*p[2]
def mask(name):
    fi,factor,thr=CFG[name]; ss=4
    px,fw,fh=frame(name,fi)
    xs=[x for y in range(fh) for x in range(fw) if px[y][x][3]>0]
    ys=[y for y in range(fh) for x in range(fw) if px[y][x][3]>0]
    x0,y0,x1,y1=min(xs),min(ys),max(xs)+1,max(ys)+1
    TW=int(round((x1-x0)/factor)); TH=int(round((y1-y0)/factor))
    cov=[[0]*TW for _ in range(TH)]; dark=[[0]*TW for _ in range(TH)]
    for ty in range(TH):
        for tx in range(TW):
            hit=0; dk=0
            for sy in range(ss):
                for sx in range(ss):
                    X=int(x0+(tx+(sx+0.5)/ss)*factor); Y=int(y1-(TH-ty)*factor+((sy+0.5)/ss)*factor)
                    if 0<=X<fw and 0<=Y<fh and px[Y][X][3]>0:
                        hit+=1
                        if luma(px[Y][X])<30: dk+=1
            cov[ty][tx]=hit/(ss*ss); dark[ty][tx]=dk/(ss*ss)
    rows=[]
    for ty in range(TH):
        r=''
        for tx in range(TW):
            if cov[ty][tx]<thr: r+='.'; continue
            inner=all(0<=ty+dy<TH and 0<=tx+dx<TW and cov[ty+dy][tx+dx]>=thr for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
            r+='+' if (inner and dark[ty][tx]>=0.3) else '#'
        rows.append(r)
    return rows
def preview(masks, out, s=6):
    W=sum(len(m[0])*s+12 for m in masks.values()); H=max(len(m) for m in masks.values())*s
    img=[[(40,40,60,255)]*W for _ in range(H)]
    ox=0
    for m in masks.values():
        h=len(m); w=len(m[0]); oy=H-h*s
        for y in range(h*s):
            for x in range(w*s):
                ch=m[y//s][x//s]
                col={'#':(0,0,0,255),'+':(63,63,116,255),'o':(203,219,252,255),'R':(217,87,99,255)}.get(ch)
                if col: img[oy+y][ox+x]=col
        ox+=w*s+12
    write_png(out,W,H,img)
if __name__=='__main__':
    ms={n:mask(n) for n in CFG}
    with open('masks_raw3.txt','w') as f:
        for n,rows in ms.items():
            f.write('[%s]\n'%n); f.write('\n'.join(rows)+'\n\n')
    preview(ms,'out/masks_raw3_6x.png')
