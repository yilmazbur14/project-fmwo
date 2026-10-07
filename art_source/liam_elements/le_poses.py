"""Liam's elements-phase key poses, one 96x96 frame each, built on his approved liam_v2 layers.

His body is the approved 64x64 figure at 1:1 (never rescaled). BODY is the ONE constant that places it
in the frame; the final contract (PLAN.md section 8) pins it at (16, 32): feet on texel row 95, anchor
point (48, 96). Every pose keeps its art inside body rows -26..63, so BODY can move without clipping.

Pillar-top poses also honour the in-game box while he stands on the pillar (feet at screen (960, 198)):
  * nothing above frame row 30 (that is screen y 0; his hair tops out at row 33),
  * nothing outside frame x 12..83 on the rope rows (the top rope's doorway is x 852..1068).
"""
import math

import numpy as np

import le_rig as R
import le_staff as S

FW = FH = 96
BODY = (16, 32)                       # where the approved 64x64 figure sits in the frame (PLAN 8, pinned)
FEET = (BODY[0] + 32, BODY[1] + 64)   # (48, 96): the anchor POINT, the cell's bottom-centre edge
# on the pillar his feet are at screen y 198, so screen y 0 is 66 texels above them: frame row 30.
# The rope doorway (x 852..1068) is 72 texels: frame x 12..83.
PERCH_BOX = dict(top=FEET[1] - 66, left=12, right=83)

B64 = R.load_v2_layers()


def P(x, y):
    """body (64-space) coords -> frame coords"""
    return (x + BODY[0], y + BODY[1])


def layer():
    return R.blank(FW, FH)


def place(L64, dx=0, dy=0):
    return R.pad(L64, FW, FH, BODY[0] + dx, BODY[1] + dy)


def body(name, dx=0, dy=0):
    return place(B64[name], dx, dy)


def arm(delt, up, fore, cuff=(0.4, 2.3), draw_up=True, dx=0, dy=0):
    """liam_v2 arm_pose with body-space numbers, drawn into the frame."""
    ox, oy = BODY[0] + dx, BODY[1] + dy
    d = (delt[0] + ox, delt[1] + oy, delt[2])
    u = (up[0] + ox, up[1] + oy, up[2] + ox, up[3] + oy, up[4], up[5])
    f = (fore[0] + ox, fore[1] + oy, fore[2] + ox, fore[3] + oy, fore[4], fore[5])
    return R.arm_pose(FW, FH, d, u, f, cuff=cuff, draw_up=draw_up)


def blkb(L, x, y, rows, dx=0, dy=0):
    """blk at body coords."""
    return R.blk(L, x + BODY[0] + dx, y + BODY[1] + dy, rows)


def staff_line(butt_b, head_b, orb='neutral', **kw):
    """Staff from a butt point to a head centre, both in body coords (floats)."""
    b = (butt_b[0] + BODY[0], butt_b[1] + BODY[1])
    h = (head_b[0] + BODY[0], head_b[1] + BODY[1])
    return S.staff(FW, FH, b, h, orb=orb, **kw)


# ------------------------------------------------------------------ legs
def _rows_to_layer(spec):
    L = R.blank(64, 64)
    for y, segs in spec.items():
        for x, s in segs:
            for i, ch in enumerate(s):
                if ch != ' ':
                    L[y, x + i] = ch
    return L


