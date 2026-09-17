"""polish.py: base grids + rule passes + explicit detail edits -> frame{i}.txt, then build strip.
Source of truth = frame{i}_base.txt + this file."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from puppet import *

SKIN = set('hsmdD')


def load(i):
    return text_to_grid(open(os.path.join(HERE, 'frame%d_base.txt' % i)).read())


def save(i, g):
    with open(os.path.join(HERE, 'frame%d.txt' % i), 'w') as f:
        f.write(grid_to_text(g))


def P(g, pts, ch):
    for x, y in pts:
        g[y][x] = ch


def only(g, pts, ch, allowed):
    """set only where current char is in allowed"""
    for x, y in pts:
        if g[y][x] in allowed:
            g[y][x] = ch


def line(x0, y0, x1, y1):
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def denoise(g, box):
    x0, y0, x1, y1 = box
    out = [r[:] for r in g]
    for y in range(max(1, y0), min(63, y1 + 1)):
        for x in range(max(1, x0), min(63, x1 + 1)):
            c = g[y][x]
            if c not in SKIN:
                continue
            nb = [g[y - 1][x], g[y + 1][x], g[y][x - 1], g[y][x + 1]]
            if all(n in SKIN for n in nb) and len(set(nb)) == 1 and nb[0] != c:
                out[y][x] = nb[0]
    return out


def edge_dist(g):
    """BFS distance (4-neighbour) from any non-skin pixel"""
    INF = 99
    d = [[INF] * 64 for _ in range(64)]
    q = []
    for y in range(64):
        for x in range(64):
            if g[y][x] not in SKIN:
                d[y][x] = 0
                q.append((x, y))
    head = 0
    while head < len(q):
        x, y = q[head]
        head += 1
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < 64 and 0 <= yy < 64 and d[yy][xx] > d[y][x] + 1:
                d[yy][xx] = d[y][x] + 1
                q.append((xx, yy))
    return d


def thin_h(g, box, keep):
    x0, y0, x1, y1 = box
    d = edge_dist(g)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g[y][x] == 'h' and d[y][x] > keep:
                g[y][x] = 's'


# ---------------------------------------------------------------- dive (frames 0,1)
def polish_dive(g, var):
    g = denoise(g, (14, 18, 42, 60))
    thin_h(g, (15, 19, 36, 36), 2)
    # lat crease: curved shadow line from under the deltoid up to the waist, deepest in the middle
    crease = [(27, 36), (28, 35), (29, 35), (30, 34), (31, 33), (32, 33), (33, 32), (34, 31), (35, 30), (36, 29)]
    only(g, crease, 'm', 'hs')
    only(g, [(30, 34), (31, 33), (32, 33)], 'd', 'm')
    # lit edge of the lat bulge just above the crease
    only(g, [(28, 34), (29, 34), (30, 33), (32, 32), (33, 31)], 'h', 's')
    # serratus fingers on the ribcage below the crease
    only(g, [(31, 35), (32, 36), (33, 34), (34, 35), (35, 32), (36, 33)], 'm', 'hs')
    # ab notches along the belly edge
    only(g, [(34, 36), (36, 34), (38, 32)], 'd', 'ms')
    # trunks: waistband highlight along skin/trunks diagonal
    for y in range(20, 32):
        for x in range(28, 46):
            if g[y][x] == 'B' and g[y][x - 1] in SKIN:
                g[y][x] = 'L'
    # near arm: deltoid highlight crescent + shadow, biceps highlight, deltoid/arm split
    only(g, [(21, 39), (22, 38), (23, 38), (22, 39), (23, 39), (24, 39), (22, 40)], 'h', 'hs')
    only(g, [(21, 40), (21, 41), (23, 40), (24, 40)], 's', 'h')
    only(g, [(26, 41), (27, 41), (27, 42)], 'm', 'hs')
    only(g, [(21, 45), (22, 45), (26, 44), (27, 44)], 'm', 'hs')
    only(g, [(22, 47), (22, 48), (23, 48), (22, 49)], 'h', 's')
    only(g, [(26, 50), (26, 51), (26, 52), (25, 53)], 'm', 's')
    # elbow bone point
    only(g, [(23, 57)], 'h', 's')
    only(g, [(24, 58)], 'm', 's')
    # tucked fist behind upper arm: finger lines
    only(g, [(31, 46), (32, 46), (31, 48)], 'm', 's')
    # far raised fist: finger lines
    fx, fy = (0, 0) if var == 0 else (3, -3)
    only(g, [(8 + fx, 13 + fy), (8 + fx, 14 + fy), (10 + fx, 13 + fy), (10 + fx, 14 + fy)], 'm', 's')
    # beard underside faces open air in the dive: outline it
    only(g, [(x, 48) for x in range(6, 13)], 'K', 'r')
    return g


# ---------------------------------------------------------------- impact (frame 2)
def polish_impact(g):
    g = denoise(g, (6, 30, 56, 62))
    thin_h(g, (19, 32, 42, 50), 2)
    # lat crease running along the flattened torso, deepest in the middle, lit edge above
    crease = [(32, 46), (33, 45), (34, 45), (35, 44), (36, 44), (37, 43), (38, 42), (39, 42), (40, 41), (41, 40)]
    only(g, crease, 'm', 'hs')
    only(g, [(35, 44), (36, 44), (37, 43)], 'd', 'm')
    only(g, [(33, 44), (34, 44), (36, 43), (38, 41)], 'h', 's')
    # serratus fingers below the crease
    only(g, [(34, 47), (35, 47), (37, 46), (38, 45)], 'm', 'hs')
    # waistband highlight
    for y in range(28, 46):
        for x in range(38, 54):
            if g[y][x] == 'B' and g[y][x - 1] in SKIN:
                g[y][x] = 'L'
    # elbow pillar: deltoid split + biceps highlight
    only(g, [(24, 50), (25, 50), (28, 49)], 'm', 'hs')
    only(g, [(25, 52), (25, 53), (26, 53)], 'h', 's')
    # slapping fist: finger lines
    only(g, [(4, 57), (5, 58), (6, 56), (7, 57)], 'm', 's')
    # beard underside faces open air: outline it
    only(g, [(x, 54) for x in range(11, 18)], 'K', 'r')
    P(g, [(20, 54)], 'K')
    return g


def outline_trunks(g):
    """house style: pure-black outline wherever trunks touch transparency (idle sprite omits it)"""
    adds = []
    for y in range(64):
        for x in range(64):
            if g[y][x] in 'BLb':
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 64 and 0 <= yy < 64 and g[yy][xx] == '.':
                        adds.append((xx, yy))
    for x, y in adds:
        g[y][x] = 'K'


# ---------------------------------------------------------------- squat (frame 3)
def polish_squat(g):
    # armpit creases exposed by removing the idle's hanging arms: outline them, symmetric
    P(g, [(22, 44), (41, 44)], 'K')
    P(g, [(41, 45)], '.')
    P(g, [(39, 46)], 's')
    P(g, [(40, 46)], 'K')
    P(g, [(38, 48)], 's')
    P(g, [(39, 48)], 'K')
    outline_trunks(g)
    return g


# ---------------------------------------------------------------- superman (frame 4)
def polish_superman(g):
    P(g, [(22, 36), (41, 36)], 'K')          # exposed armpit creases
    P(g, [(42, 25)], 'K')                    # close notch between shoulder and right deltoid
    P(g, [(21, 34)], 'K')                    # exposed torso pixel under the raised arm
    outline_trunks(g)
    # raised fist: finger separations + thumb wrap
    only(g, [(15, 5), (15, 6), (17, 5), (17, 6)], 'm', 's')
    only(g, [(13, 7), (14, 7), (15, 7)], 'm', 's')
    return g


def main():
    frames = []
    for i in range(5):
        g = load(i)
        if i in (0, 1):
            g = polish_dive(g, i)
        elif i == 2:
            g = polish_impact(g)
        elif i == 3:
            g = polish_squat(g)
        elif i == 4:
            g = polish_superman(g)
        save(i, g)
        frames.append(g)
    write_strip(os.path.join(HERE, 'carter_elbowdrop_wip.png'), frames)
    print('polished')


if __name__ == '__main__':
    main()
