"""Jordan's room - room_props: everything that sits on, hangs on or is pinned to
the furniture and the back wall. Figures and boxes on the shelves, the desk
top clutter, posters, the fairy lights, the hoodie on its peg.

Posters are parodies with no real logos or wordmarks: the princess of Jordan's
shirt, a promo sheet of the fight's four funkos, the server's mascot icon (the
house style: a white disc with the blurple face), a made-up space shooter, an
anime print and the speedy hedgehog.
"""
import math
import random

import numpy as np

from jr_lib import Canvas, W, H, IDX, KEYS, T, border, poly_mask, rect_mask, ellipse_mask, \
    bayer, from_rows, line_pts
from jr_geom import FLOOR_Y, DESK_TOP_Y, DESK_LIP_Y, PC_X0, PC_X1
from jr_furniture import outline, fill_shaded
import jr_furniture2 as F2
import jr_figures as F
from jr_track import Null, Tracker

TR = Null()        # set by build_props(track=True); only watches the canvas

# ---------------------------------------------------------------- tiny font (3x5)
FONT = {
    'A': ".X. X.X XXX X.X X.X", 'C': "XXX X.. X.. X.. XXX", 'E': "XXX X.. XX. X.. XXX",
    'I': "XXX .X. .X. .X. XXX", 'J': "..X ..X ..X X.X .X.", 'L': "X.. X.. X.. X.. XXX",
    'M': "X.X XXX XXX X.X X.X", 'N': "XX. X.X X.X X.X X.X", 'O': "XXX X.X X.X X.X XXX",
    'T': "XXX .X. .X. .X. .X.", 'P': "XXX X.X XXX X.. X..", 'S': "XXX X.. XXX ..X XXX",
    'G': "XXX X.. X.X X.X XXX", 'U': "X.X X.X X.X X.X XXX", '0': "XXX X.X X.X X.X XXX",
    '9': "XXX X.X XXX ..X XXX", '1': ".X. XX. .X. .X. XXX", '!': "X X X . X",
    ' ': "... ... ... ... ...",
}


def text(c, x, y, s, k):
    for ch in s:
        g = FONT[ch].split()
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == 'X':
                    c.set(x + i, y + j, k)
        x += len(g[0]) + 1
    return x


def text_w(s):
    return sum(len(FONT[ch].split()[0]) + 1 for ch in s) - 1


# ================================================================ helpers
def place(c, spr, x, feet_y):
    """Blit a sprite so its last row lands on feet_y."""
    c.blit(spr, x, feet_y - spr.h + 1)


def poster_frame(c, x0, y0, x1, y1, border_col='P', tape=True):
    c.box(x0, y0, x1, y1, 'K')
    c.box(x0 + 1, y0 + 1, x1 - 1, y1 - 1, border_col)
    c.hline(x0 + 1, x1 - 1, y0 + 1, 'W' if border_col in ('P', 'W') else border_col)
    if tape:
        for (tx, ty) in ((x0 - 1, y0 - 1), (x1 - 2, y0 - 1)):
            c.rect(tx, ty, tx + 3, ty + 2, 'g')
            c.set(tx, ty, 'P')


