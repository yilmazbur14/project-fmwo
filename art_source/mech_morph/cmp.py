import sys
from pngio import *
a=read_png(sys.argv[1]); b=read_png(sys.argv[2])
assert a[0]==b[0] and a[1]==b[1], (a[:2], b[:2])
d=0
for y in range(a[1]):
    for x in range(a[0]):
        pa=a[2][y][x]; pb=b[2][y][x]
        if pa[3]==0 and pb[3]==0: continue
        if pa!=pb: d+=1
print("diff pixels:", d)
