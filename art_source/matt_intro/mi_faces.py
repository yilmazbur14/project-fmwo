"""Matt's faces for the intro, drawn pixel by pixel.

Every face is the approved idle face (art_source/matt/face.py IDLE, x 31-65 from row 29) with its
features swapped: BASE is that face with the brows, lashes, eyes and mouth taken out and the skin
shading carried through, and each expression is BASE plus patches for brows, eyes and mouth. So the
head shape, ears, nose, hairline and skin ramp are the approved ones on every frame, and only the
features act. Faces whose jaw drops (a shout) rewrite the rows from the mouth down, as the approved
roar does.

Patches are (y, x, keys) in frame coordinates at the head's rest position; in keys '_' keeps the
pixel underneath and '.' makes it transparent. Light from the upper left: the forehead and left
cheek lit, the right cheek and jaw in shade.

    python mi_faces.py        # check every map's width, render every face on the head at 8x
"""
import mi_base as B

X0 = 31                     # the maps cover x 31-65
Y0 = 29
IDLE = B.rows_of(B.rig_face.IDLE)
ROAR = B.rows_of(B.rig_face.ROAR)
W = 35


def patched(rows, edits, y0=Y0):
    """rows (35-wide, starting at y0) with (y, x, keys) spans applied; rows are added below if a
    span reaches past the end."""
    out = [list(r) for r in rows]
    for y, x, keys in edits:
        r = y - y0
        while r >= len(out):
            out.append(['.'] * W)
        c = x - X0
        for ch in keys.replace(' ', ''):
            if 0 <= c < W and ch != '_':
                out[r][c] = ch
            c += 1
    return [''.join(r) for r in out]


# ------------------------------------------------------------------ the featureless base
BASE = patched(IDLE, [
    (32, 51, '2222222'),                  # the raised right brow out
    (33, 39, '222222'), (33, 53, '222222'),
    (34, 38, '222222'),
    (35, 37, '2222222'), (35, 53, '2222222'),   # lashes out
    (36, 38, '222222'), (36, 53, '222222'),     # eyes out
    (37, 38, '222222'), (37, 53, '22222'),
    (38, 39, '2222'), (38, 53, '22222'),        # under-eye shadows out (each eye brings its own)
    (44, 55, '22'),                             # the grin out
    (45, 41, '2222222222222222'),
    (46, 42, '22222222222222'),
    (47, 43, '222222222222'),
    (48, 44, '2222222223'),
    (49, 45, '2222223'),
])


def face(*groups):
    """BASE with the given patch groups applied in order."""
    edits = []
    for g in groups:
        edits += g
    return patched(BASE, edits)



# ------------------------------------------------------------------ brows
BR_RELAX = [(32, 40, 'hhhh'), (33, 38, 'hhhhhhh'), (32, 53, 'hhhh'), (33, 52, 'hhhhhhh')]
BR_HIGH = [(31, 40, 'hhhh'), (32, 38, 'hhhhhhh'), (31, 53, 'hhhh'), (32, 52, 'hhhhhhh')]
# inner ends up, outer ends down
BR_WORRY = [(31, 42, 'hhh'), (32, 39, 'hhhhhh'), (33, 38, 'hhhh'),
            (31, 52, 'hhh'), (32, 52, 'hhhhhh'), (33, 55, 'hhhh')]
# inner ends down onto the eyes, a furrow between
BR_ANGRY = [(32, 37, 'hhh'), (33, 38, 'hhhhhh'), (34, 41, 'hhhhh'),
            (32, 57, 'hhh'), (33, 53, 'hhhhhh'), (34, 51, 'hhhhh'),
            (33, 48, '3'), (34, 48, '4')]
BR_FURY = [(31, 37, 'hh'), (32, 38, 'hhhh'), (33, 40, 'hhhhh'), (34, 42, 'hhhhh'),
           (31, 58, 'hh'), (32, 55, 'hhhh'), (33, 52, 'hhhhh'), (34, 50, 'hhhhh'),
           (32, 48, '4'), (33, 48, '5'), (34, 47, '4_4')]
# irritated: the left brow down hard, the right one hitched up and kinked
BR_TWITCH = [(32, 37, 'hhh'), (33, 38, 'hhhhhh'), (34, 41, 'hhhhh'),
             (31, 54, 'hhh'), (32, 52, 'hh'), (32, 57, 'hh'), (33, 48, '3')]

