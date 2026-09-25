"""Captain Burak's head: his face (15-18.jpg), hair and the tricorn. Front view, column 48 the axis,
lit from the upper left like the rest of the cast. Sized to Matt's intro standard: a big face with
bold black features that read from across the arena at 3x.

Likeness notes from the photos:
  - thick, voluminous, wavy near-black hair parted near the middle, curtain bangs in heavy locks
    over the forehead; the screen-right curtain drops a lock over that brow; the sides sit close
  - thick straight dark brows sitting low over heavy-lidded brown eyes (the unimpressed smoulder)
  - a straight nose, a full lower lip, light-tan skin, a slightly rounded jaw
  - light patchy stubble: a moustache shadow and chin/jaw specks, never a full beard
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import amap, curve, ellipse, ellipsoid, fill, lock, poly, rect, shade_lock  # noqa: E402

# ------------------------------------------------------------------ face

# Skin x 35-61 (keylined at 34 and 62 when stamped), forehead from y 19, chin keyline on y 49.
FACE_OUTLINE = [(35, 19), (61, 19), (61, 40), (60.6, 42.6), (59.2, 45), (56.6, 47.1), (53, 48.2),
                (48, 48.5), (43, 48.2), (39.4, 47.1), (36.8, 45), (35.4, 42.6), (35, 40)]


def face_base():
    """Clean anime planes like Matt's: a lit left edge, a flat base, a shadow down the right side and
    under the jaw, a highlight on the near cheekbone."""
    part = fill(poly(FACE_OUTLINE), '3')
    for (x, y) in list(part):
        xs = [xx for (xx, yy) in part if yy == y]
        lo, hi = min(xs), max(xs)
        t = (x - lo) / max(1, hi - lo)
        k = '2' if t < 0.1 else ('3' if t < 0.72 else ('4' if t < 0.9 else '5'))
        if y >= 46 and k in '23':
            k = '4'                                  # the jaw turning under
        if y >= 47 and k == '4' and t > 0.55:
            k = '5'
        part[(x, y)] = k
    for q in ((37, 36), (38, 36), (37, 37)):
        part[q] = '2'                                # the near cheekbone catches the light
    part[(37, 36)] = '1'
    for q in ((56, 36), (57, 36), (56, 37), (57, 37), (57, 38)):
        part[q] = '4'                                # the far cheek turns away
    return part


# Feature overlays, x 36-60, from y 28. '.' keeps the skin underneath. Black brows, black upper lids,
# black mouth lines: the features are drawn to read at 3x from across the ring.
FEAT_X0, FEAT_Y0 = 36, 28

# Idle: the unimpressed smoulder. Left brow level, right brow cocked up; heavy flat black lids cut the
# tops of his brown irises; a big lopsided smirk that curls up on his left (screen right) and bares
# the teeth there.
IDLE = [
    # x: 36-40 41-45 46-50 51-55 56-60      y
    "..... ..... ..... ....h hhh..",       # 28  the cocked brow's arch
    "...hh hhhhh ..... hhhhk kkki.",       # 29  thick brows
    ".kkkk kkkkk ..... kkkk. .....",       # 30
    "..444 4444. ..... .4444 444..",       # 31  lids in the brows' shadow
    "..kkk kkkk. ..... .kkkk kkk..",       # 32  heavy upper lids
    "..kW9 k9W4. ..... .4W9k 9Wk..",       # 33  brown irises under the lid
    "...49 994.. ..... ..499 94...",       # 34  lower lids
    "..... ..... .2... ..... .....",       # 35  nose bridge
    "..... ..... .2.4. ..... .....",       # 36
    "..... ..... .2.44 ..... .....",       # 37
    "..... ..... 31245 ..... .....",       # 38  nose tip
    "..... ....4 65565 ..... .....",       # 39  nostrils
    "..... ..s.s s.ss. ....k k....",       # 40  moustache shadow; the smirk hooks up hard
    "..... ..... ..... kkkk. 5....",       # 41  ...on his left (screen right), a dimple crease
    "..... .kkkk kkkkk ..... 5....",       # 42  mouth line, closed and flat on the other side
    "..... ..4pp ppp4. ..... .....",       # 43  full lower lip
    "..... ...44 444.. ..... .....",       # 44
    "..... ....s .s.s. ..... .....",       # 45  chin stubble, light and patchy
    "..... ..... s...s ..... .....",       # 46
]

# The shot: a cocky wink over a huge toothy grin (16.jpg / 17.jpg).
SHOT = [
    # x: 36-40 41-45 46-50 51-55 56-60      y
    "..... ..... ..... ....h hhh..",       # 28  the open eye's brow cocked high
    "..... ..... ..... hhhhk kkki.",       # 29
    "..hhh hhhhh ..... kkkk. .....",       # 30  the winking side's brow pulled down
    ".kkkk kkkk. ..... .4444 444..",       # 31
    "....k kk... ..... .kkkk kkk..",       # 32  the wink: a shut, smiling lid
    "...k. ..k.. ..... .4W9k 9Wk..",       # 33
    "..k.. ...k. ..... ..499 94...",       # 34
    "..... ..... .2... ..... .....",       # 35
    "..... ..... .2.4. ..... .....",       # 36
    "..... ..... .2.44 ..... .....",       # 37
    "..... ..... 31245 ..... .....",       # 38
    "..... k...4 65565 ....k .....",       # 39  the grin's corners pulled up
    "..... kkkkk kkkkk kkkkk .....",       # 40  upper lip
    "..... kWWWW WWWWW WWWWk .....",       # 41  upper teeth
    "..... keWWW WWWWW WWWek .....",       # 42
    "..... .kxxy yyyyy yxxk. .....",       # 43  mouth, tongue
    "..... ..kpp ppppp ppk.. .....",       # 44  lower lip
    "..... ...kk kkkkk kk... .....",       # 45
    "..... ...s. s.s.s .s... .....",       # 46  chin stubble
]


def features(expr='idle'):
    return amap(IDLE if expr == 'idle' else SHOT, FEAT_X0, FEAT_Y0)


def ears():
    """Ear interiors (keylined when stamped): the left lit, the right in shade."""
    left = {(32, 32): '3', (33, 32): '2', (31, 33): '4', (32, 33): '5', (33, 33): '2', (31, 34): '4',
            (32, 34): '5', (33, 34): '3', (31, 35): '4', (32, 35): '4', (33, 35): '3', (32, 36): '4',
            (33, 36): '3', (33, 37): '4'}
    right = {(96 - x, y): {'2': '4', '3': '4', '4': '5', '5': '6'}[k] for (x, y), k in left.items()}
    return left, right


def neck():
    n = fill(rect(42, 44, 54, 54), '4')
    for (x, y) in list(n):
        if y <= 49:
            n[(x, y)] = '5' if x < 52 else '6'     # in the jaw's shadow
        elif x >= 52:
            n[(x, y)] = '5'
        elif x <= 44:
            n[(x, y)] = '3'
    return n


# ------------------------------------------------------------------ hair

# The lowest hair row in each column: the curtain bangs' lower edge, the side hair, the sideburns.
HAIR_LOW = {29: 27, 30: 30, 31: 31, 32: 31, 33: 32, 34: 35, 35: 36, 36: 30, 37: 28, 38: 27, 39: 27,
            40: 26, 41: 26, 42: 25, 43: 24, 44: 23, 45: 22, 46: 21, 47: 20, 48: 20, 49: 21, 50: 23,
            51: 28, 52: 31, 53: 32, 54: 31, 55: 24, 56: 24, 57: 24, 58: 25, 59: 26, 60: 30, 61: 36,
            62: 35, 63: 32, 64: 31, 65: 31, 66: 30, 67: 27}


# The curtains, as (base, tip, half-width at base, at tip, bow). Drawn back to front: the outer locks
# first, the front curtain locks last, each one's edge seamed dark where it lies over another.
LOCKS_LEFT = [
    ((38, 12), (29, 31), 3.5, 1.2, -2.0),    # outer side lock, over the ear
    ((43, 13), (31, 26), 3.8, 1.0, -3.0),    # middle
    ((47, 17), (35, 28), 3.4, 0.8, -3.0),    # front curtain: its lower edge frames the forehead
]
LOCKS_RIGHT = [
    ((58, 12), (67, 31), 3.5, 1.2, 2.0),     # outer side lock
    ((53, 13), (65, 26), 3.8, 1.0, 3.0),     # middle
    ((49, 17), (62, 24), 2.8, 0.8, 3.0),     # front curtain, lifted clear of the cocked brow
    ((49, 18), (52, 31), 2.2, 0.6, 1.5),     # the heavy lock that falls over the brow (15.jpg)
]


def hair_back():
    """The dark mass behind the locks: fills up under the brim and down the sides to the ears."""
    shape = ellipse(48, 22, 18.6, 12.5) | rect(30, 20, 66, 29) | rect(31, 11, 65, 20)
    shape = {(x, y) for (x, y) in shape if y <= HAIR_LOW.get(x, -1)}
    return fill(shape, 'i')


def hair_locks():
    parts = []
    for spec in LOCKS_LEFT + LOCKS_RIGHT:
        info = lock(*spec)
        parts.append(shade_lock(info, 'mljih', (0.93, 0.78, 0.45, 0.05)))
    return parts


def hair():
    """One part: the back mass with the locks laid over it, seamed where they overlap."""
    part = hair_back()
    for lk in hair_locks():
        for (x, y) in lk:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in part and q not in lk:
                    part[q] = 'h'
        part.update(lk)
    return part


# Loose flyaway strands curling off the sides of his hair (17.jpg), fine enough to stay 1px.
FLYAWAYS = {(30, 15): 'k', (29, 14): 'k', (28, 14): 'k', (27, 15): 'k',
            (66, 26): 'k', (67, 25): 'k', (68, 25): 'k', (69, 26): 'k', (69, 27): 'k'}


def flyaways():
    return dict(FLYAWAYS)


# ------------------------------------------------------------------ tricorn

# Built as the left half (x 23-48) and mirrored about column 48. Tilted back on his hair: black felt,
# a gold-trimmed brim sweeping in a V from each upturned tip down to a sharp front point, the front
# walls' felt under the trim, the crown doming up between the tips.
#   TOP:  the silhouette's first row (a keyline)      TRIM: the gold trim's top row
# The brim band under the keyline above the trim is: trim, trim underside, then felt rows, then the
# bottom keyline. It narrows toward the tip so the tip comes to a point.
TOP = {24: 1, 25: 2, 26: 3, 27: 4, 28: 5, 29: 6, 30: 6, 31: 6, 32: 6, 33: 5, 34: 4, 35: 3, 36: 3,
       37: 2, 38: 2, 39: 2, 40: 1, 41: 1, 42: 1, 43: 1, 44: 1, 45: 1, 46: 1, 47: 1, 48: 1}
TRIM = {24: 2, 25: 3, 26: 4, 27: 5, 28: 6, 29: 7, 30: 7, 31: 7, 32: 8, 33: 8, 34: 8, 35: 9, 36: 9,
        37: 9, 38: 10, 39: 10, 40: 10, 41: 11, 42: 11, 43: 11, 44: 12, 45: 12, 46: 13, 47: 13, 48: 14}
BAND = {24: 0, 25: 1, 26: 2, 27: 3}                      # rows under the trim near the tip (else 3)


def hat_left():
    part = {}
    for x, t in TRIM.items():
        top = TOP[x]
        band = BAND.get(x, 3)                            # trim underside + felt rows
        part[(x, top)] = 'k'
        for y in range(top + 1, t - 1):                  # crown / back wall
            u = (x - 43.0) / 10.0
            v = (y - 2.0) / 8.0
            d = u * 0.8 + v
            part[(x, y)] = 'u' if d < -0.35 else ('t' if d < 0.3 else 'r')
        if t - 1 > top:
            part[(x, t - 1)] = 'k'
        part[(x, t)] = 'Y' if x >= 46 else 'O'
        rows = ['o' if x >= 36 else 'G', 't' if x < 40 else 'r', 'q'][:band]
        for i, k in enumerate(rows):
            part[(x, t + 1 + i)] = k
        part[(x, t + 1 + band)] = 'k'
    part[(23, 1)] = 'k'                                  # the tip's point
    part[(23, 2)] = 'k'
    return part


def hat(tilt=0.0):
    left = hat_left()
    part = dict(left)
    for (x, y), k in left.items():
        if x != 48:
            part[(96 - x, y)] = k
    # the right-front wall faces away from the light: darken it, and dim its trim
    darker = {'u': 't', 't': 'r', 'r': 'q', 'Y': 'O', 'O': 'o', 'o': 'G', 'G': 'g'}
    for (x, y), k in list(part.items()):
        if x > 48 and k in darker:
            part[(x, y)] = darker[k]
    # the crown is one rounded dome: shade it as a whole, lit from the upper left
    for (x, y) in list(part):
        xl = x if x <= 48 else 96 - x
        if xl in TRIM and TOP[xl] < y < TRIM[xl] - 1:
            u, v = (x - 48.0) / 15.0, (y - 7.0) / 7.5
            z = max(0.0, 1.0 - u * u - v * v) ** 0.5
            i = (u * -0.55 + v * -0.62 + z * 0.56) / max(1e-6, (u * u + v * v + z * z) ** 0.5)
            part[(x, y)] = 'u' if i > 0.62 else ('t' if i > 0.3 else ('r' if i > -0.05 else 'q'))
    if tilt:
        part = {(x, y + int(round((x - 48) * tilt))): k for (x, y), k in part.items()}
    return part
