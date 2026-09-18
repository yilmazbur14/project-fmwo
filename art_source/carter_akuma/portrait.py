"""Carter's dialogue portrait: Assets/Characters/Carter/portrait.png.

The old file was the two-headed Carter-and-Josh bust from the tag-team fight -
byte for byte the same image that used to sit in Josh's folder.  Josh's has been
redrawn; this is Carter's.  He is alone, on the approved Satsui no Hado design:
bald skull, short orange beard, cross earring on his left ear, the deadpan stare
with the eye slits burning red, the torn navy-into-violet gi over his shoulders,
the juzu, and the dark red-purple aura coming off him.

This is the face the player is looking at while he says "I only have one move.
You won't see it twice.", so it is pitched at menace rather than neutrality: the
lids sit heavy and low, the brows drive down into a furrow, the mouth is a flat
line that is not going to move, and the only bright thing in the picture is the
pair of slits looking straight out of it.

Format, measured off the old file so it drops straight into the dialogue system:
    64x64, binary alpha, bust framing with the shoulders running off the bottom.

Drawn at portrait scale rather than upscaled from the 96x96 sprite - the sprite's
face is 24px wide and survives being seen at 3x across a room, not being stared
at.  Here the skull is 33px wide and the features are redrawn to suit, but every
colour comes out of lib.PAL so he stays exactly on palette with the sheets.

Run:  python portrait.py [dest_dir]
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
lib.W = lib.H = 64                 # portrait canvas, not the 96x96 sprite frame
from lib import (Canvas, poly, ell, union, inter, sub, grow, erode, empty,
                 bayer, band, PALC, BLACK, RAMPS, hexc,
                 TH_HARD, TH_HARD2, GI_RAMP, GIP_RAMP, _lerp)
from pngio import write_png

W = H = 64
AX = 64.0                          # mirror: x' = 64 - x, so centre is 32.0
CX = 32.0


# ---------------------------------------------------------------- helpers
# render.seg and intro_lib bind lib.W/H by value at import time, so the combat
# modules cannot be reused at this size; these are 64-wide equivalents.

def mir(half):
    return half + [(AX - x, y) for x, y in reversed(half[1:-1])]


def seg(cv, pts, ch, both=False, over_only=True):
    col = PALC[ch]
    runs = [pts] + ([[(AX - x, y) for x, y in pts]] if both else [])
    for run in runs:
        for i in range(len(run) - 1):
            x0, y0 = run[i]
            x1, y1 = run[i + 1]
            n = int(max(abs(x1 - x0), abs(y1 - y0)))
            for s in range(n + 1):
                t = s / max(1, n)
                x = int(round(x0 + (x1 - x0) * t))
                y = int(round(y0 + (y1 - y0) * t))
                if not (0 <= x < W and 0 <= y < H):
                    continue
                if over_only and (cv.px[y][x] is None or cv.px[y][x] == BLACK):
                    continue
                cv.px[y][x] = col


def dot(cv, x, y, ch):
    if 0 <= x < W and 0 <= y < H and cv.px[y][x] is not None:
        cv.px[y][x] = PALC[ch]


def cylm(a, b, r):
    return ('cyl', a, b, r)


def sphm(cx, cy, rx, ry, flat=0.0):
    return ('sphere', cx, cy, rx, ry, flat)


_PAL_LIST = list(PALC.values())


def snap(rgb):
    best, bd = None, 1 << 30
    for c in _PAL_LIST:
        d = ((c[0] - rgb[0]) ** 2 + (c[1] - rgb[1]) ** 2 + (c[2] - rgb[2]) ** 2)
        if d < bd:
            bd, best = d, c
    return best


def mixc(a, b, t):
    if t <= 0:
        return a
    if t >= 1:
        return b
    return snap((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
                 a[2] + (b[2] - a[2]) * t))


def cyl_mask(a, b, r0, r1=None):
    if r1 is None:
        r1 = r0
    m = empty()
    (x0, y0), (x1, y1) = a, b
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - x0, y + 0.5 - y0
            t = 0.0 if L2 == 0 else max(0.0, min(1.0, (px * dx + py * dy) / L2))
            cx, cy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                m[y][x] = True
    return m


def _bez(pts, t):
    p = list(pts)
    while len(p) > 1:
        p = [((1 - t) * p[i][0] + t * p[i + 1][0],
              (1 - t) * p[i][1] + t * p[i + 1][1]) for i in range(len(p) - 1)]
    return p[0]


def tendril(ctrl, w0, w1, n=20):
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        cx, cy = _bez(ctrl, t)
        ax, ay = _bez(ctrl, min(1.0, t + 0.03))
        bx, by = _bez(ctrl, max(0.0, t - 0.03))
        dx, dy = ax - bx, ay - by
        L = math.hypot(dx, dy) or 1.0
        px, py = -dy / L, dx / L
        wd = (w0 + (w1 - w0) * (t ** 0.75)) / 2.0
        left.append((cx + px * wd, cy + py * wd))
        right.append((cx - px * wd, cy - py * wd))
    return poly(left + list(reversed(right)))


# ---------------------------------------------------------------- masks

# Skull: the approved head shape, re-proportioned for a bust.  Wide temples, a
# heavy brow shelf and a jaw that tapers but stays broad - at 33px across the
# dome has to stay a skull rather than becoming an egg.
HEAD_HALF = [
    (32.0, 10.4),
    (25.6, 10.8),
    (20.8, 13.0),
    (17.8, 17.0),
    (16.8, 22.0),
    (17.0, 27.8),
    (18.4, 33.4),
    (21.2, 38.6),
    (25.6, 42.4),
    (32.0, 44.0),
]


def head():
    return poly(mir(HEAD_HALF))


def ears():
    e = union(ell(17.0, 28.4, 3.4, 5.0), ell(18.4, 25.8, 2.8, 3.6))
    return union(e, [row[::-1] for row in e])


def beard():
    """Solid short beard over jaw and chin plus sideburns up to the ears, and a
    separate heavy moustache above it.  Not a crescent - Carter's beard is a
    mass, exactly as on the sheets."""
    # The top edge is the whole thing.  Run it flat across at eye level and the
    # beard reads as a mask strapped to his face; it has to ride HIGH at the
    # ears, where the sideburns are, and DIP in the middle under the nose, so
    # the cheeks stay skin and the shape becomes a beard.
    low = poly(mir([
        (32.0, 50.4),
        (27.4, 49.8),
        (23.0, 47.2),
        (19.6, 42.6),
        (17.8, 36.4),
        (17.4, 29.4),
        (20.6, 30.6),
        (24.0, 32.8),
        (27.8, 35.0),
        (32.0, 36.2),
    ]))
    low = inter(low, grow(head(), 3))
    sb = inter(sub(head(), erode(head(), 3)), band(24.5, 39.0))
    return union(low, sb)


def moustache():
    """The moustache is drawn as its own mask so it can be lit a step brighter
    than the chin beard.  At portrait size a single flat orange mass from the
    eyes to the collarbone reads as a mask, not a face - the separation between
    moustache, mouth and chin is what makes it a beard."""
    m = poly(mir([
        (32.0, 37.0), (27.8, 36.6), (23.4, 38.0), (22.2, 41.8),
        (25.4, 43.6), (32.0, 44.2),
    ]))
    notch = poly([(29.6, 33.8), (34.4, 33.8), (34.4, 38.2), (29.6, 38.2)])
    return sub(m, notch)


def neck():
    return poly(mir([
        (32.0, 40.0), (26.0, 40.6), (23.8, 45.0), (23.2, 53.0), (32.0, 55.0),
    ]))


def traps():
    """The slab from the jaw out to the deltoids.  The first version sloped
    away too shallowly and left a head floating over a sliver of shoulder;
    Josh's bust fills the bottom quarter of the frame and this now does too."""
    return poly(mir([
        (32.0, 46.0), (23.0, 47.6), (15.4, 51.4), (9.0, 56.6), (5.2, 62.0),
        (4.4, 64.5), (32.0, 64.5),
    ]))


