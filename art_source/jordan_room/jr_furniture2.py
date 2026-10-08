"""Jordan's room - room_furniture, part 2: cube shelf, glass cabinet, bookcase,
floating shelves, shipping cartons, bin, coat rail.

Everything stands against (or hangs on) the back wall and is complete without
its contents, which are drawn in jr_props.
"""
import numpy as np

from jr_lib import Canvas, W, H, IDX, KEYS, T, DARKER, border, poly_mask, rect_mask, \
    ellipse_mask, bayer
from jr_geom import FLOOR_Y
from jr_furniture import shade_under, outline, fill_shaded

# ================================================================ cube shelf
KX0, KX1 = 110, 201
K_TOP, K_FRONT, K_BASE = 76, 87, 160          # top surface / front face / front bottom row


def cube_rects():
    """(col, row, x0, y0, x1, y1) of each open cube's inside."""
    out = []
    for j in range(4):
        for i in range(5):
            x0 = KX0 + 2 + i * 18
            y0 = K_FRONT + 2 + j * 18
            out.append((i, j, x0, y0, x0 + 15, y0 + 15))
    return out


LIT_CUBES = {(1, 1), (3, 0), (0, 2), (4, 3)}          # cubes with a puck light


def cube_shelf(under):
    c = Canvas()
    shade_under(c, under, rect_mask(KX0 - 1, K_BASE + 1, KX1 + 2, K_BASE + 2), 1)
    shade_under(c, under, rect_mask(KX1 + 1, K_FRONT, KX1 + 3, K_BASE), 1, 0.5)
    c.rect(KX0, K_TOP, KX1, K_FRONT - 1, 'P')             # top surface
    c.hline(KX0, KX1, K_TOP, 'W')
    c.rect(KX0, K_FRONT, KX1, K_BASE, 'g')
    for (i, j, x0, y0, x1, y1) in cube_rects():
        # the wall seen through the open back, in the cube's shade
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                v = under.a[y, x]
                k = KEYS[v] if v != T else 'N'
                k = DARKER[DARKER[k]]
                c.a[y, x] = IDX[k if k != 'K' else 'N']
        if (i, j) in LIT_CUBES:
            for y in range(y0, y1 - 2):
                for x in range(x0, x1 + 1):
                    d = ((x - (x0 + x1) / 2) / 9) ** 2 + ((y - y0) / 12) ** 2
                    if d < 1 and bayer(x, y) < (1 - d) * 0.9:
                        c.set(x, y, 'I')
        c.hline(x0, x1, y1 - 1, 'F')                      # the cube's floor, from above
        c.hline(x0, x1, y1, 'g')
        c.hline(x0, x1, y0, 'K')                          # shade under the board above
        if (i, j) in LIT_CUBES:
            c.hline(x0 + 5, x1 - 5, y0, 'W')              # the puck light itself
    for j in range(5):
        y = K_FRONT + j * 18
        c.hline(KX0, KX1, y, 'P')
        c.hline(KX0, KX1, y + 1, 'g')
    for i in range(6):
        x = KX0 + i * 18
        c.vline(x, K_FRONT, K_BASE, 'g')
        c.vline(x + 1, K_FRONT, K_BASE, 'F')
    c.hline(KX0, KX1, K_BASE, 'F')
    outline(c, rect_mask(KX0, K_TOP, KX1, K_BASE))
    c.hline(KX0, KX1, K_FRONT - 1, 'F')
    c.hline(KX0, KX1, K_FRONT, 'W')
    return c


# ================================================================ glass cabinet
GX0, GX1 = 518, 554
G_TOP, G_FRONT, G_BASE = 40, 51, 160
G_SHELVES = [G_FRONT + 26, G_FRONT + 52, G_FRONT + 78, G_BASE - 1]
G_GLARE = ((GX0 + 6, G_FRONT + 34, 10), (GX0 + 9, G_FRONT + 34, 5),
           (GX0 + 24, G_FRONT + 88, 12), (GX0 + 27, G_FRONT + 90, 6))


