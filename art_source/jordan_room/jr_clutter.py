"""Jordan's room - the rug (part of room_floor) and room_clutter: flat mess on
the boards. Clothes all over the ground, a pizza box, cans, a chip bag, game
cases, manga, socks. Everything here lies flat, so the bosses can stand on it.

Clothes are built at true size for the room (a T-shirt laid flat is ~30x20
texels: 0.65 m wide, depth foreshortened) from a silhouette that is jittered,
turned in the floor plane and squashed into the 3/4 view, then lit from the
upper left with fold lines and a keyline, so no two pieces look stamped.

The heaviest mess hugs the walls and the front edge; the walkable middle only
gets flat, scattered bits. The doorway path and the chair spot stay clear.
"""
import math
import random

import numpy as np

from jr_lib import Canvas, W, H, IDX, KEYS, T, DARKER, border, poly_mask, rect_mask, \
    ellipse_mask, bayer, line_pts
from jr_geom import FLOOR_Y, NEAR_Y
from jr_track import Null, Tracker

RAMPS = {
    'red': ('r', 'R', 'B'), 'green': ('1', '2', '3'), 'white': ('W', 'P', 'g'),
    'black': ('E', '6', 'N'), 'grey': ('g', 'F', 'D'), 'blue': ('U', '7', 'I'),
    'teal': ('c', '3', '4'), 'yellow': ('Y', 'd', 'A'), 'purple': ('8', 'V', 'M'),
    'pink': ('P', '8', 'V'), 'orange': ('d', 'O', 'w'), 'navy': ('U', 'I', 'N'),
    'denim': ('u', 'U', 'I'), 'olive': ('9', '5', '6'),
}
SQUASH = 0.7          # floor depth foreshortening for things lying flat

# ---------------------------------------------------------------- silhouettes
SHAPES = {
    'tshirt': [(11, 0), (5, 1), (0, 7), (3, 12), (8, 10), (8, 27), (22, 27), (22, 10),
               (27, 12), (30, 7), (25, 1), (19, 0), (15, 3)],
    'hoodie': [(10, 0), (4, 3), (0, 11), (1, 20), (6, 19), (7, 31), (27, 32), (28, 19),
               (35, 24), (38, 17), (30, 4), (22, 0), (17, 5)],
    'jeans': [(0, 2), (14, 0), (16, 9), (30, 6), (42, 10), (42, 16), (28, 14), (17, 17),
              (12, 16), (8, 30), (2, 30), (1, 16)],
    'shorts': [(0, 0), (18, 0), (19, 11), (11, 12), (9, 7), (7, 12), (0, 11)],
    'towel': [(0, 0), (34, 2), (33, 16), (-1, 14)],
    'sock': [(0, 0), (5, 0), (6, 8), (12, 9), (12, 13), (2, 13), (0, 9)],
}


def _shape(kind, angle, seed, jitter=1.1, scale=1.0):
    rnd = random.Random(seed)
    pts = [(x * scale + rnd.uniform(-jitter, jitter), y * scale + rnd.uniform(-jitter, jitter))
           for (x, y) in SHAPES[kind]]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    ca, sa = math.cos(angle), math.sin(angle)
    out = [(cx + (x - cx) * ca - (y - cy) * sa, cy + ((x - cx) * sa + (y - cy) * ca) * SQUASH)
           for (x, y) in pts]
    mx = min(p[0] for p in out) - 2
    my = min(p[1] for p in out) - 2
    out = [(x - mx, y - my) for (x, y) in out]
    w = int(math.ceil(max(p[0] for p in out))) + 3
    h = int(math.ceil(max(p[1] for p in out))) + 3
    return out, w, h, (lambda x, y: (cx + (x - cx) * ca - (y - cy) * sa - mx,
                                     cy + ((x - cx) * sa + (y - cy) * ca) * SQUASH - my))