# ================================================================ posters
def poster_princess(c, x0, y0):
    """44x44: the princess from Jordan's shirt, bigger."""
    w = h = 44
    x1, y1 = x0 + w - 1, y0 + h - 1
    art = Canvas(40, 40)
    art.rect(0, 0, 39, 39, 'c')
    for (sx, sy) in ((4, 5), (33, 8), (7, 30), (35, 27), (26, 3)):
        art.set(sx, sy, 'W')
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            art.set(sx + dx, sy + dy, 'P')
    cx = 20
    # hair: a big blonde mass, long down behind the shoulders
    hair = ellipse_mask(cx, 17, 14, 13.5, 40, 40) | rect_mask(cx - 14, 17, cx + 13, 33, 40, 40)
    face = ellipse_mask(cx, 19.5, 8.2, 8.8, 40, 40)
    art.fill(hair, 'Y')
    hy, hx = np.nonzero(hair)
    for y, x in zip(hy, hx):
        if x > cx + 7 or y > 30:
            art.set(x, y, 'd')
        if (x < cx - 9 and y < 22 and (x + y) % 5 == 0):
            art.set(x, y, 'W')
    art.fill(face, 's')
    fy, fx = np.nonzero(face)
    for y, x in zip(fy, fx):
        if x >= cx + 5:
            art.set(x, y, 'd')
    # bangs over the forehead
    bangs = poly_mask([(cx - 9, 10), (cx + 9, 10), (cx + 8, 15), (cx + 4, 13), (cx + 1, 16),
                       (cx - 2, 13), (cx - 6, 16), (cx - 9, 14)], 40, 40)
    art.fill(bangs, 'Y')
    art.fill(border(bangs) & face, 'A')
    # crown
    crown = ["..Y..Y..Y..",
             ".YAY.YrY.YA",
             ".YYYYYYYYY.",
             ".YAUAYAUAY.",
             ".AAAAAAAAA."]
    art.stamp(crown, cx - 6, 1)
    # eyes: big and blue with a white catch-light
    for ex in (cx - 5, cx + 3):
        art.hline(ex - 1, ex + 2, 17, 'K')
        art.rect(ex, 18, ex + 1, 21, 'U')
        art.vline(ex - 1, 18, 21, 'K')
        art.set(ex, 18, 'W')
        art.hline(ex, ex + 1, 21, 'I')
    art.set(cx - 7, 23, 'r')
    art.set(cx + 6, 23, 'r')
    art.hline(cx - 1, cx, 25, 'R')
    # dress: pink shoulders, white collar, blue brooch
    dress = poly_mask([(cx - 13, 40), (cx - 12, 32), (cx - 6, 29), (cx + 6, 29), (cx + 12, 32),
                       (cx + 13, 40)], 40, 40)
    art.fill(dress, '8')
    dy, dx = np.nonzero(dress)
    for y, x in zip(dy, dx):
        if x > cx + 6:
            art.set(x, y, 'V')
        elif x < cx - 8 and y < 35:
            art.set(x, y, 'P')
    art.fill(poly_mask([(cx - 6, 29), (cx + 6, 29), (cx + 3, 33), (cx - 3, 33)], 40, 40), 'W')
    art.rect(cx - 1, 32, cx, 34, 'U')
    art.set(cx - 1, 32, 'u')
    # neck
    art.rect(cx - 2, 27, cx + 1, 28, 'd')
    # keyline round the figure against the backdrop
    fig = hair | face | dress | rect_mask(cx - 6, 0, cx + 5, 5, 40, 40)
    fig &= art.a != IDX['c']
    art.a[border(fig) & (art.a == IDX['c'])] = IDX['K']
    c.blit(art, x0 + 2, y0 + 2)
    poster_frame(c, x0, y0, x1, y1, 'P')


