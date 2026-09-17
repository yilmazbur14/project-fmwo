import sys
from pngio import *
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
refs = ["Greyson/greyson.png","Greyson/portrait.png","Computah/computah.png","Mason/mason.png","Bixby/bixby.png","Liam/liam.png","Liam/portrait.png","Mason/mason_sheet.png"]
for r in refs:
    w,h,px = read_png(C+r)
    print(r, w, h)
