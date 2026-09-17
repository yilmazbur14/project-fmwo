"""Guest elbow drop (5 frames) in the approved style. Elbow contact at ~(26,61) like the old sheet."""
from approved import *
import frames_more as fm


def diag_lines(g, specs):
    """specs: (x0, y0, length) streaks going up-right from (x0,y0); bright at the start."""
    for x0, y0, n in specs:
        for i in range(n):
            x, y = x0 + i, y0 - i
            if 0 <= x < 64 and 0 <= y < 64 and g[y][x] == '.':
                t = i / max(1, n - 1)
                g[y][x] = 'f' if t < 0.4 else ('F' if t < 0.7 else 'L')


def dive(alt=False):
    s = 1 if alt else 0
    P = []
    P.append(Part('legA', 2, 'skin', poly_pixels([(38, 20), (44, 14), (50, 8), (55, 11), (49, 19), (42, 26)])))
    P.append(Part('bootA', 3, 'boot', poly_pixels([(49, 4), (55, 0), (60, 3), (58, 10), (52, 12), (48, 9)])))
    P.append(Part('legB', 1, 'skin', poly_pixels([(42, 24), (49, 18 - s), (56, 15 - s), (60, 19 - s), (52, 26), (45, 30)])))
    P.append(Part('bootB', 1, 'boot', poly_pixels([(55, 12 - 2 * s), (61, 9 - 2 * s), (63, 14 - 2 * s), (62, 20 - 2 * s), (57, 21 - 2 * s)])))
    P.append(Part('speedo', 4, 'blue', poly_pixels([(34, 24), (42, 18), (48, 24), (46, 32), (38, 34), (32, 30)])))
    P.append(Part('torso', 3, 'skin', poly_pixels([(18, 40), (26, 31), (36, 24), (46, 28), (44, 36), (34, 43), (24, 48), (18, 46)])))
    P.append(Part('upB', 5, 'skin', poly_pixels([(14, 24), (20, 20), (27, 30), (23, 35), (17, 33)])))
    P.append(Part('foreB', 6, 'skin', poly_pixels([(6 + s, 12), (11 + s, 9), (19, 23), (15, 26), (9 + s, 22)])))
    P.append(Part('fistB', 7, 'skin', poly_pixels([(3 + 2 * s, 5), (10 + 2 * s, 3), (12 + 2 * s, 9), (8 + 2 * s, 13), (3 + 2 * s, 11)])))
    P.append(Part('upE', 9, 'skin', poly_pixels([(21, 42), (30, 40), (32, 50), (31, 60), (27, 63), (22, 61), (20, 52)])))
    P.append(Part('foreE', 10, 'skin', poly_pixels([(29, 48), (35, 45), (38, 50), (35, 58), (30, 60), (28, 55)])))
    g, lab = shade(P, term_x=44)
    repaint_speedo(g, lab, cx=40)
    paste(g, HEAD_FRONT, -17, 24)
    upE, _ = shade([p for p in P if p.name in ('upE', 'foreE')], term_x=44)
    paste(g, upE)                                     # elbow arm in front of the beard
    segs(g, {52: [(31, "HsH")], 53: [(31, "dDd")]})   # knuckles of the tucked fist
    diag_lines(g, [(40 + 2 * s, 44, 9), (46, 38 - s, 8), (33, 18, 6), (50, 44, 7), (12, 58 - 2 * s, 5)])
    return g


def landed():
    P = []
    P.append(Part('legA', 2, 'skin', poly_pixels([(48, 18), (52, 12), (56, 8), (60, 11), (55, 20), (51, 24)])))
    P.append(Part('bootA', 3, 'boot', poly_pixels([(53, 4), (58, 1), (62, 4), (61, 11), (57, 13), (53, 10)])))
    P.append(Part('legB', 1, 'skin', poly_pixels([(50, 24), (55, 18), (59, 16), (62, 20), (57, 27), (52, 29)])))
    P.append(Part('bootB', 1, 'boot', poly_pixels([(58, 12), (63, 11), (63, 21), (59, 22)])))
    P.append(Part('speedo', 4, 'blue', poly_pixels([(42, 22), (50, 18), (55, 24), (53, 32), (46, 35), (41, 30)])))
    P.append(Part('torso', 3, 'skin', poly_pixels([(24, 40), (34, 32), (44, 27), (50, 32), (46, 40), (36, 46), (28, 50), (22, 48)])))
    P.append(Part('armB', 5, 'skin', poly_pixels([(1, 56), (10, 52), (14, 56), (10, 62), (2, 63)])))
    P.append(Part('upE', 9, 'skin', poly_pixels([(22, 46), (31, 44), (32, 52), (31, 60), (28, 63), (24, 63), (21, 58), (21, 50)])))
    P.append(Part('foreE', 10, 'skin', poly_pixels([(29, 56), (38, 55), (43, 57), (42, 62), (30, 63)])))
    g, lab = shade(P, term_x=44)
    repaint_speedo(g, lab, cx=48)
    paste(g, HEAD_FRONT, -14, 27)
    front, _ = shade([p for p in P if p.name in ('upE', 'foreE')], term_x=44)
    paste(g, front)
    segs(g, {58: [(39, "HsH")], 59: [(39, "dDd")]})
    # impact dashes around the elbow
    for x, y in ((20, 62), (19, 61), (35, 53), (36, 52), (18, 57)):
        if g[y][x] == '.':
            g[y][x] = 'f'
    return g


def sit_up():
    g = fm.recover(0, [])
    # swap the panting head for the approved glare
    pant = fm.head_variant('pant')
    for y in range(64):
        for x in range(64):
            yy = y - 12
            if 0 <= yy < 64 and pant[yy][x] != '.':
                pass
    body = fm.recover(0, [])
    # rebuild: recover body without head, then approved head
    import copy
    return _recover_with_head(HEAD_FRONT)


def _recover_with_head(head):
    orig = fm.head_variant
    fm.head_variant = lambda kind: head
    try:
        return fm.recover(0, [])
    finally:
        fm.head_variant = orig


def leap_out():
    import idle_block as ib
    g = copyg(IDLE)
    for y in range(64):
        for x in range(64):
            if IDLE_LABEL[y][x] == 'armL':
                g[y][x] = '.'
    torso_full, _ = shade([Part('torso', 3, 'skin', pix) for name, z, fill, pix, ol in ib.cv.parts if name == 'torso'])
    for y in range(64):
        for x in range(64):
            if g[y][x] == '.' and torso_full[y][x] != '.':
                g[y][x] = torso_full[y][x]
    P = [Part('delt', 5, 'skin', poly_pixels([(9, 29), (11, 24), (16, 23), (20, 26), (20, 32), (15, 35), (10, 34)])),
         Part('up', 4, 'skin', poly_pixels([(7, 12), (14, 11), (17, 26), (10, 28)])),
         Part('fist', 6, 'skin', poly_pixels([(5, 2), (13, 1), (16, 6), (15, 12), (7, 13), (4, 8)]))]
    arm, alab = shade(P, term_x=44)
    paste(g, arm)
    paste(g, HEAD_FRONT)            # head stays in front of the raised arm
    segs(g, {5: [(7, "HsHs")], 6: [(7, "dDdD")]})
    return outline_pass(g)


def e0():
    return dive(False)


def e1():
    return dive(True)


def e2():
    return landed()


def e3():
    return _recover_with_head(HEAD_FRONT)


def e4():
    return leap_out()