def poster_promo(c, x0, y0):
    """47x81: a promo sheet of the four funkos - COLLECT on a red band."""
    w, h = 47, 81
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 'I')
    rnd = random.Random(3)
    for _ in range(26):
        sx = rnd.randrange(x0 + 3, x1 - 2)
        sy = rnd.randrange(y0 + 14, y1 - 12)
        c.set(sx, sy, rnd.choice(('P', 'W', 'u')))
    # header
    c.rect(x0 + 2, y0 + 2, x1 - 2, y0 + 12, 'R')
    c.hline(x0 + 2, x1 - 2, y0 + 2, 'r')
    tw = text_w('COLLECT')
    text(c, x0 + (w - tw) // 2, y0 + 5, 'COLLECT', 'W')
    c.hline(x0 + 2, x1 - 2, y0 + 12, 'K')
    # the four, on little pedestals, two by two
    figs = [F.approved('plumber'), F.approved('hedgehog', flip=True), F.approved('mascot'),
            F.approved('gamer', flip=True)]
    for i, f in enumerate(figs):
        col, row = i % 2, i // 2
        cx = x0 + 12 + col * 22
        feet = y0 + 38 + row * 28
        c.ellipse(cx + 0.5, feet + 1.5, 9, 2.6, 'U')
        c.hline(cx - 7, cx + 8, feet + 3, 'K')
        place(c, f, cx - f.w // 2, feet + 1)
    # footer: gold star and fine print
    c.rect(x0 + 2, y1 - 12, x1 - 2, y1 - 2, 'R')
    c.hline(x0 + 2, x1 - 2, y1 - 12, 'K')
    star = ["..Y..", ".YYY.", "YYYYY", ".YYY.", ".Y.Y."]
    c.stamp(star, x0 + 5, y1 - 10)
    for k in range(3):
        c.hline(x0 + 13, x1 - 6 - k * 6, y1 - 9 + k * 2, 'r')
    poster_frame(c, x0, y0, x1, y1, 'Y')
    c.hline(x0 + 1, x1 - 1, y0 + 1, 'Y')


def poster_server(c, x0, y0):
    """27x51: the server's icon - a white disc with the blurple mascot face."""
    w, h = 27, 51
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 'U')
    for y in range(y0 + 2, y1 - 1):
        for x in range(x0 + 2, x1 - 1):
            if (x - y) % 6 == 0:
                c.set(x, y, 'u')
    cx, cy = x0 + w / 2.0, y0 + 19.5
    disc = ellipse_mask(cx, cy, 10.5, 10.5)
    c.fill(disc, 'W')
    c.fill(border(disc), 'K')
    dy_, dx_ = np.nonzero(disc)
    for y, x in zip(dy_, dx_):
        if x > cx + 6 and y > cy - 2:
            c.set(x, y, 'P')
    face = ["..UUUUUUUUU..",
            ".UUUUUUUUUUU.",
            "UUWWUUUUUWWUU",
            "UUWWUUUUUWWUU",
            "UUUUUUUUUUUUU",
            "UUUUKKKKKUUUU",
            "UUU.......UUU",
            ".U.........U."]
    c.stamp(face, int(cx) - 6, int(cy) - 4, {'K': 'U'})
    c.hline(int(cx) - 2, int(cx) + 2, int(cy) + 1, 'I')
    tw = text_w('JOIN')
    c.rect(x0 + 3, y0 + 34, x1 - 3, y0 + 42, 'N')
    text(c, x0 + (w - tw) // 2, y0 + 36, 'JOIN', 'W')
    for k in range(2):
        c.hline(x0 + 6, x1 - 6 - k * 4, y0 + 45 + k * 2, 'P')
    poster_frame(c, x0, y0, x1, y1, 'P')


def poster_shooter(c, x0, y0):
    """27x41: a made-up space shooter."""
    w, h = 27, 41
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 'N')
    rnd = random.Random(9)
    for _ in range(14):
        c.set(rnd.randrange(x0 + 3, x1 - 2), rnd.randrange(y0 + 3, y1 - 3), rnd.choice('PWg'))
    text(c, x0 + 3, y0 + 3, '0990', 'Y')
    bugs = [["K.K.K", ".KKK.", "K.K.K"],
            [".K.K.", "KKKKK", "K...K"],
            ["K...K", ".KKK.", ".K.K."]]
    cols = ['1', '8', 'Y']
    for r, (bug, col) in enumerate(zip(bugs, cols)):
        for k in range(3):
            c.stamp(bug, x0 + 4 + k * 7, y0 + 11 + r * 6, {'K': col})
    c.vline(x0 + 13, y0 + 26, y0 + 31, 'c')
    ship = ["..c..", ".cPc.", "cPPPc", "U.U.U"]
    c.stamp(ship, x0 + 11, y1 - 8)
    poster_frame(c, x0, y0, x1, y1, 'P')


def poster_anime(c, x0, y0):
    """24x47: a swordsman against a red sun."""
    w, h = 24, 47
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 's')
    c.fill(ellipse_mask(x0 + w / 2.0, y0 + 17, 8.5, 8.5), 'R')
    c.rect(x0 + 2, y1 - 9, x1 - 2, y1 - 2, 'R')
    c.hline(x0 + 2, x1 - 2, y1 - 9, 'B')
    fig = ["....KK....",
           "...KKKK...",
           "....KK..K.",
           "..KKKKKK..",
           ".K.KKKK.K.",
           "...KKKK..K",
           "...KKKK...",
           "..KK..KK..",
           "..K....K..",
           ".KK....KK."]
    c.stamp(fig, x0 + 7, y1 - 20)
    c.line(x0 + 16, y1 - 17, x0 + 20, y1 - 25, 'P')
    poster_frame(c, x0, y0, x1, y1, 'W')


def poster_hedgehog(c, x0, y0):
    """51x21: the speedy hedgehog over green hills."""
    w, h = 51, 21
    x1, y1 = x0 + w - 1, y0 + h - 1
    c.rect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 'u')
    for (hx, r) in ((x0 + 10, 9), (x0 + 30, 11), (x0 + 46, 8)):
        m = ellipse_mask(hx, y1 + 2, r, 9) & rect_mask(x0 + 2, y0 + 2, x1 - 2, y1 - 2)
        c.fill(m, '2')
        c.fill(border(m) & rect_mask(x0 + 2, y0 + 2, x1 - 2, y1 - 2) & ~m, '3')
    for k in range(6):
        c.hline(x0 + 4 + k * 2, x0 + 12 + k * 2, y0 + 6 + k * 2, 'P')
    hedge = F.approved('hedgehog', flip=True)
    place(c, hedge, x0 + 20, y1 - 3)
    for rx in (x0 + 38, x0 + 43):
        c.ellipse(rx + 0.5, y0 + 8.5, 2, 2, 'Y')
        c.set(rx, y0 + 8, 'u')
    poster_frame(c, x0, y0, x1, y1, 'P')


