from keys import *
from glyphs2 import BOLD
import keys

def body_variant(v):
    g = keycap_grid()
    if v >= 2:
        # round top-face top corners, add glint
        g[2][4] = 'M'
        g[3][5] = 'W'; g[3][6] = 'W'; g[4][5] = 'W'
        # front skirt: 4 mid rows, 2 dark rows
        for y in range(24, 30):
            for x in range(2, 30):
                if g[y][x] in 'DS' and g[y][x] != '#':
                    if y <= 27 and x < 25:
                        g[y][x] = 'D'
                    elif y <= 27:
                        g[y][x] = 'S'
                    elif x < 27:
                        g[y][x] = 'S'
    if v >= 3:
        # left skirt shading darker at the bottom
        for y in range(26, 30):
            for x in range(1, 4):
                if g[y][x] == 'M':
                    g[y][x] = 'D'
    return g

def make(glyph, body=1, body_w=None, dy=0):
    c = Canvas(32, 32)
    g = body_variant(body)
    c.grid(0, 0, [''.join(r) for r in g], COL)
    gh, gw = len(glyph), len(glyph[0])
    bw = body_w if body_w else gw
    x0 = int(round(15.5 - bw / 2 + 0.5))
    y0 = int(round(12.5 - gh / 2 + 0.5)) + dy
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == 'X':
                c.set(x0 + i, y0 + j, COL['g'])
    return c

items = []
# row 1: thin (current) on body 1
items += [make(GLYPHS['Q_a'], 1, 12), make(GLYPHS['W_c'], 1), make(GLYPHS['A_a'], 1), make(orient(GLYPHS['A_a'],'left'), 1)]
# row 2: bold on body 2
items += [make(BOLD['Q_bold1'], 2, 14), make(BOLD['W_bold1'], 2), make(BOLD['A_bold1'], 2), make(orient(BOLD['A_bold1'],'left'), 2)]
# row 3: bold alt on body 3
items += [make(BOLD['Q_bold2'], 3, 14), make(BOLD['W_bold2'], 3), make(BOLD['A_bold2'], 3), make(orient(BOLD['A_bold2'],'right'), 3)]
# row 4: more alts
items += [make(BOLD['Q_bold3'], 2, 13), make(BOLD['W_bold3'], 2), make(orient(BOLD['A_bold1'],'down'), 2), make(orient(BOLD['A_bold1'],'right'), 2)]
s = sheet(items, 4, pad=3)
for sc in (3, 6):
    W, H, px = composite_on(s, (69, 40, 60), sc)
    write_png(os.path.join(OUT, 'cmp2_%dx.png' % sc), W, H, px)
print('ok')
