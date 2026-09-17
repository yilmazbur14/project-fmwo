"""The profile beat of Carter's turn - he faces screen-left, mid-pivot.

This is the one genuinely new drawing in the entrance: a squeezed front or back
view turns to mush at 90 degrees, so the edge-on pose is built from its own
masks in the same part vocabulary as the approved sheet.  Row bands (head 11-40,
shoulders 41, belt 63-71, shins 85-91, feet to 95) are kept identical to the
shipped frames so his height never wobbles through the turn.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, ring,
                 erode, poly, ell, PALC, BLACK, bayer, band, TH_HARD, TH_HARD2,
                 gi_fade)
import parts as P
import face as F
from render import seg, dot, cylm, sphm
import intro_lib as IL


def cyl(a, b, r0, r1=None):
    return P.cyl(a, b, r0, r1)


# ------------------------------------------------------------------ head

def head_p():
    """Skull and face, jaw line only - the beard goes on top.  The brow ridge
    and the nose are real notches in the silhouette: edge-on they are the only
    thing that says "Carter" before the beard lands."""
    return poly([
        (46.0, 11.2), (40.8, 11.8), (36.4, 14.0), (33.4, 17.5),
        (31.9, 21.6), (31.1, 24.6), (32.8, 27.2), (31.4, 28.8),
        (29.3, 31.4), (31.8, 33.2), (33.1, 34.6), (34.4, 38.2),
        (37.0, 41.8), (40.8, 44.0), (45.2, 44.6), (50.6, 42.6),
        (55.0, 38.4), (58.2, 33.0), (59.8, 27.0), (59.6, 20.6),
        (56.9, 15.5), (52.2, 12.3),
    ])


def beard_p():
    """A solid orange mass over jaw, chin and lip - not a crescent.  Its top
    boundary follows the cheekbone so the eye and the nose stay skin."""
    m = poly([
        (35.2, 31.4), (31.6, 34.0), (30.6, 37.0), (31.2, 40.4),
        (33.2, 43.6), (36.6, 46.2), (41.4, 47.2), (46.6, 46.2),
        (50.8, 43.4), (53.2, 39.0), (53.8, 31.8), (51.2, 28.4),
        (49.0, 31.0), (44.2, 34.0), (39.4, 34.2), (36.6, 32.6),
    ])
    return inter(m, grow(head_p(), 4))


def trap_p():
    """The slab of neck and trapezius that closes the gap under the jaw."""
    return poly([(39.8, 40.0), (54.0, 39.4), (57.6, 45.0), (57.0, 50.0),
                 (38.4, 50.0), (37.6, 44.6)])


def ear_p():
    return union(ell(51.6, 27.6, 3.5, 4.7), ell(50.6, 26.2, 2.6, 3.2))


def neck_p():
    return poly([(40.8, 34.0), (52.8, 34.0), (54.4, 46.0), (39.6, 47.0)])


# ------------------------------------------------------------------ torso

def torso_p():
    # 30px deep, not 27: at the narrower width the ribcage read as a plank
    # next to a head that is 30 across, and the whole figure lost its mass
    return poly([
        (33.0, 44.2), (31.4, 49.8), (33.0, 55.0), (35.4, 60.0),
        (36.6, 64.5), (37.4, 70.6), (59.6, 71.0), (58.6, 64.0),
        (59.8, 57.0), (60.8, 50.0), (58.6, 44.2),
    ])


def delt_p():
    return union(ell(45.6, 50.2, 10.0, 8.8), ell(46.6, 45.6, 8.2, 5.4))


# The near arm hangs a little behind the chest front so the gi lapel and the
# juzu stay readable - an arm centred on the torso swallows the whole costume.
NEAR = dict(sh=(47.4, 49.4), el=(44.6, 63.6), wr=(43.6, 73.6),
            fist=(42.8, 78.2), r=(6.7, 5.8, 5.1))
FAR = dict(sh=(52.0, 49.4), el=(49.2, 63.6), wr=(48.2, 73.6),
           fist=(47.4, 78.2), r=(6.2, 5.4, 4.7))


def arm_p(A):
    up = cyl(A['sh'], A['el'], A['r'][0], A['r'][1])
    fo = cyl(A['el'], A['wr'], A['r'][1], A['r'][2])
    fi = union(ell(A['fist'][0], A['fist'][1], A['r'][2], A['r'][2] - 0.2),
               ell(A['fist'][0] + 0.8, A['fist'][1] - 3.2, A['r'][2] - 0.4,
                   A['r'][2] - 1.4))
    return up, fo, fi


def wrap_p(A):
    _, fo, fi = arm_p(A)
    band_m = cyl((A['wr'][0] + 0.6, A['wr'][1] - 4.0), A['wr'], A['r'][2] + 0.4)
    return union(inter(band_m, fo), fi)


# ------------------------------------------------------------------ lower

NEAR_LEG = dict(hip=(45.0, 64.0), knee=(40.2, 84.0), ank=(38.9, 90.4),
                r=(9.2, 8.2, 5.6, 5.2))
FAR_LEG = dict(hip=(50.4, 64.0), knee=(45.6, 84.0), ank=(44.3, 90.4),
               r=(8.6, 7.7, 5.3, 4.9))


def foot_p(dx=0.0):
    return poly([(26.0 + dx, 87.6), (43.0 + dx, 87.2), (44.2 + dx, 91.4),
                 (43.0 + dx, 95.6), (25.2 + dx, 95.6), (23.0 + dx, 92.6),
                 (23.6 + dx, 89.6)])


def leg_p(L, dx):
    th = cyl(L['hip'], L['knee'], L['r'][0], L['r'][1])
    # the shin starts above the torn hem so no bare gap opens at the knee
    sh = cyl((L['knee'][0] + 0.4, 79.0), L['ank'], L['r'][2] + 0.3, L['r'][3])
    return th, sh, foot_p(dx)


def pants_p():
    body = poly([
        (36.6, 60.6), (34.4, 66.0), (34.8, 72.0), (36.0, 78.0),
        (37.4, 82.4), (60.0, 82.0), (60.8, 76.0), (60.2, 68.0),
        (58.4, 61.0),
    ])
    th1 = cyl(NEAR_LEG['hip'], NEAR_LEG['knee'], NEAR_LEG['r'][0], NEAR_LEG['r'][1])
    th2 = cyl(FAR_LEG['hip'], FAR_LEG['knee'], FAR_LEG['r'][0], FAR_LEG['r'][1])
    return sub(union(union(body, th1), th2), P._hem_cut(79.0, 82.6, step=3.0))


def belt_p():
    return poly([(35.4, 62.6), (60.2, 62.6), (60.6, 68.4), (35.0, 68.4)])


def knot_p():
    return union(ell(37.4, 65.4, 4.4, 3.6),
                 poly([(35.0, 67.6), (38.0, 67.8), (37.0, 75.4), (34.2, 74.2)]))


def jacket_p():
    """Shoulder cap, the open front edge, and the closed back panel that
    carries the mark."""
    cap = jacket_cap()
    front = poly([(34.4, 44.0), (39.6, 45.6), (40.4, 55.0), (41.4, 64.0),
                  (42.6, 74.4), (36.2, 75.0), (34.0, 64.0), (33.4, 52.0)])
    backp = poly([(51.0, 43.4), (58.6, 45.0), (60.2, 54.0), (60.0, 64.0),
                  (59.0, 75.0), (50.4, 75.4), (50.0, 62.0), (50.2, 50.0)])
    j = union(union(cap, front), backp)
    return sub(j, P._hem_cut(71.4, 75.4, step=2.8))


def jacket_cap():
    """Only the top of the deltoid - the sleeve is torn off below it, so the
    cap must stop by row 52 or it swallows the whole upper arm."""
    return inter(union(ell(46.2, 46.6, 11.6, 8.0), ell(47.6, 49.6, 10.8, 5.6)),
                 band(38.0, 52.5))


def mark_sliver():
    """The sigil seen edge-on - a narrow hot seam hugging the back edge, fatter
    where the ring's belly would be so it still reads as the same mark."""
    return poly([(57.4, 46.8), (59.2, 47.8), (59.6, 53.0), (59.2, 58.2),
                 (58.4, 61.8), (57.2, 61.4), (57.8, 56.6), (58.0, 52.0)])


