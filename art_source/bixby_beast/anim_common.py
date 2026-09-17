"""Shared helpers for the beast Bixby animation sheets: strips, previews, ground line guides."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pngio import write_png, read_png, scale, crop

HERE = os.path.dirname(os.path.abspath(__file__))
PREV = os.path.join(HERE, '..', 'prev')
FINAL = os.path.join(HERE, '..', 'final_anims')
os.makedirs(PREV, exist_ok=True)
os.makedirs(FINAL, exist_ok=True)

FLOOR = (136, 180, 99, 255)
BG = (96, 112, 104, 255)
ANCHOR = (96, 151)          # hover feet anchor == grounded feet anchor (frame space)
GROUND_Y = 151


def strip_of(frames, fw=192, fh=160):
    s = Canvas(fw * len(frames), fh)
    for i, c in enumerate(frames):
        s.blit(c, fw * i, 0)
    return s


def preview(cv, name, s=3, bg=FLOOR, guides=False, fw=192):
    px = cv.rgba()
    px = [[(p if p[3] else bg) for p in row] for row in px]
    if guides:
        for fx in range(0, cv.w, fw):
            x = fx + ANCHOR[0]
            for y in range(cv.h):
                if px[y][x] == bg:
                    px[y][x] = (200, 60, 60, 255)
            for xx in range(fx, fx + fw):
                if px[GROUND_Y][xx] == bg:
                    px[GROUND_Y][xx] = (60, 60, 200, 255)
    out = os.path.join(PREV, name)
    write_png(out, cv.w * s, cv.h * s, scale(px, s))
    return out


def crop_canvas(cv, x0, y0, w, h):
    out = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            out.px[y][x] = cv.get(x0 + x, y0 + y)
    return out
