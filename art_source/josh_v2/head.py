"""Idle head: row-extent mask + rule-based skin + anchored feature sprites + hair/glasses block."""
from jlib import *

# (y): (x_left_outline, x_right_outline)
HEAD_ROWS = {
    8: (22, 44), 9: (22, 44), 10: (22, 44), 11: (22, 44), 12: (22, 44),
    13: (22, 44), 14: (22, 44), 15: (22, 44), 16: (22, 44), 17: (22, 44), 18: (22, 44),
    19: (22, 44), 20: (22, 44), 21: (22, 44), 22: (22, 44),
    23: (23, 43), 24: (23, 43), 25: (24, 42), 26: (25, 41), 27: (27, 39), 28: (29, 37),
}

HAIR_BLOCK = [  # x 17..47, y 0..12 ; '.' keep
    "..............##########.......",
    "..........####JJjjjHhkJj##.....",
    ".......###JjjjjHHhhkJjhkJh#....",
    ".....##JjjjHHhkJJjjHhkJjhkjh#..",
    "....#j#######jHhk#######Jhkh#..",
    "...#j#CcBBBbb####cBBBbbb#hhk#..",
    "...#h#cBBbbbb#kk#Bbbbbbb#hkh#..",
    "...#hh#######hHhh#######hhkhh#.",
    "..#hjjHhhkHjjHhhkHjjHhhkhhkhk#.",
    "..#hHhhk.................khhk#.",
    "..#hhk...................hk#...",
    "..#hkk....................k#...",
    "...##k....................h#...",
]


def skin_at(x, y):
    lo, hi = HEAD_ROWS[y]
    if y <= 9:
        return 'd'
    if x >= hi - 1 and y <= 22:
        return 'f' if 18 <= y <= 22 else 'd'
    if x >= hi - 2 and y <= 22:
        return 'd'
    if y >= 23 and (x >= hi - 2):
        return 'd'
    if y >= 26:
        return 'd'
    if y == 10 and x <= 30:
        return 'a'
    if 15 <= y <= 17 and x <= 26:
        return 'a'
    return 's'


EAR = (19, 12, [
    ".##.",
    "#sd#",
    "#af#",
    "#sf#",
    "#df#",
    "#dd#",
    ".#d#",
    "..##",
])

BROW_EYES = {
    'A': [  # thick brows with dropping outer ends, lidded squint + glint
        (24, 10, [".hkkkkh",
                  "kkkkkkk",
                  "kh....."]),
        (36, 10, ["hkkkkh.",
                  "kkkkkkk",
                  ".....hk"]),
        (25, 13, [".####.",
                  "#ewee#",
                  ".dssd."]),
        (37, 13, [".###.",
                  "#ewe#",
                  ".dsd."]),
    ],
    'B': [  # arched brows lifted, crescent lids, iris + glint, crinkle
        (24, 10, ["..hkkkh",
                  ".kkkkkkh",
                  "kh......"]),
        (36, 10, ["hkkkh..",
                  "kkkkkkk",
                  "......k"]),
        (25, 13, ["..###.",
                  ".#ewe#",
                  "#.dd.#"]),
        (37, 13, [".###.",
                  "#ewe#",
                  "d.d.d"]),
    ],
    'C': [  # arched brows, happy crescents (^ ^)
        (24, 10, ["..hkkkh",
                  ".kkkkkkh",
                  "kh......"]),
        (36, 10, ["hkkkh..",
                  "kkkkkkk",
                  "......k"]),
        (25, 13, ["..##..",
                  ".#ee#.",
                  "#d..d#"]),
        (37, 13, [".##..",
                  "#ee#.",
                  "d..d."]),
    ],
    'CH': [  # charge: brows furrowed toward the nose, narrowed eyes looking forward (right)
        (24, 10, ["hkk.....",
                  "kkkkkh..",
                  "..hkkkkh"]),
        (36, 10, ["....kkh",
                  "..hkkkk",
                  "hkkkk.."]),
        (25, 13, [".#####",
                  "#wwee#",
                  ".####."]),
        (37, 13, ["####.",
                  "#wee#",
                  ".###."]),
    ],
    'TIRED': [  # worried brows (inner ends up), eyes squeezed shut > <
        (24, 10, [".....hkk",
                  "..hkkkkh",
                  "kkkh...."]),
        (36, 10, ["kkh....",
                  "hkkkkh.",
                  "...hkkk"]),
        (26, 13, ["##..",
                  ".###",
                  "##.."]),
        (38, 13, ["..##",
                  "###.",
                  "..##"]),
    ],
    'HURT': [  # near eye squeezed shut, far eye popped wide, brows yanked
        (24, 10, ["hkkh....",
                  ".hkkkkh.",
                  "....hkkk"]),
        (36, 9, ["..hkkkh",
                 "hkk....",
                 "......."]),
        (26, 13, ["##..",
                  ".###",
                  "##.."]),
        (37, 12, [".###.",
                  "#wew#",
                  "#www#",
                  ".###."]),
    ],
    'ROLL': [  # eyes rolled back (dazed), brows slack
        (24, 11, ["hkkkkkh."]),
        (36, 11, [".hkkkkkh"]),
        (25, 13, [".####.",
                  "#wwwW#",
                  ".####."]),
        (37, 13, [".###.",
                  "#wwW#",
                  ".###."]),
    ],
    'KO': [  # X_X
        (24, 11, ["hkkkkkh."]),
        (36, 11, [".hkkkkkh"]),
        (26, 12, ["#...#",
                  ".#.#.",
                  "..#..",
                  ".#.#.",
                  "#...#"]),
        (37, 12, ["#...#",
                  ".#.#.",
                  "..#..",
                  ".#.#.",
                  "#...#"]),
    ],
    'D': [  # brows raised with gap; big warm eyes: black lid, 2-row iris w/ glint, cheek crinkle
        (24, 10, [".hkkkkh.",
                  "kkkkkkkk",
                  "k......."]),
        (36, 10, ["hkkkkh.",
                  "kkkkkkk",
                  "......k"]),
        (25, 13, [".####.",
                  "#ewee#",
                  ".#ee#.",
                  "d....d"]),
        (37, 13, [".###.",
                  "#ewe#",
                  ".#e#.",
                  "d...d"]),
    ],
}