def legs_narrow():
    """His approved legs and shoes brought under the hips so the stance is 41 texels (x 11..51) and fits
    the pillar top. Built from the approved rows: trouser texture kept, each shoe shortened by dropping
    5 columns of its flat middle (toe curve, heel and sole untouched)."""
    spec = {
        46: [(15, '#' * 33)],
        47: [(15, '#pppppqqqqqqqqQQQqqqqqqqqqqqQQQz#')],
        48: [(15, '#pppppqqqqqqqqQQQQqqqqqqqqqqQQQz#')],
        49: [(15, '#pppppqqqqqqqqQQzzzQQqqqqqqqQQQz#')],
        50: [(15, '#pppppqqqqqqqQQzzZzQQqqqqqqqQQQz#')],
        51: [(15, '#pppppqqqqqqQQzz#zQqqpqqqqqqQQQz#')],
        52: [(15, '#pppppqqqqqqQQQz#QqqqpqqqqqqQQQz#')],
        53: [(15, '#pppppqqqqqqQQQz#qqqpqqqqqqqQQQz#')],
        54: [(16, '#ppppqqqqqqQQQz#qqpqqqqqqqQQQz#')],
        55: [(16, '#ppppqqqqqqQQzz#qpqqqqqqqqQQQz#')],
        56: [(16, '#pppqqqqqqqQQQz#qpqqqqqqqqQQQz#')],
        57: [(15, '#' * 33)],
        58: [(14, '#oooOOOOOOxxxxxxx#OOOOOOOOOoooooo##')],
        59: [(12, '##ooooOOOOOxxxxxxxx#OOOOOOOOooooooOOO##')],
        60: [(11, '#ooooOOOOOOxxxxxxxxx#OOOOOOOOOoooOOOOOO#')],
        61: [(11, '#oooOOOOOOOxxxxxxxxx#OOOOOOOOOOOOOOxxxxx#')],
        62: [(11, '#' + 'x' * 19 + '#' + 'x' * 19 + '#')],
        63: [(12, '#' * 19 + ' ' + '#' * 19)],
    }
    return _rows_to_layer(spec)


def legs_lift_near(up=5, out=2):
    """legs_narrow with the near foot lifted off the pillar (knee toward the camera): the near shoe is
    moved up `up` and out `out`, the near trouser leg ends at the new hem."""
    L = legs_narrow()
    shoe = L[57:64, 31:52].copy()
    shoe[:, 0] = np.where(shoe[:, 0] == '#', '#', shoe[:, 0])
    L[57 - up:64, 32:56] = '.'
    L[57 - up:64, 31] = np.where(np.arange(57 - up, 64) < 57, L[57 - up:64, 31], '.')
    # near trouser leg ends one row above the shoe's top outline
    R.composite(L, shoe, 31 + out, 57 - up)
    # re-close the far shoe's heel line (it shared column 31 with the near shoe)
    for y in range(57, 63):
        L[y, 31] = '#'
    L[63, 31] = '.'
    # the lifted heel meets the far leg's inner line, so the slit between them is keyline too
    for y in range(57 - up, 57 - up + 6):
        if L[y, 32] == '.':
            L[y, 32] = '#'
    return L


# ------------------------------------------------------------------ faces (64-space, head at dy=0)
SMIRK = [  # x 16..39, y 20..24 (liam_v2 anim.SMIRK)
    "#hhHhhHHhkhHHhhk##hHhhh#",
    "#hHhhHhkhH#WWWWWW#hhHhh#",
    "#hhHhhkhHhh#WWWw#hHhhH#.",
    ".#hhHhHhhkhH####hHhhHh#.",
    ".#hHhhkhHhhHhhkhhhHhh#..",
]
GRIN_BIG = [  # x 16..39, y 19..25 (liam_v2 anim.GRIN_BIG_ROWS)
    "..................##....",
    "#hhHhhHHhkhHHhhkhH#hHhh#",
    "#hH#WWWWWWWWWWWWWWW#hHh#",
    "#hhh#WWwWWwWWwWWwW#hHh#.",
    ".#hHh#############hHhh#.",
    ".#hHhh#WWwWWwWWW#hHhh#..",
    ".#hhHrH#########khHh#...",
]
LENS_FAR = [(x, y) for y in (14, 15, 16) for x in range(19, 24)]
LENS_NEAR = [(x, y) for y in (14, 15, 16) for x in range(27, 34)]


def lenses(H, kind):
    if kind == 'dim':
        for (x, y) in LENS_FAR + LENS_NEAR:
            H[y, x] = 'l'
        for (x, y) in [(20, 16), (21, 15), (22, 14), (29, 16), (30, 15), (31, 14), (32, 16), (33, 15)]:
            H[y, x] = 'W'
    elif kind == 'flash':
        for (x, y) in LENS_FAR + LENS_NEAR:
            H[y, x] = 'W'
    elif kind == 'swirl':
        for (x, y) in LENS_FAR + LENS_NEAR:
            H[y, x] = 'W'
        for (x, y) in [(20, 14), (21, 14), (22, 15), (21, 16), (20, 16), (19, 15),
                       (29, 14), (30, 14), (31, 14), (32, 15), (31, 16), (30, 16), (29, 16), (28, 15)]:
            H[y, x] = 'b'
        H[15, 21] = '5'
        H[15, 30] = '5'
    return H


