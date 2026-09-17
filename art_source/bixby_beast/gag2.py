"""Swallow gag frame v2 (64x72): the original 64x64 bixby.png sits in the bottom 64 rows (same bottom-centre
anchor). Middle head has gulped Liam: his legs stick straight up out of the mouth, boots soles-up, belt buckle
between the lips, a headband tail hanging from the mouth corner. Side heads react (left smug, right startled).
The saddle starts cracking with lava glow (transformation hint)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK
import view

SRC = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Bixby/bixby.png'
GW, GH = 64, 72
OY = 8   # original sprite offset

XC = {'Y': (0x3b, 0x1e, 0x12, 255), 'A': (0xf4, 0xe9, 0xdc, 255)}


def C(ch):
    return XC[ch] if ch in XC else PALC[ch]


def stamp(cv, grid, x0, y0):
    rows = grid.strip('\n').split('\n')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch == '.':
                continue
            if ch == '_':
                cv.put(x0 + dx, y0 + dy, None)
            else:
                cv.put(x0 + dx, y0 + dy, C(ch))


# middle head face (cols 21..42, rows 9..22 in original coords -> +OY): squeezed-shut eyes pushed outward,
# puffed cheeks, clamped lips around Liam's waist (belt + buckle), nose hidden behind the legs
FACE = """
..k1222222.....22222333k..
.k112222222...222222333k..
kk12kk2222.....2222kk33kk.
k12222kk22.....22kk33334k.
k23kk2222w.....w2222kk44k.
k2322222ww.....wwv22234k..
k233wwwwww.....wwvvvu34k..
k34wwwwwww.....wwvvvvu4k..
kWwwwwwwwk.....kvvvvvuuk..
kwwwwwwwkk.....kkvvvvuuk..
kvwwwwkkkkkkkkkkkkkvuutk..
.kvvuuukkkkkkkkkkkkuutk...
..kkuuuuuuuuuuuuuuuuk.....
....kkkkkkkkkkkkkkkk......
"""

BOOT_L = """
..kkkkkk
.kEEEEEEk
kffgggEk.
kfggggk..
.kkggk...
"""
BOOT_R = """
kkkkkk..
kEEEEEEk.
.kgggEEEk
..kggggEk
...kggkk.
"""

HB_TAIL = """
kkk..
kHIk.
kHIk.
.kHIk
.kHIk
.kHIk
..kHIk
..kHIk
..kkk.
"""

SWEAT = """
.C.
CCk
CWk
.k.
"""

LEFT_SMUG_EYES = """
kk....kkk
YY....YYY
"""

LEFT_SMIRK = """
kWkkkkkkkk
kWwwwwwvk.
"""

RIGHT_STARTLED_EYES = """
.kk.....kk.
kWWk...kWWk
kWkk...kkWk
.kk.....kk.
"""


def legs(cv):
    """two legs straight up out of the mouth in a slight V; 3px fill each, shared centre outline"""
    top = 11
    for r in range(top, 29):
        t = (28 - r) / (28 - top)          # 0 at mouth, 1 at top
        la = 30 - int(round(t * 1.4))      # left leg centre drifts left
        lb = 34 + int(round(t * 1.4))      # right leg centre drifts right
        for c, sgn in ((la, -1), (lb, 1)):
            cv.put(c - 2, r, BLACK)
            cv.put(c + 2, r, BLACK)
            # light from top-left: left edge highlight, right edge shadow
            cv.put(c - 1, r, PALC['6'])
            cv.put(c, r, PALC['7'])
            cv.put(c + 1, r, PALC['8'])
        # gap between the legs: dark crotch shadow instead of showing the face through it
        for c in range(la + 3, lb - 2):
            cv.put(c, r, BLACK)
    # cuffs under the boots
    for c in range(26, 39):
        if cv.get(c, 12) not in (None, BLACK):
            cv.put(c, 12, PALC['9'])
    # belt with a silver buckle right at the lips
    for c in range(28, 37):
        cv.put(c, 27, BLACK)
    for c, ch in ((31, 'X'), (32, 'x'), (33, 'X')):
        cv.put(c, 27, PALC[ch])
    for c in (31, 33):
        cv.put(c, 26, PALC['y'])
    stamp(cv, BOOT_L, 22, 5)
    stamp(cv, BOOT_R, 34, 5)


def glow_cracks(cv):
    cracks = [
        [(2, 30, 'F'), (3, 31, 'o'), (3, 32, 'O'), (4, 33, 'o'), (4, 34, 'F')],
        [(2, 38, 'F'), (3, 39, 'o'), (4, 40, 'o'), (5, 40, 'F')],
        [(24, 38, 'F'), (25, 39, 'o'), (26, 40, 'O'), (27, 40, 'o'), (28, 41, 'F')],
        [(38, 38, 'F'), (39, 39, 'o'), (40, 39, 'O'), (41, 40, 'o'), (42, 41, 'F')],
        [(46, 41, 'F'), (47, 42, 'o'), (48, 42, 'o'), (49, 43, 'F')],
    ]
    for cr in cracks:
        for x, y, ch in cr:
            c = cv.get(x, y + OY)
            if c is not None and c != BLACK:
                cv.put(x, y + OY, PALC[ch])
    for x, y, ch in ((6, 20, 'o'), (58, 38, 'O'), (61, 33, 'o'), (19, 45, 'o'), (60, 26, 'o')):
        if cv.get(x, y + OY) is None:
            cv.put(x, y + OY, PALC[ch])


def build():
    lib.set_size(GW, GH)
    src = from_png(SRC)
    cv = Canvas(GW, GH)
    cv.blit(src, 0, OY)
    stamp(cv, FACE, 20, 8 + OY)
    legs(cv)
    stamp(cv, HB_TAIL, 24, 19 + OY)
    stamp(cv, LEFT_SMUG_EYES, 10, 23 + OY)
    stamp(cv, LEFT_SMIRK, 5, 30 + OY)
    stamp(cv, RIGHT_STARTLED_EYES, 44, 21 + OY)
    stamp(cv, SWEAT, 58, 12 + OY)
    glow_cracks(cv)
    return cv


if __name__ == '__main__':
    tag = sys.argv[1] if len(sys.argv) > 1 else 'gagv2'
    cv = build()
    cv.save(os.path.join(view.PREV, '%s.png' % tag))
    view.zoom_canvas(cv, 10, '%s_10x.png' % tag)
    print('ok')
