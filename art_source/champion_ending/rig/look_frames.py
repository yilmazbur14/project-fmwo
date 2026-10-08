import sys
sys.dont_write_bytecode = True
from PIL import Image
from common import zoom, save, paste
import champion as C, burak as BK
take = sys.argv[1] if len(sys.argv) > 1 else 'A'
names = sys.argv[2].split(',') if len(sys.argv) > 2 else BK.ORDER
k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
W, H = C.CELL
sheet = Image.new('RGBA', (W * len(names), H), (136, 182, 101, 255))
for i, n in enumerate(names):
    paste(sheet, C.compose(take, n), (i * W, 0))
save(zoom(sheet, k), f'work/look_frames_{take}.png')
