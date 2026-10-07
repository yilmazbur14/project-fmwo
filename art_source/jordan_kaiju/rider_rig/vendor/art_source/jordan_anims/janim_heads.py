"""Jordan's heads for the fight animations, in his approved v2 look.

A head is an expression's face rows (row 22 down: the approved face, rig head.HEAD / head.SHOUT, and my
variants of it, written as whole replacement rows over one of those two in the rig's head space,
columns x = 37..59, rows from y = 10) under v2's greasy hair (jv2_head.hair, columns 35..61 from row 7).
The idle and shout heads come out exactly as v2's own (checked in _selftest).

The hit and defeat heads wear FLOPPED_V2, v2's hair with the quiff knocked flat. Heads that turn
(thrown back laughing, hanging in defeat) are these same heads tilted by the callers.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import janim_base as B  # noqa: E402

RH = B.rig_head
V2H = B.jv2_head
X0, Y0 = RH.X0, RH.Y0
IDLE = B.rows_of(RH.HEAD)
SHOUT = IDLE[:22 - Y0] + B.rows_of(RH.SHOUT)


def _check(rows):
    for i, r in enumerate(rows):
        if len(r) != 23:
            raise ValueError('head row %d is %d wide: %r' % (Y0 + i, len(r), r))
    return rows


def over(base, repl):
    """base rows with {y: row} replacements (rows may run past the base's end)."""
    rows = list(base)
    for y, r in repl.items():
        i = y - Y0
        while len(rows) <= i:
            rows.append('.' * 23)
        rows[i] = r.replace(' ', '')
    return _check(rows)


#EXPRESSIONS OVER THE UPRIGHT HEAD

# Idle, admiring the box: the near eye slides toward it, the far brow cocks up and the mouth
# curls at the far corner.
ADMIRE = over(IDLE, {
    21: ".kijj ihdee eeeed djiii ik.",
    22: ".kijj idiii iiide dchhh hk.",
    23: ".kiji hchhh hhhhd ecdcc ck.",
    26: "kdaci jccWW Wlhdd ecWlh ck.",
    30: "..kij lcdjc djlji jlkkc jk.",
    31: "...ki jjclj dbkkk kkbbj ik.",
})

# Summon wind-up: the shout's brows, jaw clenched on a bar of teeth.
GRIT = over(SHOUT, {
    31: "...ki jjclj dkWWW WWWkj ik.",
    32: "...kh icjjc jkkkk kkkkc ik.",
    33: "...kh icjjc jippd dppic ik.",
})

# Summon recovery: pleased with himself, a wide grin, the brows relaxed back to the idle's.
GRIN = over(SHOUT, {
    22: ".kijj idiii iiide djiii ik.",
    23: ".kiji hchhh hhhhd echhh hk.",
    24: ".kdci icccb bbbbd edcbb ck.",
    31: "...ki jjclk kWWWW WWkkj ik.",
    32: "...kh icjjc kWWWW WWkic ik.",
    33: "...kh icjjc jkkkk kkiic ik.",
})


# Laughing (upright; the taunt tips it back): brows up, eyes squeezed into arcs over pushed-up
# cheeks, the jaw dropped two rows on a wide open mouth: upper teeth, dark, tongue, lower lip.
LAUGH = over(SHOUT, {
    21: ".kijj ihiii iiide djiii ik.",
    22: ".kijj idhhh hhhhd echhh hk.",
    23: ".kiji hcccc cccdd edccc ck.",
    24: ".kdci icckk kkcdd edckc ck.",
    25: "kdbci ickde edkdd eckdk ck.",
    26: "kdaci jccdd ddcdd eccdc ck.",
    27: "kdbci jcdcc ccddd ebccd ck.",
    31: "...ki jjclj dkWWW WWWkj ik.",
    32: "...kh icjjc jkaaa aaakc ik.",
    33: "...kh icjjc jkapp ppakc ik.",
    34: "...kh icjjc jippd dppic ik.",
    35: "....k hijcj ijihi jljic ik.",
    36: ".....k hijj ljiij ljiih k..",
    37: "......k hhi ijjjj jiiih k..",
    38: ".......k hh iiiii iiihk ...",
    39: "........ kk kkkkk kkkk. ...",
})
# The same laugh a beat later, the jaw half closed: the shout's mouth under the laughing eyes.
LAUGH_MID = over(SHOUT, {r: LAUGH[r - Y0] for r in range(21, 28)})


# The quiff knocked flat, in v2's greasy hair: the crest is gone, the top of the head sits low and
# round, and the whole front of the quiff has flopped forward over his forehead, a big oily lock
# hanging off the far side past the face's edge and down to the brow. The back of the head, the tuft
# and the rat-tail are v2's own, untouched (columns 35..44 below are copied from jv2_head.HAIR).
# Head space as v2's hair map: columns x = 35..61, rows from y = 7 ('.' is transparent).
FLOPPED_V2 = [
    # x: 35-39 40-44 45-49 50-54 55-59 60-61      y
    "..... ..... ..... ..... ..... ..",       # 7
    "..... ..... ..... ..... ..... ..",       # 8
    "..... ..... ..... ..... ..... ..",       # 9
    "..... ..... ..... ..... ..... ..",       # 10
    "..... ..... ..... ..... ..... ..",       # 11
    "..... ..... .kkkk kkk.. ..... ..",       # 12  the top, low and round now
    "..... k...k kAYAh jAYkk ..... ..",       # 13  the shine band slid forward with it
    "....k jkkkA YAhjl jhAYA kk... ..",       # 14
    "..... kAmhi ljhil jhWlA YAkk. ..",       # 15
    "....k kmjhi lWhim jhilj hlAk. ..",       # 16
    "...kj lihjW ihjmi hjlih jWlik ..",       # 17  the flop hangs past the face's edge
    "..kih jijii hiiji ihijl mljih k.",       # 18
    ".kiki iWijh cciid kilmA mljih k.",       # 19  the greasy lock over the forehead
    ".kjki iijhd eeeie dkjAl jihih k.",       # 20
    ".kiki jjihd eeeeh edkji ljihk ..",       # 21  its tip resting on the far brow
]


def _flopped_hair():
    rows = B.rows_of(FLOPPED_V2)
    for i, r in enumerate(rows):
        if len(r) != 27:
            raise ValueError('flopped row %d is %d wide' % (V2H.HY0 + i, len(r)))
    v2rows = B.rows_of(V2H.HAIR)
    for i in range(len(rows)):                       # the back of the head must stay v2's own
        if i >= 6 and rows[i][:10] != v2rows[i][:10]:
            raise ValueError('flopped row %d changed the back of the head' % (V2H.HY0 + i))
    part = B.amap(rows, V2H.HX0, V2H.HY0)
    part.update(V2H.TAIL_TIP)
    return part


# Hit, the moment it lands: eyes squeezed shut to > <, brows crushed down, teeth clenched.
PAIN = over(SHOUT, {
    24: ".kdci icccb bhhhh dhhbb ck.",
    25: "kdbci ickkc ccddd ecckk ck.",
    26: "kdaci jccck kkddd eckcc ck.",
    27: "kdbci jcckk ccddd ebckk ck.",
    31: "...ki jjclk kWWWW WWWkk ik.",
    32: "...kh icjjk kkkkk kkkkc ik.",
    33: "...kh icjjc jippd dppic ik.",
})

# Hit, recoiling: still wincing, the near eye screwed shut, the far one cracked open.
WINCE = over(SHOUT, {
    24: ".kdci icccb bhhhh dhhbb ck.",
    25: "kdbci ickkc ccddd eckkk ck.",
    26: "kdaci jccck kkddd ecWlh ck.",
    27: "kdbci jcckk ccddd ebccd ck.",
    31: "...ki jjclj dkWWW WWWkj ik.",
    32: "...kh icjjc jkkkk kkkkc ik.",
    33: "...kh icjjc jippd dppic ik.",
})

# Defeat, staggering: eyes wide and wall-eyed (the pupils drifting apart), the jaw hanging open on a
# gasp.
DAZE = over(IDLE, {
    26: "kdaci jcchW WWWdd ecWWh ck.",
    31: "...ki jjclj dbkkk kkbij ik.",
    32: "...kh icjjc jbkaa akbic ik.",
    33: "....k hijcj jijkk kjjic ik.",
})

# Defeat, beaten: eyes shut (just the lid line), the mouth sagging at the corners. The defeat frames
# tip it forward so his head hangs.
DROOP = over(IDLE, {
    22: ".kijj idiii iiide djiii ik.",
    23: ".kiji hchhh hhhhd echhh hk.",
    24: ".kdci icccc ccccd edccc ck.",
    25: "kdbci ickkk kkkdd eckkk ck.",
    26: "kdaci jcccc cccdd ecccc ck.",
    31: "...ki jjclj dbdkk kkdbj ik.",
    32: "...kh icjjc jikpd pkijc ik.",
})


def rows(name):
    return {'idle': IDLE, 'shout': SHOUT, 'admire': ADMIRE, 'grit': GRIT, 'grin': GRIN,
            'laugh': LAUGH, 'laugh_mid': LAUGH_MID, 'pain': PAIN, 'wince': WINCE,
            'daze': DAZE, 'droop': DROOP}[name]


# The hit and defeat heads wear the flopped quiff; the rest wear v2's hair as approved.
FLOPPED = {'pain', 'wince', 'daze', 'droop'}

# Expressions whose brows rise into row 21, which is v2's hair row: the brow pixels laid over it,
# butting against the greasy forelock's tip (the admire cocks the far brow, the laugh lifts both).
ROW21 = {
    'admire': {(x, 21): 'i' for x in range(54, 58)},
    'laugh': {(x, 21): 'i' for x in list(range(44, 50)) + list(range(54, 58))},
    'laugh_mid': {(x, 21): 'i' for x in list(range(44, 50)) + list(range(54, 58))},
}


def head(name='idle', dx=0, dy=0):
    """A head in v2's look, as a part (in build coordinates when dx, dy are the frame's offsets):
    the expression's face rows (row 22 down, the approved face and my variants of it) under v2's
    greasy hair, or under the flopped version of it for the hit and defeat heads."""
    face = {q: k for q, k in B.amap(rows(name), X0, Y0).items() if q[1] >= 22}
    part = dict(face)
    part.update(_flopped_hair() if name in FLOPPED else V2H.hair())
    part.update(ROW21.get(name, {}))
    return B.shift(part, dx, dy)


def _selftest():
    ok = head('idle') == V2H.head(False) and head('shout') == V2H.head(True)
    print('idle / shout heads match the approved v2 heads:', ok)
    return ok


if __name__ == '__main__':
    sys.exit(0 if _selftest() else 1)
