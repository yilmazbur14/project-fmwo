"""Greyson's new fight expressions, drawn on the approved face grid (gr_face: columns x 46-66, 21 per
row, from row 30; each row written as left x 46-56 and right x 57-66 so the widths are checked). They
reuse the approved rows wherever the expression allows (the vein, the brows, the gold glasses, the
cheeks, the moustache), and add no colours. INVENTED for the fight (not in the approved pass):

  'hurt'   a hit landing: the flex face's swollen vein and crushed brows, the eyes squeezed shut to
           > < behind the glasses, the mouth wrenched open on clenched teeth, the jaw a row lower
  'daze'   Broken, dizzy: eyes wide and wall-eyed (the pupils drifting apart), the jaw slack, the
           tongue lolling out (the vein's red, as in the approved 'roar')
  'laugh'  victory: the idle's easy brows, the eyes squeezed into happy arcs behind the glasses, the
           mouth thrown wide open (the approved 'roar' mouth)
  'grin'   victory, between laughs: the same happy arcs over the approved idle grin
  'ko'     beaten: the eyes shut to flat lines, the mouth hanging open

Every face is laid over the approved mane (gr_face.mane) like the approved ones.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gan_base as B  # noqa: E402

gr_face = B.gr_face
gf_faces = B.gf_faces
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of

IDLE = gr_face.IDLE
FLEX = gr_face.FLEX
ROAR = gf_faces.ROAR


def _r(y, rows):
    return rows[y - FY0]


HURT = [_r(y, FLEX) for y in range(30, 37)] + rows_of([
    # left x 46-56    right x 57-66       y
    ("Ggkk3333GGG", "GG3333kkGG"),   # 37  eyes squeezed shut: > <
    ("1G33kkk3G13", "4G3kkk33G4"),   # 38
    ("1Gkk3333G12", "3G3333kkG4"),   # 39
]) + [_r(y, FLEX) for y in range(40, 45)] + rows_of([
    ("k2d4kkkkkkk", "kkkkkk4d4k"),   # 45  the mouth wrenched open
    ("k2dkWWWxWWx", "WWxWWXkd4k"),   # 46  upper teeth
    ("k2dk6666666", "666666kd4k"),   # 47  the dark between them
    ("k2dkXXxXXxX", "XxXXxxkd4k"),   # 48  lower teeth
    (".k3dkkkkkkk", "kkkkkkd4k."),   # 49  bottom line; the moustache dragged down
    ("..k22233333", "3334445k.."),   # 50  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 51  the jaw's keyline, a row lower
])

DAZE = [_r(y, IDLE) for y in range(30, 38)] + rows_of([
    ("1GkWnWWWG12", "3GWWWnWkG4"),   # 38  eyes wide, the pupils drifting apart
    ("1G2WWWWXG12", "3GXWWWW4G4"),   # 39
]) + [_r(y, IDLE) for y in range(40, 45)] + rows_of([
    ("k222dkkkkkk", "kkkkkd344k"),   # 45  the upper lip line
    ("k222dk66666", "6666kd344k"),   # 46  the jaw hanging open
    ("k2223k66vvv", "vV6kd3344k"),   # 47  the tongue lolling out
    (".k2222kvvvv", "vVk33444k."),   # 48
    ("..k22232kvv", "Vk334445k."),   # 49  its tip over the lip
    ("...kkkkkkkk", "kkkkkkkk.."),   # 50  the jaw's keyline
])

LAUGH = [_r(y, IDLE) for y in range(30, 37)] + rows_of([
    ("Gg33kk33GGG", "GG33kk33GG"),   # 37  eyes squeezed into happy arcs
    ("1G3k22k3G12", "3G3k33k3G4"),   # 38
    ("1Gk2222kG12", "3Gk3333kG4"),   # 39
]) + [_r(y, IDLE) for y in range(40, 44)] + [_r(y, ROAR) for y in range(44, 56)]

GRIN = [_r(y, IDLE) for y in range(30, 37)] + LAUGH[37 - FY0:40 - FY0] + [_r(y, IDLE) for y in range(40, 51)]

KO = [_r(y, IDLE) for y in range(30, 37)] + rows_of([
    ("Gg333333GGG", "GG333333GG"),   # 37  eyes shut
    ("1GkkkkkkG12", "3GkkkkkkG4"),   # 38  flat lid lines
    ("1G222222G12", "3G444444G4"),   # 39
]) + [_r(y, IDLE) for y in range(40, 45)] + rows_of([
    ("k2222dkkkk3", "3kkkkd344k"),   # 45  the mouth hanging open
    ("k2222k66663", "3666k3344k"),   # 46
    (".k2222k666k", "666k33444k"),   # 47
    ("..k22232kkk", "kk3334445k"),   # 48
    ("...k2223333", "3334445k.."),   # 49  chin
    ("....kkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

FACES = {'hurt': HURT, 'daze': DAZE, 'laugh': LAUGH, 'grin': GRIN, 'ko': KO}


def _check():
    for name, rows in FACES.items():
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))


_check()


def face(name):
    """Any face by name: the approved ones (gr_face), the fight rig's (gf_faces), or these."""
    if name in FACES:
        out = {}
        for r, row in enumerate(FACES[name]):
            for c, ch in enumerate(row):
                if ch != '.':
                    out[(FX0 + c, FY0 + r)] = ch
        return out
    return gf_faces.face(name)


def head(name, dx=0, dy=0):
    """The approved mane with the face laid over it (and the flex face's sweat bead), moved."""
    part = gr_face.mane()
    part.update(face(name))
    if name == 'flex':
        part.update(gr_face.SWEAT)
    return B.moved(part, dx, dy)


def keep(name, dx=0, dy=0):
    """The face's hand-drawn pixels, which the final sweep must never change."""
    k = dict(face(name))
    if name == 'flex':
        k.update(gr_face.SWEAT)
    return B.moved(k, dx, dy)
