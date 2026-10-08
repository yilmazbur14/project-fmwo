"""The player's fake-moustache gag: player_moustache (8 columns x 4 rows of 32x32) and moustache_prop
(5 frames of 16x16).

Everything is drawn in the player's own style, measured off Assets/Characters/MainPlayer/
player_4dir_sheet.png: 7 flat colours, no keyline (his black is his hair and shoes), no shading ramp
beyond his own two skin tones and three blues, alpha 0/255 only. Every frame is one of his own
frames edited, so his head, body, sole row and centre column are his pixels exactly.

The moustache is black, his hair's colour: a bar wider than his face with the ends drooping (a big,
obviously fake horseshoe), and in profile the same bar under his nose with its end hanging down.

Rows (the sheet's order): 0 DOWN, 1 UP (his back: the moustache is behind his head), 2 LEFT, 3 RIGHT.
Columns: 0 idle with the moustache, 1 reach, 2 press, 3 done / smug, 4 tap wind-up, 5 tap,
6 talk (open mouth), 7 caught (no moustache).
LEFT is RIGHT mirrored (x' = 31 - x), exactly as the source sheet's LEFT row is.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jfc_base as B  # noqa: E402
from PIL import Image  # noqa: E402

CELL = 32
COLS = ['idle', 'reach', 'press', 'done', 'tap_windup', 'tap', 'talk', 'caught']
ROWS = ['DOWN', 'UP', 'LEFT', 'RIGHT']

# his palette, keyed like the drafts
PPAL = {'K': (0, 0, 0, 255), 'B': (36, 100, 189, 255), 's': (215, 152, 100, 255), 'd': (172, 113, 79, 255),
        'r': (172, 50, 50, 255), 'N': (22, 47, 187, 255), 'L': (56, 131, 201, 255)}
KEYS = {v[:3]: k for k, v in PPAL.items()}

# the moustache on his face, per facing, in cell pixels (MOUSTACHE_LIP is the first texel of each)
STACHE = {
    'DOWN': [(15, 10), (13, 10), (14, 10), (16, 10), (17, 10), (13, 11), (17, 11)],
    'RIGHT': [(18, 9), (17, 9), (18, 10)],
}
STACHE['LEFT'] = [(31 - x, y) for (x, y) in STACHE['RIGHT']]
MOUSTACHE_LIP = {'DOWN': STACHE['DOWN'][0], 'LEFT': STACHE['LEFT'][0], 'RIGHT': STACHE['RIGHT'][0],
                 'UP': None}


def source():
    return Image.open(B.PLAYER_SHEET).convert('RGBA')


def cell_px(sheet, row, col):
    """{(x, y): key} for one of his cells."""
    out = {}
    for y in range(CELL):
        for x in range(CELL):
            c = sheet.getpixel((col * CELL + x, row * CELL + y))
            if c[3]:
                out[(x, y)] = KEYS[c[:3]]
    return out


def apply(px, edits):
    """edits: [(x, y, key)], key '.' clears."""
    px = dict(px)
    for (x, y, k) in edits:
        if k == '.':
            px.pop((x, y), None)
        else:
            px[(x, y)] = k
    return px


def stache(facing):
    return [(x, y, 'K') for (x, y) in STACHE[facing]]


def glove(x, y, key='B'):
    return [(x, y, key), (x + 1, y, key), (x, y + 1, key), (x + 1, y + 1, key)]


def clear(pts):
    return [(x, y, '.') for (x, y) in pts]


# a sweat drop in his own light blue (he has no white): the "caught" beat
def drop(x, y):
    return [(x, y, 'L'), (x - 1, y + 1, 'L'), (x, y + 1, 'L'), (x, y + 2, 'B')]


#DOWN (facing the camera: the gag is put on here)

def down(sheet):
    base = cell_px(sheet, 0, 0)
    rg = [(18, 9), (19, 9), (18, 10), (19, 10)]            # his right-side glove at rest
    lg = [(11, 8), (12, 8), (11, 9), (12, 9)]
    f = {}
    f['idle'] = apply(base, stache('DOWN'))
    # reach: the glove comes in under his chin, the moustache held on top of it
    f['reach'] = apply(base, clear(rg) + [(14, 11, 'K'), (15, 11, 'K'), (16, 11, 'K'), (17, 11, 'K'),
                                          (18, 11, 'K'), (14, 12, 'K'), (18, 12, 'K')] + glove(16, 12))
    # press: the glove flat over his mouth, the moustache's ends showing either side of it
    f['press'] = apply(base, clear(rg) + [(13, 10, 'K'), (14, 10, 'K'), (17, 10, 'K'), (13, 11, 'K'),
                                          (17, 11, 'K')] + glove(15, 10))
    # done / smug: moustache on, fists on his hips, elbows out
    f['done'] = apply(base, clear(rg + lg) + [(11, 10, '.'), (12, 10, '.')] + stache('DOWN') +
                      [(10, 12, 's'), (10, 13, 'd'), (10, 14, 's'), (20, 12, 's'), (20, 13, 'd'), (20, 14, 's')] +
                      glove(10, 15) + glove(19, 15))
    # tap wind-up: his glove raised beside his head
    f['tap_windup'] = apply(base, clear(rg) + stache('DOWN') + [(20, 10, 's'), (20, 9, 'd'), (20, 8, 's')] +
                            glove(19, 6))
    # tap: the arm reaching up and out
    f['tap'] = apply(base, clear(rg) + stache('DOWN') + [(20, 10, 's'), (21, 9, 's'), (22, 8, 'd')] +
                     glove(22, 6))
    # talk: the moustache on, his mouth open under it (red, like his other features)
    f['talk'] = apply(base, stache('DOWN') + [(14, 11, 'r'), (15, 11, 'r'), (16, 11, 'r')])
    # caught: no moustache, fists snapped up to his face (his block pose), a sweat drop
    f['caught'] = apply(cell_px(sheet, 0, 9), drop(20, 4))
    return f


#RIGHT (and LEFT, its mirror): the tap and the talk happen facing right

def right(sheet):
    base = cell_px(sheet, 3, 0)
    ng = [(19, 8), (20, 8), (19, 9), (20, 9)]              # the near glove at rest, before his face
    f = {}
    f['idle'] = apply(base, stache('RIGHT'))
    # reach: the glove drops to under his chin, the moustache poking out of its top
    f['reach'] = apply(base, clear(ng) + glove(18, 10) + [(19, 9, 'K'), (20, 9, 'K')])
    # press: the glove over his mouth, the moustache's back end showing behind it
    f['press'] = apply(base, clear(ng) + [(17, 9, 'K')] + glove(18, 9))
    # done / smug: moustache on, the near fist on his hip
    f['done'] = apply(base, clear(ng) + stache('RIGHT') + [(19, 12, 'd'), (19, 13, 's'), (19, 14, 'd')] +
                      glove(18, 15))
    # tap wind-up: the arm lifts, the glove up by his brow
    f['tap_windup'] = apply(base, clear(ng) + stache('RIGHT') + [(19, 9, 'd'), (20, 8, 's'), (20, 7, 'd')] +
                            glove(20, 5))
    # tap: the arm stretched up and forward, the glove out at shoulder-tap height
    f['tap'] = apply(base, clear(ng) + stache('RIGHT') + [(19, 9, 'd'), (20, 8, 's'), (21, 7, 's'),
                                                          (22, 6, 'd')] + glove(23, 4))
    # talk: the moustache on, the mouth open under its front
    f['talk'] = apply(base, stache('RIGHT') + [(17, 10, 'r')])
    # caught: no moustache, fists up (his block pose), a sweat drop behind his head
    f['caught'] = apply(cell_px(sheet, 3, 9), drop(13, 3))
    return f


def mirror_frames(frames):
    return {k: {(31 - x, y): v for (x, y), v in px.items()} for k, px in frames.items()}


#UP (his back to the camera: the moustache is on his far side)

def up(sheet):
    base = cell_px(sheet, 1, 0)
    rg = [(18, 8), (19, 8), (18, 9), (19, 9)]
    lg = [(11, 9), (12, 9), (11, 10), (12, 10)]
    f = {}
    f['idle'] = dict(base)
    # reach: one glove comes up beside his head (the hand going to his face, out of sight)
    f['reach'] = apply(base, clear(rg) + [(18, 8, 'd')] + glove(18, 6))
    # press: both gloves up at the sides of his head
    f['press'] = apply(base, clear(rg + lg) + [(18, 8, 'd'), (12, 9, 's'), (12, 8, 'd')] + glove(18, 6) +
                       glove(11, 6))
    # done: fists on his hips, elbows out
    f['done'] = apply(base, clear(rg + lg) + [(10, 12, 's'), (10, 13, 'd'), (10, 14, 's'), (20, 12, 's'),
                                              (20, 13, 'd'), (20, 14, 's')] + glove(10, 15) + glove(19, 15))
    # tap wind-up / tap: his own raised-arm frames (the up punch's rise and reach)
    f['tap_windup'] = cell_px(sheet, 1, 7)
    f['tap'] = cell_px(sheet, 1, 8)
    # talk: a glove lifted in a gesture
    f['talk'] = apply(base, clear([(18, 9), (19, 9)]) + [(18, 7, 'B'), (19, 7, 'B')])
    # caught: fists up (his block pose), a sweat drop
    f['caught'] = apply(cell_px(sheet, 1, 9), drop(20, 3))
    return f


def frames():
    """{row name: {col name: px}}"""
    sheet = source()
    r = right(sheet)
    return {'DOWN': down(sheet), 'UP': up(sheet), 'LEFT': mirror_frames(r), 'RIGHT': r}


def image(px, w=CELL, h=CELL):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for (x, y), k in px.items():
        if 0 <= x < w and 0 <= y < h:
            im.putpixel((x, y), PPAL[k])
    return im


def sheet_image():
    fr = frames()
    out = Image.new('RGBA', (CELL * len(COLS), CELL * len(ROWS)), (0, 0, 0, 0))
    for ri, rn in enumerate(ROWS):
        for ci, cn in enumerate(COLS):
            out.alpha_composite(image(fr[rn][cn]), (ci * CELL, ri * CELL))
    return out


#THE LOOSE MOUSTACHE (16x16, pivot (8, 8)): the same horseshoe, tumbling as it drifts down

PROP = [
    # 0: level, as it sat on his lip
    [(6, 8), (7, 8), (8, 8), (9, 8), (10, 8), (6, 9), (10, 9)],
    # 1: tipping right-end down
    [(6, 7), (7, 7), (8, 8), (9, 8), (10, 8), (6, 8), (10, 9)],
    # 2: the air flips its ends up (a cup)
    [(6, 8), (10, 8), (6, 9), (7, 9), (8, 9), (9, 9), (10, 9)],
    # 3: tipping left-end down
    [(10, 7), (9, 7), (8, 8), (7, 8), (6, 8), (10, 8), (6, 9)],
    # 4: landed, lying flat on the floor: the two lobes splayed, its lowest texel on row 15
    [(7, 14), (8, 14), (9, 14), (6, 15), (7, 15), (9, 15), (10, 15)],
]
PROP_PIVOT = (8, 8)


def prop_image():
    out = Image.new('RGBA', (16 * len(PROP), 16), (0, 0, 0, 0))
    for i, pts in enumerate(PROP):
        for (x, y) in pts:
            out.putpixel((i * 16 + x, y), PPAL['K'])
    return out


def measure_source():
    """His sheet's own numbers: colours, black ratio, alpha levels."""
    im = source()
    data = list(im.get_flattened_data())
    op = [c for c in data if c[3]]
    return {'colours': len({c[:3] for c in op}), 'black': sum(1 for c in op if c[:3] == (0, 0, 0)) / len(op),
            'alpha': sorted({c[3] for c in data})}


if __name__ == '__main__':
    print('source', measure_source())
    im = sheet_image()
    data = list(im.get_flattened_data())
    op = [c for c in data if c[3]]
    print('sheet', im.size, 'colours', len({c[:3] for c in op}), 'black %.3f' % (sum(1 for c in op if c[:3] == (0, 0, 0)) / len(op)),
          'alpha', sorted({c[3] for c in data}))
    print('MOUSTACHE_LIP', MOUSTACHE_LIP)
