"""Dazed stars orbiting the KO'd player's head: 4-frame horizontal strip.
3 stars 120 deg apart, 30 deg per frame -> frame 4 == frame 0 (seamless loop).
python stars.py"""
import math
from lib import *

FW, FH = 56, 26
ORBIT = (28.0, 13.0, 22.0, 7.0)        # cx, cy, rx, ry inside a frame
# placement of the frame's top-left in the 640x360 background (head centre x=318)
ANCHOR = (290, 123)

BIG = [
    "....K....",
    "...KyK...",
    "KKKKyKKKK",
    "KyywyyyyK",
    ".KyyyyyK.",
    "..KyyyK..",
    ".KyyKyyK.",
    ".KyK.KyK.",
    ".KK...KK.",
]
BIG_SHADE = {  # lower-right pixels get the tan shade
    (6, 3), (7, 3), (5, 4), (6, 4), (5, 5), (6, 6), (6, 7),
}
SMALL = [
    "...K...",
    "..KyK..",
    "KKKyKKK",
    "KyyyyyK",
    ".KyyyK.",
    ".KyKyK.",
    ".KK.KK.",
]


def stamp_star(img, rows, x0, y0, body, glint, shade, shade_px=()):
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '.':
                continue
            c = {'K': K, 'y': body, 'w': glint}[ch]
            if ch == 'y' and (x, y) in shade_px:
                c = shade
            img.set(x0 + x, y0 + y, c)


def frame(k):
    img = Img(FW, FH)
    cx, cy, rx, ry = ORBIT
    stars = []
    for i in range(3):
        th = math.radians(k * 30 + i * 120)
        x = cx + rx * math.cos(th)
        y = cy + ry * math.sin(th)
        stars.append((y, x, math.sin(th)))
    # back stars first (smaller, dimmer), front stars on top
    for (y, x, s) in sorted(stars):
        if s < -0.2:
            stamp_star(img, SMALL, int(round(x - 3.5)), int(round(y - 3.5)), TAN, TAN, BRASS, {(4, 3), (5, 3), (4, 4)})
        else:
            stamp_star(img, BIG, int(round(x - 4.5)), int(round(y - 4.5)), YELLOW, WHITE, TAN, BIG_SHADE)
    return img


def strip():
    s = Img(FW * 4, FH)
    for k in range(4):
        s.blit(frame(k), k * FW, 0)
    return s


if __name__ == '__main__':
    st = strip()
    st.save('out/stars_strip.png')
    zoom_save(st, 'out/stars_strip_8x.png', 8)
    import sys
    bg = load(sys.argv[1] if len(sys.argv) > 1 else 'out/bg_s9.png')
    prev = Img(4 * 90, 60)
    for k in range(4):
        tile = bg.crop(ANCHOR[0] - 23, ANCHOR[1] - 10, 90, 60)
        tile.blit(frame(k), 23, 10)
        prev.blit(tile, k * 90, 0)
    zoom_save(prev, 'out/stars_on_bg_6x.png', 6)
