import sys
from pngio import read_png, write_png
src,out,x0,y0,w,h,s=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:8])
W,H,px=read_png(src)
o=[]
for j in range(h*s):
    r=[]
    for i in range(w*s):
        p=px[y0+j//s][x0+i//s]
        if p[3]==0:
            c=200 if ((i//(s*2)+j//(s*2))%2==0) else 170
            p=(c,c,c,255)
        r.append(p)
    o.append(r)
write_png(out,w*s,h*s,o)
