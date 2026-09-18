# SUPERSEDED: the tower's live silhouettes are masks_clean.txt, which bg.py reads directly.
# Nothing imports this file; its sprite paths are several redesigns out of date.
import sys
from pngio import read_png, write_png
P="C:/Users/theyi/OneDrive/Documents/new-game-project/"
items=[("Assets/Characters/MainPlayer/Sprite-0004-sheet.png",0,0,32,32,6),
("Assets/Characters/Eric/eric_redesign_sword.png",0,0,128,128,2),
("Assets/Characters/GreysonMech/greyson_mech.png",0,0,96,96,3),
("Assets/Characters/Greyson/greyson.png",0,0,64,64,4),
("Assets/Characters/Computah/computah.png",0,0,64,64,4),
("Assets/Characters/Carter/carter_redesign.png",0,0,64,64,4),
("Assets/Characters/Josh/josh_redesign.png",0,0,64,64,4),
("Assets/Characters/Mason/mason.png",0,0,64,64,4),
("Assets/Characters/Liam/liam.png",0,0,64,64,4),
("Assets/Characters/Bixby/bixby.png",0,0,64,64,4),
("Assets/Characters/Jordan/jordan.png",0,0,64,64,4),
]
W=1600;H=560
out=[[(90,90,100,255)]*W for _ in range(H)]
x=4;y=4;rowh=0
for f,sx,sy,w,h,s in items:
    _,_,px=read_png(P+f)
    if x+w*s>W: x=4;y+=rowh+4;rowh=0
    for j in range(h*s):
        for i in range(w*s):
            p=px[sy+j//s][sx+i//s]
            if p[3]>0: out[y+j][x+i]=p[:3]+(255,)
    x+=w*s+8; rowh=max(rowh,h*s)
write_png("ref/cast_sheet.png",W,H,out)
