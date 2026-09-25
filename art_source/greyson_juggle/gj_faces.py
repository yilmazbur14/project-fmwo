"""Greyson's juggle faces, drawn on the approved face grid (gr_face: columns x 46-66, 21 per row,
from row 30; each new row written as left x 46-56 and right x 57-66 so the widths are checked).
They reuse the approved rows wherever the expression allows -- the vein, the brows, the gold
glasses, the cheeks, the moustache, the approved flex grimace and the fight rig's approved roar
mouth -- and add no colours. The lenses' insides are x 48-53 and x 59-64, rows 37-39.

All INVENTED for the juggle (the contract asks for big readable faces on the hit and the KO; the
user has not seen these):
  'jolt'    the hit: the flex face's swollen vein and crushed brows, the eyes squeezed shut to
            > < behind the glasses, the jaw dropped wide open (the approved roar's mouth)
  'gasp'    the apex hang: the eyes blown wide and white behind the lenses with pinprick
            pupils, under the approved idle's easy brows, the roar's jaw hanging open
  'roll0'-'roll3'  the tumble: 'gasp' with the pupils rolled round the eyes a quarter at a time
  'crash'   the landing: the squeezed > < eyes over the approved flex grimace's clenched teeth
  'daze'    the bounce: the eyes wide and wall-eyed, the jaw slack, the tongue lolling out
  'ko'      down: the vein gone quiet, an X in each lens, the mouth hanging open and the tongue
            out over the lip (the tongue and throat in the approved roar's own red and dark)
The squeezed eyes are the house's > < (the other fight sheets' hit faces use the same shape).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gj_rig as R  # noqa: E402

gr_face, gf_faces = R.gr_face, R.gf_faces
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of
IDLE, FLEX, ROAR = gr_face.IDLE, gr_face.FLEX, gf_faces.ROAR


def _r(rows, y0, y1):
    """Rows y0..y1 (inclusive) of an approved face."""
    return rows[y0 - FY0:y1 - FY0 + 1]


SQUEEZED = rows_of([
    # left x 46-56    right x 57-66       y
    ("Ggkk2222GGG", "GG3333kkGG"),   # 37  eyes squeezed shut: > <
    ("1G22kkk2G13", "4G3kkk33G4"),   # 38
    ("1Gkk2222G12", "3G3333kkG4"),   # 39
])


def wide(lp, rp):
    """Eyes blown wide and white, a pinprick pupil in each: lp and rp are the pupils' (x, y) in
    the left and right lens (x 48-53 / 59-64, rows 38-39)."""
    rows = [list("GgkkkkkkGGG" + "GGkkkkkkGG"),      # 37  the lash lines (approved)
            list("1GkWWWWXG13" + "4GXWWWWkG4"),      # 38  white to the rims
            list("1G2XWWWWG12" + "3GWWWWX4G4")]      # 39
    for (x, y) in (lp, rp):
        rows[y - 37][x - FX0] = 'n'
    return [''.join(r) for r in rows]


JOLT = _r(FLEX, 30, 36) + SQUEEZED + _r(FLEX, 40, 43) + _r(ROAR, 44, 55)
GASP_EYES = wide((51, 38), (61, 38))
GASP = _r(IDLE, 30, 36) + GASP_EYES + _r(IDLE, 40, 43) + _r(ROAR, 44, 55)
# the pupils rolled round together, a quarter at a time as he turns: up-left, up-right,
# down-right, down-left (both eyes the same way, so they read as rolling, not crossing)
ROLLS = [wide((50, 38), (60, 38)), wide((52, 38), (62, 38)), wide((52, 39), (62, 39)),
         wide((50, 39), (60, 39))]
CRASH = _r(FLEX, 30, 36) + SQUEEZED + _r(FLEX, 40, 50)

DAZE = _r(IDLE, 30, 36) + [
    "GgkkkkkkGGG" + "GGkkkkkkGG",    # 37
    "1GkWnWWXG13" + "4GXWWnWkG4",    # 38  wall-eyed: the pupils drifting apart
    "1G2XWWWWG12" + "3GWWWWX4G4",    # 39
] + _r(IDLE, 40, 44) + rows_of([
    ("k222dkkkkkk", "kkkkkd344k"),   # 45  the upper lip line
    ("k222dk66666", "6666kd344k"),   # 46  the jaw hanging slack
    ("k2223k66vvv", "vV6k33344k"),   # 47  the tongue lolling out
    (".k2222kvvvv", "vVk333444k"),   # 48
    ("..k22232kvv", "Vk3334445k"),   # 49  its tip over the lip
    ("...kkkkkkkk", "kkkkkkkk.."),   # 50  the jaw's keyline
])

KO = _r(IDLE, 30, 36) + rows_of([
    # left x 46-56    right x 57-66       y
    ("GgWkWWkWGGG", "GGWkWWkWGG"),   # 37  an X in each lens, on white:
    ("1GWWkkWWG12", "3GWWkkWWG4"),   # 38  its arms crossing...
    ("1GWkWWkWG12", "3GWkWWkWG4"),   # 39  ...and parting again
]) + _r(IDLE, 40, 45) + rows_of([
    ("k222dk66666", "6666kd344k"),   # 46  the grin gone slack: the mouth hanging open
    ("k2223dk6vvv", "vV6kd3344k"),   # 47  the tongue coming out...
    (".k22222kvvv", "vVk33444k."),   # 48  ...over the lower lip...
    ("..k2223kvvv", "Vk34445k.."),   # 49  ...and down the chin
    ("...kkkkkvvV", "kkkkkkk..."),   # 50  the jaw's keyline, the tongue past it
    ("........kkk", ".........."),   # 51  the tongue tip's keyline
])

FACES = {'jolt': JOLT, 'gasp': GASP, 'crash': CRASH, 'daze': DAZE, 'ko': KO}
for _i, _eyes in enumerate(ROLLS):
    FACES['roll%d' % _i] = _r(IDLE, 30, 36) + _eyes + _r(IDLE, 40, 43) + _r(ROAR, 44, 55)


def _check():
    keys = set(R.K.PAL) | {'.'}
    for name, rows in FACES.items():
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))
            assert set(r) <= keys, (name, FY0 + i, r)


_check()


def face(name):
    """{(x, y): key} for a juggle face (or an approved / fight one by its own name)."""
    if name not in FACES:
        return gf_faces.face(name)
    out = {}
    for r, row in enumerate(FACES[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


def head(name):
    """(the approved mane with the face over it, the face's own pixels)."""
    part = gr_face.mane()
    f = face(name)
    part.update(f)
    return part, f
