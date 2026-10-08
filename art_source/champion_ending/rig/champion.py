"""Composes the champion sheet: Burak < stand < trophy < Burak's grip < effects, per 40x64 cell.

Cell registration: body (0,0) of the 4dir sheet's 32x32 cell sits at BODY_AT in every cell, so
the 32x32 body box spans cell x 4..35, y 21..52, and the player's own sprite centre (body 16,16)
is cell (20, 37).
"""
import sys
sys.dont_write_bytecode = True
from PIL import Image
import trophy as T
import burak as BK
import fx as FX
from common import paste, grid_to_image, PROP

CELL = (40, 64)
BODY_AT = (4, 21)
STAND_AT = (15 - T.S['CX'], BK.SEAT_Y - T.S['SEAT_Y'])     # body coords of the stand's top-left

# spark anchor on each trophy (trophy-local): A = the lit left lip, B = the star finial
SPARK_AT = {'A': (3, 1), 'B': (8, 1)}

# per-frame trophy glint and effects
FRAME_FX = {
    'arrive': {}, 'take_in': {}, 'reach': {}, 'grab': {}, 'gather_a': {},
    'gather_b': {'spark': 'dot'},
    'lift': {'shine': 6, 'spark': 'big', 'burst': (11, 16), 'streaks': True},
    'settle': {'shine': 11, 'spark': 'mid', 'burst': (14, 19)},
    'hold_1': {'shine': 17, 'spark': 'small'},
    'hold_2': {},
    'hold_3': {'shine': 2, 'spark': 'mid'},
    'hold_4': {'spark': 'dot'},
}


def trophy_xy(take, name):
    sp = T.spec(take)
    dx, bottom = BK.TROPHY_AT[name]
    return 15 + dx - sp['CX'], bottom - (sp['H'] - 1)       # body coords of the trophy's top-left


def trophy_image(take, shine=None):
    g = T.trophy(take)
    rows = g.rows() if shine is None else FX.shine(g, shine)
    return grid_to_image(rows, PROP)


def layers(take, name):
    """The cell's layers in draw order."""
    ox, oy = BODY_AT
    f = FRAME_FX.get(name, {})
    stand = Image.new('RGBA', CELL, (0, 0, 0, 0))
    paste(stand, T.stand().image(), (ox + STAND_AT[0], oy + STAND_AT[1]))
    back, front = BK.render(name, ox, oy, CELL)
    tro = Image.new('RGBA', CELL, (0, 0, 0, 0))
    tx, ty = trophy_xy(take, name)
    tx, ty = ox + tx, oy + ty
    paste(tro, trophy_image(take, f.get('shine')), (tx, ty))
    fxl = Image.new('RGBA', CELL, (0, 0, 0, 0))
    sp = T.spec(take)
    if f.get('streaks'):
        FX.streaks(fxl, [ox + 4, ox + 26], oy + 3, oy + 17, colour='1', dash=(4, 2))
        FX.streaks(fxl, [ox + 5, ox + 25], oy + 9, oy + 22, colour='W', dash=(3, 2))
    if f.get('burst'):
        r0, r1 = f['burst']
        FX.burst_lines(fxl, tx + sp['CX'], ty + sp['H'] // 2, r0, r1, n=10, colour='1',
                       skip=(5,))
    if f.get('spark'):
        sx, sy = SPARK_AT[take]
        FX.spark(fxl, f['spark'], tx + sx, ty + sy)
    return {'burak': back, 'stand': stand, 'trophy': tro, 'grip': front, 'fx': fxl}


def compose(take, name):
    cell = Image.new('RGBA', CELL, (0, 0, 0, 0))
    for im in layers(take, name).values():
        cell.alpha_composite(im)
    return cell


def trophy_rect(take, name):
    """Cell-space (x, y, w, h) of the trophy in a frame."""
    tx, ty = trophy_xy(take, name)
    sp = T.spec(take)
    return [BODY_AT[0] + tx, BODY_AT[1] + ty, sp['W'], sp['H']]
