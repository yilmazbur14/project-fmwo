"""v2 lower legs for turned views: 8 rows (knee plate x2, lame, foot lame x2 + black lines), same tone scheme as
designer A's LEG_L stamp. 96-space, rows 88..95."""
import lib
from lib import PALC, BLACK

TOP = ['A', 'W', 'W', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'D']
BOT = ['B', 'B', 'C', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'E']
DARKER = {'W': 'A', 'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'E'}

SHAPES = {   # (dy, x0, x1, kind) relative to leg centre; toe = +x (facing right)
    'profile': [(0, -5, 5, 't'), (1, -6, 6, 'b'), (2, -7, 8, 'k'), (3, -7, 10, 't'), (4, -8, 12, 'k'),
                (5, -8, 14, 't'), (6, -8, 14, 'b'), (7, -7, 13, 'k')],
    '34': [(0, -6, 6, 't'), (1, -7, 7, 'b'), (2, -8, 9, 'k'), (3, -8, 10, 't'), (4, -9, 11, 'k'),
           (5, -9, 12, 't'), (6, -9, 12, 'b'), (7, -8, 11, 'k')],
    'back': [(0, -6, 6, 't'), (1, -7, 7, 'b'), (2, -8, 8, 'k'), (3, -8, 8, 't'), (4, -9, 9, 'k'),
             (5, -9, 9, 't'), (6, -9, 9, 'b'), (7, -8, 8, 'k')],
    'back34': [(0, -6, 6, 't'), (1, -7, 6, 'b'), (2, -8, 7, 'k'), (3, -9, 7, 't'), (4, -10, 8, 'k'),
               (5, -11, 8, 't'), (6, -11, 8, 'b'), (7, -10, 7, 'k')],
}


def draw_leg(cv, shape, cx, y0=88, side=1, dark=0):
    rows = SHAPES[shape]
    for dy, a, b, kind in rows:
        if side < 0:
            a, b = -b, -a
        x0, x1 = int(round(cx + a)), int(round(cx + b))
        y = y0 + dy
        n = x1 - x0
        for x in range(x0, x1 + 1):
            if not (0 <= x < 96 and 0 <= y < 96):
                continue
            if kind == 'k' or x in (x0, x1):
                cv.px[y][x] = BLACK
                continue
            t = (x - x0) / max(1, n)
            tones = TOP if kind == 't' else BOT
            ch = tones[min(len(tones) - 1, int(t * len(tones)))]
            for _ in range(dark):
                ch = DARKER[ch]
            cv.px[y][x] = PALC[ch]
    dy, a, b, kind = rows[0]
    if side < 0:
        a, b = -b, -a
    for x in range(int(round(cx + a)), int(round(cx + b)) + 1):
        if 0 <= x < 96:
            cv.px[y0 - 1][x] = BLACK


def legs_layer(yaw, side=1):
    lib.W = lib.H = 96
    cv = lib.Canvas()
    S = 0.8
    c = lambda x: 48 + (x - 48) * S
    if yaw == 45:
        draw_leg(cv, '34', 48 + side * (c(60) - 48), 87, side, dark=1)
        draw_leg(cv, '34', 48 + side * (c(37) - 48), 88, side)
    elif yaw == 90:
        draw_leg(cv, 'profile', 48 + side * -3, 87, side, dark=1)
        draw_leg(cv, 'profile', 48 + side * 1, 88, side)
    elif yaw == 135:
        draw_leg(cv, 'back34', 48 + side * (c(36) - 48), 87, side, dark=1)
        draw_leg(cv, 'back34', 48 + side * (c(60) - 48), 88, side)
    elif yaw == 180:
        draw_leg(cv, 'back', c(31), 88, 1)
        draw_leg(cv, 'back', c(65), 88, 1)
    return cv.px
