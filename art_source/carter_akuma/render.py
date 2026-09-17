"""Shared renderer: turns a pose's part masks into a fully shaded canvas."""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 dither, hexc, BLACK, PALC, TH_METAL, TH_SOFT, TH_CLOTH,
                 gi_fade, shave_corners, ell, poly)
from lib import TH_HARD, TH_HARD2
import parts as P
import face as F


def cylm(a, b, r):
    return ('cyl', a, b, r)


def sphm(cx, cy, rx, ry, flat=0.0):
    return ('sphere', cx, cy, rx, ry, flat)


# ------------------------------------------------------------------ helpers

def seg(cv, pts, ch, mirror_too=True, over_only=True):
    """draw a 1px polyline in palette colour ch (only over painted pixels)."""
    col = PALC[ch]
    pl = list(pts)
    if mirror_too:
        pl = pl + [[(95 - x, y) for x, y in pts]]
        runs = [pts, [(95 - x, y) for x, y in pts]]
    else:
        runs = [pts]
    for run in runs:
        for i in range(len(run) - 1):
            x0, y0 = run[i]
            x1, y1 = run[i + 1]
            n = max(abs(x1 - x0), abs(y1 - y0))
            for s in range(n + 1):
                t = s / max(1, n)
                x = int(round(x0 + (x1 - x0) * t))
                y = int(round(y0 + (y1 - y0) * t))
                if 0 <= x < W and 0 <= y < H:
                    if over_only and cv.px[y][x] is None:
                        continue
                    if over_only and cv.px[y][x] == BLACK:
                        continue
                    cv.px[y][x] = col


def dot(cv, x, y, ch):
    if 0 <= x < W and 0 <= y < H and cv.px[y][x] is not None:
        cv.px[y][x] = PALC[ch]


# ------------------------------------------------------------------ body

def legs_and_trousers(cv):
    cv.part(P.feet(), 'skin', ('dist', 4.2), TH_HARD, bias=0)
    cv.part(sub(P.shins(), P.feet()), 'skin',
            cylm((34.0, 83.0), (33.0, 90.4), 6.0), TH_HARD, bias=0)

    trs = P.gi_pants()
    cv.part(trs, 'gi', ('dist', 9.6), TH_HARD2, bias=0)
    cv.recolor(inter(trs, P.thighs()), 'gi',
               cylm((40.0, 64.5), (34.2, 84.4), 11.2), TH_HARD2, bias=0)
    cv.recolor(inter(trs, mirror(P.thighs())), 'gi',
               cylm((55.0, 64.5), (60.8, 84.4), 11.2), TH_HARD2, bias=0)
    cv.outline(trs)
    gi_fade(cv, trs, 74.0, 84.0)
    # fabric folds + a rim light along the outer leg
    seg(cv, [(43, 70), (42, 76), (41, 80)], 'e')
    seg(cv, [(31, 68), (30, 73), (30, 78)], 'a')
    seg(cv, [(36, 62), (33, 65), (31, 69)], 'b')