def shoulders():
    return poly(mir([
        (32.0, 48.0), (21.0, 50.0), (13.0, 54.0), (7.2, 59.4), (4.8, 64.5),
        (32.0, 64.5),
    ]))


def gi():
    """Torn gi over both shoulders, open down the front so the chest and the
    juzu read.  The hem runs off the bottom edge, like Josh's coat."""
    cap = poly(mir([
        (32.0, 50.6), (22.0, 52.2), (14.0, 56.0), (8.2, 61.0), (5.8, 64.5),
        (32.0, 64.5),
    ]))
    # the opening: a V down the middle where the jacket falls away
    opening = poly([(25.6, 50.0), (32.0, 60.0), (38.4, 50.0),
                    (38.4, 65.0), (25.6, 65.0)])
    j = sub(cap, opening)
    # ragged torn edge along the collar
    tear = empty()
    for (x0, y0, x1, y1) in ((7.4, 60.4, 11.4, 57.0), (12.4, 57.6, 16.4, 55.0),
                             (17.4, 55.4, 21.4, 53.0),
                             (56.6, 60.4, 52.6, 57.0), (51.6, 57.6, 47.6, 55.0),
                             (46.6, 55.4, 42.6, 53.0)):
        tear = union(tear, cyl_mask((x0, y0 - 1.5), (x1, y1 - 1.5), 1.4))
    return sub(j, tear)


