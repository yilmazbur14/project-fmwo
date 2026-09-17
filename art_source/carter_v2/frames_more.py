from approved import *


# ---------------- face variants of the approved front head ----------------
def head_variant(kind):
    h = copyg(HEAD_FRONT)

    def put(y, x, s):
        for i, c in enumerate(s):
            if c != '.':
                h[y][x + i] = c

    def clear_eyes():
        for y in (14, 15):
            for x in list(range(23, 30)) + list(range(34, 41)):
                if h[y][x] in 'Wi#':
                    h[y][x] = 's' if x < 36 else 'm'

    if kind in ('pant', 'ko', 'dizzy'):
        put(21, 29, "#WWWW#"); put(22, 30, "#DD#"); put(23, 31, "##")
    if kind == 'ko':
        put(23, 30, "#mm#"); put(24, 31, "##")          # tongue lolling
    if kind == 'hit':
        put(21, 29, "#WWWW#"); put(22, 29, "######")
        clear_eyes()                                     # >< squeezed shut
        put(13, 23, "##"); put(14, 25, "###"); put(15, 23, "##")
        put(13, 39, "##"); put(14, 36, "###"); put(15, 39, "##")
    if kind in ('ko', 'dizzy'):                          # X eyes
        clear_eyes()
        for cx in (25, 38):
            put(13, cx - 1, "#.#"); put(14, cx, "#"); put(15, cx - 1, "#.#")
    return h


def sweat(g, pts):
    for (x, y) in pts:
        segs(g, {y: [(x + 1, "#")], y + 1: [(x, "#F#")], y + 2: [(x, "#f#")], y + 3: [(x + 1, "#")]})


# ---------------- recover: hands on knees, panting ----------------
def recover(u=0, drops=()):
    P = []
    up = lambda pts: [(x, y - u) for x, y in pts]
    P.append(Part('torso', 3, 'skin', poly_pixels(up([(14, 26), (18, 22), (24, 20), (39, 20), (45, 22), (49, 26), (47, 36),
                                                     (45, 46), (40, 50), (23, 50), (18, 46), (16, 36)]))))
    dL = [(5, 30), (7, 25), (11, 22), (16, 21), (20, 23), (21, 28), (20, 33), (16, 36), (10, 37), (6, 35)]
    aL = [(6, 33), (14, 34), (16, 44), (16, 48), (9, 49), (7, 42)]
    hL = [(8, 46), (17, 45), (20, 48), (19, 52), (10, 53), (7, 50)]
    for nm, pts, z, mv in (('delt', dL, 6, True), ('arm', aL, 5, False), ('hand', hL, 8, False)):
        pts2 = up(pts) if mv else pts
        P.append(Part(nm + 'L', z, 'skin', poly_pixels(pts2)))
        P.append(Part(nm + 'R', z, 'skin', poly_pixels(mirror_pts(pts2))))
    P.append(Part('speedo', 4, 'blue', poly_pixels([(21, 45), (42, 45), (44, 49), (40, 53), (23, 53), (19, 49)])))
    tL = [(20, 48), (31, 50), (29, 55), (22, 57), (12, 55), (12, 50)]
    bL = [(11, 54), (24, 54), (24, 58), (25, 63), (8, 63), (10, 58)]
    P += [Part('thighL', 7, 'skin', poly_pixels(tL)), Part('thighR', 7, 'skin', poly_pixels(mirror_pts(tL))),
          Part('bootL', 2, 'boot', poly_pixels(bL)), Part('bootR', 2, 'boot', poly_pixels(mirror_pts(bL)))]
    g, lab = shade(P, term_x=40)
    repaint_speedo(g, lab)
    for x in range(6, 58):
        for y in range(53, 63):
            if lab[y][x] in ('bootL', 'bootR') and g[y][x] in 'qkK' and g[y - 1][x] == '#':
                g[y][x] = 'g' if x < 40 else 'q'
                break
    segs(g, {49: [(10, "sdsds"), (48, "dmdmd")], 50: [(10, "mdmdm"), (48, "dDdDd")]})   # fingers over the knees
    paste(g, head_variant('pant'), 0, 12 - u)
    sweat(g, drops)
    return g


# ---------------- hit: recoil, arms flung up, head snapped back ----------------
def hit():
    import idle_block as ib
    parts = [Part('torso', z, 'skin', pix) for name, z, fill, pix, ol in ib.cv.parts if name == 'torso']
    base, lab = shade(parts)
    keep = {'torso', 'speedo', 'legL', 'legR', 'bootL', 'bootR'}
    g = copyg(base)
    for y in range(64):
        for x in range(64):
            if IDLE_LABEL[y][x] in keep:
                g[y][x] = IDLE[y][x]
    P = []
    uL = [(8, 25), (13, 22), (19, 24), (19, 30), (13, 32), (7, 29)]
    fL = [(3, 15), (8, 13), (13, 23), (9, 27), (4, 24)]
    kL = [(1, 9), (8, 8), (10, 14), (5, 17), (1, 14)]
    for nm, pts, z in (('up', uL, 5), ('fore', fL, 6), ('fist', kL, 7)):
        P.append(Part(nm + 'L', z, 'skin', poly_pixels(pts)))
        P.append(Part(nm + 'R', z, 'skin', poly_pixels(mirror_pts(pts))))
    arms, alab = shade(P, term_x=40)
    paste(g, arms)
    paste(g, head_variant('hit'), 0, -2)
    segs(g, {4: [(12, "f"), (51, "f")], 5: [(13, "f"), (50, "f")], 10: [(15, "ff"), (47, "ff")]})
    return outline_pass(g)