# ------------------------------------------------------------------ eyes
EY_SOFT = [(35, 38, 'kkkkkk'), (36, 38, 'kWhhXk'), (37, 39, 'kkkk'), (38, 39, '1111'),
           (35, 53, 'kkkkkk'), (36, 53, 'kWhhXk'), (37, 54, 'kkkk')]
EY_ARC = [(35, 39, 'kkkk'), (36, 38, 'k'), (36, 43, 'k'),
          (35, 54, 'kkkk'), (36, 53, 'k'), (36, 58, 'k')]
EY_SMUG = [(36, 37, 'kk'), (36, 43, 'k'), (37, 39, 'kkkk'),
           (36, 53, 'k'), (36, 58, 'kk'), (37, 54, 'kkkk')]
EY_SIDE = [(35, 37, 'kkkkkkk'), (36, 38, 'kWWhhk'), (37, 39, 'kXjk'),
           (35, 53, 'kkkkkkk'), (36, 53, 'kWWhhk'), (37, 54, 'kXjk')]
EY_ANGRY = [(35, 37, 'kkkkk'), (36, 38, 'kWhhkk'), (37, 39, 'kkk'),
            (35, 55, 'kkkkk'), (36, 53, 'kkhhWk'), (37, 55, 'kkk')]
EY_BLANK = [(35, 37, 'kkkkk'), (36, 38, 'kWWXkk'), (37, 39, 'kkk'),
            (35, 55, 'kkkkk'), (36, 53, 'kkWWXk'), (37, 55, 'kkk')]
EY_SQUEEZE = [(35, 38, 'kk'), (36, 40, 'kkk'), (37, 38, 'kk'),
              (35, 57, 'kk'), (36, 54, 'kkk'), (37, 57, 'kk')]

# ------------------------------------------------------------------ mouths (the jaw stays put)
M_SMILE = [(44, 41, 'k'), (44, 55, 'k'), (45, 42, 'kk'), (45, 53, 'kk'), (46, 44, 'kkkkkkkkk'),
           (47, 45, '1111113'), (45, 40, '3'), (45, 56, '4')]
M_SMILE_OPEN = [(44, 41, 'k'), (44, 55, 'k'), (45, 42, 'kkkkkkkkkkkkk'), (46, 42, 'kWWWWWWWWWWXk'),
                (47, 43, 'kmnqrrrqnmk'), (48, 44, 'kkkkkkkkk'), (49, 45, '1111113')]
M_GRIN_TEETH = [(44, 40, 'k'), (44, 56, 'k'), (45, 41, 'kkkkkkkkkkkkkkk'), (46, 41, 'kWWWWWWWWWWWWXk'),
                (47, 42, 'kXXXXXXXXXXxk'), (48, 43, 'kkkkkkkkkkk'), (49, 45, '1111113')]
M_LAUGH = [(44, 40, 'k'), (44, 56, 'k'), (45, 41, 'kkkkkkkkkkkkkkk'), (46, 41, 'kWWWWWWWWWWWWXk'),
           (47, 41, 'kmnnmmmmmmmnnmk'), (48, 42, 'kmqrRRrrrrqmk'), (49, 43, 'kkqrrrrrqkk'),
           (50, 45, 'kkkkkkk')]
M_SMIRK = [(43, 56, 'k'), (44, 54, 'kk'), (45, 42, 'kkkkkkkkkkkk'), (46, 44, '1111113'), (45, 41, '3')]
M_GRIN_BIG = [(44, 40, 'k'), (44, 56, 'k'), (45, 41, 'kkkkkkkkkkkkkkk'), (46, 41, 'kWWWWWWWWWWWWXk'),
              (47, 42, 'kmnqrRRrrqnmk'), (48, 43, 'kkqrrrrrqkk'), (49, 45, 'kkkkkkk')]
M_WAVY = [(46, 43, 'k'), (45, 44, 'kk'), (46, 46, 'kk'), (45, 48, 'k'), (46, 49, 'kk'), (45, 51, 'kk'),
          (46, 53, 'k'), (47, 45, '111113')]
M_SMALL_OPEN = [(45, 44, 'kkkkkkkkk'), (46, 44, 'kWWWWWWXk'), (47, 45, 'kmnqnmk'), (48, 46, 'kkkkk'),
                (49, 46, '11113')]
