"""Jordan's room - collectible figures for the shelves.

* APPROVED: the four funko designs of the fight (Assets/Characters/Jordan/Funkos,
  source art_source/jordan_funkos/figures.py), standing, with their colours moved
  onto the room's DB32 palette. Head masters and torso blocks are copied from
  that file unchanged; the stand pose is its STAND pose.
* funko(): a generic vinyl figure in the same language - wide head, black button
  eyes, no mouth, tiny body, pure-black keyline - built from a hair style and
  colour ramps, so a shelf can hold many different ones.
* collector_box(): the red "chase edition" window box Jordan carries in his
  idle, redrawn at shelf size.
* Figurines, plushies and spines for the shelves.

Every builder returns a Canvas cropped to the figure, feet on its last row.
"""
import random

import numpy as np

from jr_lib import Canvas, from_rows, IDX, KEYS, T, border, ix

# ================================================================ approved four
STAND = [
    "............",
    "....####....",
    ".KaK####KaK.",
    ".KhK####KhK.",
    "..KsSKKffFK.",
    "..KKKK.KKKK.",
    "............",
]

APPROVED = {
    'plumber': dict(
        head=["...KKKKKKK.....",
              "..K5443Y33K....",
              ".K544YYYYY2K...",
              ".K4433Y3Y22KK..",
              ".K12222222344K.",
              ".KnSSKttKtTKK..",
              ".KNTtnnsSnnK...",
              "..KTmmmmmmK...."],
        torso_l=5, torso=["3bb3", "bYBY", "dBBd"],
        roles={'a': '3', 'A': '4', 'h': 't', 'H': 'T', 'n': 'd', 'N': 'D',
               's': 'h', 'S': 'H', 'z': 'h', 'f': 'h', 'F': 'H', 'Z': 'h'},
        db32={'K': 'K', '5': 'r', '4': 'r', '3': 'R', '2': 'R', '1': 'B',
              's': 's', 'S': 's', 't': 'd', 'T': 'w', 'm': 'M', 'n': 'B', 'N': 'w',
              'b': 'u', 'B': 'U', 'd': 'I', 'D': 'N', 'Y': 'Y', 'y': 'd', 'W': 'W',
              'h': 'w', 'H': 'B'}),
    'hedgehog': dict(
        head=[".KK..KKKK.K....",
              ".KCKKCccCKcK...",
              "..KCCCcclCllK..",
              "KKKCCClllllLK..",
              ".KCClllWKlWKK..",
              "..KKLllWKlWKSK.",
              ".KCLllLLSsSSSnK",
              ".KKKLLLKTTSSTKK"],
        torso_l=7, torso=["llll", "lSSl", "LllL"],
        roles={'a': 'l', 'A': 'C', 'h': 'S', 'H': 't', 'n': 'l', 'N': 'L',
               's': 'Y', 'S': 'W', 'z': 'W', 'f': 'Y', 'F': 'W', 'Z': 'W'},
        db32={'K': 'K', 'c': 'c', 'C': 'u', 'l': 'U', 'L': 'I', 'v': 'N',
              's': 's', 'S': 's', 't': 'd', 'T': 'w', 'Y': 'Y', 'y': 'd', 'o': 'O',
              'W': 'W', 'w': 'P', 'n': 'N'}),
    'mascot': dict(
        head=["...KKKKKK.....",
              ".KKWWwwwpKK...",
              "KwWWwLffffLK..",
              "KwWwfWfffWfK..",
              "KwwpffffffxK..",
              "KppgfxxgxxKKK.",
              ".KpgggGGGKaeK.",
              "..KKKKKKKKeEK."],
        torso_l=5, torso=["ffff", "Lffx", "fffx"],
        roles={'a': 'f', 'A': 'L', 'h': 'W', 'H': 'p', 'n': 'x', 'N': 'X',
               's': 'N', 'S': 'n', 'z': 'W', 'f': 'N', 'F': 'n', 'Z': 'W'},
        db32={'K': 'K', 'W': 'W', 'w': 'W', 'p': 'P', 'g': 'g', 'G': 'F',
              'F': 'u', 'L': 'u', 'f': 'U', 'x': 'I', 'X': 'N', 'a': '1', 'e': '2',
              'E': '3', 'n': 'N', 'N': 'I'}),
    'gamer': dict(
        head=["....KKKKKK....",
              "..KK21k2223K..",
              ".K211k222233K.",
              ".K21khhhhhK3K.",
              "KkkkKhSKSKhK4K",
              "KccmKSSSSSSK4K",
              "KkkmKtSSSTK44K",
              ".KKK4mmmKK44K."],
        torso_l=5, torso=["3223", "2W2W", "3223"],
        roles={'a': '3', 'A': '2', 'h': 's', 'H': 'S', 'n': 'j', 'N': 'J',
               's': 'W', 'S': 'w', 'z': 'W', 'f': 'W', 'F': 'w', 'Z': 'W'},
        db32={'K': 'K', '1': '8', '2': 'V', '3': 'V', '4': 'M', '5': 'M',
              's': 's', 'S': 's', 't': 'd', 'T': 'w', 'h': 'M', 'H': 'B', 'k': 'N',
              'm': 'E', 'c': 'c', 'C': 'P', 'j': 'E', 'J': '6', 'W': 'W', 'w': 'P'}),
}


