import sys
from pngio import *
FL=(136,180,99,255)
src,x0,y0,w,h,s,out=sys.argv[1],*map(int,sys.argv[2:7]),sys.argv[7]
_,_,px=read_png(src)
c=crop(px,x0,y0,w,h)
z=scale(c,s,FL)
# grid lines every 8 px for coordinate reading
for yy in range(len(z)):
    for xx in range(len(z[0])):
        gx=(xx//s+x0); gy=(yy//s+y0)
        if (xx % s==0 and gx%8==0) or (yy % s==0 and gy%8==0):
            r,g,b,a=z[yy][xx]; z[yy][xx]=(min(255,r+60),g//2,b//2,255)
write_png(out,len(z[0]),len(z),z)
