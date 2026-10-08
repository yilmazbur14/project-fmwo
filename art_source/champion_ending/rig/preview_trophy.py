import sys
sys.dont_write_bytecode = True
from PIL import Image
from common import zoom, save, paste
import trophy as T
a = T.trophy_a().image(); b = T.trophy_b().image(); s = T.stand().image()
canvas = Image.new('RGBA', (120, 50), (136, 182, 101, 255))
paste(canvas, s, (2, 30))
for img, sx, cx in ((a, 32, T.A_CX), (b, 62, T.B_CX)):
    paste(canvas, s, (sx, 30))
    paste(canvas, img, (sx + T.S_CX - cx, 30 + T.STAND_SEAT_Y - (img.height - 2)))
paste(canvas, a, (92, 2)); paste(canvas, b, (92, 24))
save(zoom(canvas, 8), 'work/look_trophy.png')
