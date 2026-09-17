import pickle, sys
from pngio import *
frames = pickle.load(open('eric_frames.pkl','rb'))
BG=(120,160,120,255)
def strip(idx, x0,y0,w,h,s,out,src=frames,gap=2):
    W=len(idx)*(w*s+gap*s)
    img=blank(W,h*s,(40,40,40,255))
    for k,i in enumerate(idx):
        c=crop(src[i],x0,y0,w,h)
        sc=scale(c,s,BG)
        paste(img,sc,k*(w*s+gap*s),0,False)
    write_png(out,W,h*s,img)
if __name__=='__main__':
    idx=[int(v) for v in sys.argv[1].split(',')]
    x0,y0,w,h,s=[int(v) for v in sys.argv[2:7]]
    strip(idx,x0,y0,w,h,s,sys.argv[7])
