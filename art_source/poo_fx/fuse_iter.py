import fxpng
from bomb_final import *

SP_BIG_A = [
    "....Y....",
    "....Y....",
    ".O..Y..O.",
    "...YWY...",
    "YYYWWWYYY",
    "...YWY...",
    ".O..Y..O.",
    "....Y....",
    "....O....",
]
SP_BIG_B = [
    "...O...",
    ".O.Y.O.",
    "..YWY..",
    "OYWWWYO",
    "..YWY..",
    ".O.Y.O.",
    "...O...",
]
SP_BIG_C = [
    "....O....",
    ".R..Y..R.",
    "..O.Y.O..",
    "...YWY...",
    "OYYWWWYYO",
    "...YWY...",
    "..O.Y.O..",
    ".R..Y..R.",
    "....O....",
]
SP_SMALL_A = [
    "Y...Y",
    ".OWO.",
    ".WWW.",
    ".OWO.",
    "Y...Y",
]
SP_SMALL_B = [
    "..O..",
    ".YWY.",
    "OWWWO",
    ".YWY.",
    "..O..",
]
SP_SMALL_C = [
    "O.....O",
    ".Y...Y.",
    "..YWY..",
    "..WWW..",
    "..YWY..",
    ".Y...Y.",
    "O.....O",
]

def tip0(f):
    stamp(f, 7, [(17, ".KK."), (16, "KdcK."), (16, "KedcK"), (16, "KedcbK"), (15, "KeddcbK"),
                 (12, "KKKeeddcbK"), (11, "KeedKdddcbbKK")])

def variant(cord, sp, sc, erase_top=True):
    f = grid_of(PILE[0])
    tip0(f)
    fuse(f, cord)
    spark(f, sc[0], sc[1], sp, protect={(x, y) for x, y, _ in cord if _ != 'i'})
    return f

cordA = [(19, 6, 'g'), (20, 6, 'h'), (20, 5, 'g'), (21, 5, 'h'), (21, 4, 'i')]
# B: rises then hooks right
cordB = [(18, 6, 'g'), (19, 6, 'h'), (19, 5, 'g'), (20, 5, 'h'), (20, 4, 'g'), (21, 4, 'g'), (21, 5, 'h'), (22, 4, 'h'), (22, 3, 'i')]
# C: curls right, long, spark at upper right
cordC = [(18, 6, 'g'), (19, 6, 'h'), (19, 5, 'g'), (20, 5, 'g'), (20, 6, 'h'), (21, 5, 'h'), (21, 4, 'g'), (22, 4, 'h'), (22, 3, 'i')]
vars_ = [
    variant(cordA, SPARK_BIG, (22, 3)),
    variant(cordB, SP_BIG_B, (23, 3)),
    variant(cordC, SP_BIG_C, (23, 4)),
    variant(cordC, SP_BIG_A, (23, 4)),
]
smalls = []
for sp in (SP_SMALL_A, SP_SMALL_B, SP_SMALL_C):
    f = grid_of(PILE[0]); tip0(f); fuse(f, cordC)
    spark(f, 23, 3 if len(sp) == 5 else 3, sp, protect={(x, y) for x, y, _ in cordC if _ != 'i'})
    smalls.append(f)
allf = vars_ + smalls
px = to_px(allf)
n = len(allf)
fxpng.write_png('fuse_iter.png', 32 * n, 32, px)
rows = []
for y in range(0, 16):
    r = []
    for i in range(n):
        r += px[y][32 * i + 12:32 * i + 30] + [(255, 0, 255, 255)]
    rows.append(r)
a, b, o = fxpng.view(len(rows[0]), 16, rows, 9)
fxpng.write_png('fuse_iter_top9x.png', a, b, o)
a, b, o = fxpng.view(32 * n, 32, px, 3, bg=FLOOR)
fxpng.write_png('fuse_iter_3x.png', a, b, o)
for f in allf:
    for y in range(0, 10):
        print(''.join(f[y][12:30]))
    print()
