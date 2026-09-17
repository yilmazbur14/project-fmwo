"""Normal-size Bixby (bixby.png, 64x64) and Liam (liam.png, 64x64) variants for the defeat sequence.
Everything is built by stamping ASCII edits onto the approved sprites, so identity pixels stay untouched.
Local palettes extend pal.PALC with each sprite's own extra colours (copied from the PNGs)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
from pal import PALC, BLACK

ROOT = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/'
BIXBY_PNG = ROOT + 'Bixby/bixby.png'
LIAM_PNG = ROOT + 'Liam/liam.png'


def hexc(s):
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


# bixby.png extras
BPAL = dict(PALC)
BPAL.update({'!': hexc('f4e9dc'), '#': hexc('3b1e12'), '$': hexc('ff9a3c'), '%': hexc('ffb3c0')})
# liam.png extras (hair / skin / jacket / shirt / tie)
LPAL = dict(PALC)
LPAL.update({'!': hexc('56352a'), '#': hexc('36201a'), '$': hexc('120a08'), '%': hexc('eec39a'), '&': hexc('fadcb8'),
             '*': hexc('d9a066'), '=': hexc('b8794a'), '?': hexc('8a5236'), '@': hexc('d6dee5'), '^': hexc('663931'),
             '~': hexc('8f563b'), ';': hexc('c3885a'), ':': hexc('a96b43'), '<': hexc('a3b1bc'), '>': hexc('c4d2da'),
             '/': hexc('45283c'), '\\': hexc('181830')})
# slime (pale blue saliva): C = CBDBFC, W = white highlight, i = B3C0C9 shade, j = 7B8893 rim


def stamp(cv, grid, x0, y0, pal, flip=False):
    """'.' keeps, '_' clears, anything else paints from pal"""
    rows = grid.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x = x0 + (w - 1 - dx if flip else dx)
            if ch == '_':
                cv.put(x, y0 + dy, None)
            else:
                cv.put(x, y0 + dy, pal[ch])


def load(path):
    return from_png(path)


def keep_size(fn):
    """small-sprite builders change lib's global mask size; restore it so callers' masks are not clipped"""
    def wrap(*a, **k):
        w, h = lib.W, lib.H
        try:
            return fn(*a, **k)
        finally:
            lib.set_size(w, h)
    wrap.__name__ = fn.__name__
    return wrap


# ================================================================== BIXBY expression stamps (64x64 coords)
# measured on bixby.png: middle eyes x24-28 / x34-38 rows 9-13, nose rows 14-18, smile rows 19-20 x28-34,
# chin outline row 23, collar from row 24. Left head eyes x10-12 / x16-18 rows 22-24 (faces left),
# right head eyes x45-47 / x53-55 rows 21-23 (faces right), right tongue x53-57 rows 31-34.
EYE_SWIRL = """
2kkk2
k222k
k2k2k
k22k2
2k222
"""
EYE_SHUT_L = """
22222
kk222
22kk2
kk222
22222
"""
EYE_WIDE = """
2kkk2
kWWWk
kWW#k
kWWWk
2kkk2
"""
EYE_GLANCE = """
22222
kkkkk
3kW#k
2kkk2
22222
"""
SIDE_X = """
k2k
2k2
k2k
"""
SIDE_WIDE = """
2k2
kWk
k#k
2k2
"""
SIDE_HAPPY = """
2k2
k2k
222
"""
MOUTH_CLAMP = """
ww..w..w..vvv
.wkkkkkkkkkv.
"""
MOUTH_HACK = """
..kkkkkkkkk..
.kMMCMMMCMMk.
kMMMCMMMCMMMk
kMMMMMMMMMMMk
kMnmmmmmmmnMk
.kMm%%%%%mMk.
..kkkkkkkkk..
"""
MOUTH_NERVOUS = """
kwwkwwkwwk
wkkwkkwkkw
"""
TONGUE_L_LONG = """
k%mmmnk
.kmnmnk
.kmmnk.
..kmk..
..kk...
"""
SWEAT = """
.k.
kCk
CWk
kkk
"""


@keep_size
def bixby_variant(kind):
    cv = load(BIXBY_PNG)
    P = BPAL
    if kind == 'base':
        return cv
    if kind == 'dizzy':
        stamp(cv, EYE_SWIRL, 24, 9, P)
        stamp(cv, EYE_SWIRL, 34, 9, P, flip=True)
        stamp(cv, SIDE_X, 10, 22, P)
        stamp(cv, SIDE_X, 16, 22, P)
        stamp(cv, SIDE_X, 45, 21, P)
        stamp(cv, SIDE_X, 53, 21, P)
        stamp(cv, TONGUE_L_LONG, 6, 31, P)
    elif kind == 'cough':
        stamp(cv, EYE_SHUT_L, 24, 9, P)
        stamp(cv, EYE_SHUT_L, 34, 9, P, flip=True)
        stamp(cv, MOUTH_CLAMP, 25, 19, P)
        stamp(cv, SIDE_WIDE, 10, 21, P)
        stamp(cv, SIDE_WIDE, 16, 21, P)
        stamp(cv, SIDE_WIDE, 45, 20, P)
        stamp(cv, SIDE_WIDE, 53, 20, P)
    elif kind == 'hack':
        stamp(cv, EYE_SHUT_L, 24, 9, P)
        stamp(cv, EYE_SHUT_L, 34, 9, P, flip=True)
        stamp(cv, MOUTH_HACK, 25, 18, P)
        stamp(cv, SIDE_WIDE, 10, 21, P)
        stamp(cv, SIDE_WIDE, 16, 21, P)
        stamp(cv, SIDE_WIDE, 45, 20, P)
        stamp(cv, SIDE_WIDE, 53, 20, P)
    elif kind == 'look':
        stamp(cv, EYE_WIDE, 24, 9, P)
        stamp(cv, EYE_WIDE, 34, 9, P)
        stamp(cv, SIDE_WIDE, 10, 21, P)
        stamp(cv, SIDE_WIDE, 16, 21, P)
        stamp(cv, SIDE_WIDE, 45, 20, P)
        stamp(cv, SIDE_WIDE, 53, 20, P)
    elif kind == 'sheepish':
        stamp(cv, EYE_GLANCE, 24, 9, P)
        stamp(cv, EYE_GLANCE, 34, 9, P)
        stamp(cv, MOUTH_NERVOUS, 27, 19, P)
        stamp(cv, SIDE_HAPPY, 10, 22, P)
        stamp(cv, SIDE_HAPPY, 16, 22, P)
        stamp(cv, SWEAT, 41, 4, P)
    return cv


# ================================================================== BIXBY sitting (sheepish hold pose)
EYE_WORRY_L = """
2222k
22kk2
kk222
2kW#k
22kk2
"""
EYE_WORRY_R = """
k2222
2kk22
222kk
kW#k2
2kk22
"""
BLUSH = """
%%.
"""
HAUNCH = """
..kDDJJDDJJJJJJJJwvuuJ
..kDJ32J323JJJJJwvuuuu
..k3221223334JJuvuuuuu
.k322334112233uuuuuuuu
.k2233wwwww3344uuuuuuu
k2233wWWwwwv3344uuuuuk
k2334wWwwwwvvv344uuuuk
k334wWwwwwwvvvu44uuuuk
k34wWwwwwwvvvvuu4kuuk.
k4wWwwwwwvvvvuuuukuuk.
kwWwwwwwvvvvuuuukkkkk.
kWwwwwwvvvvuuuuk......
.kWwwkwwkvvkuuk.......
.kwwwkwvkuuuuk........
..kkkkkkkkkkk.........
"""


@keep_size
def bixby_sit():
    """bixby.png sitting sheepishly: worried brows glancing right (at Liam), nervous smile, happy-guilty side heads
    with a blush, sweat drop; upper body lowered 3px (leg shafts shortened), rump folded into a haunch."""
    src = load(BIXBY_PNG)
    P = BPAL
    stamp(src, EYE_WORRY_L, 24, 8, P)
    stamp(src, EYE_WORRY_R, 34, 8, P)
    stamp(src, MOUTH_NERVOUS, 27, 19, P)
    stamp(src, SIDE_HAPPY, 10, 22, P)
    stamp(src, SIDE_HAPPY, 16, 22, P)
    stamp(src, BLUSH, 8, 26, P)
    stamp(src, BLUSH, 52, 25, P)
    lib.set_size(64, 64)
    cv = Canvas(64, 64)
    for y in range(0, 53):
        for x in range(64):
            cv.px[y + 3][x] = src.px[y][x]
    for y in range(56, 64):
        for x in range(22, 64):
            cv.px[y][x] = src.px[y][x]
    for y in range(56, 64):
        for x in range(0, 22):
            cv.px[y][x] = None
    stamp(cv, HAUNCH, 0, 49, P)
    stamp(cv, SWEAT, 41, 6, P)
    return cv


# ================================================================== LIAM variants
SLIME = {'C': PALC['C'], 'W': PALC['W'], 'i': PALC['i'], 'j': PALC['j']}
GLASSES_ASKEW = """
.................kkkkkkkkk........
.................kkWWWWWWk........
.................kkWWWWWCk........
.................kkWWWWWWkkkkkkkkk
.................kkkkkkkkkkWWWWWWk
.................ke%&%%%*kWWjWWWWk
.................ke#e%k%*kWjWWWWCk
.................kee#ee##kjWWWWWCk
.................ke#ekWWWkkkkkkkkk
"""
GRIN_DAZED = """
................kee#ekWWWWWWWWkkkkk
................ke#ekW@WW@WWWWWWWk.
.................kee#kWWWWW@W@WWk..
.................ke#ee$kkkkkWWWkk..
.................kee#!#e#ee#kkk....
"""
SLIME_BLOBS = [
    # (stamp, x, y) in liam.png coords: a dollop on the curls, drips off the headband, shoulders and fist
    ("""