M_STRAINED = [(44, 41, 'k'), (45, 42, 'kkkkkkkkkkkkk'), (46, 42, 'kWWxWWxWWxWXk'),
              (47, 43, 'kkkkkkkkkkkk'), (46, 55, 'k'), (48, 45, '111113')]
M_STRAINED_OPEN = [(44, 41, 'k'), (45, 42, 'kkkkkkkkkkkkk'), (46, 42, 'kWWxWWxWWxWXk'),
                   (47, 42, 'kmmmmmmmmmmmk'), (48, 43, 'kXxXXxXXxXXk'), (49, 44, 'kkkkkkkkkk'),
                   (46, 55, 'k')]
M_SCOWL = [(45, 44, 'kkkkkkkkk'), (46, 43, 'kWWWWWWWXk'), (47, 42, 'kXXXXXXXXXXxk'),
           (48, 41, 'kkkkkkkkkkkkkkk')]
M_GRIT = [(44, 43, 'kkkkkkkkkkk'), (45, 42, 'kWWkWWkWWkWXk'), (46, 41, 'kXXXkXXkXXkXXxk'),
          (47, 40, 'kkkkkkkkkkkkkkkkk')]
M_SMALL_SMILE = [(45, 44, 'k'), (46, 45, 'kk'), (46, 49, 'kk'), (45, 48, 'k'), (45, 52, 'k'),
                 (46, 47, 'k')]
M_HAHA = [(45, 44, 'kkkkkkkkk'), (46, 44, 'kWWWWWWXk'), (47, 44, 'kmqrrrqmk'), (48, 45, 'kkkkkkk')]

# ------------------------------------------------------------------ extras
BLUSH = [(39, 38, 'q_q_q'), (40, 37, 'q_q_q'), (39, 54, 'q_q_q'), (40, 55, 'q_q_q')]

# the smirk, re-cut: a closed smile that climbs to a hooked right corner, the lower lip lit
M_SMIRK = [(45, 42, 'k'), (46, 43, 'kkkkkkkk'), (45, 51, 'kkk'), (44, 54, 'kk'), (43, 56, 'k'),
           (47, 44, '111113'), (44, 57, '3'), (46, 41, '3')]

# ------------------------------------------------------------------ jaw-drop mouths
# These replace every row from 43 down, as the approved roar does: the lip line, the upper teeth
# with fangs at the corners, the throat going to black, a lit tongue, the lower teeth, then the
# approved chin carried down.
YELL_ROWS = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    "..... k1222 32222 23332 22223 2233k .....",       # 43  creases from the nose
    "..... k1223 kkkkk kkkkk kkkkk 3233k .....",       # 44  upper lip
    "..... k122k WWWWW WWWWW WWWWX k233k .....",       # 45  upper teeth
    "..... k12kW WXnmm mmmmm mmnWW Xk23k .....",       # 46  fangs
    "..... k12kq Wnmmk kkkkk kmmnX pk23k .....",       # 47  throat
    "..... k12kq pnmmk kkkkk kmmnp pk23k .....",       # 48
    "..... k12kq pnmqr RRrrr rqmnp pk23k .....",       # 49  tongue
    "..... k12kp nqrRR rrrrr rrqnp qk23k .....",       # 50
    "..... k12kp qWrrr rrrrr rrrWq pk23k .....",       # 51  lower fangs
    "..... k122k WWkkk kkkkk kkWWX k233k .....",       # 52  tongue behind the teeth
    "..... .k12k WWWWW WWWWW WXXXX k33k. .....",       # 53  lower teeth
    "..... .k122 kkkkk kkkkk kkkkk 333k. .....",       # 54  lower lip
    "..... ..k12 22223 11113 32333 34k.. .....",       # 55  the approved chin, 6 rows down
    "..... ...kk 22222 23332 33344 kk... .....",       # 56
    "..... ..... kk332 22333 444kk ..... .....",       # 57
    "..... ..... ..kkk kkkkk kkk.. ..... .....",       # 58
]
# ENOUGH: squarer and a row deeper, both rows of teeth bared
ENOUGH_ROWS = [
    "..... k1222 32222 23332 22223 2233k .....",       # 43
    "..... k122k kkkkk kkkkk kkkkk k233k .....",       # 44  upper lip, wider
    "..... k12kW WWWWW WWWWW WWWWX Xk23k .....",       # 45  upper teeth
    "..... k12kW Xnnmm mmmmm mmnnX Xk23k .....",       # 46  fangs
    "..... k12kX nmmkk kkkkk kkmmn Xk23k .....",       # 47
    "..... k12kq nmkkk kkkkk kkkmn pk23k .....",       # 48  throat
    "..... k12kq pnmkk kkkkk kkmnp pk23k .....",       # 49
    "..... k12kq pnmqr rrrrr rqmnp pk23k .....",       # 50  tongue
    "..... k12kp nqrRR rrrrr rrqnp qk23k .....",       # 51
    "..... k12kp qrRrr rrrrr rrrqp qk23k .....",       # 52
    "..... k12kX Xkkkk kkkkk kkkkX Xk23k .....",       # 53  lower fangs, tongue's edge
    "..... k12kW WWWWW WWWWW WWWWX Xk23k .....",       # 54  lower teeth
    "..... .k12k XXXXX XXXXX XXxxx k23k. .....",       # 55
    "..... .k122 kkkkk kkkkk kkkkk 333k. .....",       # 56  lower lip
    "..... ..k12 22223 11113 32333 34k.. .....",       # 57  the approved chin, 8 rows down
    "..... ...kk 22222 23332 33344 kk... .....",       # 58
    "..... ..... kk332 22333 444kk ..... .....",       # 59
    "..... ..... ..kkk kkkkk kkk.. ..... .....",       # 60
]


