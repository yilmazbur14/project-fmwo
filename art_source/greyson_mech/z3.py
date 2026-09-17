from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(120,160,120,255)
w,h,px = read_png(C+"Liam/liam.png")
write_png("zoom_liam_body.png", 40*12, 36*12, scale(crop(px,4,26,40,36),12,BG))