def cloth(kind, ramp, angle=0.0, seed=0, folds=3, print_=None, scale=1.0):
    """A flat, crumpled garment. Returns a Canvas."""
    pts, w, h, tf = _shape(kind, angle, seed, scale=scale)
    m = poly_mask(pts, w, h)
    hi, base, lo = RAMPS[ramp]
    c = Canvas(w, h)
    c.fill(m, base)
    # light from the upper left, shade on the lower right edges
    up = m & ~np.roll(m, 1, axis=0)
    lf = m & ~np.roll(m, 1, axis=1)
    dn = m & ~np.roll(m, -1, axis=0)
    rt = m & ~np.roll(m, -1, axis=1)
    c.fill(dn | rt, lo)
    c.fill((up | lf) & ~(dn | rt), hi)
    # fold lines: a shadow crease with its lit ridge just above
    rnd = random.Random(seed * 31 + 7)
    ys, xs = np.nonzero(m)
    for _ in range(folds):
        i = rnd.randrange(len(xs))
        x0, y0 = xs[i], ys[i]
        ln = rnd.randrange(5, 12)
        ang = rnd.uniform(-0.6, 0.6)
        x1 = int(round(x0 + math.cos(ang) * ln))
        y1 = int(round(y0 + math.sin(ang) * ln * 0.6))
        for (x, y) in line_pts(x0, y0, x1, y1):
            if 0 <= x < w and 1 <= y < h - 1 and m[y, x] and m[y - 1, x] and m[y + 1, x]:
                c.set(x, y, lo)
                if m[y - 1, x] and c.get(x, y - 1) == base:
                    c.set(x, y - 1, hi)
    # neck hole / waistband details
    if kind in ('tshirt', 'hoodie'):
        nx, ny = tf(15 if kind == 'tshirt' else 17, 2.5 if kind == 'tshirt' else 5)
        hole = ellipse_mask(nx, ny, 3.2 if kind == 'tshirt' else 4.2, 1.8, w, h) & m
        c.fill(hole, lo)
        c.fill(hole & ellipse_mask(nx, ny + 0.6, 2.0, 1.0, w, h), 'K')
    if kind == 'jeans':
        a, b = tf(2, 3), tf(14, 1)
        for (x, y) in line_pts(int(a[0]), int(a[1]), int(b[0]), int(b[1])):
            if 0 <= x < w and 0 <= y < h and m[y, x]:
                c.set(x, y, lo)
        px, py = tf(8, 6)
        c.set(int(px), int(py), 'd')                      # a rivet
    if kind == 'towel':
        for yy in (3, 11):
            a, b = tf(0, yy), tf(34, yy + 2)
            for (x, y) in line_pts(int(a[0]), int(a[1]), int(b[0]), int(b[1])):
                if 0 <= x < w and 0 <= y < h and m[y, x]:
                    c.set(x, y, 'W')
    if print_ is not None and kind in ('tshirt', 'hoodie'):
        px, py = tf(15 if kind == 'tshirt' else 17, 15 if kind == 'tshirt' else 20)
        c.stamp(PRINTS[print_], int(px) - 2, int(py) - 2)
    c.a[border(m)] = IDX['K']
    return c


PRINTS = {
    'star': ["..Y..", ".YYY.", "YYYYY", ".Y.Y."],
    'heart': [".r.r.", "rrrrr", ".rrr.", "..r.."],
    'mascot': [".UUU.", "UWUWU", "UUUUU", ".U.U."],
    'skull': [".WWW.", "WKWKW", ".WWW.", ".W.W."],
    'pixel': ["1.2.3", ".c.U.", "8.Y.r", "....."],
}

