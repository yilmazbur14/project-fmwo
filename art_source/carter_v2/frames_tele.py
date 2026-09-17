from approved import *


def _fist_overlay(g, x0, y0, right=False):
    # 3 knuckle bumps + crease, reads as a clenched fist
    rows = {0: "HsHsH", 1: "dDdDd", 2: "smsms"} if not right else {0: "sdsdm", 1: "DdDdD", 2: "mdmdd"}
    for dy, s in rows.items():
        for i, c in enumerate(s):
            if g[y0 + dy][x0 + i] not in ('.', '#'):
                g[y0 + dy][x0 + i] = c


def telegraph(deep=0, scrape=False):
    d = deep
    parts = []
    torsoL = [(14, 27 + d), (18, 22 + d), (24, 20 + d)]
    torso = torsoL + list(reversed(mirror_pts(torsoL)))
    torso = [(24, 20 + d), (39, 20 + d), (45, 22 + d), (49, 27 + d), (47, 34 + d), (45, 41 + d), (43, 47 + d),
             (20, 47 + d), (18, 41 + d), (16, 34 + d), (14, 27 + d), (18, 22 + d)]
    parts.append(Part('torso', 3, 'skin', poly_pixels(torso)))
    deltL = [(6, 27), (8, 24), (11, 22), (15, 22), (18, 24), (20, 27), (21, 31), (20, 35), (17, 38), (12, 39), (8, 37), (5, 33)]
    armL = [(6, 34), (13, 36), (12, 41), (9, 46), (5, 46), (3, 41)]
    foreL = [(4, 43), (10, 42), (16, 43), (18, 47), (15, 50), (9, 50), (5, 47)]
    fistL = [(14, 42), (20, 41), (23, 44), (22, 49), (16, 50), (13, 47)]
    sh = lambda pts: [(x, y + d) for x, y in pts]
    for nm, pts, z in (('deltL', deltL, 6), ('armL', armL, 5), ('foreL', foreL, 7), ('fistL', fistL, 8)):
        parts.append(Part(nm, z, 'skin', poly_pixels(sh(pts))))
        parts.append(Part(nm.replace('L', 'R'), z, 'skin', poly_pixels(sh(mirror_pts(pts)))))
    speedo = [(20, 46 + d), (43, 46 + d), (44, 50 + d), (40, 53 + d), (23, 53 + d), (19, 50 + d)]
    parts.append(Part('speedo', 4, 'blue', poly_pixels(speedo)))
    legL = [(20, 48 + d), (30, 50 + d), (25, 55), (21, 58), (12, 57), (11, 53), (15, 49 + d)]
    bootL = [(10, 55), (22, 55), (22, 59), (23, 63), (7, 63), (9, 59)]
    parts.append(Part('legL', 2, 'skin', poly_pixels(legL)))
    parts.append(Part('legR', 2, 'skin', poly_pixels(mirror_pts(legL))))
    parts.append(Part('bootL', 1, 'boot', poly_pixels(bootL)))
    bootR = mirror_pts(bootL)
    if scrape:  # right foot scraping back: lifted 2px, shifted out
        bootR = [(x + 2, y - 2) for x, y in bootR]
    parts.append(Part('bootR', 1, 'boot', poly_pixels(bootR)))
    g, lab = shade(parts, term_x=40)
    # head (tucked glare) over the body
    paste(g, HEAD_TUCK, 0, 3 + d)
    # fists
    _fist_overlay(g, 16, 44 + d)
    _fist_overlay(g, 43, 44 + d, right=True)
    repaint_speedo(g, lab)
    repaint_abs(g, lab, 43 + d, 46 + d, cx=32, half=8)
    # pec underside lines either side of the beard
    line(g, lab, [(19, 36 + d), (20, 37 + d), (21, 38 + d), (22, 38 + d), (23, 38 + d)], 'd')
    line(g, lab, [(44, 36 + d), (43, 37 + d), (42, 38 + d), (41, 38 + d), (40, 38 + d)], 'D')
    # boot top rims
    for x in range(8, 57):
        for y in range(54, 63):
            if lab[y][x] in ('bootL', 'bootR') and g[y][x] in 'qkK' and g[y - 1][x] == '#':
                g[y][x] = 'g' if x < 40 else 'q'
                break
    if scrape:
        segs(g, {61: [(54, "nnN"), (58, "n")], 62: [(51, "NnnnN"), (57, "nn")], 63: [(50, "NnNNn")]})
    return g


def f3():
    return telegraph(0)


def f4():
    return telegraph(2, scrape=True)
