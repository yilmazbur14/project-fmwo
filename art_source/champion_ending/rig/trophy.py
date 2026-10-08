"""The champion trophy (two takes) and the stand it waits on.

Built as character grids: a cup is a stack of row spans filled with a polished-metal band ramp
(light from the upper left, like the cast), auto-outlined in pure black, then hand-finished
(handles, emblem, speculars). Each take is symmetric in silhouette about its centre column CX.

Every trophy image's bottom row is its plinth's black outline; that row is what rests on the
stand's seat row (STAND_SEAT_Y) and what Burak's hands grip the sides of (GRIP_Y rows up).
"""
import math
from common import PROP, grid_to_image

GOLD_BANDS = [(0.12, 2), (0.30, 1), (0.45, 2), (0.62, 3), (0.80, 4), (0.92, 5), (1.01, 4)]


def band(u, shift=0):
    for lim, tone in GOLD_BANDS:
        if u < lim:
            return str(max(1, min(5, tone + shift)))
    return '4'


class Grid:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.c = [['.'] * w for _ in range(h)]

    def get(self, x, y):
        return self.c[y][x] if 0 <= x < self.w and 0 <= y < self.h else '.'

    def set(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y][x] = ch

    def metal(self, y, x0, x1, shift=0):
        n = x1 - x0 + 1
        for x in range(x0, x1 + 1):
            self.set(x, y, band((x - x0 + 0.5) / n, shift))

    def fill(self, y, x0, x1, ch):
        for x in range(x0, x1 + 1):
            self.set(x, y, ch)

    def outline(self, ch='K'):
        filled = {(x, y) for y in range(self.h) for x in range(self.w) if self.c[y][x] != '.'}
        for (x, y) in list(filled):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in filled and 0 <= q[0] < self.w and 0 <= q[1] < self.h:
                    self.c[q[1]][q[0]] = ch

    def stamp(self, rows, x0, y0, mirror=False):
        """Paste a hand-drawn part; mirror=True flips it to the other side and swaps the gold
        ramp toward shade (the right side is the dark side)."""
        w = max(len(r) for r in rows)
        for j, r in enumerate(rows):
            for i, ch in enumerate(r.ljust(w, '.')):
                if ch == '.':
                    continue
                x = (self.w - 1 - (x0 + i)) if mirror else (x0 + i)
                if mirror:
                    ch = {'1': '3', '2': '4', '3': '5', 'W': '2'}.get(ch, ch)
                self.set(x, y0 + j, ch)

    def rows(self):
        return [''.join(r) for r in self.c]

    def image(self, pal=PROP):
        return grid_to_image(self.rows(), pal)


# ================================================================ TAKE A: the Glove Cup
# A classic two-handled loving cup on a navy plinth with a gold name plate, a blue boxing glove
# (Burak's own glove blue) on the bowl.  17 x 16, centre column CX = 8.
A = dict(W=17, H=16, CX=8, PLINTH=(3, 13), GRIP_Y=2)


def trophy_a(back=False):
    W, H = A['W'], A['H']
    g = Grid(W, H)
    # the mouth, seen from a little above: dark inside, the inner back-right wall catching light
    g.fill(1, 4, 12, '5')
    g.set(3, 1, '2'); g.set(13, 1, '3')
    for x in (10, 11):
        g.set(x, 1, '4')
    g.set(12, 1, '3')
    g.metal(2, 2, 14, -1)                       # front lip, brighter and wider than the bowl
    for y, x0, x1, sh in ((3, 3, 13, 0), (4, 3, 13, 0), (5, 4, 12, 0), (6, 4, 12, 0),
                          (7, 5, 11, 1), (8, 6, 10, 1)):
        g.metal(y, x0, x1, sh)
    g.metal(9, 7, 9, 1)                         # stem
    g.metal(10, 6, 10, 0)                       # knop
    g.metal(11, 5, 11, 0)                       # foot
    g.fill(12, 3, 13, 'm')                      # plinth: lit top face
    g.fill(13, 3, 13, 'n'); g.fill(14, 3, 13, 'n')
    g.set(3, 13, 'o'); g.set(3, 14, 'o')
    g.outline()
    g.fill(13, 6, 10, '3'); g.set(6, 13, '2'); g.set(10, 13, '4')   # name plate
    handle = [
        '.KK',
        'K2K',
        'K2K',
        'K2K',
        'K3KK',
        '.K3K',
        '..KK',
    ]
    g.stamp(handle, 0, 1)
    g.stamp(handle, 0, 1, mirror=True)
    # the glove: profile, punching right; white cuff, blue mitt in Burak's blues
    emblem = [
        '..KKK..',
        '.KcbbK.',
        'KwKbbbK',
        'KwKbbBK',
        '.KKBBK.',
        '...KK..',
    ]
    if not back:                                # seen from behind: plain gold, no glove
        g.stamp(emblem, 5, 3)
    # speculars (upper-left light)
    g.set(4, 2, 'W'); g.set(4, 3, 'W'); g.set(4, 4, '1')
    return g