def glass_cabinet(under):
    c = Canvas()
    shade_under(c, under, rect_mask(GX0 - 1, G_BASE + 1, GX1 + 2, G_BASE + 2), 1)
    c.rect(GX0, G_TOP, GX1, G_FRONT - 1, 'E')
    c.hline(GX0, GX1, G_TOP, 'F')
    # the LED in the top, lighting the back wall through the glass
    for y in range(G_FRONT + 1, G_BASE - 1):
        for x in range(GX0 + 2, GX1 - 1):
            d = (y - G_FRONT) / 34.0
            if d < 1 and bayer(x, y) < (1 - d) * 0.55:
                v = under.a[y, x]
                k = KEYS[v] if v != T else 'N'
                c.set(x, y, {'N': 'I', 'I': 'U', 'U': 'u', 'K': 'N'}.get(k, k))
    c.hline(GX0 + 3, GX1 - 3, G_FRONT + 1, 'W')
    c.hline(GX0 + 2, GX1 - 2, G_FRONT + 2, 'P')
    draw_cabinet_glass(c)
    c.rect(GX0, G_FRONT, GX0 + 1, G_BASE, 'E')
    c.rect(GX1 - 1, G_FRONT, GX1, G_BASE, 'N')
    c.vline(GX0, G_FRONT, G_BASE, 'F')
    c.rect(GX0, G_BASE - 1, GX1, G_BASE, 'N')
    c.hline(GX0, GX1, G_FRONT, 'D')
    outline(c, rect_mask(GX0, G_TOP, GX1, G_BASE))
    c.hline(GX0, GX1, G_FRONT - 1, 'K')
    return c


