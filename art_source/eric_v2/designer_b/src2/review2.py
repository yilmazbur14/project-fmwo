import sys, pickle, os
from base2 import *
import runframes
pairs = [tuple(int(v) for v in p.split(',')) for p in sys.argv[2:]]
tag = sys.argv[1]
idx = sorted(set(i for p in pairs for i in p))
imgs = runframes.render(idx, use_cache=True)
for p in pairs:
    out = blank(len(p) * 258, 192, (40, 40, 40, 255))
    for k, i in enumerate(p):
        paste(out, rgba_on(imgs[i]), k * 258, 0)
    z = scale(out, int(os.environ.get('Z', '3')))
    write_png('../r2_%s_%s.png' % (tag, '_'.join(map(str, p))), len(z[0]), len(z), z)
