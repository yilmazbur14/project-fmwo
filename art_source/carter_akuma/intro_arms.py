"""The arm swing that links the turn to the signature crossed pose.

t = 0 is the approved idle (arms down, sheet frame 0), t = 1 is the approved
signature (arms folded, sheet frame 1).  Both ends are only ever used as a
sanity check - the shipped entrance splices the real approved frames in at the
ends and uses this purely for the in-between beats.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow,
                 erode, poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, gi_fade)
import parts as P
import poses as PO
import render as R
from render import seg, dot, cylm, sphm


def lp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def lf(a, b, t):
    return a + (b - a) * t


# down pose (approved frame 0)            crossed pose (approved frame 1)
D_UP_L = ((26.2, 50.2), (22.0, 64.0))
X_UP_L = ((26.0, 49.6), (25.0, 61.6))
D_UP_R = ((69.8, 50.2), (74.0, 64.0))
X_UP_R = ((69.5, 49.6), (70.5, 60.2))
D_FO_L = ((22.0, 64.0), (20.8, 73.8))
X_FO_L = ((25.4, 61.4), (62.0, 57.6))
D_FO_R = ((74.0, 64.0), (75.2, 73.8))
X_FO_R = ((70.2, 59.6), (34.0, 51.6))
D_FI_L, X_FI_L = (19.8, 78.2), (60.0, 57.8)
D_FI_R, X_FI_R = (76.2, 78.2), (36.0, 51.8)


def geom(t):
    g = {}
    g['upL'] = (lp(D_UP_L[0], X_UP_L[0], t), lp(D_UP_L[1], X_UP_L[1], t),
                lf(7.0, 7.2, t), lf(6.0, 6.6, t))
    g['upR'] = (lp(D_UP_R[0], X_UP_R[0], t), lp(D_UP_R[1], X_UP_R[1], t),
                lf(7.0, 7.2, t), lf(6.0, 6.6, t))
    g['foL'] = (lp(D_FO_L[0], X_FO_L[0], t), lp(D_FO_L[1], X_FO_L[1], t),
                lf(6.0, 5.8, t), lf(5.2, 5.2, t))
    g['foR'] = (lp(D_FO_R[0], X_FO_R[0], t), lp(D_FO_R[1], X_FO_R[1], t),
                lf(6.0, 6.0, t), lf(5.2, 5.4, t))
    g['fiL'] = lp(D_FI_L, X_FI_L, t)
    g['fiR'] = lp(D_FI_R, X_FI_R, t)
    return g


def _cyl(spec):
    a, b, r0, r1 = spec
    return P.cyl(a, b, r0, r1)


def _fist(c, r=5.1):
    return union(ell(c[0], c[1], r, r - 0.2), ell(c[0], c[1] - 3.0, r - 0.4, r - 1.3))


def _wrap(spec, fist_c):
    """cream hand wrap over the far third of the forearm plus the fist"""
    a, b, r0, r1 = spec
    mid = (a[0] + (b[0] - a[0]) * 0.62, a[1] + (b[1] - a[1]) * 0.62)
    return union(inter(P.cyl(mid, b, r1 + 0.5), _cyl(spec)), _fist(fist_c))


def arms_mask(t):
    g = geom(t)
    return union(union(_cyl(g['upL']), _cyl(g['upR'])),
                 union(union(_cyl(g['foL']), _fist(g['fiL'])),
                       union(_cyl(g['foR']), _fist(g['fiR']))))


def body_mask(t):
    return union(union(P.legs(), P.gi_pants()),
                 union(union(P.hips(), P.torso()),
                       union(union(P.delts(), arms_mask(t)),
                             union(P.neck(), union(P.head(),
                                                   union(P.ears(), P.beard()))))))


def jacket(t):
    j = union(P.gi_shoulders(), P.gi_lapels())
    j = sub(j, P._hem_cut(71.4, 75.4, step=2.8))
    return sub(j, arms_mask(t))


def draw_lerp(cv, t):
    g = geom(t)
    R.legs_and_trousers(cv)

    tor = union(P.torso(), P.hips())
    cv.part(tor, 'skin', cylm((21.0, 55.0), (74.0, 55.0), 31.0), TH_HARD, bias=-1)
    cv.recolor(inter(tor, P.pecs()), 'skin', ('dist', 5.4), TH_HARD, bias=0)
    cv.recolor(inter(tor, mirror(P.pecs())), 'skin', ('dist', 5.4), TH_HARD, bias=0)
    R.anatomy(cv)
    R.beads_on(cv)

    dl = P.delts()
    cv.part(dl, 'skin', sphm(25.4, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.recolor(inter(dl, mirror(P.delts())), 'skin',
               sphm(70.1, 51.6, 12.4, 11.2), TH_HARD, bias=0)
    cv.outline(dl)

    ua = union(_cyl(g['upL']), _cyl(g['upR']))
    cv.part(ua, 'skin', cylm(g['upL'][0], g['upL'][1], 8.6), TH_HARD, bias=0)
    cv.recolor(inter(ua, _cyl(g['upR'])), 'skin',
               cylm(g['upR'][0], g['upR'][1], 8.6), TH_HARD, bias=0)
    cv.outline(ua)

    # left forearm sits behind, one ramp step darker - same z-order as frame 1
    for key, fi, bias in (('foL', 'fiL', 1), ('foR', 'fiR', 0)):
        fo = union(_cyl(g[key]), _fist(g[fi]))
        wr = _wrap(g[key], g[fi])
        skin = sub(fo, wr)
        cv.part(skin, 'skin', cylm(g[key][0], g[key][1], 6.8), TH_HARD, bias=bias)
        cv.part(inter(fo, wr), 'rope', ('dist', 5.2), TH_HARD2, bias=bias)
        cv.recolor(_fist(g[fi]), 'rope',
                   sphm(g[fi][0] - 1.2, g[fi][1] - 1.2, 6.2, 6.0), TH_HARD2, bias=bias)
        cv.outline(fo)
        # wrap bindings across the forearm, perpendicular to its axis
        (ax, ay), (bx, by) = g[key][0], g[key][1]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        for f in (0.72, 0.86):
            cxx, cyy = ax + dx * f, ay + dy * f
            seg(cv, [(int(round(cxx - px * 4.4)), int(round(cyy - py * 4.4))),
                     (int(round(cxx + px * 4.4)), int(round(cyy + py * 4.4)))],
                'j', mirror_too=False)
        # mass: lit along the top of the forearm, shadow underneath
        for f, ch, off in ((0.35, 's', -3), (0.55, 'w', 3), (0.7, 'W', 4)):
            cxx, cyy = ax + dx * f, ay + dy * f
            seg(cv, [(int(round(cxx - dx * 0.25)), int(round(cyy - dy * 0.25 + off))),
                     (int(round(cxx + dx * 0.25)), int(round(cyy + dy * 0.25 + off)))],
                ch, mirror_too=False)

    jk = jacket(t)
    cv.part(jk, 'gi', ('dist', 7.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, P.delts()), 'gi', sphm(25.4, 49.0, 13.0, 11.0),
               TH_HARD2, bias=0)
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
