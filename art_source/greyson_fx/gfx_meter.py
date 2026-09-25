"""Greyson's hype meter (UI): the cannon's BATTERY, charged by the crowd. Not the player's HYPE meter (a gold bar
with a megaphone medallion, bottom right): this is a purple battery in Computah's paint, the crowd feeding it,
beside Greyson's own boss bar. The house UI style: DB32-leaning, a black keyline, alpha 0/255 except where noted.
Each part ships with a pre-scaled _3x copy for the HUD, like the other meters.
  greyson_hype_frame   80x20  the battery: a crowd emblem on the left (three fans, arms up, in the crowd's
                              cyan), a lead from it into a purple casing with six cell windows, and the casing's
                              terminal nub on the right
  greyson_hype_cell    7x10   one charged cell: the crowd's energy, cyan to white-hot at the top
  greyson_hype_pop     3 x 11x14  the burst over a cell as it charges (a pose lands): once at 0.05 s
  greyson_hype_full    2 x 80x20  the whole battery lit when all six are charged: alternate at 0.2 s (2.5
                              flashes a second, under the 3 a second limit), until the spirit bomb takes over
Layout (1x texels; x3 for the _3x): the six cell windows are at x 25 + 8k (k = 0..5), y 5, each 7x10; draw a
charged cell there, and its pop centred on the window (at x 23 + 8k, y 3). PROPOSED SPOT: the meter's top-left at
screen (1212, 97): 12 px right of his boss bar's end (the bar is x 720-1200, y 100-154), centred on the bar's
height, so it reads as part of his block and nowhere near the player's meter (bottom right).
"""
import math

K = '000000'
P = ('E0B8FF', 'C892F2', 'A063DC', '7C3BB4', '592687', '391555')   # the casing: Computah's violets, a highlight
CY = ('FFFFFF', 'E6F7FF', 'B4DCFF', '5FE1FF', '2FA8E0', '2E5FB0', '1E3566')
N0 = '1A1828'
W, H = 80, 20
CELL_X0, CELL_Y, CELL_W, CELL_H, PITCH = 25, 5, 7, 10, 8


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [[None] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def image(self):
        from PIL import Image
        im = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        px = im.load()
        for y in range(self.h):
            for x in range(self.w):
                c = self.p[y][x]
                if c:
                    px[x, y] = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
        return im


def casing(c, lit=False):
    """The battery body: x 21-73, y 1-18, rounded, lit on its top edge; six windows; the nub x 74-77."""
    x0, x1, y0, y1 = 21, 73, 1, 18
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            corner = (x in (x0, x1)) and (y in (y0, y1))
            if corner:
                continue
            edge = x in (x0, x1) or y in (y0, y1) or (x in (x0 + 1, x1 - 1) and y in (y0, y1))
            if edge:
                col = K
            elif y == y0 + 1:
                col = (CY[1] if lit else P[0])
            elif y == y0 + 2:
                col = (CY[3] if lit else P[1])
            elif y >= y1 - 2:
                col = P[4] if y == y1 - 2 else P[5]
            else:
                col = P[2] if x < x0 + 3 else P[3]
            c.set(x, y, col)
    # the terminal nub
    for y in range(6, 14):
        for x in range(74, 78):
            edge = x == 77 or y in (6, 13) or x == 74
            c.set(x, y, K if edge and x != 74 else (P[1] if y < 9 else P[3]))
    c.set(77, 6, None)
    c.set(77, 13, None)
    # six cell windows, dark, each with a black rim
    for k in range(6):
        wx = CELL_X0 + PITCH * k
        for y in range(CELL_Y - 1, CELL_Y + CELL_H + 1):
            for x in range(wx - 1, wx + CELL_W + 1):
                inside = wx <= x < wx + CELL_W and CELL_Y <= y < CELL_Y + CELL_H
                c.set(x, y, N0 if inside else K)
        # a tick under each window, the casing's lit lip over it
        c.set(wx + 3, CELL_Y + CELL_H + 1, P[2])


def crowd(c, lit=False):
    """The crowd emblem: a round badge with three fans, arms up, the lead running from it into the battery."""
    cx, cy, r = 9.5, 10.0, 9.2
    for y in range(20):
        for x in range(20):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d > r:
                continue
            if d > r - 1.0:
                col = K
            elif d > r - 2.2:
                lit_side = (x + 0.5 - cx) + (y + 0.5 - cy) < 0
                col = (CY[1] if lit else P[1]) if lit_side else P[3]
            else:
                col = N0
            c.set(x, y, col)
    fans = [(5, 11), (9, 9), (13, 11)]        # head positions
    for (hx, hy) in fans:
        for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
            c.set(hx + dx, hy + dy, CY[2])
        c.set(hx, hy, CY[0])
        for dy in range(2, 6):                 # shoulders
            c.set(hx - 1, hy + dy, CY[3]) if dy == 2 else None
            c.set(hx + 2, hy + dy, CY[3]) if dy == 2 else None
            c.set(hx, hy + dy, CY[4])
            c.set(hx + 1, hy + dy, CY[4])
        # arms up
        c.set(hx - 1, hy - 1, CY[3])
        c.set(hx - 2, hy - 2, CY[2])
        c.set(hx + 2, hy - 1, CY[3])
        c.set(hx + 3, hy - 2, CY[2])
    # the lead from the badge into the battery
    for x in range(19, 21):
        c.set(x, 9, CY[3])
        c.set(x, 10, CY[4])
        c.set(x, 8, K)
        c.set(x, 11, K)


def frame_part(lit=False):
    c = Canvas(W, H)
    casing(c, lit)
    crowd(c, lit)
    return c


def cell_part():
    c = Canvas(CELL_W, CELL_H)
    for y in range(CELL_H):
        for x in range(CELL_W):
            col = CY[0] if y == 0 else (CY[1] if y == 1 else (CY[2] if y < 4 else (CY[3] if y < 7 else (CY[4] if y < 9 else CY[5]))))
            if x == CELL_W - 1 and y > 1:
                col = CY[4] if y < 7 else CY[5]
            c.set(x, y, col)
    c.set(1, 1, CY[0])
    return c


def pop_frames():
    out = []
    for f in range(3):
        c = Canvas(11, 14)
        cx, cy = 5.5, 7.0
        r = [3.0, 5.5, 6.5][f]
        for y in range(14):
            for x in range(11):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                if f < 2 and d <= r * (0.6 if f == 0 else 0.45):
                    c.set(x, y, CY[0])
                elif abs(abs(dx) - abs(dy)) < 0.6 and d <= r:
                    c.set(x, y, CY[1] if f < 2 else CY[3])
                elif (abs(dx) < 0.6 or abs(dy) < 0.6) and d <= r * 1.1:
                    c.set(x, y, CY[0] if f < 2 else CY[2])
        out.append(c)
    return out


def full_frames():
    a = frame_part(lit=True)
    b = frame_part(lit=False)
    for fr, hot in ((a, True), (b, False)):
        for k in range(6):
            cell = cell_part()
            wx = CELL_X0 + PITCH * k
            for y in range(CELL_H):
                for x in range(CELL_W):
                    col = cell.p[y][x]
                    if hot and y > 1:
                        col = CY[1] if y < 5 else CY[3]
                    fr.set(wx + x, CELL_Y + y, col)
    return [a, b]


def parts():
    return {'greyson_hype_frame': [frame_part()], 'greyson_hype_cell': [cell_part()],
            'greyson_hype_pop': pop_frames(), 'greyson_hype_full': full_frames()}
