"""Previews for the approval pass.

  scale : the new frames at 3x game scale standing on the arena mat (Assets/Environment/arena_mat.png,
          itself drawn at 3x) beside the player (player_4dir_sheet.png, 32x32 frames at 3x).
  before_after : the approved sumo idle next to the redesign at 4x on a dark background, with the
          small form beside them for identity.

  python previews.py <sheet.png> <out-dir>
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CHAR = os.path.join(ROOT, 'Assets', 'Characters')
FW, FH = 176, 144
BG = (46, 49, 58, 255)


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def frames(sheet):
    return [sheet.crop((i * FW, 0, i * FW + FW, FH)) for i in range(sheet.width // FW)]


def scale_preview(sheet, out):
    """Each frame at 3x on the mat, anchor (88, 144) planted, with the player at 3x in front."""
    mat = Image.open(os.path.join(ROOT, 'Assets', 'Environment', 'arena_mat.png')).convert('RGBA')
    mat3 = up(mat, 3)                                       # 1695 x 855, as the arena draws it
    player = Image.open(os.path.join(CHAR, 'MainPlayer', 'player_4dir_sheet.png')).convert('RGBA')
    p_back = player.crop((0, 32, 32, 64))                   # frame 10: the default, facing the boss
    p_side = player.crop((0, 64, 32, 96))                   # row 2: side-on, for a height read
    fr = frames(sheet)
    panels = []
    for f in fr:
        # a window of the mat around the ring's centre
        win = mat3.crop((340, 60, 1360, 800)).copy()        # 1020 x 740
        ax, ay = 500, 470                                   # where the anchor (88, 144) lands
        win.alpha_composite(up(f, 3), (ax - 88 * 3, ay - 144 * 3))
        # the player a couple of steps in front and to the side, feet on the same kind of line
        win.alpha_composite(up(p_back, 3), (ax - 330, ay + 150))
        win.alpha_composite(up(p_side, 3), (ax + 250, ay - 29 * 3))
        panels.append(win)
    w = sum(p.width for p in panels) + 20 * (len(panels) - 1)
    sheet_im = Image.new('RGBA', (w, panels[0].height), BG)
    x = 0
    for p in panels:
        sheet_im.alpha_composite(p, (x, 0))
        x += p.width + 20
    sheet_im.save(os.path.join(out, 'danny_redesign_3x_on_mat.png'))
    return sheet_im


def before_after(sheet, out, s=4):
    old = Image.open(os.path.join(CHAR, 'Danny', 'Sumo', 'danny_sumo_idle.png')).convert('RGBA').crop((0, 0, FW, FH))
    small = Image.open(os.path.join(CHAR, 'Danny', 'danny.png')).convert('RGBA').crop((0, 0, 64, 64))
    fr = frames(sheet)
    # the small form stands on the same floor line, at its in-game size relative to the big one
    small_panel = Image.new('RGBA', (64 + 16, FH), (0, 0, 0, 0))
    small_panel.alpha_composite(small, (8, FH - 64))
    tiles = [small_panel, old] + fr
    pad = 12
    w = sum(t.width for t in tiles) + pad * (len(tiles) + 1)
    im = Image.new('RGBA', (w, FH + 2 * pad), BG)
    x = pad
    for t in tiles:
        im.alpha_composite(t, (x, pad))
        x += t.width + pad
    big = up(im, s)
    big.save(os.path.join(out, 'danny_redesign_before_after_%dx.png' % s))
    return big


if __name__ == '__main__':
    sheet = Image.open(sys.argv[1]).convert('RGBA')
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    scale_preview(sheet, out)
    before_after(sheet, out)
