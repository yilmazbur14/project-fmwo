"""Generates the 0 deg and 45 deg thrown-sword grids, modelled on the in-hand greatsword in
EricTopDownRevised frames 13/14/18/21: thin white grip in a black outline, small dark guard block,
~11px-thick blade with light rims and a speckled grey body, double-bevelled point.
Output grids sword_000.txt / sword_045.txt are the source the sheet is built from."""
from common import *
N = 96

def part0(x, y):
    """0 deg: tip right. blade axis on row 47."""
    if 19 <= x <= 29 and 46 <= y <= 48: return 'grip'
    if 30 <= x <= 33 and 41 <= y <= 53: return 'guard'
    if 34 <= x <= 70 and 42 <= y <= 52: return 'blade'
    if 71 <= x <= 74:
        k = x - 70
        if 42 + k <= y <= 52 - k: return 'tip'
    return None

def part45(x, y):
    """45 deg: tip down-right. blade axis on the x == y diagonal."""
    s = x + y; d = x - y
    if 54 <= s <= 69 and abs(d) <= 1: return 'grip'
    if 70 <= s <= 75 and abs(d) <= 9: return 'guard'
    if 76 <= s and abs(d) <= 7 and x <= 67 and y <= 67:
        return 'blade' if s <= 127 else 'tip'
    return None

PROF0 = 'K214444471K'                    # rows 42..52
PROF45 = 'K22144444447 11K'.replace(' ', '')   # d = +7 .. -7

def build(partf, colf):
    P = [[partf(x, y) for x in range(N)] for y in range(N)]
    g = [['.'] * N for _ in range(N)]
    for y in range(N):
        for x in range(N):
            p = P[y][x]
            if p is None:
                continue
            edge = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = P[y + dy][x + dx]
                if q is None or (p == 'guard') != (q == 'guard'):
                    # guard owns the seam with its neighbours; blade/grip do not double it
                    if q is None or p == 'guard':
                        edge = True
            if edge:
                g[y][x] = 'K'
    for y in range(N):
        for x in range(N):
            p = P[y][x]
            if p is None or g[y][x] == 'K':
                continue
            nearK = any(g[y + dy][x + dx] == 'K' for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            g[y][x] = colf(x, y, p, nearK)
    return [''.join(r) for r in g]

def col0(x, y, p, nearK):
    if p == 'grip': return 'W'
    if p == 'guard': return '7' if x == 31 else '3'
    if p == 'tip' and nearK: return '2' if y < 47 else '1'
    c = PROF0[y - 42]
    if c == '4':
        if x <= 35: c = '3'                                           # dark ricasso next to the guard
        elif (x + y // 2) % 6 == 0 and (x // 6) % 4 != 3: c = '5'
    if y == 43 and x % 5 == 2: c = '1'
    return c

def col45(x, y, p, nearK):
    s = x + y; d = x - y
    if p == 'grip': return 'W'
    if p == 'guard': return '7' if s <= 72 else '3'
    if p == 'tip' and nearK: return '2' if d > 0 else '1'
    c = PROF45[7 - d]
    if c == '4':
        if s <= 78: c = '3'
        elif (s + (d + 20) // 3) % 8 == 0: c = '5'
    if d == 6 and (s // 2) % 5 == 1: c = '1'
    return c

if __name__ == '__main__':
    assert len(PROF0) == 11, PROF0
    assert len(PROF45) == 15, PROF45
    g0 = build(part0, col0)
    g45 = build(part45, col45)
    save_grid('sword_000.txt', g0)
    save_grid('sword_045.txt', g45)
    view('sword_gen_8x.png', strip([[r[12:84] for r in g0[30:66]], [r[12:84] for r in g45[20:74]][:36]]), 8)
    for y in range(38, 57): print(f'{y:2d} ' + g0[y][16:80])
    for y in range(24, 72): print(f'{y:2d} ' + g45[y][20:72])
