"""Josh's head: approved likeness (grin, pencil moustache, soul patch, blue shades) under an
Ash-style red/white cap with a card tucked in the band.

Vertical anchors in the 80x80 frame:
    y15..26  cap crown (red, white front band y21..26)
    y25..30  flat brim (dark, lit top surface)
    y24..48  head skin, x29..51, centre x=40
    y32..36  blue sunglasses ON the eyes
    y41..44  grin
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
import rig
from rig import hdome, hbump, hf_shade, TH_5, TH_6, TH_BLK, RED, IVORY, BLACK, SKIN
import cards as CD

CX = 40

# ------------------------------------------------------------------ head skin
HEAD_ROWS = {}
for _y in range(24, 43):
    HEAD_ROWS[_y] = (29, 51)
HEAD_ROWS[43] = (29, 51)
HEAD_ROWS[44] = (30, 50)
HEAD_ROWS[45] = (31, 49)
HEAD_ROWS[46] = (32, 48)
HEAD_ROWS[47] = (34, 46)
HEAD_ROWS[48] = (36, 44)


def head_mask():
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def face_h(px, py):
    h = hdome(px, py, 40.0, 36.0, 13.0, 13.5, 7.0)
    h += hbump(px, py, 34.0, 37.0, 5.5, 5.5, 5.5, 6.0, 1.6)     # near cheek
    h += hbump(px, py, 46.5, 37.0, 5.0, 5.0, 5.0, 5.5, 1.1)     # far cheek
    h += hbump(px, py, 40.0, 45.5, 6.5, 6.5, 4.5, 4.0, 1.3)     # chin
    h += hbump(px, py, 41.0, 37.5, 2.6, 2.6, 4.0, 3.0, 1.7)     # nose bridge
    h += hbump(px, py, 40.0, 31.0, 10.0, 10.0, 4.0, 4.0, 0.7)   # brow ridge
    return h


EAR = (26, 34, [
    ".##.",
    "#sd#",
    "#af#",
    "#sf#",
    "#df#",
    "#dd#",
    ".#d#",
    "..##",
])

FOREHEAD = [(30, 31, ["ffffffffffffffffffff"])]

# --- REJECTED ALTERNATIVE (shades_up=False): blue sunglasses worn ON the eyes under the brim.
# The user picked shades-up; this branch is kept only so the look can be re-rendered on request.
SHADES = [
    (29, 32, ["#######################"]),
    (29, 33, ["#CcBBBbbbb#XXX#BBBbbbb#"]),
    (29, 34, ["#cBBBbbbbb#.X.#BBbbbbb#"]),
    (29, 35, ["#BBBbbbbbb#.X.#Bbbbbbb#"]),
    (29, 36, ["##bbbbbb##.....##bbbb##"]),
]
GLINT = [
    (33, 35, ["C"]),
    (34, 34, ["Cw"]),
    (35, 33, ["wC"]),
    (46, 34, ["c"]),
    (47, 33, ["C"]),
]
TEMPLES = [(28, 33, ["X"]), (28, 34, ["X"]), (52, 33, ["X"]), (52, 34, ["X"])]

# --- SHIPPED (shades_up=True, the default): shades pushed up onto the cap brim, his approved
# eyes visible.  Carried over from his approved redesign (art_source/josh_v2/head.py, BROW_EYES['D']).
SHADES_UP = [
    (30, 23, ["#####################"]),
    (30, 24, ["#CccBBBBB#XXX#cBBBBB#"]),
    (30, 25, ["#cBBBBBBb#.X.#BBBBBb#"]),
    (30, 26, ["#BBBbbbb##.X.##BBBbb#"]),
    (30, 27, ["##Vbb##########Vbb###"]),
]
EYES = [
    (31, 29, [".hkkkkh.", "kkkkkkkk", "k......."]),
    (43, 29, ["hkkkkh.", "kkkkkkk", "......k"]),
    (32, 32, [".####.", "#ewee#", ".#ee#.", "d....d"]),
    (44, 32, [".###.", "#ewe#", ".#e#.", "d...d"]),
]

NOSE = [
    (40, 37, [".sd."]),
    (39, 38, ["asdf"]),
    (40, 39, [".ff."]),
]

BLUSH = [(31, 37, ["rrr"]), (48, 37, ["rr"]), (32, 38, ["rr"]), (48, 38, ["r"])]

STUBBLE = [(30, 42, ["t"]), (31, 44, ["t"]), (33, 46, ["T"]), (37, 47, ["T"]),
           (43, 47, ["T"]), (46, 46, ["T"]), (48, 44, ["T"]), (49, 42, ["T"])]

MOUTH = [
    (35, 40, [".hkkkh.hkkkh"]),               # pencil moustache, philtrum gap
    (34, 41, ["#############"]),
    (33, 42, ["#wwwWwwwWwwwWw#"]),
    (34, 43, ["#Wwwwwwwwwww#"]),
    (35, 44, ["###########"]),
    (39, 45, ["hkh"]), (39, 46, ["khk"]), (40, 47, ["k"]),
]

# --- dark hair escaping under the cap, both sides
HAIR = [
    (26, 28, ["...hh"]),
    (25, 29, ["..jHh"]),
    (25, 30, [".jHhhk"]),
    (24, 31, ["#hHHhkk"]),
    (24, 32, ["#jhHhk."]),
    (24, 33, ["#khhk."]),
    (25, 34, ["#kkh."]),
    (26, 35, [".#k."]),
    (50, 28, ["hh..."]),
    (51, 29, ["hHj.."]),
    (50, 30, ["kHhHj."]),
    (50, 31, ["khHHhj#"]),
    (51, 32, ["khHhk#"]),
    (52, 33, ["khhk#"]),
    (53, 34, ["hkk#"]),
    (54, 35, [".k#"]),
]


def build_face(c, glint=True, shades_up=True):
    m = head_mask()
    hf_shade(c, m, face_h, SKIN, [0.0, 0.26, 0.52, 0.80, 0.965], zscale=0.95)
    despeckle(c, region=m)
    block(c, *EAR)
    for (x, y, rows) in FOREHEAD + NOSE + BLUSH + STUBBLE + MOUTH:
        block(c, x, y, rows)
    if shades_up:
        for (x, y, rows) in EYES:
            block(c, x, y, rows)
    else:
        for (x, y, rows) in TEMPLES:
            block(c, x, y, rows)
        for (x, y, rows) in SHADES:
            block(c, x, y, rows)
        if glint:
            for (x, y, rows) in GLINT:
                block(c, x, y, rows)
    for (x, y, rows) in HAIR:
        block(c, x, y, rows)
    return c


# ================================================================== CAP
# red crown y15..24 (symmetric about x=40), white front panel y19..24, flat brim y24..29.
CROWN = [(31, 17), (35, 15), (45, 15), (49, 17), (52, 19), (53, 22), (53, 24),
         (27, 24), (27, 22), (28, 19)]


def crown_h(px, py):
    h = hdome(px, py, 40.0, 26.0, 14.0, 12.0, 8.0)
    h += hbump(px, py, 34.0, 19.0, 7.0, 7.0, 4.0, 6.0, 1.3)
    return h


PANEL = [(32, 20), (36, 18), (44, 18), (48, 20), (49, 24), (31, 24)]


def panel_h(px, py):
    return hdome(px, py, 40.0, 26.0, 9.5, 8.5, 7.0) + hbump(px, py, 35.5, 21.0, 5.0, 5.0, 2.5, 3.0, 0.9)


PIP = [                                   # bold black spade on the white panel
    (37, 18, [".#."]),
    (36, 19, ["###"]),
    (36, 20, ["#####"]),
    (36, 21, ["#####"]),
    (36, 22, ["##D##"]),
    (37, 23, [".#."]),
    (36, 24, ["###"]),
]

# --- flat brim: row extents + per-row tone; thin lit top edge, dark body
BRIM_ROWS = {24: (28, 52), 25: (24, 56), 26: (22, 58), 27: (22, 58), 28: (25, 55), 29: (30, 50)}
BRIM_TONE = {24: 'X', 25: 'V', 26: 'X', 27: 'X', 28: 'x', 29: 'x'}


def brim_mask():
    m = mask_empty()
    for y, (lo, hi) in BRIM_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def build_brim(c):
    m = brim_mask()
    for y, (lo, hi) in BRIM_ROWS.items():
        for x in range(lo, hi + 1):
            ch = BRIM_TONE[y]
            if y == 25 and lo + 2 <= x <= lo + 13:
                ch = 'z'                      # specular streak on the lit side
            if y == 25 and x > hi - 10:
                ch = 'X'
            if y == 26 and x < lo + 4:
                ch = 'V'
            c[y][x] = ch
    ol, _ = outline_pixels(m, prune=False)
    for y in range(H):
        for x in range(W):
            if ol[y][x] and y != 24:
                c[y][x] = '#'
    return c


def build_band_card(c):
    """Playing card tucked into the band on his left (our right)."""
    CD.draw_card(c, 55, 18, 7, 14, -32, pip=CD.DIAMOND3, pip_col='Q')
    return c


def build_cap(c):
    build_band_card(c)
    cm = poly_mask(CROWN)
    hf_shade(c, cm, crown_h, RED, [0.30, 0.62, 0.86, 0.985], zscale=0.85)
    pm = m_and(poly_mask(PANEL), cm)
    hf_shade(c, pm, panel_h, 'UuNn', [0.10, 0.34, 0.72], zscale=0.85, outline=False)
    for (x, y, rows) in PIP:
        block(c, x, y, rows)
    build_brim(c)
    return c


def build(c, glint=True, shades_up=True):
    build_face(c, glint, shades_up)
    build_cap(c)
    if shades_up:
        for (x, y, rows) in SHADES_UP:
            block(c, x, y, rows)
        block(c, 34, 23, ["Cw"])
        block(c, 46, 23, ["Cc"])
    return c


if __name__ == '__main__':
    out = sys.argv[1]
    c = blank()
    build(c)
    save_png(c, out + '/head_test.png')
    preview(c, out + '/head_test_8x.png', s=8)
    print('ok')