# ================================================================ TAKE B: the Title Cup
# A lidded chalice with a star finial, its plinth wrapped in a championship title belt: red
# leather strap (Burak's headband red), gold studs, and a gold centre plate carrying the arena's
# own slanted '#' crest.  17 x 19, centre column CX = 8.
B = dict(W=17, H=20, CX=8, PLINTH=(1, 15), GRIP_Y=3)


def trophy_b(back=False):
    W, H = B['W'], B['H']
    g = Grid(W, H)
    g.stamp(['.2.', '2W3', '.4.'], 7, 1)       # star finial
    g.set(8, 4, '3')                           # its stem
    g.metal(5, 6, 10, -1)                      # lid dome
    g.metal(6, 4, 12, 0)                       # lid rim
    g.metal(8, 2, 14, -1)                      # the cup's flared lip
    for y, x0, x1, sh in ((9, 3, 13, 0), (10, 3, 13, 0), (11, 4, 12, 0), (12, 5, 11, 1),
                          (13, 6, 10, 1)):
        g.metal(y, x0, x1, sh)
    g.metal(14, 7, 9, 0)                       # stem
    for y in range(15, 19):                    # the belted plinth
        g.fill(y, 1, 15, 'n')
    g.outline()
    for x in range(3, 14):                     # the lid sits in the cup: a black seam
        g.set(x, 7, 'K')
    # the title belt round the plinth: red strap, gold studs
    for x in range(1, 16):
        g.set(x, 15, 'K'); g.set(x, 16, 'R'); g.set(x, 17, 'q'); g.set(x, 18, 'K')
    for sx in (2, 14):
        g.set(sx, 16, '2' if sx < 8 else '4'); g.set(sx, 17, '3' if sx < 8 else '5')
    # the buckle: a gold plate with the arena's slanted '#'
    plate = [
        '.KKKKKKKKK.',
        'K122R2R334K',
        'K2RRRRRR34K',
        'K23R3R3445K',
        'K2RRRRRR45K',
        'K3R4R44455K',
        '.KKKKKKKKK.',
    ]
    if not back:                                # seen from behind: just the strap
        g.stamp(plate, 3, 13)
    g.set(4, 8, 'W'); g.set(4, 9, 'W'); g.set(4, 10, '1'); g.set(7, 5, 'W')
    return g


# ================================================================ the stand
# A round podium in the ringside skirt's navy: a red velvet top, a gold lip round it, a gold
# foot ring and the skirt's gold studs.  23 x 13, centre column CX = 11.  The trophy's bottom
# (outline) row sits on SEAT_Y, centred on CX.
S = dict(W=23, H=13, CX=11, SEAT_Y=4)
TOP_CY, TOP_RX, TOP_RY = 3.6, 9.6, 2.6
DRUM_DEPTH = 5


def _half(x, rx):
    t = (x - S['CX']) / rx
    return math.sqrt(max(0.0, 1 - t * t))


def stand():
    W, H = S['W'], S['H']
    g = Grid(W, H)
    spans = {}
    for x in range(W):
        h = _half(x, TOP_RX + 0.5)
        if h <= 0:
            continue
        top = round(TOP_CY - TOP_RY * h)
        front = round(TOP_CY + TOP_RY * h)
        spans[x] = (top, front)
        u = (x - (S['CX'] - TOP_RX) + 0.5) / (2 * TOP_RX + 1)
        for y in range(top, front):
            g.set(x, y, 'R')
        g.set(x, front, band(u, -1))            # gold lip
        for y in range(front + 1, front + 1 + DRUM_DEPTH):
            g.set(x, y, 'm' if u < 0.18 else ('o' if u < 0.62 else 'n'))
        g.set(x, front + 1 + DRUM_DEPTH, band(u, 1))   # gold foot ring
    g.outline()
    for x, (top, front) in spans.items():
        if x < S['CX'] + 2 and g.get(x, top) == 'R':
            g.set(x, top, 'r')
        if x > S['CX'] + 1 and g.get(x, front - 1) == 'R':
            g.set(x, front - 1, 'q')
    for sx in (5, 11, 17):
        top, front = spans[sx]
        g.set(sx, front + 3, '3' if sx < 14 else '4')
    return g


def trophy(take, back=False):
    return trophy_a(back) if take == 'A' else trophy_b(back)


def spec(take):
    return A if take == 'A' else B
