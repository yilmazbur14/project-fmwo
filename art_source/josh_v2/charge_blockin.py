"""Charge key-pose block-in v3 (facing right): flat tones + outlines."""
import sys
from jlib import *
import head as HD

HEAD_OFF = (9, 4)
G = dict(
    f_arm=[(32, 29), (24, 26), (15, 23), (11, 22), (10, 27), (15, 29), (23, 32), (30, 35)],
    f_fist=[(3, 22), (6, 19), (11, 19), (13, 22), (12, 27), (7, 28), (3, 26)],
    f_thigh=[(33, 44), (41, 45), (48, 48), (51, 52), (48, 55), (42, 52), (34, 51)],
    f_shin=[(45, 50), (51, 50), (52, 55), (51, 59), (46, 59), (45, 55)],
    f_boot=[(44, 56), (52, 56), (55, 58), (60, 60), (61, 64), (44, 64)],
    torso=[(36, 25), (46, 28), (51, 36), (48, 43), (41, 48), (32, 50), (24, 48), (20, 42), (21, 35), (27, 29)],
    n_leg=[(22, 44), (31, 47), (29, 52), (22, 55), (14, 58), (10, 60), (7, 57), (12, 53), (17, 49)],
    n_boot=[(1, 55), (8, 53), (12, 57), (16, 60), (17, 64), (3, 64), (0, 60)],
    speedo=[(20, 41), (26, 44), (34, 46), (43, 46), (42, 50), (37, 53), (30, 54), (24, 52), (19, 47)],
    n_delt=(52, 34, 7.0, 6.5),
    n_upper=[(46, 36), (54, 38), (54, 44), (51, 47), (46, 46), (45, 41)],
    n_fist=[(47, 43), (53, 42), (56, 45), (55, 49), (51, 50), (47, 48)],
)


def flat(ch):
    return lambda x, y: ch


def build(*_):
    c = blank()
    paint_part(c, poly_mask(G['f_arm']), flat('d'))
    paint_part(c, poly_mask(G['f_fist']), flat('d'))
    paint_part(c, poly_mask(G['f_thigh']), flat('d'))
    paint_part(c, poly_mask(G['f_shin']), flat('d'))
    paint_part(c, poly_mask(G['f_boot']), flat('X'))
    paint_part(c, poly_mask(G['torso']), flat('s'))
    paint_part(c, poly_mask(G['n_leg']), flat('s'))
    paint_part(c, poly_mask(G['n_boot']), flat('X'))
    paint_part(c, poly_mask(G['speedo']), flat('O'))
    hc = blank()
    HD.build_head(hc, 'B')
    hc = shift_canvas(hc, *HEAD_OFF)
    composite(c, hc)
    paint_part(c, poly_mask(G['n_upper']), flat('s'))
    paint_part(c, poly_mask(G['n_fist']), flat('a'))
    paint_part(c, ellipse_mask(*G['n_delt']), flat('a'))
    return c


if __name__ == '__main__':
    c = build()
    save_png(c, os.path.join(OUT, 'charge_blockin.png'))
    preview(c, os.path.join(OUT, 'charge_blockin_8x.png'))
    print('ok')