def beads_pts():
    """juzu slung across the collarbones, dipping in the middle"""
    pts = []
    for i in range(9):
        t = i / 8.0
        x = 19.0 + t * 26.0
        y = 52.0 + math.sin(math.pi * t) * 7.4
        pts.append((x, y))
    return pts


# ---------------------------------------------------------------- stamps
# 31 wide, anchored at x=17, so the stamp's centre column lands on x=32 and
# every mirrored pair lines up exactly with the head's own axis.

BROWS = """
.44444444.............44444444.
.55555555555.......55555555555.
..556666666666...666666666655..
"""

EYES = """
.kkkkkkkkkkk.......kkkkkkkkkkk.
.kkkkkkkkkkk.......kkkkkkkkkkk.
.kkkkkkkkkkk.......kkkkkkkkkkk.
.kVOOOOOOOVk.......kVOOOOOOOVk.
.kV7777777Vk.......kV7777777Vk.
.k877777778k.......k877777778k.
..kwwwwwwwk.........kwwwwwwwk..
...vvvvvvv...........vvvvvvv...
"""

# 7 wide, anchored x=29: lit down the left of the bridge, shadowed on the right,
# two separate nostrils rather than the one black bar the sprite can get away
# with at a quarter of this size.
NOSE = """
..stvw.
..stvw.
.sstvww
.sstvww
.sttvwW
.sttvwW
wkk.kkw
.vwwWv.
"""

# 15 wide, anchored x=25.  A flat closed line, the lit underside of the
# moustache above it and the chin in shadow below: the deadpan.
MOUTH = """
..2222222..
.kkkkkkkkk.
.kkkkkkkkk.
.k5555555k.
..6666666..
"""

# the cross earring, hanging off his left lobe
EARRING = """
...k...
...k...
...k...
..kkk..
..k#k..
..k#k..
kkk#kkk
k##%##k
k#####k
kkk&kkk
..k&k..
..k&k..
..kkk..
"""


# ---------------------------------------------------------------- aura
# Deliberately shorter and narrower than the sheets' crown.  At full height it
# read as a set of horns filling the top third of the frame, and the face
# stopped being the subject of its own portrait.

AURA = [
    ([(23.0, 17.0), (17.5, 11.0), (19.5, 6.0), (13.5, 3.0)], 7.2, 1.1),
    ([(27.5, 12.5), (25.2, 8.0), (27.4, 5.0), (23.4, 3.2)], 6.2, 1.1),
    ([(32.0, 10.4), (33.0, 6.2), (30.8, 4.0), (33.6, 2.8)], 6.8, 1.1),
    ([(36.5, 12.5), (38.8, 8.0), (36.6, 5.0), (40.6, 3.2)], 6.2, 1.1),
    ([(41.0, 17.0), (46.5, 11.0), (44.5, 6.0), (50.5, 3.0)], 7.2, 1.1),
    ([(18.8, 24.0), (13.6, 20.0), (14.8, 14.8), (9.6, 11.2)], 5.4, 1.0),
    ([(45.2, 24.0), (50.4, 20.0), (49.2, 14.8), (54.4, 11.2)], 5.4, 1.0),
    ([(19.4, 38.0), (13.8, 35.0), (14.6, 30.0), (9.4, 26.6)], 5.0, 1.0),
    ([(44.6, 38.0), (50.2, 35.0), (49.4, 30.0), (54.6, 26.6)], 5.0, 1.0),
]

SPARKS = [(16.0, 10.5), (48.0, 9.5), (10.5, 21.5), (53.5, 20.5),
          (27.5, 5.0), (36.5, 5.5), (9.0, 34.0), (55.0, 33.0)]


