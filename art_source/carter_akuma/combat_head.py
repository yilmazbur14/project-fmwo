"""Carter's head, re-rendered at an offset with a choice of expression.

render.head + render.faces_on draw the approved head at fixed coordinates.  The
combat set needs the same head lifted, dropped, hung and lit differently, so
this rebuilds it from the same masks with (dx, dy) applied to every mask, every
shading model and every detail line.  The face stamps are the approved ones plus
four new ones: the glare, the white-hot flash, the strain of the punish window
and the beaten stare.
"""
import math
from lib import (W, H, Canvas, union, inter, sub, mirror, empty, grow, erode,
                 poly, ell, PALC, BLACK, TH_HARD, TH_HARD2, bayer)
import parts as P
import face as F
from render import cylm, sphm
import combat_lib as CL
from combat_lib import shift_mask

# ---------------------------------------------------------------- new stamps

# Harder than the approved chevron: the inner ends drive down toward the nose
# and a furrow opens between them.  Anchored at x=36, y=23 like F.BROWS.
BROWS_GLARE = """
5555................5555
6555555..........5555556
.66555555......55555566.
..2665555......5555662..
"""

# The flash keeps the glare - a brow that lifts reads as surprise, and he is
# the one doing this to you.  Three rows only, so the taller slit has room.
# Anchored x=36, y=23.
BROWS_FLASH = """
5555................5555
6555555..........5555556
.66555555......55555566.
"""

# y=26.  Level 1: the slit doubles and loses its dark rim.
EYES_LIT = """
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.kOOOOOOk......kOOOOOOk.
.kVVVVVVk......kVVVVVVk.
..k7777k........k7777k..
...vvvv..........vvvv...
"""

# y=25.  Level 2: a white core opens inside the glow and the lid peels back.
EYES_HOT = """
.kkkkkkkk......kkkkkkkk.
.kOOOOOOk......kOOOOOOk.
kOMMMMMMOk....kOMMMMMMOk
.kMMMMMMk......kMMMMMMk.
.kOOOOOOk......kOOOOOOk.
..kVVVVk........kVVVVk..
...7777..........7777...
"""

# y=26.  Level 3: burnt out.  Deliberately the SAME width as the approved slit
# - widening it merged the two sockets into one white bar across the bridge of
# the nose and the face stopped being a face.  It grows downward instead, and
# the drama comes from the lances, the socket halo and the light on his body.
EYES_FLASH = """
.kkkkkkkk......kkkkkkkk.
.kOMMMMOk......kOMMMMOk.
.kMMMMMMk......kMMMMMMk.
.kMMMMMMk......kMMMMMMk.
.kOOOOOOk......kOOOOOOk.
..kVVVVk........kVVVVk..
...7777..........7777...
"""

# y=26.  Punish window: the glow has almost gone out and the lid sags shut.
EYES_SPENT = """
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.k988889k......k988889k.
..kwwwwk........kwwwwk..
...vvvv..........vvvv...
"""

# y=26.  Beaten: no light left in them at all.
EYES_OUT = """
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.kkkkkkkk......kkkkkkkk.
.kk9999kk......kk9999kk.
..kwwwwk........kwwwwk..
...vvvv..........vvvv...
"""

# y=34, x=44.  The deadpan finally breaks: the jaw drops open.
MOUTH_SNARL = """
.555555.
kkkkkkkk
k4kkkk4k
k4NNNN4k
kk4444kk
.566665.
"""

# y=35, x=44.  Punish window: dragging air in through a clenched jaw.
MOUTH_GASP = """
.555555.
kkkkkkkk
k4NNNN4k
kk4444kk
.k5665k.
"""

# y=36, x=45.  Beaten: slack.
MOUTH_SLACK = """
.5555.
kkkkkk
k4NN4k
.5665.
"""


# ---------------------------------------------------------------- helpers

def _seg(cv, pts, ch, dx=0, dy=0, mirror_too=True, over_only=True):
    col = PALC[ch]
    runs = [pts]
    if mirror_too:
        runs.append([(95 - x, y) for x, y in pts])
    for run in runs:
        for i in range(len(run) - 1):
            x0, y0 = run[i][0] + dx, run[i][1] + dy
            x1, y1 = run[i + 1][0] + dx, run[i + 1][1] + dy
            n = max(abs(x1 - x0), abs(y1 - y0))
            for s in range(n + 1):
                t = s / max(1, n)
                x = int(round(x0 + (x1 - x0) * t))
                y = int(round(y0 + (y1 - y0) * t))
                if not (0 <= x < W and 0 <= y < H):
                    continue
                if over_only and (cv.px[y][x] is None or cv.px[y][x] == BLACK):
                    continue
                cv.px[y][x] = col


