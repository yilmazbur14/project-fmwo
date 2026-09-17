import json, os
from lib import *
import scene
M=json.load(open('masks_raw.json'))
def put(c, rows, cx, feet, k, anchor=None):
    h=len(rows); w=len(rows[0])
    ax = anchor if anchor is not None else w//2
    x0=cx-ax; y0=feet-h+1
    hi,base,lo=scene.ROLE[k]
    S=lambda x,y: 0<=y<h and 0<=x<w and rows[y][x]=='#'
    for y in range(h):
        for x in range(w):
            if not S(x,y): continue
            col=K
            up=not S(x,y-1); l=not S(x-1,y); r=not S(x+1,y)
            if up: col=hi
            elif l or r: col=base
            c.set(x0+x,y0+y,col)
c=scene.build_stage1()
put(c,M['eric'],scene.CX,269,1,anchor=18)
put(c,M['computah'],scene.CX-42,231,2)
put(c,M['greyson'],scene.CX+42,231,2)
put(c,M['carter'],scene.CX-40,197,3)
put(c,M['josh'],scene.CX+40,197,3)
put(c,M['mason'],scene.CX,166,4)
put(c,M['liam'],scene.CX-36,138,5)
put(c,M['bixby'],scene.CX+36,138,5)
put(c,M['jordan'],scene.CX,113,6)
p=c.save('out/members_test.png')
crop_zoom(p,'out/members_test_4x.png',300,60,260,220,4)
crop_zoom(p,'out/members_test_2x.png',0,0,640,360,2)
