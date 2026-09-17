"""Palanquin building blocks + assembly (imported by throne.py's build)."""
import math
from lib import *
from pal import *

GOLD = GOLD_A

# ------------------------------------------------------------------ tiny font for plates
FONT35 = {
    '@': ["01110", "10001", "10111", "10101", "10111", "10000", "01110"],
    'L': ["100", "100", "100", "100", "111"], 'I': ["111", "010", "010", "010", "111"],
    'A': ["010", "101", "111", "101", "101"], 'M': ["10001", "11011", "10101", "10001", "10001"],
}


def plate_text(cv, s, x, y, col):
    cx = x
    for ch in s:
        g = FONT35[ch]
        oy = y - (1 if len(g) > 5 else 0)
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == '1':
                    cv.put(cx + i, oy + j, col)
        cx += len(g[0]) + 1
    return cx - x - 1


def text_w(s):
    return sum(len(FONT35[c][0]) + 1 for c in s) - 1

# ------------------------------------------------------------------ building blocks


def gold_bar_h(cv, x0, x1, y0, y1, outline=True):
    m = rect(x0, y0, x1, y1)
    cv.part(m, GOLD, ('cyl', (x0, (y0 + y1 + 1) / 2), (x1 + 1, (y0 + y1 + 1) / 2), (y1 - y0 + 1) / 2 + 0.3, 0.15), TH_METAL, outline)
    return m


def gold_ball(cv, cx, cy, r):
    m = ell(cx, cy, r, r)
    cv.part(m, GOLD, ('sphere', cx - 0.4, cy - 0.4, r + 0.8, r + 0.8), TH_METAL)
    return m


def ribbon(cv, pts, rp, width=1.4):
    m = tube(pts, (width, width))
    cv.part(m, rp, ('dist', 1.5, 0.4), [9.0, 0.75, 0.2])
    return m


def pole(cv, y0, x0, x1):
    m = rect(x0, y0, x1, y0 + 3)
    for x in range(x0, x1 + 1):
        cv.put(x, y0, BLACK)
        cv.put(x, y0 + 1, WOOD[0] if (x // 9) % 2 == 0 else WOOD[1])
        cv.put(x, y0 + 2, WOOD[2])
        cv.put(x, y0 + 3, BLACK)
    for fx in (x0, x1 - 3):
        cv.fill(rect(fx, y0, fx + 3, y0 + 3), BLACK)
        for x in range(fx + 1, fx + 3):
            cv.put(x, y0 + 1, GOLD[1])
            cv.put(x, y0 + 2, GOLD[3])
    gold_ball(cv, x0 - 3, y0 + 2, 3.2)
    gold_ball(cv, x1 + 4, y0 + 2, 3.2)
    return m


def tassel(cv, x, y):
    grid = """
.k.
kyk
kok
kyk
kok
.k.
"""
    cv.stamp(grid, x - 1, y, {'k': BLACK, 'y': GOLD[1], 'o': GOLD[3]})


def tufted_panel(cv, m, cx, cy, rx, ry):
    """velvet panel: soft pillow shading + diamond tufting lines + gold buttons"""
    cv.part(m, VELVET, ('sphere', cx - 3, cy - 6, rx * 1.3, ry * 1.25, 0.55), [9.0, 0.86, 0.62, 0.34, 0.1], outline=False)
    x0, y0, x1, y1 = bbox(m)
    step = 8
    for (x, y) in m:
        u = (x - cx) + (y - cy)
        v = (x - cx) - (y - cy)
        if u % step == 0 or v % step == 0:
            c = cv.get(x, y)
            cv.put(x, y, DARKER.get(c, c))
    for yy in range(y0 - step, y1 + step):
        for xx in range(x0 - step, x1 + step):
            if ((xx - cx) + (yy - cy)) % step == 0 and ((xx - cx) - (yy - cy)) % step == 0 and (xx, yy) in m:
                cv.put(xx, yy, GOLD[1])
                if (xx + 1, yy + 1) in m:
                    cv.put(xx + 1, yy + 1, GOLD[3])


def pennant(cv, x, ytop, ybase, side):
    """gold flagpole with a blurple pennant carrying a white @"""
    cv.part(rect(x - 1, ytop + 2, x, ybase), GOLD, ('cyl', (x - 1.5, 0), (x - 1.5, 1), 1.6), TH_METAL)
    gold_ball(cv, x - 0.5, ytop + 1, 2.2)
    fx = x + (1 if side > 0 else -2)
    flag = poly([(fx, ytop + 4), (fx + side * 17, ytop + 7), (fx + side * 13, ytop + 11), (fx + side * 18, ytop + 15), (fx, ytop + 18)])
    cv.part(flag, VELVET, ('dist', 3, 0.5), [9.0, 0.85, 0.6, 0.3, 0.1])
    at = ["01110", "10001", "10111", "10101", "10110", "01000", "00111"]
    ax = fx + (2 if side > 0 else -7)
    for j, row in enumerate(at):
        for i, v in enumerate(row):
            if v == '1':
                cv.put(ax + i, ytop + 7 + j, WHITE)
