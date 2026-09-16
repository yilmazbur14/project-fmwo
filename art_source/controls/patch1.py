src = open('bg.py', encoding='utf-8').read()


def replace_func(src, name, new_code, next_marker):
    a = src.index('def %s(' % name)
    b = src.index(next_marker, a)
    return src[:a] + new_code.strip('\n') + '\n\n\n' + src[b:]


# ---------------- door spill (subtle)
spill = '''
def draw_door_spill(c):
    """warm light leaking from under the ring door onto the floor"""
    for y in range(FLOOR_Y, FLOOR_Y + 14):
        d = y - FLOOR_Y
        xa, xb = 570 - d, 629 + d
        fall = 0.55 * (1.0 - d / 14.0)
        for x in range(xa, xb + 1):
            if not (0 <= x < W):
                continue
            edge = min(1.0, min(x - xa, xb - x) / 8.0)
            base = c.get(x, y)
            if base != G1:
                continue
            if dith(x, y, fall * edge):
                c.set(x, y, OL)
'''
src = replace_func(src, 'draw_door_spill', spill, '# ------------------------------------------------------------------ bench')

# ---------------- door (darker steel)
door = '''
def draw_door(c):
    x0, x1, y0 = DOOR['x0'], DOOR['x1'], DOOR['y0']
    yb = FLOOR_Y - 1
    # frame outline + casing (lit from top-left)
    c.vline(x0, y0, yb, K); c.vline(x1, y0, yb, K); c.hline(x0, x1, y0, K)
    c.vline(x0 + 1, y0 + 1, yb, G2); c.vline(x0 + 2, y0 + 2, yb, G1); c.vline(x0 + 3, y0 + 3, yb, K)
    c.hline(x0 + 1, x1 - 1, y0 + 1, G2); c.hline(x0 + 2, x1 - 2, y0 + 2, G1); c.hline(x0 + 3, x1 - 3, y0 + 3, K)
    c.vline(x1 - 1, y0 + 1, yb, N0); c.vline(x1 - 2, y0 + 2, yb, G1); c.vline(x1 - 3, y0 + 3, yb, K)
    # leaf
    lx0, lx1, ly0, ly1 = x0 + 4, x1 - 4, y0 + 4, yb - 1
    for y in range(ly0, ly1 + 1):
        for x in range(lx0, lx1 + 1):
            col = G1
            if x == lx0:
                col = G2
            if x == lx1 or y == ly0:
                col = N0
            c.set(x, y, col)
    # light gap under door
    c.hline(lx0, lx1, yb, GO)
    c.hline(lx0 + 4, lx1 - 4, yb, TN)
    # window: warm arena light behind wired glass
    wx0, wx1, wy0, wy1 = 588, 611, 100, 133
    c.rect(wx0, wy0, wx1, wy1, K)
    for y in range(wy0 + 1, wy1):
        for x in range(wx0 + 1, wx1):
            t = (y - wy0) / float(wy1 - wy0)
            col = TN if t < 0.22 else GO
            if 0.22 <= t < 0.42 and dith(x, y, 1 - (t - 0.22) / 0.2):
                col = TN
            if t > 0.75 and dith(x, y, (t - 0.75) / 0.25 * 0.7):
                col = OL
            if (x - wx0) % 6 == 0 or (y - wy0) % 6 == 0:
                col = GO if col == TN else OL
            c.set(x, y, col)
    for k in range(8):
        c.set(wx0 + 4 + k, wy0 + 12 - k, SK if k % 2 == 0 else TN)
    c.hline(wx0 + 1, wx1, wy1, G2)
    c.vline(wx1, wy0 + 1, wy1, G2)
    # push bar
    by = 168
    c.rect(lx0 + 3, by - 3, lx0 + 6, by + 5, K)
    c.rect(lx1 - 6, by - 3, lx1 - 3, by + 5, K)
    c.vline(lx0 + 4, by - 2, by + 4, G2); c.vline(lx1 - 5, by - 2, by + 4, G2)
    c.rect(lx0 + 5, by - 1, lx1 - 5, by + 3, K)
    c.hline(lx0 + 6, lx1 - 6, by, G4)
    c.hline(lx0 + 6, lx1 - 6, by + 1, G3)
    c.hline(lx0 + 6, lx1 - 6, by + 2, G2)
    # lower embossed panel
    px0, px1, py0, py1 = lx0 + 6, lx1 - 6, 186, 222
    c.hline(px0, px1, py0, N0); c.vline(px0, py0, py1, N0)
    c.hline(px0 + 1, px1, py1, G2); c.vline(px1, py0 + 1, py1, G2)
    # kick plate
    c.hline(lx0, lx1, 228, K)
    c.hline(lx0 + 1, lx1 - 1, 229, G3)
    c.rect(lx0 + 1, 230, lx1 - 1, yb - 1, G2)
    for sx in (lx0 + 3, lx1 - 3):
        c.set(sx, 232, K)
    # hinges
    for hy in (104, 160, 214):
        c.rect(lx0, hy, lx0 + 1, hy + 6, K)
        c.set(lx0 + 1, hy + 1, G3)
'''
src = replace_func(src, 'draw_door', door, '# ------------------------------------------------------------------ banner')

