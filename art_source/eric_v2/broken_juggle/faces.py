"""Face features for Eric's v2 head, drawn after the head is placed at any angle.

Every feature is authored in IDLE FRAME pixels (where it sits when the head is upright at the idle
neck point, e.g. his eyes are on row 131-132) and is mapped through the head transform, so it turns
with the head. Lines are re-rasterised 1 px thick at the new angle; single pixels map to their
nearest pixel. Colours are palette chars (lib.PALC)."""
import math
import lib
from lib import PALC, BLACK
import jr

NX, NY = jr.NECK_F


def _map(ht, x, y):
    X, Y = ht.local(x + 0.5 - NX, y + 0.5 - NY)
    return int(math.floor(X)), int(math.floor(Y))


def _put(lay, lab, X, Y, ch, anywhere=False):
    if not (0 <= X < jr.FW and 0 <= Y < jr.FH):
        return
    if not anywhere and (X, Y) not in lab:
        return
    lay.px[Y][X] = PALC[ch]


def draw(lay, ht, feats, lab=None, anywhere=False):
    """feats: list of (kind, ch, data):
        ('px', ch, [(x, y), ...])            single pixels
        ('ln', ch, [(x0, y0), (x1, y1), ...]) 1 px polyline through pixel centres
        ('fill', ch, [(x, y), ...])          polygon in continuous idle-frame coords
    """
    if lab is None:
        lab = jr.head_labels(ht)
    for kind, ch, data in feats:
        if kind == 'px':
            for x, y in data:
                _put(lay, lab, *_map(ht, x, y), ch, anywhere)
        elif kind == 'ln':
            pts = [ht.local(x + 0.5 - NX, y + 0.5 - NY) for x, y in data]
            for X, Y in jr.polyline(pts):
                _put(lay, lab, X, Y, ch, anywhere)
        elif kind == 'fill':
            jr.wf()
            m = lib.poly([ht.local(x - NX, y - NY) for x, y in data])
            for Y in range(jr.FH):
                for X in range(jr.FW):
                    if m[Y][X]:
                        _put(lay, lab, X, Y, ch, anywhere)


def run(x0, x1, y):
    return [(x, y) for x in range(x0, x1 + 1)]


# ---------------------------------------------------------------- the approved idle glare (head_s FACE_FIX)
IDLE = [
    ('px', '5', [(120, 129), (121, 129), (134, 129), (135, 129)] + run(121, 123, 130) + run(132, 134, 130)
     + [(124, 131), (125, 131), (130, 131), (131, 131)]),
    ('px', 'k', run(121, 123, 131) + run(132, 134, 131) + [(124, 132), (131, 132)] + run(125, 130, 140)),
    ('px', 'e', [(121, 132), (134, 132)]),
    ('px', 'b', [(122, 132), (123, 132), (132, 132), (133, 132)]),
    ('px', 'u', run(121, 123, 133) + run(132, 134, 133)),
]

# ---------------------------------------------------------------- worn out (rig2 FACE_TIRED, panting)
TIRED = [
    ('px', '5', [(120, 129), (121, 129), (134, 129), (135, 129)] + run(121, 123, 130) + run(132, 134, 130)),
    ('px', 'n', [(122, 130), (123, 130), (132, 130), (133, 130)]),
    ('px', 'k', run(121, 124, 131) + run(131, 134, 131)),
    ('px', 'k', [(121, 132), (122, 132), (124, 132), (131, 132), (133, 132), (134, 132)]),
    ('px', 'b', [(123, 132), (132, 132)]),
    ('px', 'u', run(121, 123, 133) + run(132, 134, 133)),
    ('px', 'k', run(125, 130, 139)),
    ('px', '6', run(125, 130, 140) + run(126, 129, 141)),
    ('px', 'k', [(124, 140), (131, 140), (125, 141), (130, 141), (126, 142), (129, 142)]),
    ('px', 'P', [(127, 142), (128, 142)]),
]

