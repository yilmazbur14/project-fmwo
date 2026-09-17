"""The newcomer (player), seen from behind, looking up the tower.
Built as a half-mask (mirrored), then shaded region by region and hand-adjusted; output is an ASCII grid."""
from lib import *

W, H = 32, 52

# left-half spans (cols 0..15, col 15 touches the axis); label per span
L = {
    0: [('head', 13, 15)], 1: [('head', 11, 15)], 2: [('head', 10, 15)], 3: [('head', 10, 15)],
    4: [('head', 10, 15)], 5: [('head', 10, 15)], 6: [('head', 9, 15)], 7: [('head', 9, 15)],
    8: [('head', 10, 15)], 9: [('head', 11, 15)], 10: [('neck', 12, 15)],
    11: [('back', 10, 15)], 12: [('back', 7, 15)], 13: [('back', 5, 15)], 14: [('back', 4, 15)],
    15: [('back', 3, 15)], 16: [('back', 3, 15)], 17: [('back', 2, 15)],
}
for y in range(18, 22):
    L[y] = [('arm', 2, 6), ('back', 8, 15)]
for y in range(22, 28):
    L[y] = [('arm', 2, 6), ('back', 9, 15)]
L[28] = [('arm', 2, 6), ('shorts', 8, 15)]
L[29] = [('fist', 1, 6), ('shorts', 8, 15)]
for y in range(30, 34):
    L[y] = [('fist', 1, 6), ('shorts', 8, 15)]
L[34] = [('fist', 2, 5), ('shorts', 8, 15)]
L[35] = [('shorts', 8, 15)]
for y in range(36, 39):
    L[y] = [('shorts', 8, 14)]
for y, (a, b) in zip(range(39, 49), [(9, 14), (9, 14), (9, 13), (9, 13), (9, 14), (9, 14), (9, 14), (10, 14),
                                      (10, 13), (10, 13)]):
    L[y] = [('leg', a, b)]
L[49] = [('shoe', 9, 14)]
L[50] = [('shoe', 8, 14)]
L[51] = [('shoe', 8, 14)]