def neck(dy=0, lean=0.0):
    """A neck that behaves in both directions.

    Lifting the head has to STRETCH the throat - the top rises with the skull
    and the base stays on the shoulders - but dropping it must not, or the
    polygon inverts and a slab of skin is painted across the chest.  A hung
    head sinks instead: the whole neck travels down with it and the jaw covers
    what is left."""
    down = max(0.0, float(dy))
    top = 35.0 + dy
    bot = 46.0 + down
    mid = 38.6 + dy * (0.5 if dy < 0 else 1.0)
    return poly(P.mir_pts([
        (47.5 + lean, top), (43.2 + lean, top + 0.4), (41.6 + lean * 0.6, mid),
        (41.2, 44.0 + down), (47.5, bot),
    ]))


def head_masks(dx=0, dy=0):
    hd = shift_mask(P.head(), dx, dy)
    er = shift_mask(P.ears(), dx, dy)
    bd = shift_mask(P.beard(), dx, dy)
    return hd, er, bd


# ---------------------------------------------------------------- render

def draw_head(cv, dx=0, dy=0, expr='deadpan', eye=0, drop=0, lean=0.0,
              shade=0, bloom=0.0):
    """expr: deadpan | glare | flash | strain | beaten
    eye: 0 approved, 1 lit, 2 hot, 3 burnt out, -1 dim, -2 dead
    drop: extra rows the FACE sits down the skull - a positive value reads as
          the chin coming up, because the features slide toward the jaw.
    shade: ramp bias for the whole head (1 = head hanging in its own shadow)."""
    hd, er, bd = head_masks(dx, dy)
    nk = neck(dy, lean)

    cv.part(nk, 'skin', cylm((41.0 + dx, 40.0 + dy), (54.0 + dx, 40.0 + dy), 7.4),
            TH_HARD, bias=shade)
    cv.part(er, 'skin', ('dist', 3.4), TH_HARD, bias=shade)
    cv.part(hd, 'skin', sphm(45.0 + dx, 25.0 + dy, 17.4, 17.6, 0.30), TH_HARD,
            bias=shade)

    # bald-dome specular and the rim down the far side
    _seg(cv, [(38, 20), (38, 17), (40, 14), (44, 13), (49, 13)], 's', dx, dy, False)
    _seg(cv, [(39, 20), (39, 17), (41, 15), (44, 14), (49, 14)], 's', dx, dy, False)
    _seg(cv, [(58, 16), (60, 20), (60, 25), (59, 29)], 'v', dx, dy, False)
    _seg(cv, [(57, 17), (59, 21), (59, 26)], 'u', dx, dy, False)
    _seg(cv, [(58, 32), (56, 36), (52, 39)], 'v', dx, dy, False)
    _seg(cv, [(35, 20), (34, 24)], 'v', dx, dy)

    cv.part(bd, 'hair', ('dist', 4.4), TH_HARD, bias=shade)
    _seg(cv, [(38, 33), (37, 37)], '4', dx, dy)
    _seg(cv, [(41, 40), (40, 43)], '4', dx, dy)
    _seg(cv, [(44, 41), (44, 44)], '2', dx, dy, False)
    _seg(cv, [(36, 29), (36, 33)], '1', dx, dy)
    _seg(cv, [(43, 43), (47, 44)], '1', dx, dy)
    _seg(cv, [(41, 45), (47, 46)], '6', dx, dy)
    _seg(cv, [(34, 25), (33, 28), (34, 30)], 'w', dx, dy)
    _seg(cv, [(35, 26), (34, 29)], 'v', dx, dy)

    faces_on(cv, dx, dy + drop, expr, eye)
    if bloom > 0.02:
        socket_glow(cv, dx, dy + drop, bloom)
    return hd, er, bd, nk


SKIN_SET = None


def socket_glow(cv, dx, dy, level):
    """Light spilling out of the two sockets onto the skin around them.

    One wide bloom centred between the eyes turned the whole skull and the
    beard into pale mud, so this is two tight halos instead, and it only
    touches skin - the beard, the brows and the black lids keep their colour
    so the face stays a face while it burns."""
    global SKIN_SET
    if SKIN_SET is None:
        from lib import hexc, RAMPS
        SKIN_SET = set(hexc(c) for c in RAMPS['skin'] + RAMPS['skinr'])
    r = 5.0 + 3.0 * level
    for cx, cy in ((40.5 + dx, 28.5 + dy), (54.5 + dx, 28.5 + dy)):
        for y in range(max(0, int(cy - r - 1)), min(H, int(cy + r + 2))):
            for x in range(max(0, int(cx - r - 1)), min(W, int(cx + r + 2))):
                c = cv.px[y][x]
                if c not in SKIN_SET:
                    continue
                f = max(0.0, 1.0 - math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r)
                a = (f ** 1.25) * level
                if a < 0.16:
                    continue
                cv.px[y][x] = CL.mixc(c, PALC['M'] if a > 0.62 else PALC['O'],
                                      min(0.9, a))


