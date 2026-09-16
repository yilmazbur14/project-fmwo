src = open('bg.py', encoding='utf-8').read()

# ---- towel v3: lies on the seat, bends over the front edge, flares toward the hem
rows = [
    "...###############...",
    "..#" + "W" * 14 + "g" + "#..",
    "..#" + "W" * 14 + "g" + "#..",
    "..#" + "w" * 14 + "g" + "#..",
    "..#" + "ggg" + "w" * 8 + "gggg" + "#..",
    "..#" + "W" + "w" * 5 + "g" + "w" * 7 + "g" + "#..",
    "..#" + "W" + "w" * 5 + "g" + "w" * 7 + "g" + "#..",
    ".#" + "W" + "w" * 6 + "g" + "w" * 8 + "g" + "#.",
    ".#" + "W" + "w" * 6 + "g" + "w" * 8 + "g" + "#.",
    ".#" + "W" + "w" * 7 + "g" + "w" * 7 + "g" + "#.",
    ".#" + "p" + "r" * 15 + "R" + "#.",
    ".#" + "R" * 17 + "#.",
    ".#" + "W" + "w" * 7 + "g" + "w" * 7 + "g" + "#.",
    ".#" + "p" + "r" * 15 + "R" + "#.",
    ".#" + "R" * 17 + "#.",
    "#" + "W" + "w" * 8 + "g" + "w" * 8 + "g" + "#",
    "#" + "W" + "w" * 9 + "g" + "w" * 7 + "g" + "#",
    "#" + "w" * 10 + "g" + "w" * 7 + "g" + "#",
    "#" + "g" + "w" * 9 + "g" + "w" * 6 + "gg" + "#",
    "#" + "gggg" + "w" * 6 + "g" + "w" * 6 + "gg" + "#",
    "." + "####" + "ggg" + "www" + "g" + "wwwww" + "ggg" + "#",
    "....." + "####" + "gggg" + "www" + "ggg" + "#" + ".",
    "........." + "#####" + "gggg" + "#" + "..",
    ".............." + "####" + "...",
]
for r in rows:
    assert len(r) == 21, (r, len(r))
a = src.index('TOWEL = [')
b = src.index(']\n', a) + 2
src = src[:a] + 'TOWEL = [\n' + ''.join('    "%s",\n' % r for r in rows) + ']\n' + src[b:]
src = src.replace("c.grid(18, 216, towel_grid(), TOWEL_MAP, skip='.')",
                  "c.grid(18, 221, towel_grid(), TOWEL_MAP, skip='.')")

# ---- door spill: small deliberate glow instead of scattered dither
a = src.index('def draw_door_spill(c):')
b = src.index('# ------------------------------------------------------------------ bench', a)
spill = '''def draw_door_spill(c):
    """warm light leaking from under the ring door onto the floor"""
    # (row offset below the floor line, coverage, horizontal growth)
    bands = [(0, 1.0, 0), (1, 0.5, 1), (2, 0.5, 2), (3, 0.25, 3), (4, 0.25, 4)]
    for d, cov, grow in bands:
        y = FLOOR_Y + d
        xa, xb = 572 - grow, 627 + grow
        for x in range(xa, xb + 1):
            if not (0 <= x < W) or c.get(x, y) not in (G1, N0):
                continue
            # soften the band ends
            end = min(x - xa, xb - x)
            cv = cov if end >= 3 else cov * 0.5
            if cv >= 1.0 or dith(x, y, cv):
                c.set(x, y, OL)


'''
src = src[:a] + spill + src[b:]
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