def with_jaw(rows, lower, from_y=43):
    """A face's rows above from_y, then `lower` (full rows) from there down."""
    keep = B.rows_of(rows)[:from_y - Y0]
    return keep + B.rows_of(lower)


# ------------------------------------------------------------------ flush (ENOUGH)
# Red to the ears: the skin ramp swapped for the mouth ramp's pinks and the Exploud reds, darkest
# where the skin was darkest, so the face keeps its modelling and only its colour boils.
FLUSH = {'1': 'O', '2': 'r', '3': 'q', '4': 'Q', '5': 'T', '6': 'n'}


def flushed(rows, top=30, bottom=99):
    out = []
    for i, r in enumerate(B.rows_of(rows)):
        y = Y0 + i
        if top <= y <= bottom:
            r = ''.join(FLUSH.get(c, c) for c in r)
        out.append(r)
    return out


# ------------------------------------------------------------------ small parts (maps + anchors)
# A sweat drop, anime-sized: pointed top, round bottom, the Exploud lavender for water, a white
# glint on its lit left side, darkest where it turns away at the lower right.
SWEAT = [
    "...k...",
    "..kAk..",
    "..kAk..",
    ".kWABk.",
    ".kWABk.",
    "kWAABCk",
    "kAABCCk",
    "kABCCDk",
    ".kCDDk.",
    "..kkk..",
]
# The anger mark: four red arcs bulging out round a cross of whatever is under it, keylined.
VEIN = [
    "..kk.kk..",
    ".kPQkQPk.",
    "kPQk.kQPk",
    "kQk...kQk",
    ".k.....k.",
    "kQk...kQk",
    "kPQk.kQPk",
    ".kPQkQPk.",
    "..kk.kk..",
]
# Steam blowing off his head: effects, so no keyline; a white core and a grey edge that holds on
# the pale mat. Two sets, so the pair of talk frames puffs.
PUFF_A = [
    "...xxx...",
    ".xxXWXxx.",
    "xXWWWWWXx",
    "xXWWWWXXx",
    ".xXWWXXx.",
    "..xxxxx..",
]
PUFF_B = [
    "..xxx..",
    ".xXWXx.",
    "xXWWWXx",
    "xXWWXXx",
    ".xxxxx.",
]
PUFF_C = [
    ".xx.",
    "xWXx",
    "xXXx",
    ".xx.",
]

