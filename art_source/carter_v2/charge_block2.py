"""Charge-down key pose block-in v2: head forward & prominent, traps below head line."""
from shapes import *

cv = Canvas()
T = 8  # head top
def hs(rows):
    return {T + r: v for r, v in rows.items()}
head = span_pixels(merge(hs({0: (28, 35), 1: (25, 38), 2: (23, 40)}), hs(rng(3, 4, (22, 41))), hs(rng(5, 14, (21, 42))),
                         hs(rng(15, 16, (22, 41))), hs(rng(17, 18, (23, 40))), hs({19: (24, 39)})))
cv.add('head', 7, 's', head)
earL = span_pixels(merge({15: (19, 21)}, rng(16, 19, (18, 21)), {20: (19, 21), 21: (20, 21)}))
cv.add('earL', 6, 's', earL)
cv.add('earR', 6, 'm', mirror_set(earL))
beard = span_pixels(merge(rng(20, 21, [(22, 22), (41, 41)]), {22: [(22, 23), (40, 41)], 23: [(22, 24), (39, 41)],
                          24: [(22, 24), (28, 35), (39, 41)]}, rng(25, 26, (23, 40)), rng(27, 28, (24, 39)),
                          rng(29, 30, (25, 38)), {31: (26, 37), 32: (27, 36), 33: (28, 35), 34: (29, 34), 35: (30, 33), 36: (31, 32)}))
cv.add('beard', 8, 'o', beard)

torso = [(14, 24), (18, 19), (23, 17), (40, 17), (46, 18), (50, 21), (51, 27), (47, 32), (46, 38), (44, 44), (43, 48),
         (22, 48), (22, 44), (20, 38), (18, 33), (15, 29)]
cv.add('torso', 3, 's', poly_pixels(torso))
delt = [(6, 28), (8, 23), (12, 20), (17, 19), (21, 21), (23, 25), (23, 30), (21, 34), (18, 37), (13, 38), (9, 36), (6, 33)]
cv.add('deltL', 5, 's', poly_pixels(delt))
elbow = [(9, 35), (17, 36), (18, 41), (14, 43), (10, 42), (8, 39)]
cv.add('elbowL', 4, 's', poly_pixels(elbow))
forearm = [(15, 38), (22, 37), (28, 38), (31, 41), (30, 45), (25, 46), (18, 45), (14, 42)]
cv.add('forearmL', 9, 's', poly_pixels(forearm))
deltR = [(43, 20), (46, 17), (51, 17), (55, 20), (56, 25), (55, 29), (51, 31), (46, 30), (43, 26)]
cv.add('deltR', 5, 'm', poly_pixels(deltR))
armR = [(50, 28), (55, 27), (58, 33), (59, 38), (56, 40), (52, 37), (49, 32)]
cv.add('armR', 4, 'm', poly_pixels(armR))
fistR = [(54, 38), (59, 37), (61, 41), (60, 45), (56, 46), (53, 43)]
cv.add('fistR', 5, 'm', poly_pixels(fistR))
speedo = [(22, 47), (43, 46), (44, 50), (40, 53), (35, 54), (29, 54), (25, 53), (21, 50)]
cv.add('speedo', 3, 'b', poly_pixels(speedo))
cv.add('legR', 2, 's', poly_pixels([(33, 50), (44, 48), (46, 52), (46, 57), (44, 59), (35, 59), (33, 55)]))
cv.add('bootR', 2, 'k', poly_pixels([(33, 57), (46, 57), (47, 60), (48, 63), (32, 63), (32, 60)]))
cv.add('legL', 1, 's', poly_pixels([(21, 50), (31, 51), (31, 55), (29, 57), (21, 57), (20, 54)]))
cv.add('bootL', 1, 'k', poly_pixels([(20, 55), (30, 55), (30, 58), (29, 61), (22, 61), (20, 58)]))

if __name__ == '__main__':
    g = cv.render()
    save_grid(os.path.join(HERE, 'charge_block2.txt'), g)
    save(os.path.join(HERE, 'charge_block2_8x.png'), zoom(grid_to_pix(g), 8))
    print('ok')