def approved(name, flip=False):
    """One of the fight's four figures, standing, in DB32. About 14x12."""
    d = APPROVED[name]
    pal = d['db32']
    g = Canvas(24, 24)
    FX0, FY0 = 10, 17
    # body first (STAND grid spans x -4..7, y -2..4 around the torso origin)
    for yi, r in enumerate(STAND):
        y = yi - 2
        for xi, ch in enumerate(r):
            x = xi - 4
            if ch in '. ':
                continue
            if ch == 'K':
                k = 'K'
            elif ch == '#':
                tr = y + 1
                if 0 <= tr < 3 and 0 <= x < 4:
                    c = d['torso'][tr][x]
                    k = 'K' if c == 'K' else pal[c]
                else:
                    k = 'K'
            else:
                pc = d['roles'].get(ch, ch)
                k = 'K' if pc == 'K' else pal[pc]
            g.set(FX0 + x, FY0 + y, k)
    hx0, hy0 = FX0 - d['torso_l'], FY0 - 8
    for yi, r in enumerate(d['head']):
        for xi, ch in enumerate(r):
            if ch in '. ':
                continue
            g.set(hx0 + xi, hy0 + yi, pal[ch])
    return _crop(g, flip)


def _crop(c, flip=False):
    bb = c.bbox()
    x0, y0, x1, y1 = bb
    out = Canvas(x1 - x0 + 1, y1 - y0 + 1)
    out.a = c.a[y0:y1 + 1, x0:x1 + 1].copy()
    if flip:
        out.a = out.a[:, ::-1].copy()
    return out


# ================================================================ generic funko
# colour ramps (light, base, shadow)
RAMPS = {
    'red': ('r', 'R', 'B'), 'blue': ('u', 'U', 'I'), 'cyan': ('c', '7', 'I'),
    'green': ('1', '2', '3'), 'yellow': ('Y', 'd', 'A'), 'orange': ('d', 'O', 'w'),
    'purple': ('8', 'V', 'M'), 'pink': ('P', '8', 'V'), 'white': ('W', 'P', 'g'),
    'grey': ('g', 'F', 'D'), 'black': ('E', '6', 'N'), 'brown': ('d', 'w', 'B'),
    'navy': ('U', 'I', 'N'), 'teal': ('1', '3', '4'), 'olive': ('9', '5', '6'),
    'gold': ('Y', 'A', '5'), 'silver': ('W', 'g', 'F'), 'maroon': ('R', 'B', 'M'),
}
SKINS = {'light': ('s', 's', 'd'), 'tan': ('s', 'd', 'w'), 'dark': ('d', 'w', 'B'),
         'green': ('1', '2', '3'), 'blue': ('c', 'u', 'U'), 'grey': ('P', 'g', 'F')}

