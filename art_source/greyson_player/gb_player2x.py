"""The player's brawl poses at exactly 2x (PLAN_BRAWL.md, "The staging decision" and section 7).

    player_final_brawl_2x   10 columns x 4 rows of 64x96 (640x384)

The contract, per cell (the Sprite2D is centred on the CharacterBody2D, scaled 3x, so a 2x texel is
3 px on screen and the player simply stands twice as tall):
  - the ground line (the soles' bottom edge) at y 61, which is 13 texels (39 px) below the origin at
    the cell centre (32, 48), exactly where it is at 1x; the sole texels are rows 59-60;
  - x centre at column 32;
  - every row the same back view, columns as approved: guard 0-1, slip L 2-3, slip R 4-5, parry 6-7,
    hit 8-9.

A 1x texel (x, y) of player_final_brawl (gb_player) lands on the 2x texels (2x..2x+1, 2y+3..2y+4): a
nearest-neighbour x2 about the ground line. `placeholder_cells()` is exactly that, the shippable
stand-in; the native redraw (drawn at 2x, not chunky) replaces it cell by cell once approved.

Nothing in this module writes anything.
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gb_player as G  # noqa: E402

W2, H2 = 64, 96
X0, Y0 = 0, 3                      # where the x2 of a 1x cell's (0, 0) lands in the 2x cell
GROUND = 61                        # the soles' bottom edge; sole texels on rows 59-60
ORIGIN = (32, 48)                  # the cell centre, which is the player's origin


def to2x(x, y):
    """A 1x texel's top-left corner in 2x cell texels."""
    return X0 + 2 * x, Y0 + 2 * y


def x2(px):
    """Nearest-neighbour x2 of a 1x cell ({(x, y): key}) into a 2x cell."""
    out = {}
    for (x, y), k in px.items():
        bx, by = to2x(x, y)
        for dx in (0, 1):
            for dy in (0, 1):
                out[(bx + dx, by + dy)] = k
    return out


def placeholder_cells():
    """[(name, 2x pixels)] for the ten columns: the approved 1x poses, x2, re-registered."""
    return [(name, x2(G.g(grid))) for name, grid in G.FRAMES]


def image2x(px):
    from PIL import Image
    im = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < W2 and 0 <= y < H2:
            im.putpixel((x, y), G.PAL[k])
    return im


def px_from_origin(x, y):
    """Continuous cell coordinates -> game px from the player's origin (scale 3)."""
    return ((x - ORIGIN[0]) * 3, (y - ORIGIN[1]) * 3)
