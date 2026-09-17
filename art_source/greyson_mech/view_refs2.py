from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(120,160,120,255)
def save_scaled(src, name, s=8, bg=BG):
    w,h,px = read_png(C+src)
    write_png(name, w*s, h*s, scale(px, s, bg))
save_scaled("Greyson/portrait.png","ref_greyson_portrait_8x.png")
save_scaled("Mason/mason.png","ref_mason_8x.png")
save_scaled("Bixby/bixby.png","ref_bixby_8x.png")
save_scaled("Liam/liam.png","ref_liam_8x.png")
w,h,px = read_png(C+"Greyson/greyson.png")
write_png("ref_greyson_sheet_5x.png", w*5, h*5, scale(px,5,BG))
w,h,px = read_png(C+"Greyson/greyson.png")
f0 = crop(px,0,0,64,64)
write_png("ref_greyson_f0_8x.png", 512,512, scale(f0,8,BG))
w,h,px = read_png(C+"Computah/computah.png")
for i,(a,b) in enumerate([(0,5),(5,10),(10,15),(15,20)]):
    part = crop(px, a*64, 0, (b-a)*64, 64)
    write_png(f"ref_computah_{a}_{b}_4x.png", (b-a)*64*4, 256, scale(part,4,BG))
f0 = crop(px,0,0,64,64)
write_png("ref_computah_f0_8x.png",512,512,scale(f0,8,BG))
