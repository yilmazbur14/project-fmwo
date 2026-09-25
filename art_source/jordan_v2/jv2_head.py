"""Jordan v2's head: the approved face exactly as it is (rig head rows 22 and down, idle and shout),
under new hair.

The hair is his swept-up quiff on the approved outline (the dome rising to the crest at the front,
the small flick at the back of the crown, the tuft at the back), made greasy:
  - a darker, oily body (the ramp pushed down to h / i / j) cut into clumps by dark grooves;
  - a hard shine band along the quiff (Y cores, A round them), broken by the grooves: the wet look;
  - a greasy forelock fallen out of the quiff, stuck to the right of his forehead;
  - a loose strand stuck to the forehead on the near side;
  - a lank rat-tail hanging off the back of the head, behind the ear;
  - flakes of dandruff (W) in the dark of the hair (and on his shoulders, in jv2_body).

Head space as the rig's: rows from y = 7, columns x = 35..61; '.' is transparent. The hair map
replaces the rig head's rows 10..21 whole (the rig's tufts and sheen are not used).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jv2_base as B  # noqa: E402

RH = B.rig_head
HX0, HY0 = 35, 7

HAIR = [
    # x: 35-39 40-44 45-49 50-54 55-59 60-61      y
    "..... ..... ..... ..... ...kk ..",       # 7   the crest, a greasy clump flicking forward
    "..... ..... ..... ..... ..klj k.",       # 8
    "..... ..... ..... ..k.. .klAi k.",       # 9
    "..... ..... ..... .kmkk kAYih k.",       # 10  the oily shine band runs along the quiff,
    "..... ..... ..... kkjkA Yljih k.",       # 11  broken into clumps by dark grooves
    "..... ..... ..kkk mAYhl Ajihk ..",       # 12
    "..... k...k kkAYA hiljh iljik ..",       # 13
    "....k jkkkA YAhjl jhilj hijhk ..",       # 14
    "..... kAmhi ljhil jhWlj hihhk ..",       # 15  flakes of dandruff (W)
    "....k kmjhi lWhim jhilj hihhk ..",       # 16
    "...kj lihjW ihjmi hjlih jWhhk ..",       # 17  a lank rat-tail hangs off the back
    "..kih jijii hiiji ihiih hihk. ..",       # 18
    ".kiki iWijh cciid dkjmA jihk. ..",       # 19  the forelock falls over the forehead;
    ".kjki iijhd eeeie ekjAi kcbk. ..",       # 20  a loose strand sticks on the near side
    ".kiki jjihd eeeeh edkkd dcbk. ..",       # 21
]
# the rat-tail's tip, one row into the face rows (behind the ear, outside the face)
TAIL_TIP = {(37, 22): 'k'}


def hair():
    rows = B.rows_of(HAIR)
    for i, r in enumerate(rows):
        if len(r) != 27:
            raise ValueError('hair row %d is %d wide' % (HY0 + i, len(r)))
    part = B.amap(rows, HX0, HY0)
    part.update(TAIL_TIP)
    return part


def head(shout=False):
    """The v2 head in head space (the rig's): the approved face and jaw, the greasy hair."""
    rows = B.rows_of(RH.HEAD)
    if shout:
        rows = rows[:22 - RH.Y0] + B.rows_of(RH.SHOUT)
    face = B.amap(rows, RH.X0, RH.Y0)
    part = {q: k for q, k in face.items() if q[1] >= 22}
    part.update(hair())
    return part


def _selftest():
    """The face rows must be the approved rig's, pixel for pixel (the rat-tail tip, outside the
    face, is the one addition)."""
    ok = True
    for shout in (False, True):
        ref = RH.head(shout)
        got = head(shout)
        bad = [q for q in ref if q[1] >= 22 and ref[q] != got.get(q)]
        # only the rat-tail's tip may add to the face rows, and only where the face has nothing
        bad += [q for q in got if q[1] >= 22 and q not in ref and q not in TAIL_TIP]
        print('face rows match the approved %s head:' % ('shout' if shout else 'idle'), not bad)
        ok &= not bad
    return ok


if __name__ == '__main__':
    sys.exit(0 if _selftest() else 1)
