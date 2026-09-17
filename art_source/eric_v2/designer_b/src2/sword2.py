"""v2 greatsword renderer (any angle, optional length foreshortening) matching designer A's 1.25x bar sword:
blade 26 px wide ("kJIJ" + K*14 + "LLNMMMNk"), 110 px from a=5.5 to the tip, 13 px point, crossguard 33 x 9
("kJIKKLMNk", lit toward the upper-left), grip 24 x 7 with leather wrap, 9 x 6 pommel, forge pits.
Sword-local: a along the axis (guard centre a=0, + toward the tip), b across (screen px, billboarded)."""
import math
import lib
from lib import PALC, BLACK

BLADE_A0, TIP_A, HW, PT = 4.5, 115.5, 13.0, 13.0
GUARD_A, GUARD_HW = 4.5, 16.5
GRIP_A0, GRIP_A1, GRIP_HW = -28.5, -4.5, 3.5
POM_A, POM_HL, POM_HW = -32.0, 3.0, 4.5
CHIPS = []
PITS = [(115.5 - p, c, ch) for p, c, ch in [
    (11, 7, 'L'), (11, 8, 'L'), (20, 14, 'L'), (27, 6, 'L'), (27, 7, 'L'), (34, 11, 'L'), (39, 15, 'L'),
    (39, 16, 'L'), (47, 7, 'L'), (55, 12, 'L'), (61, 6, 'L'), (61, 7, 'L'), (67, 14, 'L'), (75, 10, 'L'),
    (80, 15, 'L'), (85, 8, 'L'), (93, 12, 'L'), (98, 7, 'L'), (51, 15, 'L'), (30, 18, 'L'), (72, 19, 'L'),
    (16, 6, 'J'), (17, 6, 'J'), (45, 11, 'J'), (46, 11, 'J'), (65, 10, 'J'), (66, 10, 'J'), (90, 7, 'J'), (91, 7, 'J')]]


def edge(m, W, H):
    e = set()
    for (x, y) in m:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) not in m:
                e.add((x, y))
                break
    return e


