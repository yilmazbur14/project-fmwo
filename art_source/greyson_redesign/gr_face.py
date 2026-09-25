"""Greyson's head, drawn pixel by pixel.

Likeness, from his photos and the portrait the user drew of him:
  - hair: long, straight, parted dead centre, falling past the jaw in two curtains that frame the
    face; golden blonde with strawberry-copper shadows (the portrait's yellow, the photos' honey);
  - the forehead vein: the photo's raised vein down the middle of a high forehead, drawn as the
    portrait's red chevron under the parting;
  - light blue eyes and pale brows;
  - thin gold wire glasses (photo 1, and the 2026-09-18 approved sprite);
  - a long straight nose with a rounded tip;
  - a thin strawberry moustache whose corners drop (the portrait's and the mech pilot's horseshoe);
  - a strong square jaw.
Light from the upper left: the left side of the face and the left curtain lit, the right in shade.

The mane is written as its LEFT half only (x 38-56) and mirrored about column 56 (x' = 112 - x)
with a one-step-darker relight, so its silhouette is exactly symmetric and its right side sits in
shade. Faces are full-width maps (x 46-66, 21 columns) laid over it, one per expression; each row
is written as left (x 46-56, 11) and right (x 57-66, 10) so the widths are checked.
"""
X0 = 38          # the mane map's first column
Y0 = 26          # the mane map's first row
FX0 = 46         # the face maps' first column
FY0 = 30         # the face maps' first row


def _row(*parts):
    return ''.join(parts)


D = '.'

# ------------------------------------------------------------------------------------ the mane

# (x 38-56, 19 columns; the parting is column 56)
HAIR_L = [
    _row(D * 12, 'kkkkkkk'),                        # 26  crown
    _row(D * 10, 'kk', 'baabbc', 'k'),              # 27  the parting is black
    _row(D * 8, 'kk', 'baabbbcc', 'k'),             # 28  the ring of highlight arcs down-left
    _row(D * 7, 'k', 'baabbbbccd', 'k'),            # 29
    _row(D * 6, 'k', 'babbbbcccd', 'k', D),         # 30  the forehead opens under the parting
    _row(D * 5, 'k', 'babbbcccd', 'k', D * 3),      # 31
    _row(D * 4, 'k', 'babbbccd', 'k', D * 5),       # 32
    _row(D * 3, 'k', 'babbbcd', 'k', D * 7),        # 33
    _row(D * 3, 'k', 'abbcd', 'k', D * 9),          # 34
    _row(D * 2, 'k', 'abbd', 'k', D * 11),          # 35
    _row(D * 2, 'k', 'abcd', 'k', D * 11),          # 36  the curtain falls beside the face
    _row(D, 'k', 'abbcd', 'k', D * 11),             # 37
    _row(D, 'k', 'bbcbd', 'k', D * 11),             # 38
    _row(D, 'k', 'bcbbe', 'k', D * 11),             # 39
    _row(D, 'k', 'bcbce', 'k', D * 11),             # 40
    _row(D, 'k', 'bbcce', 'k', D * 11),             # 41
    _row(D, 'k', 'bcbce', 'k', D * 11),             # 42
    _row('k', 'bbcbce', 'k', D * 11),               # 43
    _row('k', 'bcbcde', 'k', D * 11),               # 44
    _row('k', 'bcbcdd', 'e', D * 11),               # 45  from here the jaw carries the keyline
    _row('k', 'bccbdd', 'e', D * 11),               # 46
    _row('k', 'bcc', 'k', 'dd', 'e', D * 11),       # 47  a cut splits the curtain into two locks
    _row('k', 'bcc', 'k', 'de', 'e', 'e', D * 10),  # 48
    _row('k', 'bcc', 'k', 'cde', 'k', D * 10),      # 49  the mane runs on past the jaw...
    _row('k', 'bcd', 'k', 'cde', 'k', D * 10),      # 50
    _row('k', 'bcd', 'k', 'cde', 'k', D * 10),      # 51  ...over the traps, onto the chest
    _row('k', 'bcd', 'k', 'cd', 'k', D * 11),       # 52
    _row('k', 'bcd', 'k', 'cd', 'k', D * 11),       # 53
    _row('k', 'bcd', 'k', 'd', 'k', D * 12),        # 54
    _row('k', 'bcd', 'k', 'k', D * 13),             # 55  the inner lock's tip
    _row('k', 'bcd', 'k', D * 14),                  # 56
    _row('k', 'bcd', 'k', D * 14),                  # 57
    _row('k', 'cd', 'k', D * 15),                   # 58
    _row(D, 'k', 'd', 'k', D * 15),                 # 59
    _row(D * 2, 'k', D * 16),                       # 60  the outer lock's tip
]

RELIGHT = {'a': 'b', 'b': 'c', 'c': 'd', 'd': 'e', 'e': 'e', 'k': 'k', '.': '.'}


def mane():
    """{(x, y): key} for the whole mane: the left half as drawn, the right half mirrored and
    relit one step darker."""
    out = {}
    for r, row in enumerate(HAIR_L):
        assert len(row) == 19, (Y0 + r, row, len(row))
        y = Y0 + r
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            x = X0 + c
            out[(x, y)] = ch
            if x != 56:
                out[(112 - x, y)] = RELIGHT[ch]
    return out


