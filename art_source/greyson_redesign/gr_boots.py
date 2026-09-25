"""Greyson's white wrestling boots (the style reference's and the 2026-09-18 sprite's), as a
STRUCTURE map for the LEFT boot, shaded per part so the mirrored right boot keeps the upper-left
light: 'c' the folded cuff, 's' the shaft, 't' the toe box, 'o' the sole, 'l' the laces, 'k' lines.
The sole ends on row 110 so the keyline under it is row 111, the frame's bottom row: his feet.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gr_kit as K  # noqa: E402

X0, Y0 = 36, 100
# x: 36-40 41-45 46-50 51-55
BOOT_L = [
    "..... kkkkk kkkkk kk...",   # 100  the cuff's top edge, over the calf
    "....k ccccc ccccc cck..",   # 101  the folded cuff
    "....k sssss lssss ssk..",   # 102  shaft, laces up the front
    "....k sssss slsss ssk..",   # 103
    "....k sssss lssss ssk..",   # 104
    "...ks sssss slsss sssk.",   # 105
    "..kst ttttt ttttt tttk.",   # 106  the toe box rounds forward
    ".kttt ttttt ttttt tttk.",   # 107
    ".kttt ttttt ttttt tttk.",   # 108
    ".kooo ooooo ooooo oook.",   # 109  sole
    ".kooo ooooo ooooo oook.",   # 110
    "..kkk kkkkk kkkkk kkk..",   # 111  the keyline under the sole: the feet
]


def _rows():
    rows = [r.replace(' ', '') for r in BOOT_L]
    for i, r in enumerate(rows):
        assert len(r) == 20, (Y0 + i, r, len(r))
    return rows


def boot(side):
    rows = _rows()
    part = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == '.':
                continue
            x = X0 + c
            if side:
                x = K.AX - x
            part[(x, Y0 + r)] = ch
    body = [p for p, ch in part.items() if ch in 'cstl']
    xs = [p[0] for p in body]
    cx = (min(xs) + max(xs)) / 2.0
    out = {}
    for p, ch in part.items():
        if ch == 'k':
            out[p] = 'k'
    shaft = {p: 'W' for p, ch in part.items() if ch in 'csl'}
    K.cylinder(shaft, (cx - 0.5, 96), (cx - 0.5, 112), 6.8, 'WXx', (0.34, -0.30))
    toe = {p: 'W' for p, ch in part.items() if ch == 't'}
    K.ellipsoid(toe, cx - 1.5, 105.5, 9.5, 4.0, 'WXx', (0.34, -0.25))
    sole = {p: 'L' for p, ch in part.items() if ch == 'o'}
    for p in sole:
        sole[p] = 'M' if (p[1] == 109 and p[0] < cx) else 'L'
    for p, ch in part.items():
        if ch == 'c':
            shaft[p] = K.DARKER[shaft[p]]            # the fold sits in its own shadow
        elif ch == 'l':
            shaft[p] = 'x'                           # lace crossings
    out.update(shaft)
    out.update(toe)
    out.update(sole)
    return out
