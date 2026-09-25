"""Greyson's fists, in the house convention of Matt's and Danny's approved fists: squared blocks,
every finger its own rounded segment split by black and lit on its upper left. Round fists with
dots read as faces (a lesson from his 2026-09-18 sprite), so they stay blocky.

Maps are STRUCTURE: 'k' lines and 's' skin, drawn for the LEFT fist (screen left, his right
hand). The skin is shaded afterwards, each finger segment (a connected piece of skin between the
black lines) as its own small pillow under one fist-wide form lit from the upper left. That keeps
both fists lit the same way: the right fist is the mirrored structure, shaded fresh, never a
mirrored picture (a mirror would move the light). `@` marks the pixel that sits on the pose's
fist point; it is skin.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gr_kit as K  # noqa: E402
from gr_muscle import Form, Region, RegionLayer  # noqa: E402

# Idle: hanging beside the thigh, knuckles forward (Matt's convention). The back of the hand on
# top, a knuckle row (the dips are shaded from the lines below them), four finger segments.
IDLE_L = [
    "..kkkkkkkkk..",
    ".kssss@sssk..",
    "ksssssssssskk",
    "ksssssssssssk",
    "ksskssksskssk",
    "ksskssksskssk",
    "ksskssksskssk",
    "ksskssksskssk",
    ".kskssksskkk.",
    "..kkkkkkkk...",
]

# Flex: raised beside the head, the curled fingers toward us (Danny's approved fist, stood up).
# Four finger segments across the top, the thumb laid across the three nearest the head, the
# heel of the hand under it running into the wrist.
FLEX_L = [
    ".kkkkkkkkkkk.",
    "ksskssksskssk",
    "ksskssksskssk",
    "ksskssksskssk",
    "ksskkkkkkkkkk",
    "ksskssssssssk",
    "ksskssssssssk",
    ".kkkkkkkkkkk.",
    "..ksss@sssk..",
    "...kkkkkkk...",
]

MAPS = {'idle': IDLE_L, 'flex': FLEX_L}
CUTS = (0.80, 0.50, 0.14, -0.20)


def _check():
    for name, rows in MAPS.items():
        w = len(rows[0])
        for i, r in enumerate(rows):
            assert len(r) == w, (name, i, r)
        assert sum(r.count('@') for r in rows) == 1, name


_check()


def _structure(rows, side):
    """{(col, row): 'k' or 's'} with the anchor, mirrored for side 1."""
    w = len(rows[0])
    px, anchor = {}, None
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            if ch == '@':
                anchor = (c, r)
                ch = 's'
            cc = (w - 1 - c) if side else c
            px[(cc, r)] = ch
    if side:
        anchor = (w - 1 - anchor[0], anchor[1])
    return px, anchor


def _components(skin):
    left, comps = set(skin), []
    while left:
        seed = left.pop()
        comp, todo = {seed}, [seed]
        while todo:
            x, y = todo.pop()
            for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if q in left:
                    left.remove(q)
                    comp.add(q)
                    todo.append(q)
        comps.append(comp)
    return comps


def fist(pose, side, center):
    """The fist for `pose` on `side` (0 = screen left, 1 = the mirror), its anchor on `center`
    (left-side coordinates; mirrored for side 1)."""
    px, (ax, ay) = _structure(MAPS[pose], side)
    cx = int(round(K.AX - center[0])) if side else int(round(center[0]))
    cy = int(round(center[1]))
    placed = {(cx + c - ax, cy + r - ay): ch for (c, r), ch in px.items()}
    skin = [p for p, ch in placed.items() if ch == 's']
    xs = [p[0] for p in skin]
    ys = [p[1] for p in skin]
    form = Form(ellipsoid=((min(xs) + max(xs)) / 2.0 - 0.5, (min(ys) + max(ys)) / 2.0 - 0.5,
                           (max(xs) - min(xs)) / 2.0 + 2.0, (max(ys) - min(ys)) / 2.0 + 2.0))
    regions = [Region('seg%d' % i, comp, amp=1.2, round_px=1.6, cast=0, depth=0)
               for i, comp in enumerate(_components(skin))]
    shaded = RegionLayer(form, regions).shade(cuts=CUTS, lines=False)[0]
    out = {p: 'k' for p, ch in placed.items() if ch == 'k'}
    out.update(shaded)
    return out
