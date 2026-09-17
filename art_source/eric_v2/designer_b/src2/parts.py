"""Eric redesign parts."""
import math
from lib import *
from lib import _LIGHTER, _DARKER

ID = lambda m: m


def arc_line(cx, cy, rx, ry, x0, x1):
    """lower half-ellipse arc from x0..x1 (inclusive) as an 8-connected 1px line mask"""
    m = empty()
    prev = None
    for x in range(x0, x1 + 1):
        t = (x + 0.5 - cx) / rx
        if abs(t) >= 1:
            continue
        y = int(math.floor(cy + ry * math.sqrt(1 - t * t)))
        if prev is not None and abs(y - prev) > 1:
            step = 1 if y > prev else -1
            # fill the vertical gap on the column nearer the steeper side
            for yy in range(prev + step, y, step):
                xx = x - 1 if (x + 0.5) < cx else x
                if 0 <= yy < H:
                    m[yy][xx] = True
        if 0 <= y < H:
            m[y][x] = True
        prev = y
    return m


def seg_line(p0, p1):
    """bresenham 1px line mask"""
    m = empty()
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        if 0 <= x0 < W and 0 <= y0 < H:
            m[y0][x0] = True
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return m


def edge(m):
    e = empty()
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or not m[yy][xx]:
                        e[y][x] = True
                        break
    return e


def dots(pts):
    m = empty()
    for x, y in pts:
        if 0 <= x < W and 0 <= y < H:
            m[y][x] = True
    return m

# ---------------------------------------------------------------- cape


def cape(cv):
    pts = [(48, 40), (30, 39), (17, 45), (11.5, 56), (8.5, 68), (6.5, 80), (5, 90),
           (7, 94.5), (10, 90.5), (13.5, 95.5), (18, 90), (22, 94), (26, 91), (30, 95.5), (34, 92),
           (48, 92),
           (62, 92.5), (66, 95.5), (70, 91), (74.5, 94.5), (79, 89.5), (83, 95), (86.5, 90.5), (90, 93.5), (91.5, 88),
           (89.5, 78), (87.5, 67), (84.5, 56), (79, 45), (66, 39)]
    m = poly(pts)
    cv.part(m, 'cape', ('sphere', 44, 56, 46, 46, 0.7), th=[9.0, 0.95, 0.80, 0.55, 0.2], bias=0)
    # fold lines (darker) and inner shadow between legs
    for p0, p1 in [((13, 62), (10, 86)), ((19, 70), (18, 89)), ((81, 64), (84, 86)), ((75, 72), (76, 88))]:
        ln = inter(seg_line(p0, p1), m)
        for y in range(H):
            for x in range(W):
                if ln[y][x] and cv.px[y][x] != BLACK:
                    cv.px[y][x] = PALC['S']
    return m

# ---------------------------------------------------------------- legs


def legs(cv):
    for f in (ID, mirror):
        sab = f(poly([(23, 89.5), (41, 89.5), (43.5, 92), (44, 96), (17.5, 96), (17.5, 93)]))
        cx = 31 if f is ID else 65
        cv.part(sab, 'plate', ('sphere', cx - 2, 92, 16, 9, 0.2), th=TH_METAL)
        shin = f(poly([(27, 84), (41.5, 84), (42.3, 90.5), (26.2, 90.5)]))
        ax = 34 if f is ID else 62
        cv.part(shin, 'plate', ('cyl', (ax, 70), (ax, 100), 9.5), th=TH_METAL)
        knee = f(ell(34.3, 86.8, 6.6, 3.9))
        cv.part(knee, 'plate', ('sphere', 33.5 if f is ID else 62.5, 86, 7.5, 5.5), th=TH_METAL)


def flap(cv):
    m = poly(sym_pts([(48, 76), (43, 76), (42.6, 87), (44.2, 91.5), (48, 89.5)]))
    cv.part(m, 'cape', ('cyl', (47, 60), (47, 100), 6), th=TH_CLOTH, bias=0)
    return m


def tassets(cv):
    for f in (ID, mirror):
        m = f(poly([(25.5, 71), (46.2, 77), (46.8, 84.2), (44.5, 86), (36, 86.4), (28, 85.4), (23.2, 83), (23.6, 77)]))
        cx = 34 if f is ID else 62
        cv.part(m, 'plate', ('cyl', (cx, 60), (cx + (1.5 if f is ID else -1.5), 100), 14), th=TH_METAL)
        # lame seam + bevel
        seam = f(poly([(23.5, 79.2), (46.5, 81.8), (46.5, 82.8), (23.5, 80.2)]))
        cv.line_on(inter(seam, sub(m, edge(m))), BLACK)
        bev = f(poly([(23.5, 80.2), (46.5, 82.8), (46.5, 83.8), (23.5, 81.2)]))
        cv.recolor(inter(bev, sub(m, edge(m))), 'plate', ('cyl', (cx, 60), (cx, 100), 14), th=TH_METAL, bias=-1)
        cv.outline(m)