def paint_aura(cv, body):
    whole = empty()
    for ctrl, w0, w1 in AURA:
        whole = union(whole, tendril(ctrl, w0, w1))
    for sx, sy in SPARKS:
        whole = union(whole, ell(sx, sy, 1.4, 1.4))
    whole = sub(whole, grow(body, 1))
    cv.paint(whole, PALC['T'])
    for ch, n in (('S', 1), ('R', 2), ('Y', 3), ('y', 4)):
        cv.paint(erode(whole, n), PALC[ch])
    # hot at the roots where it leaves him, cool out at the tips
    near = inter(whole, grow(body, 6))
    warm = {PALC['T']: PALC['Z'], PALC['S']: PALC['z'], PALC['R']: PALC['Y'],
            PALC['Y']: PALC['y'], PALC['y']: PALC['X']}
    for y in range(H):
        for x in range(W):
            if near[y][x] and cv.px[y][x] in warm:
                cv.px[y][x] = warm[cv.px[y][x]]
    cv.outline(whole, PALC['U'])
    return whole


def haze(cv, body):
    r1 = sub(grow(body, 2), body)
    r2 = sub(grow(body, 4), grow(body, 2))
    for rgn, lvl, ch in ((r1, 6, 'T'), (r2, 3, 'U')):
        d = bayer(rgn, lvl, 0)
        for y in range(H):
            for x in range(W):
                if d[y][x] and cv.px[y][x] is None:
                    cv.px[y][x] = PALC[ch]


def eye_light(cv, level=0.55):
    """The slits are a real light source sitting in his face, so the sockets,
    the nose bridge and the upper cheeks catch some of it.  Red, not white -
    this is the deadpan, not the eye flash."""
    skin = set(hexc(c) for c in RAMPS['skin'] + RAMPS['skinr'])
    for cx, cy in ((23.0, 27.0), (41.0, 27.0)):
        r = 8.0
        for y in range(max(0, int(cy - r)), min(H, int(cy + r + 1))):
            for x in range(max(0, int(cx - r)), min(W, int(cx + r + 1))):
                c = cv.px[y][x]
                if c not in skin:
                    continue
                f = max(0.0, 1.0 - math.hypot(x + 0.5 - cx, y + 0.5 - cy) / r)
                a = (f ** 1.4) * level
                if a < 0.14:
                    continue
                cv.px[y][x] = mixc(c, PALC['V'] if a > 0.40 else PALC['7'],
                                   min(0.7, a))


def gi_fade(cv, mask, y0, y1):
    """the same navy-to-violet fall-off the sheets use, so the gi matches"""
    steps = [[_lerp(GI_RAMP[i], GIP_RAMP[i], t) for i in range(6)]
             for t in (0.0, 0.34, 0.67, 1.0)]
    idx_of = {c: i for i, c in enumerate(GI_RAMP)}
    for y in range(H):
        t = max(0.0, min(1.0, (y - y0) / max(1e-6, (y1 - y0))))
        st = min(3, int(t * 3.999))
        for x in range(W):
            if mask[y][x] and cv.px[y][x] in idx_of:
                cv.px[y][x] = steps[st][idx_of[cv.px[y][x]]]


# ---------------------------------------------------------------- build

def body_mask():
    return union(union(union(head(), ears()), union(beard(), moustache())),
                 union(union(neck(), traps()), union(shoulders(), gi())))