# ---------------------------------------------------------------- shock (reel): brows flung up, pin-prick pupils, mouth open
SHOCK = [
    ('ln', '5', [(119, 130), (121, 128), (124, 128)]),
    ('ln', '5', [(131, 128), (134, 128), (136, 130)]),
    ('px', 'k', run(121, 124, 130) + run(131, 134, 130)),
    ('px', 'e', run(121, 124, 131) + run(131, 134, 131) + run(121, 124, 132) + run(131, 134, 132)),
    ('px', 'b', [(123, 131), (132, 131)]),
    ('px', 'k', [(120, 131), (120, 132), (125, 131), (125, 132), (130, 131), (130, 132), (135, 131), (135, 132)]),
    ('px', 'k', run(121, 124, 133) + run(131, 134, 133)),
    ('px', 'k', run(125, 130, 139) + [(124, 140), (131, 140), (124, 141), (131, 141), (124, 142), (131, 142)]
     + run(125, 130, 143)),
    ('px', '6', run(125, 130, 140) + run(125, 130, 141) + run(125, 130, 142)),
    ('px', 'e', run(126, 129, 140)),
    ('px', 'P', [(127, 142), (128, 142)]),
]

# ---------------------------------------------------------------- pain (hit / crash): eyes screwed shut, teeth gritted
PAIN = [
    ('ln', '5', [(119, 128), (122, 129), (124, 131)]),
    ('ln', '5', [(136, 128), (133, 129), (131, 131)]),
    ('ln', 'k', [(120, 130), (123, 131), (120, 133)]),
    ('ln', 'k', [(135, 130), (132, 131), (135, 133)]),
    ('px', 'k', run(124, 131, 139) + run(124, 131, 142) + [(123, 140), (123, 141), (132, 140), (132, 141)]),
    ('px', 'e', run(124, 131, 140) + run(124, 131, 141)),
    ('px', 'k', [(126, 140), (126, 141), (129, 140), (129, 141)]),
]

# ---------------------------------------------------------------- dazed / KO: spiral eyes, jaw hanging, tongue out
SPIRAL_L = [(121, 129), (122, 129), (123, 129), (124, 130), (124, 131), (124, 132), (123, 133), (122, 133),
            (121, 133), (120, 132), (120, 131), (121, 130), (122, 131)]
SPIRAL_R = [(134, 129), (133, 129), (132, 129), (131, 130), (131, 131), (131, 132), (132, 133), (133, 133),
            (134, 133), (135, 132), (135, 131), (134, 130), (133, 131)]
DAZED = [
    ('ln', '5', [(119, 128), (121, 127), (124, 127)]),
    ('ln', '5', [(131, 127), (134, 127), (136, 128)]),
    ('px', 'e', run(121, 123, 130) + run(121, 123, 131) + run(121, 123, 132) + run(132, 134, 130)
     + run(132, 134, 131) + run(132, 134, 132)),
    ('px', 'k', SPIRAL_L + SPIRAL_R),
    ('px', 'k', run(125, 130, 139) + [(124, 140), (131, 140), (124, 141), (131, 141), (125, 142), (130, 142)]
     + run(126, 129, 143)),
    ('px', '6', run(125, 130, 140) + run(125, 130, 141) + run(126, 129, 142)),
    ('px', 'P', [(127, 142), (128, 142), (127, 143), (128, 143)]),
    ('px', 'x', [(127, 142)]),
    ('px', 'k', [(126, 144), (129, 144), (127, 145), (128, 145)]),
    ('px', 'P', [(127, 144), (128, 144)]),
]

# ---------------------------------------------------------------- groggy (kneel): half-lidded unfocused eyes, slack mouth
GROGGY = [
    ('ln', '5', [(119, 129), (121, 128), (124, 129)]),
    ('ln', '5', [(131, 129), (134, 128), (136, 129)]),
    ('px', 'k', run(121, 124, 131) + run(131, 134, 131)),
    ('px', 'e', [(121, 132), (124, 132), (131, 132), (134, 132)]),
    ('px', 'b', [(122, 132), (123, 132), (132, 132), (133, 132)]),
    ('px', 'u', run(121, 124, 133) + run(131, 134, 133)),
    ('px', 'k', run(125, 130, 139) + [(125, 140), (130, 140), (126, 141), (129, 141)]),
    ('px', '6', run(126, 129, 140) + [(127, 141), (128, 141)]),
]

EXPR = {'idle': IDLE, 'tired': TIRED, 'shock': SHOCK, 'pain': PAIN, 'dazed': DAZED, 'groggy': GROGGY}


def expr(name):
    feats = EXPR[name]

    def fn(lay, ht, lab):
        draw(lay, ht, feats, lab)
    return fn
