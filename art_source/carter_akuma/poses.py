"""Frame 1 (arms crossed, aura flaring) and frame 2 (back view with the mark)."""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, gi_fade, band, erode)
import parts as P
import face as F
import render as R
from render import seg, dot, cylm, sphm

# ------------------------------------------------------------------ frame 1
# crossed forearms: right arm behind, left arm in front

X_SH_L, X_EL_L = (26.0, 49.6), (25.0, 61.6)
X_SH_R, X_EL_R = (69.5, 49.6), (70.5, 60.2)
# lower forearm: left arm, behind - hand tucks under the right upper arm
X_FORE_LO = ((25.4, 61.4), (62.0, 57.6))
# upper forearm: right arm, in front - hand tucks under the left upper arm
X_FORE_HI = ((70.2, 59.6), (34.0, 51.6))


def x_upperarms():
    return union(P.cyl(X_SH_L, X_EL_L, 7.2, 6.6),
                 P.cyl(X_SH_R, X_EL_R, 7.2, 6.6))


def x_fore_back():
    return P.cyl(X_FORE_LO[0], X_FORE_LO[1], 5.8, 5.2)


def x_fore_front():
    return P.cyl(X_FORE_HI[0], X_FORE_HI[1], 6.0, 5.4)


def x_wrap_back():
    """cream wrap on the far end of the lower forearm"""
    return inter(P.cyl((53.0, 58.6), (64.0, 57.4), 5.6, 5.2), x_fore_back())


def x_wrap_front():
    """cream wrap on the far end of the upper forearm"""
    return inter(P.cyl((44.0, 53.2), (32.0, 50.6), 5.8, 5.4), x_fore_front())


def x_fist_back():
    return x_wrap_back()


def x_fist_front():
    return x_wrap_front()


def x_arms():
    return union(union(x_upperarms(), x_fore_back()), x_fore_front())


def x_jacket():
    """same gi, but the front panels stop where the crossed arms cover them"""
    j = union(P.gi_shoulders(), P.gi_lapels())
    j = sub(j, P._hem_cut(71.4, 75.4, step=2.8))
    return sub(j, x_arms())


def x_body_mask():
    return union(union(P.legs(), P.gi_pants()),
                 union(union(P.hips(), P.torso()),
                       union(union(P.delts(), x_arms()),
                             union(P.neck(), union(P.head(),
                                                   union(P.ears(), P.beard()))))))


