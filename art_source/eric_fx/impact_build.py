import math, random
from common import *
from stamps import *
W, H = 160, 80
CX, CY = 80, 66          # impact pixel (sword ground contact goes here)
FY = 0.42                # ground foreshortening (3/4 top-down)

# ---------- ground cracks: fixed jagged paths, revealed progressively ----------
def make_crack(seed, ang, length, jitter=3.0, step=6):
    rnd = random.Random(seed)
    pts = []
    a = math.radians(ang)
    n = max(1, int(round(length / step)))
    for i in range(n + 1):
        r = length * i / n
        off = rnd.uniform(-jitter, jitter) if 0 < i else 0
        px_ = r * math.cos(a) - off * math.sin(a)
        py_ = (r * math.sin(a) + off * math.cos(a)) * FY
        pts.append((round(px_), round(py_)))
    return pts

# (seed, angle deg, length in ground px, doubled px near centre)
CRACKS = [
    (1, 3, 74, 16), (2, 177, 74, 16), (3, 32, 54, 8), (4, 148, 54, 8),
    (5, 74, 30, 4), (6, 106, 30, 4), (7, -30, 46, 6), (8, -150, 46, 6),
]
# (parent, fraction along parent, seed, angle offset, length)
BRANCH = [
    (0, 0.45, 21, 38, 14), (1, 0.55, 22, -38, 14),
    (2, 0.55, 25, -45, 10), (3, 0.6, 26, 45, 10), (6, 0.5, 27, 40, 8), (7, 0.55, 28, -40, 8),
]
PATHS = [make_crack(s, a, L) for s, a, L, _ in CRACKS]

def draw_cracks(g, grow):
    for (s, a, L, thick), path in zip(CRACKS, PATHS):
        pts = polyline([(CX + x, CY + y) for x, y in path])
        n = max(2, round(len(pts) * grow))
        pts = pts[:n]
        put(g, pts, 'K')
        for x, y in pts[:thick]:
            if 0 <= y + 1 < H and g[y + 1][x] == '.':
                g[y + 1][x] = 'K'
        for x, y in pts[2:max(2, thick - 2)]:
            if 0 <= y - 1 < H and g[y - 1][x] == '.':
                g[y - 1][x] = 'e'
    for pi, frac, seed, doff, L in BRANCH:
        if grow < frac + 0.1:
            continue
        path = polyline([(CX + x, CY + y) for x, y in PATHS[pi]])
        bx, by = path[int(len(path) * frac)]
        sub = make_crack(seed, CRACKS[pi][1] + doff, L, jitter=1.5, step=5)
        sub = polyline([(bx + x, by + y) for x, y in sub])
        n = max(2, round(len(sub) * min(1.0, (grow - frac) / 0.3)))
        put(g, sub[:n], 'K')

# ---------- flying debris: (stamp in flight, landed stamp, dir deg, ground dist, peak h, flight time) ----------
DEBRIS = [
    ('turf12', 'turf9', 188, 22, 12, 2.2), ('turf12', 'turf9', -9, 24, 11, 2.3),
    ('boulder11', 'rock6', 158, 44, 30, 2.9), ('boulder11', 'rock6', 23, 40, 33, 2.8),
    ('clod4', 'pebble', 222, 38, 34, 3.0), ('pebble', 'pebble', -38, 34, 38, 3.0),
    ('turf9', 'clod4', 128, 28, 46, 3.0), ('clod6', 'clod4', 54, 33, 41, 3.0),
    ('rock5', 'pebble', 176, 72, 18, 3.2), ('clod5', 'pebble', 6, 68, 21, 3.1),
    ('clod5', 'pebble', 106, 16, 54, 3.2), ('rock5', 'pebble', 73, 20, 50, 3.3),
    ('rock7', 'rock4', 203, 60, 22, 3.1), ('rock7', 'rock4', -22, 56, 25, 3.2),
    ('pebble', 'pebble', 148, 64, 42, 3.3), ('clod4', 'pebble', 33, 60, 37, 3.2),
    ('rock4', None, 96, 7, 60, 3.1), ('pebble', None, 83, 11, 50, 3.0),
]

def debris_at(back, front, t):
    for i, (fly, landed, ang, D, peak, T) in enumerate(DEBRIS):
        launch = (0.05, 0.3, 0.45, 0.15, 0.35, 0.2)[i % 6]
        tt = t - launch
        if tt <= 0:
            continue
        a = math.radians(ang)
        u = min(tt / T, 1.0)
        ux = 1 - (1 - u) ** 2              # outward motion front-loaded so pieces separate quickly
        gx = CX + D * ux * math.cos(a)
        gy = CY + D * ux * math.sin(a) * FY
        h = 4 * peak * u * (1 - u)
        tgt = back if gy < CY + 2 else front
        if u >= 1.0:
            if landed:
                stampc(tgt, landed, round(gx), round(gy))
        else:
            stampc(tgt, fly, round(gx), round(gy - h))

# ---------- white fx ----------
def shock_ring(g, rx, ry, gaps, thick=1):
    pts = set()
    for i in range(1440):
        a = i / 4
        if any(g0 <= a < g1 or g0 <= a - 360 < g1 for g0, g1 in gaps):
            continue
        r = math.radians(a)
        for k in range(thick):
            pts.add((math.floor(CX + 0.5 + (rx + k) * math.cos(r)),
                     math.floor(CY + 0.5 + (ry + k * 0.5) * math.sin(r))))
    put(g, pts, 'W')

