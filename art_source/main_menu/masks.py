"""Derive silhouette masks from the real character sprites (so shapes are not invented)."""
# SUPERSEDED: the tower's live silhouettes are masks_clean.txt, which bg.py reads directly.
# Nothing imports this file; its sprite paths are several redesigns out of date.
import sys, json
from pngio import read_png, write_png
P="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
SRC={"eric":("Eric/eric_redesign_sword.png",128,128,0),"mech":("GreysonMech/greyson_mech.png",96,96,0),
"greyson":("Greyson/greyson.png",64,64,0),"computah":("Computah/computah.png",64,64,0),"carter":("Carter/carter_redesign.png",64,64,0),
"josh":("Josh/josh_redesign.png",64,64,0),"mason":("Mason/mason.png",64,64,0),"liam":("Liam/liam.png",64,64,0),"bixby":("Bixby/bixby.png",64,64,0),"jordan":("Jordan/jordan.png",64,64,0)}

def mask(name, factor, thr=0.34, ss=4):
    f,fw,fh,fi=SRC[name]
    w,h,px=read_png(P+f)
    xs=[];ys=[]
    for y in range(fh):
        for x in range(fw):
            if px[y][fi*fw+x][3]>0: xs.append(x); ys.append(y)
    x0,y0,x1,y1=min(xs),min(ys),max(xs)+1,max(ys)+1
    # anchor bottom (feet) so the ground line is exact
    TW=int(round((x1-x0)/factor)); TH=int(round((y1-y0)/factor))
    rows=[]
    for ty in range(TH):
        r=''
        for tx in range(TW):
            hit=0
            for sy in range(ss):
                for sx in range(ss):
                    X=x0+(tx+(sx+0.5)/ss)*factor
                    Y=y1-(TH-ty)*factor+((sy+0.5)/ss)*factor
                    X=int(X);Y=int(Y)
                    if 0<=X<fw and 0<=Y<fh and px[Y][fi*fw+X][3]>0: hit+=1
            r+='#' if hit/(ss*ss)>=thr else '.'
        rows.append(r)
    return rows

if __name__=='__main__':
    cfg=json.loads(sys.argv[1])
    out={}
    for name,(fac,thr) in cfg.items():
        out[name]=mask(name,fac,thr)
        print(name,len(out[name][0]),'x',len(out[name]))
        print('\n'.join(out[name]))
    json.dump(out,open('masks_raw.json','w'),indent=0)
