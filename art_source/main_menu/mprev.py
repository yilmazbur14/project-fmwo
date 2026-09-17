"""Preview masks (from a txt file) with rim light next to the nearest-downscaled source sprite."""
import sys
from pngio import read_png, write_png
from masks2 import SRC, frame, CFG as CFG2
FACT={"eric":(0,3.0),"greyson":(1,2.0),"computah":(0,2.0),"carter":(0,2.1),"josh":(0,2.1),"mason":(0,2.1),"liam":(0,2.1),"bixby":(0,2.2),"jordan":(0,1.9)}
def load(path):
    ms={}; cur=None
    for line in open(path):
        line=line.rstrip('\n')
        if line.startswith('['): cur=line[1:-1]; ms[cur]=[]
        elif line.strip() and cur: ms[cur].append(line)
    for n,m in ms.items():
        L=set(len(r) for r in m)
        assert len(L)==1, (n, [ (i,len(r)) for i,r in enumerate(m)])
    return ms
def rim_rgba(m):
    h=len(m); w=len(m[0])
    S=lambda x,y: 0<=y<h and 0<=x<w and m[y][x]!='.'
    out=[[None]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            ch=m[y][x]
            if ch=='.': continue
            col=(0,0,0)
            if ch=='+': col=(34,32,52)
            elif ch=='o': col=(203,219,252)
            elif ch=='R': col=(217,87,99)
            elif ch=='y': col=(251,242,54)
            elif not S(x,y-1): col=(251,242,54)
            elif not S(x-1,y) or not S(x+1,y): col=(217,160,102)
            out[y][x]=col
    return out
if __name__=='__main__':
    ms=load(sys.argv[1]); s=int(sys.argv[3]) if len(sys.argv)>3 else 6
    names=[n for n in ms if len(sys.argv)<5 or n in sys.argv[4].split(',')]
    cols=[]
    for n in names:
        m=ms[n]; h=len(m); w=len(m[0])
        fi,fac=FACT[n]; px,fw,fh=frame(n,fi)
        xs=[x for y in range(fh) for x in range(fw) if px[y][x][3]>0]; ys=[y for y in range(fh) for x in range(fw) if px[y][x][3]>0]
        x0,y1=min(xs),max(ys)+1
        src=[[None]*w for _ in range(h)]
        for ty in range(h):
            for tx in range(w):
                X=int(x0+(tx+0.5)*fac); Y=int(y1-(h-ty)*fac+0.5*fac)
                if 0<=X<fw and 0<=Y<fh and px[Y][X][3]>0: src[ty][tx]=px[Y][X][:3]
        cols.append((rim_rgba(m),src,w,h))
    W=sum((c[2]*2+3)*s+16 for c in cols); H=max(c[3] for c in cols)*s
    img=[[(63,63,116,255)]*W for _ in range(H)]
    ox=0
    for rim,src,w,h in cols:
        oy=H-h*s
        for part,dx in ((rim,0),(src,(w+3)*s)):
            for y in range(h*s):
                for x in range(w*s):
                    c=part[y//s][x//s]
                    if c is not None: img[oy+y][ox+dx+x]=c+(255,)
        ox+=(w*2+3)*s+16
    write_png(sys.argv[2],W,H,img)
