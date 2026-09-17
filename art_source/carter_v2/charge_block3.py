"""Charge-down key pose block-in v3: compressed lean, left shoulder + left knee drive, right leg pushes off."""
from shapes import *

cv = Canvas()
T = 10
def hs(rows):
    return {T + r: v for r, v in rows.items()}
head = span_pixels(merge(hs({0: (28, 35), 1: (25, 38), 2: (23, 40)}), hs(rng(3, 4, (22, 41))), hs(rng(5, 14, (21, 42))),
                         hs(rng(15, 16, (22, 41))), hs(rng(17, 18, (23, 40))), hs({19: (24, 39)})))
cv.add('head', 7, 's', head)
earL = span_pixels(merge({17: (19, 21)}, rng(18, 21, (18, 21)), {22: (19, 21), 23: (20, 21)}))
cv.add('earL', 6, 's', earL)
cv.add('earR', 6, 'm', mirror_set(earL))
B = T + 12  # beard rows start
beard = span_pixels(merge(rng(22, 23, [(22, 22), (41, 41)]), {24: [(22, 23), (40, 41)], 25: [(22, 24), (39, 41)],
                          26: [(22, 24), (28, 35), (39, 41)]}, rng(27, 28, (23, 40)), rng(29, 30, (24, 39)),
                          {31: (25, 38), 32: (26, 37), 33: (27, 36), 34: (28, 35), 35: (29, 34), 36: (30, 33), 37: (31, 32)}))
cv.add('beard', 8, 'o', beard)

torso = [(15, 27), (19, 22), (24, 20), (39, 20), (45, 21), (50, 24), (51, 29), (47, 34), (45, 40), (43, 45),
         (22, 45), (21, 40), (19, 35), (16, 31)]
cv.add('torso', 3, 's', poly_pixels(torso))
delt = [(5, 31), (7, 26), (11, 23), (16, 22), (21, 24), (23, 28), (23, 33), (21, 37), (17, 40), (12, 40), (8, 38), (5, 35)]
cv.add('deltL', 5, 's', poly_pixels(delt))
elbow = [(7, 37), (15, 38), (16, 43), (12, 45), (8, 44), (6, 41)]
cv.add('elbowL', 4, 's', poly_pixels(elbow))
forearm = [(12, 40), (18, 38), (24, 35), (29, 35), (31, 38), (31, 42), (27, 44), (21, 44), (15, 45), (11, 44)]
cv.add('forearmL', 9, 's', poly_pixels(forearm))
deltR = [(43, 23), (46, 20), (51, 20), (55, 23), (56, 28), (54, 32), (50, 33), (46, 32), (43, 28)]
cv.add('deltR', 5, 'm', poly_pixels(deltR))
armR = [(50, 30), (55, 28), (59, 33), (61, 38), (58, 40), (54, 37), (50, 34)]
cv.add('armR', 4, 'm', poly_pixels(armR))
fistR = [(56, 37), (60, 36), (62, 40), (61, 44), (57, 45), (55, 42)]
cv.add('fistR', 5, 'm', poly_pixels(fistR))
speedo = [(22, 44), (43, 44), (44, 48), (40, 51), (35, 52), (29, 52), (24, 51), (21, 48)]
cv.add('speedo', 4, 'b', poly_pixels(speedo))
# forward (screen-left) leg: knee up toward camera, boot lifted
cv.add('legL', 3, 's', poly_pixels([(21, 47), (31, 48), (32, 52), (31, 56), (27, 57), (20, 56), (18, 52)]))
cv.add('bootL', 2, 'k', poly_pixels([(19, 54), (31, 54), (32, 58), (30, 61), (21, 61), (18, 58)]))
# back (screen-right) leg: pushing off, boot planted
cv.add('legR', 1, 'm', poly_pixels([(33, 48), (43, 47), (45, 52), (46, 56), (37, 57), (34, 53)]))
cv.add('bootR', 1, 'k', poly_pixels([(36, 55), (46, 55), (47, 59), (48, 63), (35, 63), (35, 59)]))

if __name__ == '__main__':
    g = cv.render()
    save_grid(os.path.join(HERE, 'charge_block3.txt'), g)
    save(os.path.join(HERE, 'charge_block3_8x.png'), zoom(grid_to_pix(g), 8))
    print('ok')
