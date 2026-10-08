import sys; sys.dont_write_bytecode = True
import importlib
from PIL import Image
from collections import Counter
from view import to_img
A = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Mason/'
def cols(im): return Counter(p[:3] for p in im.get_flattened_data() if p[3])
APPROVED = set(cols(Image.open(A + 'mason_sheet.png').convert('RGBA'))) | set(cols(Image.open(A + 'nugget_meteor.png').convert('RGBA')))
def lint(name, f, xmin=None, xmax=None):
    px = list(f.get_flattened_data()); op = [p for p in px if p[3]]
    semi = sum(1 for p in px if 0 < p[3] < 255)
    blk = sum(1 for p in op if p[:3] == (0, 0, 0)); c = cols(f)
    W, H = f.size
    edge = [(x, y) for y in range(H) for x in range(W) if f.getpixel((x, y))[3] and (x in (0, W - 1) or y == 0)]
    foreign = sorted('#%02X%02X%02X' % k for k in c if k not in APPROVED)
    feet = sum(1 for x in range(W) if f.getpixel((x, H - 1))[3])
    xs = [x for y in range(H) for x in range(W) if f.getpixel((x, y))[3]]
    span = (min(xs), max(xs))
    ok = 0.215 <= blk / len(op) <= 0.29 and 13 <= len(c) <= 21 and not semi and not edge and not foreign and feet > 0
    if xmin is not None: ok = ok and span[0] >= xmin and span[1] <= xmax
    return ('%-15s ratio %.3f colours %2d semi %d edge %d foreign %s feet-row %2d x-span %s %s' % (
        name, blk / len(op), len(c), semi, len(edge), foreign or '-', feet, span, 'OK' if ok else '<<< CHECK'))
if __name__ == '__main__':
    mod = importlib.import_module(sys.argv[1])
    lim = (6, 58) if sys.argv[1] == 'broken' else (None, None)
    for n, p in mod.FRAMES:
        print(lint(n, to_img(mod.render(p)), *lim))
