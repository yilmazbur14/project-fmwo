"""Burak's trophy lift, facing the camera, in his own 7 colours at his normal 32x32 scale.

Every frame is written as row spans in BODY coordinates: the same coordinates as one cell of
player_4dir_sheet.png (x 0..31, y 0..31, shoes on rows 26-28, head centre column x = 15), with
rows above 0 (negative y) allowed for the arms and the trophy overhead.

    (y, x0, 'pixels')      '.' = leave clear

Symbols: K b s d r B c are Burak's measured palette. The FRONT layer (drawn over the trophy,
i.e. the gloves where they grip the plinth) uses g h G (glove b, c, B) and f F (skin s, d).

Layer order in a cell: stand < Burak < trophy < Burak's FRONT layer < effects.
"""
import os
from PIL import Image
from common import BURAK, ASSETS

FRONT = {'g': 'b', 'h': 'c', 'G': 'B', 'f': 's', 'F': 'd'}

# ---------------------------------------------------------------- shared parts
HEAD = [  # rows 0..6 of the head, x0 13, exactly the 4dir sheet's front face
    (0, 14, 'KKK'),
    (1, 13, 'KKKKK'),
    (2, 13, 'rKKKr'),
    (3, 13, 'rrKrr'),
    (4, 13, 'ssrss'),
    (5, 13, 'srsrs'),
]


def head(top, mouth=False, dx=0):
    rows = [(top + y, x + dx, p) for y, x, p in HEAD]
    rows.append((top + 6, 14 + dx, 'sKs' if mouth else 'sss'))
    return rows


# legs + shorts from the 4dir sheet's block frame (col 9), rows 17-28
LEGS_STAND = [
    (17, 13, 'bcbcbc'),
    (18, 13, 'bbbbbB'),
    (19, 12, 'bbbbbbbB'),
    (20, 11, 'bbbbbbbbbB'),
    (21, 11, 'bbbbbbbbbB'),
    (22, 11, 'bbbb..bbbB'),
    (23, 11, 'bbb....bbB'),
    (24, 11, 'sd......sd'),
    (25, 11, 'sd......sd'),
    (26, 11, 'KK......sd'),
    (27, 11, 'KK......KK'),
    (28, 19, 'KKK'),
]
# knees bent, stance a pixel wider each side: the shorts drop 2 rows
LEGS_CROUCH = [
    (19, 13, 'bcbcbc'),
    (20, 12, 'bbbbbbbB'),
    (21, 11, 'bbbbbbbbbB'),
    (22, 10, 'bbbbbbbbbbbB'),
    (23, 10, 'bbbb....bbbB'),
    (24, 10, 'sd.......sd'),
    (25, 10, 'sd........sd'),
    (26, 10, 'KK........sd'),
    (27, 10, 'KK........KK'),
    (28, 20, 'KKK'),
]
# on the lift: up on the balls of the feet, legs straight and planted wide
LEGS_LIFT = [
    (17, 13, 'bcbcbc'),
    (18, 13, 'bbbbbB'),
    (19, 12, 'bbbbbbbB'),
    (20, 11, 'bbbbbbbbbB'),
    (21, 11, 'bbbbbbbbbB'),
    (22, 10, 'bbbbb..bbbbB'),
    (23, 10, 'bbbb....bbbB'),
    (24, 10, 'sd......sd'),
    (25, 10, 'sd.......sd'),
    (26, 10, 'sd.......sd'),
    (27, 10, 'KK.......KK'),
    (28, 10, 'K.........KK'),
]


def shift(rows, dy=0, dx=0):
    return [(y + dy, x + dx, p) for y, x, p in rows]


# ---------------------------------------------------------------- frames
FRAMES = {}

# 0 ARRIVE: the 4dir sheet's idle_down cell, untouched (loaded from the sheet at build time)
FRAMES['arrive'] = 'SHEET:0,0'

# Arms are written as the LEFT arm's path (y, x of its 2-pixel 'sd' run) and mirrored about the
# head's centre column (x' = 30 - x): the right arm reads 'ds', lit on its outer side like the sheet.
def arms(path, gloves=None, front_from=None, dx=0):
    """path: [(y, x)] for the left arm. gloves: (y, x) top-left of the left 2x2 glove (FRONT layer).
    Rows at or below `front_from` (y) are drawn in the FRONT layer (forearms over the trophy)."""
    out = []
    for y, x in path:
        fl = front_from is not None and y >= front_from
        out.append((y, x + dx, 'fF' if fl else 'sd'))
        out.append((y, 29 - x + dx, 'Ff' if fl else 'ds'))
    if gloves:
        gy, gx = gloves
        out += [(gy, gx + dx, 'hg'), (gy + 1, gx + dx, 'gG'),
                (gy, 29 - gx + dx, 'gG'), (gy + 1, 29 - gx + dx, 'GG')]
    return out


TORSO = [  # the sheet's chest and abs, shoulders on row 10, no arms
    (10, 11, 'sssssssss'),
    (11, 11, 'sssdsdsss'),
    (12, 11, 'ssdsdsdss'),
    (13, 12, 'sssssss'),
    (14, 12, 'sssdsss'),
    (15, 13, 'ssdss'),
    (16, 13, 'sssss'),
]

