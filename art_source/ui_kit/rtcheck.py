import sys
from kitlib import *
UI = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/UI/"
ok = True
for name in sys.argv[1:]:
    a = read_png(UI + name + ".png")
    b = read_png("final/rt_" + name + ".png")
    # compare treating all fully-transparent pixels as equal
    norm = lambda px: [[p if p[3] else (0, 0, 0, 0) for p in r] for r in px]
    same = a[0] == b[0] and a[1] == b[1] and norm(a[2]) == norm(b[2])
    if not same:
        ok = False
        diffs = [(x, y, a[2][y][x], b[2][y][x]) for y in range(min(a[1], b[1])) for x in range(min(a[0], b[0])) if (a[2][y][x] if a[2][y][x][3] else (0,0,0,0)) != (b[2][y][x] if b[2][y][x][3] else (0,0,0,0))]
        print(name, "MISMATCH", a[0], a[1], "vs", b[0], b[1], diffs[:5])
    else:
        print(name, "round-trip identical", a[0], "x", a[1])
print("ALL OK" if ok else "FAILURES")
