"""Greyson + Computah -> Greyson Mech morph strip. 8 frames of 96x96."""
import math, sys
import build as B
from build import BLACK, hexc, W, H, stamp
import mparts as M
import gbig
from pngio import read_png, write_png, scale
import gridtool

ASSET = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
GREEN = (120, 160, 120, 255)

FX = {k: hexc(v) for k, v in {
    'W': 'ffffff', 'P': 'ffe8ec', 'r': 'ff9aa8', 'R': 'e8566a', 'X': 'ac3232', 'V': '6e1e22',
    'k': '000000', 'q': 'c4d2da', 'm': '9badb7', 'n': '7b8893', 'o': '5a6570'}.items()}

# ------------------------------------------------------------------ canvas utils

def blank():
    return [[None] * W for _ in range(H)]

def set_canvas(grid):
    for y in range(H):
        for x in range(W):
            B.canvas[y][x] = grid[y][x] if grid is not None else None

def snap():
    return [row[:] for row in B.canvas]

def paste(dst, src, dx=0, dy=0):
    for y in range(H):
        for x in range(W):
            p = src[y][x]
            if p is None:
                continue
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H:
                dst[yy][xx] = p

def under(dst, src):
    """paste src only where dst is empty"""
    for y in range(H):
        for x in range(W):
            if dst[y][x] is None and src[y][x] is not None:
                dst[y][x] = src[y][x]

def put(g, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        g[y][x] = c

def stamp_fx(g, grid, x0, y0, only_empty=False):
    rows = grid.strip('\n').split('\n')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x, y = x0 + dx, y0 + dy
            if 0 <= x < W and 0 <= y < H and (not only_empty or g[y][x] is None):
                g[y][x] = FX[ch]

def to_rgba(g):
    return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in g]

# ------------------------------------------------------------------ mech part groups

def antenna():
    stamp(M.ANTENNA, 47, 0)

def emits():
    stamp(M.EMIT, 0, 44)
    stamp(M.EMIT, 0, 44, mirror=True)

GROUP_OF = ['RACK', 'RACK', 'RACK', 'LEGS', 'CHEST', 'CHEST', 'HELM', 'HELM', 'HELM', 'CHEST', 'CHEST',
            'CHEST', 'CHEST', 'LEGS', 'LEGS', 'LEGS', 'LEGS', 'LEGS', 'GAUNT', 'PAUL', 'PAUL', 'GAUNT',
            'GAUNT', 'GAUNT', 'GAUNT', 'GAUNT']
ITEMS = list(M.order[:26])
ITEMS.append(antenna); GROUP_OF.append('HELM')
ITEMS.append(emits); GROUP_OF.append('GAUNT')
assert len(ITEMS) == len(GROUP_OF)

def run_groups(groups, base=None):
    set_canvas(base)
    for item, g in zip(ITEMS, GROUP_OF):
        if g in groups:
            M.run_item(item)
    return snap()

def split_lr(layer):
    L, R = blank(), blank()
    for y in range(H):
        for x in range(W):
            if layer[y][x] is not None:
                (L if x <= 47 else R)[y][x] = layer[y][x]
    return L, R

