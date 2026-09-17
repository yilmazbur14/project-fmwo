import sys, copy
import crowd
from pngio import write_png, scale
def crop_rows(frames, idxs, x0, w, z):
    rows = []
    for i in idxs:
        fr = [[(c[0],c[1],c[2],255) if c else (0,0,0,255) for c in row[x0:x0+w]] for row in frames[i]]
        rows.extend(scale(fr, z))
        rows.extend([[(90,90,90,255)]*(w*z) for _ in range(z)])
    return rows
variants = {}
base = copy.deepcopy(crowd.DEPTHS)
variants['A'] = base
b = copy.deepcopy(base); b[2]['outline'] = None; b[3]['outline'] = None
variants['B'] = b
c = copy.deepcopy(base); c[2]['outline'] = K0 = (0,0,0); c[3]['outline'] = None
variants['C'] = c
out = []
x0, w, z = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
for name in sys.argv[4:]:
    crowd.DEPTHS[:] = variants[name]
    figs, frames = crowd.render()
    out.extend(crop_rows(frames, [0, 3], x0, w, z))
    out.extend([[(200,40,40,255)]*(w*z) for _ in range(z*2)])
write_png('prev/compare.png', w*z, len(out), out)
print('ok')
