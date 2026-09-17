"""Charge key pose v4: hand-designed part spans (with outline included) + z priority -> label map + flat preview."""
from shapes import *

cv = Canvas()
T = 10


def S(d):
    return span_pixels(d)


# head (same egg as idle, top at y10), in front of the leading shoulder
head = S(merge({T: (28, 35), T + 1: (25, 38), T + 2: (23, 40)}, rng(T + 3, T + 4, (22, 41)), rng(T + 5, T + 14, (21, 42)),
               rng(T + 15, T + 16, (22, 41)), rng(T + 17, T + 18, (23, 40)), {T + 19: (24, 39)}))
cv.add('head', 70, 's', head)
earL = S(merge({19: (19, 21)}, rng(20, 23, (18, 21)), {24: (19, 21), 25: (20, 21)}))
cv.add('earL', 60, 's', earL)
cv.add('earR', 60, 'm', mirror_set(earL))
beard = S(merge(rng(22, 23, [(22, 22), (41, 41)]), rng(24, 25, [(22, 23), (40, 41)]), {26: [(22, 24), (28, 35), (39, 41)]},
                rng(27, 28, (23, 40)), rng(29, 30, (24, 39)), rng(31, 32, (25, 38)), rng(33, 34, (26, 37)),
                {35: (27, 36), 36: (28, 35), 37: (29, 34), 38: (30, 33), 39: (31, 32)}))
cv.add('beard', 80, 'o', beard)

# torso: traps behind head, chest/abs under beard
torso = S(merge({16: (43, 43), 17: [(20, 20), (43, 44)], 18: [(18, 20), (43, 46)], 19: [(15, 18), (44, 48)],
                 20: [(12, 17), (45, 49)]},
                rng(21, 28, (40, 46)), {29: (38, 46), 30: (38, 46), 31: (36, 46), 32: (36, 47), 33: (26, 48), 34: (26, 49)},
                rng(35, 38, (24, 50)), rng(39, 41, (24, 49)), rng(42, 45, (23, 47))))
cv.add('torso', 30, 's', torso)

# leading (screen-left) delt: big round cap, closest to camera
delt = S({21: (10, 17), 22: (8, 19), 23: (7, 20), 24: (6, 21), 25: (5, 22), 26: (5, 22), 27: (5, 22), 28: (4, 23),
          29: (4, 23), 30: (4, 23), 31: (4, 23), 32: (4, 23), 33: (5, 23), 34: (5, 23), 35: (5, 23), 36: (6, 22),
          37: (7, 21), 38: (8, 20), 39: (9, 18)})
cv.add('deltL', 50, 's', delt)
# leading elbow poking down-left, forearm across belly to a fist under the beard
forearm = S({37: (19, 22), 38: (15, 30), 39: (11, 31), 40: (9, 31), 41: (8, 31), 42: (8, 31), 43: (9, 31),
             44: (10, 30), 45: (12, 29), 46: (22, 28)})
cv.add('forearmL', 90, 's', forearm)
fist = S({35: (22, 29), 36: (21, 30), 37: (21, 31)})
cv.add('fistL', 90, 's', fist)

# trailing (screen-right) delt + arm pumped back, fist behind
deltR = S({20: (47, 53), 21: (45, 55), 22: (44, 56), 23: (43, 57), 24: (43, 57), 25: (43, 57), 26: (43, 57),
           27: (43, 57), 28: (43, 57), 29: (43, 57), 30: (44, 57), 31: (45, 58), 32: (46, 58), 33: (48, 59),
           34: (49, 59), 35: (51, 60), 36: (52, 61), 37: (53, 61), 38: (54, 61), 39: (55, 61)})
cv.add('armR', 40, 'm', deltR)
fistR = S({39: (54, 60), 40: (53, 61), 41: (53, 62), 42: (53, 62), 43: (53, 62), 44: (54, 61), 45: (55, 60)})
cv.add('fistR', 45, 'm', fistR)

speedo = S({44: (22, 46), 45: (21, 47), 46: (21, 47), 47: (21, 47), 48: (21, 46), 49: (22, 45), 50: (24, 43), 51: (27, 40)})
cv.add('speedo', 35, 'b', speedo)
# forward (screen-left) leg: knee toward camera, boot lifted
legL = S({48: (20, 32), 49: (19, 33), 50: (18, 33), 51: (18, 33), 52: (18, 33), 53: (18, 32), 54: (19, 31), 55: (20, 30)})
cv.add('legL', 25, 's', legL)
bootL = S({54: (18, 32), 55: (18, 32), 56: (18, 33), 57: (18, 33), 58: (18, 33), 59: (19, 32), 60: (20, 31)})
cv.add('bootL', 20, 'k', bootL)
# back (screen-right) leg pushing off, boot planted
legR = S({49: (33, 45), 50: (34, 46), 51: (35, 46), 52: (35, 46), 53: (36, 46), 54: (36, 46), 55: (37, 46)})
cv.add('legR', 15, 'm', legR)
bootR = S({55: (36, 47), 56: (36, 47), 57: (36, 47), 58: (36, 47), 59: (36, 48), 60: (36, 48), 61: (35, 49),
           62: (35, 49), 63: (35, 49)})
cv.add('bootR', 10, 'k', bootR)

if __name__ == '__main__':
    g = cv.render()
    save_grid(os.path.join(HERE, 'charge_map.txt'), g)
    save(os.path.join(HERE, 'charge_map_8x.png'), zoom(grid_to_pix(g), 8))
    print('ok')
