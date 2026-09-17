"""Preview helpers: zoomed PNGs on a neutral bg into ../le_prev, side-by-side strips."""
import os
from pngio import write_png, scale, blank, paste, crop

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.normpath(os.path.join(HERE, '..', 'le_prev'))
os.makedirs(PREV, exist_ok=True)
BG = (96, 112, 104, 255)
FLOOR = (136, 180, 99, 255)


def zoom(cv, s, name, bg=BG, region=None):
    px = cv.rgba()
    w, h = cv.w, cv.h
    if region:
        x0, y0, rw, rh = region
        px = crop(px, x0, y0, rw, rh)
        w, h = rw, rh
    path = os.path.join(PREV, name)
    write_png(path, w * s, h * s, scale(px, s, bg))
    return path


def row(cvs, s, name, gap=4, bg=BG, panel=None, bottom=True):
    W = sum(c.w for c in cvs) + gap * (len(cvs) + 1)
    H = max(c.h for c in cvs) + gap * 2
    out = blank(W, H, bg)
    x = gap
    for c in cvs:
        y = (H - gap - c.h) if bottom else gap
        px = c.rgba()
        if panel:
            px = [[p if p[3] else panel for p in r] for r in px]
        paste(out, px, x, y)
        x += c.w + gap
    path = os.path.join(PREV, name)
    write_png(path, W * s, H * s, scale(out, s))
    return path