# new mouths for this phase (x 16.., y from the key); interior = his own dark jacket tones N/n so the
# colour count stays his (no new reds): N 45283c inside, n 663931 tongue.
MOUTHS = {
    # fierce shout: upper teeth, dark mouth, tongue, lower teeth
    'shout': (16, 20, [
        "#hhHhhHHhkhHHhhkhH#hHhh#",
        "#hH#WWWWWWWWWWWWWW#hHhh#",
        "#hh#NNNNNNNNNNNNNN#hHh#.",
        ".#h#NNnnnnnnnnNNN#hHhh#.",
        ".#hh#WWwWWwWWwWW#hHhh#..",
        ".#hhH###########hkhHh#..",
    ]),
    # laugh, head thrown back: huge open mouth, top teeth only, tongue
    'laugh': (16, 20, [
        "#hhHhhHHhkhHHhhkhH#hHhh#",
        "#h#WWWWWWWWWWWWWWWW#hHh#",
        "#h#NNNNNNNNNNNNNNNN#hH#.",
        ".#h#NNNNNNNNNNNNNN#hHh#.",
        ".#hh#NNnnnnnnnnNN#hHhh#.",
        ".#hhH#nnnnnnnnnn#hkhH#..",
        "..#hhH##########khHh#...",
    ]),
    # panic gasp: a tall round O
    'gasp': (16, 20, [
        "#hhHhhHHhkhHHhhk##hHhhh#",
        "#hHhhHh######hhHhhhHhh#.",
        "#hhHhh#NNNNNN#hHhhHhhH#.",
        ".#hhHh#NNnnNN#hHhhHhh#..",
        ".#hHhh#NnnnnN#hhHhhHh#..",
        ".#hhHhh######hhHhhhh#...",
    ]),
    # blowing cold air: pursed little o, cheeks puffed (beard bulges one px each side)
    'blow': (15, 19, [
        "..#hHhs#sdfdssdhHhhHhhhh#",
        ".#hhHhhHHhkhHHhhHhhHhhh#.",
        "#hHhhHhhHhh###hhHhhHhhhh#",
        "#hhHhhHhhh#NNN#hHhhHhhh#.",
        "#hHhhHhhhh#NnN#hhHhhHhh#.",
        ".#hhHhhHhhh###hHhhHhhh#..",
        ".#hhHrHhHhhHhhHhkhHhh#...",
    ]),
    # dazed: slack open mouth, tongue lolling out over the beard
    'dazed': (16, 20, [
        "#hhHhhHHhkhHHhhk##hHhhh#",
        "#hHhhH#WWWWWWW#hhHhhHh#.",
        "#hhHh#NNNNNNNNN#hHhhH#..",
        ".#hhHh#NNnnnNN#hHhhHh#..",
        ".#hHhhh##iii##hhHhhh#...",
        ".#hhHrHh#iij#HhkhHh#....",
        "..#hhHhH#jij#hHhhk#.....",
        "...#hHhh.###hhkhkk#.....",
    ]),
}


def head_variant(mouth=None, lens=None, extra=None):
    H = B64['head'].copy()
    if lens:
        lenses(H, lens)
    if mouth == 'smirk':
        R.blk(H, 16, 20, SMIRK)
    elif mouth == 'big':
        R.blk(H, 16, 19, GRIN_BIG)
    elif isinstance(mouth, tuple):
        R.blk(H, mouth[0], mouth[1], mouth[2])
    elif mouth in MOUTHS:
        x0, y0, rows = MOUTHS[mouth]
        R.blk(H, x0, y0, rows)
    if extra:
        extra(H)
    return H


# ------------------------------------------------------------------ hands (drawn over a 5-px shaft)
FIST = [  # a fist wrapped round a shaft, knuckles to the viewer (9 x 8); centre (4, 3.5)
    ".#######.",
    "#aassssd#",
    "#assssdd#",
    "#sfsfsfd#",
    "#ssssddf#",
    "#dsdsdff#",
    ".#ddfff#.",
    "..#####..",
]


def fist_at(L, cx, cy, rows=None):
    """Paste a fist block centred on frame point (cx, cy)."""
    rows = rows or FIST
    R.blk(L, int(round(cx - len(rows[0]) / 2)), int(round(cy - len(rows) / 2)), rows)
    return L