def build():
    reg = [[None] * W for _ in range(H)]
    for y, spans in L.items():
        for name, a, b in spans:
            for x in range(a, b + 1):
                reg[y][x] = name
                reg[y][W - 1 - x] = name
    inside = lambda x, y: 0 <= x < W and 0 <= y < H and reg[y][x] is not None
    g = [['.'] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            r = reg[y][x]
            if r is None:
                continue
            edge = any(not inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            # region boundaries (e.g. back/shorts) are outlined too
            if not edge and r in ('shorts', 'back', 'neck', 'head') and y > 0 and reg[y - 1][x] not in (r, None):
                if (r, reg[y - 1][x]) in (('shorts', 'back'),):
                    g[y][x] = 'K'
                    continue
            if edge:
                g[y][x] = 'K'
                continue
            m = min(x, W - 1 - x)          # distance-ish from the left/right edge (mirror aware)
            top = not inside(x, y - 2) or reg[y - 1][x] != r
            if r == 'head':
                g[y][x] = 'N'
                if y <= 3 and (y == 1 or not inside(x, y - 2)):
                    g[y][x] = 'n'
            elif r == 'neck':
                g[y][x] = '4'
            elif r == 'back':
                g[y][x] = '3'
            elif r == 'arm':
                g[y][x] = '3'
            elif r == 'fist':
                g[y][x] = 'u'
            elif r == 'shorts':
                g[y][x] = 'u'
            elif r == 'leg':
                g[y][x] = '3'
            elif r == 'shoe':
                g[y][x] = 's'
    return g, reg


def half_set(g, pts, ch, mirror=True):
    for x, y in pts:
        g[y][x] = ch
        if mirror:
            g[y][W - 1 - x] = ch


def detail(g):
    # --- head: hair volume + headband + ears
    half_set(g, [(12, 2), (13, 2), (13, 3), (14, 1), (15, 1)], 'n')
    for x in range(11, 21):
        g[4][x] = 'p'
        g[5][x] = 'r'
    half_set(g, [(11, 5)], 'b')
    half_set(g, [(10, 6), (10, 7)], '3')
    half_set(g, [(10, 7)], '4')
    # knot at the back of the head
    g[5][15] = 'p'; g[5][16] = 'r'; g[6][15] = 'r'; g[6][16] = 'r'; g[7][15] = 'b'; g[7][16] = 'r'
    # neck
    half_set(g, [(14, 10), (15, 10)], '3')
    # traps / shoulders lit from above
    for x in range(11, 21):
        g[11][x] = '2'
    half_set(g, [(8, 12), (9, 12), (10, 12)], '2')
    half_set(g, [(6, 13), (7, 13), (8, 13)], '2')
    half_set(g, [(5, 14), (6, 14)], '2')
    half_set(g, [(4, 15), (4, 16)], '2')
    half_set(g, [(5, 15)], '1')
    half_set(g, [(3, 17), (3, 18), (3, 19), (3, 20)], '2')
    # deltoid / back separation shadow
    half_set(g, [(7, 15), (7, 16), (7, 17), (6, 17)], '4')
    # spine groove
    for y in range(12, 28):
        g[y][15] = '4'; g[y][16] = '4'
    half_set(g, [(15, 11)], '2')
    # shoulder blades (lower edge shadows) + upper highlights
    half_set(g, [(10, 19), (11, 20), (12, 20), (13, 19)], '4')
    half_set(g, [(10, 14), (11, 14), (12, 15)], '2')
    # lats: shadow along the arm gap
    for y in range(18, 22):
        half_set(g, [(9, y)], '4')
    for y in range(22, 28):
        half_set(g, [(10, y)], '4')
    # lower-back dimples
    half_set(g, [(13, 25), (13, 26)], '4')
    # arms: outer rim light, inner shadow, elbow crease
    for y in range(21, 28):
        half_set(g, [(3, y)], '2')
    for y in range(18, 28):
        half_set(g, [(5, y)], '4')
    half_set(g, [(4, 24)], '4')
    # fists (blue wraps)
    half_set(g, [(2, 30), (3, 30), (2, 31)], 'B')
    half_set(g, [(2, 32), (3, 32), (4, 32), (5, 32)], 'i')
    half_set(g, [(5, 30), (5, 31), (5, 33), (4, 33)], 'i')
    # shorts
    for x in range(9, 23):
        g[28][x] = 'K'
        g[29][x] = 'B'
    half_set(g, [(9, 30), (9, 31), (9, 32), (9, 33), (9, 34), (9, 35), (9, 36), (9, 37)], 'B')
    half_set(g, [(10, 30), (10, 31), (10, 32), (10, 33), (10, 34), (10, 35), (10, 36), (10, 37)], 'i')
    half_set(g, [(14, 33), (14, 34), (13, 36), (13, 37), (15, 30), (15, 31)], 'i')
    # legs
    for y in range(39, 49):
        half_set(g, [(10, y)], '2')
    half_set(g, [(10, 39)], '4')
    half_set(g, [(12, 41), (12, 42)], '4')
    half_set(g, [(11, 43), (11, 44)], '2')
    half_set(g, [(13, 39), (13, 40), (13, 45), (13, 46)], '4')
    # shoes
    half_set(g, [(10, 50), (11, 50), (9, 51), (10, 51)], 'g')
    # headband tails flutter to the right, over the hair and out past the head
    tails = [(17, 7, 'r'), (18, 7, 'r'), (18, 8, 'r'), (19, 8, 'b'), (20, 8, 'r'), (21, 8, 'r'), (22, 8, 'r'),
             (22, 9, 'b'), (23, 9, 'r'), (24, 9, 'r'), (25, 10, 'b'), (19, 9, 'r'), (20, 9, 'r'), (21, 10, 'r'),
             (22, 10, 'r'), (23, 11, 'b')]
    for x, y, ch in tails:
        g[y][x] = ch
    # black outline around the parts of the tails that stick out into the air
    tail_set = {(x, y) for x, y, _ in tails}
    for x, y, _ in tails:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and g[ny][nx] == '.' and (nx, ny) not in tail_set:
                g[ny][nx] = 'K'
    return g


CMAP = {'K': K, 'N': N0, 'n': IN, 'p': PK, 'r': RD, 'b': BR, '1': SK, '2': TN, '3': BR2, '4': BR, '5': P0,
        'B': SB, 'u': RB, 'i': IN, 's': N0, 'g': G2}


def player_rows():
    g, reg = build()
    g = detail(g)
    return [''.join(r) for r in g]


if __name__ == '__main__':
    rows = player_rows()
    print('\n'.join(rows))
    c = Canvas(W, H)
    c.grid(0, 0, rows, CMAP, skip='.')
    p = c.save('out/player.png')
    crop_zoom(p, 'out/player_10x.png', 0, 0, W, H, 10)
