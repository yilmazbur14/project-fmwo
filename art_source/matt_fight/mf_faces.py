"""Faces for the fight body set, built exactly as the intro's (mi_faces): the approved idle face with
its features swapped by patches, and whole lower-face rows where the jaw changes shape.
"""
import mf_base  # noqa: F401  (paths)
from mf_base import G

# ------------------------------------------------------------------ cheeks full (the yell's inhale)
# He has gulped a lungful and is holding it: the cheeks bulge a texel past his jaw on both sides,
# lit round on the left, the lips pressed into a short line between them, the chin a row lower.
PUFF_ROWS = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    "....k 11122 22222 23332 22222 22333 k....",       # 43  cheeks bulge past the jaw
    "....k 11112 22222 22222 22222 23333 k....",       # 44
    "....k 11122 22223 kkkkk 32222 23333 k....",       # 45  lips pressed
    "....k 11222 22222 23332 22222 23334 k....",       # 46
    "....k 12222 22222 22222 22222 33344 k....",       # 47
    "..... k1222 22222 22222 22223 3334k .....",       # 48
    "..... .k122 22222 22222 22333 334k. .....",       # 49
    "..... ..k12 22222 22222 33333 44k.. .....",       # 50
    "..... ...kk 22222 23332 33344 kk... .....",       # 51
    "..... ..... kk332 22333 444kk ..... .....",       # 52
    "..... ..... ..kkk kkkkk kkk.. ..... .....",       # 53  chin, a row lower
]


def puffed(*groups):
    return G.with_jaw(G.face(*groups), PUFF_ROWS)


# ------------------------------------------------------------------ small mouths
# a tight-lipped inhale through the nose: pressed lips, nostrils flared
M_PRESS = [(46, 45, 'kkkkkkk'), (47, 46, '11113'), (42, 46, '46_64')]
# "HA!": a sharp open shout, wide and short, upper teeth and tongue
M_HA = [(44, 41, 'k'), (44, 55, 'k'), (45, 41, 'kkkkkkkkkkkkkkk'), (46, 41, 'kWWWWWWWWWWWWXk'),
        (47, 41, 'kmnnmmmmmmmnnmk'), (48, 42, 'kmqrRRrrrrqmk'), (49, 43, 'kkqrrrrrqkk'),
        (50, 45, 'kkkkkkk')]
# a dark open "O" for the silent roar's gasp
M_O = [(44, 46, 'kkkkk'), (45, 45, 'kmmnmmk'), (46, 44, 'kmmmmmmmk'), (47, 44, 'kmmnnnmmk'),
       (48, 45, 'kmnqnmk'), (49, 46, 'kkkkk')]
# tight panting "haa" (spent: controlled, not wiped out)
M_HAA = [(45, 44, 'kkkkkkkkk'), (46, 44, 'kWWWWWWXk'), (47, 45, 'kmnqnmk'), (48, 46, 'kkkkk'),
         (49, 46, '11113')]
M_HAA_SHUT = [(46, 44, 'kkkkkkkkk'), (47, 45, '1111113')]
# a wobbling pout (defeat)
M_POUT = [(47, 45, 'kkk'), (46, 48, 'kk'), (47, 50, 'kk'), (48, 46, '1113')]
# tearful closed eyes with a tear welling at each outer corner
EY_TEARY = [(36, 38, 'kkkkkk'), (37, 39, 'kkkk'), (37, 37, 'A'), (38, 37, 'B'),
            (36, 53, 'kkkkkk'), (37, 54, 'kkkk'), (37, 59, 'A'), (38, 59, 'B')]
