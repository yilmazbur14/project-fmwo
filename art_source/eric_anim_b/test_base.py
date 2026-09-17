from base import *
fr = arig.Frame()
body(fr)
AW.draw(fr)
px = fr.rgba()
ap = approved_px()
d = sum(1 for y in range(128) for x in range(128) if tuple(px[y][x]) != tuple(ap[y][x]))
print('frame21 via designer-A rig vs approved: diff', d)
