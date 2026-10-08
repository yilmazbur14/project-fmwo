import sys
sys.dont_write_bytecode = True
from PIL import Image
from common import zoom, save, paste
import trophy as T
V = {
 'p1': ['....KKKK..', '..KKcbbbK.', '.KcKcbbbbK', 'KwKcbbbbBK', 'KwwKbbbBBK', '.KwKBBBBK.', '..K.KKKK..'],
 'p2': ['...KKKK...', '.KKcbbbK..', 'KwKcbbbbK.', 'KwKbbbbbBK', 'KwKbbbbBBK', '.KKKBBBBK.', '...KKKKK..'],
 'p3': ['....555...', '..55cbb5..', '.5c5bbbb5.', '5w5bbbbbB5', '5w5bbbbBB5', '.555BBBB5.', '....5555..'],
 'st': ['....K....', '...KWK...', 'KKKW1WKKK', 'K1WW1WW2K', '.K2W1W2K.', '.K22K22K.', 'K2K...K2K', 'KK.....KK'],
 'ri': ['..KKKKK..', '.KbbbbbK.', 'KbbcWcbbK', 'KbcWWWcbK', 'KbbcWcbbK', '.KbbbbBK.', '..KKKKK..'],
}
canvas = Image.new('RGBA', (26 * len(V), 24), (136, 182, 101, 255))
for i, (k, em) in enumerate(V.items()):
    g = T.trophy_a()
    # clear old emblem area back to metal
    for y, x0, x1, sh in ((3, 4, 18, 0), (4, 4, 18, 0), (5, 5, 17, 0), (6, 5, 17, 0),
                          (7, 6, 16, 0), (8, 7, 15, 1), (9, 8, 14, 1)):
        g.metal(y, x0, x1, sh)
    g.set(5, 3, 'W'); g.set(5, 4, '1')
    for j, r in enumerate(em):
        for x, ch in enumerate(r):
            if ch != '.':
                g.set(6 + x, 3 + j, ch)
    paste(canvas, g.image(), (i * 26 + 1, 2))
save(zoom(canvas, 8), 'work/emblem_try.png')
save(canvas.resize((canvas.width*3, canvas.height*3), Image.NEAREST), 'work/emblem_try_3x.png')