def draw_cross(cv):
    R.legs_and_trousers(cv)

    tor = union(P.torso(), P.hips())
    cv.part(tor, 'skin', cylm((21.0, 55.0), (74.0, 55.0), 31.0), TH_HARD, bias=-1)
    cv.recolor(inter(tor, P.pecs()), 'skin', ('dist', 5.4), TH_HARD, bias=0)
    cv.recolor(inter(tor, mirror(P.pecs())), 'skin', ('dist', 5.4), TH_HARD, bias=0)
    R.anatomy(cv)

    # beads first: the necklace hangs under the crossed arms
    R.beads_on(cv)

    dl = P.delts()
    cv.part(dl, 'skin', sphm(25.4, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.recolor(inter(dl, mirror(P.delts())), 'skin',
               sphm(70.1, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.outline(dl)

    ua = x_upperarms()
    cv.part(ua, 'skin', cylm(X_SH_L, X_EL_L, 8.6), TH_HARD, bias=0)
    cv.recolor(inter(ua, P.cyl(X_SH_R, X_EL_R, 7.2, 6.6)), 'skin',
               cylm(X_SH_R, X_EL_R, 8.6), TH_HARD, bias=0)
    cv.outline(ua)

    # ---- lower forearm (left arm), behind: one step darker
    fb = sub(x_fore_back(), x_wrap_back())
    cv.part(fb, 'skin', cylm(X_FORE_LO[0], X_FORE_LO[1], 6.6), TH_HARD, bias=1)
    cv.outline(fb)
    wb = x_wrap_back()
    cv.part(wb, 'rope', ('dist', 5.0), TH_HARD2, bias=1)
    cv.outline(wb)
    seg(cv, [(55, 55), (55, 60)], 'j', mirror_too=False)
    seg(cv, [(59, 55), (59, 60)], 'j', mirror_too=False)
    seg(cv, [(30, 59), (44, 57), (52, 57)], 'v', mirror_too=False)

    # ---- upper forearm (right arm), in front
    ff = sub(x_fore_front(), x_wrap_front())
    cv.part(ff, 'skin', cylm(X_FORE_HI[0], X_FORE_HI[1], 6.8), TH_HARD, bias=0)
    cv.outline(ff)
    wf = x_wrap_front()
    cv.part(wf, 'rope', ('dist', 5.2), TH_HARD2, bias=0)
    cv.outline(wf)
    seg(cv, [(38, 49), (38, 55)], 'j', mirror_too=False)
    seg(cv, [(42, 50), (42, 56)], 'j', mirror_too=False)
    # forearm mass: highlight along the top, shadow underneath
    seg(cv, [(46, 50), (56, 52), (65, 55)], 's', mirror_too=False)
    seg(cv, [(45, 55), (56, 57), (66, 60)], 'w', mirror_too=False)
    seg(cv, [(45, 56), (56, 58), (66, 61)], 'W', mirror_too=False)
    seg(cv, [(33, 57), (42, 57)], 'W', mirror_too=False)
    seg(cv, [(34, 48), (42, 49)], 't', mirror_too=False)
    # knuckles on the tucked hands
    for kx, ky in ((31, 50), (31, 52), (31, 54)):
        dot(cv, kx, ky, 'g')

    # ---- gi over the shoulders, belt
    jk = x_jacket()
    cv.part(jk, 'gi', ('dist', 7.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, P.delts()), 'gi', sphm(25.4, 49.0, 13.0, 11.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, mirror(P.delts())), 'gi', sphm(70.1, 49.0, 13.0, 11.0),
               TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, 66.0, 77.0)
    seg(cv, [(22, 47), (25, 43), (31, 41), (39, 40)], 'a')
    seg(cv, [(20, 50), (21, 46)], 'b')

    blt = P.belt()
    cv.part(blt, 'belt', cylm((20.0, 65.6), (76.0, 65.6), 3.8), TH_HARD2, bias=0)
    cv.part(P.belt_knot(), 'belt', ('dist', 3.6), TH_HARD2, bias=0)
    for x0 in range(32, 68, 5):
        seg(cv, [(x0, 63), (x0 - 3, 68)], 'r', mirror_too=False)
    seg(cv, [(30, 63), (65, 63)], 'n')

    R.head(cv)
    R.faces_on(cv)
    return cv


# ------------------------------------------------------------------ frame 2
# back view

def back_jacket():
    """from behind the gi is closed: one navy field across the back."""
    body = poly(P.mir_pts([
        (47.5, 39.4), (38.6, 39.6), (31.4, 41.4), (25.2, 44.2),
        (21.4, 49.0), (23.6, 55.4), (26.2, 59.0), (27.2, 66.0),
        (28.2, 73.0), (47.5, 77.0),
    ]))
    # torn armholes so the deltoids show through
    hole = union(ell(23.2, 53.8, 6.2, 7.6), ell(72.3, 53.8, 6.2, 7.6))
    body = sub(body, hole)
    return sub(body, P._hem_cut(72.0, 77.0, step=3.0))


def sigil_v1():
    """The first mark: a broken ring cut by a diagonal slash.  Superseded -
    at 3x it read as a scribble rather than an emblem.  Kept for reference."""
    cx, cy = 47.5, 52.0
    ringm = sub(ell(cx, cy, 13.0, 9.8), ell(cx, cy, 9.4, 6.4))
    # brush opening at the top right, like an unclosed enso
    gap = poly([(cx + 2.0, cy - 12.0), (cx + 15.0, cy - 5.0),
                (cx + 11.0, cy - 1.5), (cx - 1.0, cy - 8.0)])
    ringm = sub(ringm, gap)
    # tapering diagonal slash straight through it
    slash = poly([(34.0, 41.6), (39.2, 41.0), (62.0, 62.6), (56.6, 64.0)])
    # a short cross-tick at the head of the slash - nods at the earring
    tick = poly([(36.4, 48.0), (47.4, 41.4), (49.4, 44.0), (38.4, 50.6)])
    return union(union(ringm, slash), tick)


def sigil():
    """ORIGINAL mark brushed on the back of the gi - the dark power he has
    given himself over to.  Bold, symmetrical about the spine, thick enough to
    survive the 3x blit and the flare.  Defined in intro_sigil.py."""
    import intro_sigil
    return intro_sigil.sigil()


def draw_back(cv):
    R.legs_and_trousers(cv)
    # heels instead of toes
    for hx in (27, 31, 35):
        seg(cv, [(hx, 92), (hx, 94)], 'u', over_only=True)

    tor = union(P.torso(), P.hips())
    cv.part(tor, 'skin', cylm((21.0, 55.0), (74.0, 55.0), 31.0), TH_HARD, bias=-1)

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
    cv.recolor(inter(wr, mirror(P.fists())), 'rope', sphm(76.9, 77.2, 6.2, 6.0),
               TH_HARD2, bias=0)
    cv.outline(wr)
    seg(cv, [(17, 71), (26, 69)], 'j')
    seg(cv, [(17, 75), (26, 74)], 'j')
    # triceps
    seg(cv, [(23, 55), (22, 62)], 'w')
    seg(cv, [(26, 53), (25, 60)], 'v')

    jk = back_jacket()
    cv.part(jk, 'gi', ('dist', 12.0), TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, 64.0, 76.0)
    seg(cv, [(24, 46), (30, 42), (39, 40)], 'a')
    seg(cv, [(30, 48), (29, 56), (29, 64), (30, 71)], 'b')
    # the mark, brushed across the back
    sg = inter(sigil(), jk)
    cv.part(sg, 'ember', ('dist', 3.2), TH_HARD2, bias=1)
    cv.outline(sg, PALC['9'])

    blt = P.belt()
    cv.part(blt, 'belt', cylm((20.0, 65.6), (76.0, 65.6), 3.8), TH_HARD2, bias=0)
    for x0 in range(32, 68, 5):
        seg(cv, [(x0, 63), (x0 - 3, 68)], 'r', mirror_too=False)
    seg(cv, [(30, 63), (65, 63)], 'n')

    # head from behind
    cv.part(P.neck(), 'skin', cylm((41.0, 40.0), (54.0, 40.0), 7.4), TH_HARD, bias=1)
    cv.part(P.ears(), 'skin', ('dist', 3.4), TH_HARD, bias=0)
    cv.part(P.head(), 'skin', sphm(45.0, 25.0, 17.4, 17.6, 0.30), TH_HARD, bias=0)
    seg(cv, [(38, 20), (38, 17), (40, 14), (44, 13), (49, 13)], 's', mirror_too=False)
    seg(cv, [(39, 20), (39, 17), (41, 15), (44, 14), (49, 14)], 's', mirror_too=False)
    seg(cv, [(58, 16), (60, 20), (60, 25), (59, 29)], 'v', mirror_too=False)
    # occiput / base of the skull
    seg(cv, [(40, 34), (47, 36)], 'v')
    seg(cv, [(41, 37), (47, 39)], 'w')
    # orange beard fuzz showing past the jaw from behind - keeps him Carter
    jaw = union(P.poly(P.mir_pts([
        (47.5, 44.0), (43.6, 43.6), (40.2, 41.8), (37.0, 38.4),
        (34.8, 34.0), (34.0, 29.6), (36.4, 29.0), (37.6, 33.4),
        (39.6, 37.0), (42.6, 39.6), (47.5, 40.6),
    ])), P.empty_mask())
    jaw = inter(jaw, grow(P.head(), 2))
    cv.part(jaw, 'hair', ('dist', 2.6), TH_HARD, bias=0)
    seg(cv, [(36, 31), (37, 36), (40, 40)], '2')
    # ear inner + the cross earring, now on the viewer's right
    seg(cv, [(62, 25), (62, 29)], 'w', mirror_too=False)
    seg(cv, [(34, 24), (33, 28), (34, 31)], 'w', mirror_too=False)
    cv.stamp(F.EARRING, 59, 32, flip=True)
    return cv


def back_body_mask():
    return union(union(P.legs(), P.gi_pants()),
                 union(union(P.hips(), P.torso()), union(back_jacket(),
                       union(union(P.delts(), P.arms()),
                             union(P.neck(), union(P.head(), P.ears()))))))
