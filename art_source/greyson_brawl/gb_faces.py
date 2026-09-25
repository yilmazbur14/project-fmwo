"""Greyson's brawl faces, on the approved face grid (gr_face: x 46-66, 21 columns, rows 30-50;
every row written as left x 46-56 and right x 57-66 so the widths are checked). INVENTED for the
brawl from the approved faces' parts; no new colours. The jaw stays on row 50 in every face here,
so the chin anchor never moves with the expression.

  'dazed'  the approved idle face gone slack: the lids drooping half over the eyes, the pupils
           drifting apart behind the lenses, the grin fallen open into a lopsided slack mouth
           (the throat the deepest skin tone, as in the fight's roar face) with the tongue lolling
           out over the lower lip (the vein's red, as the roar's tongue).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gb_base as B  # noqa: E402

gr_face = B.G.gr_face
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of
IDLE = gr_face.IDLE

DAZED = IDLE[:7] + rows_of([
    # left x 46-56    right x 57-66       y
    ("Gg233333GGG", "GG333344GG"),   # 37  the lids hang down inside the lenses
    ("1GkkkkkkG12", "3GkkkkkkG4"),   # 38  the lids' edges, half way down the eyes
    ("1GknXWWkG12", "3GkWWXnkG4"),   # 39  the pupils drifting apart
]) + IDLE[10:14] + rows_of([
    ("12223dccccc", "ccdde33344"),   # 44  the moustache
    ("k222dkkkkkk", "kkkkd3344k"),   # 45  the mouth fallen open...
    ("k222dk66666", "666kkd344k"),   # 46  ...its throat in the deepest skin tone
    ("k2223kvv666", "66kk3d344k"),   # 47  the tongue lolling out of the left corner
    (".k2222kvVkk", "kk333444k."),   # 48  over the lower lip
    ("..k2223kV23", "3334445k.."),   # 49
]) + IDLE[20:]

FACES = {'dazed': DAZED}


def _check():
    for name, rows in FACES.items():
        assert len(rows) == len(IDLE), (name, len(rows))
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))
            assert set(r) <= set(B.K.PAL) | {'.'}, (name, FY0 + i, r)


_check()


def face(name):
    out = {}
    for r, row in enumerate(FACES[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out
