from pngio import *
C="C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(120,160,120,255)
w,h,px=read_png(C+"Computah/computah.png"); print("computah",w,h)
write_png("ref_computah_a.png",64*10*3,64*3,scale(crop(px,0,0,640,64),3,BG))
write_png("ref_computah_b.png",64*10*3,64*3,scale(crop(px,640,0,640,64),3,BG))
write_png("ref_computah_f0.png",64*8,64*8,scale(crop(px,0,0,64,64),8,BG))
w,h,px=read_png(C+"Greyson/portrait.png"); print("portrait",w,h); write_png("ref_portrait.png",w*8,h*8,scale(px,8,BG))
w,h,px=read_png(C+"Mason/mason.png"); print("mason",w,h); write_png("ref_mason.png",min(w,64*4)*6,h*6,scale(crop(px,0,0,min(w,256),h),6,BG))
w,h,px=read_png(C+"Greyson/greyson.png"); write_png("ref_greyson_f0.png",64*8,64*8,scale(crop(px,0,0,64,64),8,BG))
