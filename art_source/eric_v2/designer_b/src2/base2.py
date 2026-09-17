"""Part-B v2 base: designer A's rig2 (snapshot in a_prop/) + helpers."""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'a_prop'))
sys.path.insert(1, HERE)

import rig2 as R
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT, hexc, RAMPS
from pngio import write_png, read_png, scale, blank, paste, crop

FW, FH = 256, 192
FL = (136, 180, 99, 255)
GROUND = (104, 140, 76, 255)
APPROVED = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_v2.png'


def wf():
    lib.W, lib.H = FW, FH


def cv(fr):
    return fr.canvas()


def rgba_on(px, bg=FL):
    return [[(p if p[3] else bg) for p in row] for row in px]


def layer_rgba(px96):
    return [[(p if p is not None else (0, 0, 0, 0)) for p in row] for row in px96]


def strip(imgs, s, path, pad=6, ground=True):
    fw, fh = FW * s, FH * s
    Wd = pad + len(imgs) * (fw + pad)
    Ht = fh + 2 * pad
    canvas = blank(Wd, Ht, FL)
    if ground:
        for y in range(pad + fh, Ht):
            for x in range(Wd):
                canvas[y][x] = GROUND
    for k, im in enumerate(imgs):
        paste(canvas, scale(im, s), pad + k * (fw + pad), pad)
    write_png(path, Wd, Ht, canvas)


def zoom(px, s, path, region=None):
    if region:
        px = crop(px, *region)
    z = scale(rgba_on(px), s)
    write_png(path, len(z[0]), len(z), z)


def approved_px():
    return read_png(APPROVED)[2]
