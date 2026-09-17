"""Travelling quake shockwave segment, 4 x 32x32. 'Up' (y=0) is the direction of travel (outward).
A row of rock shards bursts out of a dark fissure, heaped with torn earth, with white dust spray at the
leading edge. Everything is drawn with x modulo 32, so the tile repeats seamlessly side by side."""
from common import *
from stamps import S

N = 32

def P(g, x, y, c):
    if 0 <= y < N:
        g[y][x % N] = c

def G(g, x, y):
    return g[y][x % N] if 0 <= y < N else '.'

def blit(g, rows, x0, y0, only_empty=False):
    for dy, row in enumerate(rows):
        for dx, c in enumerate(row):
            if c != '.':
                if only_empty and G(g, x0 + dx, y0 + dy) != '.':
                    continue
                P(g, x0 + dx, y0 + dy, c)

def spike(g, cx, base, h, hw, lean):
    """rock shard: tip at top, lit left face / shadow right face, black outline"""
    if h < 2:
        return
    cells = {}
    for r in range(h):
        y = base - h + 1 + r
        t = (r + 1) / h
        w = 0.6 + (hw - 0.6) * t
        c = cx + lean * (1 - t)
        for x in range(int(c - w) - 2, int(c + w) + 3):
            if abs(x + 0.5 - c) <= w + 0.5:
                p = (x + 0.5 - c) / max(w, 0.5)
                cells[(x % N, y)] = p
    for (x, y), p in cells.items():
        edge = any(((x + dx) % N, y + dy) not in cells for dx, dy in ((1, 0), (-1, 0), (0, -1)))
        left_open = ((x - 1) % N, y) not in cells
        if edge:
            col = 'K'
        elif ((x - 2) % N, y) not in cells or ((x - 1) % N, y - 1) not in cells and p < 0:
            col = '2'
        elif p < -0.05:
            col = '4'
        elif p < 0.5:
            col = '7'
        else:
            col = '3'
        P(g, x, y, col)

# spikes: (centre x, base row, full height, half width at base, lean)
SPIKES = [(3.5, 21, 14, 4.4, -1.0), (11.5, 21, 9, 3.6, 1.0), (19.0, 21, 16, 5.0, 0.5), (26.5, 21, 10, 3.8, -1.0)]
# height scale per frame: breaking out, full, overshoot, crumbling back
GROW = [[0.45, 0.85, 1.0, 0.7], [0.8, 1.0, 0.65, 0.4], [0.55, 0.95, 1.0, 0.75], [0.9, 0.7, 0.45, 0.8]]

MOUND = [17, 16, 16, 17, 18, 18, 17, 17, 18, 19, 18, 17, 17, 18, 18, 17,
         16, 16, 17, 18, 18, 17, 16, 16, 17, 18, 19, 19, 18, 17, 17, 17]

SPRAY = [
    [(2, 4, 'dust3'), (17, 2, 'dust4'), (10, 9, 'dot'), (25, 8, 'dot')],
    [(1, 1, 'dust4'), (18, 0, 'dust3'), (9, 6, 'dust2'), (26, 6, 'dust2'), (14, 3, 'dot')],
    [(0, 0, 'dust2'), (20, 0, 'dot'), (8, 3, 'dust3'), (27, 3, 'dust3'), (13, 0, 'dot')],
    [(3, 6, 'dust2'), (16, 4, 'dust3'), (9, 1, 'dot'), (28, 0, 'dot'), (23, 9, 'dot')],
]
PEBBLES = [
    [(7, 11, 'pebble'), (23, 13, 'pebble')],
    [(6, 8, 'pebble'), (23, 9, 'pebble'), (30, 12, 'pebble')],
    [(6, 5, 'pebble'), (22, 5, 'pebble'), (30, 8, 'pebble')],
    [(14, 12, 'pebble'), (22, 2, 'pebble'), (29, 5, 'pebble')],
]

def frame(k):
    g = [['.'] * N for _ in range(N)]
    # dark fissure the wave leaves behind
    for x in range(N):
        wob = (0, 1, 1, 0, 1, 2, 1, 0)[x % 8]
        for y in range(21, 24 + wob):
            P(g, x, y, 'g')
        P(g, x, 24 + wob, 'K')
    for pts in ([(5, 25), (4, 26), (4, 27), (3, 28)], [(14, 26), (15, 27), (15, 28), (16, 29)],
                [(25, 26), (26, 27), (27, 28)], [(21, 26), (20, 27)], [(31, 25), (0, 26)]):
        for x, y in pts:
            P(g, x, y, 'K')
    # torn earth heaped along the fissure
    for x in range(N):
        t = MOUND[x]
        P(g, x, t - 1, 'K')
        for y in range(t, 22):
            d = y - t
            P(g, x, y, 'e' if d <= 1 else ('b' if d <= 3 else 'd'))
    for x in range(N):
        a, b = MOUND[x], MOUND[(x + 1) % N]
        for y in range(min(a, b) - 1, max(a, b) - 1):
            if G(g, x if a > b else x + 1, y) == '.':
                P(g, x if a > b else x + 1, y, 'K')
    # rock shards bursting out
    for (cx, base, h, hw, lean), gr in zip(SPIKES, GROW):
        s = gr[k]
        spike(g, cx, base, max(2, round(h * s)), hw * (0.75 + 0.25 * s), lean)
    # clods thrown on the front of the heap (over the shard bases)
    for x, y, st in ((8, 17, 'rock4'), (24, 18, 'rock4')):
        blit(g, S[st], x, y)
    # white dust spray and pebbles ahead of the crest
    for x, y, st in SPRAY[k]:
        blit(g, S[st], x, y, only_empty=True)
    for x, y, st in PEBBLES[k]:
        blit(g, S[st], x, y, only_empty=True)
    return [''.join(r) for r in g]

if __name__ == '__main__':
    fr = [frame(k) for k in range(4)]
    st = strip(fr)
    save_grid('eric_quake_segment_grid.txt', st)
    write_grid_png('eric_quake_segment.png', st)
    view('segment_strip_8x.png', st, 8)
    tiled = [''.join(f[y] * 3 + '....' for f in fr) for y in range(N)]
    view('segment_tiled_4x.png', tiled, 4)
