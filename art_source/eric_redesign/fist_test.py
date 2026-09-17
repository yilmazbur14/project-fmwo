from lib import *
FIST_D = """
....kkkkk....
..kkAAWWAkk..
.kAAWWWAAABk.
kAAWWAAAAABBk
kAAWAAAAABBkk
kAAAAAABBkkCk
kAAAABBkkCkCk
kAABBkkCCkCDk
kABkkCkCDkDDk
kBkCCkCDkDDEk
.kCCkCDDkDEk.
..kCDkDDkEk..
...kkkkkkkk..
"""
from pngio import scale, write_png
cv = Canvas()
cv.stamp(FIST_D, 2, 2)
px = cv.rgba()
from pngio import crop
z = scale(crop(px, 0, 0, 17, 17), 20, (136, 180, 99, 255))
write_png('fist_test.png', len(z[0]), len(z), z)
