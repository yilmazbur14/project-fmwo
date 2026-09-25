"""Josh, redesigned: the initial sprite (idle + signature pose), 2 frames of 80x80, feet on row 79.

Build order is back to front. Every part is keylined as it is stamped, so a part laid over another
cuts its own black line into it - that is where the interior separations come from.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import Canvas, amap, ellipse, fill, line, paint, poly, rect, rim, shift, stroke  # noqa: F401
import lib


def capsule(p0, p1, r0, r1):
    """A tapered limb from p0 to p1 with radii r0 and r1, as a pixel set."""
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    pts = [(x0 + nx * r0, y0 + ny * r0), (x1 + nx * r1, y1 + ny * r1),
           (x1 - nx * r1, y1 - ny * r1), (x0 - nx * r0, y0 - ny * r0)]
    return poly(pts) | ellipse(x0, y0, r0, r0) | ellipse(x1, y1, r1, r1)


#CARDS

PIP_SPADE = ['.k.', 'kkk', 'k.k']
PIP_HEART = ['R.R', 'RRR', '.R.']
PIP_DIAMOND = ['.R.', 'RRR', '.R.']
# the front card's big pip, and the corner marks the cards behind it show
BIG_HEART = ['.R.R.', 'RTRRR', 'RRRRR', '.RRR.', '..R..']
BIG_SPADE = ['..k..', '.kkk.', 'kkkkk', 'kkkkk', '.k.k.', '..k..']
MARK_SPADE = ['.k.', 'kkk', '.k.']
MARK_DIAMOND = ['.R.', 'RRR', '.R.']


def card(bx, by, angle_deg, w=7, h=10, pip=None, face='0', border='8'):
    """A card standing on its bottom-centre point (bx, by), rotated by angle (0 = upright, positive
    leans right). Face, a 1px inset border, and an upright pip at its centre."""
    a = math.radians(angle_deg)
    ux, uy = math.sin(a), -math.cos(a)        # up the card
    rx, ry = math.cos(a), math.sin(a)         # across the card
    hw = (w - 1) / 2.0

    def at(u, v):                              # u across from centre line, v up from bottom
        return (bx + rx * u + ux * v, by + ry * u + uy * v)

    body = poly([at(-hw, 0), at(hw, 0), at(hw, h - 1), at(-hw, h - 1)])
    inner = poly([at(-hw + 1.2, 1.2), at(hw - 1.2, 1.2), at(hw - 1.2, h - 2.2), at(-hw + 1.2, h - 2.2)])
    part = fill(body, border)
    for p in inner:
        if p in part:
            part[p] = face
    if pip:
        cx, cy = at(0, (h - 1) / 2.0)
        cx, cy = int(round(cx)) - 1, int(round(cy)) - 1
        for r, row in enumerate(pip):
            for c, ch in enumerate(row):
                if ch != '.' and (cx + c, cy + r) in part:
                    part[(cx + c, cy + r)] = ch
    return part


def card_poly(corners, pip, face='0', border='9', pip_at=None):
    """A card from its four corners (integer points on clean 2:1 or 1:1 slopes keep the edges
    tidy): border colour on the edge pixels, face inside, an upright pip at the centre."""
    body = poly(corners)
    part = fill(body, face)
    rim(part, border, -1, 0)
    rim(part, border, 1, 0)
    rim(part, border, 0, -1)
    rim(part, border, 0, 1)
    cx = sum(c[0] for c in corners) / 4.0
    cy = sum(c[1] for c in corners) / 4.0
    ox, oy = int(round(cx)) - 1, int(round(cy)) - 1
    if pip_at:
        ox, oy = pip_at
    for r, row in enumerate(pip):
        for c, ch in enumerate(row):
            if ch != '.' and (ox + c, oy + r) in part:
                part[(ox + c, oy + r)] = ch
    return part


#FRAME 0 PARTS

def collar():
    """The popped collar standing up behind his hair: crimson inner face, cream rim over its top."""
    left = fill(poly([(29, 31), (31, 31), (35, 37), (35, 41), (31, 42), (29, 39)]), 'R')
    rim(left, '9', -1, 0, only='R')
    rim(left, '0', 0, -1)
    right = fill(poly([(55, 31), (53, 31), (49, 37), (49, 41), (53, 42), (55, 39)]), 'V')
    rim(right, '8', 1, 0)
    rim(right, '9', 0, -1)
    return [left, right]


def coat_back():
    return fill(poly([(33, 56), (51, 56), (53, 70), (31, 70)]), 'v')


def legs():
    near = fill(poly([(35, 56), (40, 56), (40, 72), (35, 72)]), 'N')
    far = fill(poly([(42, 56), (47, 56), (48, 72), (44, 72)]), 'N')
    for leg in (near, far):
        rim(leg, 's', -1, 0)
        rim(leg, 'n', 1, 0)
    return [far, near]


BOOT_NEAR = [
    # x: 34-38 39-43
    ".kkkk kk...",      # 72
    ".kmll ik...",      # 73
    ".klji ik...",      # 74
    ".klji ikk..",      # 75
    ".klji jik..",      # 76
    "kljjj jjik.",      # 77
    "khhhh hhhhk",      # 78
    ".kkkk kkkk.",      # 79
]
BOOT_FAR = [
    # x: 43-47 48-52
    ".kkkk kk...",      # 72
    ".klll ik...",      # 73
    ".klji ik...",      # 74
    ".klji ikk..",      # 75
    ".klji jjik.",      # 76
    "kljjj jjjik",      # 77
    "khhhh hhhhk",      # 78
    ".kkkk kkkk.",      # 79
]


def boots():
    return [amap(BOOT_FAR, 43, 72), amap(BOOT_NEAR, 34, 72)]


def coat_panels():
    left = fill(poly([(32, 41), (37, 41), (38, 46), (37, 52), (37, 56), (36, 63), (35, 70),
                      (26, 70), (28, 63), (30, 56), (30, 48)]), '9')
    rim(left, '0', -1, 0)
    rim(left, 'o', 1, 0)
    stroke(left, [(33, 57), (32, 63), (31, 70)], '8', only='9')
    stroke(left, [(32, 64), (31, 70)], '7', only='8')
    rim(left, '8', 0, 1, only='90')
    right = fill(poly([(47, 41), (52, 41), (53, 48), (53, 56), (55, 63), (57, 70), (49, 70),
                       (48, 63), (47, 56), (47, 52), (46, 46)]), '8')
    rim(right, 'G', -1, 0)
    lining = poly([(48, 55), (50, 58), (51, 63), (52, 70), (49, 70), (48, 63), (47, 56)])
    paint(right, lining, 'R')
    rim(right, 'G', -1, 0)
    stroke(right, [(50, 58), (51, 63), (52, 69)], 'V', only='R')
    rim(right, '7', 1, 0, only='8')
    stroke(right, [(54, 60), (55, 66)], '7', only='8')
    rim(right, '7', 0, 1, only='8')
    return [right, left]


def lapels():
    left = fill(poly([(36, 40), (39, 40), (38, 47), (37, 49), (34, 44), (34, 41)]), '0')
    rim(left, '9', 1, 0)
    right = fill(poly([(48, 40), (45, 40), (46, 47), (47, 49), (50, 44), (50, 41)]), '8')
    rim(right, '7', 1, 0)
    return [right, left]


VEST_TOP = [
    # x: 38-42 43-47
    "k0kyk 0k...",    # 39  shirt collar points, cravat knot
    "S90zy 09S..",    # 40
    "SS9zy x9SS.",    # 41
    "SSSzy xSSS.",    # 42
    "SSSty xsSS.",    # 43
    "SSSSy sSSS.",    # 44
]


def vest():
    part = fill(poly([(37, 40), (47, 40), (47, 46), (47, 56), (45, 58), (42, 56), (39, 58),
                      (37, 56), (37, 46)]), 'S')
    rim(part, 't', -1, 0)
    rim(part, 's', 1, 0)
    rim(part, 's', 0, 1)
    for p, k in amap(VEST_TOP, 38, 39).items():
        part[p] = k
    for y in (47, 50, 53):
        part[(42, y)] = 'O'
        part[(42, y + 1)] = 'G' if (42, y + 1) in part else part.get((42, y + 1))
    for q in [(43, 51), (44, 52), (45, 52), (46, 51)]:
        part[q] = 'o'
    return part


def far_arm():
    upper = fill(capsule((51, 43), (56, 50), 2.4, 2.1), '8')
    rim(upper, '9', 0, -1)
    rim(upper, '7', 1, 0)
    fore = fill(capsule((56, 50), (51, 55), 2.1, 1.9), '8')
    rim(fore, '9', 0, -1)
    rim(fore, '7', 0, 1)
    paint(fore, capsule((52.5, 53.8), (51.5, 54.8), 1.6, 1.6), 'o')
    hand = amap([
        # x: 46-50 51
        ".kkk. .",     # 53
        "kRTRk .",     # 54
        "kRRRV k",     # 55
        "kVRRV k",     # 56
        ".kVVk .",     # 57
    ], 46, 53)
    return [(upper, True), (fore, True), (hand, False)]


def raised_arm():
    """Frame 1: the far arm up beside his face, the gold card held between two fingers."""
    upper = fill(capsule((51, 43), (58, 45), 2.4, 2.1), '8')
    rim(upper, '9', 0, -1)
    rim(upper, '7', 0, 1)
    fore = fill(capsule((58, 45), (59.5, 38.5), 2.1, 1.9), '8')
    rim(fore, '9', -1, 0)
    paint(fore, capsule((59.3, 39.2), (59.4, 39.8), 2.0, 2.0), 'o')
    hand = amap([
        # x: 57-61 62
        ".k.k. .",     # 33  two fingertips pinching the card
        "kdkdk .",     # 34
        "kRkRk k",     # 35
        "kTRRR k",     # 36
        "kRRRV k",     # 37
        ".kVVk .",     # 38
    ], 57, 33)
    return [(upper, True), (fore, True), (hand, False)]


GOLD_CARD = [
    # x: 55-59 60-64 65
    ".kkkk kkkkk .",     # 22
    "kYYOO OOOOO k",     # 23
    "kYOOO kOOOO k",     # 24
    "kOOOk kkOOO k",     # 25
    "kOOkk kkkOO k",     # 26
    "kOOkk kkkOo k",     # 27
    "kOOkO kOkOo k",     # 28
    "kOOOO kOOOo k",     # 29
    "kOOOk kkOoo k",     # 30
    "kOOoo ooooG k",     # 31
    ".kkkk kkkkk .",     # 32
]


def gold_card():
    """The signature card: a glowing gold face with a spade cut through it, keylined like the rest,
    and the glow as a ring of light round the keyline."""
    card_px = amap(GOLD_CARD, 55, 22)
    glow = {}
    body = set(card_px)
    for (x, y) in body:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (x + dx, y + dy)
                if q not in body:
                    glow[q] = 'O'
    ring2 = {}
    for (x, y) in list(glow) + list(body):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in body and q not in glow:
                ring2[q] = 'r'
    return card_px, glow, ring2


def near_arm():
    upper = fill(capsule((32, 43), (27, 50), 2.4, 2.1), '9')
    rim(upper, '0', -1, 0)
    rim(upper, '8', 1, 0)
    fore = fill(capsule((27, 50), (21.5, 46.5), 2.0, 1.9), '9')
    rim(fore, '0', 0, -1)
    rim(fore, '8', 0, 1)
    paint(fore, capsule((22.6, 47.2), (23.2, 47.6), 1.9, 1.9), 'o')
    return upper, fore


# The fan by hand: the back card on a 45 degree lean showing a red diamond, the middle one on a 1:2
# lean showing a spade, the ace of hearts upright in front. Transparent cells stamp nothing, so the
# forearm behind it survives; the glove goes on after.
FAN = [
    # x: 6-10 11-15 16-20 21-25 26          y
    "..... ..... ..kkk kkkkk k",            # 34
    "..... .k... .kk99 99999 k",            # 35
    "..... k9k.k k9k90 00009 k",            # 36
    "....k 90kk9 90k90 00009 k",            # 37
    "...k9 kk99k 00k90 R0R09 k",            # 38
    "..k9k 990kk k0k9R TRRR9 k",            # 39
    ".k90k 900kk k0k9R RRRR9 k",            # 40
    "k90R0 k900k 00k90 RRR09 k",            # 41
    ".kRRR k9000 00k90 0R009 k",            # 42
    "..kR0 0k900 ..k90 00009 k",            # 43
    "...k9 0k9.. ..k99 99999 k",            # 44
    "....k 90k.. ..kkk kkkkk k",            # 45
    "..... k9k.. ..... ..... .",            # 46
    "..... .k99. ..... ..... .",            # 47
    "..... ..k9k ..... ..... .",            # 48
    "..... ...k. ..... ..... .",            # 49
]


def fan_old():
    """Three cards fanned on clean slopes, back to front: left leaning 1:2, upright, right 1:2."""
    back = card_poly([(15, 48), (20, 43), (13, 36), (8, 41)], MARK_DIAMOND, pip_at=(10, 40))
    mid = card_poly([(17, 47), (23, 44), (19, 36), (13, 39)], MARK_SPADE, pip_at=(14, 39))
    front = card_poly([(19, 45), (25, 45), (25, 36), (19, 36)], BIG_HEART, pip_at=(20, 38))
    return [back, mid, front]


NEAR_HAND = [
    # x: 14-18 19-23
    "..... kk...",     # 40
    "..... kdk..",     # 41  thumb up the front card, fingertip bare
    ".kkkk kck..",     # 42
    "kTRRR kRkk.",     # 43
    "kRTRR RRRVk",     # 44
    "kRRRR RRRVk",     # 45
    "kVRRR RRVVk",     # 46
    ".kVVV VVVk.",     # 47
    "..kkk kkk..",     # 48
]


HEAD = [
    # x: 31-35 36-40 41-45 46-50 51-52            y
    "..iii iiiii iiiii iiiii ..",                 # 17
    ".iiii iiiii iiiii iiiii i.",                 # 18
    "iiiii iiiii iiiii iiiii ii",                 # 19
    "lmmlj iiiii iiiii iiiij ih",                 # 20
    "mmllj ljjlj jljij ijijj ih",                 # 21
    "mlljj jcccc ccccc cccjl ih",                 # 22
    "lmljj deeed ddddd hhhjj ih",                 # 23
    "llmlj hhhhk dedch cccjj h.",                 # 24
    "lllmj dkkkk dedck kkcji h.",                 # 25
    "jlllj d0lk0 dedcl k0cjj h.",                 # 26
    "jljlj dcccd dedbc ccbji h.",                 # 27
    "ljlji eeddd dedbc ccbij h.",                 # 28
    "ljjji dpddd cddbc cciij h.",                 # 29
    "jljii idddc cbabc ciiij h.",                 # 30
    ".ijji icjjj jjjji kciih ..",                 # 31
    ".ijii iiiik kkk00 kiih. ..",                 # 32
    "..iih iiiii ppbii iiih. ..",                 # 33
    "....i jjjii iiiii iih.. ..",                 # 34
    "..... ijiii iiiii ih... ..",                 # 35
    "..... .hiii iiiih h.... ..",                 # 36
    "..... ...ab bbbaa ..... ..",                 # 37
    "..... ...aa bbaaa ..... ..",                 # 38
    "..... ....a aaa.. ..... ..",                 # 39
]


def head():
    return amap(HEAD, 31, 17)


CROWN = [
    # x: 32-36 37-41 42-46 47-51 52        y
    "....k kkkkk kkkkk kk... .",           # 5
    "...kz ZZZZz zzzyy yyk.. .",           # 6
    "..kzZ zzzzy yyoyy xxxk. .",           # 7
    "..kzZ zzzzy yokoy xxxk. .",           # 8
    "..kzZ zzzzy okkko xxxk. .",           # 9
    ".kzzZ zzzyo kkkkk oxxxk .",           # 10
    ".kzzZ zzzyo kkkkk oxxxk .",           # 11
    ".kzzz yyyyy okoko yxxxk .",           # 12
    "kzzzz yyyyy yokoy xxxxx k",           # 13
    "kOOOO OOooo ooooo GGGGG k",           # 14
    "koooo ooGGG GGGGG ggggg k",           # 15
]

BRIM = [
    # x: 20-24 25-29 30-34 35-39 40-44 45-49 50-54 55-59 60-62     y
    ".kk.. ..... ..... ..... ..... ..... ..... ..... kk.",        # 15
    "kzzkk kkkkk kkkkk kkkkk kkkkk kkkkk kkkkk kkkkk yyk",        # 16
    "kzZZZ ZZZZZ zzzzz zzzzz zzzzz yyyyy yyyyy yyyyy yyk",        # 17
    "kkkyy yyyyy yyyyy yyyyy yxxxx xxxxx xxxxx xxxxx kkk",        # 18
    "...kk kkkkk kkkkk wwwww wwwww wwwww wkkkk kkkkk ...",        # 19
    "..... ..... ..... kkkkk kkkkk kkkkk k.... ..... ...",        # 20
]


def hat():
    """Crown (with its band and the gold-rimmed spade), the card tucked in the band, and the brim.
    Returned in stamp order: (part, outline)."""
    crown = amap(CROWN, 32, 5)
    band = {p: k for p, k in crown.items() if p[1] >= 14}
    tucked = card_poly([(33, 16), (37, 14), (33, 6), (29, 8)], ['R'], face='0', border='9')
    brim = amap(BRIM, 20, 15)
    return [(crown, False), (tucked, True), (band, False), (brim, False)]


# The skirt of the duster and the legs, row by row: (y, left outer keyline, left front keyline,
# right front keyline, right outer keyline, lining width showing on the swept-back right panel).
SKIRT_ROWS = [
    (56, 29, 37, 47, 54, 1), (57, 29, 37, 47, 54, 1), (58, 29, 37, 47, 54, 1),
    (59, 28, 37, 48, 55, 1), (60, 28, 37, 48, 55, 2), (61, 28, 37, 48, 55, 2),
    (62, 27, 37, 48, 55, 2), (63, 27, 37, 48, 56, 2), (64, 27, 37, 48, 56, 2),
    (65, 27, 36, 49, 56, 3), (66, 26, 36, 49, 56, 3), (67, 26, 36, 49, 57, 3),
    (68, 26, 36, 49, 57, 3), (69, 25, 36, 49, 57, 3), (70, 25, 36, 49, 57, 3),
]
HEM_Y = 70


def skirt():
    """Both coat panels, the trousers between them, and the hem keyline, as one hand-ruled layer."""
    px = {}
    for (y, lo, lf, rf, ro, lw) in SKIRT_ROWS:
        hem = (y == HEM_Y)
        # left panel: lit edge, two folds, gold trim on the front edge
        fold_a = int(round(33 - (y - 57) * 2.0 / 13.0))
        fold_b = 35 if y < 66 else 34
        px[(lo, y)] = 'k'
        for x in range(lo + 1, lf):
            k = '9'
            if x == lo + 1:
                k = '0'
            if x == fold_a:
                k = '8'
            if x == fold_a + 1 and y >= 63:
                k = '7'
            if x == fold_b and y >= 61:
                k = '8'
            if y <= 57 and x <= lo + 4:
                k = '8'                                  # the elbow's shadow
            if hem:
                k = '7' if x in (fold_a, fold_a + 1) else '8'
            if x == lf - 1:
                k = 'o'
            px[(x, y)] = k
        px[(lf, y)] = 'k'
        # right panel: shadowed trim, the lining it is swept back to show, then the cloth
        px[(rf, y)] = 'k'
        x = rf + 1
        px[(x, y)] = 'G'
        lining = 'R' if lw == 1 else ('RV' if lw == 2 else 'RRV')
        for i, k in enumerate(lining):
            px[(x + 1 + i, y)] = 'V' if hem else k
        for xx in range(x + 1 + lw, ro):
            k = '8'
            if xx == ro - 1:
                k = '7'
            if y >= 62 and xx == ro - 3:
                k = '7'
            if hem:
                k = '7' if xx < ro - 1 else '6'
            px[(xx, y)] = k
        px[(ro, y)] = 'k'
        # the trousers between the panels (the waistcoat covers them above row 59)
        if y >= 59:
            split = 42 if y < 66 else 43
            for xx in range(lf + 1, rf):
                if y <= 60:
                    k = 'n' if xx == 42 else ('s' if xx == lf + 1 else 'N')
                elif xx == 42:
                    k = 'k'
                elif y >= 66 and xx == 43:
                    k = 'v'
                elif xx < 42:
                    k = 's' if xx == lf + 1 else ('n' if xx == 41 else 'N')
                    if y in (62, 63) and xx == lf + 2:
                        k = 'S'                          # knee
                else:
                    first = 44 if y >= 66 else 43
                    k = 's' if xx == first else ('n' if xx == rf - 1 else 'N')
                    if y in (63, 64) and xx == first + 1:
                        k = 'S'
                px[(xx, y)] = k
    # the hem keyline, and the trouser legs showing under it
    for x in range(25, 37):
        px[(x, 71)] = 'k'
    for x in range(49, 58):
        px[(x, 71)] = 'k'
    for x, k in zip(range(37, 49), 'sNNnkvsNNNnk'):
        px[(x, 71)] = k
    return px


VEST_HEM = [
    (56, 37, "ktSSS sSSSs k"),
    (57, 37, "ksSSs ksSSs k"),
    (58, 37, "kkssk Nkssk k"),
    (59, 37, "kNkkN NNkkN k"),
]


# The chest by hand: the lapels (gold-trimmed, the near one lit), the waistcoat's V and the wine
# ascot knotted under his beard. Spans are (y, x0, keys); '_' keeps what is under.
CHEST = [
    (39, 33, "___kk kk___ kkkkk __"),
    (40, 33, "k0000 okzZy xkG88 7k"),
    (41, 33, "k0090 okSzy skG88 7k"),
    (42, 33, "k0900 oktyx SkG88 7k"),
    (43, 33, "k0090 okSyx SkG87 k_"),
    (44, 33, "_k000 okSxy SkG87 k_"),
    (45, 33, "__k00 okSSx SkG7k __"),
    (46, 33, "___k0 oktSk SkGk_ __"),
    (47, 33, "____k okSSO SkGk_ __"),
]


def build_frame0():
    return build_frame(False)


def build_frame(sig):
    cv = Canvas()
    for c in collar():
        cv.stamp(c)
    cv.stamp(coat_back())
    for leg in legs():
        cv.stamp(leg)
    for b in boots():
        cv.stamp(b, outline=False)
    for c in coat_panels():
        cv.stamp(c)
    cv.stamp(vest())
    lib.patch(cv.px, CHEST)
    sk = skirt()
    for q in [q for q in cv.px if 56 <= q[1] <= 71 and 24 <= q[0] <= 58]:
        del cv.px[q]
    cv.px.update(sk)
    lib.patch(cv.px, VEST_HEM)
    if not sig:
        for part, outline in far_arm():
            cv.stamp(part, outline=outline)
    cv.stamp(head())
    for part, outline in hat():
        cv.stamp(part, outline=outline)
    up, fo = near_arm()
    cv.stamp(up)
    cv.stamp(fo)
    cv.stamp(amap(FAN, 6, 34), outline=False)
    cv.stamp(amap(NEAR_HAND, 14, 40), outline=False)
    if sig:
        for part, outline in raised_arm():
            cv.stamp(part, outline=outline)
        card_px, glow, ring2 = gold_card()
        rim_light(cv.px, set(card_px), reach=9)
        for q, k in ring2.items():
            if q not in cv.px:
                cv.px[q] = k
        for q, k in glow.items():
            if q not in cv.px:
                cv.px[q] = k
        cv.stamp(card_px, outline=False)
        for q, k in SPARKLES.items():
            if q not in cv.px:
                cv.px[q] = k
        lib.patch(cv.px, WINK)
    return cv


# Frame 1's face: the near eye shut in a wink.
WINK = [
    (25, 37, "dkkd"),
    (26, 37, "kddk"),
]

# Four-point glints thrown off the card.
SPARKLES = {}
for (sx, sy) in ((53, 22), (67, 27), (65, 36)):
    SPARKLES[(sx, sy)] = 'W'
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        SPARKLES[(sx + dx, sy + dy)] = 'Y'

# What the card's light turns each colour into, on the edges that face it.
GOLD_LIGHT = {
    'h': 'g', 'i': 'g', 'j': 'G', 'l': 'o', 'm': 'O',
    'w': 'y', 'x': 'z', 'y': 'Z', 'z': 'Z',
    '6': 'G', '7': 'o', '8': 'O', '9': 'Y', '0': 'Y',
    'v': 'V', 'V': 'R', 'R': 'T',
    'a': 'c', 'b': 'd', 'c': 'e', 'd': 'e',
    'N': 's', 's': 'S', 'S': 't',
}


def rim_light(px, source, reach):
    """Gold rim light: every drawn pixel whose keyline faces the card, within `reach` of it, takes
    the card's colour. Keylines stay black."""
    cx = sum(p[0] for p in source) / len(source)
    cy = sum(p[1] for p in source) / len(source)
    hits = []
    for (x, y), k in px.items():
        if k == 'k' or k not in GOLD_LIGHT:
            continue
        # nearest point of the card
        d = min(abs(x - sx) + abs(y - sy) for (sx, sy) in source)
        if d > reach:
            continue
        ddx = cx - x
        ddy = cy - y
        steps = []
        if abs(ddx) >= abs(ddy) * 0.5:
            steps.append((1 if ddx > 0 else -1, 0))
        if abs(ddy) >= abs(ddx) * 0.5:
            steps.append((0, 1 if ddy > 0 else -1))
        for sx, sy in steps:
            n1 = px.get((x + sx, y + sy))
            n2 = px.get((x + 2 * sx, y + 2 * sy))
            if n1 == 'k' and (n2 is None or (x + 2 * sx, y + 2 * sy) in source):
                hits.append((x, y))
                break
    for q in hits:
        px[q] = GOLD_LIGHT[px[q]]


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(lib.HERE, 'out')
    os.makedirs(out, exist_ok=True)
    im = build_frame(False).image()
    im.save(os.path.join(out, 'f0.png'))
    im1 = build_frame(True).image()
    im1.save(os.path.join(out, 'f1.png'))
    sheet = lib.Image.new('RGBA', (160, 80), (0, 0, 0, 0))
    sheet.alpha_composite(im, (0, 0))
    sheet.alpha_composite(im1, (80, 0))
    sheet.save(os.path.join(out, 'sheet.png'))
    lib.upscale(lib.on_bg(sheet), 5).save(os.path.join(out, 'sheet_5x.png'))
    print(lib.stats(im), lib.stats(im1), lib.stats(sheet))
