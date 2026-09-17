from base2 import *
from sword2 import Sword2

# designer A's bar sword (idle) vs mine at the same pose
a = R.Frame()
R.compose(a)
R.idle_weapon(a)
b = R.Frame()
R.compose(b)
arm, sw = R._idle_parts()
b.put(arm)
L = math.hypot(*R.IDLE_UP)
u = (R.IDLE_UP[0] / L, R.IDLE_UP[1] / L)
guard = (R.IDLE_FIST[0] + u[0] * 10, R.IDLE_FIST[1] + u[1] * 10)
wf()
S = Sword2(guard, math.degrees(math.atan2(u[1], u[0])))
S.draw(b.canvas())
R.fist(b, *R.IDLE_FIST)
c = R.Frame()
wf()
for ang, sa, g in ((0, 1.0, (140, 60)), (35, 0.55, (60, 40)), (90, 0.25, (200, 60)), (-150, 0.8, (120, 170))):
    Sword2(g, ang, sa).draw(c.canvas())
out = blank(3 * 260, 192, (40, 40, 40, 255))
for i, im in enumerate((a.rgba(), b.rgba(), c.rgba())):
    paste(out, rgba_on(im), i * 260, 0)
z = scale(out, 2)
write_png('../v2_sword_test_2x.png', len(z[0]), len(z), z)
zoom(crop(b.rgba(), 50, 20, 70, 160), 5, '../v2_sword_mine_5x.png')
zoom(crop(a.rgba(), 50, 20, 70, 160), 5, '../v2_sword_theirs_5x.png')