# hair / headwear templates on a 15x12 head grid (x 0..14, y 0..11). The head
# itself is x 3..11, y 4..10 with its corners cut. H hair, A accessory, V visor,
# B beard (hair colour on the face), X a cut from the head shape.
STYLES = {
    'short': ["...............", "...............", "...............",
              "....HHHHHHH....", "...HHHHHHHHH...", "...HHHHHHHHH...",
              "...HH..HHHHH...", "...H.......H..."],
    'side': ["...............", "...............", "...............",
             "....HHHHHHHH...", "...HHHHHHHHHH..", "...HHHHHHHHHH..",
             "...HHHHH...HH..", "...HH......H..."],
    'spiky': ["....H....H.....", "....HH..HH..H..", "...HHHHHHHHHH..",
              "..HHHHHHHHHHH..", "..HHHHHHHHHHHH.", "...HHHHHHHHH...",
              "...HH.HH.HHH...", "...H.......H..."],
    'long': ["...............", "...............", "...............",
             "....HHHHHHH....", "...HHHHHHHHH...", "..HHHHHHHHHHH..",
             "..HHH.....HHH..", "..HH.......HH..", "..HH.......HH..",
             "..HH.......HH..", "..HH.......HH..", "..HH.......HH.."],
    'bun': ["......HHH......", ".....HHHHH.....", "......HHH......",
            "....HHHHHHH....", "...HHHHHHHHH...", "...HHHHHHHHH...",
            "...H.......H..."],
    'twintail': ["...............", "...............", "...............",
                 "....HHHHHHH....", "...HHHHHHHHH...", ".HHHHHHHHHHHHH.",
                 "HHHH.......HHHH", "HH.H.......H.HH", "HH...........HH",
                 ".H...........H.", ".H...........H."],
    'ears': ["...H.......H...", "...HH.....HH...", "...HHH...HHH...",
             "...HHHHHHHHH...", "...HHHHHHHHH...", "...HHHHHHHHH...",
             "...HH.....HH...", "...H.......H..."],
    'cap': ["...............", "...............", "...............",
            "....AAAAAAA....", "...AAAAAAAAA...", "...AAAAAAAAAAA.",
            "...HH.....HH...", "...H.......H..."],
    'hood': ["...............", "...............", "...............",
             "....AAAAAAA....", "...AAAAAAAAA...", "..AAAAAAAAAAA..",
             "..AAA.....AAA..", "..AA.......AA..", "..AA.......AA..",
             "..AA.......AA..", "..AAA.....AAA..", "...AAAAAAAAA..."],
    'helmet': ["...............", "...............", "...............",
               "....AAAAAAA....", "...AAAAAAAAA...", "...AAAAAAAAA...",
               "...AVVVVVVVA...", "...AVVVVVVVA...", "...AVVVVVVVA...",
               "...AAAAAAAAA...", "....AAAAAAA...."],
    'wizard': [".......A.......", "......AAA......", ".....AAAAA.....",
               "...AAAAAAAAA...", "..AAAAAAAAAAA..", "...HHHHHHHHH...",
               "...HH.....HH...", "...H.......H..."],
    'band': ["...............", "...............", "...............",
             "....HHHHHHH....", "...HHHHHHHHH...", "...AAAAAAAAAAA.",
             "...HH......AA..", "...H.......H..."],
    'bald': ["...............", "...............", "...............",
             "...............", "...............", "...............",
             "...............", "...............", "...............",
             "...BB.....BB...", "....BBBBBBB...."],
    'crown': ["...A..A..A.....", "...AA.AA.AA....", "...AAAAAAAA....",
              "....HHHHHHH....", "...HHHHHHHHH...", "...HHHHHHHHH...",
              "...H.......H..."],
}


def _shade(mask, base, hi, lo):
    """Per-pixel light/base/shadow for a region: lit on the top-left edge, dark on
    the right and bottom edges."""
    h, w = mask.shape
    out = {}
    ys, xs = np.nonzero(mask)
    cx = xs.mean() if len(xs) else 0
    for y, x in zip(ys, xs):
        up = y == 0 or not mask[y - 1, x]
        left = x == 0 or not mask[y, x - 1]
        right = x == w - 1 or not mask[y, x + 1]
        down = y == h - 1 or not mask[y + 1, x]
        if right or (down and x > cx):
            out[(x, y)] = lo
        elif (up and x <= cx + 1) or (left and y < h * 0.6):
            out[(x, y)] = hi
        else:
            out[(x, y)] = base
    return out