# ---------------- defeated ----------------
def kneel():
    P = [Part('torso', 3, 'skin', poly_pixels([(15, 32), (19, 28), (25, 26), (38, 26), (44, 28), (48, 32), (46, 42),
                                               (44, 50), (20, 50), (17, 42)]))]
    dL = [(8, 34), (10, 30), (14, 28), (19, 28), (22, 31), (22, 36), (19, 40), (13, 41), (9, 39)]
    aL = [(8, 38), (15, 39), (14, 50), (13, 58), (8, 58), (7, 48)]
    hL = [(5, 56), (14, 56), (15, 61), (13, 63), (6, 63), (4, 60)]
    for nm, pts, z in (('delt', dL, 6), ('arm', aL, 5), ('hand', hL, 7)):
        P.append(Part(nm + 'L', z, 'skin', poly_pixels(pts)))
        P.append(Part(nm + 'R', z, 'skin', poly_pixels(mirror_pts(pts))))
    P.append(Part('speedo', 4, 'blue', poly_pixels([(20, 48), (43, 48), (45, 52), (41, 56), (22, 56), (18, 52)])))
    tL = [(18, 53), (31, 54), (31, 60), (29, 63), (17, 63), (16, 58)]
    P += [Part('thighL', 5, 'skin', poly_pixels(tL)), Part('thighR', 5, 'skin', poly_pixels(mirror_pts(tL)))]
    bL = [(10, 58), (18, 57), (18, 63), (9, 63)]
    P += [Part('bootL', 1, 'boot', poly_pixels(bL)), Part('bootR', 1, 'boot', poly_pixels(mirror_pts(bL)))]
    g, lab = shade(P, term_x=40)
    repaint_speedo(g, lab)
    repaint_abs(g, lab, 44, 47, cx=32, half=7)
    paste(g, head_variant('dizzy'), 0, 16)
    return g


def sit_ko():
    P = [Part('torso', 3, 'skin', poly_pixels([(16, 38), (20, 34), (26, 32), (37, 32), (43, 34), (47, 38), (45, 47),
                                               (43, 53), (20, 53), (18, 47)]))]
    dL = [(9, 40), (11, 36), (15, 34), (20, 34), (23, 37), (23, 42), (20, 46), (14, 47), (10, 45)]
    aL = [(8, 44), (15, 45), (13, 55), (10, 60), (5, 59), (6, 51)]
    hL = [(1, 57), (9, 56), (11, 60), (9, 63), (1, 63)]
    for nm, pts, z in (('delt', dL, 6), ('arm', aL, 5), ('hand', hL, 5)):
        P.append(Part(nm + 'L', z, 'skin', poly_pixels(pts)))
        P.append(Part(nm + 'R', z, 'skin', poly_pixels(mirror_pts(pts))))
    P.append(Part('speedo', 4, 'blue', poly_pixels([(19, 51), (44, 51), (46, 55), (42, 59), (21, 59), (17, 55)])))
    lL = [(20, 55), (29, 57), (24, 61), (17, 63), (10, 62), (13, 58)]
    P += [Part('legL', 5, 'skin', poly_pixels(lL)), Part('legR', 5, 'skin', poly_pixels(mirror_pts(lL)))]
    sL = [(9, 55), (17, 54), (19, 59), (17, 63), (8, 63), (6, 59)]      # boot soles toward camera
    P += [Part('soleL', 7, 'boot', poly_pixels(sL)), Part('soleR', 7, 'boot', poly_pixels(mirror_pts(sL)))]
    g, lab = shade(P, term_x=40)
    repaint_speedo(g, lab)
    for part in ('soleL', 'soleR'):
        px = [(x, y) for y in range(64) for x in range(64) if lab[y][x] == part and g[y][x] != '#']
        top = min(y for x, y in px)
        for x, y in px:
            r = y - top
            g[y][x] = 'g' if r == 0 else ('q' if r % 2 == 1 else 'k')
    paste(g, head_variant('ko'), 0, 24)
    segs(g, {20: [(18, "f"), (45, "f")], 19: [(20, "F"), (43, "F")], 22: [(15, "L"), (48, "L")]})   # daze stars
    return g


def f9():
    return recover(0, [(12, 12), (49, 14)])


def f10():
    return recover(1, [(10, 8), (51, 10)])


def f11():
    return recover(0, [(8, 13), (54, 15)])


def f12():
    return hit()


def f13():
    return kneel()


def f14():
    return sit_ko()
