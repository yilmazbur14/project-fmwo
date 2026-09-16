"""Render a shaded, outlined puff in several candidate stink ramps on the real floor colour."""
import math, fxpng
FLOOR = (136, 180, 99)
RAMPS = {
    'A yellow-olive': ['#4A5A1C', '#6F8A24', '#A3BF34', '#CFE36A', '#EDF7B5'],
    'B bile lime':    ['#3E5A22', '#5E8A2A', '#8DBE3A', '#C4E86A', '#EAFFC0'],
    'C sickly pale':  ['#4F5B2A', '#7C8C38', '#AEC054', '#D6E48C', '#F2F8CF'],
    'D toxic chartr': ['#465218', '#768C1E', '#B4CC2C', '#DDF05A', '#F6FFB0'],
}
L = (-0.55, -0.65, 0.52); n = math.sqrt(sum(v*v for v in L)); L = tuple(v/n for v in L)
def hexc(s): return fxpng.hexc(s)
cells = []
S = 40
for name, ramp in RAMPS.items():
    g = [[None]*S for _ in range(S)]
    puffs = [(14, 20, 8.5), (25, 17, 7.5), (22, 27, 7.0)]
    for (cx, cy, r) in puffs:
        mask = {(x, y) for y in range(S) for x in range(S) if (x+0.5-cx)**2 + (y+0.5-cy)**2 <= r*r}
        for (x, y) in mask:
            nx, ny = (x+0.5-cx)/r, (y+0.5-cy)/r
            nz = math.sqrt(max(0, 1-nx*nx-ny*ny))
            v = nx*L[0] + ny*L[1] + nz*L[2]
            i = 4 if v > 0.86 else 3 if v > 0.55 else 2 if v > 0.15 else 1 if v > -0.2 else 0
            g[y][x] = hexc(ramp[i])
        for y in range(S):
            for x in range(S):
                if (x, y) not in mask and any((x+dx, y+dy) in mask for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
                    g[y][x] = (0, 0, 0, 255)
    cells.append(g)
row = []
for y in range(S):
    r = []
    for g in cells:
        r += [p if p else (0, 0, 0, 0) for p in g[y]]
    row.append(r)
W8, H8, o = fxpng.view(S*len(cells), S, row, 3, bg=FLOOR)
fxpng.write_png('green_test_3x.png', W8, H8, o)
W8, H8, o = fxpng.view(S*len(cells), S, row, 6, bg=FLOOR)
fxpng.write_png('green_test_6x.png', W8, H8, o)
print(list(RAMPS))