def beads_p():
    pts = [(38.4, 45.0), (37.0, 48.4), (37.4, 51.6), (40.0, 43.2),
           (44.4, 41.8), (49.0, 41.6), (53.2, 42.6)]
    m = empty()
    for cx, cy in pts:
        m = union(m, ell(cx, cy, 2.4, 2.4))
    return m, pts


# ------------------------------------------------------------------ face

def face_p(cv, eye_lv=0.7):
    """Heavy brow and one glowing slit; the nose is already a notch in the
    silhouette so it only needs a lit bridge and a nostril."""
    seg(cv, [(31, 23), (35, 22), (39, 23)], '5', mirror_too=False)
    seg(cv, [(31, 24), (35, 23), (39, 24)], '6', mirror_too=False)
    seg(cv, [(31, 25), (35, 24), (39, 25)], '5', mirror_too=False)
    seg(cv, [(32, 26), (38, 26)], 'k', mirror_too=False)
    seg(cv, [(32, 27), (38, 27)], 'k', mirror_too=False)
    if eye_lv < 0.25:
        hot, cool = '9', '9'
    elif eye_lv < 0.55:
        hot, cool = '7', '8'
    elif eye_lv < 0.82:
        hot, cool = 'V', '7'
    else:
        hot, cool = 'O', 'V'
    seg(cv, [(32, 28), (37, 28)], hot, mirror_too=False)
    seg(cv, [(32, 29), (37, 29)], cool, mirror_too=False)
    seg(cv, [(33, 30), (37, 30)], 'w', mirror_too=False)
    seg(cv, [(31, 28), (29, 31)], 't', mirror_too=False)
    seg(cv, [(32, 29), (30, 31)], 'u', mirror_too=False)
    seg(cv, [(30, 32), (32, 32)], 'k', mirror_too=False)
    seg(cv, [(31, 33), (33, 33)], 'w', mirror_too=False)
    seg(cv, [(35, 31), (39, 32)], 'v', mirror_too=False)


