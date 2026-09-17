"""Josh's body: short ivory duster over a black tee, indigo jeans, red fingerless gloves.

Arms and legs are built as unions of tapered capsules so a limb is always ONE connected
silhouette with a single outline - upper arm, forearm and hand never come apart.

Vertical anchors in the 80x80 frame: chin y48, shoulders y52, belt y60, hem y64, feet y79.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
from rig import (hcap, hdome, hbump, hplat, hf_shade, limb,
                 SKIN, IVORY, JEAN, BLACK, RED, TH_LIMB, TH_6, TH_5, TH_4, TH_BLK)
import cards as CD


def outline_only(c, mask, under):
    ol, pruned = outline_pixels(mask)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                c[y][x] = '#'
    for (x, y) in pruned:
        c[y][x] = under[y][x]


def paint(c, mask, hfn, ramp, th, zscale=1.0):
    for (x, y), (lam, lap, h0) in hf_values(mask, hfn, eps=0.5, zscale=zscale).items():
        c[y][x] = quant(lam, ramp, th)


# ------------------------------------------------------------------ limbs
def arm(c, S, E, Wr, Hnd, r_sh, r_el, r_wr, hand_r=3.8, sleeve_ramp=IVORY, cuff=True):
    """Sleeve (S->E) -> bare forearm (E->Wr) -> red fingerless glove at Hnd. One silhouette."""
    under = copy(c)
    m_up = tcapsule_mask(S[0], S[1], E[0], E[1], r_sh, r_el)
    m_fo = tcapsule_mask(E[0], E[1], Wr[0], Wr[1], r_el, r_wr)
    m_hd = ellipse_mask(Hnd[0], Hnd[1], hand_r, hand_r * 1.05)
    full = m_or(m_up, m_fo, m_hd)

    def hf(px, py):
        return max(hcap(px, py, S[0], S[1], E[0], E[1], r_sh, r_el),
                   hcap(px, py, E[0], E[1], Wr[0], Wr[1], r_el, r_wr),
                   hdome(px, py, Hnd[0], Hnd[1], hand_r, hand_r * 1.05, hand_r * 1.05))
    paint(c, m_sub(m_up, m_hd), hf, sleeve_ramp, [0.0, 0.13, 0.32, 0.58, 0.87], zscale=0.95)
    paint(c, m_sub(m_sub(m_fo, m_up), m_hd), hf, SKIN, TH_LIMB, zscale=0.95)
    paint(c, m_hd, hf, RED, TH_5, zscale=0.95)
    if cuff:            # red cuff: a band drawn PERPENDICULAR to the arm, clipped to the sleeve
        ang = math.degrees(math.atan2(E[0] - S[0], -(E[1] - S[1])))
        band = blank()
        CD.draw_card(band, E[0], E[1], r_el * 2 + 2.5, 3.2, ang,
                     face='Q', shade='q', dark='q', outline=None)
        for y in range(H):
            for x in range(W):
                if band[y][x] != '.' and m_up[y][x] and not m_hd[y][x]:
                    c[y][x] = band[y][x]
    outline_only(c, full, under)
    return full


def leg(c, Hp, K, A, r_h, r_k, r_a):
    under = copy(c)
    m1 = tcapsule_mask(Hp[0], Hp[1], K[0], K[1], r_h, r_k)
    m2 = tcapsule_mask(K[0], K[1], A[0], A[1], r_k, r_a)
    full = m_or(m1, m2)

    def hf(px, py):
        return max(hcap(px, py, Hp[0], Hp[1], K[0], K[1], r_h, r_k),
                   hcap(px, py, K[0], K[1], A[0], A[1], r_k, r_a))
    paint(c, full, hf, JEAN, [0.0, 0.28, 0.70], zscale=0.95)
    outline_only(c, full, under)
    return full


def shoe(c, poly, toe_left=True):
    """Dark high-top sneaker: white midsole, red flash, lit toe cap."""
    m = poly_mask(poly)
    under = copy(c)
    ys = [y for y in range(H) if any(m[y][x] for x in range(W))]
    top, bot = min(ys), max(ys)
    for y in ys:
        xs = [x for x in range(W) if m[y][x]]
        xl, xr = min(xs), max(xs)
        for x in xs:
            col, rcol = x - xl, xr - x
            if y == bot:
                ch = 'U'
            elif y == bot - 1:
                ch = 'n' if col > 1 else 'N'
            else:
                ch = 'X'
                if col <= 1:
                    ch = 'v'
                if rcol <= 1:
                    ch = 'x'
                if y == top and 1 < col < (xr - xl) - 1:
                    ch = 'v'
                if y in (bot - 3, bot - 4) and 1 < col < (xr - xl) - 1:
                    ch = 'Q' if y == bot - 4 else 'q'       # red flash
                if y == bot - 2 and (col <= 2 if toe_left else rcol <= 2):
                    ch = 'v'                                 # lit toe cap

            c[y][x] = ch
    outline_only(c, m, under)


def torso_h(px, py):
    """One clean chest/belly dome plus shoulder caps - no hard plateaus, they band badly at 80px."""
    h = hdome(px, py, 40.0, 58.0, 13.0, 15.5, 7.0)
    h = max(h, hdome(px, py, 31.0, 54.0, 5.8, 6.2, 6.7))          # near shoulder
    h = max(h, hdome(px, py, 49.0, 54.0, 5.2, 5.8, 6.3))          # far shoulder
    h += hbump(px, py, 34.0, 58.0, 6.5, 6.5, 7.0, 9.0, 0.8)       # near coat front panel
    h += hbump(px, py, 46.0, 58.0, 6.0, 6.0, 7.0, 9.0, 0.6)       # far coat front panel
    return h


NECK = [(36, 45), (44, 45), (45, 52), (35, 52)]


def collar(c, P):
    """Popped high collar, ivory outside with a red lining."""
    under = copy(c)
    for poly in (P['collar_l'], P['collar_r']):
        m = poly_mask(poly)
        paint(c, m, lambda px, py: hdome(px, py, 40.0, 56.0, 13.5, 11.0, 6.0), IVORY, [0.0, 0.13, 0.32, 0.58, 0.87], 0.9)
        outline_only(c, m, under)
        under = copy(c)
    for (x, y, rows) in P['collar_lining']:
        block(c, x, y, rows)


def belt(c, P):
    x0, x1, y0 = P['belt']
    for y in range(y0, y0 + 3):
        for x in range(x0, x1 + 1):
            if c[y][x] in '.#':
                continue
            c[y][x] = {0: 'v', 1: 'X', 2: 'x'}[y - y0]
    bx = (x0 + x1) // 2
    for (dx, dy, ch) in ((-2, 0, 'A'), (-1, 0, 'F'), (0, 0, 'F'), (1, 0, 'D'), (2, 0, 'A'),
                         (-2, 1, 'A'), (-1, 1, 'D'), (0, 1, 'D'), (1, 1, 'A'), (2, 1, 'K'),
                         (-1, 2, 'K'), (0, 2, 'K'), (1, 2, 'K')):
        if c[y0 + dy][bx + dx] != '.':
            put(c, bx + dx, y0 + dy, ch)


def coat_detail(c, P, tmask, teemask):
    """Red inner lining showing along the open front - a wedge, wide at the collar, gone by the
    belt - plus a shaded hem band."""
    rows = [y for y in range(H) if any(teemask[y][x] for x in range(W))]
    if rows:
        y0, y1 = min(rows), max(rows)
        for y in rows:
            t = (y - y0) / max(1, (y1 - y0))
            wide = 2 if t < 0.35 else (1 if t < 0.72 else 0)
            if not wide:
                continue
            xs = [x for x in range(W) if teemask[y][x]]
            for side, base in ((-1, min(xs) - 2), (1, max(xs) + 2)):
                for k in range(wide):
                    X = base + side * k
                    if 0 <= X < W and tmask[y][X] and c[y][X] in 'IiUuNn':
                        c[y][X] = 'Q' if (side < 0 and k == 0) else 'q'
    for x in range(W):                                   # hem band
        col = [y for y in range(H) if tmask[y][x]]
        if not col:
            continue
        b0 = max(col)
        for k, ch in ((1, 'U'), (2, 'u')):
            y = b0 - k
            if y >= 0 and tmask[y][x] and c[y][x] in 'IiUuNn':
                c[y][x] = ch
    for (x, y, rows_) in P.get('coat_lines', []):
        block(c, x, y, rows_)


# ------------------------------------------------------------------ poses
POSE0 = dict(
    torso=[(36, 45), (33, 47), (30, 49), (29, 53), (29, 58), (29, 62), (30, 66), (35, 65),
           (40, 63), (45, 65), (50, 66), (51, 62), (51, 58), (51, 53), (50, 49), (47, 47), (44, 45)],
    tee=[(35, 47), (45, 47), (46, 55), (43, 63), (37, 63), (34, 55)],
    collar_l=[(31, 45), (36, 48), (36, 55), (32, 55), (29, 51), (29, 46)],
    collar_r=[(49, 45), (44, 48), (44, 55), (48, 55), (51, 51), (51, 46)],
    collar_lining=[(34, 48, ["Qq"]), (34, 49, ["QQq"]), (35, 50, ["QQ"]), (35, 51, ["Qq"]),
                   (35, 52, ["Qq"]), (35, 53, ["qq"]),
                   (44, 48, ["qQ"]), (43, 49, ["qQQ"]), (43, 50, ["QQ"]), (43, 51, ["qQ"]),
                   (43, 52, ["qQ"]), (43, 53, ["qq"])],
    belt=(32, 48, 59),
    coat_lines=[(31, 55, ["u"]), (31, 56, ["U"]), (31, 57, ["U"]), (31, 58, ["u"]),
                (49, 55, ["U"]), (49, 56, ["U"]), (49, 57, ["u"])],
    l_arm=((29, 51), (25, 58), (23, 65), (22, 68), 5.2, 4.0, 3.2, 3.9),
    r_arm=((51, 51), (57, 57), (55, 63), (52, 66), 5.0, 3.8, 3.1, 3.8),
    l_leg=((34, 60), (33, 69), (32, 76), 5.4, 4.6, 4.0),
    r_leg=((46, 61), (48, 69), (48, 76), 5.1, 4.4, 3.8),
    l_shoe=[(28, 73), (38, 73), (39, 77), (37, 79), (26, 79), (25, 76)],
    r_shoe=[(42, 73), (52, 73), (54, 76), (53, 79), (42, 79), (41, 76)],
)


def build_body(c, P):
    leg(c, *P['l_leg'])
    leg(c, *P['r_leg'])
    shoe(c, P['l_shoe'], toe_left=True)
    shoe(c, P['r_shoe'], toe_left=False)
    arm(c, *P['r_arm'])                                   # far arm, behind the coat
    under = copy(c)
    nm = poly_mask(NECK)
    paint(c, nm, lambda px, py: hcap(px, py, 40, 45, 40, 53, 4.6, 4.2), SKIN, TH_LIMB, 0.95)
    outline_only(c, nm, under)
    under = copy(c)
    tmask = poly_mask(P['torso'])
    paint(c, tmask, torso_h, IVORY, [0.0, 0.13, 0.32, 0.58, 0.87], 0.9)
    despeckle(c, chars=IVORY, region=tmask)
    outline_only(c, tmask, under)
    tm = m_and(poly_mask(P['tee']), tmask)
    under = copy(c)
    paint(c, tm, lambda px, py: hdome(px, py, 40.0, 58.0, 6.5, 12.0, 5.0), BLACK, TH_BLK, 0.9)
    outline_only(c, tm, under)
    belt(c, P)
    collar(c, P)
    coat_detail(c, P, tmask, tm)
    arm(c, *P['l_arm'])                                   # near arm, in front of the coat
    return c


# frame 1: weight forward on his right foot, card arm thrust out to our left
POSE1 = dict(POSE0)
POSE1.update(
    torso=[(35, 45), (32, 47), (29, 49), (28, 53), (28, 58), (29, 62), (30, 66), (35, 65),
           (40, 63), (45, 65), (50, 66), (51, 62), (51, 58), (51, 53), (50, 49), (47, 47), (43, 45)],
    l_arm=((29, 51), (24, 49), (19, 44), (16, 41), 5.2, 4.0, 3.2, 3.9),
    r_arm=((51, 51), (57, 50), (61, 47), (62, 44), 5.0, 3.8, 3.1, 3.8),
    l_leg=((34, 60), (31, 69), (29, 76), 5.4, 4.6, 4.0),
    r_leg=((46, 60), (47, 69), (49, 76), 5.2, 4.4, 3.8),
    l_shoe=[(23, 73), (34, 73), (35, 77), (33, 79), (21, 79), (20, 76)],
    r_shoe=[(44, 73), (54, 73), (56, 76), (55, 79), (44, 79), (43, 76)],
)
