"""Jordan's room - the crumble pieces of the five layers.

    pieces = cut(layers, trackers)   # {'floor': [(label, x, y, rgba), ...], ...}

Floor and walls: ragged chunks held to 16-40 texels a side (jr_track.chunk).
Furniture, props, clutter: a whole prop per piece (jr_track.Tracker), the
monitors' light chunked like the floor. Every piece keeps only its own pixels,
and the pieces of a layer tile it exactly (checked by jr_export).
"""
import numpy as np

from jr_lib import to_image
from jr_track import chunk, cells, room_grid, split_and_tidy, pieces_from_labels, _renumber

SHORT = {'room_floor': 'floor', 'room_walls': 'walls', 'room_furniture': 'furniture',
         'room_props': 'props', 'room_clutter': 'clutter'}
GRID = room_grid()    # one ragged brick grid for the wall and the floor
GLOW = room_grid(coarse=True)   # twice as coarse for the monitors' light
CRUMB = 24            # prop parts smaller than this join a neighbour


def _by_item(tr, light_seed):
    lab = tr.groups()
    roots = {tr.find(i) for i in range(len(tr.items))}
    light_roots = {tr.find(i) for i, it in enumerate(tr.items) if it['light']}
    attach_roots = {tr.find(i) for i, it in enumerate(tr.items) if it['attach']}
    light = np.isin(lab, list(light_roots)) if light_roots else np.zeros(lab.shape, bool)
    solid = np.where(light, -1, lab)
    solid = split_and_tidy(solid, never_alone=attach_roots, crumb=CRUMB)
    if light.any():
        glow = cells(light, GLOW)
        glow = np.where(glow >= 0, glow + solid.max() + 1, -1)
        solid = np.where(glow >= 0, glow, solid)
    return _renumber(solid), light


def cut(layers, trackers):
    labels = {}
    labels['room_floor'] = chunk(layers['room_floor'].opaque(), GRID)
    labels['room_walls'] = chunk(layers['room_walls'].opaque(), GRID)
    lights = {}
    for i, name in enumerate(('room_furniture', 'room_props', 'room_clutter')):
        labels[name], lights[name] = _by_item(trackers[name], 40 + i)
    out = {}
    for name, c in layers.items():
        rgba = np.array(to_image(c))
        out[SHORT[name]] = pieces_from_labels(rgba, labels[name])
    return out, labels, lights
