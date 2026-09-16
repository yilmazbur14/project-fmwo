from png import read_png, hx
from outline import full as POLY    # the exact 74 points sent to draw_contour

W = H = 64

def bres_classic(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts

def dda_round(x0, y0, x1, y1, bias=0.0):
    n = max(abs(x1 - x0), abs(y1 - y0))
    if n == 0: return [(x0, y0)]
    out = []
    for i in range(n + 1):
        t = i / n
        fx = x0 + (x1 - x0) * t; fy = y0 + (y1 - y0) * t
        out.append((int(fx + 0.5 + bias) if fx >= 0 else int(fx - 0.5),
                    int(fy + 0.5 + bias) if fy >= 0 else int(fy - 0.5)))
    return out

def dda_floorhalf(x0, y0, x1, y1):
    # rounds .5 DOWN instead of up
    n = max(abs(x1 - x0), abs(y1 - y0))
    if n == 0: return [(x0, y0)]
    import math
    out = []
    for i in range(n + 1):
        t = i / n
        fx = x0 + (x1 - x0) * t; fy = y0 + (y1 - y0) * t
        out.append((math.ceil(fx - 0.5), math.ceil(fy - 0.5)))
    return out

def raster(poly, linefn):
    line = set()
    for i in range(len(poly)):
        a = poly[i]; b = poly[(i + 1) % len(poly)]
        for p in linefn(a[0], a[1], b[0], b[1]):
            line.add(p)
    # flood the exterior (4-connected) from the frame border
    ext = set(); stack = [(x, y) for x in range(W) for y in (0, H - 1)] + \
                         [(x, y) for y in range(H) for x in (0, W - 1)]
    while stack:
        p = stack.pop()
        if p in ext or p in line: continue
        x, y = p
        if not (0 <= x < W and 0 <= y < H): continue
        ext.add(p)
        stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
    interior = {(x, y) for x in range(W) for y in range(H)} - ext - line
    return line, interior

w, h, sil = read_png('sil.png')
ref_line = {(x, y) for y in range(H) for x in range(W) if sil[y][x][3] and hx(sil[y][x]) == '#000000'}
ref_int = {(x, y) for y in range(H) for x in range(W) if sil[y][x][3] and hx(sil[y][x]) == '#EEC39A'}
print('reference: outline', len(ref_line), ' interior', len(ref_int))

for name, fn in (('bresenham', bres_classic), ('dda_round', dda_round), ('dda_floorhalf', dda_floorhalf)):
    line, inte = raster(POLY, fn)
    dl = line ^ ref_line; di = inte ^ ref_int
    left_dl = {p for p in dl if p[0] <= 31}; left_di = {p for p in di if p[0] <= 31}
    print('%-14s outline diff %3d (left half %3d)   interior diff %3d (left half %3d)'
          % (name, len(dl), len(left_dl), len(di), len(left_di)))
    if len(dl) < 30:
        print('     outline diffs:', sorted(dl))
