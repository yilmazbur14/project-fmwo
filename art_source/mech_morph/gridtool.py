import sys
from pngio import *
PAL = {'k':'000000','1':'f0d080','2':'d0b060','3':'a09050','4':'605020','5':'806c34','W':'ffffff','w':'b3b3b3',
'u':'8060b0','v':'604090','x':'402070','U':'9a80c8','y':'d4cc2e','Y':'726e17','h':'f4ec50','K':'1a1a1a','T':'d95763',
'B':'639bff','c':'d9a066','g':'666666','M':'4a1a1a',
'm':'9badb7','n':'847e87','e':'696a6a','q':'c4d2da','Q':'dfe8ee','X':'ac3232','R':'e8566a','r':'ff9aa8','P':'ffe8ec','G':'4a4b4d'}
def hexc(s): return (int(s[0:2],16),int(s[2:4],16),int(s[4:6],16),255)
def load(path):
    rows=[r.rstrip('\n') for r in open(path) if r.strip('\n')!='' ]
    return rows
def to_px(rows):
    w=max(len(r) for r in rows)
    return [[(0,0,0,0) if (x>=len(r) or r[x]=='.') else hexc(PAL[r[x]]) for x in range(w)] for r in rows]
if __name__=='__main__':
    rows=load(sys.argv[1]); px=to_px(rows); w=len(px[0]); h=len(px)
    s=int(sys.argv[3]) if len(sys.argv)>3 else 12
    write_png(sys.argv[2],w*s,h*s,scale(px,s,(120,160,120,255)))
    for i,r in enumerate(rows):
        if len(r)!=w: print('row',i,'len',len(r))
        ks=[j for j,c in enumerate(r) if c=='k']
        if sorted(w-1-j for j in ks)!=ks: print('asym k row',i)
