"""Matt's faces for the Glass Row and the Deafening Yell, built like the intro's (mi_faces): the
approved faces with their features swapped, whole rows where the head's shape changes.
"""
import mg_base  # noqa: F401
from mg_base import B, G

ROAR = G.ROAR           # the approved roar face, rows 29-63


def row(y):
    return ROAR[y - 29]


# ------------------------------------------------------------------ the head tipped back (yell up)
# Tipped back about 50 degrees. Worked through as a turn about the neck: the face from brow to chin
# squeezes into about half its height, the ears end up level with the mouth, and the underside of the
# jaw swings into view below the chin as a shaded area as tall as the mouth. So: a one-row forehead,
# the brows knit up with the strain, the eyes squeezed shut, the approved roar's cheeks and flared
# nostrils, then the roar's own mouth with its throat thinned (four of its rows go), then the jaw's
# underside in its own shade narrowing into the neck. Built from the roar's rows so it stays his face.
def patch_row(y, edits):
    return G.patched([row(y)], [(29, x, keys) for (x, keys) in edits], y0=29)[0]


FOREHEAD = row(30)
BROWS_KNIT = B.rows_of([".kiiiik11hhhh22234 3222hhhh23kiiiik."])[0].replace(' ', '')
EYES_SHUT = "".join([".kkik12kkkkkk22222", "222kkkkkkk33kikk."])
UNDER_EYES = patch_row(37, [(40, '2222'), (53, '2222')])
TIPPED_UPPER = [row(29), FOREHEAD, BROWS_KNIT, EYES_SHUT, UNDER_EYES, row(38), row(41), row(42)]
MOUTH_ROWS = [row(y) for y in (43, 44, 45, 46, 49, 50, 53, 54, 55, 56, 57, 58)]
UNDERSIDE = B.rows_of([
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65
    "..... k3333 33333 33333 33334 4444k .....",     # the jaw's underside, in its own shade
    "..... .k344 44444 44444 44444 445k. .....",
    "..... ..kk4 44444 45554 44444 4kk.. .....",     # the throat's crease
    "..... ....k k4444 44444 4444k k.... .....",     # the neck
    "..... ..... .k444 44444 4445k ..... .....",
    "..... ..... .k444 44444 4455k ..... .....",
])
YELL_UP = TIPPED_UPPER + MOUTH_ROWS + UNDERSIDE

# the tell: the same tipped head drawing in a huge breath: mouth shut tight, cheeks full
TIP_BACK = TIPPED_UPPER + B.rows_of([
    "....k 12234 3kkkk kkkkk kkkk4 43233 k....",     # lips pressed, centred on column 48
    "...k1 22322 22222 11111 22223 33334 4k...",     # the lower lip's light, centred
    "...k1 22222 22222 22222 22223 33334 4k...",
    "....k 12222 22222 22222 22333 34444 k....",
]) + UNDERSIDE

# looking up at the ceiling: the talk sheet's round eyes with the pupils rolled up under the lid
EY_UP = [(35, 38, 'kkkkkk'), (36, 38, 'kWhhXk'), (37, 38, 'kWWWXk'), (38, 39, 'kkkk'),
         (35, 53, 'kkkkkk'), (36, 53, 'kWhhXk'), (37, 53, 'kWWWXk'), (38, 54, 'kkkk')]

if __name__ == '__main__':
    for n, rows in (('YELL_UP', YELL_UP), ('TIP_BACK', TIP_BACK)):
        print(n, len(rows), B.check_map(rows, 35, n))
