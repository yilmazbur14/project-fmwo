"""weapons + arms. Both variants share the same arms: his right hand (viewer left)
grips the weapon at shoulder height, his left arm (viewer right) is planted on his hip."""
import math
from parts import *
from lib import _DARKER, _LIGHTER


class Frame:
    def __init__(self, origin, ang_deg):
        a = math.radians(ang_deg)
        self.o = origin
        self.u = (math.cos(a), -math.sin(a))      # along weapon, toward tip
        self.p = (-self.u[1], self.u[0])          # perpendicular

    def P(self, a, b):
        return (self.o[0] + self.u[0] * a + self.p[0] * b, self.o[1] + self.u[1] * a + self.p[1] * b)

    def rect(self, a0, a1, b0, b1):
        return poly([self.P(a0, b0), self.P(a1, b0), self.P(a1, b1), self.P(a0, b1)])

    def ab(self, x, y):
        dx, dy = x + 0.5 - self.o[0], y + 0.5 - self.o[1]
        return dx * self.u[0] + dy * self.u[1], dx * self.p[0] + dy * self.p[1]


def paint_by(cv, mask, fn):
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                ch = fn(x, y)
                if ch:
                    cv.px[y][x] = PALC[ch]


FIST_CENTER = (13.5, 45.5)

# ================================================================ sword
SW = Frame((27.5, 38.8), math.degrees(math.atan2(1, 2)))
SW_L = 74.0
SW_HW = 8.5
SW_PT = 11.0
FIST_A = -15.0


def sword_blade(cv):
    F = SW
    L, hw, pt = SW_L, SW_HW, SW_PT
    m = poly([F.P(0, -hw), F.P(L - pt, -hw), F.P(L, -1.2), F.P(L, 1.2), F.P(L - pt, hw), F.P(0, hw)])
    # chips knocked out of both edges (rough, unsharpened slab)
    for a, b, r in [(27, -hw, 1.2), (47, hw, 1.4), (40, -hw, 0.9), (57, hw, 1.0), (52, -hw, 0.8)]:
        c = F.P(a, b)
        m = sub(m, ell(c[0], c[1], r * 1.6, r * 1.6))
    inner = sub(m, edge(m))

    def tone(x, y):
        a, b = F.ab(x, y)
        lh = hw if a < L - pt else max(1.0, hw * (L - a) / pt)
        r = b / lh
        if r < -0.72:
            return 'J'
        if r < -0.58:
            return 'I'
        if r > 0.74:
            return 'M'
        if r > 0.60:
            return 'L'
        return 'K'
    paint_by(cv, inner, tone)
    # forge pits, scratches and grime on the raw iron
    for a, b, ch in [(9, -2, 'L'), (10, -2, 'L'), (16, 3, 'L'), (22, -3, 'L'), (23, -3, 'L'), (27, 1, 'L'),
                     (33, 3, 'L'), (34, 3, 'L'), (41, -2, 'L'), (46, 2, 'L'), (51, -3, 'L'), (52, -3, 'L'),
                     (56, 3, 'L'), (62, -1, 'L'), (12, 4, 'L'), (44, 4, 'L'), (66, 1, 'L'), (59, -2, 'L'),
                     (14, -4, 'J'), (15, -4, 'J'), (16, -4, 'J'), (37, 0, 'J'), (38, 0, 'J'), (55, 1, 'J'), (56, 1, 'J'),
                     (63, -3, 'J'), (64, -3, 'J')]:
        x, y = F.P(a + 0.01, b + 0.01)
        x, y = int(math.floor(x)), int(math.floor(y))
        if 0 <= x < W and 0 <= y < H and inner[y][x]:
            cv.set(x, y, ch)
    cv.outline(m)
    return m


def wrap_tone(F, vertical=False):
    def gtone(x, y):
        a, b = F.ab(x, y)
        wrap = int(math.floor((a - b) / 2.5)) % 2
        if b < -1.2:
            return 'l' if wrap else 'm'
        if b > 1.3:
            return 'o' if wrap else 'p'
        return 'm' if wrap else 'n'
    return gtone


