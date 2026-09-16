"""Controls-screen background: the Arena #1 locker room. 640x360, DB32 only.

Visible areas (everything else sits behind UI): top strip y<17, left strip x<50,
right strip x>550 (above y=276), thin margins around the dialogue box.
"""
import os, sys
from common import Canvas, write_png

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
os.makedirs(OUT, exist_ok=True)

W, H = 640, 360

# ---- DB32 names
K = '000000'; N0 = '222034'; P0 = '45283c'; BR = '663931'; BR2 = '8f563b'; OR = 'df7126'
TN = 'd9a066'; SK = 'eec39a'; YL = 'fbf236'; IN = '3f3f74'; BL = '306082'; RB = '5b6ee1'
G1 = '323c39'; G2 = '595652'; G3 = '696a6a'; G4 = '847e87'; G5 = '9badb7'; WH2 = 'cbdbfc'
WH = 'ffffff'; RD = 'ac3232'; PK = 'd95763'; PU = '76428a'; GO = '8a6f30'; OL = '524b24'

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dith(x, y, t):
    return (BAYER4[y % 4][x % 4] + 0.5) / 16.0 < t


# ---- layout constants
CEIL_END = 5
WALL_Y0 = 6
CROWN_Y = 110
DOOR_Y0 = 114
DOOR_Y1 = 235
PLINTH_Y0 = 236
FLOOR_Y = 244
LOCKER_X0 = -6
LOCKER_PITCH = 22
LOCKER_END = 548
FIXTURES = [26, 173, 320, 467]


def light_level(x, y):
    best = -9.0
    for fx in FIXTURES:
        dx = (x - fx) / 70.0
        dy = (y - 10) / 95.0
        best = max(best, 1.0 - (dx * dx + dy * dy))
    return best