def ignite_eyes(cv, t, squeeze=1.0):
    """Re-light the front view's eye slits so they kindle as he comes round."""
    if t >= 0.97:
        return
    if t < 0.22:
        m = {PALC['O']: PALC['9'], PALC['V']: PALC['8'], PALC['7']: PALC['9'],
             PALC['M']: PALC['8']}
    elif t < 0.52:
        m = {PALC['O']: PALC['7'], PALC['V']: PALC['8'], PALC['7']: PALC['8'],
             PALC['M']: PALC['7']}
    elif t < 0.80:
        m = {PALC['O']: PALC['V'], PALC['V']: PALC['7'], PALC['7']: PALC['7'],
             PALC['M']: PALC['V']}
    else:
        return
    for y in range(20, 36):
        for x in range(W):
            c = cv.px[y][x]
            if c in m:
                cv.px[y][x] = m[c]


# ------------------------------------------------------------------ draw

HOT = None


def pivot_treatment(cv):
    """Turn an already-foreshortened body into the fastest frame of the pivot:
    a back-lit shape with a burning leading edge and motion streaks.

    Two earlier attempts at a fully shaded 90-degree pose both failed the same
    way - flat-on, the skull goes to a blank dome, the beard reads as a lump
    stuck to the jaw and the ribcage vanishes behind the near arm.  Feeding the
    squeezed back view through this instead keeps the good pixels, keeps the
    round-head-on-narrow-body relationship that says "edge on", and turns the
    weakest frame in the set into the one that sells the speed.  Anything
    already in the ember range is left alone, so the mark still burns through.
    """
    global HOT
    if HOT is None:
        HOT = set(PALC[c] for c in ('M', 'x', 'X', 'y', 'O', 'V'))
    m = cv.mask_of()
    out = Canvas()
    for y in range(H):
        xs = [x for x in range(W) if m[y][x]]
        if not xs:
            continue
        lo, hi = min(xs), max(xs)
        span = max(1.0, float(hi - lo))
        for x in xs:
            c = cv.px[y][x]
            if c in HOT:
                out.px[y][x] = c            # the mark keeps burning
                continue
            d = (x - lo) / span
            out.px[y][x] = PALC['U'] if d > 0.46 else PALC['T']
        # leading edge catches the light he is turning into
        out.px[y][lo] = PALC['X']
        if lo + 1 <= hi:
            out.px[y][lo + 1] = PALC['y']
        # trailing edge holds a dimmer ember so he is not a flat cut-out
        if hi > lo + 1:
            out.px[y][hi] = PALC['Y']
        if hi - 1 > lo + 1:
            out.px[y][hi - 1] = PALC['z']
    # streaks trailing the way he came from
    for i, y0 in enumerate((20, 27, 34, 46, 53, 60, 67, 76, 84)):
        xs = [x for x in range(W) if m[y0][x]]
        if not xs:
            continue
        x0, ln = max(xs), 9 + (i * 5) % 11
        for t in range(2, ln):
            x = x0 + t
            if 0 <= x < W and out.px[y0][x] is None and (t + i) % 2 == 0:
                out.px[y0][x] = PALC['z'] if t > ln * 0.5 else PALC['Y']
    return out