def sword_hilt(cv):
    F = SW
    # grip (long, two-handed)
    gr = F.rect(-25.0, -5.5, -3.0, 3.0)
    paint_by(cv, gr, wrap_tone(F))
    cv.outline(gr)
    # pommel: chunky octagon
    pm = poly([F.P(-24.6, -3.8), F.P(-26.6, -3.8), F.P(-28.0, -2.0), F.P(-28.0, 2.0), F.P(-26.6, 3.8), F.P(-24.6, 3.8)])
    paint_by(cv, pm, lambda x, y: 'I' if F.ab(x, y)[1] < -1.8 else ('J' if F.ab(x, y)[1] < 0.2 else ('L' if F.ab(x, y)[1] < 2.2 else 'M')))
    cv.outline(pm)
    # crossguard: thick dark-iron bar, wider than the blade
    g = F.rect(-6.0, 1.0, -12.5, 12.5)

    def gt(x, y):
        a, b = F.ab(x, y)
        if a < -4.6:
            return 'I' if b < -5 else 'J'
        if a > -0.4:
            return 'N' if b > -8 else 'M'
        if a > -1.8:
            return 'M'
        return 'K' if b < 4 else 'L'
    paint_by(cv, g, gt)
    cv.outline(g)

# ================================================================ hammer (upright, hand-drawn)

HAMMER_HEAD = """
...............k...............
..............kIk..............
..............kJk..............
.............kIJLk.............
..kkkkkkkkkkkkJKLkkkkkkkkkkkk..
..kIIIIIkIIIIIIIIIIIIIkIIIIJk..
..kJJJJJkJJJJJJJJJJJJJkJJJJKk..
..kkkkkkkkkkkkkkkkkkkkkkkkkkk..
.kkJLLLLkJKKKKKKKKKKKLkLLLLMkk.
kIkJLNLLkJKkkkkkkkkKKLkLLNLMkLk
kJkJLILLkJKkJJJJJLkKKLkLLILMkMk
.kkJLLLLkJKkJKKKLMkKKLkLLLLMkk.
..kJLLLLkJKkJKKKLMkKKLkLLLLMk..
..kJLLLLkJKkJKKKLMkKKLkLLLLMk..
..kJLLLLkJKkJKKKLMkKKLkLLLLMk..
..kJLLLLkJKkJKKKLMkKKLkLLLLMk..
..kJLLLLkJKkLMMMMMkKKLkLLLLMk..
.kkJLLLLkJKkkkkkkkkKKLkLLLLMkk.
kIkJLNLLkJKKKKKKKKKKKLkLLNLMkLk
kJkJLILLkJKKKKKKKKKKLLkLLILMkMk
.kkJLLLLkJLLLLLLLLLLLMkLLLLMkk.
..kJLLLLkKMMMMMMMMMMMMkLLLLNk..
..kKMMMMkMMMMMMMMMMMMMkMMMMNk..
..kkkkkkkkkkJKKKKLkkkkkkkkkkk..
...........kJKKKKLk............
............kkkkkk.............
"""

HAFT_X = 12     # left outline column of the haft (haft cols 12..18)


