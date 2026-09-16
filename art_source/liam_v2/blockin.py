from lib import *

cv = blank_chars()

def part(mask, ch):
    paint_mask(cv, mask, lambda x, y: ch)
    paint_outline(cv, mask)

# ---- headband tails (behind everything)
tail1 = poly_mask([(40, 12), (44, 12), (48, 19), (52, 26), (49, 27), (45, 21), (41, 16)])
tail2 = poly_mask([(39, 14), (42, 14), (45, 21), (47, 29), (44, 29), (42, 22), (39, 17)])
part(tail2, 'y'); part(tail1, 'T')

# ---- legs
far_leg = poly_mask([(17, 47), (31, 47), (30, 51), (26, 55), (24, 58), (10, 58), (13, 53)])
near_leg = poly_mask([(32, 47), (48, 47), (49, 52), (49, 58), (36, 58), (35, 55), (33, 51)])
far_shoe = poly_mask([(9, 57), (24, 57), (25, 63), (4, 63), (4, 61), (6, 59)])
near_shoe = poly_mask([(35, 57), (50, 57), (54, 60), (55, 63), (35, 63)])
part(far_leg, 'q'); part(near_leg, 'q')
part(far_shoe, 'O'); part(near_shoe, 'O')

# ---- far arm (viewer-left) hanging, behind torso edge
far_up = capsule_mask(16, 31, 11, 40, 4.4)
far_fore = capsule_mask(11, 40, 9, 48, 3.7)
part(m_or(far_up, far_fore), 'J')
far_fist = ellipse_mask(9, 49.5, 3.6, 3.4)
part(far_fist, 's')

# ---- torso egg
torso = poly_mask([(21, 24), (37, 24), (43, 26), (47, 29), (50, 34), (52, 40), (51, 45), (48, 49),
                   (17, 49), (14, 45), (13, 40), (14, 34), (17, 28)])
part(torso, 'J')
belt = m_and(torso, poly_mask([(0, 45), (63, 44), (63, 48), (0, 49)]))
paint_mask(cv, belt, lambda x, y: 'N')
paint_outline(cv, torso)
plate = poly_mask([(27, 44), (34, 44), (34, 49), (27, 49)])
part(plate, 'M')

# ---- near arm (viewer-right) akimbo
near_up = capsule_mask(46, 31, 56, 39, 4.4)
near_fore = capsule_mask(56, 39, 49, 45, 3.7)
part(m_or(near_up, near_fore), 'J')
near_fist = ellipse_mask(48.5, 45.5, 3.7, 3.3)
part(near_fist, 's')

# ---- collar + tie
collar_f = poly_mask([(21, 24), (28, 26), (25, 31), (18, 28)])
collar_n = poly_mask([(31, 26), (39, 24), (44, 28), (35, 32)])
part(collar_f, 'W'); part(collar_n, 'W')
tie = poly_mask([(27, 26), (31, 26), (32, 30), (32, 37), (30, 41), (28, 42), (26, 39), (26, 31)])
part(tie, 'T')

# ---- head
skull = ellipse_mask(29.5, 16, 10, 10.5)
part(skull, 's')
beard = poly_mask([(19, 18), (40, 17), (40, 22), (37, 26), (32, 28), (26, 28), (22, 26), (19, 22)])
part(beard, 'h')
hair = poly_mask([(18, 15), (17, 10), (19, 6), (24, 4), (31, 3), (37, 5), (41, 9), (42, 14), (41, 19), (39, 15), (21, 12)])
part(hair, 'h')
band = m_and(poly_mask([(17, 10), (42, 11), (42, 14), (17, 13)]), m_or(skull, hair))
part(band, 'T')
bplate = poly_mask([(22, 10), (29, 10), (29, 14), (22, 14)])
part(bplate, 'M')
# glasses
put(cv, 19, 15, '########.#######')
put(cv, 19, 16, '#LLLLL####LLLLLL#')
put(cv, 19, 17, '#LLLLL#..#LLLLLL#')
put(cv, 19, 18, '.#####....######')
put(cv, 22, 22, '#WWWWWWWWWW#')

open('blockin.txt', 'w').write(to_text(cv))
preview(cv, 'out/blockin_8x.png')
print('ok')
