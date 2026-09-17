import sys
from pngio import *
SHEET="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png"
w,h,px=read_png(SHEET)
FL=(136,180,99,255)
frames=[int(a) for a in sys.argv[2].split(",")]
s=int(sys.argv[3])
out=blank(128*len(frames)+4*(len(frames)-1),128,(40,40,40,255))
for k,i in enumerate(frames):
    f=crop(px,i*128,0,128,128)
    bgf=blank(128,128,FL); paste(bgf,f,0,0)
    paste(out,bgf,k*132,0)
z=scale(out,s)
write_png(sys.argv[1],len(z[0]),len(z),z)
