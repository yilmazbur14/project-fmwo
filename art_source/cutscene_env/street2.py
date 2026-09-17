"""street_buildings.png part 2: poster wall building, cafe, lighting, build()."""
from lib import Canvas, bayer, hsh, ellipse_mask, boundary, text_width
from fonts import F57, F35
from street import (PROT, protect_rect, W, H, WALL, SW0, SW1, FEET, CURB, ROAD, WARM, DARK, radial, bricks, panels, stain,
                    cornice, window, awning, door, ground, puddle, reflection,
                    building_A, building_B, building_C, building_D, building_E)

MASCOT15 = [
    "..UUU.....UUU..",
    ".UUUUUUUUUUUUU.",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    ".UUUUUUUUUUUUU.",
    "..UUUU...UUUU..",
]
MASCOT9 = [
    ".UU...UU.",
    "UUUUUUUUU",
    "UUUUUUUUU",
    "UUWUUUWUU",
    "UUWUUUWUU",
    "UUUUUUUUU",
    ".UUU.UUU.",
]
POSTER = (948, 166, 987, 221)   # x0, y0, x1, y1 inclusive, in street_buildings.png
LAMPS = (380, 862)             # curbside lamp posts (drawn in street_fg.png)
OPTS = {'poster': True}        # False -> build the street without the MEMBERS WANTED poster (layer split)


