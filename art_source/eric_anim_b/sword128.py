"""Greatsword v2: 128x128 frame. Body rendered exactly as v1 in 96-space, pasted at (16,32);
the colossal blade leans back against his right shoulder (viewer left), angled away from the head,
gripped at hip height."""
import math
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_SOFT, TH_METAL
from weapons import Frame, FIST_V, arm_right_back, arm_right_front, arm_left_back
from parts import (cape, flap, tassets, tasset_details, belt, torso, torso_details, belt_details,
                   gorget, pauldron, pauldron_details, ID)
from parts import mirror as mirror96
from legstamp import stamp_legs
from headrender import render_head
from headstrokes import STROKES

OX, OY = 16, 32
FW = FH = 128


def body96():
    cv = lib.Canvas()
    cape(cv); stamp_legs(cv); flap(cv); tassets(cv); tasset_details(cv); belt(cv)
    tm = torso(cv); torso_details(cv, tm); belt_details(cv); gorget(cv)
    arm_right_back(cv)
    arm_left_back(cv)
    d, l1, l2 = pauldron(cv, ID); pauldron_details(cv, ID, d, l1, l2)
    d, l1, l2 = pauldron(cv, mirror96); pauldron_details(cv, mirror96, d, l1, l2)
    arm_right_front(cv)
    render_head(cv, STROKES)
    return cv.rgba()


# ------------------------------------------------------------ 128-space helpers (use lib.W at runtime)
def edge(m):
    W, H = lib.W, lib.H
    e = lib.empty()
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or not m[yy][xx]:
                        e[y][x] = True
                        break
    return e


def paint_by(cv, mask, fn):
    for y in range(lib.H):
        for x in range(lib.W):
            if mask[y][x]:
                ch = fn(x, y)
                if ch:
                    cv.px[y][x] = PALC[ch]


def cast_shadow(cv, mask, dx, dy):
    tgt = set()
    for y in range(lib.H):
        for x in range(lib.W):
            if mask[y][x]:
                xx, yy = x + dx, y + dy
                if 0 <= xx < lib.W and 0 <= yy < lib.H and not mask[yy][xx]:
                    tgt.add((xx, yy))
    for x, y in tgt:
        c = cv.px[y][x]
        if c is not None and c != BLACK:
            cv.px[y][x] = _DARKER.get(c, c)


# ------------------------------------------------------------ sword geometry
LEAN = math.degrees(math.atan2(5, 1))          # 1 px across per 5 px up, leaning away from head
SW = Frame((28.4, 92.2), 180 - LEAN)             # u points up and slightly left
BL0, BL = 3.5, 88.0                               # blade starts at a=3.5, length 88
HW, PT = 10.5, 13.0                                # half width, point length
THICK = 2.2                                       # visible thickness band on the shadow edge


BLADE_TOP, BLADE_BOT, XL0 = 3, 92, 17
LEAN_REF = 88
BLADE_W = 21
# per column tone across the full-width blade (lit edge on the left, thickness face on the right)
FULL = "kJIJKKKKKKKKKKKLNMMNk"
# point rows from the top: (left inset, right inset) relative to the full-width run
POINT = [(8, 8), (7, 7), (6, 6), (5, 5), (4, 4), (3, 3), (2, 2), (1, 1), (0, 1)]
# edge chips: row offset from BLADE_TOP -> (left inset, right inset)
CHIPS = {33: (1, 0), 34: (2, 0), 35: (1, 0), 55: (0, 1), 56: (0, 2), 57: (0, 1), 68: (1, 0), 69: (1, 0)}
PITS = [(9, 6, 'L'), (9, 7, 'L'), (16, 11, 'L'), (22, 5, 'L'), (22, 6, 'L'), (27, 9, 'L'), (31, 12, 'L'),
        (31, 13, 'L'), (38, 6, 'L'), (44, 10, 'L'), (49, 5, 'L'), (49, 6, 'L'), (54, 11, 'L'), (60, 8, 'L'),
        (64, 12, 'L'), (68, 7, 'L'), (75, 10, 'L'), (79, 6, 'L'), (41, 12, 'L'),
        (13, 5, 'J'), (14, 5, 'J'), (36, 9, 'J'), (37, 9, 'J'), (52, 8, 'J'), (53, 8, 'J'), (72, 6, 'J'), (73, 6, 'J')]


def xl_at(y):
    if y - BLADE_TOP < len(POINT):              # point rows share the first full row's offset -> symmetric tip
        y = BLADE_TOP + len(POINT)
    return XL0 + (y - LEAN_REF) // 5


def blade(cv):
    rows = {}
    for y in range(BLADE_TOP, BLADE_BOT + 1):
        i = y - BLADE_TOP
        li, ri = (POINT[i] if i < len(POINT) else (0, 0))
        cl, cr = CHIPS.get(i, (0, 0))
        li, ri = li + cl, ri + cr
        x0 = xl_at(y)
        n = BLADE_W - li - ri
        if i < len(POINT) and i < 3:
            tones = 'k' + 'J' * 1 + 'K' * max(0, n - 4) + 'N' + 'k' if n >= 4 else 'k' * n
        else:
            core = FULL[li:BLADE_W - ri] if (li or ri) else FULL
            # keep an outline + bevel on inset edges
            core = list(core)
            core[0] = 'k'
            core[-1] = 'k'
            if li and len(core) > 3:
                core[1], core[2] = 'J', 'I'
            if ri and len(core) > 5:
                core[-2], core[-3] = 'N', 'M'
            tones = ''.join(core)
        rows[y] = (x0 + li, tones)
        for k, ch in enumerate(tones):
            cv.set(x0 + li + k, y, ch)
    # top cap
    x0, tones = rows[BLADE_TOP]
    for k in range(len(tones)):
        cv.set(x0 + k, BLADE_TOP - 1, 'k')
    # make the stair-step outline closed where rows shift (both edges)
    for y in range(BLADE_TOP + 1, BLADE_BOT + 1):
        (xa, ta), (xb, tb) = rows[y - 1], rows[y]
        la, lb = xa, xb
        ra, rb = xa + len(ta) - 1, xb + len(tb) - 1
        for x in range(min(la, lb), max(la, lb)):       # left edge jumps by >1
            pass
    # pits / scratches (column index into the full-width run)
    for yo, col, ch in PITS:
        y = BLADE_TOP + yo
        x = xl_at(y) + col
        if cv.px[y][x] == PALC['K']:
            cv.set(x, y, ch)
    return rows


