"""contact sheet: python sheet.py dst scale cellw cellh cols file[:x:y] ..."""
import sys
from pngio import read_png, write_png
a=sys.argv; dst=a[1]; s=int(a[2]); cw=int(a[3]); ch=int(a[4]); cols=int(a[5]); items=a[6:]
rows=(len(items)+cols-1)//cols
W=cols*(cw+2)*s; H=rows*(ch+2)*s
out=[[(60,58,70,255)]*W for _ in range(H)]
out=[list(r) for r in out]
for i,it in enumerate(items):
    parts=it.rsplit('|',2)
    f=parts[0]; ox=int(parts[1]) if len(parts)>1 else 0; oy=int(parts[2]) if len(parts)>2 else 0
    w,h,p=read_png(f)
    cx=(i%cols)*(cw+2)+1; cy=(i//cols)*(ch+2)+1
    for y in range(ch):
        for x in range(cw):
            sx,sy=ox+x,oy+y
            q=p[sy][sx] if 0<=sx<w and 0<=sy<h else (0,0,0,0)
            if q[3]==0:
                q=(200,200,200,255) if ((x//4+y//4)%2==0) else (170,170,170,255)
            for Y in range((cy+y)*s,(cy+y+1)*s):
                row=out[Y]
                for X in range((cx+x)*s,(cx+x+1)*s):
                    row[X]=q
write_png(dst,W,H,out)
print(dst,W,H)