# ------------------------------------------------------------------ three-quarter head (turned screen-right)
# For the walk-in and for screaming at the doll. The head turns about 20 degrees toward screen-right:
# the silhouette stays, the features slide right, the near (screen-left) ear moves in with the side
# of the head showing behind it, the far ear drops behind the cheek to a sliver, and the jaw and
# chin swing toward the turn. Same skin ramp and light as the front face.
BASE34 = B.rows_of([
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    ".kiii iiiii kkkkk kkkkk kkkkk kkkki iiik.",       # 29  hairline
    ".kiii iiiik 11112 22222 22222 2223k iiik.",       # 30
    ".kiii iiik1 12222 22222 22222 22333 kiik.",       # 31
    ".kiii iik11 22222 22222 22222 22233 kiik.",       # 32
    ".kiii iik12 22222 22222 22222 22233 kiik.",       # 33
    ".kiii iik12 22222 22222 22222 22233 kiik.",       # 34
    ".kikk ik122 22222 22222 22222 22233 kik..",       # 35  near ear's top
    "kik32 3k122 22222 22222 12222 22333 k44k.",       # 36  near ear; far ear a sliver
    "kik34 3k122 22222 22222 12322 22333 k45k.",       # 37
    "kik34 3k122 22222 22222 12322 22333 k45k.",       # 38
    "kik35 3k122 22222 22222 12332 22333 k44k.",       # 39
    "kik33 3k122 22222 22222 11332 22333 k4k..",       # 40
    ".kkk4 4k122 22222 22223 21132 22333 kk...",       # 41  ear lobe; nose tip
    "....k kk122 22222 22224 63433 2233k .....",       # 42  the near nostril
    "..... k1222 22222 22223 33322 2233k .....",       # 43
    "..... k1222 22222 22222 22222 2333k .....",       # 44
    "..... k1222 22222 22222 22222 2333k .....",       # 45
    "..... k1222 22222 22222 22222 2333k .....",       # 46
    "..... .k122 22222 22222 22223 3333k .....",       # 47
    "..... .k122 22222 22222 22233 333k. .....",       # 48
    "..... ..k12 22222 22222 22333 334k. .....",       # 49
    "..... ...kk 12222 22222 23333 44k.. .....",       # 50
    "..... ..... .kk32 22223 33344 kk... .....",       # 51
    "..... ..... ...kk kkkkk kkkkk ..... .....",       # 52  chin, swung right
])

# features for the three-quarter head: the near (screen-left) side full width, the far side
# foreshortened, everything slid toward the turn
BR34_RELAX = [(32, 43, 'hhhh'), (33, 41, 'hhhhhhh'), (32, 56, 'hhh'), (33, 55, 'hhhhh')]
EY34_SOFT = [(35, 41, 'kkkkkk'), (36, 41, 'kWWhhk'), (37, 42, 'kkkk'), (38, 42, '1111'),
             (35, 55, 'kkkkk'), (36, 55, 'kWhhk'), (37, 56, 'kkk')]
M34_SMILE_OPEN = [(44, 44, 'k'), (44, 57, 'k'), (45, 45, 'kkkkkkkkkkkk'), (46, 45, 'kWWWWWWWWWXk'),
                  (47, 46, 'kmnqrrrqnk'), (48, 47, 'kkkkkkkk'), (49, 48, '111113')]


def face34(*groups):
    edits = []
    for g in groups:
        edits += g
    return patched(BASE34, edits)


# ------------------------------------------------------------------ the roar's brace and pulse
# Sucking in air: a small dark "o", nostrils flared, cheeks pulled in under lit cheekbones.
M_INHALE = [(44, 47, 'kkk'), (45, 46, 'kmmmk'), (46, 46, 'knmnk'), (47, 47, 'kkk'),
            (42, 46, '46_64'), (40, 38, '1'), (40, 58, '2')]
# The approved roar with its throat one row deeper: the jaw pulses on the loop's middle frame.
ROAR_DEEP = ROAR[:20] + [ROAR[19]] + ROAR[20:]

# ------------------------------------------------------------------ the doll sequence
# wide, tiny-pupilled eyes: frantic (front) and fixated on the doll (three-quarter, looking right)
EY_WIDE = [(34, 38, 'kkkkk'), (35, 37, 'kWWWWWk'), (36, 37, 'kWWhWXk'), (37, 38, 'kXXXk'), (38, 39, 'kkk'),
           (34, 54, 'kkkkk'), (35, 53, 'kWWWWWk'), (36, 53, 'kWWhWXk'), (37, 54, 'kXXXk'), (38, 55, 'kkk')]
BR34_HIGH = [(31, 43, 'hhhh'), (32, 41, 'hhhhhhh'), (31, 56, 'hhh'), (32, 55, 'hhhhh')]
BR34_ANGRY = [(32, 40, 'hhh'), (33, 41, 'hhhhhh'), (34, 44, 'hhhhh'),
              (32, 58, 'hh'), (33, 55, 'hhhh'), (34, 53, 'hhhh'), (33, 51, '3'), (34, 50, '4')]