def hilt(cv):
    F = SW
    sgn = 1 if F.p[0] > 0 else -1
    # grip (long, two-handed), leather wrap
    gr = F.rect(-22.0, -3.0, -3.0, 3.0)

    def gtone(x, y):
        a, b = F.ab(x, y)
        b *= sgn
        wrap = int(math.floor((a * 0.9 + b * 0.5) / 2.2)) % 2
        if b < -1.2:
            return 'l' if wrap else 'm'
        if b > 1.3:
            return 'o' if wrap else 'p'
        return 'm' if wrap else 'n'
    paint_by(cv, gr, gtone)
    cv.outline(gr)
    # pommel
    pm = lib.poly([F.P(-21.5, -4.2), F.P(-24.0, -4.2), F.P(-26.5, -2.2), F.P(-26.5, 2.2), F.P(-24.0, 4.2), F.P(-21.5, 4.2)])

    def ptone(x, y):
        b = F.ab(x, y)[1] * sgn
        return 'I' if b < -1.8 else ('J' if b < 0.4 else ('L' if b < 2.4 else 'M'))
    paint_by(cv, pm, ptone)
    cv.outline(pm)
    guard(cv)


GUARD_X0, GUARD_X1, GUARD_H = 14, 40, 7
GUARD_ROWS = "kJKKLMk"


def guard_top(x):
    return 91 - (x - GUARD_X0) // 5


def guard(cv):
    for x in range(GUARD_X0, GUARD_X1 + 1):
        yt = guard_top(x)
        for r in range(GUARD_H):
            ch = GUARD_ROWS[r]
            if x == GUARD_X0 or x == GUARD_X1:
                ch = 'k'
            elif x == GUARD_X0 + 1 and r not in (0, GUARD_H - 1):
                ch = 'I' if r < 3 else 'K'
            elif x == GUARD_X1 - 1 and r not in (0, GUARD_H - 1):
                ch = 'M' if r < 4 else 'N'
            elif r == 1 and x < GUARD_X0 + 12:
                ch = 'I'
            cv.set(x, yt + r, ch)
    # close the outline where the top/bottom edges step
    for x in range(GUARD_X0, GUARD_X1):
        if guard_top(x + 1) != guard_top(x):
            cv.set(x, guard_top(x + 1), 'k')                  # top step: fill the corner above
            cv.set(x + 1, guard_top(x) + GUARD_H - 1, 'k')    # bottom step


def fist(cv):
    fc = SW.P(-10.0, 0)
    x0, y0 = int(round(fc[0])) - 6, int(round(fc[1])) - 6
    rows = FIST_V.strip('\n').split('\n')
    m = lib.empty()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                m[y0 + r][x0 + c] = True
    cast_shadow(cv, m, 1, 2)
    cv.stamp(FIST_V, x0, y0)
    return x0, y0


def arm(cv):
    """elbow cop + forearm of his right arm, tucked under the crossguard, reaching to the fist"""
    fc = SW.P(-10.0, 0)
    ex, ey = OX + 24.5, OY + 68.5
    va = lib.poly([(fc[0] + 1, fc[1] - 5.5), (ex + 1.5, ey - 5.0), (ex + 3.5, ey + 1.5), (ex - 1.0, ey + 5.0), (fc[0] + 1, fc[1] + 5.0)])
    cv.part(va, 'plate', ('cyl', (fc[0], fc[1] - 6), (ex, ey - 6), 6.5), th=TH_METAL)
    el = lib.ell(ex, ey, 4.8, 4.6)
    cv.part(el, 'plate', ('sphere', ex - 1, ey - 1.5, 5.5, 5.5), th=TH_METAL)


def build():
    body = body96()
    lib.W = lib.H = FW
    cv = lib.Canvas()
    for y in range(96):
        for x in range(96):
            p = body[y][x]
            if p[3]:
                cv.px[y + OY][x + OX] = p
    arm(cv)
    blade(cv)
    hilt(cv)
    fist(cv)
    return cv


if __name__ == '__main__':
    from pngio import write_png, scale
    FL = (136, 180, 99, 255)
    cv = build()
    px = cv.rgba()
    write_png('v2_sword.png', FW, FH, px)
    z = scale(px, 8, FL)
    write_png('v2_sword_8x.png', len(z[0]), len(z), z)
    z = scale(px, 3, FL)
    write_png('v2_sword_3x.png', len(z[0]), len(z), z)
    print('u', SW.u, 'p', SW.p, 'tip', SW.P(BL0 + BL, 0), 'pommel', SW.P(-26.5, 0), 'fist', SW.P(-10, 0))
