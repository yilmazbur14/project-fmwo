"""Greyson's pose-sheet faces, on the approved face grid (gr_face: x 46-66, 21 columns, from row
30; every row written as left x 46-56 and right x 57-66 so the widths are checked). Both are
INVENTED for this job, built from the approved flex face's parts; no new colours.

  'wince'    the spoiled pose's hit: the flex face's swollen vein and crushed brows, the eyes
             squeezed shut behind the lenses (a black line with the lids bunched round it), the
             clenched teeth kept. Knocked out of his pose.
  'annoyed'  the hold after it: the flex face's hard stare and furrow, the grimace pressed shut
             into a flat, down-turned mouth under the moustache's horseshoe. Hmph.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gp_base as G  # noqa: E402

gr_face = G.gr_face
FX0, FY0 = gr_face.FX0, gr_face.FY0
rows_of = gr_face.rows_of
FLEX = gr_face.FLEX

WINCE = FLEX[:8] + rows_of([
    # left x 46-56    right x 57-66       y
    ("1G3kkkk3G13", "4G4kkkk4G4"),   # 38  eyes squeezed shut
    ("1G234443G12", "3G344444G4"),   # 39  the lower lids bunched up under them
]) + FLEX[10:]

ANNOYED = FLEX[:14] + rows_of([
    # left x 46-56    right x 57-66       y
    ("123dccccccc", "cccddde444"),   # 44  the moustache
    ("k2d42222222", "2223333d4k"),   # 45  its horseshoe ends hang either side of the mouth
    ("k2d22kkkkkk", "kkkk333d4k"),   # 46  the mouth pressed into a flat line...
    ("k2d2k222111", "2223k33d4k"),   # 47  ...its corners turned down; the lower lip's light
    (".k3d2223333", "333344d4k."),   # 48
]) + FLEX[19:]

FACES = {'wince': WINCE, 'annoyed': ANNOYED}


def _check():
    for name, rows in FACES.items():
        assert len(rows) == len(FLEX), (name, len(rows))
        for i, r in enumerate(rows):
            assert len(r) == 21, (name, FY0 + i, r, len(r))
            assert set(r) <= set(G.K.PAL) | {'.'}, (name, FY0 + i, r)


_check()


def face(name):
    out = {}
    for r, row in enumerate(FACES[name]):
        for c, ch in enumerate(row):
            if ch != '.':
                out[(FX0 + c, FY0 + r)] = ch
    return out


if __name__ == '__main__':
    for n, rows in FACES.items():
        print(n)
        for i, r in enumerate(rows):
            print('  %d %s' % (FY0 + i, r))
