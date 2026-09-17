"""Generic greatsword renderer matching the approved v2 blade (sword128.py):
blade 21 px wide incl. outline, ~91 px guard->tip, 27x7 crossguard, 19 px leather grip, octagon pommel.
Sword-local coords: a along the axis (0 = guard centre line, + toward tip), b across.
Screen: P = o + a*sa*u + b*sb*p  (sa, sb <= 1 give foreshortening)."""
import math
import lib
from lib import PALC, BLACK

BLADE_A0, TIP_A = 3.5, 91.0
HW = 10.5
PT = 9.0
GUARD_A = 3.5
GUARD_HW = 13.5
GRIP_A0, GRIP_A1, GRIP_HW = -22.0, -3.0, 3.0
POM_A0, POM_A1, POM_HW = -21.5, -26.5, 4.2
# chips: (a0, a1, side, depth)  side -1 = lit edge, +1 = dark edge
CHIPS = [(56.0, 59.0, -1, 1.6), (33.5, 36.5, +1, 1.6), (21.5, 23.5, -1, 1.0)]
# pits: (a, col 0..20, ch)
PITS = [(91 - yo, col, ch) for yo, col, ch in [
    (9, 6, 'L'), (9, 7, 'L'), (16, 11, 'L'), (22, 5, 'L'), (22, 6, 'L'), (27, 9, 'L'), (31, 12, 'L'),
    (31, 13, 'L'), (38, 6, 'L'), (44, 10, 'L'), (49, 5, 'L'), (49, 6, 'L'), (54, 11, 'L'), (60, 8, 'L'),
    (64, 12, 'L'), (68, 7, 'L'), (75, 10, 'L'), (79, 6, 'L'), (41, 12, 'L'),
    (13, 5, 'J'), (14, 5, 'J'), (36, 9, 'J'), (37, 9, 'J'), (52, 8, 'J'), (53, 8, 'J'), (72, 6, 'J'), (73, 6, 'J')]]


def edge(m):
    W, H = lib.W, lib.H
    e = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if m[y][x]:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if not (0 <= xx < W and 0 <= yy < H) or not m[yy][xx]:
                        e[y][x] = True
                        break
    return e


def outline(cv, m):
    e = edge(m)
    W, H = lib.W, lib.H
    for y in range(H):
        for x in range(W):
            if e[y][x]:
                cv.px[y][x] = BLACK


