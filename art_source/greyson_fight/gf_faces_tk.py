"""Greyson's takeover faces (the cutscene where he finds Computah beaten), on the approved face
grid (gr_face: x 46-66, 21 columns, from row 30; each row written as left x 46-56 and right
x 57-66 so the widths are checked). A separate module so the shared gf_faces never changes under
the artists who import it.

He is "extremely upset" (the user's brief) the whole way through, so every upset face cries: anime
tear streams in his own eye blues ('o' #B4DCFF, 'O' #639BFF), no new colours.

  'rage'        the approved flex face (swollen forked vein, brows crushed to a V, the hard stare,
                clenched teeth) with tears welling at the outer corners and running down both
                cheeks. The walk-in, and the talk sheet's fury pose with the mouth shut.
  'rage_open'   the same, shouting: the jaw drops two rows over upper and lower teeth.
  'grief'       brows raised in the middle, eyes squeezed shut with tears pouring out from under
                the lids, a trembling frown. "That was my gym partner."
  'grief_open'  the same, sobbing: the mouth open in a wail, corners down, the jaw a row lower.
  'fond'        remembering: eyes shut in happy arcs, a tear at each outer corner, brows still
                sad, a small wet smile. "I hit my first 225 on bench with this little guy."
  'fond_open'   the same, talking through the smile.
All INVENTED for the takeover (the user gave the lines, not the faces).
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gf_base as B  # noqa: E402

gr_face = B.gr_face
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of

FLEX = gr_face.FLEX      # the approved flex face, rows 30-50
IDLE = gr_face.IDLE      # the approved idle face, rows 30-50

# ------------------------------------------------------------------------------------ rage

RAGE_EYES = rows_of([
    # left x 46-56    right x 57-66       y
    ("1GkWOnOkG13", "4GkOnOWkG4"),   # 38  the approved hard stare
    ("1Go3kkk3G12", "3G3kkk4oG4"),   # 39  tears well at the outer corners
    ("12oOGGGG212", "33GGGGoO44"),   # 40  and spill over the bottom rims
    ("11oO2223212", "332223oO44"),   # 41  down the bunched cheeks
    ("11oO3422211", "422243oO44"),   # 42
    ("12oO4322453", "542343oO44"),   # 43
    ("12odccccccc", "cccdddeo44"),   # 44  a drop at each moustache end
])

RAGE = FLEX[:8] + RAGE_EYES + FLEX[15:]

RAGE_OPEN = FLEX[:8] + RAGE_EYES + rows_of([
    ("k2d4kkkkkkk", "kkkkkk4d4k"),   # 45  the shout's top line
    ("k2dkWWWxWWx", "WWxWWXkd4k"),   # 46  upper teeth
    ("k2dk6666666", "666666kd4k"),   # 47  the throat
    ("k23kXXxXXxX", "XxXXxxk34k"),   # 48  lower teeth
    ("k223kkkkkkk", "kkkkkk344k"),   # 49  lower lip line
    (".k222223333", "33334444k."),   # 50  the chin, two rows lower than at rest
    ("..k22233333", "3334445k.."),   # 51
    ("...kkkkkkkk", "kkkkkkk..."),   # 52  the jaw's keyline
])

# ------------------------------------------------------------------------------------ grief

GRIEF_TOP = rows_of([
    # left x 46-56    right x 57-66       y
    ("..........v", ".........."),   # 30  the vein, resting
    ("........1vv", "V2........"),   # 31
    ("......111v2", "V223......"),   # 32
    ("....1111v22", "2V2233...."),   # 33
    ("..111dddd22", "2eeee334.."),   # 34  brows: the inner ends raised...
    ("11ddd222222", "22223eee44"),   # 35  ...the outer ends dropped: grief
    ("12gggGGG222", "23GGGGGG44"),   # 36  glasses: top rims
    ("Gg222222GGG", "GG333333GG"),   # 37
    ("1GkkkkkkG12", "3GkkkkkkG4"),   # 38  eyes squeezed shut
    ("1G22oO33G12", "3G33oO44G4"),   # 39  tears pour out from under the lids
    ("12GGoOGG212", "33GGoOGG44"),   # 40  over the bottom rims
    ("1122oO22212", "3233oO3344"),   # 41  down the cheeks
    ("1122oO22211", "4233oO3344"),   # 42
    ("1222oO22343", "5333oO3344"),   # 43
    ("1222odccccc", "ccddeo3344"),   # 44  dripping past the moustache
])

GRIEF = GRIEF_TOP + rows_of([
    ("k222d22kkkk", "kkk23d344k"),   # 45  a frown: the lips arch...
    ("k222d2k3333", "333k2d344k"),   # 46  ...down at the corners
    ("k2223k22112", "2333k3344k"),   # 47  and quiver
    (".k222222222", "33333444k."),   # 48
    ("..k22232233", "3334445k.."),   # 49  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

GRIEF_OPEN = GRIEF_TOP + rows_of([
    ("k222d22kkkk", "kkk23d344k"),   # 45  the wail's top line
    ("k222d2kWWWW", "WWXk2d344k"),   # 46  upper teeth
    ("k2223k66666", "6666k3344k"),   # 47  the throat
    ("k2223k6vvvv", "vvV6k3344k"),   # 48  the tongue
    (".k2223kkkkk", "kkkk3344k."),   # 49  the wail's bottom line, wider than its top
    ("..k22223333", "3334445k.."),   # 50  chin, a row lower
    ("...kkkkkkkk", "kkkkkkk..."),   # 51  the jaw's keyline
])

# ------------------------------------------------------------------------------------ fond

FOND_TOP = GRIEF_TOP[:7] + rows_of([
    # left x 46-56    right x 57-66       y
    ("Gg2kkkk2GGG", "GG3kkkk3GG"),   # 37  eyes shut in happy arcs...
    ("1Gk2222kG12", "3Gk3333kG4"),   # 38
    ("1Go22223G12", "3G33334oG4"),   # 39  ...a tear at each outer corner
    ("12oGGGGG212", "33GGGGGo44"),   # 40
    ("11o22222212", "3233333o44"),   # 41
    ("11222222211", "4233333344"),   # 42  nose tip
    ("12222222343", "5333333344"),   # 43  nostrils
    ("12223dccccc", "ccdde33344"),   # 44  moustache
])

FOND = FOND_TOP + rows_of([
    ("k222d2k2222", "222k2d344k"),   # 45  a small wet smile: the corners up...
    ("k222d22kkkk", "kkk23d344k"),   # 46  ...the line dipping between them
    ("k2222321122", "233333344k"),   # 47  lower lip
    (".k222222222", "33333444k."),   # 48
    ("..k22232233", "3334445k.."),   # 49  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

FOND_OPEN = FOND_TOP + rows_of([
    ("k222d2k2222", "222k2d344k"),   # 45  the corners up
    ("k222d22kkkk", "kkk23d344k"),   # 46  the top line
    ("k22223kWWWW", "WWXk33344k"),   # 47  teeth
    (".k22223kkkk", "kkk33444k."),   # 48  bottom line
    ("..k22232233", "3334445k.."),   # 49  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

# ------------------------------------------------------------------------------------ smug
# With the cannon on, the tears are gone and the gym bro is back: his right brow cocked up, the
# left eye heavy-lidded, the right one wide under the raised brow, a lopsided smirk rising on one
# side (INVENTED; "What Computah didn't know..." / "Pal, you won't like what comes next.").

SMUG_TOP = IDLE[:4] + rows_of([
    # left x 46-56    right x 57-66       y
    ("..11111v222", "222eeeee.."),   # 34  the right brow cocked up...
    ("11ddddd2222", "2233333344"),   # 35  ...the left one level
    ("12gggGGG222", "23GGGGGG44"),   # 36  glasses: top rims
    ("GgkkkkkkGGG", "GGkkkkkkGG"),   # 37  lash lines, the bridge
    ("1GkkkkkkG12", "3GXWnOXkG4"),   # 38  the left lid lowered, the right eye wide
    ("1G2XWnO3G12", "3G3ooO34G4"),   # 39
]) + IDLE[10:15]

SMUG = SMUG_TOP + rows_of([
    ("k222d222222", "22kk3d344k"),   # 45  the smirk's corner rises...
    ("k222d2kkkkk", "kk333d344k"),   # 46  ...from a flat line
    ("k2223d21122", "2333d3344k"),   # 47  lower lip
]) + IDLE[18:]

SMUG_OPEN = SMUG_TOP + rows_of([
    ("k222d222kkk", "kkkk3d344k"),   # 45  the top line, higher on the smirking side
    ("k222d2kkWWW", "WWXk3d344k"),   # 46  teeth
    ("k2223d2kkkk", "kkk3d3344k"),   # 47  bottom line
]) + IDLE[18:]

# ------------------------------------------------------------------------------------ inhale
# The breath before the roar (INVENTED): the flex face's swollen vein and crushed brows, eyes
# squeezed shut, nostrils flared, lips pressed flat.
INHALE = FLEX[:6] + rows_of([
    # left x 46-56    right x 57-66       y
    ("12gggGGG234", "33GGGGGG44"),   # 36  glasses: top rims
    ("Gg222222GGG", "GG333333GG"),   # 37
    ("1GkkkkkkG12", "3GkkkkkkG4"),   # 38  eyes squeezed shut
    ("1G222223G12", "3G333334G4"),   # 39
]) + FLEX[10:15] + rows_of([
    ("k2d42222222", "2222224d4k"),   # 45
    ("k2d433kkkkk", "kkkk334d4k"),   # 46  lips pressed flat
    ("k2d42223333", "3333334d4k"),   # 47
    (".k3d2222222", "33333d44k."),   # 48
]) + IDLE[19:]

FACES = {'rage': RAGE, 'rage_open': RAGE_OPEN, 'grief': GRIEF, 'grief_open': GRIEF_OPEN,
         'fond': FOND, 'fond_open': FOND_OPEN, 'smug': SMUG, 'smug_open': SMUG_OPEN,
         'inhale': INHALE}

# The middle of each mouth (texels, head at rest): where a speech balloon's tail points.
MOUTH = {'rage': (56, 46), 'rage_open': (56, 47), 'grief': (56, 45), 'grief_open': (56, 47),
         'fond': (56, 46), 'fond_open': (56, 47), 'smug': (56, 46), 'smug_open': (57, 46),
         'inhale': (56, 46)}


def _check():
    for name, rows in FACES.items():
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))


_check()


def face(name):
    out = {}
    for r, row in enumerate(FACES[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


def head(name):
    """The approved mane with a takeover face laid over it."""
    part = gr_face.mane()
    part.update(face(name))
    return part