def belt(cv):
    m = poly(sym_pts([(48, 69), (36, 67.6), (26, 64.4), (22.4, 63.6), (22.6, 70.4), (27, 73.4), (35, 76.6), (42, 78.2), (48, 78.6)]))
    cv.part(m, 'leath', ('sphere', 44, 60, 30, 20, 0.2), th=TH_SOFT)
    return m


def torso(cv):
    m = poly(sym_pts([(48, 33), (39, 34), (31, 37), (26, 42), (22.5, 49), (21, 56), (21.3, 61.5), (23.2, 65.8),
                      (27.3, 69.2), (34, 71.4), (41, 72.4), (48, 72.7)]))
    cv.part(m, 'plate', ('sphere', 46.5, 53, 28.5, 25.5, 0.05), th=TH_METAL)
    return m


def gorget(cv):
    m = poly(sym_pts([(48, 30.5), (40, 31), (34.5, 33.5), (32.2, 37.5), (34.5, 41.5), (41, 43.8), (48, 44.3)]))
    cv.part(m, 'plate', ('sphere', 46, 36, 16, 9, 0.2), th=TH_METAL, bias=1)
    return m


def pauldron(cv, f):
    right = f is not ID
    sx = (lambda x: 96 - x) if right else (lambda x: x)
    l2 = f(ell(19.3, 54, 11.3, 5.6, -18))
    cv.part(l2, 'plate', ('sphere', sx(18.5), 52.5, 12, 6.5, 0.1), th=TH_METAL)
    l1 = f(ell(20.8, 49.2, 13, 6.6, -15))
    cv.part(l1, 'plate', ('sphere', sx(20), 47.5, 13.5, 7.5, 0.1), th=TH_METAL)
    dome = f(ell(23.5, 41.3, 13.6, 10.6, -12))
    cv.part(dome, 'plate', ('sphere', sx(22.5), 40.5, 13.5, 11, 0.0), th=TH_METAL)
    return dome, l1, l2


# ---------------------------------------------------------------- details

def torso_details(cv, tm):
    inner = sub(tm, edge(tm))
    # fauld lame seams across the lower belly, each with a bevel highlight below
    for cy in (37.6,):
        ln = inter(arc_line(48, cy, 40, 31.8, 20, 76), inner)
        below = empty()
        for y in range(H - 1):
            for x in range(W):
                if ln[y][x] and inner[y + 1][x] and not ln[y + 1][x]:
                    below[y + 1][x] = True
        for y in range(H):
            for x in range(W):
                if below[y][x] and cv.px[y][x] != BLACK:
                    cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
        cv.line_on(ln, BLACK)
    # red cross emblem (shaded with the belly's own sphere)
    cross = union(poly([(45, 54), (51, 54), (51, 69), (45, 69)]),
                  poly([(38, 57), (58, 57), (58, 63), (38, 63)]))
    cv.part(cross, 'red', ('sphere', 46.5, 53, 28.5, 25.5, 0.05), th=[0.95, 0.72, 0.42, -9, -9])


def pauldron_details(cv, f, dome, l1, l2):
    right = f is not ID
    sx = (lambda x: 95 - x) if right else (lambda x: x)
    # rolled rim following the lower edge of the dome: groove + bright rolled lip
    cx0 = 23.5 if not right else 96 - 23.5
    ang = -12 if not right else 12
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    for y in range(H):
        for x in range(W):
            if not dome[y][x] or cv.px[y][x] == BLACK:
                continue
            dx, dy = x + 0.5 - cx0, y + 0.5 - 41.3
            uu = (dx * ca + dy * sa) / 13.6
            vv = (-dx * sa + dy * ca) / 10.6
            t = math.sqrt(uu * uu + vv * vv)
            if vv < 0.15:
                continue
            if 0.70 <= t < 0.80:
                cv.px[y][x] = _DARKER.get(cv.px[y][x], cv.px[y][x])
            elif 0.80 <= t < 0.92:
                cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])
    # roundel
    rc = (sx(23) + (1 if right else 0), 40.5)
    disc = ell(rc[0] if not right else rc[0], rc[1], 5.4, 5.4)
    cv.part(disc, 'plate', ('sphere', rc[0] - 1, rc[1] - 1, 6, 6), th=[0.99, 0.8, 0.45, 0.1, -9])
    cx = int(math.floor(rc[0]))
    cy = int(math.floor(rc[1]))
    cr = dots([(cx + dx, cy + dy) for dx in (-1, 0) for dy in range(-3, 3)] +
              [(cx + dx, cy + dy) for dx in range(-3, 3) for dy in (-1, 0)])
    cv.paint(cr, PALC['X'])
    for x, y in [(cx - 1, cy - 3), (cx - 3, cy - 1)]:
        cv.set(x, y, 'x')
    for x, y in [(cx, cy + 2), (cx + 2, cy), (cx, cy - 3), (cx + 2, cy - 1), (cx, cy + 1), (cx + 1, cy)]:
        cv.set(x, y, 'y')
    # rivets on lames
    for (x, y) in [(13, 49), (20, 51), (27, 52), (12, 54), (18, 57)]:
        X = sx(x)
        if cv.px[y][X] not in (None, BLACK):
            cv.set(X, y, 'E')
            cv.set(X - 1, y - 1, 'W') if cv.px[y - 1][X - 1] not in (None, BLACK) else None


