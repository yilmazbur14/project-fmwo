"""Extent blockouts of the most demanding planned poses at the new proportions (not final art):
bounding boxes decide the uniform frame size."""
import sys
import math
import pose as P
import poses
from pngio import write_png, scale, blank, paste

W, H = 256, 192


def heave():
    fr = P.Big(W, H)
    P.body(fr, skip=('armR_front',))
    P.limb(fr, (104, 146), (100, 132), 9)
    P.sword(fr, (100, 128), (0.0, -1.0))          # blade straight up beside the shoulder
    P.fist(fr, 100, 134)
    return fr


def hoist():
    fr = P.Big(W, H)
    P.body(fr, skip=('armR_front',))
    P.limb(fr, (106, 144), (98, 118), 9)
    P.limb(fr, (150, 144), (158, 124), 9)
    P.sword(fr, (104, 108), (1.0, 0.0))           # horizontal overhead
    P.fist(fr, 96, 108, horizontal=True)
    P.fist(fr, 158, 121)
    return fr


def throw_windup():
    fr = P.Big(W, H)
    P.body(fr, skip=('armR_front',))
    P.limb(fr, (150, 146), (156, 128), 9)
    P.sword(fr, (146, 118), (-0.55, -0.83))       # cocked back over the right shoulder, tip up-left
    P.fist(fr, 152, 126)
    return fr


def planted():
    fr = P.Big(W, H)
    P.body(fr)
    P.sword(fr, (90, 66), (0.0, 1.0), blade_len=118)   # planted point-down beside him, grip high
    P.fist(fr, 90, 56)
    return fr


def bearhug_lunge():
    fr = P.Big(W, H)
    P.body(fr, skip=('armR_front',))
    for sgn in (-1, 1):
        P.limb(fr, (128 + sgn * 22, 146), (128 + sgn * 52, 134), 9)
        P.fist(fr, 128 + sgn * 56, 132)
    return fr


if __name__ == '__main__':
    items = [('idle', poses.base_idle()), ('whirl_wide', poses.whirl_wide()), ('heave', heave()),
             ('hoist', hoist()), ('throw_windup', throw_windup()), ('planted', planted()),
             ('bearhug_lunge', bearhug_lunge())]
    out = blank(len(items) * (W + 4), H, (40, 40, 40, 255))
    need = [W, 0, 0, H]
    for k, (name, fr) in enumerate(items):
        px = fr.rgba()
        xs = [x for y in range(H) for x in range(W) if px[y][x][3]]
        ys = [y for y in range(H) for x in range(W) if px[y][x][3]]
        print('%-14s bbox x %3d..%3d  y %3d..%3d  -> height above ground %d, half-width from centre %d'
              % (name, min(xs), max(xs), min(ys), max(ys), H - min(ys), max(128 - min(xs), max(xs) + 1 - 128)))
        paste(out, P.to_bg(px), k * (W + 4), 0)
    z = scale(out, 1)
    write_png('fit_blocks.png', len(z[0]), len(z), z)
