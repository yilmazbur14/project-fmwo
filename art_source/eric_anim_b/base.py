"""Part-B base: designer A's rig (snapshot in a_snap/) + part-B helpers."""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'a_snap'))
sys.path.insert(1, HERE)

import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT
import rig as arig          # designer A rig (snapshot)
import fx as afx            # designer A fx (snapshot)
import variants as V
import approved_weapon as AW
import bfx
from sword import Sword
import arms as BA
from pngio import write_png, read_png, scale, blank, paste, crop

FL = (136, 180, 99, 255)
GROUND = (104, 140, 76, 255)
APPROVED = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_sword.png'


def w128():
    lib.W = lib.H = 128


def cv(fr):
    w128()
    return fr.as_canvas()


def body(fr, upper=(0, 0), shoulders=(0, 0), headx=(0, 0), cape=None, torso=None, skip=(), extra=None,
         hooks=None, off=None):
    ex = dict(extra or {})
    if cape is not None:
        ex['cape'] = V.cape_layer(*cape)
    if torso is not None:
        ex['torso'] = V.torso_layer(*torso)
    o = {'upper': upper, 'shoulders': shoulders, 'headx': headx}
    o.update(off or {})
    arig.compose_body(fr, o, skip=skip, extra=ex, hooks=hooks)
    w128()


def head_img(kind=None):
    return afx.head_variant(kind) if kind else arig.layers()['head']


def head_put(fr, upper=(0, 0), shoulders=(0, 0), headx=(0, 0), kind=None, img=None):
    im = img if img is not None else head_img(kind)
    fr.put(im, upper[0] + shoulders[0] + headx[0], upper[1] + shoulders[1] + headx[1])


def upper_arm(fr, s, e, w=11):
    arig.limb(fr, s, e, w, ramp='chain')
    w128()


def fore_arm(fr, e, h, w=11):
    arig.limb(fr, e, h, w, ramp='plate')
    arig.cop(fr, e, 5.6, 5.4)
    w128()


def fist(fr, c, vertical=True, shadow=True):
    arig.fist(fr, c[0], c[1], vertical=vertical, shadow=shadow)


def hand(fr, name, c, flip=False, shadow=True):
    """part-B hand stamps (open hands etc.)"""
    BA.hand(cv(fr), name, c, flip=flip, shadow=shadow)


def sword_at(fr, hand_xy, ang, sa=1.0, sb=1.0, grip_a=-10.0, parts=('blade', 'grip', 'pommel', 'guard')):
    w128()
    a = math.radians(ang)
    u = (math.cos(a), math.sin(a))
    o = (hand_xy[0] - u[0] * grip_a * sa, hand_xy[1] - u[1] * grip_a * sa)
    S = Sword(o, ang, sa, sb)
    if parts:
        S.draw(cv(fr), parts=parts)
    return S


def rgba_on(px, bg=FL):
    return [[(p if p[3] else bg) for p in row] for row in px]


def strip(imgs, s, path, pad=6, ground=True, labels=None):
    fw = 128 * s
    Wd = pad + len(imgs) * (fw + pad)
    Ht = fw + 2 * pad
    canvas = blank(Wd, Ht, FL)
    if ground:
        for y in range(pad + fw, Ht):
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
