"""Charge-down key pose block-in: head tucked, leading screen-left shoulder, knee driving at camera."""
from shapes import *

cv = Canvas()

# head tucked: same egg, lowered 10px
HY = 10
head = span_pixels(merge({3 + HY: (28, 35), 4 + HY: (25, 38), 5 + HY: (23, 40)}, rng(6 + HY, 7 + HY, (22, 41)),
                         rng(8 + HY, 17 + HY, (21, 42)), rng(18 + HY, 19 + HY, (22, 41)),
                         rng(20 + HY, 21 + HY, (23, 40)), {22 + HY: (24, 39)}))
cv.add('head', 7, 's', head)
earL = span_pixels(merge({8 + HY: (19, 21)}, rng(9 + HY, 12 + HY, (18, 21)), {13 + HY: (19, 21), 14 + HY: (20, 21)}))
cv.add('earL', 6, 's', earL)
cv.add('earR', 6, 'm', mirror_set(earL))
beard = span_pixels(merge(rng(26, 27, [(22, 22), (41, 41)]), {28: [(22, 23), (40, 41)], 29: [(22, 24), (28, 35), (39, 41)]},
                          rng(30, 31, (23, 40)), rng(32, 33, (24, 39)), {34: (25, 38), 35: (26, 37), 36: (27, 36),
                          37: (28, 35), 38: (29, 34), 39: (30, 33), 40: (31, 32)}))
cv.add('beard', 8, 'o', beard)

torso = [(11, 23), (15, 18), (20, 14), (26, 12), (37, 12), (43, 12), (48, 14), (52, 17), (52, 24), (47, 30),
         (46, 38), (44, 44), (43, 48), (22, 48), (22, 44), (20, 38), (17, 32), (13, 28)]
cv.add('torso', 3, 's', poly_pixels(torso))

delt_lead = [(5, 24), (7, 19), (11, 16), (16, 15), (20, 17), (23, 21), (24, 26), (23, 31), (21, 34), (20, 37),
             (18, 41), (13, 42), (9, 40), (6, 36), (5, 30)]
cv.add('armL', 5, 's', poly_pixels(delt_lead))
forearm_lead = [(14, 38), (20, 36), (26, 36), (30, 37), (31, 41), (30, 45), (25, 46), (19, 44), (15, 43)]
cv.add('forearmL', 9, 's', poly_pixels(forearm_lead))

arm_trail = [(43, 16), (47, 13), (52, 13), (56, 16), (57, 21), (56, 26), (57, 33), (59, 37), (58, 41), (54, 42),
             (51, 39), (49, 33), (46, 29), (43, 24)]
cv.add('armR', 4, 'm', poly_pixels(arm_trail))
fist_trail = [(54, 40), (59, 40), (61, 44), (59, 48), (55, 47), (53, 44)]
cv.add('fistR', 5, 'm', poly_pixels(fist_trail))

speedo = [(22, 47), (43, 46), (44, 50), (40, 53), (35, 54), (29, 54), (25, 53), (21, 50)]
cv.add('speedo', 3, 'b', poly_pixels(speedo))

leg_front = [(33, 50), (44, 48), (46, 52), (46, 57), (44, 59), (35, 59), (33, 55)]
cv.add('legR', 2, 's', poly_pixels(leg_front))
boot_front = [(33, 56), (46, 56), (47, 60), (48, 63), (32, 63), (32, 59)]
cv.add('bootR', 2, 'k', poly_pixels(boot_front))
leg_back = [(21, 50), (31, 51), (31, 55), (29, 57), (21, 57), (20, 54)]
cv.add('legL', 1, 's', poly_pixels(leg_back))
boot_back = [(20, 55), (30, 55), (30, 59), (28, 62), (22, 62), (20, 59)]
cv.add('bootL', 1, 'k', poly_pixels(boot_back))

if __name__ == '__main__':
    g = cv.render()
    save_grid(os.path.join(HERE, 'charge_block.txt'), g)
    save(os.path.join(HERE, 'charge_block_8x.png'), zoom(grid_to_pix(g), 8))
    print('ok')
