"""Knocked-out player lying on his back, seen from above (feet toward camera).
Each part = mask + height function. Normals from the height field are lit and
quantised to a 4-tone ramp, then outlined and hand-detailed.
python player.py [pl|db]"""
import math
import sys
from lib import *

SW, SH = 116, 108
LIGHT = norm3(-0.42, -0.55, 0.72)

SKIN = [SKIN_L, TAN, BROWN, BROWN_D]          # hi, base, shade, deep
BLUE_DB = [BLUE_L, BLURPLE, INDIGO, NAVY]
BLUE_PL = ['3883c9', '2464bd', '162fbb', NAVY]   # the player's own sprite blues
REDR = [RED_L, RED, BROWN_D, PLUM]
SHOE = [GREY_D, NAVY, K, K]
HAIR = [INDIGO, NAVY, K, K]


# ---------------------------------------------------------------- height fns
def h_ellipsoid(cx, cy, rx, ry, hz):
    def f(x, y):
        u = (x + 0.5 - cx) / rx
        v = (y + 0.5 - cy) / ry
        q = 1 - u * u - v * v
        return hz * math.sqrt(q) if q > 0 else 0.0
    return f


def h_capsule(ax, ay, bx, by, ra, rb, flat=1.0):
    def f(x, y):
        d, _, _, t = dist_to_seg(x + 0.5, y + 0.5, ax, ay, bx, by)
        r = ra + (rb - ra) * t
        q = r * r - d * d
        return flat * math.sqrt(q) if q > 0 else 0.0
    return f


def h_sum(*fs):
    return lambda x, y: sum(f(x, y) for f in fs)


def h_max(*fs):
    return lambda x, y: max(f(x, y) for f in fs)


def light_at(h, x, y, L=None):
    L = L or LIGHT
    gx = (h(x + 1, y) - h(x - 1, y)) / 2.0
    gy = (h(x, y + 1) - h(x, y - 1)) / 2.0
    n = norm3(-gx, -gy, 1.0)
    return n[0] * L[0] + n[1] * L[1] + n[2] * L[2]


FACE_LIGHT = norm3(-0.45, -0.2, 0.87)


def shade(img, mask, h, ramp, th=(0.93, 0.53, 0.28), L=None):
    for (x, y) in mask:
        l = light_at(h, x, y, L)
        if l > th[0]:
            c = ramp[0]
        elif l > th[1]:
            c = ramp[1]
        elif l > th[2]:
            c = ramp[2]
        else:
            c = ramp[3]
        img.set(x, y, c)


