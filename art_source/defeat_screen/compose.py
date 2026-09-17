"""Assemble the defeat background. python compose.py [tag]"""
import sys
from lib import *
import scene
import props
import player as pl
from scene import W, H, FAR_Y, side_l, side_r
from crowd import crowd_rows, face

FAR_ROWS = [
    (50, 6, 'night', 13),
    (63, 7, 'night', 15),
    (77, 8, 'deep', 17),
    (91, 9, 'dim', 19),
    (106, 10, 'dim', 21),
    (119, 11, 'dim', 24),
]

DARKER = {BROWN: BROWN_D, BROWN_D: PLUM, PLUM: NAVY, NAVY: K, GREY_D: PLUM, GREY: GREY_D,
          TAN: BROWN, INDIGO: NAVY, BLUE_D: NAVY, RED: BROWN_D}


def fade_top(img, y0, y1):
    """dithered fade to darkness above y1 (fully dark above y0)"""
    for y in range(0, y1):
        t = 1.0 if y < y0 else (y1 - y) / float(y1 - y0)
        for x in range(W):
            if t > bayer(x, y):
                c = img.get(x, y)
                img.set(x, y, DARKER.get(c, K))

PLAYER_AT = (262, 131)


def side_crowd(img):
    rows = [(132, 10, 'deep', 21), (154, 11, 'deep', 23), (180, 12, 'dim', 25), (208, 13, 'deep', 27),
            (240, 14, 'dim', 29)]
    crowd_rows(img, rows, seed=21, x0=-14, x1=70, clip=lambda x, y: x < side_l(y) + 4)
    crowd_rows(img, rows, seed=33, x0=572, x1=660, clip=lambda x, y: x > side_r(y) - 4)


def player_layer():
    img, owner, union = pl.build('pl')
    pl.details(img, 'pl')
    return img, union


def cast_shadow(im, union, ox, oy, off=(3, 3)):
    for (x, y) in union:
        X, Y = ox + x + off[0], oy + y + off[1]
        c = im.get(X, Y)
        if c == OLIVE:
            im.set(X, Y, GREEN_D)
        elif c == GREEN_D:
            im.set(X, Y, SLATE)
        elif c == SLATE:
            im.set(X, Y, NAVY)


def build(tag=''):
    im = Img(W, H)
    scene.backdrop(im)
    crowd_rows(im, FAR_ROWS[:3], seed=5)
    crowd_rows(im, FAR_ROWS[3:], seed=6, spill=(320, 110))
    fade_top(im, 46, 72)
    props.sign(im, 188, 58, 'GG EZ', card=GREY_L, shade=GREY)
    props.sign(im, 458, 54, 'L', card=GREY_L, shade=GREY)
    side_crowd(im)
    scene.canvas(im)
    scene.ropes_side(im)
    scene.ropes_far(im)
    scene.posts(im)
    # player + his cast shadow
    pimg, union = player_layer()
    ox, oy = PLAYER_AT
    cast_shadow(im, union, ox, oy)
    for (x, y) in union | outline_of(union):
        c = pimg.get(x, y)
        if c is not None:
            im.set(ox + x, oy + y, c)
    # looming boss shadow
    sm = props.boss_shadow_mask(522, 178, 1.75, 1.9, 0.25)
    props.apply_shadow(im, sm)
    # pennants
    props.pennant(im, 20, 6, 52, 64, props.pennant_icon)
    props.pennant(im, 568, 6, 52, 64, props.pennant_channel)
    return im


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'wip'
    im = build(tag)
    im.save('out/bg_%s.png' % tag)
    zoom_save(im, 'out/bg_%s_2x.png' % tag, 2)
    print('non-db32:', im.check_db32())