def helm_halves():
    layer = run_groups({'HELM'})
    face = [[None] * W for _ in range(H)]
    for grid, x0, y0 in ((M.FACE, 37, 10), (M.FACE2, 37, 22)):
        for dy, row in enumerate(grid.strip('\n').split('\n')):
            for dx, ch in enumerate(row):
                if ch != '.':
                    face[y0 + dy][x0 + dx] = ch
    for y in range(H):
        for x in range(W):
            ch = face[y][x]
            if ch is None:
                continue
            if ch != 'k':
                layer[y][x] = None
            else:
                inner = all(0 <= x + dx < W and 0 <= y + dy < H and face[y + dy][x + dx] is not None
                            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if inner:
                    layer[y][x] = None
    L, R = split_lr(layer)
    for y in range(H):
        if L[y][47] is not None:
            L[y][47] = BLACK
        if R[y][48] is not None:
            R[y][48] = BLACK
    # dark inner surface of each shell (what you see inside the open clamshell)
    inner = blank()
    dk = [hexc(c) for c in B.RAMPS['dark']]
    for y in range(H):
        for x in range(W):
            if M.helmet[y][x] and layer[y][x] is None and y < 31:
                d = min(abs(x - 47.5), 99)
                inner[y][x] = dk[4] if (y < 12 or abs(x - 47.5) > 8) else dk[5]
    IL, IR = split_lr(inner)
    return L, R, IL, IR

# ------------------------------------------------------------------ effects

STAR5 = """
..r..
..P..
rPWPr
..P..
..r..
"""
STAR7 = """
...R...
...r...
..rPr..
RrPWPrR
..rPr..
...r...
...R...
"""
CLANG = """
.....R.....
.R...r...R.
..r..P..r..
...rPWPr...
....PWP....
RrPWWWWWPrR
....PWP....
...rPWPr...
..r..P..r..
.R...r...R.
.....R.....
"""
GLINT = """
.P.
PWP
.P.
"""

def speed_lines(g, cx, cy, r0, r1, n=28, seed=1, cols='WPr', only_empty=True, jitter=0.35):
    rnd = seed
    for i in range(n):
        rnd = (rnd * 1103515245 + 12345) & 0x7fffffff
        a = 2 * math.pi * (i + (rnd % 100) / 100.0 * jitter) / n
        rnd = (rnd * 1103515245 + 12345) & 0x7fffffff
        ra = r0 + (rnd % 7)
        rb = r1 - (rnd >> 8) % 9
        steps = int((rb - ra) * 1.2) + 1
        for s in range(steps):
            t = s / max(steps - 1, 1)
            r = ra + (rb - ra) * t
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            c = cols[min(int(t * len(cols)), len(cols) - 1)]
            if 0 <= x < W and 0 <= y < H and (not only_empty or g[y][x] is None):
                g[y][x] = FX[c]

def aura(g, body, rings=('P', 'r', 'R'), sparse_last=True):
    """glow rings outside the body silhouette"""
    dist = [[None] * W for _ in range(H)]
    frontier = [(x, y) for y in range(H) for x in range(W) if body[y][x] is not None]
    for x, y in frontier:
        dist[y][x] = 0
    for d in range(1, len(rings) + 1):
        nxt = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and dist[yy][xx] is None:
                    dist[yy][xx] = d
                    nxt.append((xx, yy))
        frontier = nxt
    for y in range(H):
        for x in range(W):
            d = dist[y][x]
            if d and g[y][x] is None:
                if d == len(rings) and sparse_last and (x + y) % 2:
                    continue
                g[y][x] = FX[rings[d - 1]]

def trails(g, piece, dx, dy, length=7, spacing=3, seed=3):
    """one clean 1px streak per stripe, trailing behind a flying piece
    (pointing away from where it is heading)."""
    L = math.hypot(dx, dy)
    if L < 1:
        return
    ux, uy = dx / L, dy / L
    px_, py_ = -uy, ux
    best = {}
    for y in range(H):
        for x in range(W):
            if piece[y][x] is None:
                continue
            bx, by = int(round(x + ux)), int(round(y + uy))
            if 0 <= bx < W and 0 <= by < H and piece[by][bx] is not None:
                continue
            s = (x + 0.5) * px_ + (y + 0.5) * py_
            k = int(math.floor(s / spacing))
            if abs(s - (k + 0.5) * spacing) > 0.75:
                continue
            f = (x + 0.5) * ux + (y + 0.5) * uy
            if k not in best or f > best[k][0]:
                best[k] = (f, x, y)
    for k, (f, x, y) in best.items():
        h = (k * 2654435761 + seed * 97) & 0xffff
        n = max(3, int(length * (0.55 + (h % 100) / 220.0)))
        for s in range(1, n + 1):
            xx, yy = int(round(x + ux * s)), int(round(y + uy * s))
            if not (0 <= xx < W and 0 <= yy < H):
                break
            if piece[yy][xx] is not None:
                continue
            if g[yy][xx] is not None:
                break
            c = 'W' if s <= n * 0.34 else ('P' if s <= n * 0.67 else 'r')
            g[yy][xx] = FX[c]

def shift(layer, dx, dy):
    out = blank()
    paste(out, layer, dx, dy)
    return out

# ------------------------------------------------------------------ pieces

def build_pieces():
    P = {}
    for grp in ('LEGS', 'PAUL', 'GAUNT', 'RACK'):
        L, R = split_lr(run_groups({grp}))
        P[grp + '_L'], P[grp + '_R'] = L, R
    P['CHEST'] = run_groups({'CHEST'})
    P['HELM_L'], P['HELM_R'], P['HELMIN_L'], P['HELMIN_R'] = helm_halves()
    return P

PASTE_ORDER = ['LEGS_L', 'LEGS_R', 'GAUNT_L', 'GAUNT_R', 'CHEST', 'PAUL_L', 'PAUL_R', 'RACK_L', 'RACK_R', 'HELM_L', 'HELM_R']
GROUP_PIECES = {'LEGS': ['LEGS_L', 'LEGS_R'], 'PAUL': ['PAUL_L', 'PAUL_R'], 'CHEST': ['CHEST'],
                'GAUNT': ['GAUNT_L', 'GAUNT_R'], 'RACK': ['RACK_L', 'RACK_R'], 'HELM': ['HELM_L', 'HELM_R']}

OFF = {
    2: {'LEGS_L': (-15, 3), 'LEGS_R': (15, 3), 'PAUL_L': (-12, -9), 'PAUL_R': (12, -9), 'CHEST': (0, 30),
        'GAUNT_L': (-24, 12), 'GAUNT_R': (24, 12), 'RACK_L': (-4, -22), 'RACK_R': (4, -22)},
    3: {'CHEST': (0, 13), 'GAUNT_L': (-12, 7), 'GAUNT_R': (12, 7), 'RACK_L': (-2, -12), 'RACK_R': (2, -12)},
    4: {'GAUNT_L': (-5, 3), 'GAUNT_R': (5, 3), 'RACK_L': (-1, -5), 'RACK_R': (1, -5)},
    5: {'HELM_L': (-9, 0), 'HELM_R': (9, 0)},
    6: {},
}
LOCKED = {2: set(), 3: {'LEGS', 'PAUL'}, 4: {'LEGS', 'PAUL', 'CHEST'},
          5: {'LEGS', 'PAUL', 'CHEST', 'GAUNT', 'RACK'}, 6: {'LEGS', 'PAUL', 'CHEST', 'GAUNT', 'RACK', 'HELM'}}

def sym_fx(grid, cx, cy):
    """stamp list entries for a star centred on (cx, cy) and its mirror (x' = 95 - x)."""
    rows = grid.strip().split()
    w, h = len(rows[0]), len(rows)
    return [(grid, cx - w // 2, cy - h // 2), (grid, 95 - cx - w // 2, cy - h // 2)]

LOCK_FX = {
    3: sym_fx(STAR7, 27, 77) + sym_fx(STAR7, 9, 31) + sym_fx(STAR5, 18, 91),
    4: sym_fx(STAR7, 34, 31) + sym_fx(STAR5, 37, 66),
    5: sym_fx(STAR7, 10, 44) + sym_fx(STAR5, 25, 61) + sym_fx(STAR7, 5, 19),
    6: [(CLANG, 42, -1)] + sym_fx(STAR7, 31, 20) + sym_fx(GLINT, 17, 27),
}

def assembly_frame(f, base, pieces):
    g = blank()
    body = run_groups(LOCKED[f], base)
    if f == 2:
        speed_lines(g, 47.5, 50, 30, 70, n=32, seed=7)
    elif f == 6:
        speed_lines(g, 47.5, 48, 40, 75, n=36, seed=11)
    for side in ('L', 'R'):
        nm = 'HELM_' + side
        if nm in OFF[f]:
            dx, dy = OFF[f][nm]
            under(body, shift(pieces['HELMIN_' + side], dx, dy))
    paste(g, body)
    if f == 2:
        aura(g, body, rings=('P', 'r', 'R'))
    elif f == 3:
        aura(g, body, rings=('r',), sparse_last=True)
    for name in PASTE_ORDER:
        if name in OFF[f]:
            dx, dy = OFF[f][name]
            pc = shift(pieces[name], dx, dy)
            trails(g, pc, dx, dy, length=min(9, int(math.hypot(dx, dy) * 0.6) + 3))
            paste(g, pc)
    if f == 6:
        for deg in (-160, -135, -110, -70, -45, -20):
            a = math.radians(deg)
            for rr in range(20, 25):
                x = int(round(47.5 + rr * 1.05 * math.cos(a)))
                y = int(round(19.5 + rr * math.sin(a)))
                if 0 <= x < W and 0 <= y < H and (g[y][x] is None or g[y][x] in (FX['W'], FX['P'], FX['r'])):
                    g[y][x] = FX['W'] if rr < 23 else FX['r']
    for grid, x, y in LOCK_FX.get(f, []):
        stamp_fx(g, grid, x, y)
    return g

# ------------------------------------------------------------------ frame 0 / 1

def load_grid_layer(path, ox, oy):
    rows = gridtool.load(path)
    px = gridtool.to_px(rows)
    g = blank()
    for y, row in enumerate(px):
        for x, p in enumerate(row):
            if p[3]:
                put(g, x + ox, y + oy, p)
    return g

def frame0():
    g = blank()
    comp = load_grid_layer('csmall.txt', 17, 17)
    grey = load_grid_layer('gsmall.txt', 33, 54)
    paste(g, grey)
    trails(g, comp, -9, -6, length=12, spacing=3, seed=5)
    paste(g, comp)
    for grid, x, y in [(GLINT, 66, 60), (STAR5, 25, 64), (GLINT, 57, 34), (GLINT, 11, 58), (GLINT, 44, 44)]:
        stamp_fx(g, grid, x, y, only_empty=True)
    return g

def ellipse_d(x, y, cx, cy, rx, ry):
    return math.sqrt(((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2)

def frame1(base):
    g = blank()
    cx, cy = 47.5, 56
    # starburst: spikes whose radius varies with angle
    nsp = 14
    for y in range(H):
        for x in range(W):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.05
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx) + 0.11
            u = (a * nsp / (2 * math.pi)) % 1.0
            tri = 1 - abs(u - 0.5) * 2  # 0 at gap, 1 at spike centre
            k = int(math.floor(a * nsp / (2 * math.pi))) % nsp
            long_ = 1.0 if k % 2 == 0 else 0.72
            R = 38 + 42 * long_ * (tri ** 2.0)
            if r <= R:
                t = r / R
                if r < 33:
                    c = 'W'
                elif r < 38:
                    c = 'P'
                elif t < 0.72:
                    c = 'r'
                elif t < 0.93:
                    c = 'R'
                else:
                    c = 'X'
                g[y][x] = FX[c]
    # glowing silhouette of the grown Greyson inside the light
    sil = [[base[y][x] is not None for x in range(W)] for y in range(H)]
    for y in range(H):
        for x in range(W):
            if not sil[y][x]:
                continue
            edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or not sil[y + dy][x + dx]
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            g[y][x] = FX['r'] if edge else FX['W']
    # sparkles
    for grid, x, y in [(STAR7, 4, 6), (STAR7, 84, 10), (STAR5, 10, 80), (STAR5, 82, 78), (GLINT, 30, 2), (GLINT, 64, 3)]:
        stamp_fx(g, grid, x, y)
    return g

# ------------------------------------------------------------------ build

def build_all():
    base = gbig.render(clip=True)
    base = [row[:] for row in base]
    pieces = build_pieces()
    frames = [frame0(), frame1(base)]
    for f in range(2, 7):
        frames.append(assembly_frame(f, base, pieces))
    _, _, mech = read_png(ASSET + 'GreysonMech/greyson_mech.png')
    frames.append([[(p if p[3] else None) for p in row] for row in mech])
    return frames, base, pieces

def strip(frames):
    out = [[(0, 0, 0, 0)] * (W * len(frames)) for _ in range(H)]
    for i, fr in enumerate(frames):
        for y in range(H):
            for x in range(W):
                if fr[y][x] is not None:
                    out[y][i * W + x] = fr[y][x]
    return out

if __name__ == '__main__':
    frames, base, pieces = build_all()
    s = strip(frames)
    write_png('morph_strip.png', W * len(frames), H, s)
    write_png('morph_strip_4x.png', W * len(frames) * 4, H * 4, scale(s, 4, GREEN))
    for i, fr in enumerate(frames):
        write_png('mf%d_8x.png' % i, W * 8, H * 8, scale(to_rgba(fr), 8, GREEN))
    # check helmet-closed frame 6 minus fx vs approved
    print('done')