# ---------------------------------------------------------------- parts
def parts():
    P = []   # (name, mask, height, ramp_key, seam)  back to front
    # headband tails fanned on the canvas behind the head
    ta = capsule_mask(64, 7, 75, 2, 1.7, 1.4) | capsule_mask(75, 2, 83, 5, 1.4, 1.1)
    tb = capsule_mask(66, 10, 78, 11, 1.7, 1.4) | capsule_mask(78, 11, 85, 16, 1.4, 1.0)
    P.append(('tail_a', ta, h_capsule(64, 7, 83, 4, 1.7, 1.2), 'red', 'K'))
    P.append(('tail_b', tb, h_capsule(66, 10, 85, 15, 1.7, 1.1), 'red', 'K'))
    # legs: left straight out, right knee flopped outward
    P.append(('shoe_l', ellipse_mask(26, 100, 7.0, 5.5), h_ellipsoid(26, 100, 7.0, 5.5, 4), 'shoe', 'K'))
    P.append(('shoe_r', ellipse_mask(92, 99, 7.0, 5.5), h_ellipsoid(92, 99, 7.0, 5.5, 4), 'shoe', 'K'))
    P.append(('shin_l', capsule_mask(35, 86, 28, 96, 4.6, 3.6), h_capsule(35, 86, 28, 96, 4.6, 3.6), 'skin', None))
    P.append(('shin_r', capsule_mask(84, 84, 90, 95, 4.6, 3.6), h_capsule(84, 84, 90, 95, 4.6, 3.6), 'skin', None))
    P.append(('thigh_l', capsule_mask(44, 73, 35, 86, 6.0, 4.8), h_capsule(44, 73, 35, 86, 6.0, 4.8), 'skin', None))
    P.append(('thigh_r', capsule_mask(70, 73, 84, 84, 6.0, 4.8), h_capsule(70, 73, 84, 84, 6.0, 4.8), 'skin', None))
    # arms
    P.append(('farm_l', capsule_mask(27, 31, 17, 19, 4.4, 3.8), h_capsule(27, 31, 17, 19, 4.4, 3.8), 'skin', None))
    P.append(('uarm_l', capsule_mask(41, 39, 27, 31, 5.6, 4.4),
              h_sum(h_capsule(41, 39, 27, 31, 5.6, 4.4), h_ellipsoid(37, 36, 5, 4, 2.0)), 'skin', None))
    P.append(('farm_r', capsule_mask(88, 51, 95, 62, 4.4, 3.8), h_capsule(88, 51, 95, 62, 4.4, 3.8), 'skin', None))
    P.append(('uarm_r', capsule_mask(72, 40, 88, 51, 5.6, 4.4),
              h_sum(h_capsule(72, 40, 88, 51, 5.6, 4.4), h_ellipsoid(76, 38, 5, 4, 2.0)), 'skin', None))
    # torso with modeled anatomy
    torso_poly = [(41, 33), (49, 31), (63, 31), (71, 33), (77, 38), (76, 45), (72, 53),
                  (70, 62), (42, 62), (40, 53), (36, 45), (35, 38)]
    tm = poly_mask(torso_poly, SW, SH)
    th = h_sum(
        h_ellipsoid(56, 46, 22, 20, 9),          # ribcage dome
        h_ellipsoid(49.5, 40, 7.5, 5.5, 3.2),    # left pec
        h_ellipsoid(62.5, 40, 7.5, 5.5, 3.2),    # right pec
        h_ellipsoid(52.5, 49, 3.2, 2.4, 1.3), h_ellipsoid(59.5, 49, 3.2, 2.4, 1.3),
        h_ellipsoid(52.5, 54, 3.2, 2.4, 1.3), h_ellipsoid(59.5, 54, 3.2, 2.4, 1.3),
        h_ellipsoid(52.8, 58.5, 3.0, 2.2, 1.1), h_ellipsoid(59.2, 58.5, 3.0, 2.2, 1.1),
        h_ellipsoid(40, 38, 5, 5, 2.2), h_ellipsoid(72, 38, 5, 5, 2.2),   # deltoids
    )
    P.append(('torso', tm, th, 'skin', 'd'))
    # shorts
    sm = poly_mask([(41, 59), (71, 59), (74, 66), (79, 77), (64, 81), (57, 72), (55, 72),
                    (48, 81), (33, 77), (38, 66)], SW, SH)
    sh = h_sum(h_ellipsoid(56, 66, 20, 12, 5), h_ellipsoid(44, 74, 8, 7, 3), h_ellipsoid(68, 74, 8, 7, 3))
    P.append(('shorts', sm, sh, 'blue', 'K'))
    # gloves (thumb on the body side) and cuffs
    P.append(('cuff_l', capsule_mask(20, 22, 16.5, 17.5, 3.9, 3.9), h_capsule(20, 22, 16.5, 17.5, 3.9, 3.9), 'blue', 'K'))
    gl = ellipse_mask(12.5, 12.5, 8.0, 7.5) | ellipse_mask(19.5, 13, 3.4, 3.0)
    P.append(('glove_l', gl, h_sum(h_ellipsoid(12.5, 12.5, 8.0, 7.5, 6), h_ellipsoid(19.5, 13, 3.4, 3.0, 1.5)), 'blue', 'K'))
    P.append(('cuff_r', capsule_mask(94, 60, 96.5, 64, 3.9, 3.9), h_capsule(94, 60, 96.5, 64, 3.9, 3.9), 'blue', 'K'))
    gr = ellipse_mask(99.5, 70, 8.0, 7.5) | ellipse_mask(92, 71.5, 3.2, 3.0)
    P.append(('glove_r', gr, h_sum(h_ellipsoid(99.5, 70, 8.0, 7.5, 6), h_ellipsoid(92, 71.5, 3.2, 3.0, 1.5)), 'blue', 'K'))
    # neck + head
    P.append(('neck', poly_mask([(50, 27), (62, 27), (63, 35), (49, 35)], SW, SH),
              h_capsule(56, 27, 56, 35, 7, 7, 0.6), 'skin', 'd'))
    P.append(('ear_l', ellipse_mask(42.5, 21, 2.8, 3.8), h_ellipsoid(42.5, 21, 2.8, 3.8, 2), 'skin', 'K'))
    P.append(('ear_r', ellipse_mask(69.5, 21, 2.8, 3.8), h_ellipsoid(69.5, 21, 2.8, 3.8, 2), 'skin', 'K'))
    hm = ellipse_mask(56, 19.5, 13.5, 13.0)
    hh = h_sum(h_ellipsoid(56, 19.5, 13.5, 13.0, 5),
               h_ellipsoid(56.5, 23.5, 1.6, 2.4, 1.2),     # nose
               h_ellipsoid(49, 25, 4, 3, 0.8), h_ellipsoid(63, 25, 4, 3, 0.8))  # cheeks
    band_y0, band_y1 = 11, 14
    hair = {(x, y) for (x, y) in hm if y < band_y0}
    # messy short hair spilling past the scalp onto the canvas
    hair |= ellipse_mask(56, 9.5, 14.5, 5.5) - {(x, y) for (x, y) in ellipse_mask(56, 9.5, 14.5, 5.5) if y >= band_y0}
    for (x, y) in [(44, 5), (45, 4), (49, 3), (50, 3), (51, 4), (55, 2), (56, 2), (57, 3), (61, 3), (62, 3),
                   (66, 4), (67, 5), (42, 7), (70, 7), (41, 9), (71, 9)]:
        hair.add((x, y))
    band = {(x, y) for (x, y) in hm if band_y0 <= y <= band_y1}
    facem = hm - hair - band
    P.append(('face', facem, hh, 'skin', 'K'))
    P.append(('hair', hair, h_sum(hh, h_ellipsoid(56, 5, 9, 5, 2)), 'hair', None))
    P.append(('band', band, h_capsule(40, 12.5, 72, 12.5, 2.6, 2.6), 'red', None))
    return P


