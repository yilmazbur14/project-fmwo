"""Builds the punch FX images from design.py. Pure drawing: build.py writes them into the project.

punch_swoosh.png   3 columns x 4 rows of 48x48 cells. Rows are PlayerScript.Facing (down, up, left,
                   right), like player_4dir_sheet.png; a cell's centre is the player frame's centre, so
                   the sheet draws at the player's own position and 2x scale, texel for texel.
punch_hit_star.png 3 columns x 2 rows of 21x21 cells, centred: row 0 a landed punch, row 1 the charged
                   third punch of a combo.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image

import design as D

SWOOSH_CELL = 48
STAR_CELL = 21

# A star frame is one quadrant, top-left, including the centre row and column; the rest is mirrored.
# '.' is clear. The quadrant's bottom-right character is the centre texel.
STAR_NORMAL = [
    [  # 0: the contact, held through the hit-stop: a plump white star with a black rim, 11x11.
        "...........",
        "...........",
        "...........",
        "...........",
        "...........",
        "..........K",
        "......P..KW",
        ".........KW",
        "........KCW",
        "......KKCWW",
        ".....KWWWWW",
    ],
    [  # 1: it bursts: the core opens into a diamond and the points fly out as streaks, 13x13.
        "...........",
        "...........",
        "...........",
        "...........",
        "..........W",
        "..........W",
        "..........C",
        ".......C...",
        "..........P",
        ".........P.",
        "....WWC.P..",
    ],
    [  # 2: specks where the points went.
        "...........",
        "...........",
        "...........",
        "...........",
        "..........b",
        "...........",
        "......C....",
        "...........",
        "...........",
        "...........",
        "....b......",
    ],
]
STAR_CHARGED = [
    [  # 0: bigger and gold, for the charged third punch of a combo, 15x15.
        "...........",
        "...........",
        "...........",
        "..........K",
        ".........KW",
        ".....Y...KW",
        ".........KY",
        "........KYW",
        ".......KOWW",
        "....KKKYWWW",
        "...KWWYWWWW",
    ],
    [  # 1: the burst, a gold diamond and long streaks, 17x17.
        "...........",
        "...........",
        "..........W",
        "..........W",
        "..........Y",
        "..........O",
        "......Y....",
        "..........Y",
        ".........Y.",
        "........Y..",
        "..WWYO.Y...",
    ],
    [  # 2: specks.
        "...........",
        "...........",
        "..........O",
        "...........",
        "...........",
        ".....O.....",
        "...........",
        "...........",
        "...........",
        "...........",
        "..O........",
    ],
]


def _rgba(ch):
    r, g, b = D.PAL[ch]
    return (r, g, b, 255)


def mirrored_star(quadrant):
    """A STAR_CELL canvas from an 11x11 quadrant whose last row and column are the centre ones."""
    n = len(quadrant)
    assert all(len(row) == n for row in quadrant) and 2 * n - 1 == STAR_CELL
    img = Image.new('RGBA', (STAR_CELL, STAR_CELL), (0, 0, 0, 0))
    for y in range(STAR_CELL):
        qy = y if y < n else STAR_CELL - 1 - y
        for x in range(STAR_CELL):
            qx = x if x < n else STAR_CELL - 1 - x
            ch = quadrant[qy][qx]
            if ch != '.':
                img.putpixel((x, y), _rgba(ch))
    return img


def star_sheet():
    rows = [STAR_NORMAL, STAR_CHARGED]
    sheet = Image.new('RGBA', (STAR_CELL * 3, STAR_CELL * 2), (0, 0, 0, 0))
    for r, frames in enumerate(rows):
        for f, quadrant in enumerate(frames):
            sheet.alpha_composite(mirrored_star(quadrant), (f * STAR_CELL, r * STAR_CELL))
    return sheet


def swoosh_cell(facing, frame):
    rows = D.SWOOSH[frame]
    assert len(rows) == D.ACROSS and all(len(r) == D.ALONG for r in rows), frame
    img = Image.new('RGBA', (SWOOSH_CELL, SWOOSH_CELL), (0, 0, 0, 0))
    half = SWOOSH_CELL // 2
    for c, row in enumerate(rows):
        for a, ch in enumerate(row):
            if ch == '.':
                continue
            x, y = D.texel_of(facing, a, c)
            img.putpixel((x + half, y + half), _rgba(ch))
    return img


def swoosh_sheet():
    sheet = Image.new('RGBA', (SWOOSH_CELL * len(D.SWOOSH), SWOOSH_CELL * 4), (0, 0, 0, 0))
    for facing in range(4):
        for frame in range(len(D.SWOOSH)):
            sheet.alpha_composite(swoosh_cell(facing, frame), (frame * SWOOSH_CELL, facing * SWOOSH_CELL))
    return sheet


def used_rect(img):
    """(x0, y0, x1, y1) of the opaque pixels, exclusive end, or None."""
    return img.getbbox()
