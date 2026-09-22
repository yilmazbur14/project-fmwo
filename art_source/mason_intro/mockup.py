"""python mockup.py  - the trail as it is actually used.

The intro runs the trail DOWN the screen: Mason comes through the doorway at the
top of the arena and walks toward the camera, so the line of pieces is vertical
and each fry lies across it like a rung.  (Checked against the intro's own
capture, art_source/mason_intro/out/01_trail_laid.png.)  A strip of pieces in a
row says nothing about whether a line of them reads as a trail, so this lays
them out the way the game does, at SCALE 3 on the mat's own green, with Mason
partway along: residue behind him, full fries ahead.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fries  # noqa: E402

ROOT = r'C:/Users/theyi/OneDrive/Documents/new-game-project'
SHEET = os.path.join(ROOT, 'Assets/Characters/Mason/mason_sheet.png')
MAT = os.path.join(ROOT, 'Assets/Environment/arena_mat.png')
S = 3                       # Mason's SCALE
MASON_EAT = 9               # frames.EAT_SHUT: mid-chomp, carton in hand

# (frame, flip_h) from the doorway down.  Flipping is safe: these are lit from
# above, so a mirror moves only the one darkened cut end.
PLAN = [(5, False), (6, True), (5, True), (6, False), (5, False),
        (0, True), (3, False), (1, False), (4, False), (0, False),
        (2, True), (1, True), (0, True)]
HERO = 5                    # the stop Mason is standing at
SPACING = 66                # screen px between stops
LANE = 200                  # screen x of the trail


def main():
    sheet = Image.open(SHEET).convert('RGBA')
    trail = Image.open(os.path.join(HERE, 'fry_trail.png')).convert('RGBA')
    mat = Image.open(MAT).convert('RGB')

    h = 90 + SPACING * (len(PLAN) - 1) + 90
    bg = Image.new('RGB', (400, h))
    for x in range(0, 400, mat.width):        # the mat's own green, tiled
        for y in range(0, h, mat.height):
            bg.paste(mat, (x, y))
    out = bg.convert('RGBA')

    for i, (f, flip) in enumerate(PLAN):
        piece = trail.crop((f * fries.FW, 0, (f + 1) * fries.FW, fries.FH))
        if flip:
            piece = piece.transpose(Image.FLIP_LEFT_RIGHT)
        piece = piece.resize((piece.width * S, piece.height * S), Image.NEAREST)
        # A trail is not a ruler: nudge every stop off the lane.
        dx = (-14, 9, 3, -7, 16)[i % 5]
        out.alpha_composite(piece, (LANE + dx - piece.width // 2,
                                    90 + SPACING * i - piece.height // 2))

    m = sheet.crop((MASON_EAT * 64, 0, (MASON_EAT + 1) * 64, 64))
    m = m.resize((64 * S, 64 * S), Image.NEAREST)
    out.alpha_composite(m, (LANE - m.width // 2, 90 + SPACING * HERO - m.height + 22))

    path = os.path.join(HERE, 'trail_mockup.png')
    out.convert('RGB').save(path)
    print(path, out.size)
    return 0


if __name__ == '__main__':
    sys.exit(main())