def funko(style='short', skin='light', hair='brown', shirt='red', pants='blue', acc=None,
          visor='cyan', blush=False, shades=False, flip=False):
    """Generic figure, 15 wide grid, ~13-16 tall. Returns a cropped Canvas."""
    Wd, Hd = 15, 16
    sk = SKINS[skin]
    hr = RAMPS[hair]
    ac = RAMPS[acc] if acc else hr
    sh = RAMPS[shirt]
    pa = RAMPS[pants]
    vi = RAMPS[visor]
    head = np.zeros((Hd, Wd), bool)
    head[4:11, 3:12] = True
    for (x, y) in ((3, 4), (11, 4), (3, 10), (11, 10)):
        head[y, x] = False
    tpl = STYLES[style]
    hairm = np.zeros((Hd, Wd), bool)
    accm = np.zeros((Hd, Wd), bool)
    vism = np.zeros((Hd, Wd), bool)
    beard = np.zeros((Hd, Wd), bool)
    for y, row in enumerate(tpl):
        for x, ch in enumerate(row):
            if ch == 'H':
                hairm[y, x] = True
            elif ch == 'A':
                accm[y, x] = True
            elif ch == 'V':
                vism[y, x] = True
            elif ch == 'B':
                beard[y, x] = True
    # body: sleeves+hands x4/x10, torso x5..9 (rows 12-13), legs rows 14
    body = np.zeros((Hd, Wd), bool)
    body[12:14, 4:11] = True
    legs = np.zeros((Hd, Wd), bool)
    legs[14, 5:7] = True
    legs[14, 8:10] = True
    sil = head | hairm | accm | vism | body | legs
    c = Canvas(Wd, Hd)
    # face
    face = head & ~hairm & ~accm & ~vism
    for (x, y), k in _shade(head, sk[1], sk[0], sk[2]).items():
        if face[y, x]:
            c.set(x, y, k)
    for (x, y), k in _shade(hairm, hr[1], hr[0], hr[2]).items():
        c.set(x, y, k)
    for (x, y), k in _shade(accm, ac[1], ac[0], ac[2]).items():
        c.set(x, y, k)
    for (x, y), k in _shade(vism, vi[1], vi[0], vi[2]).items():
        c.set(x, y, k)
    for y, x in zip(*np.nonzero(beard)):
        c.set(x, y, hr[1] if x < 7 else hr[2])
    # eyes (under a visor they become two lit dots)
    if style == 'helmet':
        c.set(5, 7, vi[0])
        c.set(9, 7, vi[0])
    elif shades:
        for x in range(4, 11):
            c.set(x, 7, 'K')
        c.set(5, 8, 'K')
        c.set(9, 8, 'K')
        c.set(4, 7, 'K')
        c.set(5, 7, vi[0])
        c.set(9, 7, vi[0])
    else:
        for (x, y) in ((5, 7), (5, 8), (9, 7), (9, 8)):
            c.set(x, y, 'K')
    if blush and style != 'helmet':
        c.set(4, 9, 'r')
        c.set(10, 9, 'r')
    # body
    for x in range(4, 11):
        for y in (12, 13):
            if x in (4, 10) and y == 13:
                c.set(x, y, sk[1] if x == 4 else sk[2])          # hands
            elif x in (5, 4):
                c.set(x, y, sh[0])
            elif x in (9, 10):
                c.set(x, y, sh[2])
            else:
                c.set(x, y, sh[1])
    for x in (5, 6):
        c.set(x, 14, pa[1] if x == 5 else pa[1])
    for x in (8, 9):
        c.set(x, 14, pa[2])
    # keyline round the lot, plus the chin line between head and body
    b = border(sil)
    c.a[b] = IDX['K']
    for x in range(4, 11):
        if not (hairm[11, x] or accm[11, x]):
            c.set(x, 11, 'K')
    return _crop(c, flip)


# a curated cast for the shelves: varied silhouettes and colours, no franchises
CAST = [
    dict(style='spiky', skin='light', hair='yellow', shirt='orange', pants='blue'),
    dict(style='hood', skin='light', hair='brown', acc='grey', shirt='grey', pants='black'),
    dict(style='long', skin='light', hair='pink', shirt='white', pants='purple', blush=True),
    dict(style='helmet', skin='light', acc='white', visor='cyan', shirt='white', pants='grey'),
    dict(style='cap', skin='tan', hair='black', acc='red', shirt='blue', pants='navy'),
    dict(style='wizard', skin='light', hair='white', acc='purple', shirt='purple', pants='purple'),
    dict(style='ears', skin='light', hair='white', shirt='pink', pants='white', blush=True),
    dict(style='twintail', skin='light', hair='cyan', shirt='black', pants='black', blush=True),
    dict(style='bald', skin='tan', hair='brown', shirt='green', pants='olive'),
    dict(style='band', skin='light', hair='black', acc='red', shirt='navy', pants='navy'),
    dict(style='spiky', skin='light', hair='black', shirt='orange', pants='navy'),
    dict(style='bun', skin='tan', hair='black', shirt='red', pants='black'),
    dict(style='crown', skin='light', hair='yellow', acc='gold', shirt='pink', pants='pink',
         blush=True),
    dict(style='helmet', skin='light', acc='green', visor='yellow', shirt='green', pants='olive'),
    dict(style='side', skin='dark', hair='black', shirt='yellow', pants='blue'),
    dict(style='short', skin='light', hair='red', shirt='teal', pants='navy'),
    dict(style='long', skin='tan', hair='black', shirt='red', pants='black'),
    dict(style='hood', skin='light', hair='black', acc='green', shirt='green', pants='black'),
    dict(style='ears', skin='light', hair='orange', shirt='black', pants='black'),
    dict(style='spiky', skin='light', hair='blue', shirt='black', pants='grey'),
    dict(style='cap', skin='light', hair='brown', acc='navy', shirt='white', pants='blue'),
    dict(style='short', skin='tan', hair='brown', shirt='maroon', pants='blue', shades=True),
    dict(style='helmet', skin='light', acc='red', visor='black', shirt='red', pants='black'),
    dict(style='twintail', skin='light', hair='yellow', shirt='blue', pants='white', blush=True),
    dict(style='wizard', skin='dark', hair='white', acc='navy', shirt='navy', pants='navy'),
    dict(style='bald', skin='light', hair='orange', shirt='black', pants='black'),
    dict(style='side', skin='light', hair='white', shirt='purple', pants='black'),
    dict(style='band', skin='tan', hair='brown', acc='blue', shirt='white', pants='blue'),
]