def build(variant='pl'):
    blue = BLUE_PL if variant == 'pl' else BLUE_DB
    ramps = {'skin': SKIN, 'blue': blue, 'red': REDR, 'shoe': SHOE, 'hair': HAIR}
    img = Img(SW, SH)
    union = set()
    owner = {}
    for name, m, h, rk, seam in parts():
        if name == 'face':
            shade(img, m, h, ramps[rk], th=(0.985, 0.60, 0.33), L=FACE_LIGHT)
        elif name in ('ear_l', 'ear_r'):
            shade(img, m, h, ramps[rk], L=FACE_LIGHT)
        else:
            shade(img, m, h, ramps[rk])
        if seam and name != 'neck':
            col = K if seam == 'K' else BROWN_D
            for (x, y) in inner_edge(m):
                if name == 'torso' and y < 41:
                    continue
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    q = (x + dx, y + dy)
                    if q in union and q not in m:
                        img.set(q[0], q[1], col)
        for p in m:
            owner[p] = name
        union |= m
    for (x, y) in outline_of(union):
        img.set(x, y, K)
    cleanup(img, union)
    return img, owner, union


def cleanup(img, union, passes=2):
    """remove orphan pixels: a non-outline pixel whose 4 neighbours all share one
    other (non-outline) colour takes that colour."""
    for _ in range(passes):
        changes = []
        for (x, y) in union:
            c = img.get(x, y)
            if c in (K, None):
                continue
            nb = [img.get(x + 1, y), img.get(x - 1, y), img.get(x, y + 1), img.get(x, y - 1)]
            if nb[0] not in (K, None, c) and all(n == nb[0] for n in nb):
                changes.append((x, y, nb[0]))
        for x, y, c in changes:
            img.set(x, y, c)


PAL = None


def details(img, variant='pl'):
    blue = BLUE_PL if variant == 'pl' else BLUE_DB
    P = {'K': K, 'h': SKIN_L, 't': TAN, 's': BROWN, 'd': BROWN_D, 'R': RED, 'r': RED_L, 'p': PLUM,
         'b': blue[1], 'B': blue[2], 'l': blue[0], 'w': WHITE, 'i': ICE, 'n': NAVY, 'g': GREY_D,
         'I': INDIGO}
    # face: X eyes, nose shadow, open mouth with the tongue lolling out
    face = [
        "K...K.......K...K",
        ".K.K.........K.K.",
        "..K...........K..",
        ".K.K.........K.K.",
        "K...K.......K...K",
    ]
    img.stamp(face, 48, 17, P)
    mouth = [
        ".KKKKK.",
        "KpppppK",
        "KpprrRK",
        ".KRrrRK",
        "..KRrK.",
        "...KK..",
    ]
    img.stamp(mouth, 53, 26, P)
    img.set(57, 23, BROWN); img.set(57, 24, BROWN)
    # headband casts a 1px shadow onto the forehead (right of the highlight)
    for x in range(48, 68):
        if img.get(x, 15) in (TAN, SKIN_L):
            img.set(x, 15, BROWN)
    # navel
    img.set(56, 55, BROWN_D); img.set(56, 56, BROWN_D)
    # waistband: light band on top, shadow line under it (like the in-game shorts)
    for x in range(36, 77):
        for y, c in ((59, blue[0]), (60, blue[0]), (61, blue[2])):
            if img.get(x, y) in (blue[0], blue[1], blue[2]):
                img.set(x, y, c)
    # headband: highlight top row, base, then one shade row
    for x in range(40, 73):
        for y, c in ((11, RED_L), (12, RED), (13, RED), (14, BROWN_D)):
            if img.get(x, y) in (RED_L, RED, BROWN_D, PLUM):
                img.set(x, y, c)
    # knee highlights
    for (x, y) in [(38, 82), (39, 82), (38, 83), (77, 80), (78, 80), (78, 81)]:
        img.set(x, y, SKIN_L)
    # shoe soles: grey rim on the near edge, toe highlight
    for (cx, cy) in [(26, 100), (92, 99)]:
        for dx in range(-5, 6):
            y = cy + 4 if abs(dx) < 4 else cy + 3
            if img.get(cx + dx, y) not in (None, K):
                img.set(cx + dx, y, GREY_D)
        img.set(cx - 3, cy - 3, GREY); img.set(cx - 2, cy - 3, GREY); img.set(cx - 4, cy - 2, GREY_D)
    return img


if __name__ == '__main__':
    v = sys.argv[1] if len(sys.argv) > 1 else 'pl'
    img, owner, union = build(v)
    details(img, v)
    img.save('out/player_%s.png' % v)
    zoom_save(img, 'out/player_%s_8x.png' % v, 8)
