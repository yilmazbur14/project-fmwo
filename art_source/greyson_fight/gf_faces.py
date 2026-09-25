"""Greyson's fight faces: new expressions drawn on the approved face grid (gr_face: x 46-66,
21 columns, from row 30; each row written as left x 46-56 and right x 57-66 so the widths are
checked). The approved faces ('idle', 'flex') are used as they are.

  'roar'   (INVENTED for the fight, not in the approved pass) the approved flex face's swollen
           vein, crushed brows and hard stare, with the jaw dropped open in a roar the way Matt's
           approved roar drops his: the chin moves down four rows over the neck. For the
           spirit-bomb raise, and ready for the cutscene's roar. No new colours: the throat is
           the deepest skin tone ('6') and the tongue the vein's red ('v', the portrait's
           #D95763).
  'menace' (INVENTED) the approved idle grin under the flex face's crushed brows and stare: his
           cocky grin turned into a threat ("Pal, you won't like what comes next."). For the
           fight idle.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402

gr_face = B.gr_face
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of

# The upper face of the approved flex (rows 30-43): the vein, the brows, the stare, the cheeks.
FLEX_UPPER = gr_face.FLEX[:14]

ROAR = [r for r in FLEX_UPPER] + rows_of([
    # left x 46-56    right x 57-66       y
    ("123dccccccc", "cccddde444"),   # 44  moustache
    ("k2d4kkkkkkk", "kkkkkk4d4k"),   # 45  the mouth's top line, stretched wide
    ("k2dkWWWxWWx", "WWxWWXkd4k"),   # 46  upper teeth
    ("k2dk6666666", "666666kd4k"),   # 47  the throat
    ("k23k6666666", "666666k34k"),   # 48
    ("k23k66vvvvv", "vvvv66k34k"),   # 49  the tongue
    ("k23k6vvvvvV", "vvvvV6k34k"),   # 50
    ("k23kXXxXXxX", "XxXXxxk34k"),   # 51  lower teeth
    ("k223kkkkkkk", "kkkkkk344k"),   # 52  lower lip line
    (".k222223333", "33334444k."),   # 53  the dropped chin
    ("..k22233333", "3334445k.."),   # 54
    ("...kkkkkkkk", "kkkkkkk..."),   # 55  the jaw's keyline, four rows lower than at rest
])

MENACE = [r for r in FLEX_UPPER] + list(gr_face.IDLE[14:])

FACES = {'roar': ROAR, 'menace': MENACE}


def _check():
    for name, rows in FACES.items():
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))


_check()


def face(name):
    if name in gr_face.FACES:
        return gr_face.face(name)
    out = {}
    for r, row in enumerate(FACES[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


def head(name, extras=None):
    """The approved mane with a face laid over it (an approved one or a fight one), plus extras
    (the sweat bead, say)."""
    part = gr_face.mane()
    part.update(face(name))
    if extras:
        part.update(extras)
    return part