def draw_cabinet_glass(c):
    """Glass shelves and glare; also redrawn over the figurines in room_props."""
    for sy in G_SHELVES:
        c.hline(GX0 + 1, GX1 - 1, sy, 'P')
        c.hline(GX0 + 1, GX1 - 1, sy + 1, 'g' if sy < G_BASE - 1 else 'E')
    for (gx, gy, ln) in G_GLARE:
        for k in range(ln):
            c.set(gx + k // 2, gy - k, 'P' if k % 3 else 'W')


# ================================================================ bookcase
BCX0, BCX1 = 560, 626
BC_TOP, BC_FRONT, BC_BASE = 40, 51, 160
BC_BOARDS = [BC_FRONT, BC_FRONT + 27, BC_FRONT + 54, BC_FRONT + 81, BC_BASE - 1]


def bookcase(under):
    c = Canvas()
    shade_under(c, under, rect_mask(BCX0 - 2, BC_BASE + 1, BCX1, BC_BASE + 2), 1)
    shade_under(c, under, rect_mask(BCX0 - 3, BC_FRONT, BCX0 - 1, BC_BASE), 1, 0.5)
    c.rect(BCX0, BC_TOP, BCX1, BC_FRONT - 1, 'w')
    c.hline(BCX0, BCX1, BC_TOP, 'd')
    c.rect(BCX0, BC_FRONT, BCX1, BC_BASE, 'B')
    for a, b in zip(BC_BOARDS, BC_BOARDS[1:]):
        y0, y1 = a + 2, b - 1
        for y in range(y0, y1 + 1):
            for x in range(BCX0 + 3, BCX1 - 2):
                c.a[y, x] = IDX['M'] if (y - y0) > 1 else IDX['K']
        c.hline(BCX0 + 3, BCX1 - 3, y1, 'B')
    for yb in BC_BOARDS:
        c.hline(BCX0, BCX1, yb, 'd')
        c.hline(BCX0, BCX1, yb + 1, 'w')
    c.rect(BCX0, BC_FRONT, BCX0 + 2, BC_BASE, 'w')
    c.vline(BCX0, BC_FRONT, BC_BASE, 'd')
    c.rect(BCX1 - 2, BC_FRONT, BCX1, BC_BASE, 'B')
    c.vline(BCX1, BC_FRONT, BC_BASE, 'M')
    outline(c, rect_mask(BCX0, BC_TOP, BCX1, BC_BASE))
    c.hline(BCX0, BCX1, BC_FRONT - 1, 'K')
    return c


# ================================================================ floating shelves
# (x0, x1, y): y is the board's top row; things stand with their feet on y - 1
WALL_SHELVES = [
    (350, 472, 78), (350, 472, 54),           # above the desk
    (34, 110, 30),                            # over the door
    (262, 334, 60), (262, 334, 86), (262, 334, 112),   # the shrine
]


def wall_shelves():
    c = Canvas()
    for (x0, x1, y) in WALL_SHELVES:
        # shadow the board throws on the wall
        c.hline(x0 + 1, x1 + 1, y + 3, 'N')
        c.rect(x0, y, x1, y + 2, 'B')
        c.hline(x0, x1, y, 'd')
        c.hline(x0, x1, y + 1, 'w')
        c.box(x0 - 1, y - 1, x1 + 1, y + 3, 'K')
        # little brackets at the ends
        for bx in (x0 + 4, x1 - 5):
            c.rect(bx, y + 3, bx + 1, y + 5, 'E')
            c.box(bx - 1, y + 3, bx + 2, y + 6, 'K')
            c.hline(bx, bx + 1, y + 3, 'F')
    return c


# ================================================================ cartons, bin, coat rail
CARTONS = [   # x0, x1, top_y, depth, height, open
    (214, 254, None, 8, 26, False),
    (219, 247, None, 6, 12, False),          # stacked on the big one
    (258, 294, None, 9, 16, True),
]


def carton_geom():
    """Resolve the stack: returns [(x0, x1, y_top, depth, height, open)]."""
    out = []
    big = CARTONS[0]
    base = FLOOR_Y + big[3]                           # front bottom on the floor
    yt = base - big[4] - big[3]
    out.append((big[0], big[1], yt, big[3], big[4], big[5]))
    small = CARTONS[1]
    out.append((small[0], small[1], yt - small[4] - small[3] + big[3] - 2, small[3], small[4],
                small[5]))
    op = CARTONS[2]
    base = FLOOR_Y + op[3]
    out.append((op[0], op[1], base - op[4] - op[3], op[3], op[4], op[5]))
    return out


def cartons(under):
    c = Canvas()
    g = carton_geom()
    shade_under(c, under, rect_mask(212, FLOOR_Y + 9, 297, FLOOR_Y + 10), 1)

    def carton(x0, x1, y_top, depth, height, open_):
        yf = y_top + depth
        yb = yf + height
        c.rect(x0, y_top, x1, yf - 1, 'd')
        c.rect(x0, yf, x1, yb, 'w')
        c.vline(x0, yf, yb, 'd')
        c.hline(x0, x1, yb, 'B')
        mx = (x0 + x1) // 2
        if not open_:
            c.rect(mx - 1, y_top, mx + 1, yf - 1, 's')
            c.rect(mx - 1, yf, mx + 1, yf + 3, 's')
        else:
            c.rect(x0 + 2, y_top + 1, x1 - 2, yf - 1, 'B')
            c.hline(x0 + 2, x1 - 2, y_top + 1, 'M')
        outline(c, rect_mask(x0, y_top, x1, yb))
        c.hline(x0, x1, yf - 1, 'K')
        c.rect(x1 - 7, yf + 3, x1 - 3, yf + 6, 'P')          # shipping label
        c.hline(x1 - 6, x1 - 4, yf + 5, 'g')
        if open_:
            # flaps flopped open either side
            fl = poly_mask([(x0, y_top), (x0 - 4, y_top - 5), (x0 + 6, y_top - 6), (x0 + 8, y_top)])
            fr = poly_mask([(x1, y_top), (x1 + 3, y_top - 6), (x1 - 7, y_top - 6),
                            (x1 - 8, y_top)])
            c.fill(fl, 'd')
            c.fill(fr, 's')
            outline(c, fl | fr | rect_mask(x0, y_top, x1, yb))
            c.hline(x0, x1, yf - 1, 'K')

    for (x0, x1, yt, dp, ht, op) in g:
        carton(x0, x1, yt, dp, ht, op)
    return c


def trash_bin(under):
    c = Canvas()
    cx, base = 326, FLOOR_Y + 8
    shade_under(c, under, ellipse_mask(cx, base, 9, 3), 1)
    body = poly_mask([(cx - 7, base - 16), (cx + 7, base - 16), (cx + 6, base), (cx - 6, base)])
    c.fill(body, 'N')
    for y in range(base - 15, base):
        for x in range(cx - 6, cx + 7):
            if body[y, x] and (x + y) % 3 == 0:
                c.set(x, y, 'E')
    c.vline(cx - 6, base - 15, base - 1, 'D')
    balls = [(cx - 4, base - 18, 2.6), (cx + 2, base - 19, 3.0), (cx + 6, base - 17, 2.2),
             (cx - 1, base - 22, 2.4)]
    m = body.copy()
    for (px, py, r) in balls:
        e = ellipse_mask(px, py, r, r * 0.9)
        c.fill(e, 'P')
        c.set(int(px), int(py), 'g')
        c.set(int(px) + 1, int(py) - 1, 'W')
        m |= e
    outline(c, m)
    c.hline(cx - 7, cx + 7, base - 16, 'K')
    return c


def coat_rail():
    c = Canvas()
    c.rect(13, 70, 37, 73, 'B')
    c.hline(13, 37, 70, 'd')
    c.box(12, 69, 38, 74, 'K')
    for px in (18, 31):
        c.rect(px, 74, px + 1, 77, 'E')
        c.set(px, 74, 'F')
        c.box(px - 1, 74, px + 2, 78, 'K')
    return c