# ---------------------------------------------------------------- small hard items
PIZZA = [
    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
    "KddddddddddddddddddddddddddddK",
    "KdwwdddddddddddddddddddddwdddK",
    "KddddddddddddBBBBddddddddddddK",
    "KdddddddddddBRRRRBdddddddddddK",
    "KddddddddddddBBBBdddddddddwddK",
    "KdddwddddddddddddddddddddddddK",
    "KddddddddddddddddddddddddddddK",
    "KwwwwwwwwwwwwwwwwwwwwwwwwwwwwK",
    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
    "KwwwwwwwwwwwwwwwwwwwwwwwwwwwwK",
    "KwBBBBBBBBBBBBBBBBBBBBBBBBBBwK",
    "KwBKKKKKKKKBBBBBBBBBBBBBBBBBwK",
    "KwBKdddddddKBBBBBBBBBBwdBBBBwK",
    "KwBKdYYRYYYdKBBBBBBBBBBBBBBBwK",
    "KwBBKdYYYRYYdKBBBBBBBBBBBBBBwK",
    "KwBBBKdRYYYYdKBBBBBdBBBBBBBBwK",
    "KwBBBBKdYYRdKBBBBBBBBBBBBBBBwK",
    "KwBBBBBKdYdKBBBBBBBBBBwBBBBBwK",
    "KwBBBBBBKdKBBBBBBBBBBBBBBBBBwK",
    "KwBBBBBBBKBBBBBBBBBBBBBBBBBBwK",
    "KwwwwwwwwwwwwwwwwwwwwwwwwwwwwK",
    "KKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",
]
CAN = [
    ".KKKKKKKKK.",
    "KgbbaabbbbK",
    "KFbbWbbbbcK",
    "KgbbbbbbccK",
    ".KKKKKKKKK.",
]
CRUSHED = [
    ".KKKKKK.",
    "KbaKbbbK",
    "KgbbKbcK",
    "KgbbbccK",
    ".KKKKKK.",
]
CHIPS = [
    ".KKKKKKKKKKKKK.",
    "KYYYYYYYYYYYYYK",
    "KYOOOOOOOOOOOYK",
    "KYORRRROOOOOOYK",
    "KYORrrROOYYOOYK",
    "KYORRRROOOOOOYK",
    "KYOOOOOOOOOOOYK",
    "KdYYYYYYYYYYYdK",
    "KKdKKKKKKKKKdKK",
    "..KYdK..KdYK...",
    "...KK....KK....",
]
CONTROLLER = [
    "...KKKKKKKKKK...",
    "..KEEEEEEEEEEK..",
    ".KEEKEEEEEEcEEK.",
    "KEEKKKEEEEc8rEEK",
    "KEEEKEEEEEEYEEEK",
    "KEEEEKKKKKKEEEEK",
    ".KEEK......KEEK.",
    "..KK........KK..",
]
CASE = [
    "KKKKKKKKKKKK",
    "KaaaaaaaaabK",
    "KaPPPPPPPPbK",
    "KaPP88PPPPbK",
    "KaPP88PPPPbK",
    "KaPPPPPPPPbK",
    "KabbbbbbbbbK",
    "KbccccccccbK",
    "KKKKKKKKKKKK",
]
MANGA = [
    ".KKKKKKKKKKKKK.",
    "KWWWWWWKWWWWWPK",
    "KWggggWKWggggPK",
    "KWWWWWWKWWWWWPK",
    "KWgggWWKWWgggPK",
    "KWWWWWWKWWWWWPK",
    ".KKKKKKKKKKKKK.",
]
PAPER = [".KKK.", "KPggK", "KgPPK", ".KKK."]
PLATE = [
    "...KKKKKKKK...",
    ".KKPPPPPPPPKK.",
    "KPPWgdPPPPPPgK",
    "KPPPPPdPPgPPgK",
    ".KKgPPPPPPgKK.",
    "...KKKKKKKK...",
]
SNEAKER = [
    "...KKKKKK....",
    "..KWWPWWWKK..",
    ".KWKWKWKWPgK.",
    "KWWWWWWWWWggK",
    "KRRRRRRRRRRRK",
    ".KKKKKKKKKKK.",
]
WRAPPER = [".KKKK.", "KrYrrK", ".KKKK."]


def _hard(rows, ramp=None, flip=False):
    leg = None
    if ramp:
        a, b, c = RAMPS[ramp]
        leg = {'a': a, 'b': b, 'c': c}
    s = Canvas(max(len(r) for r in rows), len(rows))
    s.stamp(rows, 0, 0, leg, flip)
    return s