class Sword2:
    def __init__(self, guard, ang_deg, sa=1.0):
        a = math.radians(ang_deg)
        self.o = guard
        self.u = (math.cos(a), math.sin(a))
        self.p = (-self.u[1], self.u[0])
        self.sa = max(0.05, sa)
        # dark (thickness) side faces down-right
        self.dark = 1 if (self.p[0] + self.p[1]) >= 0 else -1

    def P(self, a, b):
        return (self.o[0] + self.u[0] * a * self.sa + self.p[0] * b, self.o[1] + self.u[1] * a * self.sa + self.p[1] * b)

    def ab(self, x, y):
        dx, dy = x + 0.5 - self.o[0], y + 0.5 - self.o[1]
        return ((dx * self.u[0] + dy * self.u[1]) / self.sa, dx * self.p[0] + dy * self.p[1])

    def _mask(self, test, a0, a1, bw):
        W, H = lib.W, lib.H
        pts = [self.P(a, b) for a in (a0, a1) for b in (-bw, bw)]
        x0 = max(0, int(min(p[0] for p in pts)) - 2)
        x1 = min(W - 1, int(max(p[0] for p in pts)) + 2)
        y0 = max(0, int(min(p[1] for p in pts)) - 2)
        y1 = min(H - 1, int(max(p[1] for p in pts)) + 2)
        m = set()
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                a, b = self.ab(x, y)
                if test(a, b):
                    m.add((x, y))
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

    def draw(self, cv, parts=('blade', 'grip', 'pommel', 'guard'), keep=None):
        if 'blade' in parts:
            self.draw_blade(cv)
        if 'grip' in parts:
            self.draw_grip(cv)
        if 'pommel' in parts:
            self.draw_pommel(cv)
        if 'guard' in parts:
            self.draw_guard(cv)

    def _put(self, cv, x, y, ch):
        if 0 <= x < lib.W and 0 <= y < lib.H:
            cv.px[y][x] = PALC[ch]

    def draw_blade(self, cv):
        m = self._mask(lambda a, b: abs(b) <= self.blade_hw(a, 1 if b >= 0 else -1), BLADE_A0, TIP_A, HW + 1)
        e = edge(m, lib.W, lib.H)
        for (x, y) in m:
            if (x, y) in e:
                continue
            a, b = self.ab(x, y)
            bs = b * self.dark
            dd = self.blade_hw(a, self.dark) - bs
            dl = self.blade_hw(a, -self.dark) + bs
            ch = 'K'
            if dl < 1.5:
                ch = 'J'
            elif dl < 2.5:
                ch = 'I'
            elif dl < 3.5:
                ch = 'J'
            if dd < 1.5:
                ch = 'N'
            elif dd < 4.5:
                ch = 'M'
            elif dd < 5.5:
                ch = 'N'
            elif dd < 7.5 and ch == 'K':
                ch = 'L'
            self._put(cv, x, y, ch)
        for a, col, ch in PITS:
            b = (col - 13) * (-self.dark)
            x, y = self.P(a, b)
            x, y = int(math.floor(x)), int(math.floor(y))
            if (x, y) in m and (x, y) not in e and cv.px[y][x] == PALC['K']:
                self._put(cv, x, y, ch)
        for (x, y) in e:
            self._put(cv, x, y, 'k')
        return m

    def draw_grip(self, cv):
        m = self._mask(lambda a, b: GRIP_A0 <= a <= GRIP_A1 and abs(b) <= GRIP_HW, GRIP_A0, GRIP_A1, GRIP_HW + 1)
        e = edge(m, lib.W, lib.H)
        for (x, y) in m:
            if (x, y) in e:
                self._put(cv, x, y, 'k')
                continue
            a, b = self.ab(x, y)
            bb = b * self.dark
            wrap = int(math.floor((a * self.sa * 0.9 + bb * 0.5) / 2.0)) % 2
            if bb < -1.2:
                ch = 'l' if wrap else 'm'
            elif bb > 1.3:
                ch = 'o' if wrap else 'p'
            else:
                ch = 'm' if wrap else 'n'
            self._put(cv, x, y, ch)
        return m

    def draw_pommel(self, cv):
        def t(a, b):
            da = abs(a - POM_A) * self.sa
            if da > POM_HL or abs(b) > POM_HW:
                return False
            return not (da > POM_HL - 1 and abs(b) > POM_HW - 1)
        m = self._mask(t, POM_A - POM_HL / self.sa - 1, POM_A + POM_HL / self.sa + 1, POM_HW + 1)
        e = edge(m, lib.W, lib.H)
        for (x, y) in m:
            if (x, y) in e:
                self._put(cv, x, y, 'k')
                continue
            a, b = self.ab(x, y)
            bb = b * self.dark
            ch = 'I' if bb < -2.0 else ('J' if bb < 0.0 else ('L' if bb < 2.0 else 'M'))
            self._put(cv, x, y, ch)
        return m

    def draw_guard(self, cv):
        ga = max(GUARD_A * self.sa, 2.5)
        m = self._mask(lambda a, b: abs(a * self.sa) <= ga and abs(b) <= GUARD_HW, -ga / self.sa - 1, ga / self.sa + 1,
                       GUARD_HW + 1)
        e = edge(m, lib.W, lib.H)
        # lit face: the side of the thickness that faces the upper-left
        lit_pos = (self.u[0] + self.u[1]) < 0
        tones = "JIKKLMN"
        for (x, y) in m:
            if (x, y) in e:
                self._put(cv, x, y, 'k')
                continue
            a, b = self.ab(x, y)
            s = (a * self.sa + ga) / (2 * ga)          # 0 grip side .. 1 tip side
            if not lit_pos:
                s = 1 - s
            s = 1 - s                                   # 0 = lit side
            ch = tones[min(len(tones) - 1, int(s * len(tones)))]
            bb = b * self.dark
            if bb > GUARD_HW - 2.2:
                ch = {'J': 'K', 'I': 'K', 'K': 'L', 'L': 'M', 'M': 'N', 'N': 'N'}[ch]
            elif bb < -GUARD_HW + 2.2 and ch in 'KL':
                ch = 'J'
            self._put(cv, x, y, ch)
        return m
