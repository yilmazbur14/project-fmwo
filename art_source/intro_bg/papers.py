"""Small stack of sign-up sheets with a blue chat-mascot face on the top sheet."""

# (x0, y0, x1, y1) inclusive outline rects, bottom sheet first
SHEETS = [
    (273, 191, 320, 251),
    (269, 188, 312, 247),
    (265, 184, 305, 242),
]

# simple rounded blue chat-mascot face (not a trace of any logo): ear bumps, two eyes, soft chin
MASCOT = [
    "..UUU.....UUU..",
    ".UUUUUUUUUUUUU.",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUWWUUUWWUUUU",
    "UUUUUUUUUUUUUUU",
    "UUUUUUUUUUUUUUU",
    ".UUUUUUUUUUUUU.",
    "..UUUU...UUUU..",
]

# scribbled sign-up lines (x offset, length) per row offset
LINES = [
    (0, [(6, 11, 0), (19, 10, 1)]),
    (5, [(6, 6, 0), (14, 16, -1)]),
    (10, [(6, 13, 1), (21, 7, 0)]),
    (15, [(6, 9, 0), (17, 12, 1)]),
    (20, [(6, 5, 0), (13, 4, -1)]),
]


def draw_papers(cv):
    # cast shadow on the desk (light from upper-left)
    for (x0, y0, x1, y1) in SHEETS:
        for y in range(y0 + 2, y1 + 3):
            for x in range(x0 + 2, x1 + 3):
                k = cv.get(x, y)
                if k == 'w':
                    cv.set(x, y, 'B')
                elif k == 'B':
                    cv.set(x, y, 'M')
    for i, (x0, y0, x1, y1) in enumerate(SHEETS):
        top = (i == len(SHEETS) - 1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if x in (x0, x1) or y in (y0, y1):
                    cv.set(x, y, 'K')
                else:
                    # paper thickness / curl: pale shade along right and bottom edges
                    k = 'W'
                    if x >= x1 - 2 or y >= y1 - 2:
                        k = 'P'
                    if not top:
                        k = 'P' if k == 'W' else 'g'
                    cv.set(x, y, k)
    x0, y0, x1, y1 = SHEETS[-1]
    # mascot centred near the top of the sheet
    mx = x0 + (x1 - x0 + 1 - len(MASCOT[0])) // 2
    my = y0 + 5
    for j, line in enumerate(MASCOT):
        for i, ch in enumerate(line):
            if ch != '.':
                cv.set(mx + i, my + j, ch)
    ly = my + len(MASCOT) + 5
    for (dy, segs) in LINES:
        for (ox, ln, wob) in segs:
            for i, x in enumerate(range(x0 + ox, x0 + ox + ln)):
                if x < x1 - 3:
                    yy = ly + dy + (wob if i > ln // 2 else 0)
                    cv.set(x, yy, 'E')
