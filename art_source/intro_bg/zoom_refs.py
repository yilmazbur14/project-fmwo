import sys
from collections import Counter
from pngio import *
P = "C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/"
for name, path in [("portrait", P+"Danny/portrait.png"), ("mason", P+"Mason/mason.png"), ("dannydlg", P+"Danny/DannyDialogue.png")]:
    w, h, rows = read_png(path)
    print(name, w, h)
    c = Counter(px for row in rows for px in row)
    for px, n in c.most_common(40):
        print("   ", hexc(px), px[3], n)
    write_png("ref_%s_8x.png" % name, scale(on_bg(rows, (60, 90, 60)), 8))