# 1 TAKE IT IN: the guard drops, arms hang a little away from his sides, ready
FRAMES['take_in'] = head(4) + TORSO + arms(
    [(11, 9), (12, 9), (13, 9), (14, 8), (15, 8)], gloves=(16, 8)) + LEGS_STAND

# 2 REACH: leans in over the cup, arms swinging out round its handles
FRAMES['reach'] = head(6) + shift(TORSO, 2) + arms(
    [(13, 9), (14, 8), (15, 8), (16, 7), (17, 7), (18, 6), (19, 6), (20, 6), (21, 6)],
    gloves=(22, 5), front_from=20) + shift(LEGS_STAND[1:], 1)

# 3 GRAB: bowed low behind the cup, eyes just over its lip, gloves clamped on the plinth
_grab_arms = [(19, 9), (20, 8), (21, 7), (22, 6), (23, 6), (24, 6), (25, 6), (26, 6), (27, 6),
              (28, 6), (29, 7), (30, 7)]
FRAMES['grab'] = head(12) + shift(TORSO, 8) + arms(_grab_arms, gloves=(31, 7), front_from=26) + \
    LEGS_CROUCH[2:]

# 4 GATHER a/b: the strain that holds until the drop. a sinks a pixel; b heaves the cup a pixel
#   off the velvet (gloves with it). Loop a-b while waiting.
FRAMES['gather_a'] = head(13) + shift(TORSO, 9) + arms(_grab_arms[1:], gloves=(31, 7),
                                                         front_from=26) + LEGS_CROUCH[3:]
FRAMES['gather_b'] = head(13) + shift(TORSO, 9) + arms(_grab_arms[1:-1], gloves=(30, 7),
                                                         front_from=26) + LEGS_CROUCH[3:]

# 5 LIFT - THE DROP FRAME: full extension, the cup overhead, chest out, mouth open
_up = [(9, 10), (8, 10), (7, 9), (6, 9), (5, 9), (4, 8), (3, 8), (2, 8), (1, 8)]
FRAMES['lift'] = head(4, mouth=True) + TORSO + arms(_up, gloves=(-1, 7), front_from=1) + LEGS_LIFT
# 6 SETTLE: the overshoot comes back a pixel
FRAMES['settle'] = head(4, mouth=True) + TORSO + arms(_up[:-1], gloves=(0, 7), front_from=1) + \
    LEGS_LIFT

# 7-10 HOLD LOOP: pumps the cup - up + sway left, down, up + sway right, down; shouts on the ups
_bent = [(10, 10), (9, 10), (8, 9), (7, 8), (6, 7), (5, 6), (4, 6), (3, 7)]


def hold_up(dx):
    sway = [(y, x + (dx if y <= 4 else 0)) for y, x in _up]
    return head(4, mouth=True) + TORSO + arms(sway, front_from=1) + \
        arms([], gloves=(-1, 7), dx=dx) + LEGS_LIFT


def hold_down():
    return shift(head(4) + TORSO, 1) + [(18, 13, 'sssss')] + arms(_bent, gloves=(1, 7), front_from=3) +         LEGS_CROUCH


FRAMES['hold_1'] = hold_up(-1)
FRAMES['hold_2'] = hold_down()
FRAMES['hold_3'] = hold_up(1)
FRAMES['hold_4'] = hold_down()

ORDER = ['arrive', 'take_in', 'reach', 'grab', 'gather_a', 'gather_b', 'lift', 'settle',
         'hold_1', 'hold_2', 'hold_3', 'hold_4']

# ---------------------------------------------------------------- where the trophy is, per frame
# (dx, bottom_y) in body coordinates: the trophy's centre column on x = 15 + dx, its bottom
# (outline) row on y = bottom_y.  SEAT_Y is the stand's velvet row the cup rests on.
SEAT_Y = 34
TROPHY_AT = {
    'arrive': (0, SEAT_Y), 'take_in': (0, SEAT_Y), 'reach': (0, SEAT_Y), 'grab': (0, SEAT_Y),
    'gather_a': (0, SEAT_Y), 'gather_b': (0, SEAT_Y - 1),
    'lift': (0, 1), 'settle': (0, 2),
    'hold_1': (-1, 1), 'hold_2': (0, 3), 'hold_3': (1, 1), 'hold_4': (0, 3),
}


def sheet_cell(col, row):
    sheet = Image.open(os.path.join(ASSETS, 'Characters/MainPlayer/player_4dir_sheet.png')).convert('RGBA')
    return sheet.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))


def render(name, ox, oy, size):
    """Burak's back and front layers for one frame, body (0,0) at (ox, oy) in a `size` image."""
    back = Image.new('RGBA', size, (0, 0, 0, 0))
    front = Image.new('RGBA', size, (0, 0, 0, 0))
    spec = FRAMES[name]
    if isinstance(spec, str):
        c, r = map(int, spec.split(':')[1].split(','))
        back.paste(sheet_cell(c, r), (ox, oy))
        return back, front
    bp, fp = back.load(), front.load()
    for y, x0, pix in spec:
        for i, ch in enumerate(pix):
            if ch == '.':
                continue
            X, Y = ox + x0 + i, oy + y
            if not (0 <= X < size[0] and 0 <= Y < size[1]):
                raise ValueError(f'{name}: pixel off the cell at body ({x0 + i},{y})')
            if ch in FRONT:
                fp[X, Y] = BURAK[FRONT[ch]]
            else:
                bp[X, Y] = BURAK[ch]
    return back, front