def build():
    cv = Canvas()
    bm = body_mask()
    paint_aura(cv, bm)
    haze(cv, bm)

    # ---- shoulders and traps first, the head sits on top of them
    sh = union(traps(), shoulders())
    cv.part(sh, 'skin', sphm(24.0, 68.0, 32.0, 20.0, 0.25), TH_HARD, bias=0)
    cv.outline(sh)
    seg(cv, [(10, 57), (6, 62)], 'w', both=True)
    seg(cv, [(13, 55), (8, 60)], 'v', both=True)

    # ---- collarbones and the pit of the throat, on the bare chest
    seg(cv, [(24, 54), (28, 55), (31, 56)], 'v', both=True)
    seg(cv, [(24, 53), (29, 54)], 's', both=True)
    seg(cv, [(30, 57), (32, 58), (34, 57)], 'w')

    # ---- the torn gi over the shoulders
    jk = gi()
    cv.part(jk, 'gi', ('dist', 9.0), TH_HARD2, bias=0)
    cv.outline(jk)
    gi_fade(cv, jk, 53.0, 65.0)
    seg(cv, [(6, 61), (13, 57), (21, 54)], 'a', both=True)
    seg(cv, [(4, 63), (11, 59), (19, 56)], 'b', both=True)
    seg(cv, [(24, 55), (28, 62)], 'e')
    seg(cv, [(40, 55), (36, 62)], 'e')

    # ---- juzu across the collarbones
    pts = beads_pts()
    seg(cv, [(int(round(x)), int(round(y))) for x, y in pts], 'k',
        over_only=False)
    for bx, by in pts:
        cv.part(ell(bx, by, 2.4, 2.4), 'bead', sphm(bx - 0.7, by - 0.9, 3.0, 3.0),
                TH_HARD, bias=0)
        dot(cv, int(bx - 0.8), int(by - 1.0), 'G')

    # ---- neck
    nk = neck()
    cv.part(nk, 'skin', cylm((23.0, 48.0), (41.0, 48.0), 10.0), TH_HARD, bias=0)
    cv.outline(nk)
    # sternocleidomastoid, so the throat is not a tube, and the jaw's shadow
    seg(cv, [(27, 45), (29, 51), (31, 54)], 'v')
    seg(cv, [(37, 45), (35, 51), (33, 54)], 'w')
    seg(cv, [(25, 45), (32, 47), (39, 45)], 'W')
    seg(cv, [(25, 46), (32, 48), (39, 46)], 'w')

    # ---- skull
    hd, er = head(), ears()
    cv.part(er, 'skin', ('dist', 3.6), TH_HARD, bias=0)
    cv.outline(er)
    cv.part(hd, 'skin', sphm(28.0, 25.0, 19.0, 20.0, 0.30), TH_HARD, bias=0)
    cv.outline(hd)
    # bald-dome specular sweeping over the top left, rim down the right
    seg(cv, [(22, 20), (22, 16), (25, 12), (31, 10), (37, 11)], 's')
    seg(cv, [(23, 21), (23, 17), (26, 14), (31, 12), (37, 13)], 's')
    seg(cv, [(24, 23), (24, 19), (27, 16)], 't')
    seg(cv, [(45, 16), (47, 22), (47, 28), (46, 33)], 'v')
    seg(cv, [(44, 17), (46, 23), (46, 29)], 'u')
    seg(cv, [(45, 36), (42, 41), (37, 44)], 'v')
    # temple hollows and the brow shelf casting down onto the sockets
    seg(cv, [(20, 18), (19, 24)], 'v', both=True)
    seg(cv, [(21, 22), (25, 23), (29, 23)], 'v', both=True)
    seg(cv, [(22, 16), (28, 14), (32, 14)], 't', both=True)
    # ear inner
    seg(cv, [(18, 26), (17, 29), (18, 32)], 'w', both=True)
    seg(cv, [(19, 27), (18, 30)], 'v', both=True)

    # ---- beard, then the moustache one ramp step brighter on top of it
    bd = beard()
    cv.part(bd, 'hair', ('dist', 5.0), TH_HARD, bias=0)
    cv.outline(bd)
    ms = moustache()
    cv.part(ms, 'hair', ('dist', 3.4), TH_HARD, bias=0)
    cv.outline(ms)
    # strand texture: lit along the top of the jaw, dark under the chin
    seg(cv, [(21, 34), (20, 40)], '1', both=True)
    seg(cv, [(24, 33), (23, 38)], '2', both=True)
    seg(cv, [(23, 44), (26, 47)], '4', both=True)
    seg(cv, [(27, 48), (32, 49)], '6', both=True)
    seg(cv, [(22, 42), (26, 46), (31, 48)], '5')
    seg(cv, [(42, 42), (38, 46), (33, 48)], '4')
    seg(cv, [(25, 39), (32, 40), (39, 39)], '1')
    seg(cv, [(24, 45), (32, 47), (40, 45)], '6')

    # ---- face
    cv.stamp(BROWS, 17, 18, over_only=True)
    cv.stamp(EYES, 17, 22, over_only=True)
    cv.stamp(NOSE, 29, 25, over_only=True)
    cv.stamp(MOUTH, 26, 41, over_only=True)
    # the furrow between the brows: the whole expression hangs on it
    for y in (19, 20, 21, 22):
        for x in (30, 31, 32, 33):
            if cv.px[y][x] not in (None, BLACK):
                cv.px[y][x] = PALC['w' if x in (31, 32) else 'v']
    eye_light(cv, 0.38)
    cv.stamp(EARRING, 13, 32)
    return cv


if __name__ == '__main__':
    out = (sys.argv[1] if len(sys.argv) > 1
           else 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Carter')
    cv = build()
    px = cv.rgba()
    p = os.path.join(out, 'portrait.png')
    write_png(p, W, H, px)
    xs = [x for y in range(H) for x in range(W) if px[y][x][3]]
    ys = [y for y in range(H) for x in range(W) if px[y][x][3]]
    print('wrote %s  %dx%d  bounds x%d..%d y%d..%d  colours %d'
          % (p, W, H, min(xs), max(xs), min(ys), max(ys),
             len(set(tuple(q) for r in px for q in r if q[3]))))
