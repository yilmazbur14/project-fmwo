import sys
from pngio import read_png
D = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/'
for name in sys.argv[1:]:
    a = read_png(D + name + '.png'); b = read_png('rt_' + name + '.png')
    if a[:2] != b[:2]:
        print(name, 'SIZE MISMATCH', a[:2], b[:2]); continue
    diff = 0
    for ra, rb in zip(a[2], b[2]):
        for pa, pb in zip(ra, rb):
            if pa[3] == 0 and pb[3] == 0: continue
            if pa != pb: diff += 1
    print(name, a[:2], 'differing pixels:', diff)
