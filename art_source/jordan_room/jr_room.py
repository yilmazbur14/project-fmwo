"""Jordan's room - builds the five contract layers in memory.

    layers = build()      # {'room_floor': Canvas, ...} in stacking order

Bottom to top: room_floor, room_walls, room_furniture, room_props, room_clutter.
Each is 640x360 from the screen origin. room_floor + room_walls cover every
pixel; every layer is complete on its own (nothing is left unpainted under a
higher layer), so they can fall away one at a time.

Light travels with its source, so a layer that falls takes its glow with it:
  * the warm spill from the doorway onto the boards is in room_walls (with the
    doorway and the hallway);
  * the monitors' blurple halo on the wall and their pool on the boards (plus
    the PC's glow) are in room_furniture (with the monitors and the PC);
  * the RGB strip's wash is in room_walls, the fairy lights' in room_props.
room_floor on its own is the boards and the rug in the room's ambient dark.
"""
from collections import OrderedDict

import numpy as np

from jr_lib import Canvas, T
import jr_shell
import jr_furniture as FU
import jr_furniture2 as F2
import jr_props
import jr_clutter
from jr_track import Null, Tracker

LAYER_ORDER = ['room_floor', 'room_walls', 'room_furniture', 'room_props', 'room_clutter']


def _diff(lit, plain):
    """The pixels where lit differs from plain, as an overlay canvas."""
    c = Canvas()
    m = (lit.a != plain.a) & (lit.a != T)
    c.a[m] = lit.a[m]
    return c


def build(track=False):
    """The five layers. With track=True, also {layer: Tracker} for the layers that
    are cut by item (furniture, props, clutter); the pixels are the same."""
    floor_plain, rows = jr_shell.build_floor(hall=False, screens=False)
    floor_hall, _ = jr_shell.build_floor(hall=True, screens=False)
    floor_lit, _ = jr_shell.build_floor(hall=True, screens=True)
    for f in (floor_plain, floor_hall, floor_lit):
        jr_clutter.draw_rug(f)
    walls_plain = jr_shell.build_walls(halo=False)
    walls_lit = jr_shell.build_walls(halo=True)

    walls = walls_plain.copy()
    walls.blit(_diff(floor_hall, floor_plain))             # doorway light on the boards

    under = Canvas()                                       # the room as fully lit
    under.blit(floor_lit)
    under.blit(walls_lit)

    furniture = Canvas()
    tf = Tracker(furniture) if track else Null()
    tf.begin('glow_halo', light=True)
    furniture.blit(_diff(walls_lit, walls_plain))          # halo round the monitors
    tf.end()
    tf.begin('glow_pool', light=True)
    furniture.blit(_diff(floor_lit, floor_hall))           # screen + PC pool on the boards
    tf.end()
    for name, piece in (('cube_shelf', F2.cube_shelf(under)),
                        ('glass_cabinet', F2.glass_cabinet(under)),
                        ('bookcase', F2.bookcase(under)), ('cartons', F2.cartons(under)),
                        ('bin', F2.trash_bin(under)), ('wall_shelves', F2.wall_shelves()),
                        ('coat_rail', F2.coat_rail()), ('desk', FU.desk(under)),
                        ('monitors', FU.monitors()), ('pc', FU.pc_tower(under))):
        tf.begin(name)
        furniture.blit(piece)
        tf.end()

    if track:
        props, tp = jr_props.build_props(track=True)
    else:
        props = jr_props.build_props()

    beneath = under.copy()
    beneath.blit(furniture)
    if track:
        clutter, tc = jr_clutter.build_clutter(beneath, track=True)
    else:
        clutter = jr_clutter.build_clutter(beneath)

    layers = OrderedDict([('room_floor', floor_plain), ('room_walls', walls),
                          ('room_furniture', furniture), ('room_props', props),
                          ('room_clutter', clutter)])
    if track:
        return layers, {'room_furniture': tf, 'room_props': tp, 'room_clutter': tc}
    return layers


def composite(layers):
    out = Canvas()
    for name in LAYER_ORDER:
        out.blit(layers[name])
    return out
