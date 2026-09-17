"""Hand-placed facial feature stamps for beast Bixby.
Middle head local coords: lx = col - (ox - 30), ly = row - oy   (symmetry: lx <-> 59 - lx)
Side head local coords:   lx = col - ox (facing left) or col = ox + 41 - lx (facing right), ly = row - oy
'.' keeps the underlying pixel."""
from pal import PALC


def put_grid(cv, grid, lx0, ly0, tx):
    """tx(lx, ly) -> (col, row)"""
    rows = grid.strip('\n').split('\n')
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            c, r = tx(lx0 + dx, ly0 + dy)
            if ch == '_':
                cv.put(c, r, None)
            else:
                cv.put(c, r, PALC[ch])


def mid_tx(ox, oy, mirror=False):
    base = int(round(ox - 30))
    if mirror:
        return lambda lx, ly: (base + 59 - lx, oy + ly)
    return lambda lx, ly: (base + lx, oy + ly)


def side_tx(ox, oy, side):
    if side > 0:
        return lambda lx, ly: (ox + lx, oy + ly)
    return lambda lx, ly: (ox + 41 - lx, oy + ly)


# ------------------------------------------------------------------ middle head
MID_EYE_L = """
kkk.........
45kkkk......
.4555kkk....
.kkk4557kk..
.kLOkk4557k.
.kOLLOkk45k.
.4koOLOokkk.
..4kFooFk...
...4kkkk....
"""
# '7' is not a palette char here -> replace below
MID_EYE_L = MID_EYE_L.replace('7', '5')

MID_NOSE = """
..kkkkkkkkkk..
.kkNNNkkkkkkk.
kkNGGNkkkkkkkk
kkNNNkkkkkkkkk
kkkkkkkkkkkkkk
.kDDkkkkkkDDk.
..kkkkkkkkkk..
......kk......
......kk......
"""

MID_WRINKLES_L = """
u...
.v..
..u.
v..u
.u..
"""

# left half of the mouth block, lx 16..29, ly 36..56 (mirrored to lx 30..43)
MID_MOUTH_HALF = """
k3vvvvvvvvvvvv
k4vvvvvuuuuuuu
k4uuuuuuuuuuku
kktuuuuuuuuukk
.kkkkkkkkkkkkk
.kDknnnnnnnnnn
.kDkWWknnkWkWk
.kkMWWkMMkvkvk
..kMWwkTTTkTkT
..kMwvkTTFFFoo
..kMkvkTFooOOO
..kMMkTFoOOLLL
..kMMTFoOOLLWW
..kMkTFooOOLLL
...kvkFFooOOOO
...kwknFFFoooo
...kWknmmnFFFF
....kwknmmnnnn
....kvukkkkkkk
.....kuuuutttt
......kkkkkkkk
"""


def sym_half(half):
    rows = half.strip(chr(10)).split(chr(10))
    return chr(10).join(r + r[::-1] for r in rows)


def drop_rows(grid, after, extra_rows):
    rows = grid.strip(chr(10)).split(chr(10))
    return chr(10).join(rows[:after] + extra_rows + rows[after:])


MID_FIRE_ROW = "..kMMTFoOLLWWW"


def middle_face(cv, ox, oy, jaw_drop=0):
    L = mid_tx(ox, oy)
    R = mid_tx(ox, oy, mirror=True)
    put_grid(cv, MID_EYE_L, 16, 17, L)
    put_grid(cv, MID_EYE_L, 16, 17, R)
    put_grid(cv, MID_NOSE, 23, 25, L)
    half = MID_MOUTH_HALF
    if jaw_drop:
        half = drop_rows(half, 12, [MID_FIRE_ROW] * jaw_drop)
    put_grid(cv, sym_half(half), 16, 36, L)


# ------------------------------------------------------------------ side head (authored facing left)
SIDE_EYE_FAR = """
kk.....
3kkk...
3kLOkk.
.kOOokk
.3kFoFk
..3kkk.
"""

SIDE_EYE_NEAR = """
.......kk
....kkkk4
..kkk4454
kkkOLLkk4
kkOLLOok4
.kFoOOok.
..kkFFk..
....kk...
"""

SIDE_NOSE = """
..kkkkk.
.kkNNNkk
kkNGGNkk
kkkNNkkk
kDkkkkkk
kDDkkkk.
.kkkkk..
"""

SIDE_MOUTH = """
kkkkkkkkkkkkkkkkkkkkkk.
kWWknnnnnnnWWknnnnnkkk.
kWWkMkWkWkMWWkMMTTMMkk.
.kWMTTTFFFTkvkTTTTTMMk.
.kvMTFoOLOoFkTTTTTTMk..
..kMFoOLLOoFFTTTTMMk...
..kkMFoOOoFnnkkkkkk....
...kWknFFnmmnkvW.......
...kvWkknnnnkkWk.......
"""

SIDE_WRINKLE = """
..u..
.v.u.
u...v
"""


SIDE_FIRE_ROW = "..kMFoOLWLOoFFTTTTMMk.."


def side_face(cv, ox, oy, side, jaw_drop=0):
    T = side_tx(ox, oy, side)
    put_grid(cv, SIDE_EYE_FAR, 13, 9, T)
    put_grid(cv, SIDE_EYE_NEAR, 25, 7, T)
    put_grid(cv, SIDE_NOSE, 0, 17, T)
    m = SIDE_MOUTH
    if jaw_drop:
        m = drop_rows(m, 5, [SIDE_FIRE_ROW] * jaw_drop)
    put_grid(cv, m, 3, 26, T)
