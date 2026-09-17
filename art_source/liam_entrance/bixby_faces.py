"""Expression edits stamped over the approved bixby.png (coords are bixby.png pixels + (ox, oy)).
Face map (bixby.png): middle head eyes (25-27,10-12) & (35-37,10-12), nose rows 14-17 x28-34, mouth rows 18-22;
left head eyes (10-11,23-24) & (16-18,23-24), tongue rows 30-32 x6-14;
right head closed eyes (45-47,22-23) & (53-55,22-23), tongue rows 30-35 x49-57."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
import fx

BX = {'k': BLACK, 'W': WHITE, 'w': B_FUR[1], 'v': B_FUR[2], 'u': B_FUR[3],
      '1': B_TAN[0], '2': B_TAN[1], '3': B_TAN[2], '4': B_TAN[3],
      'Y': B_EYE[1], 'A': B_EYE[0], 'M': hx('5a1a22'), 'm': B_TONGUE[1], 'n': B_TONGUE[2], 'p': B_TONGUE[0],
      'P': B_COLLAR[0], 'Q': B_COLLAR[1], 'r': B_COLLAR[2],
      'G': B_SADDLE[0], 'B': B_SADDLE[1], 'D': B_SADDLE[2], 'J': B_SADDLE[3],
      'b': SWEAT[1], 'c': SWEAT[2], 'x': B_EAR[2], 'y': B_EAR[1]}


def st(cv, ox, oy, x, y, grid):
    cv.stamp(grid, ox + x, oy + y, BX)


def clear_mid_eyes(cv, ox, oy):
    st(cv, ox, oy, 24, 9, """
.2222
22222
22222
22223
""")
    st(cv, ox, oy, 34, 9, """
33333
33333
33333
33333
""")


# ------------------------------------------------------------------ SMACK: flinch
def flinch(cv, ox, oy):
    clear_mid_eyes(cv, ox, oy)
    bulge = """
.kkk.
kWWWk
kWkWk
kWWWk
.kkk.
"""
    st(cv, ox, oy, 23, 8, bulge)
    st(cv, ox, oy, 35, 8, bulge)
    # yelp
    st(cv, ox, oy, 28, 18, """
.kkkkk.
kMMMMMk
kMmmmMk
.kkkkk.
""")
    # side heads squeeze their eyes shut
    st(cv, ox, oy, 10, 23, "k3.....3k")
    st(cv, ox, oy, 10, 24, "3k.....kk")
    st(cv, ox, oy, 45, 22, "k22.....22k")
    st(cv, ox, oy, 45, 23, "2kk.....kk2")
    fx.shock(cv, ox + 27, oy - 4)
    fx.sweat(cv, ox + 1, oy + 12)
    fx.sweat(cv, ox + 58, oy + 10)


# ------------------------------------------------------------------ "he likes it": glare
def glare(cv, ox, oy):
    clear_mid_eyes(cv, ox, oy)
    st(cv, ox, oy, 23, 8, """
kk...
.kkkk
.kWYk
..kk.
""")
    st(cv, ox, oy, 35, 8, """
...kk
kkkk.
kWYk.
.kk..
""")
    # flat unamused mouth
    st(cv, ox, oy, 28, 19, """
wkkkkkv
kvvvvvk
""")
    # side heads side-eye toward Liam (screen right)
    st(cv, ox, oy, 10, 23, "kk.....kk")
    st(cv, ox, oy, 10, 24, "wY.....wY")
    st(cv, ox, oy, 45, 22, "kkk.....kkk")
    st(cv, ox, oy, 45, 23, "wYk.....wYk")
    fx.vein(cv, ox + 37, oy + 0)


# ------------------------------------------------------------------ fed up: snarl + hackles + veins
def snarl(cv, ox, oy):
    clear_mid_eyes(cv, ox, oy)
    st(cv, ox, oy, 23, 7, """
kkk....
.kkkkk.
.kWWYk.
..kkk..
""")
    st(cv, ox, oy, 34, 7, """
....kkk
.kkkkk.
.kWYYk.
..kkk..
""")
    # wrinkled muzzle
    st(cv, ox, oy, 26, 12, "u.....u")
    st(cv, ox, oy, 27, 13, "u...u")
    # bared teeth
    st(cv, ox, oy, 25, 18, """
kkkkkkkkkkkkk
kWkPPPPPPPkWk
kWWWWWWWWWWWk
kkMMMMMMMMMkk
.kWkWWWWWkWk.
..kkkkkkkkk..
""")
    # left head: teeth instead of tongue, side-eye glare
    st(cv, ox, oy, 10, 23, "kk.....kk")
    st(cv, ox, oy, 10, 24, "wY.....wY")
    st(cv, ox, oy, 5, 29, """
kkkkkkkkkk
kWWWWWWWWk
kMMMMMMMMk
.kWkWkWkk.
..kkkkkk..
""")
    # right head: tongue pulled in, teeth bared, glaring
    st(cv, ox, oy, 45, 22, "kkk.....kkk")
    st(cv, ox, oy, 45, 23, "wYk.....wYk")
    st(cv, ox, oy, 48, 29, """
kkkkkkkkkk
kWWWWWWWWk
kMMMMMMMMk
.kWkWkWkk.
..kkkkkk_.
""")
    st(cv, ox, oy, 52, 34, "__")
    st(cv, ox, oy, 53, 35, "_")
    # hackles: bristling dark fur along both flanks, bristled tail tip
    for (x, y) in ((-2, 24), (-3, 29), (-2, 34), (-3, 39)):
        st(cv, ox, oy, x, y, """
kk..
kDDk
.kDDk
""")
    for (x, y) in ((1, 8), (5, 6), (10, 7)):
        st(cv, ox, oy, x, y, """
.k.
kWk
""")
    # glare shadow over the middle head's brow
    shade = {(x, y) for x in range(23, 40) for y in range(3, 8)}
    cv.darken({(ox + x, oy + y) for (x, y) in shade}, 1)
    fx.vein(cv, ox + 37, oy - 3, big=True)
    fx.vein(cv, ox + 12, oy + 13)
    fx.vein(cv, ox + 52, oy + 12)
