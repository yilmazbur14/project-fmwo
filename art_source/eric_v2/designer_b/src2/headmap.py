"""Hand-authored head region map. Local cols c = x - 30 (0..35), rows y 3..54.
Mirror pair: c <-> 35 - c (x <-> 95 - x)."""
X0, Y0, HW, HH = 30, 3, 36, 52

rows = {}


def span(y, c0, c1, ch):
    r = rows.setdefault(y, ['.'] * HW)
    for c in range(c0, c1 + 1):
        r[c] = ch


def sspan(y, c0, c1, ch):
    """symmetric span"""
    span(y, c0, c1, ch)
    span(y, 35 - c1, 35 - c0, ch)


# ---------------- hair silhouette (slight sweep to viewer's right)
span(4, 20, 23, 'h')
span(5, 13, 25, 'h')
span(6, 10, 26, 'h')
span(7, 8, 28, 'h')
span(8, 7, 29, 'h')
span(9, 6, 30, 'h')
span(10, 5, 30, 'h')
for y in range(11, 14):
    span(y, 5, 31, 'h')
for y in range(14, 27):
    span(y, 4, 31, 'h')
# ---------------- forehead / face window (swept fringe: skin shows more on the left)
span(15, 11, 13, 'f')
span(16, 9, 17, 'f')
span(17, 8, 20, 'f'); span(17, 25, 26, 'f')
span(18, 8, 27, 'f')
for y in range(19, 27):
    span(y, 8, 27, 'f')
# ---------------- ears
for y in range(20, 26):
    sspan(y, 2, 3, 'r')
sspan(21, 1, 1, 'r'); sspan(22, 1, 1, 'r'); sspan(23, 1, 1, 'r'); sspan(24, 1, 1, 'r')
# ---------------- beard silhouette
sspan(26, 4, 7, 'd')
sspan(27, 3, 8, 'd')
sspan(28, 3, 9, 'd')
sspan(29, 3, 10, 'd')
for y in range(30, 37):
    span(y, 2, 33, 'd')
for y in range(37, 40):
    span(y, 3, 32, 'd')
for y in range(40, 42):
    span(y, 4, 31, 'd')
for y in range(42, 44):
    span(y, 5, 30, 'd')
span(44, 6, 29, 'd')
span(45, 7, 28, 'd')
span(46, 8, 27, 'd')
sspan(47, 9, 12, 'd'); span(47, 14, 21, 'd')
sspan(48, 10, 11, 'd'); span(48, 14, 21, 'd')
span(49, 15, 20, 'd')
span(50, 15, 20, 'd')
span(51, 16, 19, 'd')
span(52, 17, 18, 'd')
# face remains between beard sides on rows 26..29
span(26, 8, 27, 'f')
span(27, 9, 26, 'f')
span(28, 10, 25, 'f')
span(29, 11, 24, 'f')
# ---------------- moustache
span(27, 15, 20, 'm')
span(28, 13, 22, 'm')
span(29, 11, 24, 'm')
span(30, 9, 26, 'm')
sspan(31, 8, 14, 'm')
sspan(32, 8, 12, 'm')
sspan(33, 8, 10, 'm')
sspan(34, 9, 9, 'm')
# mouth below moustache
span(31, 15, 20, 'o')
span(32, 14, 21, 'l')
span(32, 16, 19, 'o')
# ---------------- brows (angry: inner ends low)
sspan(18, 8, 10, 'n')
sspan(19, 8, 13, 'n')
sspan(20, 11, 15, 'n')
# ---------------- eyes
sspan(21, 10, 14, 'k')
span(22, 10, 14, 'e'); span(22, 21, 25, 'e')
span(22, 12, 13, 'p'); span(22, 22, 23, 'p')
sspan(22, 14, 14, 'k')  # inner corner
sspan(23, 11, 13, 'u')  # under-eye crease (skin mid)

grid = [''.join(rows.get(y, ['.'] * HW)) for y in range(Y0, Y0 + HH)]

if __name__ == '__main__':
    for i, g in enumerate(grid):
        print('%2d %s' % (Y0 + i, g))