# ------------------------------------------------------------------------------------ faces

def rows_of(pairs):
    out = []
    for i, (l, r) in enumerate(pairs):
        assert len(l) == 11, ('left', FY0 + i, l, len(l))
        assert len(r) == 10, ('right', FY0 + i, r, len(r))
        out.append(l + r)
    return out


# The idle: cocky and easy. His photo grin, brows level, the vein resting, the eyes bright.
IDLE = rows_of([
    # left x 46-56    right x 57-66       y
    ("..........v", ".........."),   # 30  the vein rises to the parting...
    ("........1vv", "V2........"),   # 31  ...and opens into the portrait's red chevron
    ("......111v2", "V223......"),   # 32
    ("....1111v22", "2V2233...."),   # 33
    ("..11111v222", "222V3334.."),   # 34
    ("11ddddd2222", "223eeeee44"),   # 35  brows, level and easy
    ("12gggGGG222", "23GGGGGG44"),   # 36  glasses: top rims
    ("GgkkkkkkGGG", "GGkkkkkkGG"),   # 37  temples, lash lines, the bridge
    ("1GkXWnOXG12", "3GXWnOXkG4"),   # 38  eyes: lash flick, sclera, glint, pupil, iris
    ("1G22ooO3G12", "3G3ooO34G4"),   # 39  the iris's light lower half
    ("12GGGGGG212", "33GGGGGG44"),   # 40  bottom rims
    ("11222222212", "3233333344"),   # 41  cheeks, the nose's lit ridge
    ("11222222211", "4233333344"),   # 42  nose tip
    ("12222222343", "5333333344"),   # 43  nostrils
    ("12223dccccc", "ccdde33344"),   # 44  moustache
    ("k222dkkkkkk", "kkkkkd344k"),   # 45  the grin's upper line
    ("k222dkWWWWW", "WWWXkd344k"),   # 46  teeth
    ("k2223dkkkkk", "kkkkd3344k"),   # 47  lower line; the moustache drops at the corners
    (".k222221122", "33333444k."),   # 48  lower lip
    ("..k22232233", "3334445k.."),   # 49  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

# The flex: straining through the pose, the user's portrait brought to life. The vein swells into
# a thick forked ridge right up to the parting, the brows crush down into a V over a furrow, the
# eyes narrow to a hard stare, the cheeks bunch, and the teeth clench in the portrait's grimace
# with the moustache dragged down at the corners. A bead of sweat on the temple.
FLEX = rows_of([
    # left x 46-56    right x 57-66       y
    ("..........v", ".........."),   # 30  the vein swells up to the parting
    ("........1vV", "22........"),   # 31
    ("......111vV", "2233......"),   # 32
    ("....111vV22", "2vV233...."),   # 33  and forks
    ("..dddv22222", "222V3eee.."),   # 34  brows: outer ends high...
    ("1122ddddd34", "3eeeee3344"),   # 35  ...crushed down to a furrow
    ("12gggGGG234", "33GGGGGG44"),   # 36  glasses: top rims
    ("GgkkkkkkGGG", "GGkkkkkkGG"),   # 37  lash lines, the bridge
    ("1GkWOnOkG13", "4GkOnOWkG4"),   # 38  a hard stare
    ("1G23kkk3G12", "3G3kkk44G4"),   # 39  lower lids pushed up
    ("12GGGGGG212", "33GGGGGG44"),   # 40  bottom rims
    ("11112223212", "3322233344"),   # 41  cheeks bunched up
    ("11223422211", "4222433344"),   # 42  the creases beside the nose
    ("12234322453", "5423433344"),   # 43  nostrils flared
    ("123dccccccc", "cccddde444"),   # 44  moustache
    ("k2d4kkkkkkk", "kkkkkk4d4k"),   # 45  the grimace: top line
    ("k2dkWWWxWWx", "WWxXXXkd4k"),   # 46  clenched teeth
    ("k2dkXXXxXXx", "XXxxxxkd4k"),   # 47
    (".k3dkkkkkkk", "kkkkkkd4k."),   # 48  bottom line; the moustache dragged down
    ("..k22233333", "3334445k.."),   # 49  chin
    ("...kkkkkkkk", "kkkkkkk..."),   # 50  the jaw's keyline
])

# A bead of sweat on his right temple, over the mane (Matt's drops sit the same way).
SWEAT = {(66, 29): 'k',
         (65, 30): 'k', (66, 30): 'W', (67, 30): 'k',
         (65, 31): 'k', (66, 31): 'o', (67, 31): 'k',
         (64, 32): 'k', (65, 32): 'W', (66, 32): 'o', (67, 32): 'O', (68, 32): 'k',
         (64, 33): 'k', (65, 33): 'o', (66, 33): 'O', (67, 33): 'O', (68, 33): 'k',
         (65, 34): 'k', (66, 34): 'k', (67, 34): 'k'}

FACES = {'idle': IDLE, 'flex': FLEX}
EXTRAS = {'flex': SWEAT}


def face(name):
    rows = FACES[name]
    out = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


def head(name):
    """The mane with the face laid over it."""
    part = mane()
    part.update(face(name))
    part.update(EXTRAS.get(name, {}))
    return part


if __name__ == '__main__':
    print('faces', sorted(FACES), 'checked')
