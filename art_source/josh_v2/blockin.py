"""Idle block-in v2: traced polygons, flat tones + outlines."""
from jlib import *

G = dict(
    head=[(24, 5), (28, 3), (37, 3), (41, 5), (43, 8), (44, 13), (44, 18), (43, 22), (40, 25), (36, 27),
          (30, 27), (26, 25), (23, 22), (22, 18), (22, 13), (22, 8)],
    near_ear=[(22, 13), (20, 13), (19, 15), (19, 18), (21, 20), (23, 20)],
    hair=[(21, 14), (21, 8), (23, 4), (27, 1), (33, 0), (39, 1), (43, 3), (45, 7), (45, 13), (43, 12),
          (41, 9), (35, 8), (29, 8), (24, 10), (23, 14)],
    body=[(27, 22), (25, 24), (21, 25), (17, 26), (14, 27), (11, 29), (10, 32), (12, 35), (15, 37),
          (17, 40), (20, 44), (22, 47), (44, 47), (45, 44), (46, 40), (47, 37), (50, 35), (53, 31),
          (52, 28), (49, 26), (45, 25), (41, 24), (39, 22)],
    n_upper=[(16, 25), (13, 22), (9, 22), (6, 24), (3, 28), (2, 32), (4, 35), (9, 36), (13, 35), (16, 32)],
    n_fore=[(2, 29), (2, 24), (4, 19), (6, 16), (11, 16), (11, 19), (9, 24), (8, 29), (6, 32), (3, 32)],
    n_fist=[(4, 17), (4, 12), (6, 10), (11, 10), (13, 12), (13, 16), (11, 18), (6, 18)],
    f_upper=[(47, 27), (52, 27), (55, 30), (57, 35), (58, 40), (56, 43), (53, 42), (51, 37), (48, 33)],
    f_fore=[(53, 38), (58, 40), (57, 44), (53, 48), (49, 50), (46, 47), (50, 43)],
    f_fist=[(43, 44), (47, 43), (50, 45), (50, 49), (47, 51), (43, 50)],
    speedo=[(21, 45), (27, 46), (33, 46), (39, 46), (45, 45), (46, 48), (42, 51), (37, 54), (33, 55),
            (29, 54), (24, 51), (20, 48)],
    n_leg=[(21, 47), (31, 51), (30, 55), (28, 58), (17, 58), (17, 52)],
    f_leg=[(35, 51), (45, 47), (48, 52), (49, 58), (38, 58), (36, 55)],
    n_boot=[(16, 55), (29, 55), (29, 63), (12, 63), (12, 60), (15, 58)],
    f_boot=[(37, 55), (50, 55), (51, 58), (53, 61), (53, 63), (37, 63)],
)


def flat(ch):
    return lambda x, y: ch


def build(g=G):
    c = blank()
    paint_part(c, poly_mask(g['n_leg']), flat('s'))
    paint_part(c, poly_mask(g['f_leg']), flat('d'))
    paint_part(c, poly_mask(g['n_boot']), flat('X'))
    paint_part(c, poly_mask(g['f_boot']), flat('X'))
    paint_part(c, poly_mask(g['body']), flat('s'))
    paint_part(c, poly_mask(g['speedo']), flat('p'))
    paint_part(c, poly_mask(g['f_upper']), flat('d'))
    paint_part(c, poly_mask(g['f_fore']), flat('d'))
    paint_part(c, poly_mask(g['f_fist']), flat('s'))
    paint_part(c, poly_mask(g['n_upper']), flat('a'))
    paint_part(c, poly_mask(g['n_fore']), flat('s'))
    paint_part(c, poly_mask(g['n_fist']), flat('a'))
    paint_part(c, poly_mask(g['near_ear']), flat('d'))
    paint_part(c, poly_mask(g['head']), flat('s'))
    paint_part(c, poly_mask(g['hair']), flat('h'))
    return c


if __name__ == '__main__':
    c = build()
    save_png(c, os.path.join(OUT, 'blockin.png'))
    preview(c, os.path.join(OUT, 'blockin_8x.png'))
    print('ok')