class Sword:
    def __init__(self, origin, ang_deg, sa=1.0, sb=1.0, dark=None):
        """ang_deg: screen direction guard->tip in degrees, 0 = +x, 90 = +y (down)."""
        a = math.radians(ang_deg)
        self.ang = ang_deg
        self.o = origin
        self.u = (math.cos(a), math.sin(a))
        self.p = (-self.u[1], self.u[0])
        self.sa, self.sb = sa, sb
        # dark (thickness) side = the side whose normal points down-right, away from the top-left light
        if dark is None:
            dark = 1 if (self.p[0] + self.p[1]) >= 0 else -1
        self.dark = dark
        self.bscale = sb

    def P(self, a, b):
        return (self.o[0] + self.u[0] * a * self.sa + self.p[0] * b * self.sb,
                self.o[1] + self.u[1] * a * self.sa + self.p[1] * b * self.sb)

    def ab(self, x, y):
        dx, dy = x + 0.5 - self.o[0], y + 0.5 - self.o[1]
        return ((dx * self.u[0] + dy * self.u[1]) / self.sa, (dx * self.p[0] + dy * self.p[1]) / self.sb)

    def _mask(self, test):
        W, H = lib.W, lib.H
        m = [[False] * W for _ in range(H)]
        for y in range(H):
            for x in range(W):
                a, b = self.ab(x, y)
                if test(a, b):
                    m[y][x] = True
        return m

    def blade_hw(self, a, side):
        if a > TIP_A or a < BLADE_A0 - 0.01:
            return -1
        hw = HW
        if a > TIP_A - PT:
            hw = 2.5 + (HW - 2.5) * (TIP_A - a) / PT
        for a0, a1, sd, dep in CHIPS:
            if sd * self.dark == side and a0 <= a <= a1:
                mid = (a0 + a1) / 2
                hw -= dep * (1 - abs(a - mid) / ((a1 - a0) / 2 + 0.5))
        return hw

    def blade_mask(self, a_max=None, a_min=None):
        def t(a, b):
            if a_max is not None and a > a_max:
                return False
            if a_min is not None and a < a_min:
                return False
            side = 1 if b >= 0 else -1
            return abs(b) <= self.blade_hw(a, side)
        return self._mask(t)

    def draw_blade(self, cv, a_max=None, pits=True, clip=None):
        m = self.blade_mask(a_max)
        if clip is not None:
            m = [[m[y][x] and clip[y][x] for x in range(lib.W)] for y in range(lib.H)]
        W, H = lib.W, lib.H
        e = edge(m)
        for y in range(H):
            for x in range(W):
                if not m[y][x] or e[y][x]:
                    continue
                a, b = self.ab(x, y)
                bs = b * self.bscale * self.dark    # + toward the dark side, screen px
                hwd = self.blade_hw(a, self.dark) * self.bscale
                hwl = self.blade_hw(a, -self.dark) * self.bscale
                dd = hwd - bs
                dl = hwl + bs
                ch = 'K'
                if dl < 1.5:
                    ch = 'J'
                elif dl < 2.5:
                    ch = 'I'
                elif dl < 3.5:
                    ch = 'J'
                if dd < 1.5:
                    ch = 'N'
                elif dd < 2.5:
                    ch = 'M'
                elif dd < 3.5:
                    ch = 'M'
                elif dd < 4.5:
                    ch = 'N'
                elif dd < 5.5 and ch == 'K':
                    ch = 'L'
                cv.px[y][x] = PALC[ch]
        if pits:
            for a, col, ch in PITS:
                if a_max is not None and a > a_max:
                    continue
                b = (col - 10) * (-self.dark)
                x, y = self.P(a, b)
                x, y = int(math.floor(x)), int(math.floor(y))
                if 0 <= x < W and 0 <= y < H and m[y][x] and not e[y][x] and cv.px[y][x] == PALC['K']:
                    cv.px[y][x] = PALC[ch]
        outline(cv, m)
        return m

    def draw_grip(self, cv):
        def t(a, b):
            return GRIP_A0 <= a <= GRIP_A1 and abs(b) <= GRIP_HW
        m = self._mask(t)
        W, H = lib.W, lib.H
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    a, b = self.ab(x, y)
                    bb = b * self.dark
                    wrap = int(math.floor((a * 0.9 + bb * 0.5) / 2.2)) % 2
                    if bb < -1.2:
                        ch = 'l' if wrap else 'm'
                    elif bb > 1.3:
                        ch = 'o' if wrap else 'p'
                    else:
                        ch = 'm' if wrap else 'n'
                    cv.px[y][x] = PALC[ch]
        outline(cv, m)
        return m

    def draw_pommel(self, cv):
        def t(a, b):
            if not (POM_A1 <= a <= POM_A0):
                return False
            lim = POM_HW
            if a < -24.0:
                lim = POM_HW - (POM_HW - 2.2) * (-24.0 - a) / 2.5
            return abs(b) <= lim
        m = self._mask(t)
        W, H = lib.W, lib.H
        for y in range(H):
            for x in range(W):
                if m[y][x]:
                    b = self.ab(x, y)[1] * self.dark
                    ch = 'I' if b < -1.8 else ('J' if b < 0.4 else ('L' if b < 2.4 else 'M'))
                    cv.px[y][x] = PALC[ch]
        outline(cv, m)
        return m

    def draw_guard(self, cv):
        def t(a, b):
            return -GUARD_A <= a <= GUARD_A and abs(b) <= GUARD_HW
        m = self._mask(t)
        W, H = lib.W, lib.H
        lit_tip = (self.u[0] + self.u[1]) < 0
        e = edge(m)
        for y in range(H):
            for x in range(W):
                if m[y][x] and not e[y][x]:
                    a, b = self.ab(x, y)
                    s = (a + GUARD_A) / (2 * GUARD_A)
                    if not lit_tip:
                        s = 1 - s
                    ch = 'J' if s > 0.72 else ('K' if s > 0.36 else ('L' if s > 0.18 else 'M'))
                    bb = b * self.dark
                    if bb < -GUARD_HW + 2.2 and ch in 'KL':
                        ch = 'J'
                    if bb > GUARD_HW - 2.2:
                        ch = {'J': 'L', 'K': 'M', 'L': 'M', 'M': 'N'}[ch]
                    cv.px[y][x] = PALC[ch]
        outline(cv, m)
        return m

    def draw(self, cv, a_max=None, parts=('blade', 'grip', 'pommel', 'guard')):
        if 'blade' in parts:
            self.draw_blade(cv, a_max)
        if 'grip' in parts:
            self.draw_grip(cv)
        if 'pommel' in parts:
            self.draw_pommel(cv)
        if 'guard' in parts:
            self.draw_guard(cv)


class AffineSword(Sword):
    """Sword with an arbitrary (oblique) screen projection: P = o + a*U + b*Pv.
    U = screen vector for one unit along the blade, Pv = screen vector for one unit across it."""

    def __init__(self, origin, U, Pv, dark=None):
        import math as _m
        self.o = origin
        self.U, self.Pv = U, Pv
        lu = _m.hypot(*U) or 1e-6
        self.u = (U[0] / lu, U[1] / lu)
        self.ang = _m.degrees(_m.atan2(U[1], U[0]))
        # perpendicular (screen) direction on the same side as Pv
        pp = (-self.u[1], self.u[0])
        if pp[0] * Pv[0] + pp[1] * Pv[1] < 0:
            pp = (-pp[0], -pp[1])
        self.p = pp
        self.sa = lu
        self.bscale = abs(Pv[0] * pp[0] + Pv[1] * pp[1])
        self.sb = self.bscale
        det = U[0] * Pv[1] - U[1] * Pv[0]
        self._inv = (Pv[1] / det, -Pv[0] / det, -U[1] / det, U[0] / det)
        if dark is None:
            dark = 1 if (pp[0] + pp[1]) >= 0 else -1
        self.dark = dark

    def P(self, a, b):
        return (self.o[0] + self.U[0] * a + self.Pv[0] * b, self.o[1] + self.U[1] * a + self.Pv[1] * b)

    def ab(self, x, y):
        dx, dy = x + 0.5 - self.o[0], y + 0.5 - self.o[1]
        i00, i01, i10, i11 = self._inv
        return (i00 * dx + i01 * dy, i10 * dx + i11 * dy)