# (builder, x, y): x, y = top-left of the item in the room
def items():
    L = []

    def add(spr, x, y):
        L.append((spr, x, y))

    # by the door, off the entry path
    add(cloth('tshirt', 'green', 0.4, 1, print_='star'), 14, 166)
    add(cloth('sock', 'white', 0.3, 2), 20, 204)
    add(cloth('sock', 'white', -0.9, 3), 30, 208)
    add(cloth('sock', 'grey', 1.9, 4), 116, 226)
    # the left wall
    add(cloth('hoodie', 'grey', -0.3, 5, folds=5), 14, 246)
    add(cloth('jeans', 'denim', 0.2, 6, folds=4), 16, 290)
    add(cloth('shorts', 'pink', -0.5, 7), 56, 280)
    add(cloth('towel', 'teal', 0.1, 8), 20, 330)
    # the front edge
    add(_hard(PIZZA), 132, 320)
    add(_hard(CAN, 'green'), 166, 310)
    add(_hard(CHIPS), 194, 334)
    add(cloth('tshirt', 'black', -0.2, 9, print_='skull'), 214, 322)
    add(_hard(CASE, 'blue'), 262, 338)
    add(_hard(CASE, 'red'), 272, 333)
    add(_hard(MANGA), 300, 340)
    add(cloth('sock', 'white', 2.6, 10), 322, 334)
    add(_hard(CONTROLLER), 356, 338)
    add(_hard(CRUSHED, 'purple'), 380, 342)
    add(cloth('tshirt', 'red', 0.3, 11, print_='heart'), 398, 320)
    add(_hard(PLATE), 440, 340)
    add(cloth('sock', 'black', -0.4, 12), 462, 336)
    add(cloth('sock', 'black', 0.9, 13), 470, 340)
    add(cloth('hoodie', 'purple', 0.35, 14, folds=5, print_='mascot'), 494, 316)
    add(_hard(CAN, 'blue'), 548, 340)
    # round the desk and the PC (the chair spot stays empty)
    add(_hard(CAN, 'green', True), 342, 176)
    add(_hard(PAPER), 356, 188)
    add(_hard(PAPER), 364, 178)
    add(_hard(CRUSHED, 'blue'), 452, 182)
    add(_hard(PAPER), 468, 192)
    add(_hard(WRAPPER), 462, 174)
    add(_hard(CAN, 'purple'), 486, 178)
    add(_hard(MANGA), 516, 196)
    # the right wall
    add(cloth('tshirt', 'white', -0.35, 15, print_='pixel'), 586, 166)
    add(cloth('jeans', 'navy', 2.9, 16, folds=4), 580, 226)
    add(_hard(SNEAKER), 590, 280)
    add(_hard(SNEAKER, flip=True), 606, 288)
    add(cloth('sock', 'grey', 0.6, 17), 584, 306)
    add(cloth('towel', 'yellow', -0.25, 18), 560, 202)
    # a few flat things out on the open floor
    add(cloth('sock', 'white', -1.2, 19), 236, 232)
    add(_hard(CONTROLLER), 146, 262)
    add(cloth('tshirt', 'blue', 2.8, 20, folds=2), 392, 252)
    add(_hard(CASE, 'green'), 318, 300)
    add(_hard(WRAPPER), 508, 252)
    add(_hard(PAPER), 206, 196)
    add(cloth('sock', 'pink', 0.2, 21), 532, 212)
    # laundry that never made it to a basket: overlapping piles
    add(cloth('hoodie', 'navy', 2.7, 22, folds=5), 62, 312)
    add(cloth('tshirt', 'white', 0.9, 23, print_='mascot'), 78, 322)
    add(cloth('sock', 'grey', -2.2, 24), 98, 338)
    add(cloth('tshirt', 'orange', -2.9, 25, print_='pixel'), 588, 322)
    add(cloth('shorts', 'blue', 0.8, 26), 572, 344 - 12)
    # in front of the cube shelf and the cartons
    add(_hard(MANGA), 124, 166)
    add(_hard(CASE, 'purple'), 146, 168)
    add(_hard(CASE, 'yellow'), 156, 165)
    add(cloth('sock', 'white', 1.3, 27), 184, 170)
    add(_hard(PAPER), 226, 166)
    add(_hard(PAPER), 280, 170)
    add(_hard(CRUSHED, 'green'), 300, 166)
    # a couple more flat things out in the room
    add(cloth('tshirt', 'purple', -0.6, 28, folds=2, print_='heart'), 262, 202)
    add(cloth('sock', 'black', 2.1, 29), 460, 236)
    add(_hard(CAN, 'red'), 176, 214)
    return L