def belt_details(cv):
    # brass buckle centered below belly
    B = """
kkkkkkkk
kgGGGGhk
kGkkkkHk
kGknnkHk
kGkkkkHk
khhhhHHk
kkkkkkkk
"""
    cv.stamp(B, 44, 72)
    # tasset straps with little buckles
    S = """
kmmnk
kmnnk
kGGhk
kGnhk
kGGhk
kmnok
kmnok
kkkkk
"""
    cv.stamp(S, 32, 73)
    cv.stamp(S, 59, 73)


def leg_details(cv):
    for flip in (False, True):
        sx = (lambda x: 95 - x) if flip else (lambda x: x)
        # sabaton lame line
        for x in range(21, 42):
            X = sx(x)
            if cv.px[92][X] not in (None, BLACK):
                cv.px[92][X] = BLACK
        # toe cap highlight on the top lame
        for x in range(21, 27):
            X = sx(x)
            if cv.px[90][X] not in (None, BLACK):
                cv.px[90][X] = PALC['W' if not flip else 'A']


def tasset_details(cv):
    for flip in (False, True):
        sx = (lambda x: 95 - x) if flip else (lambda x: x)
        for x, y in [(27, 75), (43, 79), (27, 82), (42, 84)]:
            X = sx(x)
            if cv.px[y][X] not in (None, BLACK):
                cv.set(X, y, 'E')
                if cv.px[y - 1][X - 1] not in (None, BLACK):
                    cv.set(X - 1, y - 1, 'W')


# ---------------------------------------------------------------- head

def head(cv):
    # ears peeking out
    for f in (ID, mirror):
        ear = f(ell(34.4, 25.5, 2.6, 3.4))
        cv.part(ear, 'skin', ('sphere', 35 if f is ID else 61, 25, 3, 4), th=TH_SOFT)
    face = ell(48, 24, 12.6, 13.2)
    cv.part(face, 'skin', ('sphere', 46.5, 22, 14, 15, 0.1), th=TH_SOFT)
    hair = poly([(33.8, 29), (33.2, 20), (34.5, 14.5), (37.5, 10.5), (42, 7.8), (47.5, 6.8), (53, 7.2), (57.5, 9),
                 (61, 12.5), (62.8, 17.5), (62.8, 29),
                 (59.2, 29), (58.8, 21.5), (57, 18.8), (53.5, 17.3), (49.5, 16.8), (45, 17.3), (41, 18.2),
                 (38.6, 20), (37.2, 23), (37, 29)])
    cv.part(hair, 'hair', ('sphere', 46, 13, 17, 13, 0.1), th=TH_SOFT)
    beard = poly(sym_pts([(48, 30.8), (44.5, 30.4), (41, 31), (38.6, 29.5), (37.3, 26.5), (33.4, 26),
                          (32.6, 32), (33.3, 38), (35.8, 43), (39.8, 47.5), (44.3, 50.6), (48, 51.8)]))
    cv.part(beard, 'hair', ('sphere', 46, 36, 17, 17, 0.1), th=TH_SOFT)
    stache = poly(sym_pts([(48, 29.4), (45, 28.9), (42, 29.6), (39.6, 31.6), (38.8, 34.8), (40.6, 34.4),
                           (43, 33), (46, 32.8), (48, 33.2)]))
    cv.part(stache, 'hair', ('sphere', 46, 28, 12, 7, 0.3), th=TH_SOFT)
    return face, hair, beard, stache
