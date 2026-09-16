"""POO BOMB - final hand-refined ASCII grid composition. 2 frames x 32x32 -> 64x32.
Pile bodies were frozen from the 3D coil render (bomb_gen.py) and are edited here by hand."""
import fxpng

W = H = 32
FLOOR = (136, 180, 99)

PAL = {
    '.': None, 'K': '#000000',
    # poo ramp
    'a': '#3B1F1E',  # deep shadow
    'b': '#5C3326',  # shadow
    'c': '#7E4A2E',  # base
    'd': '#A0633A',  # light
    'e': '#C98A4E',  # highlight
    'f': '#F0CC98',  # wet glint
    # fuse cord
    'g': '#F4EEDC',  # cord lit
    'h': '#B5AA92',  # cord shade
    'i': '#4A3A36',  # charred end
    # spark
    'W': '#FFFFFF',
    'Y': '#FBF236',
    'O': '#DF7126',
    'R': '#AC3232',
}

# ---------------------------------------------------------------- frozen piles
PILE = [
    [  # frame 0 - rest
        "................................",  # 0
        "................................",  # 1
        "................................",  # 2
        "................................",  # 3
        "................................",  # 4
        "................................",  # 5
        "................................",  # 6
        ".................KK.............",  # 7
        "................KcK.............",  # 8
        "................KcK.............",  # 9
        "...............KcbK.............",  # 10
        "...............KcbbK............",  # 11
        "............KKKbbKedK...........",  # 12
        "...........KeedKeedcbKK.........",  # 13
        "...........KeedfddccbKdK........",  # 14
        ".........KKddddccccbKedcK.......",  # 15
        "........KedKccccbbbKeddcbK......",  # 16
        ".......KeeedKKbbbKKeddccbKK.....",  # 17
        "......KdeeeeeeeeeedddcccbKcK....",  # 18
        ".....KKdddddfdddddddcccbKdcK....",  # 19
        "....KeeKdddddddddccccbbbKdcK....",  # 20
        "....KeeKKccccccccccbbbKKdccK....",  # 21
        "....KeeeeKKcccccbbbbKdddcccK....",  # 22
        "....KdeeeeeeeKKKKKdddddcccbK....",  # 23
        "....KdddddffdddddddddccccbbK....",  # 24
        "....KcddddddddddddccccccbbK.....",  # 25
        ".....KccccddccccccccccbbbK......",  # 26
        "......KccccccccccccbbbbKK.......",  # 27
        ".......KKcccccbbbbbbbKK.........",  # 28
        ".........KKKKKKKKKKKK...........",  # 29
        "................................",  # 30
        "................................",  # 31
    ],
]


def grid_of(rows):
    g = [list(r) for r in rows]
    assert len(g) == H and all(len(r) == W for r in g), 'bad grid dims'
    return g


def stamp(g, y0, rows):
    """rows: list of (x0, str). '_' in str leaves the pixel unchanged."""
    for dy, (x0, s) in enumerate(rows):
        for dx, ch in enumerate(s):
            if ch != '_':
                g[y0 + dy][x0 + dx] = ch


def to_px(grids):
    out = [[(0, 0, 0, 0)] * (W * len(grids)) for _ in range(H)]
    for f, g in enumerate(grids):
        for y in range(H):
            for x in range(W):
                c = PAL[g[y][x]]
                if c:
                    out[y][f * W + x] = fxpng.hexc(c)
    return out


def crop_view(px, x0, y0, w, h, k, bg='checker'):
    sub = [row[x0:x0 + w] for row in px[y0:y0 + h]]
    return fxpng.view(w, h, sub, k, bg=bg)


def fuse(g, cord):
    """cord: list of (x, y, ch). Draw cord then a 4-connected black outline on empty cells."""
    for x, y, ch in cord:
        g[y][x] = ch
    for x, y, ch in cord:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and g[ny][nx] == '.':
                g[ny][nx] = 'K'


def spark(g, cx, cy, pattern, protect=()):
    """pattern: list of strings centred on (cx, cy); '.' = skip."""
    ph = len(pattern)
    pw = len(pattern[0])
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            x, y = cx - pw // 2 + i, cy - ph // 2 + j
            if 0 <= x < W and 0 <= y < H and (x, y) not in protect:
                g[y][x] = ch


SPARK_BIG = [
    "...Y...",
    ".O.Y.O.",
    "..YWY..",
    "YYWWWYY",
    "..YWY..",
    ".O.Y.O.",
    "...Y...",
]
SPARK_SMALL = [
    "O...O",
    ".YWY.",
    ".WWW.",
    ".YWY.",
    "O...O",
]


SPARK_PLUS = [          # frame 0: big "+" star
    "...O...",
    ".O.Y.O.",
    "..YWY..",
    "OYWWWYO",
    "..YWY..",
    ".O.Y.O.",
    "...O...",
]
SPARK_BIG9 = [          # frame 0: big "+" star with a hot orange halo
    "....O....",
    "....Y....",
    ".R..Y..R.",
    "...OWO...",
    "OYYWWWYYO",
    "...OWO...",
    ".R..Y..R.",
    "....Y....",
    "....O....",
]
SPARK_X = [             # frame 1: "x" twinkle
    "O.....O",
    ".Y...Y.",
    "..YWY..",
    "..WWW..",
    "..YWY..",
    ".Y...Y.",
    "O.....O",
]


