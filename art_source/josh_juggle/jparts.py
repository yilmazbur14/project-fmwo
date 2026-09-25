"""Josh's juggle parts, on top of his approved rig (art_source/josh_redesign, imported read-only).

Everything here is either the approved rig's own part, moved, or a face patched onto the approved
HEAD in its own coordinates the way ground_kit.FACES does it. The faces are the only new drawing:
the juggle contract asks for big comedy faces on the hit and the KO (eyes squeezed and the mouth
agape on the uppercut, a dazed face lying on the mat), which his ground sheets never needed -- their
rule was "mouth shut, at most a glint of teeth", so the open mouths below are new.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JR = os.path.join(os.path.dirname(HERE), 'josh_redesign')
if JR not in sys.path:
    sys.path.insert(0, JR)
sys.path.insert(0, HERE)

import josh3                    # noqa: E402
import lib                      # noqa: E402
import rig                      # noqa: E402
import ground_kit as gk         # noqa: E402
from lib import amap            # noqa: E402

import jkit as K                # noqa: E402

PAL = lib.PAL

# His ramps, dark -> light, as the approved rig uses them (lib.PAL).
FAMILIES = {
    'cream': '567890', 'skin': 'abcde', 'hair': 'hijlm', 'wine': 'wxyzZ',
    'crimson': 'vVRT', 'gold': 'gGoOY', 'indigo': 'nNsSt',
}
BODY_KEYS = set('abcdehijlmwxyzZvVRTnNsSt56789gGoOY0p')
FX_KEYS = set('WYOr')

# The pivot the whole figure turns on in the air: the middle of the hatless body (crown of the head
# row 15 to the soles row 79), on his waistcoat. Rig coordinates.
PIVOT = (41, 47)


# ------------------------------------------------------------------ FACES
# Spans are (y, x0, keys) on the approved HEAD (x 31-52, y 17-39); '_' keeps, '.' erases. Approved
# rows for reference (hatless): 23 deeed ddddd dhhh | 24 hhhhk dedch ccc | 25 dkkkk dedck kkc |
# 26 d0lk0 dedcl k0c | 31 moustache jjjjjjj x38-44 | 32 ikkkk00k x39-46 | chin row 36 x37-46.
SQUEEZE = [                       # > <  (ground_kit's 'wince' eyes)
    (23, 36, "dhhhe ddddd hhhjj"),
    (24, 36, "dkddd dedcc ckcjj"),
    (25, 36, "ddkkd dedck kccji"),
    (26, 36, "dkddd dedcc ckcjj"),
]
WIDE = [                          # ground_kit's 'shock' eyes: brows up, a lot of white, tiny pupils
    (22, 36, "jhhhh ccccc hhhjl"),
    (23, 36, "deeed ddddd cccjj"),
    (24, 36, "dkkkk dedck kkkjj"),
    (25, 36, "d000k dedc0 00kji"),
    (26, 36, "d0k0k dedc0 k0cjj"),
    (27, 36, "dkkkd dedbk kkbji"),
]
# The jaw dropped: a big open mouth under the moustache, upper teeth, a dark throat, the tongue, and
# the beard carried a row lower because the chin has dropped with it.
AGAPE = [
    (31, 36, "icjjj jjjjj jciih"),
    (32, 38, "ikkkk kkki"),
    (33, 38, "ik000 00ki"),
    (34, 38, "ikvvv vvki"),
    (35, 38, "ikvTT Tvki"),
    (36, 37, "hiikk kkkih"),
    (37, 38, "hhiii ihh"),
]
O_MOUTH = [                       # a small round 'oh'
    (31, 36, "icjjj jjjji jciih"),
    (32, 36, "iiiik kkkii iiih."),
    (33, 36, "iiikv vvkii iiih."),
    (34, 36, "jjjik kkiii iiih."),
]
X_EYES = [                        # knocked out: X eyes, brows gone slack
    (22, 36, "jcccc ccccc cccjl"),
    (23, 36, "deeed ddddd dcccj"),
    (24, 36, "dkdkd dedck ckcjj"),
    (25, 36, "ddkdd dedcc kccji"),
    (26, 36, "dkdkd dedck ckcjj"),
    (27, 36, "dcccd dedbc ccbji"),
]
TONGUE = [                        # mouth slack, the tongue lolling out over the beard
    (31, 36, "icjjj jjjji jciih"),
    (32, 36, "iiiik kkkkk iiih."),
    (33, 36, "iiiik TTRki iiih."),
    (34, 36, "jjjii kTRki iiih."),
    (35, 36, "ijiii ikkii iih.."),
]

FACES = {
    'agape': SQUEEZE + AGAPE,         # the hit: eyes squeezed, mouth agape
    'yell': WIDE + AGAPE,             # tumbling: eyes wide, still yelling
    'surprised': WIDE + O_MOUTH,      # the apex: limp and surprised
    'wince': list(gk.FACES['wince']),
    'ko': X_EYES + TONGUE,            # out cold on the mat
    'ko_open': X_EYES + AGAPE[:2] + TONGUE[1:],
}

# The features lifted off a turned head so they stay one pixel crisp (ground_kit.FEATURE_BOXES,
# widened to hold the open mouths): (x0, y0, x1, y1, what the lifted pixels become).
FEATURE_BOXES = [
    (36, 22, 40, 27, 'd'),
    (44, 22, 48, 27, 'c'),
    (38, 31, 46, 38, 'i'),
]
FEATURE_KEYS = set('kh0lpWbvTR')


def head(face, hatless=True):
    """The approved HEAD with an expression patched in and, with the hat gone, the crown of his hair
    (ground_kit.HAIR_TOP). Rig coordinates."""
    px = dict(josh3.head())
    lib.patch(px, FACES[face] if face in FACES else gk.FACES[face])
    if hatless:
        gk.hatless(px)
    return px


def features(px, dx=0, dy=0):
    """The feature pixels of a head drawn at (dx, dy), as (pixels, fill key) for jkit's crisp turn."""
    out = []
    for (x0, y0, x1, y1, fill) in FEATURE_BOXES:
        f = {}
        for x in range(x0 + dx, x1 + dx + 1):
            for y in range(y0 + dy, y1 + dy + 1):
                k = px.get((x, y))
                if k is not None and k in FEATURE_KEYS and not (fill == 'i' and k in 'bh'):
                    f[(x, y)] = k
        out.append((f, fill))
    return out


