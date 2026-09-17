from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(136,180,99,255)
w,h,px=read_png(C+"Eric/EricTopDownRevised.png")
f=crop(px,21*128+36,68,60,56); z=scale(f,10,BG); write_png("ref_old_f21_zoom.png",len(z[0]),len(z),z)
w,h,px=read_png(C+"Carter/carter_redesign.png")
f=crop(px,6,0,40,36); z=scale(f,14,BG); write_png("ref_carter_head.png",len(z[0]),len(z),z)
