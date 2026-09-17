import sys, pickle
from base import *
from pngio import blank, paste
src = sys.argv[1]           # 'whirl' or 'throw'
pairs = [tuple(int(v) for v in p.split(',')) for p in sys.argv[2:]]
if src == 'whirl':
    from whirl import whirl_frame as F
else:
    from throw import FRAMES
    F = lambda i: FRAMES[i]()
cache = {}
for a, b in pairs:
    out = blank(260, 128, (40, 40, 40, 255))
    for k, i in enumerate((a, b)):
        if i not in cache:
            cache[i] = F(i).rgba()
        paste(out, rgba_on(cache[i]), k * 132, 0)
    zoom(out, 5, '../r_%s_%d_%d_5x.png' % (src, a, b))
pickle.dump(cache, open('../cache_%s.pkl' % src, 'wb'))
