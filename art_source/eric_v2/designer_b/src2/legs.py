"""Lower legs (knee plate + two sabaton lames) for turned views, 96-space, same tone scheme as legstamp.py."""
import lib
from lib import PALC, BLACK

TOP = ['A', 'W', 'W', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'D']      # lit edge -> shadow edge
BOT = ['B', 'B', 'C', 'C', 'C', 'C', 'C', 'D', 'D', 'D', 'E']
DARKER = {'W': 'A', 'A': 'B', 'B': 'C', 'C': 'D', 'D': 'E', 'E': 'E'}

# per view: list of (dy, x0, x1, kind) relative to the leg centre cx and y=86; kind 't' top plate row,
# 'b' bottom plate row, 'k' black line.  toe = +x (facing right)
SHAPES = {
    'profile': [(0, -7, 7, 't'), (1, -7, 8, 't'), (2, -7, 8, 'b'), (3, -9, 10, 'k'), (4, -9, 11, 't'),
                (5, -9, 13, 'b'), (6, -11, 15, 'k'), (7, -11, 16, 't'), (8, -11, 18, 'b'), (9, -11, 17, 'k')],
    '34': [(0, -7, 7, 't'), (1, -7, 8, 't'), (2, -7, 8, 'b'), (3, -9, 10, 'k'), (4, -9, 11, 't'),
           (5, -9, 12, 'b'), (6, -10, 13, 'k'), (7, -10, 14, 't'), (8, -10, 15, 'b'), (9, -9, 14, 'k')],
    'back': [(0, -8, 8, 't'), (1, -8, 8, 't'), (2, -8, 8, 'b'), (3, -9, 9, 'k'), (4, -9, 9, 't'),
             (5, -9, 9, 'b'), (6, -10, 10, 'k'), (7, -10, 10, 't'), (8, -10, 10, 'b'), (9, -9, 9, 'k')],
    'back34': [(0, -7, 7, 't'), (1, -7, 7, 't'), (2, -7, 8, 'b'), (3, -9, 8, 'k'), (4, -10, 8, 't'),
               (5, -10, 8, 'b'), (6, -11, 9, 'k'), (7, -12, 9, 't'), (8, -12, 9, 'b'), (9, -11, 8, 'k')],
}


def draw_leg(cv, shape, cx, y0=86, side=1, dark=0):
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
    # cap the top of the knee plate
    dy, a, b, kind = rows[0]
    if side < 0:
        a, b = -b, -a
    for x in range(int(round(cx + a)), int(round(cx + b)) + 1):
        if 0 <= x < 96 and 0 <= y0 - 1 < 96:
            cv.px[y0 - 1][x] = BLACK


def legs_layer(yaw, side=1):
    """returns 96-space px for the two lower legs in the given view"""
    lib.W = lib.H = 96
    cv = lib.Canvas()
    if yaw == 45:
        far, near = 60, 37
        draw_leg(cv, '34', 48 + side * (far - 48), 85, side, dark=1)
        draw_leg(cv, '34', 48 + side * (near - 48), 86, side)
    elif yaw == 90:
        draw_leg(cv, 'profile', 48 + side * -4, 85, side, dark=1)
        draw_leg(cv, 'profile', 48 + side * 1, 86, side)
    elif yaw == 135:
        far, near = 36, 60
        draw_leg(cv, 'back34', 48 + side * (far - 48), 85, side, dark=1)
        draw_leg(cv, 'back34', 48 + side * (near - 48), 86, side)
    elif yaw == 180:
        draw_leg(cv, 'back', 31, 86, 1)
        draw_leg(cv, 'back', 65, 86, 1)
    return cv.px
