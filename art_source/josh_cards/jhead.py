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
# Fuller and rounder than the first lean pass: the reference photo is a full, soft face with
# heavy cheeks and a weighty jaw.  Narrower at the temples (the hairline is receding there),
# widest across the cheeks, and the jaw only starts to taper at y44.
HEAD_ROWS = {}
for _y in range(25, 29):
    HEAD_ROWS[_y] = (31, 49)
for _y in range(29, 44):
    HEAD_ROWS[_y] = (30, 50)
HEAD_ROWS[44] = (31, 49)
HEAD_ROWS[45] = (33, 47)
HEAD_ROWS[46] = (36, 44)


def head_mask():
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def face_h(px, py):
    h = hdome(px, py, 40.0, 35.0, 11.0, 11.0, 6.0)
    h += hbump(px, py, 34.5, 37.0, 5.5, 5.5, 5.5, 6.0, 1.5)     # near cheek, fleshy
    h += hbump(px, py, 46.0, 37.0, 5.0, 5.0, 5.0, 5.5, 1.1)     # far cheek
    h += hbump(px, py, 40.0, 43.5, 6.5, 6.5, 4.5, 3.5, 1.3)     # heavy jaw / chin
    h += hbump(px, py, 40.5, 35.0, 2.2, 2.2, 3.5, 2.5, 1.4)     # nose bridge
    h += hbump(px, py, 40.0, 28.0, 9.5, 9.5, 3.5, 3.0, 0.7)     # broad forehead
    return h


EAR = (27, 32, [".##.", "#sd#", "#df#", "#dd#", ".##."])
FOREHEAD = []

# ---------------------------------------------------------------- long hair, pulled back
# The biggest likeness cue: dark brown-black hair swept straight back off a broad forehead and
# gathered at the nape.  From the front you read it as a dark band down both temples, past the
# ears, meeting in a bunched mass under the jaw.  Nothing on the forehead - his hairline is
# receding there and the brim covers the rest.
HAIR = [
    # left temple, swept back past the ear, flaring into the gathered bunch beside the jaw
    (29, 27, ["j"]), (28, 28, ["jH"]), (28, 29, ["hH"]),
    (27, 30, ["#hH"]), (27, 31, ["#hH"]), (27, 32, ["#kh"]),
    (27, 33, ["#kh"]), (27, 34, ["#kh"]), (28, 35, ["#kh"]),
    (28, 36, ["#kh"]), (28, 37, ["#kh"]), (28, 38, ["#kh"]),
    (29, 39, ["#kh"]), (29, 40, ["#kh"]),
    (29, 41, ["#kHh"]), (29, 42, ["#kHhh"]), (30, 43, ["#kHhh"]),
    (31, 44, ["#kHh"]), (32, 45, ["#kh"]),
    # right temple, mirrored about x=40
    (51, 27, ["j"]), (51, 28, ["Hj"]), (51, 29, ["Hh"]),
    (51, 30, ["Hh#"]), (51, 31, ["Hh#"]), (51, 32, ["hk#"]),
    (51, 33, ["hk#"]), (51, 34, ["hk#"]), (50, 35, ["hk#"]),
    (50, 36, ["hk#"]), (50, 37, ["hk#"]), (50, 38, ["hk#"]),
    (49, 39, ["hk#"]), (49, 40, ["hk#"]),
    (48, 41, ["hHk#"]), (47, 42, ["hhHk#"]), (46, 43, ["hhHk#"]),
    (46, 44, ["hHk#"]), (46, 45, ["hk#"]),
]

# ---------------------------------------------------------------- expressions
# A full dark goatee: a heavy moustache curving down either side of the mouth into a chin beard
# with a soul patch.  Replaces the pencil moustache, which was far too light for him.  Kept to a
# ring one pixel thick at the sides so his cheeks stay open and the face still reads as a face.
GOATEE = [
    (34, 37, ["hkkkkkkkkkkkh"]),
    (34, 38, ["kk.........kk"]),
    (34, 39, ["k...........k"]),
    (34, 40, ["k...........k"]),
    (34, 41, ["k...........k"]),
    (34, 42, ["k...........k"]),
    (34, 43, ["kk.........kk"]),
    (35, 44, ["hkkkkHkkkkh"]),
    (36, 45, ["hkkkkkkkh"]),
    (38, 46, ["hkkkh"]),
]
MOUSTACHE = []
SOULPATCH = []

