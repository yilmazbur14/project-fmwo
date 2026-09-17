"""'ENTER THE DISCORD' title logo. Transparent PNG, DB32 only, shown at 3x.

Big bevelled brass 'DISCORD' (the O is a round server icon with the chat mascot), with a blurple
chat bubble reading 'ENTER THE' perched on top-left like a message being typed.
"""
import math, os
from lib import *
from invite import MASCOT

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')


def rrect(x, y, x0, y0, x1, y1, r):
    """inside test for a rounded rect (inclusive bounds) with corner radius r"""
    if x < x0 or x > x1 or y < y0 or y > y1:
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.5


class Mask:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.m = [[False] * w for _ in range(h)]

    def paint(self, fn, val=True):
        for y in range(self.h):
            for x in range(self.w):
                if fn(x, y):
                    self.m[y][x] = val

    def rows(self):
        return [''.join('#' if v else '.' for v in r) for r in self.m]



F79 = {
    'E': ["#######", "#######", "##.....", "######.", "######.", "##.....", "##.....", "#######", "#######"],
    'N': ["##...##", "###..##", "####.##", "#######", "##.####", "##..###", "##...##", "##...##", "##...##"],
    'T': ["#######", "#######", "..###..", "..###..", "..###..", "..###..", "..###..", "..###..", "..###.."],
    'R': ["######.", "#######", "##...##", "##...##", "#######", "######.", "##.###.", "##..###", "##...##"],
    'H': ["##...##", "##...##", "##...##", "#######", "#######", "##...##", "##...##", "##...##", "##...##"],
}


def f79_width(s):
    w = 0
    for ch in s:
        w += 4 if ch == ' ' else 7 + 2
    return w - 2


ICON_STYLE = 'white'
LW, LH, ST = 28, 36, 8       # big letter box and stroke


def letter_O():
    m = Mask(LW, LH)
    m.paint(lambda x, y: rrect(x, y, 0, 0, LW - 1, LH - 1, 8))
    m.paint(lambda x, y: rrect(x, y, ST, ST, LW - 1 - ST, LH - 1 - ST, 3), False)
    return m


def letter_C():
    m = letter_O()
    m.paint(lambda x, y: x >= LW - ST and 13 <= y <= LH - 14, False)
    return m


def letter_D():
    m = Mask(LW, LH)
    m.paint(lambda x, y: rrect(x, y, 0, 0, LW - 1, LH - 1, 9) or (x < 12))
    m.paint(lambda x, y: rrect(x, y, ST, ST, LW - 1 - ST, LH - 1 - ST, 3) or (ST <= x < 12 and ST <= y <= LH - 1 - ST), False)
    return m


def letter_I():
    m = Mask(10, LH)
    m.paint(lambda x, y: True)
    return m


def letter_S():
    m = Mask(LW, LH)
    top = lambda x, y: rrect(x, y, 0, 0, LW - 1, 21, 8) and not rrect(x, y, ST, ST, LW - 1 - ST, 21 - ST + 1, 2)
    bot = lambda x, y: rrect(x, y, 0, 14, LW - 1, LH - 1, 8) and not rrect(x, y, ST, 14 + ST - 1, LW - 1 - ST, LH - 1 - ST, 2)
    m.paint(lambda x, y: (top(x, y) and not (x >= LW - ST and 11 <= y <= 21)) or
            (bot(x, y) and not (x < ST and 14 <= y <= 24)))
    # spine: clear the inner overlap so the middle stroke is one bar
    for _ in range(2):
        for y in range(m.h):
            for x in range(m.w):
                if m.m[y][x]:
                    n = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                            if 0 <= x + dx < m.w and 0 <= y + dy < m.h and m.m[y + dy][x + dx])
                    if n <= 1:
                        m.m[y][x] = False
    return m


def letter_R():
    m = Mask(LW, LH)
    bowl = lambda x, y: (rrect(x, y, 0, 0, LW - 1, 22, 8) or x < 12) and y <= 22
    hole = lambda x, y: rrect(x, y, ST, ST, LW - 1 - ST, 22 - ST, 2) or (ST <= x < 12 and ST <= y <= 22 - ST)
    m.paint(lambda x, y: (bowl(x, y) and not hole(x, y)) or x < ST)
    # diagonal leg
    def leg(x, y):
        if y < 18:
            return False
        t = (y - 18) / float(LH - 1 - 18)
        cx = 11 + t * (LW - 1 - 11 - 4)
        return cx - 1 <= x <= cx + 8
    m.paint(leg)
    return m


