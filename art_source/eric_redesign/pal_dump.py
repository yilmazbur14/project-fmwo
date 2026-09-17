from pngio import *
from collections import Counter
C = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
for name,box in [("Eric/portrait.png",(0,0,64,64)),("Carter/carter_redesign.png",(0,0,64,64)),("GreysonMech/greyson_mech.png",(0,0,96,96)),("Liam/liam.png",(0,0,64,64)),("Eric/EricTopDownRevised.png",(21*128,0,128,128))]:
    w,h,px=read_png(C+name)
    f=crop(px,*box)
    cnt=Counter(p for r in f for p in r if p[3]>0)
    print(name,len(cnt),'alpha',sorted(set(p[3] for r in f for p in r)))
    print('  '+' '.join('%02x%02x%02x:%d'%(c[0],c[1],c[2],n) for c,n in sorted(cnt.items(),key=lambda t:-t[1])[:48]))
