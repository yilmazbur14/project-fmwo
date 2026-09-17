from parts import *
from pngio import blank, paste, scale, write_png
FL = (136, 180, 99, 255)

cv = Canvas()
cape(cv)
legs(cv)
flap(cv)
tassets(cv)
belt(cv)
torso(cv)
gorget(cv)
pauldron(cv, ID)
pauldron(cv, mirror)
cv.save('stage1.png')
cv.save('stage1_8x.png', 8, FL)
