"""Greyson's faces for the brawl's finishing half, on the approved face grid (gr_face: x 46-66,
21 columns, rows 30-50, each row written as left x 46-56 and right x 57-66 so the widths are
checked). INVENTED for the brawl from the approved faces' own parts; no new colours.

  dazed0..3  the approved dazed face (gb_faces, the user-approved slump) with the pupils rolling
             round behind the lenses: apart (the approved frame), both right, crossed, both left.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gz_base as Z  # noqa: E402

gr_face = Z.gr_face
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of
IDLE = gr_face.IDLE
DAZED = Z.gb_faces.DAZED             # the approved dazed face (row 9 is the eyes' row, y 39)

# the dazed eyes, row y 39: (left x 46-56, right x 57-66); the eye interiors are x 49-52 and 60-63
EYES = {
    'apart': ("1GknXWWkG12", "3GkWWXnkG4"),      # the approved frame
    'right': ("1GkWWXnkG12", "3GkWWXnkG4"),
    'crossed': ("1GkWWXnkG12", "3GknXWWkG4"),
    'left': ("1GknXWWkG12", "3GknXWWkG4"),
}


def dazed(eyes):
    rows = list(DAZED)
    rows[9] = rows_of([EYES[eyes]])[0]
    return rows


ROAR = Z.gf_faces.FACES['roar']       # the fight's roar: the jaw dropped to row 55

# the uppercut's SNAP: the roar's great open mouth with the eyes squeezed shut into > < under
# brows pinched up in the middle (pain); the jaw on row 55 like the roar's
SNAP = ROAR[:4] + rows_of([
    ("..1112ddd22", "2eee2334.."),   # 34  the brows' inner ends thrown up...
    ("1dddd222223", "3233eeee44"),   # 35  ...their outer ends down
]) + ROAR[6:7] + rows_of([
    ("Ggkk2222GGG", "GG3333kkGG"),   # 37  the eyes squeezed shut: > <
    ("1G23kkk2G13", "4G3kkk34G4"),   # 38
    ("1Gkk3222G12", "3G3334kkG4"),   # 39
]) + ROAR[10:]

# the REEL he holds after it: knocked silly, the eyes blank white rings (no pupils), the dazed
# face's slack open mouth and lolling tongue; the jaw back on row 50
REEL = DAZED[:7] + rows_of([
    ("GgkkkkkkGGG", "GGkkkkkkGG"),   # 37  lashes
    ("1GkWWWWkG12", "3GkWWWWkG4"),   # 38  blank white eyes
    ("1G2kXXk2G12", "3G3kXXk4G4"),   # 39
]) + DAZED[10:]

# the KO's big SNAP: the killing uppercut. The eyes roll up out of sight (only a sliver of the
# blue left under the lids), the brows fly up, the roar's jaw hangs wide, and one upper tooth is
# knocked out; the jaw on row 55 like the roar's
_ROAR_TEETH = ROAR[16]
KO_SNAP = ROAR[:4] + rows_of([
    ("..ddddd2222", "222eeeee.."),   # 34  the brows fly up
    ("11222222222", "2233333344"),   # 35
    ("12gggGGG222", "23GGGGGG44"),   # 36  the rims' tops
    ("GgkkkkkkGGG", "GGkkkkkkGG"),   # 37  lashes
    ("1GkWOOWkG12", "3GkWOOWkG4"),   # 38  the eyes rolled up: a sliver of blue at the top
    ("1G2kWWk2G12", "3G3kWWk4G4"),   # 39  the whites
]) + ROAR[10:16] + [_ROAR_TEETH[:11] + '66' + _ROAR_TEETH[13:]] + ROAR[17:]

FACES = {
    'dazed0': dazed('apart'),
    'dazed1': dazed('right'),
    'dazed2': dazed('crossed'),
    'dazed3': dazed('left'),
    'snap': SNAP,
    'reel': REEL,
    'ko_snap': KO_SNAP,
}
assert FACES['dazed0'] == DAZED, 'the approved dazed face must be frame 0 exactly'

# every face any rig has, by name (this module's win a clash, but there are none)
ALL = {}
ALL.update(gr_face.FACES)
ALL.update(Z.gf_faces.FACES)
ALL.update(Z.gp_faces.FACES)
ALL.update(Z.gb_faces.FACES)
ALL.update(FACES)


def _check():
    for name, rows in FACES.items():
        assert len(rows) in (len(IDLE), len(ROAR)), (name, len(rows))
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))
            assert set(r) <= set(Z.K.PAL) | {'.'}, (name, FY0 + i, r)


_check()


def face(name):
    out = {}
    for r, row in enumerate(ALL[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


def jaw_row(name):
    """The jaw's keyline row on the centre column (x 56), in face coordinates (idle: 50)."""
    f = face(name)
    return max(y for (x, y), k in f.items() if x == 56 and k == 'k')


def head(name, dx=0, dy=0, extras=None):
    """The approved mane with a face (any rig's, by name), moved; -> (part, the face's pixels)."""
    part = gr_face.mane()
    f = face(name)
    part.update(f)
    if extras:
        part.update(extras)
    return Z.moved(part, dx, dy), set(Z.moved({p: 1 for p in f}, dx, dy))
