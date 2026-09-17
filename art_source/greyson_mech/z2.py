from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
BG=(120,160,120,255)
w,h,px = read_png(C+"Computah/computah.png")
write_png("zoom_computah_torso.png", 40*14, 30*14, scale(crop(px,12,22,40,30),14,BG))
# frame 15 laser
write_png("zoom_computah_laser.png", 64*8, 64*8, scale(crop(px,15*64,0,64,64),8,BG))
write_png("zoom_computah_rocket.png", 64*8, 64*8, scale(crop(px,9*64,0,64,64),8,BG))
w,h,px = read_png(C+"Computah/ComputahRocketProjectiles.png")
print(w,h)
write_png("zoom_rockets.png", w*6, h*6, scale(px,6,BG))
