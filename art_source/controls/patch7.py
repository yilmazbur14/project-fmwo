"""Adapt props to the UI-kit layout (cards x20..526, y13..265): nothing gets sliced by a card edge."""
src = open('bg.py', encoding='utf-8').read()

# ---- 1) wall clock replaces the chalkboard (fits the 20px left strip)
a = src.index('# ------------------------------------------------------------------ chalkboard')
b = src.index('# ------------------------------------------------------------------ towel', a)
clock = '''# ------------------------------------------------------------------ wall clock
def draw_clock(c):
    import math
    cx, cy = 9.5, 38.5
    R_OUT, R_BEZEL, R_FACE = 8.7, 6.4, 5.6

    def d(x, y):
        return math.hypot(x - cx, y - cy)

    def inside(x, y):
        return d(x, y) <= R_OUT
    for y in range(28, 50):
        for x in range(0, 20):
            if not inside(x, y):
                continue
            if any(not inside(x + a, y + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                c.set(x, y, K)
                continue
            r = d(x, y)
            lit = (x - cx) + (y - cy) < -1.5
            if r > R_BEZEL:
                c.set(x, y, G3 if lit else G2)
            elif r > R_FACE:
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
    c.set(10, 39, RD)   # red second-hand stub
    c.set(11, 40, RD)
    # glass glint
    c.set(6, 34, WH2)
    c.set(5, 35, WH2)


'''
src = src[:a] + clock + src[b:]
src = src.replace('    draw_chalkboard(c)\n', '    draw_clock(c)\n')

# ---- 2) towel moves to the bench's left end (cut only by the screen edge)
old = "c.grid(18, 221, towel_grid(), TOWEL_MAP, skip='.')"
assert old in src
src = src.replace(old, "c.grid(-3, 221, towel_grid(), TOWEL_MAP, skip='.')")

# ---- 3) flush-mounted ceiling lights with a clear gap above the cards
a = src.index('def draw_fixture(c, fx):')
b = src.index('# ------------------------------------------------------------------ lockers', a)
fixture = '''def draw_fixture(c, fx):
    x0, x1 = fx - 25, fx + 24
    c.hline(x0, x1, 6, K)
    for y, col in ((7, G3), (8, G2)):
        c.set(x0, y, K); c.set(x1, y, K)
        c.hline(x0 + 1, x1 - 1, y, col)
    c.set(x0, 9, K); c.set(x1, 9, K)
    c.hline(x0 + 1, x1 - 1, 9, G5)
    c.hline(x0 + 4, x1 - 4, 9, WH2)
    c.hline(x0 + 1, x1 - 1, 10, K)


'''
src = src[:a] + fixture + src[b:]

# wall: no ceiling-shadow dither directly under a light (a little light spill instead)
old = '''            sh = 1.0 - (y - WALL_Y0) / 7.0
            if sh > 0 and dith(x, y, sh):'''
assert old in src
new = '''            sh = 1.0 - (y - WALL_Y0) / 7.0
            under_light = any(abs(x - fx) <= 22 for fx in FIXTURES)
            if sh > 0 and not under_light and dith(x, y, sh):'''
src = src.replace(old, new)

# the old mock helper used the brief's card rectangles; keep it but add the UI-kit layout too
src = src.replace("CARDS = [(50, 17, 213, 275), (218, 17, 382, 275), (387, 17, 550, 275)]",
                  "CARDS = [(50, 17, 213, 275), (218, 17, 382, 275), (387, 17, 550, 275)]\n"
                  "CARDS_UIKIT = [(20, 13, 179, 265), (193, 13, 352, 265), (367, 13, 526, 265)]")
open('bg.py', 'w', encoding='utf-8').write(src)
print('patched')
