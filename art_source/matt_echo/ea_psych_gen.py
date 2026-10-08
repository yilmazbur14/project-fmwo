"""Generate the psych mouth (rows 43-63, x 31-65) on the roar's own jaw contour, by rule, for hand-tuning.
The opening is a grin-shaped D, empty: teeth on top, a black throat, a small tongue lying in the bottom.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ea_base as E
from ea_base import G

ROAR = G.ROAR
X0, Y0 = 31, 29


def build(OPEN, tongue, curl=True, tongue_out=None, depth=99):
    contour = {}
    for y in range(43, 64):
        r = ROAR[y - Y0]
        ks = [X0 + i for i, c in enumerate(r) if c != '.']
        contour[y] = (min(ks), max(ks))
    grid = {}
    for y in range(43, 59):
        a, b = contour[y]
        grid[(a, y)] = 'k'
        grid[(b, y)] = 'k'
        for x in range(a + 1, b):
            # skin by column: the lit left cheek, the shaded right
            if x == a + 1:
                k = '1'
            elif x < 47:
                k = '2'
            elif x < b - 2:
                k = '3' if y < 56 or x > 52 else '2'
            else:
                k = '4' if x == b - 1 else '3'
            grid[(x, y)] = k
    # the roar's chin, rows 59-63, exactly
    for y in range(59, 64):
        for i, c in enumerate(ROAR[y - Y0]):
            if c != '.':
                grid[(X0 + i, y)] = c
    # row 43 keeps the roar's cheeks
    for i, c in enumerate(ROAR[43 - Y0]):
        if c != '.' and c != 'k':
            grid[(X0 + i, 43)] = c
    inside = {(x, y) for y, (a, b) in OPEN.items() for x in range(a, b + 1)}
    outline = set()
    for (x, y) in inside:
        for q in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if q not in inside:
                outline.add(q)
    for q in outline:
        grid[q] = 'k'
    if curl:
        grid[(58, 43)] = 'k'
    # the lower lip, lit just under the D
    for (x, y) in outline:
        q = (x, y + 1)
        if q in grid and q not in outline and q not in inside and grid[q] in '1234' and y >= 46:
            grid[q] = '1' if x <= 49 else '2'
    top = min(OPEN)
    for y, (a, b) in OPEN.items():
        for x in range(a, b + 1):
            if x == a:
                k = 'q'
            elif x == a + 1:
                k = 'p'
            elif x == b:
                k = 'p'
            elif x == b - 1:
                k = 'n'
            elif x == a + 2 or x == b - 2:
                k = 'n' if y > top + 1 else 'm'
            else:
                # the black of the throat only `depth` rows down; below it the dark plum of an empty mouth
                k = 'k' if top + 1 < y <= top + 1 + depth and a + 3 <= x <= b - 3 else 'm'
            grid[(x, y)] = k
    # upper teeth: a full row, fangs dropping at both corners
    a, b = OPEN[top]
    for x in range(a, b + 1):
        grid[(x, top)] = 'W' if x < b - 1 else 'X'
    for x in (a, a + 1):
        grid[(x, top + 1)] = 'W'
        grid[(x, top + 2)] = 'X'
    for x in (b - 1, b):
        grid[(x, top + 1)] = 'X'
        grid[(x, top + 2)] = 'x'
    grid[(a + 2, top + 1)] = 'X'
    grid[(b - 2, top + 1)] = 'x'
    for y, (xa, keys) in tongue.items():
        for i, c in enumerate(keys):
            if c != '_' and (xa + i, y) in inside:
                grid[(xa + i, y)] = c
    # a tongue stuck out over the lower lip: drawn last, over the lip line and the chin
    for y, (xa, keys) in (tongue_out or {}).items():
        for i, c in enumerate(keys):
            if c not in '._':
                grid[(xa + i, y)] = c
    rows = []
    for y in range(43, 64):
        rows.append(''.join(grid.get((x, y), '.') for x in range(31, 66)))
    return rows


OPEN_A = {44: (39, 57), 45: (39, 57), 46: (39, 57), 47: (39, 57), 48: (40, 56), 49: (40, 56), 50: (41, 55),
          51: (41, 55), 52: (42, 54), 53: (43, 53), 54: (44, 52), 55: (46, 50)}
TONGUE_A = {51: (44, 'nqrrrrrqn'), 52: (44, 'qrRRrrrrq'), 53: (44, 'prRrrrrqp'), 54: (45, 'pqrrqqp'), 55: (46, 'pqqqp')}

if __name__ == '__main__':
    for i, r in enumerate(build(OPEN_A, TONGUE_A)):
        print('    "%s %s",   # %d' % (r[:18], r[18:], 43 + i))

# the emptier mouth: only a small tongue lying low in the jaw, a black void above it
TONGUE_B = {53: (45, 'nqrRrqn'), 54: (45, 'pqrrrqp'), 55: (46, 'pqqqp')}

# "psych!": the tongue stuck out over the lower lip and the chin, a groove down its middle, lit on the left
TONGUE_IN_C = {51: (45, 'nqrrrrqn'), 52: (45, 'qrRRrrrq'), 53: (45, 'rRRrrrrq')}
TONGUE_OUT_C = {54: (44, 'krRRrqrrk'), 55: (44, 'krRrrqrqk'), 56: (44, 'krRrrqrqk'), 57: (44, 'kkrrrqqkk'),
                58: (45, '.kqqqpk.'), 59: (46, '.kkk.')}