def build_clutter(beneath, track=False):
    """room_clutter. `beneath` (floor+walls+furniture) is only read to lay a
    one-row contact shadow under each item. With track=True it also returns the
    Tracker that watched it being drawn (for the crumble pieces)."""
    c = Canvas()
    tr = Tracker(c) if track else Null()
    for n, (s, x, y) in enumerate(items()):
        tr.begin('clutter_%02d' % n)
        m = s.opaque()
        below = np.zeros_like(m)
        below[1:, :] = m[:-1, :] & ~m[1:, :]
        ys, xs = np.nonzero(below)
        for yy, xx in zip(ys, xs):
            X, Y = x + xx, y + yy
            if 0 <= X < W and 0 <= Y < NEAR_Y and c.a[Y, X] == T:
                v = beneath.a[Y, X]
                if v != T:
                    c.a[Y, X] = IDX[DARKER[KEYS[v]]]
        c.blit(s, x, y)
        tr.end()
    tr.begin('cable', thin=True)
    cable(c)
    tr.end()
    return (c, tr) if track else c


def cable(c):
    """A charging cable snaking out from behind the PC."""
    pts = [(498, FLOOR_Y + 17), (504, FLOOR_Y + 24), (500, FLOOR_Y + 32), (512, FLOOR_Y + 40),
           (524, FLOOR_Y + 36), (532, FLOOR_Y + 44)]
    for (a, b) in zip(pts, pts[1:]):
        for (x, y) in line_pts(a[0], a[1], b[0], b[1]):
            c.set(x, y, 'K')
            if c.get(x, y - 1) is None:
                c.set(x, y - 1, 'E')
    c.rect(531, FLOOR_Y + 43, 534, FLOOR_Y + 45, 'P')
    c.box(530, FLOOR_Y + 42, 535, FLOOR_Y + 46, 'K')


# ================================================================ rug (room_floor)
RUG_CX, RUG_CY = 318, 270


def rug_mask():
    cx, cy = RUG_CX, RUG_CY
    body = poly_mask([(cx - 96, cy - 26), (cx + 96, cy - 26), (cx + 110, cy - 14),
                      (cx + 116, cy + 8), (cx - 116, cy + 8), (cx - 110, cy - 14)])
    grip_l = ellipse_mask(cx - 92, cy + 14, 42, 30)
    grip_r = ellipse_mask(cx + 92, cy + 14, 42, 30)
    return body | grip_l | grip_r


def draw_rug(floor):
    """A big game-controller rug under the open floor, low contrast so the bosses
    read on top of it. Drawn into room_floor."""
    cx, cy = RUG_CX, RUG_CY
    m = rug_mask()
    inner = m & ~border(~m) & ~border(~(m & ~border(~m)))
    edge = m & ~inner
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        k = 'N'
        if edge[y, x]:
            k = 'I'
        elif (x + y * 2) % 11 == 0:
            k = 'M'                                  # woven texture
        floor.a[y, x] = IDX[k]
    for x in range(cx - 130, cx + 131, 3):
        col = np.nonzero(m[:, x])[0] if 0 <= x < W else []
        if len(col):
            y = col.max() + 1
            if y < NEAR_Y - 1:
                floor.a[y, x] = IDX['I']
    floor.a[border(m)] = IDX['K']
    dpad = rect_mask(cx - 100, cy - 4, cx - 76, cy + 3) | rect_mask(cx - 92, cy - 12, cx - 85,
                                                                     cy + 11)
    floor.fill(dpad, 'I')
    floor.a[border(dpad) & m] = IDX['K']
    for (bx, by, col) in ((cx + 88, cy - 12, 'B'), (cx + 100, cy - 3, '3'),
                          (cx + 76, cy - 3, 'I'), (cx + 88, cy + 6, 'A')):
        b = ellipse_mask(bx, by, 6, 4.2)
        floor.fill(b, col)
        floor.a[border(b) & m] = IDX['K']
    for sx in (cx - 44, cx + 44):
        s = ellipse_mask(sx, cy + 14, 11, 7.5)
        floor.fill(s, '6')
        floor.a[border(s) & m] = IDX['K']
        floor.fill(ellipse_mask(sx - 2, cy + 12, 5, 3), 'E')
    for bx in (cx - 12, cx + 12):
        b = rect_mask(bx - 5, cy - 12, bx + 4, cy - 9)
        floor.fill(b, 'I')
        floor.a[border(b) & m] = IDX['K']
