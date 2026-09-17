"""1920x1080 mockup: background x3 + banner (9-slice x3) + kit button + text.
python mock.py bg.png out.png [title_style] [guides]"""
import sys
from lib import *
import banner as bn

UI = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/"
TXT = "out/text/"

# layout in 1920x1080 screen px
TITLE = (0, 27, 1920, 119)            # label rect x, y, w, h (text centred)
BANNER = (360, 741, 1200, 138)
BUTTON = (636, 915, 648, 126)
BANNER_TEXT_X = BANNER[0] + (bn.ML * 3) + 15
NAME_Y = BANNER[1] + 21
MSG_Y = BANNER[1] + 72


def text_mask(name):
    from pngio import read_png
    w, h, px = read_png(TXT + name + '.png')
    t = Img(w, h)
    for y in range(h):
        for x in range(w):
            if px[y][x][3] >= 128:
                t.p[y][x] = 'ffffff'
    return t


def put_text(scr, name, x, y, color, outline=None, osize=0, shadow=None, sdy=0):
    t = text_mask(name)
    pts = [(xx, yy) for yy in range(t.h) for xx in range(t.w) if t.p[yy][xx] is not None]
    if shadow:
        for (xx, yy) in pts:
            for dx in range(-osize, osize + 1):
                for dy in range(-osize, osize + 1):
                    scr.set(x + xx + dx, y + yy + dy + sdy, shadow)
    if outline:
        for (xx, yy) in pts:
            for dx in range(-osize, osize + 1):
                for dy in range(-osize, osize + 1):
                    scr.set(x + xx + dx, y + yy + dy, outline)
    for (xx, yy) in pts:
        scr.set(x + xx, y + yy, color)
    return t.w, t.h


def text_width(name):
    t = text_mask(name)
    xs = [xx for yy in range(t.h) for xx in range(t.w) if t.p[yy][xx] is not None]
    return min(xs), max(xs) + 1


def build(bg_path, out_path, title_style='red', guides=False):
    bg = load(bg_path)
    scr = bg.scaled(3)
    # banner
    b1 = load('out/defeat_banner.png') if False else bn.build('b')
    b3 = b1.scaled(3)
    nb = bn.nine_slice(b3, bn.ML * 3, bn.MT * 3, bn.MR * 3, bn.MB * 3, BANNER[2], BANNER[3])
    scr.blit(nb, BANNER[0], BANNER[1])
    # button (kit 3x, uniform 24 px margins)
    btn = load(UI + 'ui_button_3x.png')
    nbtn = bn.nine_slice(btn, 24, 24, 24, 24, BUTTON[2], BUTTON[3])
    scr.blit(nbtn, BUTTON[0], BUTTON[1])
    # title
    x0, x1 = text_width('title')
    tw = x1 - x0
    tx = TITLE[0] + (TITLE[2] - tw) // 2 - x0
    if title_style == 'red':
        put_text(scr, 'title', tx, TITLE[1], RED_L, outline=K, osize=6, shadow=PLUM, sdy=9)
    elif title_style == 'white':
        put_text(scr, 'title', tx, TITLE[1], WHITE, outline=K, osize=6, shadow=RED, sdy=9)
    # banner text
    put_text(scr, 'name', BANNER_TEXT_X, NAME_Y, RED_L)
    n0, n1 = text_width('name')
    put_text(scr, 'time', BANNER_TEXT_X + n1 + 18, NAME_Y, GREY)
    put_text(scr, 'msg', BANNER_TEXT_X, MSG_Y, ICE)
    # button text centred, content margins as ControlsScene (24/30/24/29)
    b0, b1x = text_width('btn')
    bw = b1x - b0
    put_text(scr, 'btn', BUTTON[0] + (BUTTON[2] - bw) // 2 - b0, BUTTON[1] + 30 - 1, WHITE)
    if guides:
        for (x, y, w, h) in (TITLE, BANNER, BUTTON):
            scr.hline(x, x + w - 1, y, YELLOW)
            scr.hline(x, x + w - 1, y + h - 1, YELLOW)
            scr.vline(x, y, y + h - 1, YELLOW)
            scr.vline(x + w - 1, y, y + h - 1, YELLOW)
    scr.save(out_path)
    return scr


if __name__ == '__main__':
    a = sys.argv
    build(a[1], a[2], a[3] if len(a) > 3 else 'red', len(a) > 4)
