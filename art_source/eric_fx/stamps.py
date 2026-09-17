"""Hand-drawn micro sprites used by the ground effects. '.' = transparent."""
from fxdraw import arc_pixels

S = {
 # dirt clods (outlined)
 'pebble':  [".K.",
             "KeK",
             ".K."],
 'crumb':   ["KK",
             "KK"],
 'clod4':   [".KK.",
             "KfeK",
             "KebK",
             ".KK."],
 'clod5':   [".KKK.",
             "KffeK",
             "KebdK",
             ".KKK."],
 'clod6':   [".KKKK.",
             "KffeeK",
             "KeebbK",
             "KbbddK",
             ".KKKK."],
 # rocks (outlined, lit top-left)
 'rock4':   [".KK.",
             "K24K",
             "K47K",
             ".KK."],
 'rock5':   [".KKK..",
             "K224K.",
             "K2447K",
             "K4773K",
             ".KKKK."],
 'rock6':   ["..KKK..",
             ".K224K.",
             "K22447K",
             "K24473K",
             "K47733K",
             ".KKKKK."],
 'rock7':   ["..KKKK..",
             ".K2224K.",
             "K224447K",
             "K2444773K",
             "K447733K",
             ".K7733K.",
             "..KKKK.."],
 'slab8':   ["...KKK...",
             "..K224KK.",
             ".K22444KK",
             "K2244477K",
             "K4447773K",
             "K477733K.",
             ".K7333KK.",
             "..KKKK..."],
 'boulder11': ["...KKKKK...",
               "..K222244K.",
               ".K22224447K",
               "K222444473K",
               "K244447733K",
               "K444777333K",
               ".K4773333K.",
               "..KK333KK..",
               "....KKK...."],
 'turf12':  ["...KKKKKK...",
             "..KHGGGGGKK.",
             ".KHGGGGGGGhK",
             "KhGGGGGGhhbK",
             "KbhhhhhhbbdK",
             "KebbbbbbdddK",
             ".KeebbdddgK.",
             "..KKKKKKKK.."],
 'turf9':   ["..KKKKK..",
             ".KHGGGGK.",
             "KHGGGGhhK",
             "KhhhhhbbK",
             "KebbbdddK",
             ".KKKKKKK."],
 # dust (no outline, like Eric's white fx)
 'dust2':   ["WW",
             "WW"],
 'dust3':   [".W.",
             "WWW",
             ".W."],
 'dust4':   [".WW.",
             "WWWW",
             "WWLW",
             ".LL."],
 'dust6':   ["..WW..",
             ".WWWW.",
             "WWWWWW",
             "WWWWLW",
             ".LWLL.",
             "..LL.."],
 'dust8':   ["..WWW...",
             ".WWWWWW.",
             "WWWWWWWW",
             "WWWWWWWW",
             "WWWWWWLW",
             ".LWWLLL.",
             "..LLL..."],
 'spark':   [".W.",
             "WWW",
             ".W."],
 'dot':     ["W"],
}
# ragged rows so pad
for k, v in S.items():
    w = max(len(r) for r in v)
    S[k] = [r.ljust(w, '.') for r in v]

def stamp(g, name, x, y, only_empty=False, keep=None):
    """top-left at x,y"""
    for dy, row in enumerate(S[name]):
        for dx, c in enumerate(row):
            if c == '.': continue
            X, Y = x + dx, y + dy
            if 0 <= Y < len(g) and 0 <= X < len(g[0]):
                if only_empty and g[Y][X] != '.': continue
                g[Y][X] = c

def stampc(g, name, cx, cy, **kw):
    h = len(S[name]); w = len(S[name][0])
    stamp(g, name, cx - w // 2, cy - h // 2, **kw)

def line(x0, y0, x1, y1):
    """bresenham"""
    pts = []
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy
    return pts

def polyline(pts):
    out = []
    for a, b in zip(pts, pts[1:]):
        seg = line(*a, *b)
        if out: seg = seg[1:]
        out += seg
    return out

def put(g, pts, c, only_empty=False):
    for x, y in pts:
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            if only_empty and g[y][x] != '.': continue
            g[y][x] = c

def blank(w, h):
    return [['.'] * w for _ in range(h)]

def lines(g):
    return [''.join(r) for r in g]

def ellipse_in(x, y, cx, cy, rx, ry):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0

def crater(g, cx, cy, rx, ry):
    """churned-earth crater with dark core, lit front lip, black outline"""
    H = len(g); W = len(g[0])
    inside = lambda x, y: ellipse_in(x, y, cx, cy, rx, ry)
    for y in range(H):
        for x in range(W):
            if not inside(x, y): continue
            if any(not inside(x + dx, y + dy) for dx, dy in ((1,0),(-1,0),(0,1),(0,-1))):
                g[y][x] = 'K'; continue
            if ellipse_in(x, y, cx, cy - 0.4, rx * 0.66, ry * 0.55): c = 'g'
            elif ellipse_in(x, y, cx, cy - 0.3, rx * 0.84, ry * 0.8): c = 'd'
            else: c = 'f' if y + 0.5 > cy + ry * 0.35 else ('b' if y + 0.5 < cy else 'e')
            g[y][x] = c

def cloud(g, discs, shade='L', only_empty=False, rim='f'):
    """union of discs (cx, cy, r) -> white cloud (holes filled); underside gets a grey band and a dusty-brown rim"""
    H = len(g); W = len(g[0])
    m = [[any((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r for cx, cy, r in discs) for x in range(W)] for y in range(H)]
    # fill enclosed holes
    seen = [[False] * W for _ in range(H)]
    stack = [(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < W and 0 <= y < H) or seen[y][x] or m[y][x]:
            continue
        seen[y][x] = True
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    for y in range(H):
        for x in range(W):
            if not m[y][x] and not seen[y][x]:
                m[y][x] = True
    ins = lambda x, y: 0 <= x < W and 0 <= y < H and m[y][x]
    for y in range(H):
        for x in range(W):
            if not m[y][x]:
                continue
            c = 'W'
            if not ins(x, y + 1): c = rim
            elif not ins(x, y + 2) or (not ins(x + 1, y) and not ins(x + 1, y + 1)): c = shade
            if only_empty and g[y][x] != '.':
                continue
            g[y][x] = c

def crack(g, pts, thick=3, c='K'):
    """jagged crack polyline; first `thick` pixels are doubled downward for weight"""
    p = polyline(pts)
    put(g, p, c)
    for x, y in p[:thick]:
        if 0 <= y + 1 < len(g) and 0 <= x < len(g[0]) and g[y + 1][x] in '.':
            g[y + 1][x] = c
