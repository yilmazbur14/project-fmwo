import pickle
from pngio import hexc
rows = pickle.load(open("intro_rows.pkl", "rb"))
NAMES = {'#847e87':'FLR','#222034':'NAV','#8f563b':'WD','#45283c':'MAR','#000000':'BLK','#663931':'WDk','#ffffff':'WHT','#eec39a':'SKN','#ac3232':'RED','#d9a066':'SKd','#9badb7':'GRY','#5b6ee1':'BLU'}
def runs(y, minlen=4):
    row = rows[y]
    out = []
    start = 0
    for x in range(1, len(row) + 1):
        if x == len(row) or row[x] != row[start]:
            if x - start >= minlen:
                out.append((start, x - 1, NAMES[hexc(row[start])]))
            start = x
    return out
import sys
for y in [0, 30, 60, 90, 120, 150, 160, 180, 240, 280, 285, 290, 295, 300, 360, 400, 450, 500, 560, 580, 600, 700, 800, 820, 830, 840, 850, 900, 950, 990, 1000, 1040, 1079]:
    r = runs(y, 6)
    print(y, ' '.join('%d-%d:%s' % t for t in r if t[2] not in ('WDk',)))
