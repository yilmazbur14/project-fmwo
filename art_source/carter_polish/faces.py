"""Carter's head in every state the combat sheets need, built on head.HEAD (never edited here).

    head_part(eye=0, jaw=0, dx=0, dy=0)  -> the front head, shifted, with the eyes at a glow level and
                                            the jaw open or shut
    neck_part(dx, dy)                    -> the neck that shows under the beard when the head lifts or
                                            moves off his shoulders (stamp it BEFORE the head)
    earring_part(dx, dy)                 -> the cross, moved with the head
    back_head_part(dx=0, dy=0)           -> the back of his head, for the back view and the rush pass
    lances(eye_centres, reach, level)    -> light leaving the eyes sideways (the eye flash)

Eye glow levels (the slits on rows 39-40 of the head map):
    -2  beaten      nearly out: dark red with one ember
    -1  strained    dim
     0  deadpan     the approved slit (pink core, red body)
     1  glaring     white core
     2  white-hot   the slit blown white, a red rim
     3  blow-out    white spilling past both corners; use with lances()
Jaw: 0 shut (the deadpan line), 1 panting (a small dark mouth), 2 open (a snarl, the jaw dropped).
"""
from lib import amap, shift, patch
import head as HD

# slit rows, left eye x 38..45 and right eye x 50..57, per glow level: (row 39, row 40)
# the black corners (x 38 left / 57 right on row 39) belong to the lash line and are included
EYE_L = {
    -2: ("k998899", "999999"),
    -1: ("k887788", "988889"),
    0: ("k7VOOV7", "877778"),
    1: ("kVOMMOV", "7VVVV7"),
    2: ("kOMMMMO", "VOOOOV"),
    3: ("OMMMMMM", "OMMMMO"),
}
EYE_R = {
    -2: ("998899k", "999999"),
    -1: ("887788k", "988889"),
    0: ("7VOOV7k", "877778"),
    1: ("VOMMOVk", "7VVVV7"),
    2: ("OMMMMOk", "VOOOOV"),
    3: ("MMMMMMO", "OMMMMO"),
}

# where the eyes are, in the unshifted head (the middle of each slit)
EYE_CENTRES = [(41.5, 39.5), (53.5, 39.5)]

# the mouth, rows 45-48 around x 42..53
JAW = {
    0: [],
    1: [(46, 44, "5kkkkkk5"), (47, 45, "kWWWWk"), (48, 46, "5kk5")],
    2: [(45, 43, "4kkkkkkkk4"), (46, 43, "kggggggggk"), (47, 44, "kWWWWWWk"), (48, 45, "kWWWWk"),
        (49, 46, "kkkk")],
}


def head_part(eye=0, jaw=0, dx=0, dy=0):
    px = amap(HD.HEAD, HD.X0, HD.Y0)
    r39l, r40l = EYE_L[eye]
    r39r, r40r = EYE_R[eye]
    edits = [(39, 38, r39l), (40, 39, r40l), (39, 51, r39r), (40, 51, r40r)]
    if eye == 3:
        # the white spills over the lids
        edits += [(38, 39, "OOOOO"), (38, 52, "OOOOO")]
    patch(px, edits)
    patch(px, JAW[jaw])
    return shift(px, dx, dy)


def earring_part(dx=0, dy=0):
    return shift(amap(HD.EARRING, 31, 43), dx, dy)


# the neck under the beard: a thick bull neck, lit on its left, stamped before the head so the
# beard's keyline lands over its top
NECK = [
    # x: 41-45 46-50 51-54      y
    "kuuuu uuuvv vvwk",        # 49
    "kttuu uuuvv vvwk",        # 50
    "kttuu uuuvv vwwk",        # 51
    "ktuuu uuvvv vwwk",        # 52
    "ktuuu uuvvv wwWk",        # 53
]


def neck_part(dx=0, dy=0, rows=5):
    """Only needed when the head has moved off his shoulders; `rows` of it show under the chin."""
    return shift(amap(NECK[:rows], 41, 49), dx, dy)


