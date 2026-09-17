import math, rig, lib, sword128
from sword import Sword
from pngio import write_png, scale, blank, paste
L = rig.layers()
rig.use128()


def body():
    f = rig.Frame128()
    for k in ('core', 'uarm_R', 'uarm_L', 'paul_L', 'paul_R', 'farm_R', 'head'):
        f.put(L[k])
    return f


ang = math.degrees(math.atan2(-0.9805806756909201, -0.1961161351381841))
f1 = body(); sword128.arm(f1.cv); sword128.blade(f1.cv); sword128.hilt(f1.cv); sword128.fist(f1.cv)
f2 = body(); sword128.arm(f2.cv); S = Sword((28.4, 92.2), ang); S.draw(f2.cv); sword128.fist(f2.cv)
tests = []
for ang2, sa, sb in [(200, 1, 1), (135, 1, 1), (90, 0.4, 1), (-45, 1, 0.55), (0, 1, 0.5)]:
    f = rig.Frame128(); Sword((64 - 40 * math.cos(math.radians(ang2)), 64 - 40 * math.sin(math.radians(ang2))), ang2, sa, sb).draw(f.cv); tests.append(f.rgba())
FL = rig.FL
out = blank(4 + 7 * 132, 4 + 132, (40, 40, 40, 255))
for i, px in enumerate([f1.rgba(), f2.rgba()] + tests):
    paste(out, [[p if p[3] else FL for p in r] for r in px], 4 + i * 132, 4)
z = scale(out, 2)
write_png('../t_sword_2x.png', len(z[0]), len(z), z)
z = scale([r[:] for r in f2.rgba()], 6, FL)
write_png('../t_sword_generic_6x.png', len(z[0]), len(z), z)
