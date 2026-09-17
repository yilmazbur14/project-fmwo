from parts import *
FL = (136, 180, 99, 255)
cv = Canvas()
cape(cv); legs(cv); leg_details(cv); flap(cv); tassets(cv); belt(cv)
tm = torso(cv); torso_details(cv, tm); belt_details(cv); gorget(cv)
for f in (ID, mirror):
    d, l1, l2 = pauldron(cv, f); pauldron_details(cv, f, d, l1, l2)
head(cv)
cv.save('stage3.png')
cv.save('stage3_8x.png', 8, FL)
from pngio import crop, scale, write_png
px = cv.rgba()
z = scale(crop(px, 28, 2, 40, 54), 14, FL)
write_png('stage3_head14x.png', len(z[0]), len(z), z)