# The beard ring leaves an opening of x35..45 / y39..43.  The distress mouths need most of it:
# at 3x a dark spot inside a dark beard reads as nothing, so `open`, `pant`, `grit` and `slack`
# are as wide and as tall as the ring allows.
MOUTHS = {
    # DEFAULT everywhere he is in control: closed lips hitched up on one side, a glint of tooth
    'smirk': [
        (43, 39, ["##"]),
        (40, 40, ["####"]),
        (36, 41, ["#####ww#"]),
        (36, 42, ["########"]),
    ],
    'open': [                                  # shouting / shocked
        (36, 39, ["#########"]),
        (35, 40, ["#wwWwwWww#"]),
        (35, 41, ["#mmmMmmmm#"]),
        (36, 42, ["#########"]),
    ],
    'pant': [                                  # winded: hanging open, tongue showing
        (37, 39, ["#######"]),
        (36, 40, ["#wwWww#"]),
        (36, 41, ["#mMMmm#"]),
        (36, 42, ["#mmmmm#"]),
        (37, 43, ["#####"]),
    ],
    'grit': [                                  # clenched
        (36, 39, ["#########"]),
        (36, 40, ["#w#wWw#w#"]),
        (36, 41, ["#W#ww#w#"]),
        (36, 42, ["#########"]),
    ],
    'slack': [                                 # beaten
        (37, 40, ["#######"]),
        (36, 41, ["#mmmmmm#"]),
        (37, 42, ["#######"]),
    ],
    'flat': [                                  # the deadpan between tricks
        (36, 41, ["#########"]),
        (37, 42, ["ddddddd"]),
    ],
}

# Thick, dark, straight brows - with the lenses on, these and the beard carry the likeness as
# well as the whole performance, so they are heavier than the first pass.
BROWS = {
    'flat': [(31, 26, ["hkkkkkkk", "kkkkkkkk"]), (42, 26, ["kkkkkkkh", "kkkkkkkk"])],
    'cocky': [(31, 27, ["hkkkkkkk", "kkkkkkkk"]), (42, 26, ["kkkkkkkh", "kkkkkkkk"])],
    'angry': [(31, 26, ["hkkk"]), (34, 27, ["kkkkk", "kkkkk"]),
              (41, 27, ["kkkkk", "kkkkk"]), (46, 26, ["kkkh"])],
    'pain': [(31, 27, ["hkkk", "kkkk"]), (35, 26, ["kkkkk"]),
             (41, 26, ["kkkkk"]), (46, 27, ["kkkh", "kkkk"])],
    'up': [(31, 25, ["hkkkkkkk", "kkkkkkkk"]), (42, 25, ["kkkkkkkh", "kkkkkkkk"])],
}

# ---------------------------------------------------------------- shades, ON his eyes
SHADES = [
    (29, 29, ["#######################"]),
    (29, 30, ["#CCBBbbbbb#X#CCBBbbbbb#"]),
    (29, 31, ["#CBBbbbbbb#X#CBBbbbbbb#"]),
    (29, 32, ["#BBbbbbbbb#X#BBbbbbbbb#"]),
    (29, 33, ["#######################"]),
]
TEMPLES = [(27, 31, ["XX"]), (52, 31, ["XX"])]

NOSE = [(39, 34, ["sd"]), (38, 35, ["asdf"]), (39, 36, ["ff"])]
BLUSH = [(32, 36, ["rrr"]), (46, 36, ["rr"])]
STUBBLE = [(32, 39, ["t"]), (33, 43, ["T"]), (46, 43, ["T"]), (47, 39, ["t"])]

SWEATS = {
    0: [],
    1: [(26, 31, ["C"]), (27, 32, ["y"]), (55, 33, ["C"]), (56, 34, ["y"])],
    2: [(25, 35, ["C"]), (26, 36, ["y"]), (56, 37, ["C"]), (57, 38, ["y"]), (24, 29, ["C"])],
    3: [(27, 28, ["C"]), (28, 29, ["y"]), (54, 30, ["C"]), (55, 31, ["y"]),
        (25, 39, ["C"]), (58, 41, ["C"])],
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
    t = int(round(turn))

    def fh(px, py):
        return face_h(px - turn * 0.55, py)

    hf_shade(c, m, fh, SKIN, [0.0, 0.26, 0.52, 0.80, 0.965], zscale=0.95)
    despeckle(c, region=m)
    if ear:
        ex, ey, rows = EAR
        block(c, ex + int(round(turn * 0.45)), ey, rows)

    fx = blank()                                 # features, clipped to the skull
    for (x, y, rows) in off(NOSE, t) + off(BLUSH, t) + off(STUBBLE, int(round(turn * 0.5))):
        block(fx, x, y, rows)
    for (x, y, rows) in off(GOATEE, t):
        block(fx, x, y, rows)
    for (x, y, rows) in off(MOUTHS[mouth], t):
        block(fx, x, y, rows)
    for (x, y, rows) in off(BROWS[brows], t):
        block(fx, x, y, rows)
    for y in range(H):
        for x in range(W):
            if fx[y][x] != '.' and m[y][x]:
                c[y][x] = fx[y][x]

    for (x, y, rows) in off(HAIR, int(round(turn * 0.4))):
        block(c, x, y, rows)
    if shades:
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