# ================================================================ shelf contents
def cube_contents(c):
    rnd = random.Random(4)
    cast_i = 0
    plan = {
        (0, 0): 'boxes2', (1, 0): 'fig', (2, 0): 'spines', (3, 0): 'boxes2', (4, 0): 'fig2',
        (0, 1): 'fig', (1, 1): 'chase', (2, 1): 'boxes2', (3, 1): 'figurine', (4, 1): 'spines',
        (0, 2): 'chase', (1, 2): 'spines', (2, 2): 'fig2', (3, 2): 'console', (4, 2): 'boxes2',
        (0, 3): 'plush', (1, 3): 'boxes2', (2, 3): 'fig', (3, 3): 'spines', (4, 3): 'chase',
    }
    box_cols = [(('r', 'R', 'B'), ('Y', 'A', '5')), (('u', 'U', 'I'), ('W', 'g', 'F')),
                (('1', '2', '3'), ('W', 'g', 'F')), (('8', 'V', 'M'), ('W', 'P', 'g')),
                (('E', '6', 'N'), ('Y', 'A', '5')), (('d', 'O', 'w'), ('W', 'g', 'F'))]
    for (i, j, x0, y0, x1, y1) in F2.cube_rects():
        kind = plan[(i, j)]
        floor = y1 - 1
        TR.begin('cube_%d_%d' % (i, j), group='cube_%d_%d' % (i, j))
        if kind == 'fig':
            f = F.cast_figure(cast_i)
            cast_i += 1
            place(c, f, x0 + (16 - f.w) // 2, floor)
        elif kind == 'fig2':
            a, b = F.cast_figure(cast_i), F.cast_figure(cast_i + 1)
            cast_i += 2
            place(c, a, x0 - 2, floor)
            place(c, b, x0 + 16 - b.w + 2, floor)
        elif kind == 'boxes2':
            (t1, s1) = box_cols[rnd.randrange(len(box_cols))]
            (t2, s2) = box_cols[rnd.randrange(len(box_cols))]
            b1 = F.collector_box(F.cast_figure(cast_i), top=t1, side=s1)
            b2 = F.collector_box(F.cast_figure(cast_i + 1), top=t2, side=s2)
            cast_i += 2
            place(c, b2, x0 + 6, floor - 1)
            place(c, b1, x0 - 1, floor)
        elif kind == 'chase':
            b = F.collector_box(F.approved(['plumber', 'hedgehog', 'gamer'][rnd.randrange(3)]))
            place(c, b, x0 + 3, floor)
        elif kind == 'spines':
            s = F.spines(16, 13, seed=i * 7 + j)
            place(c, s, x0, floor)
        elif kind == 'figurine':
            f = F.figurine('mech')
            place(c, f, x0 + (16 - f.w) // 2, floor)
        elif kind == 'console':
            con = ["KKKKKKKKKKKKKK",
                   "KFFFFFFFFFFFFK",
                   "KgggggggggggFK",
                   "KgKKKKKgRRgUFK",
                   "KgggggggggggFK",
                   "KKKKKKKKKKKKKK",
                   ".KNK......KNK."]
            c.stamp(con, x0 + 1, floor - 6)
            c.stamp(["KKKKKK", "KEcE8K", "KKKKKK"], x0 + 4, floor - 9)
        elif kind == 'plush':
            place(c, F.plush('mascot'), x0 + 2, floor)
        TR.end()
    # low things on top of the cube shelf
    top = F2.K_TOP + 4
    TR.begin('cubetop_games')
    for k, (col, hi) in enumerate((('R', 'r'), ('7', 'c'), ('2', '1'), ('E', 'F'))):
        y = top - k * 3
        c.rect(F2.KX0 + 6, y, F2.KX0 + 22, y + 2, col)
        c.hline(F2.KX0 + 6, F2.KX0 + 22, y, hi)
        c.box(F2.KX0 + 5, y - 1, F2.KX0 + 23, y + 3, 'K')
    TR.end()
    TR.begin('cubetop_mascot')
    place(c, F.approved('mascot'), F2.KX0 + 30, F2.K_TOP + 6)
    TR.end()
    TR.begin('cubetop_crown')
    place(c, F.cast_figure(12), F2.KX0 + 46, F2.K_TOP + 6)
    TR.end()
    TR.begin('cubetop_plush')
    place(c, F.plush('hedgehog'), F2.KX0 + 62, F2.K_TOP + 7)
    TR.end()
    TR.begin('cubetop_ears')
    place(c, F.cast_figure(6, flip=True), F2.KX1 - 14, F2.K_TOP + 6)
    TR.end()


def cabinet_contents(c):
    items = [
        [F.figurine('hero'), F.figurine('critter')],
        [F.figurine('dragon')],
        [F.figurine('knight'), F.approved('hedgehog', flip=True)],
        [F.figurine('slime'), F.approved('plumber')],
    ]
    for si, (sy, row) in enumerate(zip(F2.G_SHELVES, items)):
        total = sum(f.w for f in row)
        gap = max(0, (F2.GX1 - F2.GX0 - 3 - total) // (len(row) + 1))
        x = F2.GX0 + 2 + gap
        for fi, f in enumerate(row):
            TR.begin('cabinet_%d_%d' % (si, fi))
            place(c, f, x, sy - 1)
            TR.end()
            x += f.w + gap
    # the glass is in front of them: shelves' edges and glare over the figures
    TR.begin('cabinet_glass', thin=True, attach=True)
    F2.draw_cabinet_glass(c)
    TR.end()
    # a boxed statue standing on top of the cabinet
    TR.begin('cabinet_top')
    big = collector_like(20, 26, ('U', 'I', 'N'), F.figurine('hero'))
    place(c, big, F2.GX0 + 8, F2.G_TOP + 6)
    TR.end()


def bookcase_contents(c):
    b = F2.BC_BOARDS
    x0 = F2.BCX0
    TR.begin('books_manga')
    s = F.spines(F2.BCX1 - F2.BCX0 - 6, 20, seed=41)
    place(c, s, x0 + 3, b[1] - 1)
    TR.end()
    for k in range(5):
        TR.begin('books_box_%d' % k)
        bx = F.collector_box(F.cast_figure(10 + k),
                             top=[('r', 'R', 'B'), ('u', 'U', 'I'), ('8', 'V', 'M'),
                                  ('1', '2', '3'), ('d', 'O', 'w')][k])
        place(c, bx, x0 + 4 + k * 12, b[2] - 1)
        TR.end()
    TR.begin('books_cases')
    s2 = F.spines(28, 16, seed=77, palette=['W', 'R', 'U', 'E', 'P', '2'])
    place(c, s2, x0 + 3, b[3] - 1)
    TR.end()
    TR.begin('books_fig_a')
    f = F.cast_figure(3)
    place(c, f, x0 + 34, b[3] - 1)
    TR.end()
    TR.begin('books_fig_b')
    f2 = F.cast_figure(7, flip=True)
    place(c, f2, x0 + 48, b[3] - 1)
    TR.end()
    TR.begin('books_boardgames')
    for k, (col, hi) in enumerate((('R', 'r'), ('U', 'u'), ('2', '1'), ('Y', 'W'))):
        y = b[4] - 6 - k * 5
        c.rect(x0 + 4, y, x0 + 32 - k * 2, y + 3, col)
        c.hline(x0 + 4, x0 + 32 - k * 2, y, hi)
        c.hline(x0 + 8, x0 + 16, y + 2, 'W' if col != 'Y' else 'B')
        c.box(x0 + 3, y - 1, x0 + 33 - k * 2, y + 4, 'K')
    TR.end()
    TR.begin('books_plush')
    place(c, F.plush('mascot'), x0 + 42, b[4] - 1)
    TR.end()
    # on top: a trophy and a very dead plant
    TR.begin('books_trophy')
    trophy = [".KKKKK.", "KYYYYAK", "KYYYAK.", ".KYAK..", "..KAK..", ".KKKKK.", ".KAAAK.",
              ".KKKKK."]
    c.stamp(trophy, x0 + 8, F2.BC_TOP - 3)
    TR.end()
    TR.begin('books_plant')
    plant = ["..5.9.", ".5.95.", "..55..", ".KKKK.", "KwwwwK", ".KwwK.", ".KKKK."]
    c.stamp(plant, x0 + 50, F2.BC_TOP - 2)
    TR.end()
    TR.begin('books_topgames')
    for k, (col, hi) in enumerate((('7', 'c'), ('8', 'P'))):
        y = F2.BC_TOP + 2 - k * 3
        c.rect(x0 + 22, y, x0 + 40, y + 2, col)
        c.hline(x0 + 22, x0 + 40, y, hi)
        c.box(x0 + 21, y - 1, x0 + 41, y + 3, 'K')
    TR.end()


def collector_like(w, h, cols, inner):
    """A bigger window box for a statue."""
    c = Canvas(w, h)
    hi, base, lo = cols
    c.rect(0, 0, w - 1, h - 1, base)
    c.rect(0, 0, w - 1, 4, hi)
    c.rect(3, 6, w - 4, h - 4, 'N')
    if inner is not None:
        ox = 3 + (w - 6 - inner.w) // 2
        oy = h - 4 - inner.h
        for y in range(inner.h):
            for x in range(inner.w):
                v = inner.a[y, x]
                X, Y = ox + x, oy + y
                if v != T and 3 <= X <= w - 4 and 6 <= Y <= h - 4:
                    c.a[Y, X] = v
    c.box(0, 0, w - 1, h - 1, 'K')
    c.hline(0, w - 1, 5, 'K')
    c.box(2, 5, w - 3, h - 3, 'K')
    c.vline(w - 5, 7, h - 6, 'P')
    c.set(w - 6, 7, 'W')
    c.hline(2, w - 3, h - 2, lo)
    c.set(w // 2, 2, 'Y')
    c.set(w // 2 - 1, 2, 'Y')
    return c


def shelf_figures(c):
    """Funkos crowding the floating shelves."""
    sh = F2.WALL_SHELVES
    # above the desk, lower board: a row of figures
    x0, x1, y = sh[0]
    x = x0 + 3
    i = 0
    while x < x1 - 12:
        f = F.cast_figure(i + 5)
        TR.begin('shelfA_%d' % i)
        place(c, f, x, y - 1)
        TR.end()
        x += f.w - 1
        i += 1
    # upper board: the four stars of the collection in their chase boxes, flanked
    x0, x1, y = sh[1]
    names = ['plumber', 'hedgehog', 'mascot', 'gamer']
    bx = x0 + 32
    for k, n in enumerate(names):
        TR.begin('shelfB_box_%s' % n)
        place(c, F.collector_box(F.approved(n)), bx + k * 14, y - 1)
        TR.end()
    for k, xx in enumerate((x0 + 3, x0 + 16, x1 - 30, x1 - 16)):
        TR.begin('shelfB_fig_%d' % k)
        place(c, F.cast_figure(15 + k, flip=bool(k & 1)), xx, y - 1)
        TR.end()
    # over the door
    x0, x1, y = sh[2]
    x = x0 + 2
    for k in range(6):
        f = F.cast_figure(20 + k)
        TR.begin('shelfdoor_%d' % k)
        place(c, f, x, y - 1)
        TR.end()
        x += f.w - 1
    # the shrine: boxes and figures, three boards
    for bi, (x0, x1, y) in enumerate(sh[3:6]):
        x = x0 + 2
        k = 0
        while x < x1 - 10:
            if (k + bi) % 3 == 0:
                tops = [('r', 'R', 'B'), ('u', 'U', 'I'), ('8', 'V', 'M'), ('E', '6', 'N')]
                spr = F.collector_box(F.cast_figure(bi * 7 + k), top=tops[(k + bi) % 4],
                                      side=('W', 'g', 'F') if k % 2 else ('Y', 'A', '5'))
            else:
                spr = F.cast_figure(bi * 7 + k + 2, flip=bool(k & 1))
            TR.begin('shrine_%d_%d' % (bi, k))
            place(c, spr, x, y - 1)
            TR.end()
            x += spr.w - (1 if spr.w > 12 else 0)
            k += 1


# ================================================================ desk top
def desk_items(c):
    top, lip = DESK_TOP_Y, DESK_LIP_Y             # 114, 132
    # desk mat with an RGB edge
    mx0, mx1, my0, my1 = 362, 462, 121, 130
    TR.begin('desk_mat')
    c.rect(mx0, my0, mx1, my1, 'M')
    c.box(mx0, my0, mx1, my1, 'V')
    c.hline(mx0 + 1, mx1 - 1, my1, '8')
    for x in range(mx0 + 1, mx1):
        if (x + my0) % 7 == 0:
            c.set(x, my0, '8')
    TR.end()
    # keyboard with an RGB wash across its keys
    TR.begin('desk_keyboard')
    kx0, ky0 = 390, 123
    c.rect(kx0, ky0, kx0 + 32, ky0 + 5, 'N')
    for x in range(kx0 + 1, kx0 + 32):
        col = ['8', 'V', 'U', 'c', 'U', 'V'][((x - kx0) // 6) % 6]
        for yy in (ky0 + 1, ky0 + 3):
            c.set(x, yy, col if (x + yy) % 2 == 0 else 'E')
    c.hline(kx0 + 8, kx0 + 22, ky0 + 4, 'E')
    c.box(kx0 - 1, ky0 - 1, kx0 + 33, ky0 + 6, 'K')
    TR.end()
    # mouse
    TR.begin('desk_mouse')
    c.rect(432, 124, 435, 128, 'E')
    c.set(432, 124, 'F')
    c.set(433, 125, 'c')
    c.box(431, 123, 436, 129, 'K')
    TR.end()
    # energy drinks standing at the back, one crushed on the mat
    for (x, col, hi) in ((345, '2', '1'), (349, 'U', 'u'), (470, '8', 'P'), (474, '2', '1')):
        TR.begin('desk_can_%d' % x)
        c.rect(x, top + 1, x + 2, top + 7, col)
        c.vline(x, top + 2, top + 6, hi)
        c.hline(x, x + 2, top + 1, 'g')
        c.box(x - 1, top, x + 3, top + 8, 'K')
        TR.end()
    TR.begin('desk_crushed')
    c.rect(452, 126, 457, 128, 'R')
    c.hline(452, 457, 126, 'r')
    c.box(451, 125, 458, 129, 'K')
    TR.end()
    # cup noodles with a fork
    TR.begin('desk_noodles')
    c.rect(344, top + 11, 349, top + 16, 'P')
    c.hline(344, 349, top + 13, 'R')
    c.vline(344, top + 11, top + 16, 'W')
    c.box(343, top + 10, 350, top + 17, 'K')
    c.line(348, top + 7, 350, top + 10, 'g')
    TR.end()
    # controller on the mat
    TR.begin('desk_controller')
    ctl = ["..KKKKKKKK..",
           ".KEEEEEEEEK.",
           "KEKEEEEcEEEK",
           "KKKEEEE8rEEK",
           "KEEKKKKKKEEK",
           ".KK......KK."]
    c.stamp(ctl, 438, 124)
    TR.end()
    # a mug
    TR.begin('desk_mug')
    c.rect(464, top + 10, 468, top + 15, 'W')
    c.vline(464, top + 10, top + 15, 'P')
    c.vline(468, top + 11, top + 15, 'g')
    c.box(463, top + 9, 469, top + 16, 'K')
    for (dx, dy) in ((6, 11), (6, 12), (7, 11)):
        c.set(463 + dx, top + dy, 'K')
    TR.end()
    # sticky notes on the chat screen's bezel, papers by the keyboard
    TR.begin('desk_sticky')
    c.rect(377, 94, 380, 97, 'Y')
    c.box(376, 93, 381, 98, 'K')
    TR.end()
    TR.begin('desk_papers')
    c.rect(364, 122, 372, 128, 'P')
    c.line(365, 124, 370, 124, 'g')
    c.line(365, 126, 369, 126, 'g')
    c.box(363, 121, 373, 129, 'K')
    TR.end()
    # the gamer funko as a desk buddy
    TR.begin('desk_buddy')
    place(c, F.approved('gamer', flip=True), 446, top + 8)
    TR.end()
    # mic on a boom arm clamped at the right end
    TR.begin('desk_mic')
    arm = [(478, top + 2), (478, 100), (466, 92), (452, 92)]
    for (a, b) in zip(arm, arm[1:]):
        c.line(a[0], a[1], b[0], b[1], 'K')
        c.line(a[0] + 1, a[1], b[0] + 1, b[1], 'E')
    c.rect(445, 90, 449, 98, 'D')
    c.vline(445, 90, 98, 'F')
    c.box(444, 89, 450, 99, 'K')
    for yy in (92, 94, 96):
        c.hline(446, 448, yy, 'E')
    c.rect(476, top + 1, 480, top + 3, 'E')
    c.box(475, top, 481, top + 4, 'K')
    TR.end()
    # on top of the PC: a can and a tiny plush
    TR.begin('pc_can')
    c.rect(PC_X0 + 3, FLOOR_Y - 42, PC_X0 + 5, FLOOR_Y - 36, 'Y')
    c.vline(PC_X0 + 3, FLOOR_Y - 41, FLOOR_Y - 37, 'W')
    c.box(PC_X0 + 2, FLOOR_Y - 43, PC_X0 + 6, FLOOR_Y - 35, 'K')
    TR.end()
    TR.begin('pc_slime')
    place(c, F.figurine('slime'), PC_X0 + 9, FLOOR_Y - 36)
    TR.end()


# ================================================================ wall hangings
def fairy_lights(c):
    """A string of bulbs swagged along the top of the left half of the wall."""
    anchors = [(12, 12), (108, 12), (206, 12), (336, 14)]
    bulbs = ['Y', 'O', '8', 'c', '1']
    bi = 0
    for si, (a, b) in enumerate(zip(anchors, anchors[1:])):
        TR.begin('lights_%d' % si, thin=True)
        (ax, ay), (bx, by_) = a, b
        n = bx - ax
        pts = []
        for i in range(n + 1):
            t = i / n
            sag = 11 * 4 * t * (1 - t)
            pts.append((ax + i, int(round(ay + (by_ - ay) * t + sag))))
        for (p, q) in zip(pts, pts[1:]):
            for (x, y) in line_pts(p[0], p[1], q[0], q[1]):
                c.set(x, y, 'K')
        for i in range(4, n - 2, 9):
            x, y = pts[i]
            col = bulbs[bi % len(bulbs)]
            bi += 1
            c.set(x, y + 1, 'E')
            c.set(x, y + 2, col)
            c.set(x, y + 3, col)
            c.set(x - 1, y + 2, 'K')
            c.set(x + 1, y + 2, 'K')
            c.set(x - 1, y + 3, 'K')
            c.set(x + 1, y + 3, 'K')
            c.set(x, y + 4, 'K')
            # a small halo on the wall
            for (dx, dy) in ((-2, 2), (2, 2), (-2, 3), (2, 3), (0, 5), (-1, 5), (1, 5)):
                if c.get(x + dx, y + dy) is None and bayer(x + dx, y + dy) < 0.5:
                    c.set(x + dx, y + dy, {'Y': 'A', 'O': 'w', '8': 'V', 'c': '7', '1': '3'}[col])
        TR.end()


def hoodie_and_bag(c):
    """A grey hoodie hung by its hood and a red backpack on the coat rail pegs."""
    hoodie = ["........KK.........",
              ".......KgFK........",
              "......KgFFFK.......",
              ".....KgFFFFDK......",
              "....KgFFFFFFDK.....",
              "....KgFFKFFFDK.....",
              "....KFgFKFFFDK.....",
              "...KKFFgKFFFDKK....",
              "..KgFFFFFFFFFFDK...",
              ".KgFFFFFFFFFFFFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFDKFDK..",
              ".KgFKFFFFFFFDKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KgFKFFFFFFFFKFDK..",
              ".KEEKFFFFFFFFKEEK..",
              ".KKKKFFFFFFFFKKKK..",
              "....KgFFFFFFFDK....",
              "....KDDDDDDDDDK....",
              "....KKKKKKKKKKK...."]
    TR.begin('hoodie')
    c.stamp(hoodie, 10, 75)
    TR.end()
    bag = ["....KKKKK.....",
           "...KK...KK....",
           "..KKKKKKKKK...",
           ".KrrRRRRRRBK..",
           "KrrRRRRRRRRBK.",
           "KrRRRRRRRRRBK.",
           "KrRKKKKKKKRBK.",
           "KrRRRRRRRRRBK.",
           "KrRKKKKKKKRBK.",
           "KrRKrRRRRKRBK.",
           "KrRKrRYRRKRBK.",
           "KrRKRRRRRKRBK.",
           "KrRKKKKKKKRBK.",
           "KrRRRRRRRRRBK.",
           "KBBBBBBBBBBBK.",
           ".KKKKKKKKKKK.."]
    TR.begin('backpack')
    c.stamp(bag, 25, 76)
    TR.end()


# ================================================================ assemble
POSTERS = [
    (poster_anime, 13, 16),
    (poster_princess, 132, 14),
    (poster_promo, 208, 25),
    (poster_shooter, 485, 14),
    (poster_server, 485, 60),
    (poster_hedgehog, 568, 10),
]


def build_props(furniture_bits=None, track=False):
    """room_props. With track=True it also returns the Tracker that watched it being
    drawn (for the crumble pieces); the pixels are the same either way."""
    global TR
    c = Canvas()
    TR = Tracker(c) if track else Null()
    try:
        for (fn, x, y) in POSTERS:
            TR.begin(fn.__name__)
            fn(c, x, y)
            TR.end()
        fairy_lights(c)
        hoodie_and_bag(c)
        cube_contents(c)
        cabinet_contents(c)
        bookcase_contents(c)
        shelf_figures(c)
        desk_items(c)
        # what's in the open carton: a collector box and packing peanuts
        TR.begin('carton_box')
        g = F2.carton_geom()
        (ox0, ox1, oyt, odp, oht, _) = g[2]
        b = F.collector_box(F.cast_figure(4), top=('u', 'U', 'I'), side=('W', 'g', 'F'))
        place(c, b, ox0 + 8, oyt + odp)
        for (px, py) in ((ox0 + 3, oyt + 3), (ox0 + 5, oyt + 2), (ox1 - 12, oyt + 3),
                         (ox1 - 8, oyt + 4), (ox1 - 5, oyt + 2), (ox0 + 22, oyt + 3)):
            c.set(px, py, 'W')
            c.set(px + 1, py, 'P')
        TR.end()
    finally:
        tracker, TR = TR, Null()
    return (c, tracker) if track else c
