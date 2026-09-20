"""Zoomed previews of the punch FX over the player's real punch frames, with today's hitbox (red) and the
proposed v2 box (green). Writes into the folder given on the command line, never into the project.

    python preview.py OUT_DIR
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw

import design as D
import punchfx_art as A

PROJ = 'C:/Users/theyi/OneDrive/Documents/new-game-project/'
SHEET = PROJ + 'Assets/Characters/MainPlayer/player_4dir_sheet.png'
CELL = A.SWOOSH_CELL
HALF = CELL // 2


def player_cell(sheet, row, col):
    """The player's 32x32 frame centred in a CELL x CELL canvas, like the swoosh cells."""
    out = Image.new('RGBA', (CELL, CELL), (0, 0, 0, 0))
    out.alpha_composite(sheet.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)), (HALF - 16, HALF - 16))
    return out


def outline(draw, box, zoom, colour):
    x, y, w, h = box
    x0, y0 = (x + HALF) * zoom, (y + HALF) * zoom
    x1, y1 = (x + w + HALF) * zoom - 1, (y + h + HALF) * zoom - 1
    draw.rectangle((round(x0), round(y0), round(x1), round(y1)), outline=colour, width=2)


def facing_strip(sheet, swoosh, facing, zoom=8, bg=(118, 170, 84, 255)):
    """Wind-up, launch, full extension, afterimage, idle, for one facing."""
    steps = [(6, None, 'col 6'), (7, 0, 'col 7 + swoosh 0'), (8, 1, 'col 8 + swoosh 1'), (0, 2, 'idle + swoosh 2')]
    tiles = []
    for col, frame, label in steps:
        base = Image.new('RGBA', (CELL, CELL), bg)
        base.alpha_composite(player_cell(sheet, facing, col))
        if frame is not None:
            base.alpha_composite(swoosh.crop((frame * CELL, facing * CELL, frame * CELL + CELL, facing * CELL + CELL)))
        big = base.resize((CELL * zoom, CELL * zoom), Image.NEAREST)
        d = ImageDraw.Draw(big)
        outline(d, D.CURRENT_BOXES[facing], zoom, (255, 60, 60, 255))
        outline(d, D.V2_BOXES[facing], zoom, (80, 255, 80, 255))
        d.text((6, 4), '%s  %s' % (D.FACINGS[facing], label), fill=(255, 255, 255, 255))
        tiles.append(big)
    w = sum(t.width for t in tiles) + 6 * (len(tiles) - 1)
    strip = Image.new('RGBA', (w, tiles[0].height), (25, 25, 30, 255))
    x = 0
    for t in tiles:
        strip.paste(t, (x, 0))
        x += t.width + 6
    return strip


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    sheet = Image.open(SHEET).convert('RGBA')
    swoosh = A.swoosh_sheet()
    strips = [facing_strip(sheet, swoosh, f) for f in (1, 0, 2, 3)]
    w = max(s.width for s in strips)
    h = sum(s.height for s in strips) + 6 * (len(strips) - 1)
    board = Image.new('RGBA', (w, h), (25, 25, 30, 255))
    y = 0
    for s in strips:
        board.paste(s, (0, y))
        y += s.height + 6
    board.save(os.path.join(out_dir, 'swoosh_over_frames.png'))
    stars = A.star_sheet()
    z = 10
    big = stars.resize((stars.width * z, stars.height * z), Image.NEAREST)
    bg = Image.new('RGBA', big.size, (118, 170, 84, 255))
    bg.alpha_composite(big)
    bg.save(os.path.join(out_dir, 'star_sheet_zoom.png'))
    print('previews ->', out_dir)


if __name__ == '__main__':
    main(sys.argv[1])