def cast_figure(i, flip=None):
    spec = dict(CAST[i % len(CAST)])
    if flip is None:
        flip = bool(i & 1)
    return funko(flip=flip, **spec)


# ================================================================ boxes
BOX_CHASE = [
    "KKKKKKKKKKK",
    "KrrrrYrrrRK",
    "KrrrYYYrrRK",
    "KRRrrYrrRRK",
    "KKKKKKKKKKK",
    "KAKuuuuuKAK",
    "KYKu.....K.",
    "KYKu.....K.",
    "KYKu.....K.",
    "KYKu.....K.",
    "KAKu.....K.",
    "KAKu.....K.",
    "KAKKKKKKKAK",
    "KAYYYYYYYAK",
    "KKKKKKKKKKK",
]


def collector_box(inner=None, top=('r', 'R', 'B'), side=('Y', 'A', '5'), window='u'):
    """Window box with a figure inside (11x15). Default = the red chase edition box."""
    c = Canvas(11, 15)
    leg = {'r': top[0], 'R': top[1], 'Y': side[0], 'A': side[1], 'u': window}
    c.stamp(BOX_CHASE, 0, 0, leg)
    # window: dark back, the figure's head and shoulders peeking out
    for y in range(6, 12):
        for x in range(4, 9):
            c.set(x, y, 'N' if y > 6 else 'I')
    if inner is not None:
        # squeeze the figure into the window: its top 6 rows, centred
        fw = inner.w
        ox = 4 + (5 - min(fw, 5)) // 2 - max(0, (fw - 5) // 2)
        for y in range(min(6, inner.h)):
            for x in range(inner.w):
                v = inner.a[y + 1 if y + 1 < inner.h else y, x]
                X, Y = ox + x, 6 + y
                if 4 <= X <= 8 and 6 <= Y <= 11 and v != T:
                    c.a[Y, X] = v
    # glass glare: one bright diagonal
    c.set(8, 7, 'P')
    c.set(8, 6, 'W')
    c.set(9, 5, side[0])
    c.vline(9, 6, 11, 'P' if window != 'N' else 'g')
    c.vline(10, 5, 12, 'K')
    return c


def mini_head(spec):
    """A 5x6 head+shoulders for inside a window box."""
    f = funko(**spec)
    return f


# ================================================================ figurines
STATUE_HERO = [
    "......K.....",
    ".....KWK....",
    ".....KgK....",
    "..KK.KgK....",
    ".KYYKKgK....",
    "KYYYYKKK....",
    "KYdsdK.KKK..",
    "KdsKsKKRRRK.",
    ".KsssKRrRRK.",
    "..KKKRrRRK..",
    ".KRRKrRRBK..",
    ".KsKKRRBKK..",
    "..KKKRBBK...",
    "...KIIKIK...",
    "...KIKKIK...",
    "..KNNKKNNK..",
    ".KFFFFFFFFK.",
    ".KDDDDDDDDK.",
    "..KKKKKKKK..",
]

MECH = [
    "....KKK.....",
    "...KgWgK....",
    "..KKcKcKK...",
    ".KRKgggKRK..",
    "KgRKKKKKRgK.",
    "KgWgUUUgWgK.",
    "KgggUuUgggK.",
    ".KKgUUUgKK..",
    ".KgKgggKgK..",
    ".KgKKKKKgK..",
    ".KFK.K.KFK..",
    "..KgK.KgK...",
    "..KgK.KgK...",
    ".KgFK.KFgK..",
    ".KKKK.KKKK..",
]

