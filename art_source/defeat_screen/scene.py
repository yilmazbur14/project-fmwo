"""Defeat screen background: environment layers (ring, ropes, posts, light)."""
import math
from lib import *

W, H = 640, 360
FAR_Y = 121            # canvas far edge (first canvas row)
FAR_L = 58             # far-left canvas corner x
K_SLOPE = 100 / 240.0  # outward x per y
POOL = (320, 184, 138, 62)   # spotlight pool cx, cy, rx, ry
POOL_CORE = 0.78


def side_l(y):
    return FAR_L - (y - FAR_Y) * K_SLOPE


def side_r(y):
    return 639 - side_l(y)


def persp(y):
    """size scale at canvas row y (1.0 at the far edge)"""
    return 1.0 + 0.385 * (y - FAR_Y) / 240.0


def pool_r(x, y):
    cx, cy, rx, ry = POOL
    return math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)


def backdrop(img):
    """rafters + stands darkness"""
    for y in range(H):
        for x in range(W):
            if y < 34:
                c = K
            elif y < 58:
                c = mix(x, y, K, NAVY, (y - 34) / 24.0)
            elif y < 96:
                c = mix(x, y, NAVY, PLUM, (y - 58) / 60.0)
            else:
                c = mix(x, y, NAVY, PLUM, 0.62)
            img.set(x, y, c)


def canvas(img):
    for y in range(FAR_Y - 3, H):
        xl, xr = side_l(y), side_r(y)
        for x in range(W):
            if not (xl - 4 <= x + 0.5 <= xr + 4):
                continue
            apron = not (xl <= x + 0.5 <= xr) or y < FAR_Y
            r = pool_r(x, y)
            if apron:
                c = K if (y == FAR_Y - 3 or abs(x + 0.5 - (xl - 4)) < 0.8 or abs(x + 0.5 - (xr + 4)) < 0.8) else PLUM
                img.set(x, y, c)
                continue
            if r < POOL_CORE:
                c = OLIVE
            elif r < POOL_CORE + 0.06:
                c = checker(x, y, OLIVE, GREEN_D)
            elif r < 0.985:
                c = GREEN_D
            elif r < 1.03:
                c = checker(x, y, GREEN_D, SLATE)
            else:
                # falloff into red-tinted dark
                t = min(1.0, (r - 1.03) / 1.1)
                c = mix(x, y, SLATE, PLUM, t)
            img.set(x, y, c)
    # canvas lip line along far edge and sides (edge of ring mat)
    for y in range(FAR_Y - 2, H):
        xl, xr = side_l(y), side_r(y)
        img.set(int(round(xl - 0.5)), y, K)
        img.set(int(round(xr - 0.5)), y, K)
    img.hline(int(side_l(FAR_Y)), int(side_r(FAR_Y)), FAR_Y - 1, K)


ROPE_H = [34, 22, 10]


def rope_line(img, pts, lit=False):
    """pts: list of (x,y) centre points; rope is 4px tall: K, top, body, K"""
    top, body = (GREY_L, GREY) if lit else (GREY, GREY_D)
    cols = {}
    for x, y in pts:
        cols.setdefault(x, []).append(y)
    for x, ys in cols.items():
        y0, y1 = min(ys), max(ys)
        img.set(x, y0 - 2, K)
        for yy in range(y0 - 1, y1 + 2):
            img.set(x, yy, K)
        img.set(x, y0 - 1, top)
        for yy in range(y0, y1 + 1):
            img.set(x, yy, body)
        img.set(x, y1 + 1, K)


def ropes_far(img):
    xl = int(side_l(FAR_Y)) + 4
    xr = int(side_r(FAR_Y)) - 4
    for h in ROPE_H:
        y = FAR_Y - h
        rope_line(img, [(x, y) for x in range(xl, xr + 1)])


def ropes_side(img):
    for h in ROPE_H:
        x0, y0 = FAR_L + 4, FAR_Y - h
        # where the rope exits the frame at x = -1
        yb = FAR_Y + (FAR_L + 1) / K_SLOPE
        y1 = int(round(yb - h * persp(yb)))
        pts = line_pts(x0, y0, -1, y1)
        rope_line(img, pts)
        rope_line(img, [(639 - x, y) for x, y in pts])


def post(img, cx, top, base):
    """brass ring post, 11 px wide cylinder with a domed cap"""
    ramp = {-5: K, -4: BRASS, -3: TAN, -2: TAN, -1: BRASS, 0: BRASS, 1: BRASS, 2: BRASS, 3: OLIVE_D, 4: OLIVE_D, 5: K}
    for y in range(top, base + 1):
        for dx in range(-5, 6):
            img.set(cx + dx, y, ramp[dx])
    # domed cap
    img.hline(cx - 3, cx + 3, top - 3, K)
    img.set(cx - 4, top - 2, K); img.set(cx + 4, top - 2, K)
    img.hline(cx - 3, cx + 3, top - 2, TAN)
    img.set(cx - 2, top - 2, SKIN_L)
    img.hline(cx + 2, cx + 3, top - 2, BRASS)
    img.set(cx - 5, top - 1, K); img.set(cx + 5, top - 1, K)
    img.hline(cx - 4, cx + 4, top - 1, BRASS)
    img.hline(cx - 3, cx - 2, top - 1, TAN)
    img.hline(cx + 3, cx + 4, top - 1, OLIVE_D)
    img.hline(cx - 4, cx + 4, top, K)
    img.hline(cx - 4, cx + 4, base + 1, K)
    # rope attach collars
    for h in ROPE_H:
        y = FAR_Y - h
        img.hline(cx - 5, cx + 5, y - 2, K)
        img.hline(cx - 5, cx + 5, y + 2, K)
        img.hline(cx - 4, cx + 4, y - 1, GREY)
        img.hline(cx - 4, cx + 4, y, GREY_D)
        img.hline(cx - 4, cx + 4, y + 1, GREY_D)
        img.set(cx - 3, y - 1, GREY_L)


def posts(img):
    post(img, FAR_L + 3, FAR_Y - ROPE_H[0] - 9, FAR_Y + 1)
    post(img, 639 - (FAR_L + 3), FAR_Y - ROPE_H[0] - 9, FAR_Y + 1)


if __name__ == '__main__':
    im = Img(W, H)
    backdrop(im)
    canvas(im)
    ropes_side(im)
    ropes_far(im)
    posts(im)
    im.save('out/stage1.png')
    zoom_save(im, 'out/stage1_2x.png', 2)
    print(im.check_db32())