# ---------------- gloves (bigger, clearer)
gl_start = src.index('GLOVE = [')
gl_end = src.index('# ------------------------------------------------------------------ chalkboard')
gloves = '''GLOVE = [
    "....#####....",
    "...#ccccc#...",
    "...#cCCCC#...",
    "...#CCCCC#...",
    "..#########..",
    ".#hhhrrrrrr#.",
    ".#hrrrrrrrr#.",
    "#hrrrrrrrrr##",
    "#hrrrrrrrr#t#",
    "#hrrrrrrrr#t#",
    "#hrrrrrrrr#t#",
    "#hrrrrrrrr#d#",
    "#rrrrrrrrrr##",
    "#rrrrrrrrrrd#",
    "#rrrrrrrrrrd#",
    "#rrrrrrrrrdd#",
    "#drrrrrrrrdd#",
    ".#drrrrrrdd#.",
    ".#dddrrdddd#.",
    "..##dddddd#..",
    "....######...",
]
GLOVE_MAP = {'#': K, 'c': G5, 'C': G4, 'h': PK, 'r': RD, 'd': BR, 't': RD}


def draw_gloves(c):
    hx, hy = 559, 118
    c.rect(hx - 1, hy, hx + 1, hy + 3, K)
    c.set(hx, hy + 1, G3)
    back_map = dict(GLOVE_MAP)
    back_map.update({'h': RD, 'r': BR, 'd': P0, 't': BR, 'c': G4, 'C': G2})
    mirrored = [r[::-1] for r in GLOVE]
    # laces first so the cuffs sit over them
    c.line(hx, hy + 3, 553, 134, G3)
    c.line(hx, hy + 3, 562, 138, G4)
    c.grid(547, 134, mirrored, back_map, skip='.')
    c.grid(556, 138, GLOVE, GLOVE_MAP, skip='.')


'''
src = src[:gl_start] + gloves + src[gl_end:]

# ---------------- towel draped over the bench
tw_start = src.index('TOWEL = [')
tw_end = src.index('def build():')
towel = '''def towel_grid():
    Wd, Hd = 23, 30

    def edges(r):
        if r == 0:
            return (7, 15)
        if r == 1:
            return (5, 17)
        if r == 2:
            return (3, 19)
        if r <= 10:
            return (2, 20)
        if r <= 19:
            return (1, 21)
        return (0, 22)
    bottom = [26, 27, 28, 28, 27, 26, 27, 28, 29, 29, 28, 28, 27, 28, 29, 29, 28, 27, 26, 27, 28, 28, 27]

    def inside(cx, r):
        if r < 0 or r >= Hd or cx < 0 or cx >= Wd:
            return False
        L, R = edges(r)
        return L <= cx <= R and r <= bottom[cx]
    g = [['.'] * Wd for _ in range(Hd)]
    folds = {7: 'g', 15: 'g'}
    for r in range(Hd):
        L, R = edges(r)
        for cx in range(Wd):
            if not inside(cx, r):
                continue
            if any(not inside(cx + a, r + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[r][cx] = '#'
                continue
            ch = 'w'
            if r <= 2:
                ch = 'W'
            elif r == 7:
                ch = 'W'
            elif r == 8:
                ch = 'g'
            else:
                fold_shift = 1 if r >= 17 else 0
                if r >= 9 and (cx - fold_shift) in folds:
                    ch = 'g'
                elif r >= 9 and (cx - fold_shift - 1) in folds:
                    ch = 'W'
                if r in (19, 22):
                    ch = 'r'
                elif r in (20, 23):
                    ch = 'R'
            if cx == L + 1 and ch in 'wg':
                ch = 'W'
            if cx == R - 1 and ch in 'wW':
                ch = 'g'
            if r >= bottom[cx] - 1 and ch in 'wW':
                ch = 'g'
            g[r][cx] = ch
    return [''.join(row) for row in g]


TOWEL_MAP = {'#': K, 'W': G5, 'w': G4, 'g': G2, 'r': RD, 'R': BR}


def draw_towel(c):
    c.grid(17, 213, towel_grid(), TOWEL_MAP, skip='.')


'''
src = src[:tw_start] + towel + src[tw_end:]
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