def wedge(pts, ang, L, w0, fy):
    a = math.radians(ang)
    for i in range(int(L * 4)):
        r = i / 4
        w = w0 * (1 - r / L)
        n = int(w * 2)
        for j in range(-n, n + 1):
            off = j / 2
            x = CX + r * math.cos(a) - off * math.sin(a)
            y = CY + (r * math.sin(a) + off * math.cos(a)) * fy
            pts.add((math.floor(x + 0.5), math.floor(y + 0.5)))

def flash(g):
    """Eric-style solid white impact burst: flat ground spikes + upward flare, no outline"""
    pts = set()
    for ang, L, w in ((0, 44, 5), (180, 44, 5), (14, 30, 4), (166, 30, 4), (-14, 30, 4), (-166, 30, 4),
                      (38, 18, 3), (142, 18, 3), (-40, 22, 3), (-140, 22, 3)):
        wedge(pts, ang, L, w, FY)
    for ang, L, w in ((-90, 34, 3.5), (-68, 24, 2.5), (-112, 24, 2.5), (-48, 15, 2), (-132, 15, 2)):
        wedge(pts, ang, L, w, 1.0)
    for y in range(H):
        for x in range(W):
            if ellipse_in(x, y, CX + 0.5, CY + 0.5, 15, 5.5):
                pts.add((x, y))
    put(g, pts, 'W')
    # grey underside so the burst sits on the ground
    for x, y in list(pts):
        if (x, y + 1) not in pts and 0 <= y < H:
            g[y][x] = 'L'

def compose(layers):
    out = blank(W, H)
    for L in layers:
        for y in range(H):
            for x in range(W):
                if L[y][x] != '.':
                    out[y][x] = L[y][x]
    return out

def mirror_discs(L):
    return L + [(2 * CX + 1 - x, y, r) for x, y, r in L]

def billow(rows, seed):
    """rows: list of (y offset, radius, [x offsets]) mirrored left/right with a little per-side jitter"""
    rnd = random.Random(seed)
    discs = []
    for dy, r, xs in rows:
        for dx in xs:
            for side in (-1, 1):
                discs.append((CX + 0.5 + side * (dx + rnd.uniform(-1.2, 1.2)),
                              CY + dy + rnd.uniform(-1.0, 1.0), r + rnd.uniform(-0.5, 0.5)))
    return discs

DUST = {
    1: [(-2, 5.0, [8, 15, 22]), (-7, 4.0, [11, 18])],
    2: [(-2, 6.0, [10, 19, 28, 36]), (-9, 5.5, [13, 23, 31]), (-15, 4.0, [17, 26])],
    3: [(-3, 6.5, [12, 22, 33, 44, 52]), (-11, 6.0, [16, 27, 38, 47]), (-19, 4.8, [20, 31, 40]), (-25, 3.2, [26, 36])],
    4: [(-5, 5.0, [36, 43, 50, 56]), (-13, 4.8, [32, 39, 47]), (-21, 3.8, [36, 43]), (-27, 2.6, [40])],
    5: [(-6, 2.6, [40, 56]), (-20, 3.0, [31, 49]), (-31, 2.0, [42])],
}

def frame(k):
    ground = blank(W, H); back = blank(W, H); front = blank(W, H); fx = blank(W, H); dustl = blank(W, H)
    grow = [0.22, 0.5, 0.78, 1.0, 1.0, 1.0][k]
    draw_cracks(ground, grow)
    crater(ground, CX + 0.5, CY + 0.8, 9 if k == 0 else 12.5, 3.3 if k == 0 else 4.3)
    if k == 0:
        flash(fx)
        shock_ring(fx, 30, 10, [(70, 110), (250, 290), (160, 200), (-20, 20)], thick=2)
        for sx, sy in ((CX - 34, CY - 22), (CX + 35, CY - 20), (CX - 16, CY - 42), (CX + 18, CY - 40)):
            stampc(fx, 'spark', sx, sy)
    else:
        debris_at(back, front, k)
        cloud(dustl, billow(DUST[k], 30 + k))
        if k == 1:
            shock_ring(fx, 52, 16, [(38, 142), (240, 300), (160, 202), (-22, 20)], thick=2)
            for sx, sy in ((CX - 44, CY - 30), (CX + 45, CY - 28), (CX - 22, CY - 50), (CX + 24, CY - 48)):
                stampc(fx, 'spark', sx, sy)
        elif k == 2:
            shock_ring(fx, 70, 21, [(33, 147), (225, 315), (160, 200), (-20, 20)], thick=1)
            for sx, sy in ((CX - 56, CY - 38), (CX + 57, CY - 36), (CX - 30, CY - 60), (CX + 31, CY - 58)):
                stampc(fx, 'dot', sx, sy)
        elif k == 4:
            for sx, sy in ((CX - 62, CY - 30), (CX + 61, CY - 32), (CX - 40, CY - 52), (CX + 42, CY - 54)):
                stampc(fx, 'dot', sx, sy)
    return lines(compose([ground, dustl, back, front, fx]))

if __name__ == '__main__':
    fr = [frame(k) for k in range(6)]
    st = strip(fr)
    save_grid('eric_quake_impact_grid.txt', st)
    write_grid_png('eric_quake_impact.png', st)
    view('impact_f012_4x.png', strip(fr[0:3]), 4)
    view('impact_f345_4x.png', strip(fr[3:6]), 4)