DRAGON = [
    "....KK......KK..",
    "...K1K.....K33K.",
    "..KK12K...K3443K",
    ".K112YK..K34443K",
    "K11222KK.K34443K",
    "KKKK122K.K3443K.",
    "....K12K.K343K..",
    "....K12KK2K3K...",
    "...K12dd222K....",
    "..K12ddd2223K...",
    "..K1Kddd2K23K...",
    "..KK2dd22K33KKK.",
    "...K22222K3K..3K",
    "...KK2K2KK.K33K.",
    "..KFFFFFFFFFKK..",
    "..KDDDDDDDDDK...",
    "..KKKKKKKKKKK...",
]

CREATURE = [      # a little ghost (generic)
    "...KKKK...",
    "..KWWWPK..",
    ".KWWWWWPK.",
    ".KWKWWKPK.",
    ".KWKWWKgK.",
    ".KWWWWWgK.",
    ".KWWWWPgK.",
    ".KWPWgWgK.",
    ".KgKgKgKK.",
    "..K.K.K...",
]

SLIME = [          # a round jelly blob (generic)
    "...KKKK...",
    "..K1122K..",
    ".K1W1222K.",
    ".K122223K.",
    "K2K22K223K",
    "K22222233K",
    "K32222333K",
    ".KKKKKKKK.",
]

KNIGHT = [
    "...KKKK...",
    "..KgWggK..",
    "..KNNNFK..",
    "..KggFFK..",
    ".KKKKKKKK.",
    "KgWgggFFDK",
    "KgKggFFKDK",
    "KgKgRRFKDK",
    ".KKgRFFKK.",
    "..KgFFDK..",
    "..KFKKDK..",
    "..KgK.KDK.",
    ".KKKK.KKK.",
]


def figurine(name, flip=False):
    rows = {'hero': STATUE_HERO, 'mech': MECH, 'dragon': DRAGON, 'critter': CREATURE,
            'slime': SLIME, 'knight': KNIGHT}[name]
    return from_rows(rows, flip=flip)


# ================================================================ plushies
PLUSH_HEDGEHOG = [
    "..KK.KKKK.......",
    ".KuKKuuuuKK.....",
    "..KuuuuUUUUK....",
    "KKKuuuUUUUUUK...",
    ".KuuUUWKUWKUK...",
    "..KKUUWKUWKsK...",
    ".KuUUUUsssssK...",
    ".KKKUUUKsssKK...",
    "...KUUUUUUK.....",
    "..KsKUUUUKsK....",
    "..KKRRKKRRKK....",
    "...KKKKKKKK.....",
]

PLUSH_MASCOT = [
    "...KKKKKK...",
    ".KKWWWWWPKK.",
    "KWWWWWWWWPPK",
    "KWUUUUUUUUPK",
    "KWUWKUUWKUPK",
    "KWUUUUUUUUgK",
    "KPUUKKKKUUgK",
    ".KPgUUUUggK.",
    "..KKKKKKKK..",
]


def plush(name):
    return from_rows({'hedgehog': PLUSH_HEDGEHOG, 'mascot': PLUSH_MASCOT}[name])


# ================================================================ spines
def spines(width, height, seed=3, palette=None):
    """A row of book/manga/game-case spines packed on a shelf, bottom-aligned."""
    rnd = random.Random(seed)
    pal = palette or ['R', 'U', 'W', '2', 'Y', 'V', 'O', 'c', 'P', '8', 'I', 'E']
    c = Canvas(width, height)
    x = 0
    while x < width - 1:
        w = rnd.choice((2, 2, 3, 3, 4))
        h = height - rnd.choice((0, 0, 1, 2, 3))
        col = rnd.choice(pal)
        if x + w > width:
            w = width - x
        y0 = height - h
        c.rect(x, y0, x + w - 1, height - 1, col)
        c.vline(x, y0, height - 1, 'K')
        c.hline(x, x + w - 1, y0, 'K')
        # a label band
        if h > 5:
            lb = y0 + 2 + rnd.randrange(0, max(1, h - 5))
            c.hline(x + 1, x + w - 1, lb, 'W' if col not in ('W', 'P', 'Y') else 'N')
        x += w
    c.vline(width - 1, 0, height - 1, 'K')
    # keep the right edge closed only where books reach
    return c
