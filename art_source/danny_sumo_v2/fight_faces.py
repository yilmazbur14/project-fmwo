"""New expressions for Danny's fight sheets (2026-09-24), in the approved rig's own map format.

Every map is placed where the approved ones are (face.py / anim.py): eyes 14 x 7 at x 66 (viewer's
left) and 96 (right, the mirror one tone down), mouths 20 wide at (78, 43). Keys are sumo_lib.PAL's.

Reused, not redrawn: the juggle's EYE_SQUEEZE / EYE_X (art_source/danny_juggle/dparts.py, approved
2026-09-23) are copied here verbatim so this rig does not import the juggle's machinery just for them.

New drawing:
  MOUTH_PURSE   lips pressed shut round a mouthful (the cheeks puff: see fight.head's `puff`)
  MOUTH_SPIT    the jaw dropped wide for the spit (the chin comes down with it: fight.head's `jaw`)
  MOUTH_SMIRK   the sleepy-smug block: the frown's line with its left corner curled up
  MOUTH_SNORE   asleep, mouth a little open
  MOUTH_GRIT    the strain: the approved clenched teeth ('ow'), set wider
  SWEAT, DROOL  small keylined drops, in the knit's light blues (water)
"""
import anim
import face as F

# ------------------------------------------------------------------ EYES (from the approved juggle)
EYE_SQUEEZE_L = [
    "..33. ..... ....",
    "..kkk k.... ....",
    "....k kkk.. ....",
    "..... .kkkk k...",
    "....k kkk.. ....",
    "..kkk k.... ....",
    "..33. ..... ....",
]
EYE_X_L = [
    "...kk ....k k...",
    "....k k..kk ....",
    ".... .kkkk. ....",
    ".... .kkkk. ....",
    "....k k..kk ....",
    "...kk ....k k...",
    "..33. ...33 ....",
]

# The eyes squeezed shut in his SLEEP: the approved sleepy lid, pressed down into a crumpled line (a
# grimace that never opens). The lash bar bends down at both ends; the lid above bunches.
EYE_SCRUNCH_L = [
    # x: 0-4   5-9   10-13
    "..333 33333 3...",    # 0 crease, pushed up
    ".3544 45554 43..",    # 1 the lid bunched (darker than the calm lid)
    "k5555 55555 55k.",    # 2
    ".kkkk kkkkk kkk.",    # 3 the lash, pressed flat
    "k..kk kkkkk k..k",    # 4 its ends bent down: screwed tight
    "..4.. ..... .4..",    # 5
    "...44 45554 4...",    # 6 bag
]


# Sleepy-smug: the lid dead flat and heavy across the top half of the eye, the pupil sunk to the
# bottom of what shows, looking down at whoever is in front of him. Unimpressed.
EYE_LAZY_L = [
    # x: 0-4   5-9   10-13
    "..333 33333 3...",    # 0 crease
    ".3566 67776 63..",    # 1 the heavy lid
    "kkkkk kkkkk kkkk",    # 2 its edge, dead level
    ".kWWW WWWWW Wkk.",    # 3 the white under it
    "..kWW WWUUW kk..",    # 4 the pupil at the bottom, toward the nose
    "...kk kkkkk k4..",    # 5 lower lid
    "...44 45554 4...",    # 6 bag
]


def _pad(rows, w):
    return [r.replace(' ', '') + '.' * (w - len(r.replace(' ', ''))) for r in rows]


def _mirror_eye(rows):
    return [''.join(F.DOWN.get(c, c) for c in r[::-1]) for r in rows]