def deep_shadows(g):
    """Occlusion: shadow pixels tucked against the outline at the bottom/right, or directly
    under a crease, drop to the deepest tone."""
    hits = []
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if g[y][x] != 'b':
                continue
            below, right, above = g[y + 1][x], g[y][x + 1], g[y - 1][x]
            if below == 'K' and x >= 13:
                hits.append((x, y))
            elif right == 'K' and y >= 21:
                hits.append((x, y))
            elif above == 'K' and y >= 14 and x >= 12:
                hits.append((x, y))
    for x, y in hits:
        g[y][x] = 'a'


def move_glint(g, old, new):
    for x, y in old:
        assert g[y][x] == 'f', (x, y, g[y][x])
        g[y][x] = 'd'
    for x, y in new:
        g[y][x] = 'f'


def swell(g, lcol=13, rcol=18, drow=20):
    """Throb frame: duplicate one column in each half (1px wider each side) and one row
    (1px taller, everything above moves up). Keeps every crease in the same structure."""
    out = [['.'] * W for _ in range(H)]
    xmap = {}
    for x in range(W):
        if x < lcol:
            xmap.setdefault(x - 1, x)
        elif x == lcol:
            xmap[x - 1] = x
            xmap[x] = x
        elif x < rcol:
            xmap[x] = x
        elif x == rcol:
            xmap[x] = x
            xmap[x + 1] = x
        else:
            xmap[x + 1] = x
    ymap = {}
    for y in range(H):
        if y < drow:
            ymap[y - 1] = y
        elif y == drow:
            ymap[y - 1] = y
            ymap[y] = y
        else:
            ymap[y] = y
    for ny, oy in ymap.items():
        if not 0 <= ny < H:
            continue
        for nx, ox in xmap.items():
            if 0 <= nx < W:
                out[ny][nx] = g[oy][ox]
    return out


def build(drow=20):
    f0 = grid_of(PILE[0])

    # ---- pile clean-up -------------------------------------------------------
    # wet glints: short streaks on the lit upper-left band of each coil
    move_glint(f0, [(15, 14), (12, 19), (10, 24), (11, 24)], [(13, 14), (10, 18), (11, 18), (8, 23), (9, 23)])
    deep_shadows(f0)
    # clear the generated wisp of a tip; everything above tier 3 is redrawn by hand
    for y in range(0, 12):
        f0[y] = ['.'] * W
    stamp(f0, 8, [
        (17, "KK"),
        (16, "KdcK"),
        (15, "KeddcK"),
        (15, "KeddcbK"),
        (12, "KKKeeddcbK"),
        (11, "KeefKdddcbbKK"),
    ])

    # ---- frame 1 = swollen copy of the finished pile (before fuse/spark) ------
    f1 = swell(f0, drow=drow)

    # ---- frame 0: fuse + big "+" spark -----------------------------------------
    cord0 = [(18, 7, 'g'), (19, 7, 'h'), (19, 6, 'g'), (20, 6, 'h'), (20, 5, 'g'), (21, 5, 'g'),
             (21, 6, 'h'), (22, 5, 'h'), (22, 4, 'i')]
    fuse(f0, cord0)
    spark(f0, 23, 4, SPARK_BIG9, protect={(x, y) for x, y, c in cord0 if c != 'i'})

    # ---- frame 1: same fuse shifted with the swollen tip, "x" twinkle ----------
    cord1 = [(x + 1, y - 1, c) for x, y, c in cord0]
    fuse(f1, cord1)
    # the twinkle's outer sparkles must not eat the cord's outline, but its white core
    # always draws over it (the spark sits in front of the burning end)
    outline1 = {(x + dx, y + dy) for x, y, c in cord1 if c != 'i'
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if f1[y + dy][x + dx] == 'K'}
    before = {p: f1[p[1]][p[0]] for p in outline1}
    spark(f1, 24, 3, SPARK_X, protect={(x, y) for x, y, c in cord1 if c != 'i'})
    for (x, y), ch in before.items():
        if f1[y][x] not in ('W', ch):
            f1[y][x] = ch
    return [f0, f1]


def show(frames, tag):
    px = to_px(frames)
    fxpng.write_png('bomb_%s.png' % tag, 64, 32, px)
    a, b, o = fxpng.view(64, 32, px, 10, grid=(32, 32))
    fxpng.write_png('bomb_%s_10x.png' % tag, a, b, o)
    # top detail crop of both frames side by side
    rows = []
    for y in range(0, 18):
        rows.append(px[y][8:28] + [(255, 0, 255, 255)] + px[y][40:60])
    a, b, o = fxpng.view(41, 18, rows, 16)
    fxpng.write_png('bomb_%s_top16x.png' % tag, a, b, o)
    a, b, o = fxpng.view(64, 32, px, 3, bg=FLOOR)
    fxpng.write_png('bomb_%s_3x_floor.png' % tag, a, b, o)
    return px


if __name__ == '__main__':
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else 'v2'
    drow = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    frames = build(drow)
    show(frames, tag)
    for f in frames:
        print('    ' + ''.join(str(x % 10) for x in range(32)))
        for y, row in enumerate(f):
            print('%2d  %s' % (y, ''.join(row)))
