from lib import *
from crowd import face
im = Img(200, 110, NAVY)
x = 12
for r in (5, 6, 7, 8, 9, 11):
    for i, e in enumerate(['laugh', 'cry', 'xd', 'smug', 'skull']):
        face(im, 12 + i * 2.6 * 11 + 6, 12 + (r - 5) * 17 if r < 11 else 97, r, e, 'mid' if r < 9 else 'lit')
zoom_save(im, 'out/facetest_6x.png', 6)
