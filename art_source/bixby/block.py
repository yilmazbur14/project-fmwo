"""Stage 1: silhouette blocking v2. Flat colours per part, outlines per part."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from canvas import *

PAL = {
    'K': '#000000',
    't': '#C8793A',  # tan (head)
    'w': '#EDE6DA',  # white
    'k': '#34303C',  # black coat
    'b': '#5A3420',  # ear
    'r': '#AC3232',  # collar
    'n': '#20181A',  # nose
}

g = blank()

# ---- tail (back-most): rises from the rump, curls forward at the tip
tail = mask_tube([(10, 39), (6, 34), (3.5, 27), (3.5, 20), (5.5, 14), (9, 10)], (3.4, 2.0))
paint_part(g, tail, 'k')

# ---- far legs (higher on screen = further away)
far_hind = mask_poly([(20, 47), (27, 47), (26, 54), (27, 58), (29, 61), (20, 61), (21, 55)])
paint_part(g, far_hind, 'w')
far_front = mask_poly([(40, 47), (47, 47), (46, 55), (47, 60), (39, 60), (40, 55)])
paint_part(g, far_front, 'w')

# ---- body + near legs as one silhouette
body = mask_poly([
    (6, 38), (12, 34), (22, 33), (34, 32), (44, 30), (51, 30), (56, 33), (59, 38),
    (59, 45), (56, 50),
    (55, 56), (57, 63), (46, 63), (47, 56), (46, 51),   # near front leg
    (38, 51), (28, 50), (19, 50),
    (17, 54), (17, 58), (19, 63), (8, 63), (9, 58), (7, 53),  # near hind leg
    (4, 48), (3, 43)])
paint_part(g, body, 'k')

# ---- necks + collars
def neck(pts, collar_pts):
    paint_part(g, mask_poly(pts), 'w')
    paint_part(g, mask_poly(collar_pts), 'r')

neck([(12, 20), (22, 20), (27, 36), (16, 37)], [(13.5, 26), (23.5, 25), (25, 30), (14.5, 31)])
neck([(42, 19), (52, 19), (50, 36), (39, 35)], [(41, 25), (51.5, 26), (50.5, 31), (40, 30)])
neck([(26, 16), (38, 16), (39, 34), (25, 34)], [(25.5, 23), (38.5, 23), (38.5, 27), (25.5, 27)])

def head(cx, cy, rx, ry, ear_dx, ear_dy, ear_rx, ear_ry, muzzle):
    for s in (-1, 1):
        ear = mask_ellipse(cx + s * ear_dx, cy + ear_dy, ear_rx, ear_ry)
        paint_part(g, ear, 'b')
    skull = mask_ellipse(cx, cy, rx, ry)
    mz = mask_ellipse(*muzzle)
    paint_part(g, skull | mz, 't')

# left head (turned left), right head (turned right), centre (front)
head(17, 14, 7.5, 7.0, 6.5, 5, 2.6, 6.5, (14.0, 18.5, 5.5, 4.0))
head(49, 13, 7.5, 7.0, 6.5, 5, 2.6, 6.5, (52.0, 17.5, 5.5, 4.0))
head(32, 10, 9.0, 8.5, 8.2, 5, 3.0, 8.0, (32.0, 15.5, 5.5, 4.5))

save_rows(os.path.join(HERE, 'block.txt'), g)
save_png(os.path.join(HERE, 'block_8x.png'), g, PAL, 8, bg='checker')
save_png(os.path.join(HERE, 'block_3x.png'), g, PAL, 3, bg='checker')
print('ok')
