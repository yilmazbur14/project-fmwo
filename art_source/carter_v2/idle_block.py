"""Idle block-in v2: polygon silhouette."""
from shapes import *

cv = Canvas()

# head: egg, widest at the temples, tapering jaw
head = span_pixels(merge({3: (28, 35), 4: (25, 38), 5: (23, 40)}, rng(6, 7, (22, 41)), rng(8, 16, (21, 42)),
                         {17: (21, 42)}, rng(18, 19, (22, 41)), rng(20, 21, (23, 40)), {22: (24, 39)}))
cv.add('head', 7, 's', head)

earL = span_pixels(merge({13: (19, 21)}, rng(14, 17, (18, 21)), {18: (19, 21), 19: (20, 21)}))
cv.add('earL', 6, 's', earL)
cv.add('earR', 6, 'm', mirror_set(earL))

beard = span_pixels(merge(rng(15, 16, [(22, 22), (41, 41)]), rng(17, 18, [(22, 23), (40, 41)]),
                          {19: [(22, 24), (28, 35), (39, 41)]}, rng(20, 21, (23, 40)), rng(22, 23, (24, 39)),
                          rng(24, 25, (25, 38)), {26: (26, 37), 27: (26, 37), 28: (27, 36), 29: (28, 35),
                                                  30: (29, 34), 31: (30, 33), 32: (31, 32)}))
cv.add('beard', 8, 'o', beard)

# torso incl. neck + traps (symmetric)
torsoL = [(25, 17), (24, 20), (19, 22), (15, 24), (12, 26), (12, 29), (17, 31), (17, 34), (20, 39), (22, 42), (22, 48)]
torso = torsoL + list(reversed(mirror_pts(torsoL)))
cv.add('torso', 3, 's', poly_pixels(torso))

# screen-left arm: hangs bowed out, fist clenched by the thigh
armL = [(12, 25), (15, 24), (18, 25), (20, 28), (20, 32), (17, 37), (16, 40), (17, 43), (19, 45), (20, 47), (20, 51), (18, 53), (14, 53), (12, 51), (12, 47), (11, 44), (9, 41), (8, 38), (8, 33), (9, 29), (10, 27)]
cv.add('armL', 5, 's', poly_pixels(armL))

# screen-right arm: elbow out, fist planted on the hip
armR = [(51, 25), (48, 24), (45, 25), (43, 28), (44, 32), (48, 38), (45, 42), (42, 43), (39, 43), (39, 48), (42, 49), (46, 48), (52, 45), (55, 40), (56, 35), (55, 30), (53, 27)]
cv.add('armR', 5, 'm', poly_pixels(armR))

speedo = [(22, 43), (41, 43), (42, 47), (38, 50), (34, 51), (29, 51), (25, 50), (21, 47)]
cv.add('speedo', 4, 'b', poly_pixels(speedo))

legL = [(22, 45), (31, 46), (31, 51), (29, 53), (28, 56), (19, 56), (19, 52), (21, 48)]
legR = [(32, 46), (41, 45), (42, 48), (44, 52), (44, 56), (35, 56), (34, 53), (32, 51)]
cv.add('legL', 1, 's', poly_pixels(legL))
cv.add('legR', 1, 'm', poly_pixels(legR))

bootL = [(18, 54), (29, 54), (29, 63), (15, 63), (16, 61), (17, 58)]
bootR = [(34, 54), (45, 54), (45, 58), (47, 61), (48, 63), (34, 63)]
cv.add('bootL', 2, 'k', poly_pixels(bootL))
cv.add('bootR', 2, 'k', poly_pixels(bootR))

if __name__ == '__main__':
    g = cv.render()
    save_grid(os.path.join(HERE, 'idle_block.txt'), g)
    save(os.path.join(HERE, 'idle_block_8x.png'), zoom(grid_to_pix(g), 8))
    print('ok')