def faces_on(cv, dx=0, dy=0, expr='deadpan', eye=0):
    brow = {'glare': (BROWS_GLARE, 23), 'flash': (BROWS_FLASH, 21),
            'strain': (BROWS_GLARE, 23), 'beaten': (F.BROWS, 24)}.get(
                expr, (F.BROWS, 23))
    cv.stamp(brow[0], 36 + dx, brow[1] + dy, over_only=True)

    eyes = {0: (F.EYES, 26), 1: (EYES_LIT, 26), 2: (EYES_HOT, 25),
            3: (EYES_FLASH, 26), -1: (EYES_SPENT, 26), -2: (EYES_OUT, 26)}[eye]
    cv.stamp(eyes[0], 36 + dx, eyes[1] + dy, over_only=True)

    cv.stamp(F.NOSE, 45 + dx, 27 + dy, over_only=True)

    mouth = {'flash': (MOUTH_SNARL, 44, 34), 'strain': (MOUTH_GASP, 44, 35),
             'beaten': (MOUTH_SLACK, 45, 36)}.get(expr, (F.MOUTH, 44, 35))
    cv.stamp(mouth[0], mouth[1] + dx, mouth[2] + dy, over_only=True)

    # the furrow between the brows - the cheapest anger tell there is
    if expr in ('glare', 'strain'):
        for y in (24, 25, 26):
            for x in (46, 47, 48, 49):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and cv.px[yy][xx] not in (None, BLACK):
                    cv.px[yy][xx] = PALC['w' if x in (47, 48) else 'v']

    cv.stamp(F.EARRING, 30 + dx, 32 + dy)


def eye_lances(cv, dx=0, dy=0, drop=0, reach=16, level=1.0):
    """Two bars of light punching sideways out of the sockets.  This is the
    frame where the player loses control, so the light has to leave his face."""
    ey = 29 + dy + drop
    for side, x0 in ((-1, 38 + dx), (1, 57 + dx)):
        for t in range(1, reach):
            f = t / float(reach)
            x = x0 + side * t
            if not (0 <= x < W):
                continue
            hgt = 2 if f < 0.30 else (1 if f < 0.72 else 0)
            for d in range(-hgt, hgt + 1):
                y = ey + d
                if not (0 <= y < H):
                    continue
                if abs(d) == hgt and hgt and (t + d) % 2:
                    continue
                c = 'M' if f < 0.26 else ('O' if f < 0.55 else
                                          ('V' if f < 0.80 else '7'))
                cv.px[y][x] = PALC[c]
            if f > 0.72 and (t % 2):
                break


# ---------------------------------------------------------------- back of head

def draw_back_head(cv, dx=0, dy=0, shade=0):
    """The skull from behind, for the clone leaving the frame: bald dome,
    occiput in shadow, the orange beard showing past the jaw on both sides so
    he is still unmistakably Carter with his back turned, and the cross earring
    swapped to the other ear.  Same construction as poses.draw_back."""
    from lib import grow as _grow
    hd, er, bd = head_masks(dx, dy)
    nk = neck(dy)
    cv.part(nk, 'skin', cylm((41.0 + dx, 40.0 + dy), (54.0 + dx, 40.0 + dy), 7.4),
            TH_HARD, bias=1 + shade)
    cv.part(er, 'skin', ('dist', 3.4), TH_HARD, bias=shade)
    cv.part(hd, 'skin', sphm(45.0 + dx, 25.0 + dy, 17.4, 17.6, 0.30), TH_HARD,
            bias=shade)
    _seg(cv, [(38, 20), (38, 17), (40, 14), (44, 13), (49, 13)], 's', dx, dy, False)
    _seg(cv, [(39, 20), (39, 17), (41, 15), (44, 14), (49, 14)], 's', dx, dy, False)
    _seg(cv, [(58, 16), (60, 20), (60, 25), (59, 29)], 'v', dx, dy, False)
    # occiput / base of the skull
    _seg(cv, [(40, 34), (47, 36)], 'v', dx, dy)
    _seg(cv, [(41, 37), (47, 39)], 'w', dx, dy)

    jaw = inter(shift_mask(poly(P.mir_pts([
        (47.5, 44.0), (43.6, 43.6), (40.2, 41.8), (37.0, 38.4),
        (34.8, 34.0), (34.0, 29.6), (36.4, 29.0), (37.6, 33.4),
        (39.6, 37.0), (42.6, 39.6), (47.5, 40.6),
    ])), dx, dy), _grow(hd, 2))
    # thicken the crescent: at the width poses.draw_back uses it is a 1px rim,
    # which is invisible on a clone going past at speed.  The beard is the only
    # thing that says Carter when you cannot see his face.
    jaw = inter(_grow(jaw, 1), _grow(hd, 2))
    cv.part(jaw, 'hair', ('dist', 3.2), TH_HARD, bias=shade)
    _seg(cv, [(36, 31), (37, 36), (40, 40)], '2', dx, dy)
    _seg(cv, [(62, 25), (62, 29)], 'w', dx, dy, False)
    _seg(cv, [(34, 24), (33, 28), (34, 31)], 'w', dx, dy, False)
    cv.stamp(EARRING_R, 59 + dx, 32 + dy)
    return hd, er, jaw, nk


EARRING_R = """
...k...
...k...
..kkk..
..k#k..
kkk#kkk
k##%##k
kkk&kkk
..k&k..
..kkk..
"""
