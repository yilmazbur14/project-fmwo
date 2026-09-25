"""Put perch frames on the arena at game scale: 3x, the anchor (96,151) on the perch point, the top rope
drawn over him as the arena draws it (z 1), and optionally the HUD boxes (which the fight fades while he
is perched) and the player for scale."""
import os

from PIL import Image, ImageDraw

import arena_bg
from common import ANCHOR, ROOT, ROPE

SCALE = 3
PERCH_X = 960
PERCH_Y = arena_bg.TOP_ROPE_Y + (ANCHOR[1] - ROPE) * SCALE      # 445 for ROPE 36


def up(im, s):
    return im.resize((im.width * s, im.height * s), Image.NEAREST)


def player(facing_row=1, col=0):
    sheet = Image.open(os.path.join(ROOT, 'Assets', 'Characters', 'MainPlayer', 'player_4dir_sheet.png'))
    return up(sheet.convert('RGBA').crop((col * 32, facing_row * 32, col * 32 + 32, facing_row * 32 + 32)), 3)


def place(bg, frame, x=PERCH_X, y=PERCH_Y):
    """Composite one frame with its anchor at (x, y); returns the frame's top-left on screen."""
    big = up(frame, SCALE)
    tl = (x - ANCHOR[0] * SCALE, y - ANCHOR[1] * SCALE)
    bg.alpha_composite(big, (max(0, tl[0]), max(0, tl[1])),
                       (max(0, -tl[0]), max(0, -tl[1])))
    return tl


def hud_boxes(img, alpha=70, outline=190):
    """Mark the boss bar and name plate. Drawn on an overlay and composited: ImageDraw on an RGBA image
    replaces pixels (alpha too) instead of blending them."""
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for box, col in ((arena_bg.HUD_BAR, (255, 60, 60)), (arena_bg.HUD_PLATE, (80, 200, 255))):
        d.rectangle(box, fill=col + (alpha,), outline=col + (outline,), width=3)
    img.alpha_composite(over)


def scene(frame, hud=True, with_player=True, player_at=(1180, 760)):
    bg = arena_bg.arena(ropes=False)
    if with_player:
        p = player()
        bg.alpha_composite(p, (player_at[0] - 48, player_at[1] - 80))
    place(bg, frame)
    arena_bg.top_ropes(bg)
    if hud:
        hud_boxes(bg)
    return bg


def crop_around(img, w=640, h=560, cx=PERCH_X, top=0):
    return img.crop((cx - w // 2, top, cx + w // 2, top + h))