def big_word():
    glyphs = [letter_D(), letter_I(), letter_S(), letter_C(), None, letter_R(), letter_D()]
    gap = 4
    widths = [g.w if g else LH for g in glyphs]
    W = sum(widths) + gap * (len(glyphs) - 1)
    word = Mask(W, LH)
    x = 0
    slots = []
    for g, w in zip(glyphs, widths):
        if g:
            for yy in range(LH):
                for xx in range(g.w):
                    if g.m[yy][xx]:
                        word.m[yy][x + xx] = True
        slots.append((x, w))
        x += w + gap
    return word, slots


def render():
    word, slots = big_word()
    PAD_L, PAD_T = 4, 26
    CW, CH = word.w + PAD_L + 10, LH + PAD_T + 8
    c = Canvas(CW, CH)
    ox, oy = PAD_L, PAD_T
    inside = lambda x, y: 0 <= x < word.w and 0 <= y < word.h and word.m[y][x]
    # extrusion (drop depth) down-right, then outline around letters + extrusion
    depth = 4
    ext = set()
    for y in range(word.h):
        for x in range(word.w):
            if word.m[y][x]:
                for d in range(1, depth + 1):
                    ext.add((x + d // 2, y + d))
    for (x, y) in ext:
        c.set(ox + x, oy + y, P0)
    solid = ext | {(x, y) for y in range(word.h) for x in range(word.w) if word.m[y][x]}
    for (x, y) in list(solid):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if (x + dx, y + dy) not in solid:
                    c.set(ox + x + dx, oy + y + dy, K)
    for (x, y) in ext:
        if not inside(x, y):
            # darker lower face of the extrusion
            col = P0 if (x, y - 1) in solid and not inside(x - 1, y) else N0
            if inside(x, y - 1) or inside(x - 1, y - 1):
                col = BR
            c.set(ox + x, oy + y, col)
    # brass face with bevel
    for y in range(word.h):
        for x in range(word.w):
            if not word.m[y][x]:
                continue
            t = y / float(LH - 1)
            col = TN
            if t < 0.22:
                col = YL
            elif t < 0.30:
                col = YL if dith(x, y, 0.5) else TN
            elif t > 0.80:
                col = GO
            elif t > 0.70:
                col = GO if dith(x, y, 0.5) else TN
            up, left = inside(x, y - 1), inside(x - 1, y)
            down, right = inside(x, y + 1), inside(x + 1, y)
            if not up or not left:
                col = WH if t < 0.3 else SK
            elif not down or not right:
                col = OL if t > 0.5 else GO
            c.set(ox + x, oy + y, col)
    # shine streak across the upper part
    for y in range(word.h):
        for x in range(word.w):
            if word.m[y][x] and 0 < (x - y * 0.5) % 46 < 3 and y > 1 and inside(x, y - 1) and inside(x - 1, y) \
                    and inside(x + 1, y) and inside(x, y + 1):
                c.set(ox + x, oy + y, WH if y < LH * 0.3 else SK)

    # the O: a round server icon with the chat mascot
    sx, sw = slots[4]
    icx, icy = ox + sx + sw / 2.0 - 0.5, oy + LH / 2.0 - 0.5
    R = LH / 2.0
    for y in range(int(icy - R - 3), int(icy + R + 6)):
        for x in range(int(icx - R - 3), int(icx + R + 6)):
            d = math.hypot(x - icx, y - icy)
            dd = math.hypot(x - icx - 2, y - icy - 4)
            if d > R + 1 and dd <= R and c.get(x, y) is None:
                c.set(x, y, N0 if dd < R - 1 else K)
    white = ICON_STYLE == 'white'
    for y in range(int(icy - R - 2), int(icy + R + 3)):
        for x in range(int(icx - R - 2), int(icx + R + 3)):
            d = math.hypot(x - icx, y - icy)
            if d <= R + 1:
                if d > R:
                    col = K
                else:
                    a = (x - icx) + (y - icy)
                    if white:
                        col = WH
                        if d > R - 3.2:
                            col = WH if a < -4 else G5 if a > 6 else WH2
                        elif a > 14:
                            col = WH2
                    else:
                        col = RB
                        if d > R - 3.2:
                            col = SB if a < -4 else IN if a > 6 else RB
                        if d > R - 1.2 and a < -10:
                            col = WH2
                c.set(x, y, col)
    mx, my = int(round(icx - 14.5)), int(round(icy - 10.5))
    for j, row in enumerate(MASCOT):
        for i, ch in enumerate(row):
            for a in (0, 1):
                for b in (0, 1):
                    X, Y = mx + i * 2 + a, my + j * 2 + b
                    if ch == 'B':
                        if white:
                            col = RB
                            if j <= 1 or (j <= 3 and (i * 2 + a) <= 3):
                                col = SB
                            if j >= 9 or (j >= 7 and (i * 2 + a) >= 26):
                                col = IN
                        else:
                            col = WH if j < 7 else WH2
                        c.set(X, Y, col)
                    elif j in (4, 5, 6) and 0 < i < 14:
                        c.set(X, Y, WH if white else N0)
    if not white:
        for j, row in enumerate(MASCOT):
            for i, ch in enumerate(row):
                if ch == 'B':
                    for a in (0, 1):
                        X, Y = mx + i * 2 + a, my + j * 2 + 2
                        if c.get(X, Y) == RB and (j + 1 >= len(MASCOT) or MASCOT[j + 1][i] != 'B'):
                            c.set(X, Y, IN)
    # notification badge on the icon
    bx, by = int(icx + R * 0.55), int(icy - R - 2)
    badge = ["..KKKKK..", ".KppppdK.", "KppWWpddK", "KppdWpddK", "KpppWpddK", "KpppWpddK", "KdpWWWddK",
             ".KdddddK.", "..KKKKK.."]
    c.grid(bx, by, badge, {'K': K, 'p': PK, 'd': RD, 'W': WH}, skip='.')

    # 'ENTER THE' chat bubble
    small = "ENTER THE"
    tw = f79_width(small)
    bx0, by0 = ox + 1, 1
    bx1, by1 = bx0 + tw + 15, by0 + 19
    for y in range(by0, by1 + 1):
        for x in range(bx0, bx1 + 1):
            if not rrect(x, y, bx0, by0, bx1, by1, 5):
                continue
            edge = not all(rrect(x + dx, y + dy, bx0, by0, bx1, by1, 5) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            col = K if edge else RB
            if not edge and y == by0 + 1:
                col = SB
            if not edge and y >= by1 - 2:
                col = IN
            c.set(x, y, col)
    tail = ["KRRRRK", "KRRRK.", "KRRK..", "KRK...", "KK...."]
    for j, row in enumerate(tail):
        for i, ch in enumerate(row):
            if ch != '.':
                c.set(bx0 + 7 + i, by1 + j, K if ch == 'K' else IN)
    for layer in ('shadow', 'face'):
        tx, ty = bx0 + 8, by0 + 5
        for ch in small:
            if ch == ' ':
                tx += 4
                continue
            g = F79[ch]
            for j, row in enumerate(g):
                for i, v in enumerate(row):
                    if v == '#':
                        if layer == 'shadow':
                            c.set(tx + i, ty + j + 1, IN)
                        else:
                            c.set(tx + i, ty + j, WH if j < 4 else WH2)
            tx += 9
    # typing dots after the bubble
    dx0 = bx1 + 5
    for k in range(3):
        c.grid(dx0 + k * 6, by1 - 7, ['.KK.', 'KwwK', 'KwgK', '.KK.'], {'K': K, 'w': WH2, 'g': G5}, skip='.')
    return c


def crop_to_content(c, pad=1):
    xs = [x for y in range(c.h) for x in range(c.w) if c.p[y][x] is not None]
    ys = [y for y in range(c.h) for x in range(c.w) if c.p[y][x] is not None]
    x0, x1, y0, y1 = max(0, min(xs) - pad), min(c.w - 1, max(xs) + pad), max(0, min(ys) - pad), min(c.h - 1, max(ys) + pad)
    out = Canvas(x1 - x0 + 1, y1 - y0 + 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            out.p[y - y0][x - x0] = c.p[y][x]
    return out


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        ICON_STYLE = sys.argv[1]
    c = crop_to_content(render())
    p = c.save(os.path.join(OUT, 'logo_%s.png' % ICON_STYLE))
    crop_zoom(p, os.path.join(OUT, 'logo_%s_6x.png' % ICON_STYLE), 0, 0, c.w, c.h, 6)
    print(c.w, c.h)