..kkkkk..
.kCWWWCk.
kCCCCCCCk
kCkCCkCCk
.k.kCk.k.
....k....
""", 24, 0),
    ("""
kCk
kCk
kWk
.k.
""", 17, 9),
    ("""
kCCk
.kCk
.kWk
..k.
""", 40, 10),
    ("""
kCCCk
.kCk.
.kWk.
..k..
""", 8, 27),
    ("""
kCCk
kCk.
kWk.
.k..
""", 52, 29),
    ("""
kCk
kWk
.k.
""", 32, 28),
]
SLIME_DRIPS = []


def slime_drip(cv, x, y, n):
    cv.put(x, y, PALC['W'])
    for k in range(1, n + 1):
        cv.put(x, y + k, PALC['C'])
    cv.put(x, y + n + 1, PALC['j'])


@keep_size
def liam_base(slimy=True, dazed=True):
    cv = load(LIAM_PNG)
    if dazed:
        stamp(cv, GLASSES_ASKEW, 0, 12, LPAL)
        stamp(cv, GRIN_DAZED, 0, 21, LPAL)
    if slimy:
        for grid, x, y in SLIME_BLOBS:
            stamp(cv, grid, x, y, LPAL)
    return cv


@keep_size
def liam_sit(squash=0, slimy=True):
    """dazed Liam sitting on the floor, legs splayed forward (shoes up), fist on the floor, hand on hip.
    64x64, ground contact on rows 60-63. squash > 0 compresses the torso for the landing impact frame."""
    src = liam_base(slimy=slimy)
    lib.set_size(64, 64)
    cv = Canvas(64, 64)
    # slime puddle under him
    puddle = ell(32, 61, 27, 3.2)
    cv.paint(puddle, PALC['i'])
    cv.paint(ell(26, 60.5, 14, 1.6), PALC['C'])
    cv.outline(puddle, PALC['j'])
    # legs: thighs out of the belt toward the viewer, shoes pointing up at the ends
    for side, hip, knee, foot in ((1, (24, 50), (17, 56), (11, 58)), (-1, (40, 50), (47, 56), (53, 58))):
        leg = capsule(hip, knee, 6.2, 5.2) | capsule(knee, foot, 5.2, 4.4)
        cv.part(leg, 'pants', ('cyl', (hip[0] - 1, hip[1] - 1), (foot[0] - 1, foot[1] - 1), 7, 0.1), [0.95, 0.62, 0.30, 0.05])
        shoe = ell(foot[0] - 2 * side, foot[1] + 1, 6.4, 4.6)
        cv.part(shoe, 'shoe', ('sphere', foot[0] - 4, foot[1] - 2, 7, 6), [0.8, 0.45, 0.1])
        sole = ell(foot[0] - 2 * side, foot[1] + 3.2, 5.0, 1.6) & erode(shoe, 1)
        cv.paint(sole, PALC['E'])
    # upper body (liam.png rows 0..46) sits on top of the legs
    top = 5 + squash
    rows = list(range(0, 47))
    if squash:
        drop = [30, 34, 38][:squash]
        rows = [r for r in rows if r not in drop]
    for i, r in enumerate(rows):
        for x in range(64):
            p = src.px[r][x]
            if p is not None:
                cv.px[top + i][x] = p
    # left fist planted on the floor beside the leg (liam.png rows 47..53, x 3..10)
    fy = top + len(rows) - 1
    for r in range(47, 54):
        for x in range(2, 12):
            p = src.px[r][x]
            if p is not None and 0 <= fy + (r - 47) - 2 < 64:
                cv.px[fy + (r - 47) - 2][x] = p
    # right hand on the hip (rest of liam.png rows 47..49, x 44..52)
    for r in range(47, 50):
        for x in range(44, 53):
            p = src.px[r][x]
            if p is not None:
                cv.px[fy + (r - 46)][x] = p
    return cv


def rot90(cv, k=1):
    """exact pixel rotation by 90 degrees * k (clockwise)"""
    out = cv
    for _ in range(k % 4):
        w, h = out.w, out.h
        r = Canvas(h, w)
        for y in range(h):
            for x in range(w):
                r.px[x][h - 1 - y] = out.px[y][x]
        out = r
    return out


@keep_size
def liam_tumble(k):
    """Liam spinning through the air: liam.png rotated 90*k degrees, slimy, glasses askew"""
    cv = liam_base(slimy=True)
    return rot90(cv, k)


if __name__ == '__main__':
    import anim_common as AC
    items = [bixby_variant(k) for k in ['base', 'dizzy', 'cough', 'hack', 'look']] + [bixby_sit(), liam_base(), liam_sit(), liam_sit(squash=2), liam_tumble(2), liam_tumble(1)]
    strip = Canvas(68 * len(items), 64)
    for i, c in enumerate(items):
        strip.blit(c, i * 68, 0)
    AC.preview(strip, 'small_art_6x.png', 6, bg=AC.BG)
    print('ok')