# ------------------------------------------------------------------ wall
def draw_wall(c):
    for y in range(0, CEIL_END + 1):
        for x in range(W):
            c.set(x, y, N0)
    for x in range(0, W, 40):
        for y in range(0, CEIL_END):
            c.set(x, y, K)
    c.hline(0, W - 1, CEIL_END, K)
    BH, BW = 14, 28
    for y in range(WALL_Y0, FLOOR_Y):
        row = (y - WALL_Y0) // BH
        off = (BW // 2) if row % 2 else 0
        for x in range(W):
            mh = (y - WALL_Y0) % BH == BH - 1
            mv = (x + off) % BW == BW - 1
            mortar = mh or mv
            lv = light_level(x, y)
            top_edge = (y - WALL_Y0) % BH == 0
            col = P0
            if mortar:
                col = P0 if lv > 0.5 else N0
            elif top_edge and lv > 0.55:
                col = BR
            # soft shadow under the ceiling line
            sh = 1.0 - (y - WALL_Y0) / 7.0
            under_light = any(abs(x - fx) <= 22 for fx in FIXTURES)
            if sh > 0 and not under_light and dith(x, y, sh):
                col = K if mortar else N0
            c.set(x, y, col)
    c.hline(0, W - 1, FLOOR_Y - 1, K)


def draw_fixture(c, fx):
    x0, x1 = fx - 25, fx + 24
    c.hline(x0, x1, 6, K)
    for y, col in ((7, G3), (8, G2)):
        c.set(x0, y, K); c.set(x1, y, K)
        c.hline(x0 + 1, x1 - 1, y, col)
    c.set(x0, 9, K); c.set(x1, 9, K)
    c.hline(x0 + 1, x1 - 1, 9, G5)
    c.hline(x0 + 4, x1 - 4, 9, WH2)
    c.hline(x0 + 1, x1 - 1, 10, K)


# ------------------------------------------------------------------ lockers
def draw_lockers(c):
    c.hline(0, LOCKER_END, CROWN_Y, K)
    c.hline(0, LOCKER_END - 1, CROWN_Y + 1, BL)
    c.hline(0, LOCKER_END - 1, CROWN_Y + 2, IN)
    c.hline(0, LOCKER_END - 1, CROWN_Y + 3, N0)
    c.vline(LOCKER_END, CROWN_Y, FLOOR_Y - 1, K)
    i = 0
    xs = LOCKER_X0
    while xs < LOCKER_END:
        xd0, xd1 = xs + 1, min(xs + LOCKER_PITCH - 1, LOCKER_END - 1)
        if xs >= 0:
            c.vline(xs, DOOR_Y0, DOOR_Y1, K)
        for y in range(DOOR_Y0, DOOR_Y1 + 1):
            for x in range(xd0, xd1 + 1):
                col = IN
                if x == xd0 or y == DOOR_Y0:
                    col = BL
                if x == xd1 or y == DOOR_Y1:
                    col = N0
                if y > 206 and col == IN and dith(x, y, (y - 206) / 40.0):
                    col = N0
                c.set(x, y, col)
        for k in range(5):
            vy = DOOR_Y0 + 6 + k * 3
            c.hline(xd0 + 5, xd1 - 5, vy, K)
            c.hline(xd0 + 5, xd1 - 5, vy + 1, BL)
        for k in range(3):
            vy = 208 + k * 3
            c.hline(xd0 + 5, xd1 - 5, vy, K)
            c.hline(xd0 + 5, xd1 - 5, vy + 1, IN)
        c.rect(xd0 + 7, 138, xd1 - 7, 141, G2)
        c.hline(xd0 + 7, xd1 - 7, 138, G3)
        lx = xd1 - 4
        c.vline(lx - 1, 160, 176, K)
        c.vline(lx + 1, 160, 176, K)
        c.set(lx, 159, K); c.set(lx, 177, K)
        c.vline(lx, 160, 176, G3)
        c.set(lx, 161, G4)
        if i % 3 == 1:
            c.rect(lx - 2, 168, lx + 2, 173, K)
            c.rect(lx - 1, 169, lx + 1, 172, GO)
            c.set(lx - 1, 169, TN)
            c.set(lx - 1, 167, K); c.set(lx + 1, 167, K); c.hline(lx - 1, lx + 1, 166, K)
        i += 1
        xs += LOCKER_PITCH
    c.hline(0, LOCKER_END - 1, PLINTH_Y0, K)
    c.rect(0, PLINTH_Y0 + 1, LOCKER_END - 1, FLOOR_Y - 2, N0)
    c.hline(0, LOCKER_END - 1, FLOOR_Y - 1, K)


# ------------------------------------------------------------------ floor
def draw_floor(c):
    VPX, VPY = 320, 132
    for y in range(FLOOR_Y, H):
        for x in range(W):
            c.set(x, y, G1)
    for xb in range(-600, 1300, 56):
        for y in range(FLOOR_Y, H):
            t = (y - VPY) / float(FLOOR_Y - VPY)
            x = int(round(VPX + (xb - VPX) * t))
            c.set(x, y, N0)
    for y in [244, 252, 262, 275, 292, 314, 342]:
        c.hline(0, W - 1, y, N0)


def draw_door_spill(c):
    """warm light leaking from under the ring door onto the floor"""
    # (row offset below the floor line, coverage, horizontal growth)
    bands = [(0, 1.0, 0), (1, 0.5, 1), (2, 0.5, 2), (3, 0.25, 3), (4, 0.25, 4)]
    for d, cov, grow in bands:
        y = FLOOR_Y + d
        xa, xb = 572 - grow, 627 + grow
        for x in range(xa, xb + 1):
            if not (0 <= x < W) or c.get(x, y) not in (G1, N0):
                continue
            # soften the band ends
            end = min(x - xa, xb - x)
            cv = cov if end >= 3 else cov * 0.5
            if cv >= 1.0 or dith(x, y, cv):
                c.set(x, y, OL)


# ------------------------------------------------------------------ bench
def draw_bench(c):
    x0, x1 = -10, 520
    for lx in (14, 140, 266, 392, 506):
        for y in range(229, 262):
            c.set(lx - 1, y, K); c.set(lx + 2, y, K)
            c.set(lx, y, G2); c.set(lx + 1, y, G1)
        c.hline(lx - 2, lx + 3, 262, K)
    for y in range(255, 266):
        for x in range(max(0, x0), x1 + 1):
            if c.get(x, y) in (G1, N0) and dith(x, y, 0.5):
                c.set(x, y, N0)
    c.hline(x0, x1, 221, K)
    c.hline(x0, x1, 222, BR2)
    c.hline(x0, x1, 223, BR)
    c.hline(x0, x1, 224, BR)
    c.hline(x0, x1, 225, K)
    c.hline(x0, x1, 226, P0)
    c.hline(x0, x1, 227, P0)
    c.hline(x0, x1, 228, K)
    c.vline(x1, 221, 228, K)
    for sx in range(40, x1, 90):
        c.set(sx, 222, BR); c.set(sx, 223, P0); c.set(sx, 224, P0)


# ------------------------------------------------------------------ ring door
DOOR = dict(x0=566, x1=633, y0=86)


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


# ------------------------------------------------------------------ banner
FONT4 = {
    'A': [".XX.", "X..X", "XXXX", "X..X", "X..X"],
    'R': ["XXX.", "X..X", "XXX.", "X.X.", "X..X"],
    'E': ["XXXX", "X...", "XXX.", "X...", "XXXX"],
    'N': ["X..X", "XX.X", "X.XX", "X..X", "X..X"],
}
HASH = [".X.X.", ".X.X.", "XXXXX", ".X.X.", "XXXXX", ".X.X.", ".X.X."]
ONE = [".XX.", "XXX.", ".XX.", ".XX.", ".XX.", ".XX.", "XXXX"]


def stamp(c, x0, y0, rows, col, s=1):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == 'X':
                c.rect(x0 + i * s, y0 + j * s, x0 + i * s + s - 1, y0 + j * s + s - 1, col)


def draw_banner(c):
    bx0, bx1 = 575, 624
    ry = 17
    # rod
    c.rect(bx0 - 4, ry - 1, bx1 + 4, ry + 2, K)
    c.hline(bx0 - 3, bx1 + 3, ry, G4)
    c.hline(bx0 - 3, bx1 + 3, ry + 1, G2)
    top, tail, notch = ry + 3, 78, 69
    mid = (bx0 + bx1) / 2.0
    for x in range(bx0, bx1 + 1):
        # swallowtail: bottom y varies linearly from tail at edges to notch at centre
        frac = abs(x - mid) / (mid - bx0)
        ybot = int(round(notch + (tail - notch) * frac))
        for y in range(top, ybot + 1):
            col = N0
            if x == bx0 + 1:
                col = IN
            c.set(x, y, col)
        c.set(x, ybot, K)
        c.set(x, ybot + 1, K) if x in (bx0, bx1) else None
    c.vline(bx0, top, tail, K)
    c.vline(bx1, top, tail, K)
    # fix bottom outline continuity along the V edges
    for x in range(bx0, bx1 + 1):
        frac = abs(x - mid) / (mid - bx0)
        ybot = int(round(notch + (tail - notch) * frac))
        nb = int(round(notch + (tail - notch) * abs(x + 1 - mid) / (mid - bx0))) if x < bx1 else ybot
        for yy in range(min(ybot, nb), max(ybot, nb) + 1):
            if c.get(x, yy) == N0 and yy >= min(ybot, nb) and abs(yy - ybot) <= abs(nb - ybot):
                pass
    # finials on the rod ends
    for fx in (bx0 - 6, bx1 + 5):
        c.rect(fx, ry - 2, fx + 1, ry + 3, K)
        c.set(fx, ry - 1, G4)
        c.set(fx, ry, G3)
    # inner trim lines
    c.hline(bx0 + 3, bx1 - 3, top + 3, IN)
    # text
    word = 'ARENA'
    tw = len(word) * 4 + (len(word) - 1)
    tx = int(round(mid - tw / 2.0 + 0.5))
    for k, ch in enumerate(word):
        stamp(c, tx + k * 5, top + 8, FONT4[ch], G4)
    # "#1" at 2x
    hw = 5 * 2 + 2 + 4 * 2
    hx = int(round(mid - hw / 2.0 + 0.5))
    stamp(c, hx, top + 18, HASH, G5, 2)
    stamp(c, hx + 12, top + 18, ONE, G5, 2)


# ------------------------------------------------------------------ gloves
GLOVE = [
    ".....#####......",
    "....#WcccC#.....",
    "....#cccCC#.....",
    "....#######.....",
    "....#hrrrd#.....",
    "...#hrrrrrd#....",
    "..#hhrrrrrd##...",
    "..#hrrrrrrd#t#..",
    ".#hrrrrrrrd#tt#.",
    ".#hrrrrrrrr#ttd#",
    "#hhsrrrrrrrr#td#",
    "#hssrrrrrrrrr#d#",
    "#hhrrrrrrrrrrr##",
    "#hrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrrd#",
    "#rrrrrrrrrrrrdd#",
    "#drrrrrrrrrrrdd#",
    ".#drrrrrrrrrdd#.",
    ".#ddrrrrrrrddd#.",
    "..#dddddddddd#..",
    "...##dddddd##...",
    ".....######.....",
]
for _r in GLOVE:
    assert len(_r) == 16, (_r, len(_r))
GLOVE_MAP = {'#': K, 'W': G5, 'c': G4, 'C': G2, 'h': PK, 's': SK, 'r': RD, 'd': BR, 't': RD}


def draw_gloves(c):
    hx, hy = 561, 116
    c.rect(hx - 1, hy, hx + 1, hy + 3, K)
    c.set(hx, hy + 1, G3)
    back_map = dict(GLOVE_MAP)
    back_map.update({'W': G4, 'c': G2, 'C': G1, 'h': RD, 's': PK, 'r': BR, 'd': P0, 't': BR})
    mirrored = [r[::-1] for r in GLOVE]
    c.line(hx, hy + 3, 555, 131, G3)
    c.line(hx, hy + 3, 563, 135, G4)
    c.grid(547, 131, mirrored, back_map, skip='.')
    c.grid(555, 135, GLOVE, GLOVE_MAP, skip='.')


# ------------------------------------------------------------------ wall clock
CLOCK_RING = [
    "......######......",
    "....##......##....",
    "...#..........#...",
    "..#............#..",
    ".#..............#.",
    ".#..............#.",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    ".#..............#.",
    ".#..............#.",
    "..#............#..",
    "...#..........#...",
    "....##......##....",
    "......######......",
]


def draw_clock(c):
    import math
    ox, oy = 1, 30
    cx, cy = ox + 8.5, oy + 8.5
    for j, row in enumerate(CLOCK_RING):
        xs = [i for i, ch in enumerate(row) if ch == '#']
        for i in range(xs[0], xs[-1] + 1):
            x, y = ox + i, oy + j
            if row[i] == '#':
                c.set(x, y, K)
                continue
            r = math.hypot(x - cx, y - cy)
            if r > 6.3:
                c.set(x, y, G3 if (x - cx) + (y - cy) < -1.5 else G2)
            elif r > 5.4:
                c.set(x, y, N0)
            else:
                c.set(x, y, G5 if (x - cx) + (y - cy) < -4.5 else G4)
    # hour ticks
    for (x, y) in [(9, 33), (10, 33), (9, 44), (10, 44), (4, 38), (4, 39), (15, 38), (15, 39)]:
        c.set(x, y, G2)
    # hands: just before eight - minute hand near 12, hour hand toward 8
    for (x, y) in [(9, 34), (9, 35), (9, 36), (9, 37), (9, 38), (10, 38)]:
        c.set(x, y, K)
    for (x, y) in [(8, 39), (7, 40), (6, 40)]:
        c.set(x, y, K)
    c.set(10, 39, RD)
    c.set(11, 40, RD)
    c.set(6, 34, WH2)
    c.set(5, 35, WH2)


# ------------------------------------------------------------------ towel
TOWEL = [
    "...###############...",
    "..#WWWWWWWWWWWWWWg#..",
    "..#WWWWWWWWWWWWWWg#..",
    "..#wwwwwwwwwwwwwwg#..",
    "..#gggwwwwwwwwgggg#..",
    "..#Wwwwwwgwwwwwwwg#..",
    "..#Wwwwwwgwwwwwwwg#..",
    ".#Wwwwwwwgwwwwwwwwg#.",
    ".#Wwwwwwwgwwwwwwwwg#.",
    ".#Wwwwwwwwgwwwwwwwg#.",
    ".#prrrrrrrrrrrrrrrR#.",
    ".#RRRRRRRRRRRRRRRRR#.",
    ".#Wwwwwwwwgwwwwwwwg#.",
    ".#prrrrrrrrrrrrrrrR#.",
    ".#RRRRRRRRRRRRRRRRR#.",
    "#Wwwwwwwwwgwwwwwwwwg#",
    "#Wwwwwwwwwwgwwwwwwwg#",
    "#wwwwwwwwwwgwwwwwwwg#",
    "#gwwwwwwwwwgwwwwwwgg#",
    "#ggggwwwwwwgwwwwwwgg#",
    ".####gggwwwgwwwwwggg#",
    ".....####ggggwwwggg#.",
    ".........#####gggg#..",
    "..............####...",
]
for _r in TOWEL:
    assert len(_r) == 21, (_r, len(_r))


def towel_grid():
    return TOWEL


TOWEL_MAP = {'#': K, 'W': G5, 'w': G4, 'g': G2, 'r': RD, 'R': BR, 'p': PK}


def draw_towel(c):
    c.grid(-3, 221, towel_grid(), TOWEL_MAP, skip='.')


def build():
    c = Canvas(W, H)
    draw_wall(c)
    draw_floor(c)
    draw_door_spill(c)
    draw_lockers(c)
    draw_bench(c)
    draw_door(c)
    draw_banner(c)
    draw_clock(c)
    draw_towel(c)
    draw_gloves(c)
    for fx in FIXTURES:
        draw_fixture(c, fx)
    return c


CARDS = [(50, 17, 213, 275), (218, 17, 382, 275), (387, 17, 550, 275)]
CARDS_UIKIT = [(20, 13, 179, 265), (193, 13, 352, 265), (367, 13, 526, 265)]
DLG = (10, 276, 630, 354)


def mock(c, name, scale=2):
    rgba = c.to_rgba()
    out = []
    for Y in range(H * scale):
        y = Y // scale
        row = []
        for X in range(W * scale):
            x = X // scale
            p = rgba[y][x]
            for r in CARDS + [DLG]:
                if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
                    edge = x in (r[0], r[2]) or y in (r[1], r[3])
                    p = (203, 219, 252, 255) if edge else (60, 58, 70, 255)
            row.append(p)
        out.append(row)
    write_png(os.path.join(OUT, name), W * scale, H * scale, out)


def crop_zoom(c, x0, y0, x1, y1, s, name):
    rgba = c.to_rgba()
    out = []
    for Y in range((y1 - y0) * s):
        y = y0 + Y // s
        out.append([rgba[y][x0 + X // s] for X in range((x1 - x0) * s)])
    write_png(os.path.join(OUT, name), (x1 - x0) * s, (y1 - y0) * s, out)


if __name__ == '__main__':
    c = build()
    c.save(os.path.join(OUT, 'controls_bg.png'))
    rgba = c.to_rgba()
    write_png(os.path.join(OUT, 'bg_full_2x.png'), W * 2, H * 2,
              [[rgba[Y // 2][X // 2] for X in range(W * 2)] for Y in range(H * 2)])
    mock(c, 'bg_mock_2x.png')
    crop_zoom(c, 540, 0, 640, 280, 4, 'bg_right_4x.png')
    crop_zoom(c, 0, 0, 60, 280, 4, 'bg_left_4x.png')
    print('ok')
