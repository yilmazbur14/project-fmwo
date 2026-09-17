from pngio import read_png
from collections import Counter
P = 'C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Environment/crowd_v2.png'
w, h, px = read_png(P)
print('size', w, h, 'frames', w / 640)
print('alpha values', dict(Counter(p[3] for r in px for p in r)))
DB32 = {(0,0,0),(34,32,52),(69,40,60),(102,57,49),(143,86,59),(223,113,38),(217,160,102),(238,195,154),(251,242,54),(153,229,80),(106,190,48),(55,148,110),(75,105,47),(82,75,36),(50,60,57),(63,63,116),(48,96,130),(91,110,225),(99,155,255),(95,205,228),(203,219,252),(255,255,255),(155,173,183),(132,126,135),(105,106,106),(89,86,82),(118,66,138),(172,50,50),(217,87,99),(215,123,186),(143,151,74),(138,111,48)}
cols = set(p[:3] for r in px for p in r if p[3])
print('colours', len(cols), 'non-DB32:', cols - DB32)
# short-repeat check on the visible rows (0-30): best match of the frame against itself shifted sideways
for fi in (0, 3):
    F = [r[fi * 640:(fi + 1) * 640] for r in px[:31]]
    best = []
    for s in range(6, 321):
        same = sum(1 for y in range(31) for x in range(640 - s) if F[y][x] == F[y][x + s])
        best.append((same / (31 * (640 - s)), s))
    best.sort(reverse=True)
    print('frame', fi, 'top self-similarity under horizontal shift:', [(round(a, 3), s) for a, s in best[:4]])
# per-transition motion on visible rows
Fs = [[r[i * 640:(i + 1) * 640] for r in px[:31]] for i in range(5)]
for a, b in ((0, 1), (1, 2), (2, 0), (3, 4)):
    n = sum(1 for y in range(31) for x in range(640) if Fs[a][y][x] != Fs[b][y][x])
    print('change %d->%d: %.1f%%' % (a, b, 100 * n / (31 * 640)))
