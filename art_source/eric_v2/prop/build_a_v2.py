"""Render designer-A v2 frames -> ../part_a_v2.png (40 x 256x192 strip, only A indices), previews, gifs."""
import sys
import os
import pickle
import importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rig2 as R
import frames_v2
from pngio import write_png, blank, paste, scale, crop
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'anim'))
from gifio import write_gif

FL = (136, 180, 99, 255)
GROUND = (104, 140, 76, 255)
A = list(range(0, 13)) + list(range(21, 32))
FW, FH = R.FW, R.FH


def on_bg(px):
    return [[(p if p[3] else FL) for p in row] for row in px]


def render(indices):
    return {i: frames_v2.FRAMES[i]().rgba() for i in indices}


def strip(imgs, order, s, path, pad=6):
    W = pad + len(order) * (FW * s + pad)
    Hh = FH * s + 2 * pad
    cv = blank(W, Hh, FL)
    for y in range(pad + FH * s, Hh):
        for x in range(W):
            cv[y][x] = GROUND
    for k, i in enumerate(order):
        paste(cv, scale(imgs[i], s), pad + k * (FW * s + pad), pad)
    write_png(path, W, Hh, cv)


def gif(imgs, order, durations, path, s=2):
    fr = [scale(on_bg(imgs[i]), s) for i in order]
    write_gif(path, [[[p[:3] for p in row] for row in f] for f in fr], [max(2, int(round(d * 100))) for d in durations])


if __name__ == '__main__':
    only = [int(a) for a in sys.argv[1].split(',')] if len(sys.argv) > 1 else A
    imgs = render(only)
    os.makedirs(os.path.join(HERE, 'v2prev'), exist_ok=True)
    if only == A:
        sheet = blank(40 * FW, FH, (0, 0, 0, 0))
        for i in A:
            paste(sheet, imgs[i], i * FW, 0)
        write_png(os.path.join(os.path.dirname(HERE), 'part_a_v2.png'), 40 * FW, FH, sheet)
        pickle.dump(imgs, open(os.path.join(HERE, 'v2prev', 'frames_a_v2.pkl'), 'wb'))
        os.makedirs(os.path.join(HERE, 'v2prev', 'views8x'), exist_ok=True)
        for i, px in imgs.items():
            write_png(os.path.join(HERE, 'v2prev', 'views8x', 'f%02d_8x.png' % i), FW * 8, FH * 8, scale(on_bg(px), 8))
        strip(imgs, list(range(0, 13)), 3, os.path.join(HERE, 'v2prev', 'strip3x_eq.png'))
        strip(imgs, list(range(21, 32)), 3, os.path.join(HERE, 'v2prev', 'strip3x_idle_down.png'))
        eq_t = [0.16666667] + [0.08333333] * 10
        gif(imgs, list(range(0, 11)), eq_t, os.path.join(HERE, 'v2prev', 'gif_earthquake.gif'))
        gif(imgs, [11, 12, 21], [0.0833, 0.0833, 0.25], os.path.join(HERE, 'v2prev', 'gif_post_slam.gif'))
        gif(imgs, [21, 22, 23, 24], [0.25] * 4, os.path.join(HERE, 'v2prev', 'gif_idle.gif'))
        gif(imgs, [21, 22, 23, 24, 25, 26, 21, 22, 23, 24], [0.25] * 10, os.path.join(HERE, 'v2prev', 'gif_idle_variants.gif'))
        gif(imgs, [27, 28, 29, 30, 31], [0.2] * 5, os.path.join(HERE, 'v2prev', 'gif_downed.gif'))
        print('wrote part_a_v2.png and previews')
    else:
        strip(imgs, only, 2, os.path.join(HERE, 'v2prev', 'preview.png'))
        print('preview', only)