def torso_and_arms(cv):
    tor = union(P.torso(), P.hips())
    cv.part(tor, 'skin', cylm((21.0, 55.0), (74.0, 55.0), 31.0), TH_HARD, bias=-1)
    cv.recolor(inter(tor, P.pecs()), 'skin', ('dist', 5.4), TH_HARD, bias=0)
    cv.recolor(inter(tor, mirror(P.pecs())), 'skin', ('dist', 5.4), TH_HARD, bias=0)

    dl = P.delts()
    cv.part(dl, 'skin', sphm(25.4, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.recolor(inter(dl, mirror(P.delts())), 'skin',
               sphm(70.1, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.outline(dl)

    ua = P.upperarms()
    cv.part(ua, 'skin', cylm((26.2, 50.2), (22.0, 64.0), 8.8), TH_HARD, bias=0)
    cv.recolor(inter(ua, mirror(P.upperarms())), 'skin',
               cylm((69.3, 50.2), (73.5, 64.0), 8.8), TH_HARD, bias=0)
    cv.outline(ua)

    fa = sub(P.forearms(), P.wraps_wrist())
    cv.part(fa, 'skin', cylm((22.0, 64.0), (20.8, 73.8), 7.4), TH_HARD, bias=0)
    cv.recolor(inter(fa, mirror(P.forearms())), 'skin',
               cylm((73.5, 64.0), (74.7, 73.8), 7.4), TH_HARD, bias=0)
    cv.outline(fa)

    wr = union(P.wraps_wrist(), P.wraps_fist())
    cv.part(wr, 'rope', ('dist', 5.6), TH_HARD2, bias=0)
    cv.recolor(inter(wr, P.fists()), 'rope', sphm(18.6, 77.2, 6.2, 6.0), TH_HARD2, bias=0)
    cv.recolor(inter(wr, mirror(P.fists())), 'rope',
               sphm(76.9, 77.2, 6.2, 6.0), TH_HARD2, bias=0)
    cv.outline(wr)
    # wrap bindings
    seg(cv, [(17, 71), (26, 69)], 'j')
    seg(cv, [(17, 74), (26, 73)], 'j')
    # knuckles
    seg(cv, [(17, 79), (24, 78)], 'j')
    for kx in (18, 21):
        dot(cv, kx, 80, 'g')
        dot(cv, 95 - kx, 80, 'g')



def costume(cv):
    """the torn gi and the rope belt - drawn on top of the finished skin."""
    jk = P.gi_jacket()
    cv.part(jk, 'gi', ('dist', 7.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, P.delts()), 'gi', sphm(25.4, 49.0, 13.0, 11.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, mirror(P.delts())), 'gi', sphm(70.1, 49.0, 13.0, 11.0), TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, 66.0, 77.0)
    # rim light over the shoulders, bright lining where the jacket falls open
    seg(cv, [(22, 47), (25, 43), (31, 41), (39, 40)], 'a')
    seg(cv, [(38, 49), (37, 54), (38, 60), (39, 66), (40, 72)], 'a')
    seg(cv, [(20, 50), (21, 46)], 'b')
    seg(cv, [(27, 52), (26, 58), (27, 65), (28, 71)], 'b')

    blt = P.belt()
    cv.part(blt, 'belt', cylm((20.0, 65.6), (76.0, 65.6), 3.8), TH_HARD2, bias=0)
    knot = P.belt_knot()
    cv.part(knot, 'belt', ('dist', 3.6), TH_HARD2, bias=0)
    for x0 in range(32, 68, 5):
        seg(cv, [(x0, 63), (x0 - 3, 68)], 'r', mirror_too=False)
    seg(cv, [(30, 63), (65, 63)], 'n')
    seg(cv, [(44, 64), (46, 63)], 'n', mirror_too=False)
    seg(cv, [(49, 63), (51, 64)], 'n', mirror_too=False)


def anatomy(cv):
    """muscle grooves in shadow skin: pecs, abs, obliques, serratus, arms."""
    # collarbone
    seg(cv, [(40, 45), (43, 46), (46, 47)], 'v')
    seg(cv, [(41, 44), (45, 45)], 's')
    # sternum groove between the pecs
    seg(cv, [(47, 46), (47, 58)], 'w', mirror_too=False)
    seg(cv, [(48, 46), (48, 58)], 'w', mirror_too=False)
    # pec mass: highlight on top, hard shadow underneath
    seg(cv, [(39, 48), (44, 49), (46, 51)], 's')
    seg(cv, [(38, 50), (43, 51), (46, 53)], 't')
    seg(cv, [(37, 53), (39, 56), (43, 57), (46, 57)], 'W')
    seg(cv, [(37, 54), (40, 57), (43, 58), (46, 58)], 'w')
    seg(cv, [(38, 55), (41, 58), (44, 59), (46, 59)], 'v')
    # delt / pec seam
    seg(cv, [(37, 47), (36, 51), (37, 55)], 'W')
    # ab grid: centre groove plus three rungs, each block lit on top
    seg(cv, [(47, 59), (47, 68)], 'w', mirror_too=False)
    seg(cv, [(48, 59), (48, 68)], 'w', mirror_too=False)
    for ay in (61, 64, 67):
        seg(cv, [(41, ay), (46, ay)], 'w')
        seg(cv, [(42, ay + 1), (46, ay + 1)], 's')
    seg(cv, [(42, 60), (46, 60)], 's')
    # obliques
    seg(cv, [(39, 58), (40, 62)], 'v')
    seg(cv, [(38, 62), (40, 66)], 'v')
    # inner-arm shadow separating arm from torso
    seg(cv, [(30, 56), (29, 60), (30, 64)], 'W')
    # biceps / triceps
    seg(cv, [(24, 56), (23, 62)], 'w')
    seg(cv, [(27, 54), (26, 60), (25, 64)], 'v')
    seg(cv, [(23, 58), (22, 62)], 'v')
    seg(cv, [(21, 56), (25, 58), (30, 56), (34, 58), (37, 57)], 'w')
    # thigh crease
    seg(cv, [(44, 68), (43, 74)], 'e')
    # shin highlight and ankle
    seg(cv, [(32, 84), (31, 89)], 's')
    seg(cv, [(37, 85), (37, 89)], 'w')
    seg(cv, [(25, 90), (38, 89)], 'w')
    seg(cv, [(25, 91), (38, 90)], 't')
    # toes
    for tx in (27, 30, 33, 36):
        seg(cv, [(tx, 92), (tx, 95)], 'w', over_only=True)


def head(cv):
    cv.part(P.neck(), 'skin', cylm((41.0, 40.0), (54.0, 40.0), 7.4), TH_HARD, bias=0)
    cv.part(P.ears(), 'skin', ('dist', 3.4), TH_HARD, bias=0)
    cv.part(P.head(), 'skin', sphm(45.0, 25.0, 17.4, 17.6, 0.30), TH_HARD, bias=0)
    # bald-dome specular: a soft arc on the upper left, plus a rim on the right
    seg(cv, [(38, 20), (38, 17), (40, 14), (44, 13), (49, 13)], 's', mirror_too=False)
    seg(cv, [(39, 20), (39, 17), (41, 15), (44, 14), (49, 14)], 's', mirror_too=False)
    seg(cv, [(58, 16), (60, 20), (60, 25), (59, 29)], 'v', mirror_too=False)
    seg(cv, [(57, 17), (59, 21), (59, 26)], 'u', mirror_too=False)
    seg(cv, [(58, 32), (56, 36), (52, 39)], 'v', mirror_too=False)
    # temple / cheekbone shading
    seg(cv, [(35, 20), (34, 24)], 'v')

    bd = P.beard()
    cv.part(bd, 'hair', ('dist', 4.4), TH_HARD, bias=0)
    # beard strand texture
    seg(cv, [(38, 33), (37, 37)], '4')
    seg(cv, [(41, 40), (40, 43)], '4')
    seg(cv, [(44, 41), (44, 44)], '2', mirror_too=False)
    seg(cv, [(36, 29), (36, 33)], '1')
    seg(cv, [(43, 43), (47, 44)], '1')
    # under-jaw shadow so the head sits on the neck
    seg(cv, [(41, 45), (47, 46)], '6')
    # ear inner
    seg(cv, [(34, 25), (33, 28), (34, 30)], 'w')
    seg(cv, [(35, 26), (34, 29)], 'v')


def beads_on(cv):
    """juzu: a dark cord with chunky beads threaded on it."""
    pts = P.beads_centres()
    cord = [(int(round(x)), int(round(y))) for x, y in pts[:7]]
    seg(cv, cord, 'k', mirror_too=False, over_only=True)
    for cx, cy in pts:
        m = ell(cx, cy, 2.4, 2.4)
        cv.part(m, 'bead', sphm(cx - 0.7, cy - 0.8, 3.0, 3.0), TH_HARD, bias=0)
    for cx, cy in pts:
        dot(cv, int(cx - 0.8), int(cy - 0.9), 'G')


def faces_on(cv):
    cv.stamp(F.BROWS, 36, 23, over_only=True)
    cv.stamp(F.EYES, 36, 26, over_only=True)
    cv.stamp(F.NOSE, 45, 27, over_only=True)
    cv.stamp(F.MOUTH, 44, 35, over_only=True)
    cv.stamp(F.EARRING, 30, 32)


def body(cv):
    legs_and_trousers(cv)
    torso_and_arms(cv)
    anatomy(cv)
    costume(cv)
    head(cv)
    beads_on(cv)
    faces_on(cv)
    return cv