def street_poster(c):
    x0, y0, x1, y1 = POSTER
    # drop shadow on the wall
    for y in range(y0 + 2, y1 + 3):
        for x in range(x0 + 2, x1 + 3):
            k = c.get(x, y)
            if k is not None and k != 'K':
                c.set(x, y, DARK.get(DARK.get(k, k), k))
    c.rect(x0, y0, x1, y1, 'W')
    c.vline(x1 - 1, y0 + 1, y1 - 1, 'P')
    c.hline(x0 + 1, x1 - 1, y1 - 1, 'P')
    # header
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 15, 'U')
    c.hline(x0 + 1, x1 - 1, y0 + 15, 'I')
    c.hline(x0 + 1, x1 - 1, y0 + 1, 'u')
    for (word, yy) in (('MEMBERS', y0 + 3), ('WANTED', y0 + 9)):
        tw = text_width(word, F35)
        c.text(x0 + 1 + (x1 - x0 - 1 - tw) // 2, yy, word, F35, 'W')
    # mascot
    mx = x0 + (x1 - x0 + 1 - 9) // 2
    c.stamp(MASCOT9, mx, y0 + 18)
    # ARENA #1
    word = 'ARENA #1'
    tw = text_width(word, F35)
    c.text(x0 + 1 + (x1 - x0 - 1 - tw) // 2, y0 + 28, word, F35, 'N')
    # small print lines
    for (yy, a, b) in ((y0 + 36, 7, 32), (y0 + 39, 10, 29)):
        c.hline(x0 + a, x0 + b, yy, 'g')
    # tear-off tabs
    c.hline(x0 + 1, x1 - 1, y0 + 42, 'P')
    for i, tx in enumerate(range(x0 + 2, x1 - 2, 5)):
        if i in (2, 5):
            continue
        c.vline(tx + 2, y0 + 44, y1 - 2, 'g')
        c.vline(tx + 4, y0 + 43, y1 - 1, 'P')
    c.box(x0, y0, x1, y1, 'K')
    # torn-off tab gaps show the wall
    for i, tx in enumerate(range(x0 + 2, x1 - 2, 5)):
        if i in (2, 5):
            for y in range(y0 + 45, y1 + 1):
                for x in range(tx, tx + 4):
                    c.set(x, y, 'M')
            c.hline(tx - 1, tx + 4, y0 + 44, 'K')
            c.vline(tx - 1, y0 + 44, y1, 'K')
            c.vline(tx + 4, y0 + 44, y1, 'K')
    # tape
    for (tx, ty) in ((x0 - 2, y0 - 1), (x1 - 3, y0 - 1)):
        c.rect(tx, ty, tx + 5, ty + 2, 'P')
        c.set(tx, ty, 'g')
        c.set(tx + 5, ty + 2, 'g')


FLYERS = [
    # x0, y0, x1, y1, paper, ink, kind, torn corner
    (884, 162, 914, 196, 'd', 'B', 'lines', 'br'),
    (910, 168, 944, 206, 'g', 'I', 'lost', 'tl'),
    (888, 194, 922, 232, '8', 'M', 'gig', None),
    (918, 204, 950, 232, 's', 'w', 'tabs', None),
    (984, 160, 1016, 192, 'A', '5', 'lines', 'tr'),
    (994, 186, 1030, 228, 'P', '7', 'lines', 'bl'),
    (1020, 164, 1052, 198, 'F', 'N', 'sale', None),
    (1026, 196, 1052, 232, '9', '4', 'lines', 'tr'),
    (972, 212, 1000, 232, 'd', 'B', 'tabs', None),
]


def flyer(c, x0, y0, x1, y1, paper, ink, kind, torn, seed):
    m = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x in (x0, x1) or y in (y0, y1)) and hsh(x, y, seed) < 0.3:
                continue
            if torn:
                u = (x - x0) if 'l' in torn else (x1 - x)
                v = (y - y0) if 't' in torn else (y1 - y)
                if u + v < 9 + int(3 * hsh(x, y, seed + 1)):
                    continue
            m.add((x, y))
    edge = boundary(m)
    for (x, y) in m:
        k = paper
        if (x, y) in edge:
            k = DARK.get(paper, paper)
        elif y > y1 - 8 and bayer(x, y) < (y - (y1 - 8)) / 12.0:
            k = DARK.get(paper, paper)
        c.set(x, y, k)
    iw = x1 - x0

    def ink_line(xa, xb, yy, col):
        for x in range(xa, xb + 1):
            if (x, yy) in m and (x, yy) not in edge and hsh(x, yy, seed + 3) > 0.15:
                c.set(x, yy, col)

    if kind == 'lines':
        for x in range(x0 + 4, x0 + 5 + iw // 2):
            for yy in (y0 + 3, y0 + 4):
                if (x, yy) in m and (x, yy) not in edge:
                    c.set(x, yy, ink)
        for yy in range(y0 + 8, y1 - 4, 4):
            ln = int(iw * (0.45 + 0.4 * hsh(yy, x0, seed)))
            ink_line(x0 + 4, x0 + 4 + ln, yy, ink)
    elif kind == 'lost':
        c.text(x0 + 9, y0 + 4, 'LOST', F35, ink)
        cat = [".X...X.", ".XXXXX.", "XX.X.XX", "XXXXXXX", ".XXXXX.", "..XXX.."]
        c.stamp(cat, x0 + 13, y0 + 13, {'X': ink})
        for yy in (y0 + 23, y0 + 27, y0 + 31):
            ink_line(x0 + 5, x1 - 6, yy, DARK.get(paper, paper))
    elif kind == 'gig':
        star = ["....X....", "...XXX...", "XXXXXXXXX", ".XXXXXXX.", "..XXXXX..", ".XXX.XXX.", ".X.....X."]
        c.stamp(star, x0 + 12, y0 + 4, {'X': ink})
        c.text(x0 + 11, y0 + 14, 'LIVE', F35, ink)
        for yy in (y0 + 23, y0 + 27, y0 + 31):
            ink_line(x0 + 6, x1 - 7, yy, ink)
    elif kind == 'tabs':
        ink_line(x0 + 4, x1 - 5, y0 + 3, ink)
        ink_line(x0 + 4, x1 - 5, y0 + 4, ink)
        ink_line(x0 + 4, x1 - 9, y0 + 7, ink)
        ink_line(x0 + 2, x1 - 2, y0 + 11, DARK.get(paper, paper))
        for i, tx in enumerate(range(x0 + 3, x1 - 2, 4)):
            if hsh(i, x0, seed) < 0.35:
                for y in range(y0 + 12, y1 + 1):
                    for x in range(tx, tx + 3):
                        if (x, y) in m:
                            c.set(x, y, 'M')
            else:
                ink_line(tx + 1, tx + 1, y0 + 13, ink)
                for y in range(y0 + 13, y1 - 1):
                    if (tx + 1, y) in m:
                        c.set(tx + 1, y, ink)
    elif kind == 'sale':
        c.text(x0 + 10, y0 + 5, 'SALE', F35, 'R')
        c.rect(x0 + 5, y0 + 13, x1 - 6, y0 + 14, ink)
        ink_line(x0 + 5, x1 - 10, y0 + 18, ink)
        ink_line(x0 + 5, x1 - 8, y0 + 22, ink)
    if hsh(x0, y0, seed) < 0.5:
        c.rect(x0 + iw // 2 - 2, y0 - 1, x0 + iw // 2 + 2, y0 + 1, 'g')
    else:
        c.set(x0 + 4, y0 + 2, 'D')
        c.set(x0 + 5, y0 + 2, 'D')


def building_F(c):
    x0, x1 = 859, 1076
    top = 55
    bricks(c, x0, top, x1, WALL, 'B', 'M', hi='w', lo='M', seed=13)
    cornice(c, x0, x1, top - 9)
    # rooftop billboard frame (empty, peeling)
    c.rect(890, top - 40, 1044, top - 14, '6')
    for x in range(892, 1043, 6):
        c.vline(x, top - 38, top - 16, 'E' if hsh(x, 1, 2) > 0.3 else '6')
    c.box(890, top - 40, 1044, top - 14, 'K')
    for sx in (904, 966, 1030):
        c.vline(sx, top - 13, top - 10, 'K')
        c.line(sx, top - 13, sx + 6, top - 10, 'K')
    # torn paper strips hanging off the empty billboard
    for (px, ln) in ((930, 6), (951, 9), (988, 4), (1007, 7), (1018, 5)):
        c.rect(px, top - 16, px + 4, top - 16 + ln, 'F')
        c.vline(px + 4, top - 16, top - 16 + ln, 'D')
        c.set(px + 2, top - 15 + ln, 'K')
    # string courses
    for sy in (104, 152):
        c.rect(x0, sy, x1, sy + 3, 'E')
        c.hline(x0, x1, sy, 'D')
        c.hline(x0, x1, sy + 3, 'K')
        stain(c, x0, x1, sy + 4, 12, seed=sy + 5)
    # upper windows (centre bay left blank: stair column)
    for (wy, sts) in ((66, ['dark', 'blind', 'dark', 'cool']), (116, ['blind', 'dark', 'dark', 'dark'])):
        for (wx, st) in zip((876, 916, 1000, 1040), sts):
            window(c, wx, wy, wx + 22, wy + 30, st)
    # plinth
    c.rect(x0, 233, x1, WALL, 'E')
    c.hline(x0, x1, 233, 'K')
    c.hline(x0, x1, 234, 'D')
    # ghosts of old wheat-paste on the brick
    for (a, b, cc, d) in ((866, 176, 880, 210), (1056, 170, 1070, 214)):
        for y in range(b, d):
            for x in range(a, cc):
                if bayer(x, y) < 0.25 and c.get(x, y) == 'B':
                    c.set(x, y, 'w')
    # sconce light cone on the wall (before the paper goes up)
    cx = 968
    for y in range(157, 233):
        half = 8 + (y - 157) * 0.75
        for x in range(int(cx - half), int(cx + half) + 1):
            d = abs(x + 0.5 - cx) / half
            t = (1.0 - d) * (1.15 - (y - 157) / 110.0)
            if bayer(x, y) < t:
                k = c.get(x, y)
                if k in ('B', 'M', 'w'):
                    c.set(x, y, {'B': 'w', 'M': 'B', 'w': 'd'}[k])
    for i, f in enumerate(FLYERS):
        flyer(c, *f, seed=i * 7 + 1)
    # flyers away from the lamp sit in the dark
    for y in range(158, 233):
        for x in range(880, 1056):
            d = abs(x - cx) / 90.0 + max(0, y - 200) / 120.0
            if d > 0.55 and bayer(x, y) < (d - 0.55) * 1.6:
                k = c.get(x, y)
                if k in ('d', 'g', '8', 's', 'A', 'P', 'F', '9'):
                    c.set(x, y, DARK[k])
    if OPTS['poster']:
        street_poster(c)
    protect_rect(POSTER[0] - 2, POSTER[1] - 1, POSTER[2], POSTER[3])
    # the sconce
    c.rect(965, 132, 971, 136, 'E')
    c.box(965, 132, 971, 136, 'K')
    c.vline(968, 137, 146, 'K')
    c.vline(967, 139, 146, 'E')
    for i, y in enumerate(range(147, 154)):
        c.hline(964 - i, 972 + i, y, 'N' if i else 'K')
        c.set(964 - i, y, 'K')
        c.set(972 + i, y, 'K')
        if 0 < i < 5:
            c.set(966 - i + 1, y, 'I')
    c.hline(957, 979, 154, 'K')
    c.hline(960, 976, 155, 'Y')
    c.hline(964, 972, 155, 'W')
    c.hline(962, 974, 156, 'd')
    protect_rect(957, 154, 979, 156)
    c.vline(x1, top - 9, WALL, 'K')


def building_G(c):
    x0, x1 = 1077, 1279
    top = 119
    panels(c, x0, top, x1, WALL, 'N', 'K', 'I', pw=30)
    bricks(c, 1246, top, x1, WALL, 'B', 'M', hi='w', lo='M', seed=17)
    c.vline(1245, top, WALL, 'K')
    cornice(c, x0, x1 + 3, top - 9)
    # roof clutter
    c.rect(1150, top - 20, 1176, top - 10, 'D')
    c.box(1150, top - 20, 1176, top - 10, 'K')
    c.hline(1151, 1175, top - 19, 'g')
    for x in range(1154, 1173, 3):
        c.vline(x, top - 17, top - 12, 'E')
    for (vx, vh) in ((1210, 14), (1222, 9)):
        c.rect(vx, top - 9 - vh, vx + 3, top - 10, 'E')
        c.box(vx - 1, top - 10 - vh, vx + 4, top - 10, 'K')
    # round server-icon sign with a speech bubble
    cx, cy, r = 1101.5, 136.5, 12.5
    radial(c, cx, cy, 28, 24, {'N': 'I', 'I': 'V', 'K': 'N'}, 0.55, x0, x1, top, 151, protect=())
    m = ellipse_mask(cx, cy, r, r)
    c.mask(m, 'U')
    for (x, y) in m:
        if (x - cx) + (y - cy) > 7:
            c.set(x, y, 'I')
        elif (x - cx) + (y - cy) < -11:
            c.set(x, y, 'u')
    c.mask(boundary(m), 'K')
    bub = [
        ".WWWWWWWWW.",
        "WWWWWWWWWWW",
        "WWUUWUUWUUW",
        "WWWWWWWWWWW",
        ".WWWWWWWWW.",
        "..WW.......",
        ".W.........",
    ]
    c.stamp(bub, 1096, 131)
    c.ellipse(1111.5, 146.5, 3.5, 3.5, 'K')
    c.ellipse(1111.5, 146.5, 2.5, 2.5, '2')
    c.set(1110, 145, '1')
    # name board
    bx0, bx1, by0, by1 = 1120, 1270, 126, 147
    c.rect(bx0, by0, bx1, by1, 'N')
    c.box(bx0, by0, bx1, by1, 'K')
    c.hline(bx0 + 1, bx1 - 1, by0 + 1, 'I')
    txt = 'CHAT CAFE'
    tw = text_width(txt, F57, scale=2)
    c.text(bx0 + (bx1 - bx0 + 1 - tw) // 2, by0 + 4, txt, F57, 'U', scale=2, shadow=('I', 1, 1))
    # the second C has a dead tube
    c.recolor(bx0 + (bx1 - bx0 + 1 - tw) // 2 + 56, by0 + 4, bx0 + (bx1 - bx0 + 1 - tw) // 2 + 66, by0 + 17, {'U': 'I', 'I': 'N'})
    protect_rect(1089, 123, 1270, 151)
    awning(c, 1084, 1272, 152, 163, 'U', 'I', stripe=8)
    # window (closed: chairs up on the tables)
    wx0, wy0, wx1, wy1 = 1086, 174, 1196, 230
    c.rect(wx0, wy0, wx1, wy1, 'M')
    radial(c, 1170, 186, 40, 26, {'M': 'B', 'B': 'w'}, 0.9, wx0 + 1, wx1 - 1, wy0 + 1, wy1 - 1)
    for tx in (1098, 1136, 1172):
        c.rect(tx - 10, 212, tx + 10, 213, 'N')
        c.vline(tx, 214, wy1 - 1, 'N')
        c.hline(tx - 5, tx + 5, wy1 - 1, 'N')
        c.rect(tx - 6, 206, tx + 1, 211, 'N')
        c.vline(tx - 6, 196, 205, 'N')
        c.vline(tx + 1, 196, 205, 'N')
        c.vline(tx + 4, 202, 211, 'N')
    c.box(wx0, wy0, wx1, wy1, 'K')
    c.vline(1141, wy0, wy1, 'K')
    sx0, sy0 = 1152, 186
    c.line(sx0 + 4, sy0 - 1, sx0 + 13, sy0 - 9, 'K')
    c.line(sx0 + 22, sy0 - 1, sx0 + 13, sy0 - 9, 'K')
    c.rect(sx0, sy0, sx0 + 26, sy0 + 10, 'P')
    c.box(sx0, sy0, sx0 + 26, sy0 + 10, 'K')
    c.text(sx0 + 2, sy0 + 3, 'CLOSED', F35, 'R', spacing=1)
    for i in range(14):
        if i % 3:
            c.set(wx0 + 4 + i // 2, wy0 + 20 - i, 'I')
    c.rect(wx0, wy1 + 1, wx1, WALL, 'I')
    c.box(wx0, wy1 + 1, wx1, WALL, 'K')
    door(c, 1206, 172, 1236, WALL, glass='M', frame='I')


LIGHTS = [
    # cx, cy, rx, ry, intensity
    (380, 190, 84, 100, 0.70), (380, 268, 74, 22, 0.80),      # curb lamp 1 (post in street_fg)
    (862, 190, 84, 100, 0.70), (862, 268, 74, 22, 0.80),      # curb lamp 2
    (360, 72, 30, 52, 0.45),                                 # NOODLES blade sign
    (253, 200, 70, 46, 0.50), (262, 252, 74, 20, 0.50),       # noodle bar window
    (262, 160, 100, 18, 0.30),                               # awning catches the window light
    (531, 196, 104, 54, 0.55), (531, 254, 104, 22, 0.55),     # laundromat
    (672, 172, 36, 42, 0.60),                                # stoop bulb
    (780, 150, 84, 26, 0.35),                                # pawn sign
    (968, 196, 70, 84, 0.90), (968, 254, 64, 20, 0.80),       # poster sconce
    (1101, 137, 36, 32, 0.50), (1195, 137, 84, 22, 0.30),     # cafe signs
    (1180, 250, 90, 18, 0.30),
]
AMBIENT = 0.78


def darkness(x, y):
    d = AMBIENT
    if y < WALL:
        d += 0.18 * (1.0 - y / float(WALL))
    elif y >= ROAD:
        d += 0.08
    for (cx, cy, rx, ry, it) in LIGHTS:
        dx = (x + 0.5 - cx) / rx
        dy = (y + 0.5 - cy) / ry
        q = dx * dx + dy * dy
        if q < 1.0:
            d -= it * (1.0 - q)
    return d


def grade(c):
    for y in range(H):
        for x in range(W):
            k = c.p[y][x]
            if k is None or k == 'K' or (x, y) in PROT or k not in DARK:
                continue
            d = darkness(x, y)
            if d > 0.60 or (d > 0.46 and bayer(x, y) < (d - 0.46) / 0.14):
                c.p[y][x] = DARK[k]


def glows(c):
    """Coloured light that survives the grade: sign spill, puddles, wet-road streaks."""
    radial(c, 356, 70, 20, 44, {'6': 'M', 'E': 'V', 'D': '8'}, 0.8, 340, 372, 20, 140)
    radial(c, 531, 250, 96, 14, {'E': '7', 'D': 'g', '6': 'I'}, 0.55, 0, W - 1, SW0, SW1)
    radial(c, 262, 250, 60, 12, {'E': 'B', 'D': 'w', '6': 'M'}, 0.45, 0, W - 1, SW0, SW1)
    radial(c, 1160, 250, 100, 12, {'6': 'I', 'E': 'I', 'D': 'U'}, 0.45, 0, W - 1, SW0, SW1)
    radial(c, 1101.5, 137, 24, 20, {'N': 'I', 'I': 'V'}, 0.5, 1077, 1119, 119, 151, protect=('K', 'U', 'u', 'W', '2', '1'))
    for (x, wdt, col, s, dens) in ((360, 6, 'r', 1, 0.75), (380, 5, 'd', 2, 0.6), (531, 18, '7', 3, 0.6),
                                   (672, 3, 'A', 9, 0.5), (780, 10, 'A', 4, 0.45), (862, 5, 'd', 5, 0.6),
                                   (968, 7, 'd', 6, 0.4), (1101, 7, 'U', 7, 0.75), (1190, 14, 'I', 8, 0.5)):
        reflection(c, x, wdt, col, seed=s, dens=dens)
    # wet sidewalk: smeared reflections of the lit fronts
    for (x, wdt, col, s, dens) in ((253, 30, 'w', 11, 0.30), (531, 50, '7', 12, 0.35), (968, 14, 'g', 13, 0.30),
                                   (360, 4, 'r', 14, 0.45), (1101, 6, 'U', 15, 0.40), (672, 8, 'A', 16, 0.30)):
        reflection(c, x, wdt, col, y0=SW0 + 3, y1=SW1 - 2, seed=s, dens=dens)
    for (x, y, rx, ry, g, s) in ((140, 273, 26, 4, 'I', 1), (300, 268, 30, 4, 'r', 2), (566, 274, 34, 5, 'c', 3),
                                 (752, 266, 18, 3, 'A', 4), (906, 273, 22, 4, 'd', 5), (1178, 269, 30, 4, 'U', 6)):
        puddle(c, x, y, rx, ry, g, s)


def build():
    PROT.clear()
    c = Canvas(W, H)
    ground(c)
    building_A(c)
    building_B(c)
    building_C(c)
    building_D(c)
    building_E(c)
    building_F(c)
    building_G(c)
    grade(c)
    glows(c)
    return c


if __name__ == '__main__':
    c = build()
    c.save('out/street_buildings.png')
    c.crop(0, 0, 640, 360).save('view/street_left_2x.png', 2)
    c.crop(640, 0, 640, 360).save('view/street_right_2x.png', 2)
