"""Josh 'card showman' redesign rig: 80x80, feet on row 79, figure centred on x=40.

Body is traced as closed polygons and cel-shaded off a height field (same technique used for
Assets/Characters/Mason and Josh's approved redesign). The face is hand-authored text blocks so
the approved likeness (grin, pencil moustache, soul patch, blue shades) is exact.
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jlib import *
from jlib import _norm

SKIN = 'gfdsa1'
IVORY = 'IiUuNn'          # duster, dark -> light
JEAN = 'OopP'
BLACK = 'xXvVz'
RED = 'LqQRE'


# ------------------------------------------------------------------ height-field helpers
def hcap(px, py, ax, ay, bx, by, r0, r1, amp=1.0):
    t, qx, qy = seg_t(px, py, ax, ay, bx, by)
    r = r0 + (r1 - r0) * t
    d = math.hypot(px - qx, py - qy)
    return amp * math.sqrt(max(0.0, r * r - d * d))


def hdome(px, py, cx, cy, rx, ry, amp):
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    return amp * math.sqrt(max(0.0, 1 - d2))


def hbump(px, py, cx, cy, rl, rr, rt, rb, amp, power=1.0):
    rx = rl if px < cx else rr
    ry = rt if py < cy else rb
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    if d2 >= 1:
        return 0.0
    return amp * (1 - d2) ** power


def hplat(px, py, cx, cy, rl, rr, rt, rb, amp, k=4.0, dome=0.35):
    rx = rl if px < cx else rr
    ry = rt if py < cy else rb
    d2 = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
    if d2 >= 1:
        return 0.0
    return amp * (dome * (1 - d2) + (1 - dome) * min(1.0, (1 - d2) * k))


def hf_shade(c, mask, hfn, ramp, th, crease=None, crease_th=None, zscale=1.0, outline=True):
    vals = hf_values(mask, hfn, eps=0.5, zscale=zscale)
    under = copy(c)
    for (x, y), (lam, lap, h0) in vals.items():
        ch = quant(lam, ramp, th)
        if crease is not None and lap > crease_th:
            i = ramp.index(ch)
            ch = ramp[max(0, min(i, crease) - 1)]
        c[y][x] = ch
    if outline:
        ol, pruned = outline_pixels(mask)
        for y in range(H):
            for x in range(W):
                if ol[y][x]:
                    c[y][x] = '#'
        for (x, y) in pruned:
            c[y][x] = under[y][x]
    return vals


TH_LIMB = [0.0, 0.35, 0.6, 0.85, 0.98]      # 6-tone skin ramp
TH_6 = [0.02, 0.34, 0.58, 0.80, 0.96]       # 6-tone (ivory)
TH_5 = [0.20, 0.55, 0.80, 0.965]            # 5-tone (red)
TH_BLK = [0.28, 0.68, 0.90, 0.99]           # 5-tone (black cloth/leather)
TH_4 = [0.10, 0.50, 0.86]                   # 4-tone (jean)


def limb(c, poly, a, b, r0, r1, ramp=SKIN, th=TH_LIMB, extra=None):
    def hf(px, py):
        h = hcap(px, py, a[0], a[1], b[0], b[1], r0, r1)
        if extra:
            h = max(h, extra(px, py))
        return h
    return hf_shade(c, poly_mask(poly), hf, ramp, th)


# ================================================================== HEAD
# head skin: x29..51 (23 wide), y24..46. centre x = 40.
HEAD_ROWS = {}
for _y in range(24, 41):
    HEAD_ROWS[_y] = (29, 51)
HEAD_ROWS[41] = (29, 51)
HEAD_ROWS[42] = (30, 50)
HEAD_ROWS[43] = (31, 49)
HEAD_ROWS[44] = (32, 48)
HEAD_ROWS[45] = (34, 46)
HEAD_ROWS[46] = (36, 44)


def head_mask():
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def face_h(px, py):
    """Rounded skull + cheeks + chin + nose, lit from the upper left."""
    h = hdome(px, py, 40.0, 35.0, 13.0, 12.5, 7.0)
    h += hbump(px, py, 34.0, 35.5, 5.0, 5.0, 5.0, 5.5, 1.5)     # near cheek
    h += hbump(px, py, 46.5, 35.5, 4.5, 4.5, 5.0, 5.0, 1.1)     # far cheek
    h += hbump(px, py, 40.0, 43.5, 6.0, 6.0, 4.0, 4.0, 1.3)     # chin / jaw
    h += hbump(px, py, 41.0, 35.0, 2.6, 2.6, 4.0, 3.0, 1.7)     # nose bridge
    h += hbump(px, py, 40.0, 28.0, 10.0, 10.0, 4.0, 4.0, 0.7)   # brow / forehead
    return h


EAR = (26, 32, [
    ".##.",
    "#sd#",
    "#af#",
    "#sf#",
    "#df#",
    "#dd#",
    ".#d#",
    "..##",
])

# --- one row of shaded forehead peeking out under the brim
BRIM_SHADOW = [
    (30, 29, ["ffffffffffffffffffff"]),
]

# --- blue sunglasses, worn ON the eyes under the cap brim.  Anchored x29..51.
SHADES = [
    (29, 30, ["#######################"]),
    (29, 31, ["#CcBBBbbbb#XXX#BBBbbbb#"]),
    (29, 32, ["#cBBBbbbbb#.X.#BBbbbbb#"]),
    (29, 33, ["#BBBbbbbbb#.X.#Bbbbbbb#"]),
    (29, 34, ["##bbbbbb##.....##bbbb##"]),
]
GLINT = [                       # hard diagonal flash across the near lens
    (33, 33, ["C"]),
    (34, 32, ["CC"]),
    (35, 31, ["Cw"]),
    (46, 32, ["c"]),
    (47, 31, ["C"]),
]
TEMPLES = [(28, 31, ["X"]), (28, 32, ["X"]), (52, 31, ["X"]), (52, 32, ["X"])]

NOSE = [
    (40, 35, [".sd."]),
    (39, 36, ["asdf"]),
    (40, 37, [".ff."]),
]

BLUSH = [(31, 35, ["rrr"]), (48, 35, ["rr"]), (32, 36, ["rr"]), (48, 36, ["r"])]

STUBBLE = [(30, 40, ["t"]), (31, 42, ["t"]), (32, 44, ["T"]), (36, 45, ["T"]),
           (44, 45, ["T"]), (46, 44, ["T"]), (48, 42, ["T"]), (49, 40, ["T"])]

# approved grin + pencil moustache + soul patch, centred on x40
MOUTH = [
    (35, 38, [".hkkkh.hkkkh."]),
    (34, 39, ["##############"]),
    (33, 40, ["#wwwWwwwWwwwWw#"]),
    (34, 41, ["#Wwwwwwwwwwww#"]),
    (35, 42, ["############"]),
    (39, 43, ["hkh"]), (39, 44, ["khk"]), (39, 45, ["hkh"]),
]

# --- hair escaping under the cap: spiky tufts at both sides
HAIR_SIDE = [
    (25, 27, ["...hh"]),
    (24, 28, ["..jHh"]),
    (24, 29, [".jHhhk"]),
    (23, 30, ["#hHHhkk"]),
    (23, 31, ["#khHhk."]),
    (24, 32, ["#khhk."]),
    (25, 33, ["#kkh."]),
    (26, 34, [".#k."]),
    (50, 27, ["hh..."]),
    (51, 28, ["hHj.."]),
    (50, 29, ["kHhHj."]),
    (50, 30, ["khHHh#"]),
    (51, 31, ["khHhk#"]),
    (52, 32, ["khhk#"]),
    (53, 33, ["hkk#"]),
    (54, 34, [".k#"]),
]


def build_head(c, glint=True):
    m = head_mask()
    hf_shade(c, m, face_h, SKIN, [0.0, 0.26, 0.52, 0.80, 0.965], zscale=0.95)
    despeckle(c, region=m)
    block(c, *EAR)
    for (x, y, rows) in BRIM_SHADOW + NOSE + BLUSH + STUBBLE + MOUTH:
        block(c, x, y, rows)
    for (x, y, rows) in TEMPLES:
        block(c, x, y, rows)
    for (x, y, rows) in SHADES:
        block(c, x, y, rows)
    if glint:
        for (x, y, rows) in GLINT:
            block(c, x, y, rows)
    for (x, y, rows) in HAIR_SIDE:
        block(c, x, y, rows)
    return c


# ================================================================== CAP
# red crown y9..23, white front band y17..23, dark flat brim y23..29 (hand-authored extents).
CROWN = [(30, 11), (35, 9), (45, 9), (50, 11), (53, 14), (54, 18), (55, 23),
         (25, 23), (26, 18), (27, 14)]


def crown_h(px, py):
    h = hdome(px, py, 40.0, 24.0, 15.5, 15.5, 8.0)
    h += hbump(px, py, 34.0, 14.0, 7.0, 7.0, 5.0, 7.0, 1.4)
    return h


BAND_POLY = [(26, 17), (54, 17), (55, 23), (25, 23)]


def band_h(px, py):
    return hdome(px, py, 40.0, 25.0, 15.5, 9.0, 7.0) + hbump(px, py, 32.0, 19.0, 8.0, 8.0, 3.0, 4.0, 1.0)


# gold diamond pip on the white band
PIP = [
    (38, 16, [".D."]),
    (37, 17, ["DFFD"]),
    (36, 18, ["DFFFFD"]),
    (36, 19, ["#FFFFA"]),
    (37, 20, ["#FFA#"]),
    (38, 21, ["#A#"]),
]

# --- flat brim: row extents + per-row tone.  Widest at y25-26, arcs to a point at the centre bottom.
BRIM_ROWS = {23: (27, 54), 24: (24, 56), 25: (23, 57), 26: (23, 57),
             27: (25, 55), 28: (29, 52), 29: (34, 47)}
BRIM_TONE = {23: 'v', 24: 'v', 25: 'V', 26: 'v', 27: 'X', 28: 'X', 29: 'x'}


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
            if y == 25 and (x < lo + 2 or x > hi - 3):
                ch = 'v'
            if y == 24 and lo + 3 <= x <= hi - 6:
                ch = 'V'
            if y == 27 and x > hi - 6:
                ch = 'x'
            c[y][x] = ch
    ol, _ = outline_pixels(m, prune=False)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                c[y][x] = '#'
    return c


# playing card tucked into the band on his left (our right), poking up past the crown
BAND_CARD = [
    (55, 10, ["..##"]),
    (54, 11, [".#nw#"]),
    (54, 12, ["#nnw#"]),
    (53, 13, ["#nnw#"]),
    (53, 14, ["#nQw#"]),
    (52, 15, ["#QQQw#"]),
    (52, 16, ["#QQQw#"]),
    (52, 17, ["#nQnw#"]),
    (52, 18, ["#nnNu#"]),
    (52, 19, ["#NNuu#"]),
    (52, 20, [".#Nu#"]),
    (52, 21, [".#uu#"]),
    (52, 22, [".####"]),
]


def build_cap(c):
    for (x, y, rows) in BAND_CARD:
        block(c, x, y, rows)
    cm = poly_mask(CROWN)
    hf_shade(c, cm, crown_h, RED, TH_5, zscale=0.85)
    bm = m_and(poly_mask(BAND_POLY), cm)
    hf_shade(c, bm, band_h, IVORY, TH_6, zscale=0.85, outline=False)
    for (x, y, rows) in PIP:
        block(c, x, y, rows)
    build_brim(c)
    return c
