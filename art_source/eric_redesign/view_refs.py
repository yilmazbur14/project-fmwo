from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(136,180,99,255)
def info(p):
    w,h,px=read_png(C+p); print(p,w,h); return w,h,px
for name in ["Eric/portrait.png","Mason/mason.png","Bixby/bixby.png","Liam/liam.png","Carter/carter_redesign.png","GreysonMech/greyson_mech.png","Eric/EricTopDownRevised.png"]:
    w,h,px=info(name)
    if name.endswith("Revised.png"):
        f=crop(px,21*128,0,128,128); z=scale(f,5,BG)
    else:
        f=crop(px,0,0,min(w,96) if 'mech' in name else w,h)
        s = 8 if w<=64 else (6 if w<=96 else 4)
        if w>200: f=crop(px,0,0,h,h); 
        z=scale(f,s,BG)
    out="ref_"+name.split('/')[-1].replace('.png','')+".png"
    write_png(out,len(z[0]),len(z),z)
