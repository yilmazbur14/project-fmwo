import pickle, math, rig, sheet
from pngio import *
from build import hexc
imgs = pickle.load(open('frames.pkl', 'rb'))
_, _, ref = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/GreysonMech/greyson_mech.png')
w, h, sh = read_png('greyson_mech_sheet.png')
print('sheet size', w, h, 'alpha', sorted(set(p[3] for r in sh for p in r)))
n = lambda p: p if p[3] else (0, 0, 0, 0)
print('frame0 vs approved diff:', sum(1 for y in range(96) for x in range(96) if n(sh[y][x]) != n(ref[y][x])))
# feet planted: compare rows 90..95 for x in foot columns vs frame 0, per frame
foot_cols = list(range(18, 48)) + list(range(48, 78))
for i in range(23):
    d = sum(1 for y in range(88, 96) for x in foot_cols if n(sh[y][x + 96 * i]) != n(sh[y][x]))
    print(f'f{i:02d} foot-row diffs vs f0: {d}', end='; ')
print()
col = lambda c: hexc(rig.PAL[c]) if c in rig.PAL else rig.PALC[c]
glow = {rig.PALC[c] for c in 'PrR0'}
def extreme(i, region, d):
    x0, y0, x1, y1 = region
    best = None
    for y in range(y0, y1):
        for x in range(x0, x1):
            p = sh[y][x + 96 * i]
            if p[3] and p[:3] + (255,) in glow:
                k = x * d[0] + y * d[1]
                if best is None or k > best[0]:
                    best = (k, x, y)
    return best
for i, ang, region in [(6, 0, (0, 20, 20, 60)), (7, 45, (0, 35, 25, 70)), (8, 90, (0, 40, 30, 70))]:
    a = math.radians(ang)
    d = (-math.cos(a), math.sin(a))
    b = extreme(i, region, d)
    # glow tip pixel; muzzle (outline) = one more step along d
    tx, ty = b[1], b[2]
    print(f'f{i} {ang}deg left glow tip ({tx},{ty}) dir ({d[0]:.2f},{d[1]:.2f}); right glow tip ({95 - tx},{ty}) dir ({-d[0]:.2f},{d[1]:.2f})')
