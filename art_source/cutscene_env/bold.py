"""Bold poster headline font, built from rects / rounded rects / slanted bands at final size.

Cap height 20 px, stroke 4 px. Glyphs are sets of (x, y) pixels.
"""
import math
from lib import poly_mask

HGT = 20


def rect(x0, y0, x1, y1):
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)}


def rrect(x0, y0, x1, y1, r_tl=0, r_tr=0, r_br=0, r_bl=0):
    """Rounded rect (pixel centres inside)."""
    out = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            ok = True
            for (r, cx, cy, sx, sy) in ((r_tl, x0 + r_tl, y0 + r_tl, -1, -1), (r_tr, x1 - r_tr, y0 + r_tr, 1, -1),
                                        (r_br, x1 - r_br, y1 - r_br, 1, 1), (r_bl, x0 + r_bl, y1 - r_bl, -1, 1)):
                if r <= 0:
                    continue
                if (x - cx) * sx > 0 and (y - cy) * sy > 0:
                    if (x - cx) ** 2 + (y - cy) ** 2 > (r + 0.35) ** 2:
                        ok = False
            if ok:
                out.add((x, y))
    return out


def band(pts):
    return poly_mask(pts)


def g_E():
    return rect(0, 0, 15, 3) | rect(0, 0, 3, 19) | rect(0, 8, 12, 11) | rect(0, 16, 15, 19)


def g_T():
    return rect(0, 0, 15, 3) | rect(6, 0, 9, 19)


def g_M():
    w = 22
    s = rect(0, 0, 3, 19) | rect(w - 4, 0, w - 1, 19)
    s |= band([(3, 0), (8, 0), (12.6, 13), (8.6, 13)])
    s |= band([(w - 3, 0), (w - 8, 0), (w - 12.6, 13), (w - 8.6, 13)])
    return s


def g_W():
    return {(x, HGT - 1 - y) for (x, y) in g_M()}


def g_N():
    return rect(0, 0, 3, 19) | rect(14, 0, 17, 19) | band([(3, 0), (8, 0), (15, 20), (10, 20)])


def g_A():
    outer = rrect(0, 0, 17, 19, r_tl=6, r_tr=6)
    counter = rrect(4, 4, 13, 9, r_tl=2, r_tr=2)
    lower = rect(4, 14, 13, 19)
    return outer - counter - lower


def g_R():
    s = rect(0, 0, 3, 19)
    s |= rrect(0, 0, 17, 12, r_tr=5, r_br=5) - rrect(4, 4, 13, 8, r_tr=1, r_br=1)
    s |= band([(8, 12), (13, 12), (18, 20), (13, 20)])
    return s


def g_B():
    s = rect(0, 0, 3, 19)
    s |= rrect(0, 0, 16, 11, r_tr=4, r_br=3) - rrect(4, 4, 12, 7, r_tr=1, r_br=1)
    s |= rrect(0, 8, 17, 19, r_tr=3, r_br=5) - rrect(4, 12, 13, 15, r_tr=1, r_br=1)
    return s


def g_D():
    return rrect(0, 0, 17, 19, r_tr=7, r_br=7) - rrect(4, 4, 13, 15, r_tr=3, r_br=3)


def g_S():
    top = rrect(0, 0, 16, 11, r_tl=5, r_tr=2) - rect(4, 4, 16, 7)
    bot = rrect(0, 8, 16, 19, r_br=5, r_bl=2) - rect(0, 12, 12, 15)
    return top | bot


def g_Y():
    s = band([(-0.5, 0), (4, 0), (10, 10), (7, 12)]) | band([(18.5, 0), (14, 0), (8, 10), (11, 12)])
    return {(x, y) for (x, y) in s if 0 <= x <= 17} | rect(7, 10, 10, 19)


def g_O():
    return rrect(0, 0, 17, 19, 7, 7, 7, 7) - rrect(4, 4, 13, 15, 3, 3, 3, 3)


def g_U():
    return rrect(0, 0, 17, 19, r_br=7, r_bl=7) - rrect(4, -1, 13, 15, r_br=3, r_bl=3)


def g_HASH():
    return rect(3, 0, 6, 19) | rect(11, 0, 14, 19) | rect(0, 5, 17, 7) | rect(0, 12, 17, 14)


def g_1():
    return rect(6, 0, 9, 19) | band([(6, 0), (9, 0), (2, 6), (2, 3)]) | rect(2, 16, 13, 19)


def g_SPACE():
    return set()


GLYPHS = {
    'E': (g_E, 16), 'T': (g_T, 16), 'M': (g_M, 22), 'W': (g_W, 22), 'N': (g_N, 18), 'A': (g_A, 18),
    'R': (g_R, 18), 'B': (g_B, 18), 'D': (g_D, 18), 'S': (g_S, 17), 'Y': (g_Y, 18), 'O': (g_O, 18),
    'U': (g_U, 18), '#': (g_HASH, 18), '1': (g_1, 14), ' ': (g_SPACE, 8),
}


def word(s, x0=0, y0=0, spacing=3):
    pts = set()
    x = x0
    for ch in s:
        fn, w = GLYPHS[ch]
        for (gx, gy) in fn():
            if 0 <= gx < w and 0 <= gy < HGT:
                pts.add((x + gx, y0 + gy))
        x += w + spacing
    return pts


def word_width(s, spacing=3):
    return sum(GLYPHS[ch][1] + spacing for ch in s) - spacing
