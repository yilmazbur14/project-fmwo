import sys; sys.dont_write_bytecode = True
import projectile as PJ
from view import zoom, strip
from PIL import Image
def hx(h): return (int(h[1:3],16),int(h[3:5],16),int(h[5:7],16),255)
def img(g):
    im = Image.new('RGBA', (len(g[0]), len(g)), (0,0,0,0)); px = im.load()
    for y,row in enumerate(g):
        for x,c in enumerate(row):
            if c: px[x,y] = hx(c)
    return im
spin = [img(g) for g in PJ.spin_frames()]
st = [img(g) for g in PJ.streak_frames()]
ch = [img(g) for g in PJ.changeup_frames()]
def comp(trail, nug):
    c = trail.copy(); c.alpha_composite(nug, (8, 8)); return c
rowF = [zoom(comp(st[d*2 + (d % 2)], spin[d % 4]), 5) for d in range(8)]
rowC = [zoom(comp(ch[d*2 + (d % 2)], spin[d % 4]), 5) for d in range(8)]
a = strip(rowF); b = strip(rowC)
out = Image.new('RGBA', (a.width, a.height + b.height + 6), (70,70,80,255))
out.alpha_composite(a, (0,0)); out.alpha_composite(b, (0, a.height + 6))
out.save('../proj.png')
strip([zoom(s, 8) for s in spin]).save('../spin.png')
