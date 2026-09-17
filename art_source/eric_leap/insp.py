import pickle
from pngio import *
w,h,pix = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/EricTopDownRevised.png')
print(w,h)
frames=[]
for i in range(w//128):
    fr=[[pix[y][x+128*i] for x in range(128)] for y in range(128)]
    frames.append(fr)
pickle.dump(frames, open('eric_frames.pkl','wb'))
alphas=set()
cols={}
for i,fr in enumerate(frames):
    xs=[x for y in range(128) for x in range(128) if fr[y][x][3]]
    ys=[y for y in range(128) for x in range(128) if fr[y][x][3]]
    for row in fr:
        for p in row:
            alphas.add(p[3])
            if p[3]: cols[p[:3]]=cols.get(p[:3],0)+1
    if xs: print(i, 'bbox', min(xs),min(ys),max(xs),max(ys), 'n',len(xs))
    else: print(i,'empty')
print('alphas', sorted(alphas))
print(len(cols),'colors')
for c,n in sorted(cols.items(), key=lambda t:-t[1]): print('#%02x%02x%02x'%c, c, n)
