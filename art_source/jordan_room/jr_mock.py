"""Jordan's room - the 1920x1080 scale mock and the annotated layout sheet.

Reads character sprites from Assets/Characters (read-only) and pastes them at
game scale (x3) on the room: the player (first cell of player_4dir_sheet) at
the door, Jordan's idle at the desk as a stand-in, and Eric, Matt, Danny and
Liam on the open floor. Feet points are in native texels.
"""
import os

from PIL import Image, ImageDraw

from jr_lib import SCALE
from jr_geom import (WALKABLE, CHAIR_POINT, DESK_X0, DESK_X1, FLOOR_Y, DESK_FRONT_Y,
                     DESK_TOP_Y, DOOR_OPEN_X0, DOOR_OPEN_X1, DOOR_X0, DOOR_X1, DOOR_TOP)

PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
CHARS = os.path.join(PROJECT, 'Assets', 'Characters')

# (label, sheet, frame w, frame h, frame index, feet point in texels)
CAST = [
    ('Burak (player)', 'MainPlayer/player_4dir_sheet.png', 32, 32, 0, (72, 178)),
    ('Jordan (stand-in)', 'Jordan/jordan_idle.png', 96, 96, 0, CHAIR_POINT),
    ('Eric', 'Eric/eric_sheet_v2.png', 256, 192, 0, (178, 236)),
    ('Matt', 'Matt/matt_idle.png', 96, 96, 0, (560, 236)),
    ('Danny', 'Danny/Sumo/danny_sumo_idle.png', 176, 144, 0, (268, 340)),
    ('Liam', 'Liam/liam.png', 64, 64, 0, (474, 330)),
]


def frame(sheet, fw, fh, index):
    im = Image.open(os.path.join(CHARS, sheet)).convert('RGBA')
    cols = im.width // fw
    x, y = (index % cols) * fw, (index // cols) * fh
    return im.crop((x, y, x + fw, y + fh))


def cast_sprites():
    """[(label, image at x3, top-left in screen px, feet point)] sorted back to front."""
    out = []
    for (label, sheet, fw, fh, idx, (fx, fy)) in CAST:
        f = frame(sheet, fw, fh, idx)
        bb = f.getbbox()                                   # content bounds (alpha)
        feet_row = bb[3] - 1
        centre = (bb[0] + bb[2] - 1) / 2.0
        x0 = int(round(fx - centre))
        y0 = fy - feet_row
        big = f.resize((fw * SCALE, fh * SCALE), Image.NEAREST)
        out.append((label, big, (x0 * SCALE, y0 * SCALE), (fx, fy), (fw, fh), bb))
    out.sort(key=lambda t: t[3][1])
    return out


def scale_mock(room_3x):
    im = room_3x.convert('RGBA').copy()
    for (label, big, (sx, sy), feet, _, _) in cast_sprites():
        _paste(im, big, sx, sy)
    return im.convert('RGB')


def _paste(dst, src, x, y):
    layer = Image.new('RGBA', dst.size, (0, 0, 0, 0))
    layer.paste(src, (x, y), src)
    dst.alpha_composite(layer)


def annotated(room_3x):
    """The layout facts drawn over the room, for the coder (screen px = texel x 3)."""
    im = room_3x.convert('RGBA').copy()
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    s = SCALE
    poly = [(x * s + 1, y * s + 1) for (x, y) in WALKABLE]
    d.polygon(poly, fill=(95, 205, 228, 46), outline=(95, 205, 228, 255), width=3)
    d.rectangle([DESK_X0 * s, FLOOR_Y * s, (DESK_X1 + 1) * s - 1, DESK_FRONT_Y * s - 1],
                outline=(215, 123, 186, 255), width=3)
    d.rectangle([DESK_X0 * s, DESK_TOP_Y * s, (DESK_X1 + 1) * s - 1, DESK_FRONT_Y * s - 1],
                outline=(215, 123, 186, 140), width=1)
    cx, cy = CHAIR_POINT
    d.ellipse([cx * s - 14, cy * s - 14, cx * s + 16, cy * s + 16], outline=(172, 50, 50, 255),
              width=3)
    d.line([cx * s - 22, cy * s + 1, cx * s + 24, cy * s + 1], fill=(172, 50, 50, 255), width=3)
    d.line([cx * s + 1, cy * s - 22, cx * s + 1, cy * s + 24], fill=(172, 50, 50, 255), width=3)
    d.line([DOOR_OPEN_X0 * s, FLOOR_Y * s, (DOOR_OPEN_X1 + 1) * s, FLOOR_Y * s],
           fill=(251, 242, 54, 255), width=5)
    d.rectangle([DOOR_X0 * s, DOOR_TOP * s, (DOOR_X1 + 1) * s - 1, FLOOR_Y * s - 1],
                outline=(251, 242, 54, 200), width=2)
    notes = [
        ((DOOR_X0 * s, DOOR_TOP * s - 26), 'DOOR: opening x %d-%d, threshold y %d' %
         (DOOR_OPEN_X0, DOOR_OPEN_X1, FLOOR_Y), (251, 242, 54)),
        ((DESK_X0 * s, DESK_FRONT_Y * s + 8), 'DESK footprint x %d-%d, y %d-%d' %
         (DESK_X0, DESK_X1, FLOOR_Y, DESK_FRONT_Y - 1), (215, 123, 186)),
        ((cx * s + 26, cy * s + 20), 'CHAIR_POINT (%d, %d)' % (cx, cy), (255, 120, 120)),
        ((20 * s, 300 * s), 'WALKABLE floor (texels): see report', (95, 205, 228)),
    ]
    for (xy, txt, col) in notes:
        x, y = xy
        w = 7 * len(txt) + 10
        d.rectangle([x - 4, y - 3, x + w, y + 15], fill=(0, 0, 0, 200))
        d.text((x, y), txt, fill=col + (255,))
    im.alpha_composite(ov)
    return im.convert('RGB')