EY34_WIDE = [(34, 41, 'kkkkk'), (35, 40, 'kWWWWWk'), (36, 40, 'kWWWhXk'), (37, 41, 'kXXXk'), (38, 42, 'kkk'),
             (34, 56, 'kkk'), (35, 55, 'kWWhk'), (36, 55, 'kWWhk'), (37, 56, 'kkk')]
EY34_ANGRY = [(35, 40, 'kkkkk'), (36, 41, 'kWhhkk'), (37, 42, 'kkk'),
              (35, 56, 'kkkk'), (36, 55, 'kkhhk'), (37, 56, 'kk')]
M34_GRIN_TEETH = [(44, 42, 'k'), (44, 58, 'k'), (45, 43, 'kkkkkkkkkkkkkkk'), (46, 43, 'kWWWWWWWWWWWWXk'),
                  (47, 44, 'kXXXXXXXXXXxk'), (48, 45, 'kkkkkkkkkkk'), (49, 47, '111113')]
# the yell turned three-quarters: the mouth slid toward the turn, its far wall on the cheek's edge
YELL34_ROWS = [
    # x: 31-35 36-40 41-45 46-50 51-55 56-60 61-65      y
    "..... k1222 32222 22223 33322 2233k .....",       # 43
    "..... k1222 23kkk kkkkk kkkkk kk33k .....",       # 44  upper lip
    "..... k1222 2kWWW WWWWW WWWWW WXk3k .....",       # 45  upper teeth
    "..... k1222 kWWXn mmmmm mmmmn nWWXk .....",       # 46  fangs
    "..... k1222 kqWnm mkkkk kkkmm nXppk .....",       # 47  throat
    "..... k1222 kqpnm mkkkk kkkmm npppk .....",       # 48
    "..... k1222 kqpnm qrRRr rrrqm npppk .....",       # 49  tongue
    "..... k1222 kpnqr RRrrr rrrrq npqqk .....",       # 50
    "..... k1222 kpqWr rrrrr rrrrr Wqppk .....",       # 51  lower fangs
    "..... k1222 2kWWk kkkkk kkkkW WXk3k .....",       # 52
    "..... .k122 2kWWW WWWWW WWWXX XXk.. .....",       # 53  lower teeth
    "..... .k122 22kkk kkkkk kkkkk kkk.. .....",       # 54  lower lip
    "..... ..k12 22222 22222 22333 334k. .....",       # 55  the three-quarter chin, 6 rows down
    "..... ...kk 12222 22222 23333 44k.. .....",       # 56
    "..... ..... .kk32 22223 33344 kk... .....",       # 57
    "..... ..... ...kk kkkkk kkkkk ..... .....",       # 58
]

# ------------------------------------------------------------------ puzzled ("You don't think it's in the top 5?")
# one brow hitched up, the other level; round innocent eyes; a small pursed "hm" / a little "huh?"
BR_PUZZLED = [(31, 40, 'hhhh'), (32, 38, 'hhhhhhh'), (33, 52, 'hhhhhhh')]
EY_ROUND = [(35, 38, 'kkkkkk'), (36, 38, 'kWhhXk'), (37, 38, 'kWhhXk'), (38, 39, 'kkkk'),
            (35, 53, 'kkkkkk'), (36, 53, 'kWhhXk'), (37, 53, 'kWhhXk'), (38, 54, 'kkkk')]
M_HMM = [(46, 46, 'kkkkk'), (45, 51, 'k'), (47, 46, '11113')]
M_HUH = [(45, 46, 'kkkk'), (46, 45, 'kmqmk'), (47, 45, 'knqnk'), (48, 46, 'kkk'), (49, 46, '1113')]

# ------------------------------------------------------------------ stowing Hong, calming down
M_HOO = [(46, 47, 'kkk'), (47, 46, 'kmmk'), (48, 47, 'kk'), (49, 46, '1113')]
M_SETTLE = [(46, 44, 'k'), (47, 45, 'kkkkkkk'), (46, 52, 'k'), (48, 46, '11113')]
# a breath of air leaving him: an effect, no keyline
BREATH = [
    "..xxx..",
    ".xXWXx.",
    "xXWWWXx",
    ".xXWXXx",
    "..xxxx.",
]

FACES = {}


def check():
    bad = []
    for n, rows in FACES.items():
        bad += B.check_map(rows, W, n)
    return bad


if __name__ == '__main__':
    FACES['BASE'] = BASE
    for line in check():
        print(line)