# ------------------------------------------------------------------ MOUTHS (20 wide, at x 78)
MOUTH_PURSE = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 43 under the nose
    "..... ..... ..... .....",    # 44
    "..... ..kkk kk... .....",    # 45 the pucker: lips pushed out round a mouthful
    "..... .k567 64k.. .....",    # 46 lit on the upper left
    "..... .k445 43k.. .....",    # 47
    "..... ..kkk kk... .....",    # 48
    "..... ..344 3.... .....",    # 49 its shadow on the chin
]
MOUTH_SPIT = [
    # x: 78-82 83-87 88-92 93-97   (the chin drops 3 px with it: fight.head jaw=3)
    "..... 33333 333.. .....",    # 43 under the nose
    "...kk kkkkk kkkkk kk...",    # 44 upper lip
    "..kWW WhWWW hWWWh WWk..",    # 45 upper teeth
    ".k11W 11111 11111 W11k.",    # 46 the throat
    ".k111 11111 11111 111k.",    # 47
    ".k111 11111 11111 111k.",    # 48
    ".k111 11rrr rrrr1 111k.",    # 49 the tongue, pushed forward
    "..k11 1rrrr rrrrr 11k..",    # 50
    "..k11 1rrRR RRrrr 11k..",    # 51
    "...k1 1rrRR RRRr1 1k...",    # 52
    "....k kk111 111kk k....",    # 53
    "..... .4kkk kkk4. .....",    # 54 lower lip
]
MOUTH_SMIRK = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 43
    "kk... ..... ..... .....",    # 44 the left corner hooked up into the cheek
    ".3kk. ..... ..... .....",    # 45
    "...kk kkkkk kkkkk .....",    # 46 the line, level
    "..... 45566 6655k k....",    # 47 the right end tucked down: smug, not happy
    "..... .4455 544.. .....",    # 48
    "..... ..444 44... .....",    # 49
]
MOUTH_SNORE = [
    # x: 78-82 83-87 88-92 93-97
    "..... 33333 333.. .....",    # 43
    "..... ..... ..... .....",    # 44
    "..... .kkkk kk... .....",    # 45 a slack little O
    "..... k1111 11k.. .....",    # 46
    "..... k11rr r1k.. .....",    # 47
    "..... .k111 1k... .....",    # 48
    "..... .4kkk k4... .....",    # 49 lower lip
    "..... ..444 4.... .....",    # 50
]
MOUTH_GRIT = [
    # x: 78-82 83-87 88-92 93-97   the approved clenched teeth ('ow'), drawn a pixel wider each side
    "..... 33333 333.. .....",    # 43
    "..kkk kkkkk kkkkk kkk..",    # 44
    ".kWWk WWWkW WWkWW WkWk.",    # 45 teeth clenched
    ".khhk hhhkh hhkhh hkhk.",    # 46
    "..kkk kkkkk kkkkk kkk..",    # 47
    "...44 44444 44444 44...",    # 48
]

# a sweat drop: pointed top, round bottom, a glint on its lit left
SWEAT = [
    "..k..",
    ".kxk.",
    ".kwk.",
    "kxwvk",
    "kwvvk",
    "kvvuk",
    ".kkk.",
]
# drool hanging from the corner of a sleeping mouth
DROOL = [
    "kk.",
    "kxk",
    "kwk",
    "kwk",
    "kvk",
    ".k.",
]

# one pixel wider than the others: checked like the approved maps
for _rows, _n in ((EYE_SQUEEZE_L, 'EYE_SQUEEZE_L'), (EYE_X_L, 'EYE_X_L'), (EYE_SCRUNCH_L, 'EYE_SCRUNCH_L'),
                  (EYE_LAZY_L, 'EYE_LAZY_L'),
                  (MOUTH_PURSE, 'MOUTH_PURSE'), (MOUTH_SPIT, 'MOUTH_SPIT'), (MOUTH_SMIRK, 'MOUTH_SMIRK'),
                  (MOUTH_SNORE, 'MOUTH_SNORE'), (MOUTH_GRIT, 'MOUTH_GRIT'), (SWEAT, 'SWEAT'), (DROOL, 'DROOL')):
    F._check(_rows, _n)


def install():
    """Add the new maps to the approved rig's lookup tables, in memory only (anim.py is not edited).
    The juggle's 'squeeze' and 'x' go in under the same names and rows the juggle uses."""
    for name, rows, top in (('squeeze', EYE_SQUEEZE_L, 28), ('x', EYE_X_L, 29), ('scrunch', EYE_SCRUNCH_L, 28),
                            ('lazy', EYE_LAZY_L, 28)):
        left = _pad(rows, 14)
        anim.EYES.setdefault(name, (left, _mirror_eye(left), top))
    for name, rows in (('purse', MOUTH_PURSE), ('spit', MOUTH_SPIT), ('smirk', MOUTH_SMIRK),
                       ('snore', MOUTH_SNORE), ('grit', MOUTH_GRIT)):
        anim.MOUTHS.setdefault(name, rows)


install()
