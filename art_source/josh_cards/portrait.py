"""Josh's dialogue portrait: Assets/Characters/Josh/portrait.png.

The old file was the two-headed Carter-and-Josh bust from the tag-team fight - the same image
sits in Carter's folder, byte for byte.  This draws Josh alone on the current design: gambler
fedora with the gold band and the black spade, hair showing under the brim, no shades, full dark
goatee, bone duster.

Format, measured off the old file so it drops straight into the dialogue system:
    64x64, binary alpha, bust framing with the shoulders running off the bottom edge.
Run:  python portrait.py [dest_dir]
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jlib
jlib.W = jlib.H = 64                       # portrait canvas, not the 80x80 sprite frame
from jlib import (PAL, blank, block, put, copy, poly_mask, mask_empty, m_and, m_or, m_sub,
                  outline_pixels, despeckle, to_rgba, quant, hf_values)
from rig import hdome, hbump
from pngio import write_png

W = H = 64
CX = 32
SKIN = 'gfdsa1'
BONE = 'IiUuNn'
WINE = 'LqQRE'
HAIRR = 'khHjJ'
DARK = 'xXvVz'


def paint(c, mask, hfn, ramp, th, z=0.95):
    for (x, y), (lam, lap, h0) in hf_values(mask, hfn, eps=0.5, zscale=z).items():
        c[y][x] = quant(lam, ramp, th)


def outline(c, mask, under, ch='#'):
    ol, pruned = outline_pixels(mask)
    for y in range(H):
        for x in range(W):
            if ol[y][x]:
                c[y][x] = ch
    for (x, y) in pruned:
        c[y][x] = under[y][x]


# ---------------------------------------------------------------- head
HEAD_ROWS = {}
for _y in range(23, 28):
    HEAD_ROWS[_y] = (20, 44)
for _y in range(28, 50):
    HEAD_ROWS[_y] = (19, 45)
HEAD_ROWS[50] = (20, 44)
HEAD_ROWS[51] = (22, 42)
HEAD_ROWS[52] = (25, 39)
HEAD_ROWS[53] = (28, 36)


def head_mask():
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    return m


def face_h(px, py):
    h = hdome(px, py, 32.0, 37.0, 14.0, 15.5, 7.0)
    h += hbump(px, py, 25.5, 40.0, 6.5, 6.5, 6.5, 7.0, 1.6)     # near cheek
    h += hbump(px, py, 39.0, 40.0, 6.0, 6.0, 6.0, 6.5, 1.2)     # far cheek
    h += hbump(px, py, 32.0, 48.5, 8.0, 8.0, 5.5, 4.0, 1.4)     # heavy jaw
    h += hbump(px, py, 32.5, 38.0, 2.6, 2.6, 4.0, 3.0, 1.5)     # nose bridge
    h += hbump(px, py, 32.0, 30.0, 11.0, 11.0, 4.0, 3.5, 0.8)   # brow ridge
    return h


# hair showing on top under the brim, swept back, warm brown against the cool brim
HAIR_TOP = [
    (21, 23, ["khHjJJJjHHHHHHHhhhhhhk"]),
    (21, 24, ["kjJJJJJJjHHHHHHHhhhhhk"]),
    (21, 25, ["kjJJJJjHHHHHHHhhhhHhhk"]),
    (20, 26, ["khjJJjHHHHHHhhhhhhHhhhk"]),
    (20, 27, ["kkhHHhHhhhhhhhhhhhHhhkk"]),
    (20, 28, ["kkhHh.hh.k...k.hh.hHhkk"]),
    (20, 29, [".kh.....................", ]),
]

# long hair down both temples, bunching beside the jaw
HAIR_SIDE = [
    (19, 29, ["jH"]), (19, 30, ["hH"]), (18, 31, ["#hHh"]),
    (18, 32, ["#khh"]), (18, 33, ["#khh"]), (18, 34, ["#khh"]),
    (19, 35, ["#khh"]), (19, 36, ["#khh"]), (19, 37, ["#kh"]),
    (19, 38, ["#kh"]), (19, 39, ["#kh"]), (19, 40, ["#kh"]),
    (19, 41, ["#kh"]), (19, 42, ["#kHh"]), (19, 43, ["#kHhh"]),
    (20, 44, ["#kHhh"]), (20, 45, ["#kHhh"]), (21, 46, ["#kHhh"]),
    (22, 47, ["#kHh"]), (23, 48, ["#kh"]),
    (43, 29, ["Hj"]), (43, 30, ["Hh"]), (42, 31, ["hHh#"]),
    (42, 32, ["hhk#"]), (42, 33, ["hhk#"]), (42, 34, ["hhk#"]),
    (42, 35, ["hhk#"]), (42, 36, ["hhk#"]), (42, 37, ["hk#"]),
    (42, 38, ["hk#"]), (42, 39, ["hk#"]), (42, 40, ["hk#"]),
    (42, 41, ["hk#"]), (41, 42, ["hHk#"]), (40, 43, ["hhHk#"]),
    (39, 44, ["hhHk#"]), (39, 45, ["hhHk#"]), (38, 46, ["hhHk#"]),
    (38, 47, ["hHk#"]), (38, 48, ["hk#"]),
]

BROW = [(22, 31, ["hkkkkkkkk", "kkkkkkkkk"]), (33, 31, ["kkkkkkkkh", "kkkkkkkkk"])]
EYES = [
    (23, 35, ["#######"]), (23, 36, ["#wweew#"]), (23, 37, ["#wweew#"]), (24, 38, ["#####"]),
    (34, 35, ["#######"]), (34, 36, ["#weeww#"]), (34, 37, ["#weeww#"]), (35, 38, ["#####"]),
]
NOSE = [(31, 40, ["sd"]), (30, 41, ["asdf"]), (30, 42, ["asdf"]), (31, 43, ["ff"])]
BLUSH = [(23, 42, ["rrr"]), (39, 42, ["rr"])]

# Full dark goatee, drawn as ONE SOLID MASS - the moustache runs unbroken down around the mouth
# into the chin beard.  It used to be a ring with the skin of his upper lip showing through the
# middle, which at portrait scale read as a bald patch in the beard rather than as separation.
# The moustache half is a step lighter than the chin beard so the two still read apart.
GOATEE = [
    (26, 44, ["hkkkkkkkkkkkh"]),
    (26, 45, ["kHHHHHHHHHHHk"]),
    (26, 46, ["kHHHHHHHHHHHk"]),
    (26, 47, ["khhhhhhhhhhhk"]),
    (26, 48, ["khhhhhhhhhhhk"]),
    (26, 49, ["kkhhhhhhhhhkk"]),
    (27, 50, ["hkkHHkkkkkkh"]),
    (28, 51, ["hkkkkkkkkh"]),
    (29, 52, ["hkkkkkkh"]),
    (31, 53, ["hkkh"]),
]
# The mouth now sits inside that mass, so it reads by CONTRAST instead of by a skin gap: a black
# slit with a dark interior and a glint of tooth.
MOUTH = [
    (29, 47, ["#######"]),
    (29, 48, ["#mmwWm#"]),
    (29, 49, ["#######"]),
]

# ---------------------------------------------------------------- hat
CROWN = [(24, 14), (27, 10), (37, 10), (40, 14), (43, 17), (44, 22), (20, 22), (21, 17)]
BAND_ROWS = {19: (21, 43), 20: (20, 44), 21: (20, 44), 22: (20, 44)}
BAND_TONE = {19: 'F', 20: 'F', 21: 'D', 22: 'A'}
SPADE = [
    (32, 9, ["D"]),
    (30, 10, ["D###D"]),
    (29, 11, ["D#####D"]),
    (28, 12, ["D#######D"]),
    (28, 13, ["D#######D"]),
    (28, 14, ["D#######D"]),
    (28, 15, ["DD#####DD"]),
    (30, 16, ["D###D"]),
    (31, 17, ["D#D"]),
    (30, 18, ["DD#DD"]),
]
BRIM_ROWS = {22: (17, 47), 23: (9, 55), 24: (5, 59), 25: (5, 59), 26: (9, 55), 27: (16, 48)}
BRIM_TONE = {22: 'V', 23: 'X', 24: 'X', 25: 'x', 26: 'x', 27: 'x'}

# ---------------------------------------------------------------- bust
NECK = [(26, 49), (38, 49), (39, 59), (25, 59)]
COAT = [(2, 63), (4, 58), (9, 55), (17, 53), (24, 52), (32, 54), (40, 52),
        (47, 53), (55, 55), (60, 58), (62, 63)]
TEE = [(26, 55), (38, 55), (40, 63), (24, 63)]
COLLAR_L = [(22, 53), (29, 56), (29, 63), (19, 63), (17, 57)]
COLLAR_R = [(42, 53), (35, 56), (35, 63), (45, 63), (47, 57)]
LINING = [(27, 56, ["Qq"]), (27, 57, ["QQq"]), (28, 58, ["QQ"]), (28, 59, ["Qq"]),
          (28, 60, ["Qq"]), (28, 61, ["qq"]),
          (35, 56, ["qQ"]), (34, 57, ["qQQ"]), (34, 58, ["QQ"]), (34, 59, ["qQ"]),
          (34, 60, ["qQ"]), (34, 61, ["qq"])]


def build():
    c = blank()

    # --- bust first, the head sits on top of it
    under = copy(c)
    cm = poly_mask(COAT)
    paint(c, cm, lambda px, py: hdome(px, py, 32.0, 66.0, 24.0, 14.0, 7.0), BONE,
          [0.0, 0.13, 0.32, 0.58, 0.87], 0.9)
    despeckle(c, chars=BONE, region=cm)
    outline(c, cm, under)
    tm = m_and(poly_mask(TEE), cm)
    under = copy(c)
    paint(c, tm, lambda px, py: hdome(px, py, 32.0, 62.0, 8.0, 10.0, 5.0), DARK,
          [0.28, 0.68, 0.90, 0.99], 0.9)
    outline(c, tm, under)
    for poly in (COLLAR_L, COLLAR_R):
        under = copy(c)
        pm = m_and(poly_mask(poly), m_or(cm, poly_mask(poly)))
        paint(c, pm, lambda px, py: hdome(px, py, 32.0, 60.0, 20.0, 12.0, 6.0), BONE,
              [0.0, 0.13, 0.32, 0.58, 0.87], 0.9)
        outline(c, pm, under)
    for (x, y, rows) in LINING:
        block(c, x, y, rows)
    under = copy(c)
    nm = poly_mask(NECK)
    paint(c, nm, lambda px, py: hdome(px, py, 32.0, 52.0, 7.0, 12.0, 6.0), SKIN,
          [0.0, 0.35, 0.6, 0.85, 0.98], 0.95)
    outline(c, nm, under)

    # --- head
    hm = head_mask()
    under = copy(c)
    paint(c, hm, face_h, SKIN, [0.0, 0.26, 0.52, 0.80, 0.965], 0.95)
    despeckle(c, region=hm)
    outline(c, hm, under)

    fx = blank()
    for (x, y, rows) in HAIR_TOP + NOSE + BLUSH + EYES + BROW:
        block(fx, x, y, rows)
    for y in range(H):
        for x in range(W):
            if fx[y][x] != '.' and hm[y][x]:
                c[y][x] = fx[y][x]
    for (x, y, rows) in GOATEE + MOUTH:
        block(c, x, y, rows)
    for (x, y, rows) in HAIR_SIDE:
        block(c, x, y, rows)

    # --- hat
    under = copy(c)
    km = poly_mask(CROWN)
    paint(c, km, lambda px, py: hdome(px, py, 32.0, 19.0, 13.0, 13.0, 7.0)
          + hbump(px, py, 26.0, 13.0, 6.0, 6.0, 4.0, 6.0, 1.3)
          - hbump(px, py, 32.0, 9.5, 4.0, 4.0, 2.5, 4.0, 2.2), WINE,
          [0.16, 0.42, 0.70, 0.94], 0.85)
    outline(c, km, under)
    for y, (lo, hi) in BAND_ROWS.items():
        for x in range(lo, hi + 1):
            if km[y][x]:
                c[y][x] = BAND_TONE[y]
    for (x, y, rows) in SPADE:
        block(c, x, y, rows)
    bm = mask_empty()
    for y, (lo, hi) in BRIM_ROWS.items():
        for x in range(lo, hi + 1):
            bm[y][x] = True
            ch = BRIM_TONE[y]
            if y == 23 and lo + 3 <= x <= lo + 20:
                ch = 'z'
            if y == 23 and x > hi - 16:
                ch = 'X'
            if y == 24 and x < lo + 8:
                ch = 'V'
            c[y][x] = ch
    ol, _ = outline_pixels(bm, prune=False)
    for y in range(H):
        for x in range(W):
            if ol[y][x] and y != 22:
                c[y][x] = '#'
    return c


if __name__ == '__main__':
    out = (sys.argv[1] if len(sys.argv) > 1
           else 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Josh')
    c = build()
    p = out.rstrip('/\\') + '/portrait.png'
    write_png(p, W, H, to_rgba(c))
    print('wrote', p, '%dx%d' % (W, H))
