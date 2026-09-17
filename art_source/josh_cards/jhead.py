"""Josh's head - LEAN 'card sharp' build.

This replaces the earlier wrapper around head.py.  head.py holds the stocky, Ash-cap head the
first pass shipped; the user asked for a smaller, narrower, Twisted-Fate head with the blue shades
worn ON his eyes and a gambler's hat instead of a ball cap, so the geometry is authored here.

Carried over from the approved design: the pencil moustache, the soul patch, the blue shades, the
black spade, the playing card tucked in the hat band, the dark hair showing under the hat.

Vertical layout in the 80x80 frame (the whole head is 32 rows, the old one was 34, and 19 px wide
where the old one was 23)
    y16..22   hat crown, deep wine, fedora pinch
    y19..21   gold hat band, gold-rimmed black spade over it
    y22..26   wide flat gambler brim, x19..61
    y26..47   head skin, x31..49, centre x40
    y27..28   brow - with the lenses on, this and the mouth carry every expression
    y30..34   blue shades, ON his eyes
    y35..37   nose
    y38       pencil moustache
    y40..43   mouth
    y44..45   soul patch
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
import rig
from rig import hdome, hbump, hf_shade, SKIN
import cards as CD
from rot import rotate

CX, CY = 40, 34                     # head centre, used as the rotation pivot
CHIN = 46


def off(blocks, dx, dy=0):
    return [(x + dx, y + dy, rows) for (x, y, rows) in blocks]


# ---------------------------------------------------------------- skull
HEAD_ROWS = {}
for _y in range(25, 43):
    HEAD_ROWS[_y] = (31, 49)
HEAD_ROWS[43] = (32, 48)
HEAD_ROWS[44] = (33, 47)
HEAD_ROWS[45] = (35, 45)
HEAD_ROWS[46] = (37, 43)


def head_mask():
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def face_h(px, py):
    h = hdome(px, py, 40.0, 35.0, 10.0, 11.5, 6.0)
    h += hbump(px, py, 35.0, 36.0, 4.5, 4.5, 4.5, 5.0, 1.2)     # near cheek
    h += hbump(px, py, 45.5, 36.0, 4.0, 4.0, 4.0, 4.5, 0.9)     # far cheek
    h += hbump(px, py, 40.0, 43.5, 5.0, 5.0, 3.5, 3.0, 1.1)     # chin
    h += hbump(px, py, 40.5, 35.0, 2.2, 2.2, 3.5, 2.5, 1.5)     # nose bridge
    h += hbump(px, py, 40.0, 28.0, 8.5, 8.5, 3.0, 3.0, 0.6)     # brow ridge
    return h


EAR = (28, 31, [".##.", "#sd#", "#df#", "#dd#", ".##."])
FOREHEAD = []

# ---------------------------------------------------------------- expressions
MOUSTACHE = [(35, 37, [".hkkh.hkkh"])]
SOULPATCH = [(38, 43, ["hkkh"]), (39, 44, ["kk"])]

MOUTHS = {
    # DEFAULT everywhere he is in control: closed lips hitched up on one side, a glint of tooth
    'smirk': [
        (44, 39, ["##"]),
        (41, 40, ["####"]),
        (36, 41, ["#####www#"]),
        (35, 42, ["##########"]),
    ],
    'open': [                                  # shouting / shocked
        (36, 39, ["#########"]),
        (35, 40, ["#wwWwwWww#"]),
        (35, 41, ["#mmmMmmmm#"]),
        (36, 42, ["#########"]),
    ],
    'pant': [                                  # winded, tongue showing
        (37, 39, ["######"]),
        (36, 40, ["#wwWww#"]),
        (35, 41, ["#mMMmmmm#"]),
        (36, 42, ["#######"]),
    ],
    'grit': [                                  # clenched
        (35, 39, ["##########"]),
        (34, 40, ["#w#wWw#ww#"]),
        (35, 41, ["#W#ww#ww#"]),
        (36, 42, ["########"]),
    ],
    'slack': [                                 # beaten
        (37, 40, ["######"]),
        (36, 41, ["#mmmmmm#"]),
        (37, 42, ["######"]),
    ],
    'flat': [                                  # the deadpan between tricks
        (36, 41, ["#########"]),
        (37, 42, ["ddddddd"]),
    ],
}

# The lenses hide his eyes, so the brow above them is the only part of the face that can move.
# Two rows each so they still read at 3x, inside y25..28 where the brim never covers them.
BROWS = {
    'flat': [(32, 26, ["hkkkkkk", "kkkkkkk"]), (42, 26, ["kkkkkkh", "kkkkkkk"])],
    'cocky': [(33, 27, ["hkkkkk", "kkkkkk"]), (42, 26, ["kkkkkkh", "kkkkkkk"])],
    'angry': [(32, 26, ["hkkk"]), (34, 27, ["kkkkk"]), (41, 27, ["kkkkk"]), (45, 26, ["kkkh"])],
    'pain': [(32, 27, ["hkkk"]), (35, 26, ["kkkk"]), (41, 26, ["kkkk"]), (45, 27, ["kkkh"])],
    'up': [(32, 25, ["hkkkkkk", "kkkkkkk"]), (42, 25, ["kkkkkkh", "kkkkkkk"])],
}

# ---------------------------------------------------------------- shades, ON his eyes
# Dark blue glass, a hard highlight streak along the top left of each lens, a clean black frame
# and a solid three-pixel bridge.  x30..50, so the frame laps the temples.
SHADES = [
    (30, 29, ["#####################"]),
    (30, 30, ["#CCBBbbbb#X#CCBBbbbb#"]),
    (30, 31, ["#CBBbbbbb#X#CBBbbbbb#"]),
    (30, 32, ["#BBbbbbbb#X#BBbbbbbb#"]),
    (30, 33, ["#####################"]),
]
TEMPLES = [(28, 31, ["XX"]), (51, 31, ["XX"])]

NOSE = [(39, 34, ["sd"]), (38, 35, ["asdf"]), (39, 36, ["ff"])]
BLUSH = [(32, 35, ["rr"]), (47, 35, ["r"])]
STUBBLE = [(33, 39, ["t"]), (34, 41, ["T"]), (36, 43, ["T"]), (44, 43, ["T"]),
           (46, 41, ["T"]), (47, 39, ["T"])]

# dark hair at the jaw under the brim, both sides, mirrored about x=40
HAIR = [
    (29, 34, ["hh"]), (28, 35, ["jHh"]), (28, 36, ["#kHh"]),
    (28, 37, ["#khh"]), (29, 38, ["#kh"]), (30, 39, ["#k"]),
    (50, 34, ["hh"]), (50, 35, ["hHj"]), (49, 36, ["hHk#"]),
    (49, 37, ["hhk#"]), (49, 38, ["hk#"]), (49, 39, ["k#"]),
]

SWEATS = {
    0: [],
    1: [(27, 30, ["C"]), (28, 31, ["y"]), (54, 32, ["C"]), (55, 33, ["y"])],
    2: [(26, 34, ["C"]), (27, 35, ["y"]), (55, 36, ["C"]), (56, 37, ["y"]), (25, 28, ["C"])],
    3: [(28, 27, ["C"]), (29, 28, ["y"]), (53, 29, ["C"]), (54, 30, ["y"]),
        (26, 38, ["C"]), (57, 40, ["C"])],
}


# ---------------------------------------------------------------- gambler's hat
CROWN = [(34, 17), (36, 15), (44, 15), (46, 17), (48, 19), (49, 22), (31, 22), (32, 19)]


def crown_h(px, py):
    h = hdome(px, py, 40.0, 24.0, 10.0, 11.0, 7.0)
    h += hbump(px, py, 35.5, 18.5, 5.0, 5.0, 3.0, 5.0, 1.3)
    h -= hbump(px, py, 40.0, 16.0, 3.0, 3.0, 2.0, 3.5, 2.2)     # fedora pinch
    return h


BAND_ROWS = {21: (31, 49), 22: (31, 49)}
BAND_TONE = {21: 'F', 22: 'D'}

# his mark, kept from the approved design: a black spade over the gold hat band
SPADE = [
    (40, 14, ["D"]),
    (39, 15, ["D#D"]),
    (38, 16, ["D###D"]),
    (37, 17, ["D#####D"]),
    (37, 18, ["D#####D"]),
    (37, 19, ["DD###DD"]),
    (39, 20, ["D#D"]),
    (38, 21, ["DD#DD"]),
]

BRIM_ROWS = {22: (28, 52), 23: (23, 57), 24: (23, 57), 25: (27, 53)}
BRIM_TONE = {22: 'V', 23: 'X', 24: 'x', 25: 'x'}


def build_brim(c):
    m = mask_empty()
    for y, (lo, hi) in BRIM_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    for y, (lo, hi) in BRIM_ROWS.items():
        for x in range(lo, hi + 1):
            ch = BRIM_TONE[y]
            if y == 23 and lo + 2 <= x <= lo + 16:
                ch = 'z'                        # specular skim along the lit side
            if y == 23 and x > hi - 12:
                ch = 'X'
            if y == 24 and x < lo + 5:
                ch = 'V'
            c[y][x] = ch
    ol, _ = outline_pixels(m, prune=False)
    for y in range(H):
        for x in range(W):
            if ol[y][x] and y != 22:
                c[y][x] = '#'
    return c


# ---------------------------------------------------------------- layers
def face_layer(turn=0, mouth='smirk', brows='cocky', sweat=0, ear=True, shades=True, shades_dy=0):
    c = blank()
    m = head_mask()

    def fh(px, py):
        return face_h(px - turn * 0.55, py)

    hf_shade(c, m, fh, SKIN, [0.0, 0.26, 0.52, 0.80, 0.965], zscale=0.95)
    despeckle(c, region=m)
    if ear:
        ex, ey, rows = EAR
        block(c, ex + int(round(turn * 0.45)), ey, rows)
    t = int(round(turn))
    fx = blank()                                 # features, clipped to the skull
    for (x, y, rows) in FOREHEAD:
        block(fx, x, y, rows)
    for (x, y, rows) in off(NOSE, t) + off(BLUSH, t) + off(STUBBLE, int(round(turn * 0.5))):
        block(fx, x, y, rows)
    for (x, y, rows) in off(MOUSTACHE + MOUTHS[mouth] + SOULPATCH, t):
        block(fx, x, y, rows)
    for (x, y, rows) in off(BROWS[brows], t):
        block(fx, x, y, rows)
    for y in range(H):
        for x in range(W):
            if fx[y][x] != '.' and m[y][x]:
                c[y][x] = fx[y][x]
    for (x, y, rows) in off(HAIR, int(round(turn * 0.4))):
        block(c, x, y, rows)
    if shades:                                   # over the skull, lapping the temples
        for (x, y, rows) in off(TEMPLES + SHADES, t, shades_dy):
            block(c, x, y, rows)
    for (x, y, rows) in SWEATS.get(sweat, []):
        block(c, x, y, rows)
    return c


def cap_layer(turn=0, band_card=True):
    c = blank()
    if band_card:
        CD.draw_card(c, 53, 13, 7, 13, -34, pip=CD.DIAMOND3, pip_col='Q')
    cm = poly_mask(CROWN)
    hf_shade(c, cm, crown_h, rig.RED, [0.16, 0.42, 0.70, 0.94], zscale=0.85)
    for y, (lo, hi) in BAND_ROWS.items():        # gold hat band
        for x in range(lo, hi + 1):
            if cm[y][x]:
                c[y][x] = BAND_TONE[y]
    t = int(round(turn * 0.7))
    for (x, y, rows) in off(SPADE, t):
        block(c, x, y, rows)
    build_brim(c)
    return c


def build(c, dx=0, dy=0, rot=0, turn=0, mouth='smirk', brows='cocky',
          sweat=0, cap=True, cap_dx=0, cap_dy=0, cap_rot=0, band_card=True, shades=True,
          shades_dy=0, ear=True, extra=None, **kw):
    """Composite a posed head onto canvas `c`.

    dx/dy      translate the whole head (chin normally at y47, centre x40)
    rot        tilt, degrees clockwise on screen, about (40, 35)
    turn       3/4 turn: +px slides the features toward OUR right
    shades_dy  slide the lenses down his nose (the winded / staggered frames)
    cap_*      knock the hat askew independently of the head
    `eyes=` is accepted and ignored - his eyes are behind glass now.
    """
    f = face_layer(turn=turn, mouth=mouth, brows=brows, sweat=sweat, ear=ear,
                   shades=shades, shades_dy=shades_dy)
    f = rotate(f, rot, (CX, CY), (dx, dy))
    composite(c, f)
    if cap:
        k = cap_layer(turn=turn, band_card=band_card)
        k = rotate(k, rot + cap_rot, (CX, CY), (dx + cap_dx, dy + cap_dy))
        composite(c, k)
    if extra:
        for (x, y, rows) in off(extra, dx, dy):
            block(c, x, y, rows)
    return c


if __name__ == '__main__':
    out = sys.argv[1]
    c = blank()
    build(c)
    save_png(c, out + '/jhead_test.png')
    preview(c, out + '/jhead_test_8x.png', s=8)
    print('ok')
