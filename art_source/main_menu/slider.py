"""Volume-slider textures for the main menu, lifted 1:1 from the approved 1920x1080 mockup (which was
drawn on a 3px grid). 1x textures plus nearest-neighbour _3x copies (same convention as Assets/UI/ui_*).

  menu_slider_track    8x10  (3x: 24x30)  9-slice margins L3 T4 R3 B3 (3x: 9/12/9/9)   empty track
  menu_slider_fill     8x10  (3x: 24x30)  9-slice margins L3 T4 R3 B3 (3x: 9/12/9/9)   filled part (same frame, crimson)
  menu_slider_grabber 12x18  (3x: 36x54)  plain icon                                 brass handle
"""
import os
from lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
MARGINS = (3, 4, 3, 3)   # left, top, right, bottom (1x)

# frame rows shared by track and fill; 'c' = interior top row, 'i' = interior
FRAME = [
    "KKKKKKKK",
    "KttttttK",
    "KoKKKKoK",
    "KoKccKoK",
    "KoKiiKoK",
    "KoKiiKoK",
    "KoKiiKoK",
    "KoKKKKoK",
    "KooooooK",
    "KKKKKKKK",
]
TRACK_MAP = {'K': K, 't': TN, 'o': GO, 'c': N0, 'i': N0}
FILL_MAP = {'K': K, 't': TN, 'o': GO, 'c': PK, 'i': RD}

GRABBER = [
    "KKKKKKKKKKKK",
    "KyyyyyyyytoK",
    "KyyyyyyyytoK",
    "KtttttttttoK",
    "KtttttttttoK",
    "KtttttttttoK",
    "KtttoooottoK",
    "KtttoooottoK",
    "KtttoooottoK",
    "KtttoooottoK",
    "KtttoooottoK",
    "KtttoooottoK",
    "KtttttttttoK",
    "KtttttttttoK",
    "KtttttttttoK",
    "KtttttttttoK",
    "KooooooooooK",
    "KKKKKKKKKKKK",
]
GRAB_MAP = {'K': K, 'y': YL, 't': TN, 'o': GO}


def canvas(rows, cmap):
    c = Canvas(len(rows[0]), len(rows))
    c.grid(0, 0, rows, cmap, skip='.')
    return c


def scale3(c):
    o = Canvas(c.w * 3, c.h * 3)
    for y in range(o.h):
        for x in range(o.w):
            o.p[y][x] = c.p[y // 3][x // 3]
    return o


def build():
    return {
        'menu_slider_track': canvas(FRAME, TRACK_MAP),
        'menu_slider_fill': canvas(FRAME, FILL_MAP),
        'menu_slider_grabber': canvas(GRABBER, GRAB_MAP),
    }


def check_nine_slice(c, margins):
    """every row is constant across the horizontal stretch band and every column is constant down the
    vertical stretch band, so the texture stretches seamlessly as a 9-slice"""
    l, t, r, b = margins
    for y in range(c.h):
        assert len(set(c.p[y][x] for x in range(l, c.w - r))) == 1, ('row not uniform across centre', y)
    for x in range(c.w):
        assert len(set(c.p[y][x] for y in range(t, c.h - b))) == 1, ('column not uniform down centre', x)


if __name__ == '__main__':
    out = os.path.join(HERE, 'final')
    os.makedirs(out, exist_ok=True)
    for name, c in build().items():
        if name != 'menu_slider_grabber':
            check_nine_slice(c, MARGINS)
        c.save(os.path.join(out, name + '.png'))
        scale3(c).save(os.path.join(out, name + '_3x.png'))
        print(name, c.w, c.h)