# ------------------------------------------------------------------ SMALL PROPS AND EFFECTS
def card(kind, cx, cy, deg):
    """A loose card, turned (ground_kit.loose_card)."""
    return gk.loose_card(kind, cx, cy, deg)


def puff(cx, cy, r):
    """A dust ball off the canvas in his cream ramp with a black rim: lit top-left, shaded low right."""
    disc = {(cx + dx, cy + dy) for dx in range(-r - 1, r + 2) for dy in range(-r - 1, r + 2)
            if dx * dx + dy * dy <= r * r + r * 0.5}
    out = {}
    for (x, y) in disc:
        if any((x + dx, y + dy) not in disc for dx, dy in K.N4):
            out[(x, y)] = 'k'
        else:
            t = (x - cx) + (y - cy)
            out[(x, y)] = '0' if t < -r * 0.5 else ('8' if t > r * 0.6 else '9')
    return out


def arc(cx, cy, r, a0, a1, ry=None, key='W'):
    return {q: key for q in K.arc_px(cx, cy, r, a0, a1, ry)}


def lines(segs, key='k'):
    out = {}
    for (x0, y0), (x1, y1) in segs:
        for q in K.line_px(int(x0), int(y0), int(x1), int(y1)):
            out[q] = key
    return out


def floor_card(x, y, kind='heart'):
    """A card lying flat on the canvas, foreshortened (anims_ground.FLOOR_CARD), its pip picked."""
    pip = {'heart': 'R', 'diamond': 'R', 'spade': 'k', 'club': 'k'}[kind]
    return amap([".kkkkkk.", "k900%s09k" % pip, "k990009k", ".kkkkkk."], x, y)
