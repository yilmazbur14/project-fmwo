"""verify_ase.py exported.png reference.png fw -> per-frame pixel diff (alpha-0 pixels compared as transparent)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pngio import read_png
a_path, b_path, fw = sys.argv[1], sys.argv[2], int(sys.argv[3])
wa, ha, pa = read_png(a_path)
wb, hb, pb = read_png(b_path)
print('exported %dx%d  reference %dx%d' % (wa, ha, wb, hb))
n = min(wa, wb) // fw
def norm(p):
    return (0, 0, 0, 0) if p[3] == 0 else p
for f in range(n):
    diffs = [(x, y, norm(pa[y][f * fw + x]), norm(pb[y][f * fw + x])) for y in range(min(ha, hb)) for x in range(fw)
             if norm(pa[y][f * fw + x]) != norm(pb[y][f * fw + x])]
    opaque = sum(1 for y in range(ha) for x in range(fw) if pa[y][f * fw + x][3] > 0)
    print('frame', f, 'diff px:', len(diffs), 'exported non-transparent px:', opaque, diffs[:3])
