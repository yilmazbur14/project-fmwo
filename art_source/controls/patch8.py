src = open('bg.py', encoding='utf-8').read()
a = src.index('def draw_clock(c):')
b = src.index('# ------------------------------------------------------------------ towel', a)
clock = '''CLOCK_RING = [
    "......######......",
    "....##......##....",
    "...#..........#...",
    "..#............#..",
    ".#..............#.",
    ".#..............#.",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    "#................#",
    ".#..............#.",
    ".#..............#.",
    "..#............#..",
    "...#..........#...",
    "....##......##....",
    "......######......",
]


def draw_clock(c):
    import math
    ox, oy = 1, 30
    cx, cy = ox + 8.5, oy + 8.5
    for j, row in enumerate(CLOCK_RING):
        xs = [i for i, ch in enumerate(row) if ch == '#']
        for i in range(xs[0], xs[-1] + 1):
            x, y = ox + i, oy + j
            if row[i] == '#':
                c.set(x, y, K)
                continue
            r = math.hypot(x - cx, y - cy)
            if r > 6.3:
                c.set(x, y, G3 if (x - cx) + (y - cy) < -1.5 else G2)
            elif r > 5.4:
                c.set(x, y, N0)
            else:
                c.set(x, y, G5 if (x - cx) + (y - cy) < -4.5 else G4)
    # hour ticks
    for (x, y) in [(9, 33), (10, 33), (9, 44), (10, 44), (4, 38), (4, 39), (15, 38), (15, 39)]:
        c.set(x, y, G2)
    # hands: just before eight - minute hand near 12, hour hand toward 8
    for (x, y) in [(9, 34), (9, 35), (9, 36), (9, 37), (9, 38), (10, 38)]:
        c.set(x, y, K)
    for (x, y) in [(8, 39), (7, 40), (6, 40)]:
        c.set(x, y, K)
    c.set(10, 39, RD)
    c.set(11, 40, RD)
    c.set(6, 34, WH2)
    c.set(5, 35, WH2)


'''
src = src[:a] + clock + src[b:]
open('bg.py', 'w', encoding='utf-8').write(src)

# keep the layer exporter in sync with the prop change
ex = open('export_layers.py', encoding='utf-8').read()
ex = ex.replace("('props', [bg.draw_chalkboard, bg.draw_towel, bg.draw_gloves]),",
                "('props', [bg.draw_clock, bg.draw_towel, bg.draw_gloves]),")
assert 'draw_chalkboard' not in ex
open('export_layers.py', 'w', encoding='utf-8').write(ex)
print('patched')