def draw_profile(mark_lv=0.62, eye_lv=0.55):
    cv = Canvas()

    # ---- far side first, two ramp steps down so it reads as behind him
    fth, fsh, ffo = leg_p(FAR_LEG, 5.0)
    far_low = union(fsh, ffo)
    cv.part(far_low, 'skin', ('dist', 5.0), TH_HARD, bias=1)
    cv.outline(far_low)
    seg(cv, [(46, 84), (45, 90)], 'w', mirror_too=False)

    fup, ffo2, ffi = arm_p(FAR)
    fa_all = union(union(fup, ffo2), ffi)
    cv.part(fa_all, 'skin', cylm(FAR['sh'], FAR['wr'], 8.0), TH_HARD, bias=2)
    cv.part(ffi, 'rope', ('dist', 5.0), TH_HARD2, bias=2)
    cv.outline(fa_all)

    # ---- near leg + trousers
    nth, nsh, nfo = leg_p(NEAR_LEG, 0.0)
    cv.part(nfo, 'skin', ('dist', 4.2), TH_HARD, bias=0)
    cv.part(sub(nsh, nfo), 'skin', cylm(NEAR_LEG['knee'], NEAR_LEG['ank'], 6.0),
            TH_HARD, bias=0)
    cv.outline(union(nfo, nsh))
    seg(cv, [(38, 85), (37, 90)], 's', mirror_too=False)
    seg(cv, [(42, 86), (42, 90)], 'w', mirror_too=False)
    for tx in (25, 28, 31):
        seg(cv, [(tx, 91), (tx, 94)], 'w', mirror_too=False)

    trs = pants_p()
    cv.part(trs, 'gi', ('dist', 9.6), TH_HARD2, bias=0)
    cv.recolor(inter(trs, nth), 'gi',
               cylm(NEAR_LEG['hip'], NEAR_LEG['knee'], 11.2), TH_HARD2, bias=0)
    cv.recolor(inter(trs, fth), 'gi',
               cylm(FAR_LEG['hip'], FAR_LEG['knee'], 11.0), TH_HARD2, bias=1)
    cv.outline(trs)
    gi_fade(cv, trs, 74.0, 84.0)
    seg(cv, [(38, 68), (37, 74), (36, 79)], 'a', mirror_too=False)
    seg(cv, [(49, 66), (48, 73), (48, 79)], 'e', mirror_too=False)
    seg(cv, [(57, 67), (57, 74), (57, 79)], 'b', mirror_too=False)

    # ---- torso
    tor = union(torso_p(), trap_p())
    cv.part(tor, 'skin', cylm((32.0, 56.0), (60.0, 56.0), 16.5), TH_HARD, bias=-1)
    cv.outline(tor)
    seg(cv, [(35, 46), (34, 51), (35, 56)], 's', mirror_too=False)
    seg(cv, [(37, 46), (36, 51), (37, 56)], 't', mirror_too=False)
    seg(cv, [(37, 57), (40, 59)], 'W', mirror_too=False)
    seg(cv, [(38, 58), (41, 60)], 'w', mirror_too=False)
    for ay, ax in ((61, 39), (64, 40), (67, 41)):
        seg(cv, [(ax, ay), (ax + 5, ay + 1)], 'w', mirror_too=False)
        seg(cv, [(ax + 1, ay + 1), (ax + 5, ay + 2)], 'v', mirror_too=False)
    seg(cv, [(57, 46), (58, 53), (57, 61), (56, 68)], 'w', mirror_too=False)
    seg(cv, [(58, 47), (59, 53), (58, 61)], 'W', mirror_too=False)
    seg(cv, [(42, 43), (48, 41), (53, 42)], 's', mirror_too=False)
    seg(cv, [(41, 46), (47, 44), (54, 45)], 't', mirror_too=False)

    # ---- beads across the front of the chest
    _, bpts = beads_p()
    cord = [(int(round(x)), int(round(y))) for x, y in bpts[:3]]
    seg(cv, cord, 'k', mirror_too=False)
    for cx, cy in bpts:
        cv.part(ell(cx, cy, 2.4, 2.4), 'bead', sphm(cx - 0.7, cy - 0.8, 3.0, 3.0),
                TH_HARD, bias=0)
        dot(cv, int(cx - 0.8), int(cy - 0.9), 'G')

    # ---- deltoid, then the gi cap over the top of it
    dl = delt_p()
    cv.part(dl, 'skin', sphm(44.0, 48.4, 12.0, 11.0), TH_HARD, bias=0)
    cv.outline(dl)

    jk = jacket_p()
    cap = jacket_cap()
    cv.part(jk, 'gi', ('dist', 8.0), TH_HARD2, bias=0)
    cv.recolor(inter(jk, dl), 'gi', sphm(44.0, 46.0, 13.0, 11.0), TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, 64.0, 76.0)
    seg(cv, [(38, 46), (44, 42), (52, 42)], 'a', mirror_too=False)
    seg(cv, [(35, 50), (34, 58), (35, 66)], 'b', mirror_too=False)
    seg(cv, [(58, 48), (59, 58), (58, 68)], 'b', mirror_too=False)

    # ---- the mark, edge-on
    sg = inter(mark_sliver(), jk)
    IL.sigil_paint(cv, sg, mark_lv)
    IL.sigil_bloom(cv, sg, mark_lv * 0.35, host=jk)

    blt = belt_p()
    cv.part(blt, 'belt', cylm((35.0, 65.6), (61.0, 65.6), 3.8), TH_HARD2, bias=0)
    cv.part(knot_p(), 'belt', ('dist', 3.6), TH_HARD2, bias=0)
    for x0 in range(40, 60, 5):
        seg(cv, [(x0, 63), (x0 - 3, 68)], 'r', mirror_too=False)
    seg(cv, [(38, 63), (58, 63)], 'n', mirror_too=False)

    # ---- near arm LAST: the sleeve is torn off, so it hangs outside the gi
    nup, nfa, nfi = arm_p(NEAR)
    nwr = wrap_p(NEAR)
    arm_all = sub(union(union(nup, nfa), nfi), erode(cap, 1))
    cv.part(sub(arm_all, nwr), 'skin', cylm(NEAR['sh'], NEAR['wr'], 8.4),
            TH_HARD, bias=0)
    cv.part(inter(arm_all, nwr), 'rope', ('dist', 5.6), TH_HARD2, bias=0)
    cv.recolor(inter(arm_all, nfi), 'rope', sphm(38.8, 77.2, 6.2, 6.0),
               TH_HARD2, bias=0)
    cv.outline(arm_all)
    # biceps lit down the leading edge, hard shadow where it meets the ribs
    seg(cv, [(41, 53), (40, 59), (40, 64)], 's', mirror_too=False)
    seg(cv, [(42, 54), (41, 60)], 't', mirror_too=False)
    seg(cv, [(51, 54), (50, 60), (49, 65)], 'w', mirror_too=False)
    seg(cv, [(52, 55), (51, 61), (50, 66)], 'W', mirror_too=False)
    seg(cv, [(39, 70), (48, 69)], 'j', mirror_too=False)
    seg(cv, [(39, 74), (48, 73)], 'j', mirror_too=False)
    dot(cv, 40, 79, 'g')
    dot(cv, 42, 80, 'g')
    # a dark groove down the front of the arm so it separates from the chest
    for y in range(52, 70):
        xs = [x for x in range(28, 62) if arm_all[y][x]]
        if xs:
            dot(cv, min(xs) - 1, y, 'W')

    # ---- head
    cv.part(neck_p(), 'skin', cylm((41.0, 40.0), (53.0, 40.0), 6.6), TH_HARD, bias=1)
    hd = head_p()
    er = ear_p()
    cv.part(hd, 'skin', sphm(42.0, 23.5, 17.2, 17.6, 0.30), TH_HARD, bias=0)
    cv.outline(hd)
    seg(cv, [(35, 20), (36, 16), (40, 13), (46, 13), (51, 14)], 's',
        mirror_too=False)
    seg(cv, [(36, 21), (37, 17), (41, 15), (46, 14)], 's', mirror_too=False)
    seg(cv, [(57, 18), (59, 23), (59, 29), (57, 34)], 'v', mirror_too=False)
    seg(cv, [(56, 19), (58, 24), (58, 30)], 'u', mirror_too=False)
    seg(cv, [(53, 37), (48, 41)], 'v', mirror_too=False)
    seg(cv, [(33, 19), (32, 23)], 'v', mirror_too=False)
    # occiput in shadow and a brow shelf, so the skull has structure rather
    # than being one smooth dome
    seg(cv, [(55, 20), (57, 26), (57, 32), (55, 37)], 'w', mirror_too=False)
    seg(cv, [(56, 21), (58, 27), (58, 32)], 'W', mirror_too=False)
    seg(cv, [(33, 26), (36, 27), (40, 27)], 'v', mirror_too=False)
    seg(cv, [(34, 21), (39, 20), (45, 20)], 't', mirror_too=False)

    bd = beard_p()
    cv.part(bd, 'hair', ('dist', 4.2), TH_HARD, bias=0)
    # outline only where the beard meets air.  Outlining it against the face
    # cut a black seam round the jaw and the beard read as a detached lump.
    cv.outline(sub(bd, erode(union(head_p(), trap_p()), 1)))
    # and blend the top edge into the cheek with a mid hair tone instead
    seam = inter(sub(bd, erode(bd, 1)), erode(head_p(), 1))
    for y in range(H):
        for x in range(W):
            if seam[y][x] and cv.px[y][x] is not None and cv.px[y][x] != BLACK:
                cv.px[y][x] = PALC['4']
    seg(cv, [(32, 36), (32, 41)], '4', mirror_too=False)
    seg(cv, [(35, 42), (36, 45)], '4', mirror_too=False)
    seg(cv, [(40, 45), (46, 46)], '1', mirror_too=False)
    seg(cv, [(52, 32), (52, 37)], '1', mirror_too=False)
    seg(cv, [(38, 47), (45, 47)], '6', mirror_too=False)
    seg(cv, [(31, 38), (35, 38)], '6', mirror_too=False)

    # ear over the sideburn, plus the cross earring on the visible lobe
    cv.part(er, 'skin', ('dist', 3.4), TH_HARD, bias=0)
    cv.outline(er)
    seg(cv, [(51, 26), (50, 29), (51, 31)], 'w', mirror_too=False)
    seg(cv, [(52, 27), (51, 29)], 'v', mirror_too=False)
    cv.stamp(F.EARRING, 48, 32)

    face_p(cv, eye_lv)
    return cv