# ------------------------------------------------------------------ the back of the head

# The dome from behind: the same silhouette as the front head (ears included), lit on its upper
# left, the occiput in shadow, and the orange beard showing past the jaw on both sides - the approved
# back view did that with a dotted line that read as a chain; here it is a solid lick of beard under
# each ear, keylined.
BACK_HEAD = [
    # x: 30-34 35-39 40-44 45-49 50-54 55-59 60-64      y
    "..... ..... ....k kkkkk kk... ..... .....",       # 24
    "..... ..... .kkks sssst tukkk ..... .....",       # 25
    "..... ....k kssss sssst tuuuv kk... .....",       # 26
    "..... ...ks sssss ttttu uuuuu vvk.. .....",       # 27
    "..... ..kts ssstt ttuuu uuuuu vvwk. .....",       # 28
    "..... .ktts stttt uuuuu uuuuu vvvwk .....",       # 29
    "..... .ktts tttuu uuuuu uuuuu uvvwk .....",       # 30
    "..... ktttt tuuuu uuuuu uuuuu uvvvw k....",       # 31
    "..... kttuu uuuuu uuuuu uuuuu uvvvw k....",       # 32
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k....",       # 33
    "..... ktuuu uuuuu uuuuu uuuuv vvvvw k....",       # 34
    "...kk ktuuu uuuuu uuuuu uuuvv vvvvw kkk..",       # 35
    "..kut kuuuu uuuuu uuuuu uuvvv vvvvw kuvk.",       # 36
    "..kuv kuuuu uuuuu uuuuv vvvvv vvvww kvvk.",       # 37
    "..kuv vuuuu uuuuu uuuvv vvvvv vvwww vvvk.",       # 38
    "..kuw vuuuu uuuuu uuvvv vvvvv vwwww vwvk.",       # 39
    "..kvu kuuuu uuuuu uvvvv vvvvw wwwww kvwk.",       # 40
    "...kv kuuuu uuuuv vvvvv vvvww wwwww kwk..",       # 41
    "...kk k33kv vvvvv vvvvv vvvvw wwk44 kkk..",       # 42
    "..... k233k vvvvv vvvvw wwwww wk445 k....",       # 43
    "..... k2233 kvvvv vwwww wwwwW k4445 k....",       # 44
    "..... .k323 kwwww wwwww wwWWk 4455k .....",       # 45
    "..... .k333 kWwww wwwww wWWWk 4455k .....",       # 46
    "..... ..k23 kkWWw wwwww WWWkk 455k. .....",       # 47
    "..... ...kk kkkkk kkkkk kkkkk kkk.. .....",       # 48
]


def back_head_part(dx=0, dy=0):
    return shift(amap(BACK_HEAD, 30, 24), dx, dy)


def back_earring_part(dx=0, dy=0):
    """From behind, his right ear (and the cross) is on the screen RIGHT."""
    px = amap(HD.EARRING, 31, 43)
    return shift({(95 - x, y): k for (x, y), k in px.items()}, dx, dy)


# ------------------------------------------------------------------ light leaving the eyes

def lances(centres, reach, level, dy=0):
    """Horizontal shafts of light out of both eyes, hottest at the face: white, pink, then red,
    broken into dashes toward the tips. Returns a part to stamp UNDER the body (behind it)."""
    part = {}
    for (cx, cy) in centres:
        side = -1 if cx < 47.5 else 1
        x0 = int(round(cx + side * 4))
        y = int(round(cy + dy))
        for i in range(reach):
            x = x0 + side * i
            if i > reach * 0.55 and i % 3 == 2:
                continue
            k = 'M' if i < reach * 0.25 else ('O' if i < reach * 0.5 else ('V' if i < reach * 0.8 else '7'))
            part[(x, y)] = k
            if i < reach * 0.35 and level >= 0.9:
                part[(x, y - 1)] = 'V' if i % 2 == 0 else '7'
                part[(x, y + 1)] = '7'
    return part