MOUTHS = {
    'grin': [
        (27, 20, ["###############"]),
        (26, 21, ["#wwwWwwwWwwwWwww#"]),
        (27, 22, ["#Wwwwwwwwwwwww#"]),
        (28, 23, ["#############"]),
        (33, 24, ["hkh"]), (33, 25, ["kkk"]), (33, 26, ["hkh"]), (34, 27, ["k"]),   # goatee
    ],
    'pant': [  # open panting mouth: upper teeth, dark mouth, tongue
        (28, 20, ["#############"]),
        (27, 21, ["#wwWwwwwwwwWww#"]),
        (27, 22, ["#mmmmmmmmmmmmm#"]),
        (28, 23, ["#mmmMMMMMMmm#"]),
        (29, 24, ["#mMMMMMMMm#"]),
        (31, 25, ["#######"]),
        (33, 26, ["hkh"]), (34, 27, ["k"]),   # goatee
    ],
    'pant_small': [  # exhale: mouth half-closed
        (28, 20, ["#############"]),
        (27, 21, ["#wwWwwwwwwwWww#"]),
        (28, 22, ["#mmmMMMMMmmm#"]),
        (30, 23, ["#########"]),
        (33, 24, ["hkh"]), (33, 25, ["kkk"]), (34, 26, ["k"]),   # goatee
    ],
    'ko': [  # slack open mouth, pink tongue lolling out to his left, goatee strip still visible
        (29, 20, ["###########"]),
        (28, 21, ["#mmmmmmmmmmm#"]),
        (29, 22, ["#mmmmmmrRm#"]),
        (30, 23, ["######rR#"]),
        (35, 24, ["#rR#"]),
        (35, 25, [".##."]),
        (32, 25, ["hk"]), (32, 26, ["kk"]), (33, 27, ["k"]),   # goatee, one skin row below the lip so it never reads as a drip
    ],
    'grit': [  # clenched toothy grin: upper row, bite line, lower row
        (27, 20, ["###############"]),
        (26, 21, ["#wwWwwwWwwwWwww#"]),
        (26, 22, ["#W#############W#"]),
        (27, 23, ["#wWwwwWwwwWww#"]),
        (28, 24, ["#############"]),
        (33, 25, ["hkh"]), (33, 26, ["kkk"]), (34, 27, ["k"]),   # goatee
    ],
}

FIXED = [
    (34, 14, ["a"]),                        # nose bridge light
    (33, 15, ["as.", "sad"]),                # nose
    (32, 17, ["dffd"]),                      # nostrils / under-nose shadow (y17)
    (23, 16, ["rrr"]), (40, 16, ["rr"]),     # blush
    (24, 17, ["rr"]), (40, 17, ["r"]),
    (29, 18, ["hkkkk.kkkkh"]),               # pencil mustache, philtrum gap
    (34, 18, ["d"]),
    # faint stubble: sparse dots one pixel inside the jawline
    (23, 22, ["t"]), (24, 24, ["t"]), (25, 26, ["T"]), (28, 27, ["T"]), (31, 27, ["T"]),
    (36, 27, ["T"]), (38, 26, ["T"]), (40, 25, ["T"]), (41, 23, ["T"]),
]


def build_head(c, variant='A', mouth='grin'):
    # skin mask + outline
    m = mask_empty()
    for y, (lo, hi) in HEAD_ROWS.items():
        for x in range(lo, hi + 1):
            m[y][x] = True
    paint_part(c, m, skin_at, prune=False)
    # ear
    block(c, *EAR)
    # hair + glasses
    block(c, 17, 0, HAIR_BLOCK)
    for (x, y, rows) in BROW_EYES[variant]:
        block(c, x, y, rows)
    for (x, y, rows) in FIXED:
        block(c, x, y, rows)
    for (x, y, rows) in MOUTHS[mouth]:
        block(c, x, y, rows)
    return c


if __name__ == '__main__':
    import sys
    vs = sys.argv[1:] or list(BROW_EYES)
    for v in vs:
        c = blank()
        build_head(c, v)
        save_png(c, os.path.join(OUT, 'head_%s.png' % v))
    print('ok')