def hammer_back(cv):
    """haft down to the ground + head. Drawn after legs/cape/pauldron, before fist."""
    x0 = HAFT_X
    # haft wood (interior cols 13..17): q r r z O
    wood = ['q', 'r', 'r', 'z', 'O']
    for y in range(26, 91):
        cv.set(x0, y, 'k'); cv.set(x0 + 6, y, 'k')
        for i, ch in enumerate(wood):
            cv.set(x0 + 1 + i, y, ch)
    # wood grain flecks
    for y, i in [(64, 1), (65, 1), (71, 2), (72, 2), (80, 1), (84, 3), (85, 3)]:
        cv.set(x0 + 1 + i, y, 'z')
    # leather grip wrap y 38..59 (fist covers the middle)
    for y in range(37, 61):
        for i in range(5):
            wrap = ((y + i) // 2) % 2
            ch = [('l', 'm'), ('m', 'n'), ('m', 'n'), ('n', 'o'), ('o', 'p')][i][wrap]
            cv.set(x0 + 1 + i, y, ch)
    for y in (36, 61):
        for i in range(-1, 8):
            cv.set(x0 + i, y, 'k')
    # iron langets below the head
    for y in range(27, 36):
        for i, ch in enumerate(['J', 'K', 'K', 'L', 'M']):
            cv.set(x0 + 1 + i, y, ch)
    for y in (29, 33):
        cv.set(x0 + 3, y, 'N'); cv.set(x0 + 2, y - 1, 'I')
    # butt cap
    cap = """
kkkkkkkkk
kIJJJKLMk
kJKKKKLMk
kKLLLLMNk
.kkkkkkk.
"""
    cv.stamp(cap, x0 - 1, 91)
    # head
    cv.stamp(HAMMER_HEAD, 0, 0)


def hammer_front(cv):
    pass

# ================================================================ arms


def arm_right_back(cv):
    ua = poly([(72.5, 50), (85.5, 50), (92.3, 61.5), (87, 68.5), (79.5, 63)])
    cv.part(ua, 'chain', ('cyl', (78, 50), (90, 65), 6), th=TH_SOFT)
    inner = sub(ua, edge(ua))
    # riveted mail: offset rings
    for y in range(H):
        for x in range(W):
            if inner[y][x] and ((y % 2 == 0 and x % 2 == 0) or (y % 2 == 1 and x % 2 == 1)):
                cv.px[y][x] = _DARKER.get(cv.px[y][x], cv.px[y][x])
            elif inner[y][x] and y % 2 == 0 and x % 4 == 1:
                cv.px[y][x] = _LIGHTER.get(cv.px[y][x], cv.px[y][x])


def arm_right_front(cv):
    va = poly([(82.5, 61.5), (91.8, 65.5), (84.5, 75.5), (76.5, 77), (74.5, 70.5)])
    cv.part(va, 'plate', ('cyl', (91, 64), (75, 74), 6.5), th=TH_METAL)
    el = ell(87.3, 64.8, 5.2, 5.0)
    cv.part(el, 'plate', ('sphere', 86.5, 64, 5.5, 5.5), th=TH_METAL)
    RF = """
..kkkkkkk..
.kIIIIIJJk.
kIIIIIJJJKk
kJkkkkkkkKk
kJkKKKLLkLk
kKkLLLLMkLk
kKkLLMMMkMk
kLkMMMMNkMk
.kkkkkkkkk.
"""
    cv.stamp(RF, 67, 68)


def arm_left_back(cv):
    ua = poly([(4.5, 52), (17, 52), (16, 62), (4, 63)])
    cv.part(ua, 'chain', ('cyl', (10, 50), (9, 64), 6), th=TH_SOFT)


def arm_left_front(cv, variant='hammer'):
    if variant == 'sword':
        va = poly([(5.0, 50.0), (15.5, 50.0), (13.8, 60.0), (11.8, 66.0), (3.5, 65.0), (2.8, 57.0)])
        cv.part(va, 'plate', ('cyl', (6, 64), (12, 50), 7), th=TH_METAL)
        el = ell(7.5, 63.8, 5.2, 4.4)
        cv.part(el, 'plate', ('sphere', 6.5, 62.5, 6, 5), th=TH_METAL)
        return
    va = poly([(2.8, 60.5), (6.5, 50.5), (12.5, 48.5), (16.8, 52.5), (14.5, 61), (9.5, 66.5)])
    cv.part(va, 'plate', ('cyl', (6, 64), (13, 50), 6.5), th=TH_METAL)
    el = ell(6.5, 63.5, 5.0, 4.4)
    cv.part(el, 'plate', ('sphere', 5.5, 62.5, 5.5, 5), th=TH_METAL)


FIST_D = """
....kkkkk....
..kkIIIIIkk..
.kIIIIIIIIJk.
kIIIIIIIIIJJk
kIIIIIIIIJJkk
kIIIIIIJJkkKk
kIIIIJJkkKMLk
kIIJJkkKLMLMk
kIJkkKMLMLMMk
kJkKKMLMLMMNk
.kKLMLMMLMNk.
..kLMMMMMNk..
...kkkkkkkk..
"""


FIST_V = """
..kkkkkkkkk..
.kIIIIIIIJJk.
kIIIIIIIJJJKk
kIIkkkkkkkKKk
kIJkKKKLLkkKk
kIIkkkkkkkkLk
kJkKLLLMMMkLk
kJJkkkkkkkkLk
kJkLLMMMNNkMk
kKKkkkkkkkkMk
.kKKLLLLLLMk.
..kkkkkkkkk..
"""


def cast_shadow(cv, mask, dx, dy, steps=1):
    tgt = []
    for y in range(H):
        for x in range(W):
            if mask[y][x]:
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and not mask[yy][xx]:
                    tgt.append((xx, yy))
    for x, y in set(tgt):
        c = cv.px[y][x]
        if c is not None and c != BLACK:
            for _ in range(steps):
                c = _DARKER.get(c, c)
            cv.px[y][x] = c


def fist_left(cv, variant):
    stamp = FIST_V if variant == 'hammer' else FIST_D
    x0, y0 = (9, 39) if variant == 'hammer' else (5, 40)
    rows = stamp.strip(chr(10)).split(chr(10))
    m = empty()
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                m[y0 + r][x0 + c] = True
    cast_shadow(cv, m, 1, 2, 1)
    cast_shadow(cv, m, 2, 3, 1)
    cv.stamp(stamp, x0, y0)
